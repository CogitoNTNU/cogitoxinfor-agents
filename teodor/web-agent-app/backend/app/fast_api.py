from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import asyncio
import sys
import os
from typing import Dict, List, Optional, Union, Any
import base64
from pydantic import BaseModel
import time
from .mcp_agent import MCPAgent


app = FastAPI(title="Web Automation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active sessions
active_sessions = {}
active_connections = {}
response_queues = {}  # Store response queues for each session

class TestAction(BaseModel):
    action: str
    args: List[str]

class AgentRequest(BaseModel):
    query: str
    testing: bool = False
    test_actions: Optional[List[TestAction]] = None
    human_intervention: bool = False

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/agent/run")
async def run_web_agent(request: AgentRequest):
    """
    Start a new web agent session and return the session ID
    """
    session_id = str(uuid.uuid4())
    
    # Convert test actions to the format expected by the agent
    formatted_test_actions = None
    if request.test_actions:
        formatted_test_actions = [(action.action, action.args) for action in request.test_actions]
    
    # Store session info (we'll actually run the agent when the websocket connects)
    active_sessions[session_id] = {
        "query": request.query,
        "testing": request.testing,
        "test_actions": formatted_test_actions,
        "human_intervention": request.human_intervention,
        "status": "initialized"
    }
    
    return {"session_id": session_id, "message": "Session created. Connect to WebSocket to start."}

@app.get("/api/browser/{session_id}/dom", response_class=HTMLResponse)
async def get_browser_dom(session_id: str):
    """Get the current DOM from the browser"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the agent instance
    agent = active_sessions[session_id].get("agent")
    if not agent or not agent.tools:
        raise HTTPException(status_code=400, detail="Browser not available")
    
    try:
        # 1. Get screenshot using browser_take_screenshot tool
        screenshot_tool = next((t for t in agent.tools if t.name == "browser_take_screenshot"), None)
        screenshot_data = ""
        if screenshot_tool:
            screenshot_result = await screenshot_tool._arun()
            # Extract base64 data from markdown format
            import re
            match = re.search(r'data:image\/png;base64,([^)]+)', screenshot_result)
            if match:
                screenshot_data = match.group(1)
        
        # 2. Get DOM snapshot using browser_snapshot tool
        snapshot_tool = next((t for t in agent.tools if t.name == "browser_snapshot"), None)
        snapshot_data = "DOM snapshot not available"
        if snapshot_tool:
            snapshot_result = await snapshot_tool._arun()
            snapshot_data = snapshot_result
        
        # Create HTML that combines both
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Browser View - {session_id}</title>
            <style>
                body {{ margin: 0; padding: 0; font-family: system-ui, sans-serif; }}
                .container {{ display: flex; flex-direction: column; height: 100vh; }}
                .screenshot {{ flex: 1; display: flex; justify-content: center; align-items: center; }}
                .screenshot img {{ max-width: 100%; max-height: 90vh; }}
                .dom-content {{ padding: 10px; max-height: 30vh; overflow: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="screenshot">
                    <img src="data:image/png;base64,{screenshot_data}" alt="Browser screenshot" />
                </div>
                <hr>
                <div class="dom-content">
                    <details>
                        <summary>DOM Structure</summary>
                        <pre>{snapshot_data}</pre>
                    </details>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.websocket("/api/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in active_sessions:
        await websocket.close(code=4000, reason="Invalid session ID")
        return
    
    await websocket.accept()
    active_connections[session_id] = websocket
    
    # Create response queue for this session
    response_queue = asyncio.Queue()
    response_queues[session_id] = response_queue
    
    try:
        session = active_sessions[session_id]
        
        # Initialize agent
        agent = MCPAgent()
        await agent.initialize()
        
        # Store agent in session
        active_sessions[session_id]["agent"] = agent
        
        async def event_callback(event_data):
            """Enhanced event callback to structure agent events for frontend consumption"""
            print(f"Event callback triggered with data: {event_data}")
            
            # Add timestamp to all events
            formatted_event = {
                "timestamp": int(time.time() * 1000),
                "session_id": session_id,
                **event_data
            }
            
            # For tool calls/interrupts, add structured data
            if event_data.get("type") == "INTERRUPT":
                # Extract tool information from the message if available
                message = event_data.get("payload", {}).get("message", "")
                tool_info = {}
                
                # Try to parse tool information from the message
                if "with args:" in message:
                    try:
                        parts = message.split("with args:")
                        tool_name = parts[0].split("perform:")[1].strip()
                        args_str = parts[1].strip()
                        # Convert string representation of dict to actual dict
                        import ast
                        args = ast.literal_eval(args_str)
                        
                        # Add structured tool info
                        formatted_event["payload"]["tool"] = {
                            "name": tool_name,
                            "args": args
                        }
                    except Exception as e:
                        print(f"Error parsing tool info: {e}")
            
        # Background task to handle WebSocket messages
        async def handle_client_messages():
            try:
                while True:
                    data = await websocket.receive_json()
                    print(f"Received WebSocket message: {data}")
                    if data.get("type") == "INTERVENTION_RESPONSE":
                        user_input = data.get("payload", {}).get("input", "")
                        print(f"Putting response in queue: {user_input}")
                        await response_queue.put(user_input)
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for session {session_id}")
            except Exception as e:
                print(f"Error in client message handler: {str(e)}")

        # Start message handler
        client_handler = asyncio.create_task(handle_client_messages())

        playwright = None
        context = None
        page = None

        # Define default user data directory
        DEFAULT_USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "playwright_user_data")

        # Create browser configuration
        browser_config = BrowserConfig(
            browser_type="playwright_chrome",
            persistent=True,
            user_data_dir=DEFAULT_USER_DATA_DIR
        )
            
        # Initialize browser with persistent context
        playwright, context, page = await initialize_browser(
            start_url="https://www.google.com",
            reuse_session=True,
            config=browser_config
        )
    

        try:
            # Run the agent with UI mode enabled
            final_answer = await langgraph_run_agent(
                page=page,
                query=session["query"],
                config={
                    "recursion_limit": 150,
                    "configurable": {
                        "thread_id": session_id,
                        "page": None
                    }
                },
                testing=session["testing"],
                test_actions=session["test_actions"],
                human_intervention=session["human_intervention"],
                event_callback=event_callback,
                ui_mode=True,  # Enable UI mode
                response_queue=response_queue  # Pass response queue
            )
            
            # Send completion message
            await websocket.send_json({
                "type": "COMPLETED", 
                "payload": {"status": "completed", "answer": final_answer}
            })
            
        except Exception as e:
            # Send error message
            await websocket.send_json({
                "type": "ERROR", 
                "payload": {"status": "error", "message": str(e)}
            })
            raise
        finally:
            # Cancel background task
            client_handler.cancel()
            
    except WebSocketDisconnect:
        # Handle client disconnect
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in response_queues:
            del response_queues[session_id]
    except Exception as e:
        # Handle other errors
        await websocket.send_json({
            "type": "ERROR", 
            "payload": {"status": "error", "message": str(e)}
        })
    finally:
        # Clean up resources
        if session_id in active_sessions and "agent" in active_sessions[session_id]:
            await active_sessions[session_id]["agent"].cleanup()
        
        if session_id in active_connections:
            del active_connections[session_id]

# Check if the script is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.fast_api:app", host="0.0.0.0", port=8000, reload=True)
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import asyncio
import sys
import os
from typing import Dict, List, Optional, Union, Any
import base64
from pydantic import BaseModel

# No need for sys.path.append since the graph is now local
# Import from the local graph implementation
from .graph.browser import initialize_browser, close_browser, BrowserConfig
from .graph.main import run_agent as langgraph_run_agent
from .capture_dom import capture_dom

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

from .config import HISTORY_DIR

@app.get("/api/history/{session_id}/{step}")
async def get_screenshot(session_id: str, step: int):
    """Retrieve a screenshot from the history folder"""
    history_dir = os.path.join(HISTORY_DIR, session_id)
    filename = f"{step}.png"
    file_path = os.path.join(history_dir, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail=f"Screenshot not found at {file_path}")

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
        
        async def event_callback(event_data):
            print(f"Event callback triggered with data: {event_data}")
            await websocket.send_json(event_data)
        
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
            # Clean up browser resources
            try:
                await close_browser(force=False)
                print("Browser session closed.")
            except Exception as e:
                print(f"Error closing browser: {str(e)}")
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
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in response_queues:
            del response_queues[session_id]

# Check if the script is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.fast_api:app", host="0.0.0.0", port=8000, reload=True)
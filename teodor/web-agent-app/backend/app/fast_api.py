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
from datetime import datetime, timedelta

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

# Create a task to clean up old sessions
async def cleanup_old_sessions():
    while True:
        try:
            now = int(time.time())
            sessions_to_remove = []
            
            for session_id, session in active_sessions.items():
                # If session hasn't been active for more than 30 minutes
                if now - session.get("last_activity", 0) > 1800:  # 30 minutes
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                if "agent" in active_sessions[session_id]:
                    try:
                        await active_sessions[session_id]["agent"].cleanup()
                    except Exception as e:
                        print(f"Error cleaning up agent for session {session_id}: {e}")
                
                del active_sessions[session_id]
                if session_id in response_queues:
                    del response_queues[session_id]
                print(f"Cleaned up inactive session: {session_id}")
                
        except Exception as e:
            print(f"Error in session cleanup task: {e}")
        
        # Run every 5 minutes
        await asyncio.sleep(300)

# Start the cleanup task when app starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_sessions())

class TestAction(BaseModel):
    action: str
    args: List[str]

class AgentRequest(BaseModel):
    query: str = ""
    testing: bool = False
    test_actions: Optional[List[TestAction]] = None
    human_intervention: bool = False
    session_id: Optional[str] = None

class SessionCreateRequest(BaseModel):
    init_browser_only: bool = True

class SessionStatus(BaseModel):
    session_id: str
    status: str
    created_at: int
    last_activity: int

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/session/create")
async def create_session(request: SessionCreateRequest):
    """Create a new session with optional browser initialization"""
    session_id = str(uuid.uuid4())
    
    # Store basic session info
    active_sessions[session_id] = {
        "query": "",
        "testing": False,
        "test_actions": [],
        "human_intervention": False,
        "status": "initialized",
        "created_at": int(time.time()),
        "last_activity": int(time.time())
    }
    
    # Initialize browser if requested
    if request.init_browser_only:
        try:
            # Create and initialize agent
            agent = MCPAgent()
            await agent.initialize()
            
            # Store agent in session
            active_sessions[session_id]["agent"] = agent
            active_sessions[session_id]["status"] = "browser_ready"
            
            # Create a queue for potential future responses
            response_queue = asyncio.Queue()
            response_queues[session_id] = response_queue
        except Exception as e:
            return {"session_id": session_id, "status": "error", "message": str(e)}
    
    return {"session_id": session_id, "status": "success"}

@app.get("/api/session/{session_id}/status")
async def get_session_status(session_id: str) -> SessionStatus:
    """Get status of an existing session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    # Update last activity
    session["last_activity"] = int(time.time())
    
    # Determine status based on agent presence
    status = "active" if "agent" in session and session["agent"].initialized else "inactive"
    
    return SessionStatus(
        session_id=session_id,
        status=status,
        created_at=session.get("created_at", 0),
        last_activity=session["last_activity"]
    )

@app.post("/api/agent/run")
async def run_web_agent(request: AgentRequest):
    """
    Start a new web agent session and return the session ID
    """
    # Check if we're using an existing session
    if request.session_id and request.session_id in active_sessions:
        session_id = request.session_id
        session = active_sessions[session_id]
        
        # Update session parameters for this run
        session["query"] = request.query
        session["testing"] = request.testing
        session["test_actions"] = request.test_actions or []
        session["human_intervention"] = request.human_intervention
        session["status"] = "ready_to_run"
    else:
        # Create a new session as before
        session_id = str(uuid.uuid4())
        
        # Format test actions for the agent
        formatted_test_actions = []
        if request.testing and request.test_actions:
            for action in request.test_actions:
                formatted_test_actions.append({
                    "action": action.action,
                    "args": action.args
                })
        
        active_sessions[session_id] = {
            "query": request.query,
            "testing": request.testing,
            "test_actions": formatted_test_actions,
            "human_intervention": request.human_intervention,
            "status": "initialized",
            "created_at": int(time.time()),
            "last_activity": int(time.time())
        }
    
    return {"session_id": session_id, "message": "Session ready. Connect to WebSocket to start."}

@app.get("/api/browser/{session_id}/dom", response_class=HTMLResponse)
async def get_browser_dom(session_id: str):
    """Get the current DOM from the browser"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get the agent instance
    agent = active_sessions[session_id].get("agent")
    if not agent or not agent.tools:
        # Return a placeholder HTML instead of error
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Browser not available</title>
            <style>
                body { 
                    margin: 0; 
                    padding: 20px; 
                    font-family: system-ui, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                .message {
                    text-align: center;
                    padding: 20px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="message">
                <h3>Browser Not Available</h3>
                <p>The browser session is not yet initialized or has been closed.</p>
                <p>Please wait for the agent to start working or try refreshing.</p>
            </div>
        </body>
        </html>
        """)
    
    try:
        # Get browser content directly through tools without relying on the session
        screenshot_data = ""
        snapshot_data = "DOM snapshot not available"
        
        # Check for existence of browser tools
        browser_tools = [t for t in agent.tools if t.name.startswith('browser_')]
        if not browser_tools:
            raise ValueError("No browser tools available")
        
        # Get screenshot using browser_take_screenshot tool directly
        try:
            screenshot_tool = next((t for t in agent.tools if t.name == "browser_take_screenshot"), None)
            if screenshot_tool:
                screenshot_result = await screenshot_tool._arun()
                # Extract base64 data from markdown format
                import re
                match = re.search(r'data:image\/png;base64,([^)]+)', screenshot_result)
                if match:
                    screenshot_data = match.group(1)
        except Exception as screenshot_error:
            print(f"Screenshot error: {screenshot_error}")
            
        # Get DOM snapshot using browser_snapshot tool directly
        try:
            snapshot_tool = next((t for t in agent.tools if t.name == "browser_snapshot"), None)
            if snapshot_tool:
                snapshot_result = await snapshot_tool._arun()
                snapshot_data = snapshot_result
        except Exception as snapshot_error:
            print(f"Snapshot error: {snapshot_error}")
        
        # If both attempts failed, try to navigate first to initialize the browser
        if not screenshot_data and snapshot_data == "DOM snapshot not available":
            try:
                nav_tool = next((t for t in agent.tools if t.name == "browser_navigate"), None)
                if nav_tool:
                    # Try to navigate to Google to initialize the browser
                    await nav_tool._arun(url="https://www.google.com")
                    
                    # Try screenshot and snapshot again
                    if screenshot_tool:
                        screenshot_result = await screenshot_tool._arun()
                        match = re.search(r'data:image\/png;base64,([^)]+)', screenshot_result)
                        if match:
                            screenshot_data = match.group(1)
                    
                    if snapshot_tool:
                        snapshot_result = await snapshot_tool._arun()
                        snapshot_data = snapshot_result
            except Exception as nav_error:
                print(f"Navigation error: {nav_error}")
        
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
                .error-message {{ color: #ff4444; text-align: center; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="screenshot">
                    {f'<img src="data:image/png;base64,{screenshot_data}" alt="Browser screenshot" />' if screenshot_data else '<div class="error-message">Screenshot not available</div>'}
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
        # Return error HTML instead of crashing
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Browser Error</title>
            <style>
                body {{ margin: 0; padding: 20px; font-family: system-ui, sans-serif; }}
                .error {{ color: #ff4444; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h3>Error accessing browser</h3>
                <p>{str(e)}</p>
                <p>The browser session might be closed or not properly initialized.</p>
                
                <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd;">
                    <button onclick="initializeBrowser()" style="padding: 8px 16px; cursor: pointer;">
                        Initialize Browser
                    </button>
                </div>
                
                <script>
                async function initializeBrowser() {{
                    try {{
                        const response = await fetch('/api/session/{session_id}/init-browser', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}}
                        }});
                        
                        const data = await response.json();
                        if (data.status === 'success') {{
                            // Refresh the page after initialization
                            setTimeout(() => window.location.reload(), 1000);
                        }} else {{
                            alert('Error: ' + data.message);
                        }}
                    }} catch (error) {{
                        alert('Error: ' + error.message);
                    }}
                }}
                </script>
            </div>
        </body>
        </html>
        """, status_code=200)

@app.post("/api/session/{session_id}/init-browser")
async def initialize_browser(session_id: str):
    """Initialize the browser for viewing"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Get the agent instance
        agent = active_sessions[session_id].get("agent")
        if not agent or not agent.tools:
            return {"status": "error", "message": "Agent not initialized"}
        
        # Find a browser navigation tool
        nav_tool = next((t for t in agent.tools if t.name == "browser_navigate"), None)
        if not nav_tool:
            return {"status": "error", "message": "Browser navigation tool not found"}
            
        # Navigate to Google to initialize the browser
        try:
            await nav_tool._arun(url="https://www.google.com")
            return {"status": "success", "message": "Browser initialized"}
        except Exception as e:
            return {"status": "error", "message": f"Error initializing browser: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/api/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in active_sessions:
        await websocket.close(code=4000, reason="Invalid session ID")
        return
    
    await websocket.accept()
    active_connections[session_id] = websocket
    
    # Set up response queue
    response_queue = asyncio.Queue()
    response_queues[session_id] = response_queue
    consumer_task = None  # Initialize as None to avoid reference errors
    
    try:
        session = active_sessions[session_id]
        
        # Check if agent is already initialized
        if "agent" not in session or not session["agent"].initialized:
            # Initialize agent
            agent = MCPAgent()
            await agent.initialize()
            session["agent"] = agent
        
        # Use a single consumer for all incoming messages
        async def message_consumer():
            try:
                while True:
                    try:
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        if message.get("type") == "INTERVENTION_RESPONSE":
                            user_input = message.get("payload", {}).get("input", "approved")
                            print(f"Got user response: '{user_input}'")
                            await response_queue.put(user_input)
                    except WebSocketDisconnect:
                        print("WebSocket disconnected in consumer task")
                        break
                    except Exception as e:
                        print(f"Error in message consumer: {e}")
                        if "disconnect message has been received" in str(e):
                            break  # Exit the loop on disconnect errors
            except asyncio.CancelledError:
                print("Message consumer task was cancelled")
                # Just exit cleanly on cancellation
            except Exception as e:
                print(f"Fatal error in message consumer: {e}")
        
        # Start consumer task
        consumer_task = asyncio.create_task(message_consumer())
        
        # Define simple callback that just forwards events
        async def event_callback(event_data):
            try:
                if websocket.client_state.CONNECTED:  # Check if still connected
                    await websocket.send_json(event_data)
            except Exception as e:
                print(f"Error in event callback: {e}")
        
        # Run agent with minimal wrapping
        try:
            from .run_agent import run_agent
            
            final_answer = await run_agent(
                query=session["query"],
                agent=session["agent"],
                human_in_the_loop=session["human_intervention"],
                event_callback=event_callback,
                ui_mode=True,
                response_queue=response_queue
            )
            
            # Only send completion if still connected
            try:
                if websocket.client_state.CONNECTED:
                    await websocket.send_json({
                        "type": "COMPLETED", 
                        "payload": {"status": "completed", "answer": final_answer}
                    })
            except Exception as e:
                print(f"Error sending completion: {e}")
            
        except Exception as e:
            print(f"Error running agent: {e}")
            import traceback
            traceback.print_exc()
            
            # Only send error if still connected
            try:
                if websocket.client_state.CONNECTED:
                    await websocket.send_json({
                        "type": "ERROR", 
                        "payload": {"status": "error", "message": str(e)}
                    })
            except Exception as send_err:
                print(f"Error sending error message: {send_err}")
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Make sure consumer task is canceled
        if consumer_task and not consumer_task.done():
            consumer_task.cancel()
            try:
                # Wait for cancellation with timeout
                await asyncio.wait_for(asyncio.shield(consumer_task), timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            except Exception as e:
                print(f"Error cancelling consumer task: {e}")
        
        # Clean up connections
        if session_id in active_connections:
            del active_connections[session_id]
        
        print(f"WebSocket endpoint completed for session {session_id}")

# Check if the script is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.fast_api:app", host="0.0.0.0", port=8000, reload=True)
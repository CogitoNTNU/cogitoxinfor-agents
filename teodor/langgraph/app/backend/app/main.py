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
# Alternative imports using relative paths
from .graph.models import InputState, Prediction
from .graph.browser import initialize_browser, close_browser
from .graph.main import run_agent as langgraph_run_agent
from .graph.graph import get_graph_with_config
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

@app.websocket("/api/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in active_sessions:
        await websocket.close(code=4000, reason="Invalid session ID")
        return
    
    await websocket.accept()
    active_connections[session_id] = websocket
    
    try:
        # Get session parameters
        session = active_sessions[session_id]
        
        # Send initial message
        await websocket.send_json({
            "type": "STATUS_UPDATE", 
            "payload": {"status": "starting", "message": "Initializing browser..."}
        })
        
        # Define callback for sending events
        async def event_callback(event_data):
            await websocket.send_json(event_data)
            # After certain events, send a DOM update
            if event_data.get("type") in ["ACTION_UPDATE", "SCREENSHOT_UPDATE"]:
                if page:
                    dom_data = await capture_dom(page)
                    await websocket.send_json({
                        "type": "DOM_UPDATE", 
                        "payload": dom_data
                    })
        # Execute agent
        try:
            playwright = None
            context = None
            page = None
            
            # Initialize browser
            playwright, context, page = await initialize_browser()
            
            # Update status
            await websocket.send_json({
                "type": "STATUS_UPDATE", 
                "payload": {"status": "running", "message": "Browser initialized, running agent..."}
            })
            
            # Run the agent
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
                event_callback=event_callback
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
            if page:
                await close_browser(playwright, context)
            
    except WebSocketDisconnect:
        # Handle client disconnect
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        # Handle other errors
        await websocket.send_json({
            "type": "ERROR", 
            "payload": {"status": "error", "message": str(e)}
        })
        if session_id in active_connections:
            del active_connections[session_id]

# Define a human intervention handler that works with websockets
async def handle_human_intervention(message, session_id):
    """Handle user input during agent execution"""
    if session_id in active_connections:
        websocket = active_connections[session_id]
        
        # Send intervention request to client
        await websocket.send_json({
            "type": "INTERVENTION_REQUEST",
            "payload": {
                "message": message,
                "session_id": session_id
            }
        })
        
        # Wait for client response
        response = await websocket.receive_json()
        if response.get("type") == "INTERVENTION_RESPONSE":
            return response["payload"]["input"]
            
    # Default fallback
    return ""

# Check if the script is run directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
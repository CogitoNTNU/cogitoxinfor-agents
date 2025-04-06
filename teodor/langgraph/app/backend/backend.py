from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import uuid
from typing import Optional, List, Dict, Any, Union, Set
import uvicorn
import ssl
from fastapi.responses import JSONResponse
import sys
import os
import base64

# Add this to include graph directory for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use direct imports from the graph module
from graph.main import test_agent, run_agent
from graph.browser import initialize_browser, close_browser
from graph.models import InputState, Prediction

app = FastAPI(title="LLM Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced message types to include agent events
MESSAGE_TYPES = {
    "SEND_QUERY": "SEND_QUERY",
    "SESSION_UPDATE": "SESSION_UPDATE",
    "SESSION_COMPLETED": "SESSION_COMPLETED",
    "ACTION_UPDATE": "ACTION_UPDATE",  # For agent actions
    "SCREENSHOT_UPDATE": "SCREENSHOT_UPDATE",  # For webpage screenshots
    "HUMAN_INTERVENTION_REQUEST": "HUMAN_INTERVENTION_REQUEST",  # Request user input
    "HUMAN_INTERVENTION_RESPONSE": "HUMAN_INTERVENTION_RESPONSE",  # User response
    "ERROR": "ERROR",
}

# Request models
class QueryRequest(BaseModel):
    query: str
    testing: bool = False
    test_actions: Optional[List[tuple]] = None
    human_intervention: bool = False
    config: Optional[Dict[str, Any]] = None

class SessionRequest(BaseModel):
    session_id: str

class WebSocketMessage(BaseModel):
    type: str
    payload: Dict[str, Any]

# Store active sessions and their results
active_sessions = {}
session_results = {}
intervention_callbacks = {}  # Store callback functions for human intervention

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_sessions[client_id] = set()
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_sessions:
            del self.user_sessions[client_id]
    
    async def send_personal_message(self, client_id: str, message: Dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    def register_session(self, client_id: str, session_id: str):
        if client_id in self.user_sessions:
            self.user_sessions[client_id].add(session_id)
    
    def get_client_for_session(self, session_id: str):
        for client_id, sessions in self.user_sessions.items():
            if session_id in sessions:
                return client_id
        return None

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")
                payload = message.get("payload", {})
                
                # Handle different message types
                if message_type == MESSAGE_TYPES["SEND_QUERY"]:
                    # Extract query from payload
                    query = payload.get("query")
                    if not query:
                        await manager.send_personal_message(
                            client_id, 
                            {"type": MESSAGE_TYPES["ERROR"], "payload": {"message": "No query provided"}}
                        )
                        continue
                    
                    # Create a new session
                    session_id = str(uuid.uuid4())
                    manager.register_session(client_id, session_id)
                    
                    # Create request object
                    request = QueryRequest(
                        query=query,
                        testing=payload.get("testing", False),
                        test_actions=payload.get("test_actions"),
                        human_intervention=payload.get("human_intervention", False),
                        config=payload.get("config", {})
                    )
                    
                    # Add client_id to config for WebSocket communication
                    if not request.config:
                        request.config = {}
                    request.config["websocket_client_id"] = client_id
                    request.config["session_id"] = session_id
                    
                    # Store request in active sessions
                    active_sessions[session_id] = request
                    
                    # Send session update to client
                    await manager.send_personal_message(
                        client_id,
                        {
                            "type": MESSAGE_TYPES["SESSION_UPDATE"],
                            "payload": {"session_id": session_id, "status": "processing"}
                        }
                    )
                    
                    # Process the session in the background
                    asyncio.create_task(process_session(session_id))
                
                elif message_type == MESSAGE_TYPES["HUMAN_INTERVENTION_RESPONSE"]:
                    # Handle user response to intervention request
                    session_id = payload.get("session_id")
                    response = payload.get("response")
                    
                    # Get the callback for this session
                    callback = intervention_callbacks.get(session_id)
                    if callback:
                        # Call the callback with the user's response
                        await callback(response)
                        # Remove the callback
                        del intervention_callbacks[session_id]
                        
                        # Send update to client
                        await manager.send_personal_message(
                            client_id,
                            {
                                "type": MESSAGE_TYPES["SESSION_UPDATE"],
                                "payload": {"session_id": session_id, "status": "processing"}
                            }
                        )
            
            except json.JSONDecodeError as e:
                await manager.send_personal_message(
                    client_id, 
                    {"type": MESSAGE_TYPES["ERROR"], "payload": {"message": f"Invalid JSON: {str(e)}"}}
                )
            except Exception as e:
                print(f"WebSocket error processing message: {str(e)}")  # Debug log
                await manager.send_personal_message(
                    client_id, 
                    {"type": MESSAGE_TYPES["ERROR"], "payload": {"message": f"Error processing message: {str(e)}"}}
                )
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Unexpected WebSocket error: {str(e)}")
        manager.disconnect(client_id)

# Custom event handler for agent events
async def handle_agent_event(event, session_id, client_id, step_number):
    """Process an agent event and send updates to the client"""
    
    # Handle screenshot updates
    if "format_elements" in event and "img" in event["format_elements"]:
        image = event["format_elements"]["img"]
        await manager.send_personal_message(
            client_id,
            {
                "type": MESSAGE_TYPES["SCREENSHOT_UPDATE"],
                "payload": {
                    "session_id": session_id,
                    "screenshot": image,
                    "step": step_number
                }
            }
        )
    
    # Handle agent actions
    if "agent" in event:
        pred = event["agent"].get("prediction") or {}
        action = pred.action if hasattr(pred, "action") else None
        action_input = pred.args if hasattr(pred, "args") else None
        
        if action:
            # Send action update to client
            action_message = {
                "type": MESSAGE_TYPES["ACTION_UPDATE"],
                "payload": {
                    "session_id": session_id,
                    "action": action,
                    "args": action_input,
                    "step": step_number
                }
            }
            
            # Add screenshot if available
            if "format_elements" in event and "img" in event["format_elements"]:
                action_message["payload"]["screenshot"] = event["format_elements"]["img"]
                
            await manager.send_personal_message(client_id, action_message)

# Handle human intervention requests
async def request_human_intervention(message, session_id, client_id, screenshot=None):
    """Request human input and return the response"""
    
    # Create a future to store the response
    future = asyncio.Future()
    
    # Store the callback that will resolve the future
    async def callback(response):
        future.set_result(response)
    
    # Register the callback
    intervention_callbacks[session_id] = callback
    
    # Send intervention request to client
    await manager.send_personal_message(
        client_id,
        {
            "type": MESSAGE_TYPES["HUMAN_INTERVENTION_REQUEST"],
            "payload": {
                "session_id": session_id,
                "message": message,
                "screenshot": screenshot
            }
        }
    )
    
    # Wait for the response
    return await future

# Process a single session with enhanced event handling
async def process_session(session_id: str):
    request = active_sessions.get(session_id)
    client_id = manager.get_client_for_session(session_id)
    
    if not request or not client_id:
        return
    
    playwright = None
    context = None
    page = None
    
    try:
        # Initialize browser
        playwright, context, page = await initialize_browser()
        
        # Prepare config
        if not request.config:
            request.config = {}
        
        # Add custom event handler
        steps = []
        
        # Custom event handler function that integrates with WebSockets
        async def custom_event_handler(event):
            step_number = len(steps)
            
            # Process event directly (similar to run_agent logic but sending events to client)
            if "__interrupt__" in event:
                interrupt_info = event["__interrupt__"][0]
                message = interrupt_info.value
                
                # Get screenshot if available
                screenshot = None
                if "format_elements" in event and "img" in event["format_elements"]:
                    screenshot = event["format_elements"]["img"]
                
                # Request human intervention
                user_input = await request_human_intervention(message, session_id, client_id, screenshot)
                
                # Return a Command to resume execution
                from langgraph.types import Command
                return Command(resume=user_input)
            
            # Otherwise, process normal event updates
            await handle_agent_event(event, session_id, client_id, step_number)
            
            if "agent" in event:
                pred = event["agent"].get("prediction") or {}
                action = pred.action if hasattr(pred, "action") else None
                action_input = pred.args if hasattr(pred, "args") else None
                
                if action:
                    # Add to steps for tracking
                    steps.append(f"{len(steps) + 1}. {action}: {action_input}")
            
            # Return None to continue normal processing
            return None
        
        # Add the custom event handler to config
        request.config["event_handler"] = custom_event_handler
        
        # Process the request with direct run_agent call
        final_answer = await run_agent(
            page=page,
            query=request.query,
            config=request.config,
            testing=request.testing,
            test_actions=request.test_actions,
            human_intervention=request.human_intervention
        )
        
        # Store the result
        session_results[session_id] = final_answer
        # Remove from active sessions
        del active_sessions[session_id]
        
        # Send completion notification via WebSocket
        await manager.send_personal_message(
            client_id,
            {
                "type": MESSAGE_TYPES["SESSION_COMPLETED"],
                "payload": {"session_id": session_id, "result": final_answer}
            }
        )
        
    except Exception as e:
        # Store the error
        error_message = str(e)
        session_results[session_id] = {"error": error_message}
        # Remove from active sessions
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        # Send error notification via WebSocket
        if client_id:
            await manager.send_personal_message(
                client_id,
                {
                    "type": MESSAGE_TYPES["ERROR"],
                    "payload": {"session_id": session_id, "message": error_message}
                }
            )
    finally:
        # Clean up browser resources
        await close_browser(playwright, context)

# Keep existing REST API endpoints for backward compatibility...

# --- Keep existing REST API endpoints for backward compatibility ---

@app.post("/api/query", response_class=JSONResponse)
async def process_query(request: QueryRequest):
    """Process a query through the agent and return a session ID"""
    # Generate a unique session ID
    session_id = str(uuid.uuid4())
    
    # Store the request in active sessions
    active_sessions[session_id] = request
    
    # Create background task to process the session
    asyncio.create_task(process_session(session_id))
    
    # Return the session ID immediately
    return JSONResponse(content={"session_id": session_id, "status": "processing"})

@app.get("/api/session/{session_id}/status", response_class=JSONResponse)
async def get_session_status(session_id: str):
    """Get the status of a session"""
    if session_id not in active_sessions and session_id not in session_results:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_id in session_results:
        return JSONResponse(content={"status": "completed", "result": session_results[session_id]})
    
    return JSONResponse(content={"status": "processing"})

@app.post("/api/session/process")
async def process_sessions(background_tasks: BackgroundTasks):
    """Process any pending sessions in the background"""
    for session_id in list(active_sessions.keys()):
        background_tasks.add_task(process_session, session_id)
    return {"status": "processing sessions"}

# async def process_pending_sessions():
#     """Process all pending sessions - replaced by individual session processing"""
#     pass  # No longer used, kept for reference

# Setup HTTPS for secure WebSocket (wss://)
def setup_https():
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
        certfile="/path/to/cert.pem",  # Replace with your certificate path
        keyfile="/path/to/key.pem",    # Replace with your private key path
    )
    return ssl_context

if __name__ == "__main__":
    # For development, use standard HTTP/WS
    # uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
    
    # For production with HTTPS/WSS, uncomment these lines and configure your certificates
    # ssl_context = setup_https()
    # uvicorn.run(
    #     "backend:app", 
    #     host="0.0.0.0", 
    #     port=8000, 
    #     ssl_certfile="/path/to/cert.pem",
    #     ssl_keyfile="/path/to/key.pem"
    # )
    
    # For simplicity in development
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
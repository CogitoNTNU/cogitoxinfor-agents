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

# Add this to include graph directory for local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use direct imports from the graph module
from graph.main import test_agent

app = FastAPI(title="LLM Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000", "*"],  # Your Next.js frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Message types - keep in sync with frontend
MESSAGE_TYPES = {
    "SEND_QUERY": "SEND_QUERY",
    "SESSION_UPDATE": "SESSION_UPDATE",
    "SESSION_COMPLETED": "SESSION_COMPLETED",
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
                    session_id = client_id
                    manager.register_session(client_id, session_id)
                    
                    # Create request object
                    request = QueryRequest(
                        query=query,
                        testing=payload.get("testing", False),
                        test_actions=payload.get("test_actions"),
                        human_intervention=payload.get("human_intervention", False),
                        config=payload.get("config")
                    )
                    
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

# Process a single session and send updates via WebSocket
async def process_session(session_id: str):
    request = active_sessions.get(session_id)
    client_id = manager.get_client_for_session(session_id)
    
    if not request or not client_id:
        return
    
    try:
        print("request: ", request)
        # Process the request with the agent
        result = await test_agent(
            query=request.query,
            testing=request.testing,
            test_actions=request.test_actions,
            human_intervention=request.human_intervention,
            config=request.config
        )
        
        # Store the result
        session_results[session_id] = result
        # Remove from active sessions
        del active_sessions[session_id]
        
        # Send completion notification via WebSocket
        await manager.send_personal_message(
            client_id,
            {
                "type": MESSAGE_TYPES["SESSION_COMPLETED"],
                "payload": {"session_id": session_id, "result": result}
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
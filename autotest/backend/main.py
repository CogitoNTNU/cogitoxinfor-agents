import asyncio
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from queue import Queue
from threading import Lock
from typing import Any, Dict, Optional
import json
from datetime import datetime, timezone
import uuid

import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
#!/usr/bin/env python3

import requests
from dotenv import load_dotenv
from pyobjtojson import obj_to_json

# Load environment variables (for API keys)
load_dotenv()
from browser_use import Agent

# Start API server at application init time
import subprocess
import sys
import threading

def start_api_server():
    subprocess.Popen(
        [sys.executable, "api.py"],
        cwd=os.path.dirname(__file__)
    )
    print("Started api.py server in background")

# Start API server in a background thread
threading.Thread(target=start_api_server, daemon=True).start()
# Wait a moment for the server to start
time.sleep(1)

# Create logs and recordings directories if they don't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), 'recordings')
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RECORDINGS_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a rotating file handler (10MB per file, keep 5 backup files)
file_handler = RotatingFileHandler(
	os.path.join(LOGS_DIR, 'agent_manager.log'),
	maxBytes=10 * 1024 * 1024,  # 10MB
	backupCount=5,
	encoding='utf-8',
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Create a separate file for agent-specific logs
agent_file_handler = RotatingFileHandler(
	os.path.join(LOGS_DIR, 'agents.log'),
	maxBytes=10 * 1024 * 1024,  # 10MB
	backupCount=5,
	encoding='utf-8',
)
agent_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create a queue for real-time log messages
log_queue = Queue()
log_lock = Lock()

# Create a queue for real-time screenshot messages
screenshot_queue = Queue()
screenshot_lock = Lock()

from pathlib import Path

class LogHandler(logging.Handler):
    def __init__(self, agent_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent_id = agent_id
        
        # Ensure data directory exists
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
        
    def emit(self, record):
        # Format the log entry
        log_entry = self.format(record)
        
        # Put in queue for streaming (existing functionality)
        with log_lock:
            log_queue.put(log_entry)
        
        # Save to file
        try:
            # Determine agent ID (from instance or try to parse from message)
            agent_id = self.agent_id
            if not agent_id and hasattr(record, 'msg'):
                # Try to extract agent ID from message if it matches pattern
                # This is a fallback and might need adjustment based on log format
                msg = str(record.msg)
                if "Agent " in msg and ":" in msg:
                    agent_id = msg.split("Agent ")[1].split(":")[0].strip()
            
            agent_id = agent_id or "general"
            
            # Create directory structure
            agent_dir = self.data_dir / agent_id
            agent_dir.mkdir(exist_ok=True)
            
            logs_dir = agent_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Get current date for log file naming
            current_date = datetime.now().strftime("%Y-%m-%d")
            log_file = logs_dir / f"{current_date}.log"
            
            # Append log entry to file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{log_entry}\n")
                
        except Exception as e:
            # Don't let log saving errors propagate
            print(f"Error saving log to file: {e}")


# Add handlers to the browser_use logger
browser_use_logger = logging.getLogger('browser_use')
browser_use_logger.setLevel(logging.INFO)
browser_use_logger.addHandler(LogHandler())
browser_use_logger.addHandler(agent_file_handler)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allows all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allows all methods
    allow_headers=['*'],  # Allows all headers
)

# Create directories if they don't exist
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Import required modules for screenshot handling
import base64
from pathlib import Path
import json

# Define and create screenshots directory
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Mount static directories
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
app.mount('/screenshots', StaticFiles(directory=SCREENSHOTS_DIR), name='screenshots')
from pydantic import BaseModel

class RunRequest(BaseModel):
    query: str

from agent_manager import AgentManager
# Create a singleton instance
agent_manager = AgentManager()

def send_agent_history_step(data):
    """Send the agent step data to the recording API"""
    url = "http://127.0.0.1:9000/post_agent_history_step"
    response = requests.post(url, json=data)
    return response.json()

def setup_agent_logger(agent_id):
    """Create and configure a logger for a specific agent"""
    # Create a logger with the agent's ID as the name
    agent_logger = logging.getLogger(f'agent.{agent_id}')
    agent_logger.setLevel(logging.INFO)
    
    # Create a log handler for this specific agent
    agent_log_handler = LogHandler(agent_id=agent_id)
    agent_log_handler.setFormatter(logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'))
    agent_logger.addHandler(agent_log_handler)
    
    # Also add the file handler for all agent logs
    agent_logger.addHandler(agent_file_handler)
    
    return agent_logger


# --- Action logger for browser actions as JSON ---
def record_activity_after(agent_id: str):
    """Returns an async callback that logs each action using the recording API."""
    async def action_logger(agent):
        try:
            print(f'--- ON_STEP_END HOOK for agent {agent_id} ---')
            setup_agent_logger(agent_id)
            # Get state and history objects
            state = agent.state
            history = state.history
            
            # Skip if no history or empty history
            if not history or not history.history:
                logger.warning(f"Agent {agent_id}: No history available")
                return
                
            # Get the latest history entry
            last_entry = history.history[-1]
            step_number = len(history.history)
            
            # Log basic step info
            browser_logger = logging.getLogger('browser_use')
            url = last_entry.state.url if hasattr(last_entry.state, "url") else "No URL"
            title = last_entry.state.title if hasattr(last_entry.state, "title") else "No title"
            browser_logger.info(f"Step {step_number:03d} → {url} ({title!r})")
            
            # Extract screenshot and handle streaming queue
            screenshot_data = None
            if hasattr(last_entry.state, "screenshot"):
                screenshot_data = last_entry.state.screenshot
                
                if screenshot_data:
                    # We'll still maintain the streaming queue for UI updates
                    with screenshot_lock:
                        screenshot_queue.put({
                            "agent_id": agent_id,
                            "step": step_number,
                            "data": screenshot_data
                        })
            
            # Process data for API submission
            result = last_entry.result[-1] if hasattr(last_entry, "result") and last_entry.result else None
            actions = []
            brain = None
            
            if hasattr(last_entry, "model_output") and last_entry.model_output:
                # Extract actions
                if hasattr(last_entry.model_output, "action"):
                    actions = obj_to_json(
                        obj=[a for a in last_entry.model_output.action]
                    )
                
                # Get brain state
                if hasattr(last_entry.model_output, "current_state"):
                    brain = last_entry.model_output.current_state
            
            # Build step summary to send to API
            model_step_summary = {
                "agent_id": agent_id,
                "event_type": "post_step",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step_number": step_number,
                "url": url,
                "title": title,
                "website_screenshot": screenshot_data,
                "website_html": None,  # Not capturing HTML in this hook
                "actions": actions,
                "brain_state": {
                    "memory": brain.memory if brain and hasattr(brain, "memory") else None,
                    "next_goal": brain.next_goal if brain and hasattr(brain, "next_goal") else None
                },
                "result": {
                    "success": result.error is None if result else False,
                    "error": result.error if result and hasattr(result, "error") else None
                }
            }
            
            # Send data to the API
            result = send_agent_history_step(data=model_step_summary)
            print(f"Recording API response: {result}")
                
        except Exception as e:
            # Robust exception handling
            logger.error(f"Error in post-step hook for agent {agent_id}: {str(e)}", exc_info=True)
    
    return action_logger

def record_activity_before(agent_id: str):
    """Returns an async callback that logs agent state before each step."""
    async def before_step_hook(agent):
        try:
            print(f'--- ON_STEP_START HOOK for agent {agent_id} ---')
            
            website_html = None
            website_screenshot = None
            
            # Make sure we have state history
            if not hasattr(agent, "state") or not agent.state:
                logger.warning(f"Agent {agent_id}: No state available")
                return
                
            history = agent.state.history
            if not history:
                logger.warning(f"Agent {agent_id}: No history available")
                return
            
            # Process model data
            model_thoughts = obj_to_json(obj=history.model_thoughts())
            model_thoughts_last_elem = model_thoughts[-1] if model_thoughts else None
            
            model_outputs = obj_to_json(obj=history.model_outputs())
            model_outputs_last_elem = model_outputs[-1] if model_outputs else None
            
            model_actions = obj_to_json(obj=history.model_actions())
            model_actions_last_elem = model_actions[-1] if model_actions else None
            
            extracted_content = obj_to_json(obj=history.extracted_content())
            extracted_content_last_elem = extracted_content[-1] if extracted_content else None
            
            urls = obj_to_json(obj=history.urls())
            urls_last_elem = urls[-1] if urls else None
            
            # Create a summary of all data for this step
            model_step_summary = {
                "agent_id": agent_id,
                "event_type": "pre_step",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step_number": len(history.history) if history.history else 0,
                "website_html": website_html,
                "website_screenshot": website_screenshot,
                "url": urls_last_elem,
                "model_thoughts": model_thoughts_last_elem,
                "model_outputs": model_outputs_last_elem,
                "model_actions": model_actions_last_elem,
                "extracted_content": extracted_content_last_elem
            }
            
            print("--- MODEL STEP SUMMARY ---")
            print(f"URL: {urls_last_elem}")
            
            # Send data to the API
            result = send_agent_history_step(data=model_step_summary)
            print(f"Recording API response: {result}")
            
        except Exception as e:
            logger.error(f"Error in pre-step hook for agent {agent_id}: {str(e)}", exc_info=True)
            
    return before_step_hook

@app.get('/')
async def read_root():
	return FileResponse(os.path.join(STATIC_DIR, 'index.html'))


@app.post('/agent/{agent_id}/run')
async def run_agent(agent_id: str, request: RunRequest):
    """
    Create (always fresh) and start an agent with the given query.
    """
    try:
        start_time = time.time()
        # If an agent already exists, stop and remove it so we start fresh
        if agent_id in agent_manager.agents:
            try:
                agent_manager.get_agent(agent_id).stop()
            except Exception:
                pass
            agent_manager.agents.pop(agent_id)

        # Create a brand-new agent with this query
        await agent_manager.create_agent(agent_id, request.query)

        agent = agent_manager.get_agent(agent_id)
        agent_manager.set_running(agent_id, True)

        # Kick off the browser‐automation in the background
        task = asyncio.create_task(
            agent.run(
                on_step_end=record_activity_after(agent_id),
                on_step_start=record_activity_before(agent_id),
                ))

        setup_time = time.time() - start_time
        return {
            'status': 'running',
            'agent_id': agent_id,
            'query': request.query,
            'setup_time_ms': setup_time * 1000,
            'total_agents': len(agent_manager.agents),
        }
    except Exception as e:
        logger.error(f'Error running agent {agent_id}: {str(e)}')
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/ping')
async def ping():
	return {'status': 'ok'}


@app.post('/agent/{agent_id}/pause')
async def pause_agent(agent_id: str):
	try:
		agent = agent_manager.get_agent(agent_id)
		agent.pause()
		return {'status': 'paused', 'agent_id': agent_id}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@app.post('/agent/{agent_id}/resume')
async def resume_agent(agent_id: str):
	try:
		agent = agent_manager.get_agent(agent_id)
		agent.resume()
		return {'status': 'resumed', 'agent_id': agent_id}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@app.post('/agent/{agent_id}/stop')
async def stop_agent(agent_id: str):
    try:
        agent = agent_manager.get_agent(agent_id)
        
        # Now stop the agent
        agent.stop()
        agent_manager.set_running(agent_id, False)
        
        return {'status': 'stopped', 'agent_id': agent_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get('/agent/{agent_id}/status')
async def get_agent_status(agent_id: str):
	try:
		status = agent_manager.get_agent_status(agent_id)
		task = agent_manager.agents[agent_id]['task'] if agent_id in agent_manager.agents else None
		return {'status': status, 'agent_id': agent_id, 'task': task}
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))

@app.get('/agents')
async def list_agents():
	"""Return a dict of {agent_id: {task, status}}."""
	return agent_manager.list_agents()


# Create a new agent and register it without running
@app.post('/agent')
async def create_agent():
    """Create a new agent and register it without running."""
    # Generate a unique agent ID
    new_id = str(uuid.uuid4())
    # Create the agent with an empty initial task
    await agent_manager.create_agent(new_id, "")
    return {"agent_id": new_id}
            
@app.get('/agent/{agent_id}/history')
async def get_agent_history(agent_id: str, save_screenshots: bool = True):
    """Get agent history information including screenshot count"""
    try:
        agent = agent_manager.get_agent(agent_id)
        
        if hasattr(agent, "history") and agent.history and agent.history.history:
            history_info = {
                "step_count": len(agent.history.history),
                "steps": [],
                "events": [],
                "final_answer": getattr(agent, "final_answer", None) if hasattr(agent, "final_answer") else None
            }
            
            # Extract events if available
            if hasattr(agent.history, "model_actions") and callable(agent.history.model_actions):
                history_info["events"].extend([
                    {"type": "model_action", "payload": action} 
                    for action in agent.history.model_actions()
                ])
                
            if hasattr(agent.history, "errors") and callable(agent.history.errors):
                history_info["events"].extend([
                    {"type": "error", "payload": error} 
                    for error in agent.history.errors()
                ])
            
            # Add summary information for each step
            for i, step in enumerate(agent.history.history):
                goal = step.model_output.current_state.next_goal if hasattr(step, "model_output") and step.model_output else "No goal available"
                
                # Save screenshot if available and requested
                screenshot_url = None
                if save_screenshots and hasattr(step, "state") and hasattr(step.state, "screenshot") and step.state.screenshot:
                    screenshot_url = agent_manager.save_agent_screenshot(agent_id, step.state.screenshot, i)
                
                step_info = {
                    "step_number": i,
                    "has_screenshot": hasattr(step, "state") and hasattr(step.state, "screenshot") and step.state.screenshot is not None,
                    "screenshot_url": screenshot_url,
                    "url": step.state.url if hasattr(step.state, "url") else None,
                    "title": step.state.title if hasattr(step.state, "title") else None,
                    "goal": goal
                }
                history_info["steps"].append(step_info)
                
            return history_info
        
        return {"step_count": 0, "steps": [], "events": []}
    except Exception as e:
        logger.error(f"Error getting history for {agent_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Per-agent SSE stream endpoint
@app.get('/agent/{agent_id}/stream')
async def agent_stream(request: Request, agent_id: str):
    """
    SSE stream of logs and screenshots filtered by agent_id.
    """
    async def event_generator():
        while True:
            # If client disconnects, stop the loop
            if await request.is_disconnected():
                break

            # Stream log entries
            if not log_queue.empty():
                with log_lock:
                    while not log_queue.empty():
                        log_entry = log_queue.get()
                        yield {'event': 'log', 'data': log_entry}

            # Stream screenshot entries for this agent
            if not screenshot_queue.empty():
                with screenshot_lock:
                    while not screenshot_queue.empty():
                        msg = screenshot_queue.get()
                        if msg.get('agent_id') == agent_id:
                            yield {'event': 'screenshot', 'data': json.dumps(msg)}

            await asyncio.sleep(0.1)

    return EventSourceResponse(event_generator())


@app.get('/system/stats')
async def get_system_stats():
	return agent_manager.get_system_stats()


if __name__ == '__main__':


    import uvicorn

    uvicorn.run(app, host='0.0.0.0', port=8000)

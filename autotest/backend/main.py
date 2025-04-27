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


class LogHandler(logging.Handler):
	def emit(self, record):
		log_entry = self.format(record)
		with log_lock:
			log_queue.put(log_entry)


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


# --- Action logger for browser actions as JSON ---
def record_activity_after(agent_id: str):
    """Returns an async callback that logs each action as JSON to logs/browser_actions.log."""
    async def action_logger(agent):
        try:
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
            
            # Log step info (URL/title)
            browser_logger = logging.getLogger('browser_use')
            url = last_entry.state.url if hasattr(last_entry.state, "url") else "No URL"
            title = last_entry.state.title if hasattr(last_entry.state, "title") else "No title"
            browser_logger.info(f"Step {step_number:03d} → {url} ({title!r})")
            
            # Handle screenshot (if present)
            screenshot_data = None
            if hasattr(last_entry.state, "screenshot"):
                screenshot_data = last_entry.state.screenshot
                
                if screenshot_data:
                    # Save screenshot to file
                    agent_dir = Path(SCREENSHOTS_DIR) / agent_id
                    agent_dir.mkdir(parents=True, exist_ok=True)
                    img = base64.b64decode(screenshot_data)
                    path = agent_dir / f"step_{step_number:03d}.png"
                    with open(path, 'wb') as f:
                        f.write(img)
                    
                    # Add to streaming queue
                    with screenshot_lock:
                        screenshot_queue.put({
                            "agent_id": agent_id,
                            "step": step_number,
                            "data": screenshot_data
                        })
            
            # Record action information (similar to record_activity_after)
            if hasattr(last_entry, "model_output") and last_entry.model_output:
                result = last_entry.result[-1] if last_entry.result else None
                
                # Build action payloads
                actions = []
                if hasattr(last_entry.model_output, "action"):
                    actions = [a.model_dump(exclude_none=True) for a in last_entry.model_output.action]
                
                # Get brain state
                brain = last_entry.model_output.current_state if hasattr(last_entry.model_output, "current_state") else None
                
                # Construct log record (safely check for attributes)
                record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "step": step_number,
                    "url": url,
                    "memory": brain.memory if brain and hasattr(brain, "memory") else None,
                    "next_goal": brain.next_goal if brain and hasattr(brain, "next_goal") else None,
                    "actions": actions,
                    "success": result.error is None if result else False,
                    "error": result.error if result else None
                }
                
                # Write to log file
                log_path = os.path.join(LOGS_DIR, 'browser_actions.log')
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(record) + '\n')
                    
        except Exception as e:
            # Robust exception handling
            logger.error(f"Error in unified callback: {str(e)}", exc_info=True)
    return action_logger

def send_agent_history_step(data):
    """Send the agent step data to the recording API"""
    url = "http://127.0.0.1:9000/post_agent_history_step"
    response = requests.post(url, json=data)
    return response.json()


async def record_activity_before(agent_obj):
    """Hook function that captures and records agent activity at each step"""
    website_html = None
    website_screenshot = None
    urls_json_last_elem = None
    model_thoughts_last_elem = None
    model_outputs_json_last_elem = None
    model_actions_json_last_elem = None
    extracted_content_json_last_elem = None

    print('--- ON_STEP_START HOOK ---')
    
    # Capture current page state
    #website_html = await agent_obj.browser_context.get_page_html()
    #website_screenshot = await agent_obj.browser_context.take_screenshot()

    # Make sure we have state history
    if hasattr(agent_obj, "state"):
        history = agent_obj.state.history
    else:
        history = None
        print("Warning: Agent has no state history")
        return

    # Process model thoughts
    model_thoughts = obj_to_json(
        obj=history.model_thoughts(),
    )
    if len(model_thoughts) > 0:
        model_thoughts_last_elem = model_thoughts[-1]

    # Process model outputs
    model_outputs = agent_obj.state.history.model_outputs()
    model_outputs_json = obj_to_json(
        obj=model_outputs,
    )
    if len(model_outputs_json) > 0:
        model_outputs_json_last_elem = model_outputs_json[-1]

    # Process model actions
    model_actions = agent_obj.state.history.model_actions()
    model_actions_json = obj_to_json(
        obj=model_actions,
    )
    if len(model_actions_json) > 0:
        model_actions_json_last_elem = model_actions_json[-1]

    # Process extracted content
    extracted_content = agent_obj.state.history.extracted_content()
    extracted_content_json = obj_to_json(
        obj=extracted_content,
    )
    if len(extracted_content_json) > 0:
        extracted_content_json_last_elem = extracted_content_json[-1]

    # Process URLs
    urls = agent_obj.state.history.urls()
    urls_json = obj_to_json(
        obj=urls,
    )
    if len(urls_json) > 0:
        urls_json_last_elem = urls_json[-1]

    # Create a summary of all data for this step
    model_step_summary = {
        "website_html": website_html,
        "website_screenshot": website_screenshot,
        "url": urls_json_last_elem,
        "model_thoughts": model_thoughts_last_elem,
        "model_outputs": model_outputs_json_last_elem,
        "model_actions": model_actions_json_last_elem,
        "extracted_content": extracted_content_json_last_elem
    }

    print("--- MODEL STEP SUMMARY ---")
    print(f"URL: {urls_json_last_elem}")
    
    # Send data to the API
    result = send_agent_history_step(data=model_step_summary)
    print(f"Recording API response: {result}")


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
                on_step_start=record_activity_before,
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
    import subprocess
    import sys
    import time

#    # Start api.py as a subprocess
#    api_proc = subprocess.Popen(
#        [sys.executable, "api.py"],
#        cwd=os.path.dirname(__file__)
#    )
#    print("Started api.py subprocess")
#
#    # Optional: Wait a bit to ensure api.py is up before starting main FastAPI
#    time.sleep(1)

    import uvicorn
    #try:
    uvicorn.run(app, host='0.0.0.0', port=8000)
    #finally:
        # Terminate api.py when main.py exits
        #api_proc.terminate()
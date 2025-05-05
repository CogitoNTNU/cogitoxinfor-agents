import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional
import json
from datetime import datetime, timezone
import uuid
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

# Logger setup must come before any use of logger in start_api_server
from logging_setup import get_logger
logger = get_logger(__name__)

def start_api_server():
    try:
        process = subprocess.Popen(
            [sys.executable, "api.py"],
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Don't wait for communicate here as it would block the thread
        # Just log that we've started the process
        logger.info("API server process started")
        
        # Start a monitoring thread to capture output
        def monitor_process():
            try:
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    logger.error(f"API server exited with code {process.returncode}: {stderr.decode()}")
                else:
                    logger.info("API server exited normally")
            except Exception as e:
                logger.error(f"Error monitoring API server: {str(e)}")
                
        threading.Thread(target=monitor_process, daemon=True).start()
    except Exception as e:
        logger.error(f"Error starting API server: {str(e)}")

# Start API server in a background thread
threading.Thread(target=start_api_server, daemon=True).start()
# Wait a moment for the server to start
time.sleep(2)  # Increased wait time to give the server more time to initialize

from logging_setup import (
    log_queue, log_lock, screenshot_queue, screenshot_lock,
    setup_agent_logger, set_current_agent_id, STATIC_DIR,
)


app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # Allows all origins
    allow_credentials=True,
    allow_methods=['*'],  # Allows all methods
    allow_headers=['*'],  # Allows all headers
)


# Mount static directories
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
#app.mount('/screenshots', StaticFiles(directory=SCREENSHOTS_DIR), name='screenshots')

from pydantic import BaseModel

class RunRequest(BaseModel):
    query: str
    infor_mode: bool = False

from agent_manager import AgentManager
# Create a singleton instance
agent_manager = AgentManager()

def send_agent_history_step(data):
    """Send the agent step data to the recording API"""
    url = "http://127.0.0.1:9000/post_agent_history_step"
    response = requests.post(url, json=data)
    return response.json()


# --- Action logger for browser actions as JSON ---
def record_activity_after(agent_id: str):
    """Returns an async callback that logs each action using the recording API."""
    async def action_logger(agent):
        try:
            print(f'--- ON_STEP_END HOOK for agent {agent_id} ---')
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
            # Use the same logger instance for all logs from this agent
            agent_logger = setup_agent_logger(agent_id)
            url = last_entry.state.url if hasattr(last_entry.state, "url") else "No URL"
            title = last_entry.state.title if hasattr(last_entry.state, "title") else "No title"
            agent_logger.info(f"Step {step_number:03d} → {url} ({title!r})")
            
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
            element_actions = []
            brain = None

            if hasattr(last_entry, "model_output") and last_entry.model_output:
                # Extract actions
                if hasattr(last_entry.model_output, "action"):
                    actions = obj_to_json(
                        obj=[a for a in last_entry.model_output.action]
                    )
                # Build structured element_actions for logging
                element_actions = []
                if hasattr(last_entry.model_output, "action"):
                    for i, action in enumerate(last_entry.model_output.action):
                        action_data = action.model_dump(exclude_unset=True) or {}
                        action_type = next(iter(action_data), None)
                        params = action_data.get(action_type, {}) if isinstance(action_data, dict) else {}
                        # Normalize action names (including navigation)
                        if action_type in ("click", "click_element_by_index"):
                            norm_action = "click"
                        elif action_type == "input_text":
                            norm_action = "fill"
                        elif action_type == "wait":
                            norm_action = "wait"
                        elif action_type == "go_to_url":
                            norm_action = "navigate"
                        else:
                            norm_action = action_type or "unknown"
                        # Timestamp and step
                        ts = datetime.now(timezone.utc).isoformat()
                        step = step_number
                        # Derive selector: extract element ID if available, otherwise use css_selector
                        selector = None
                        interacted = getattr(last_entry.state, "interacted_element", None)
                        if interacted and i < len(interacted) and interacted[i]:
                            el = interacted[i]
                            # For logging purposes, we want to extract just the ID
                            # But we need to preserve the original selector format for Playwright
                            
                            # First check if we can get the ID directly
                            if hasattr(el, "id") and el.id:
                                selector = el.id  # Use ID directly for Playwright compatibility
                            elif hasattr(el, "attributes") and el.attributes.get("id"):
                                selector = el.attributes['id']  # Use ID directly for Playwright compatibility
                            # If we have a CSS selector, try to extract ID from it
                            elif hasattr(el, "css_selector") and el.css_selector:
                                # Look for [id="..."] pattern in the selector
                                import re
                                id_match = re.search(r'\[id=["\']([^"\']+)["\']', el.css_selector)
                                if id_match:
                                    # Extract just the ID for logging
                                    selector = id_match.group(1)
                                else:
                                    # If no ID found in selector, use the full selector
                                    selector = el.css_selector
                        # Build record
                        rec = {"step": step, "timestamp": ts, "action": norm_action}
                        if selector:
                            rec["selector"] = selector
                        # Populate action-specific fields
                        if norm_action == "click":
                            rec["button"] = params.get("button", "left")
                            rec["click_count"] = params.get("click_count", 1)
                        elif norm_action == "wait" and isinstance(params.get("seconds"), (int, float)):
                            rec["timeout"] = int(params["seconds"] * 1000)
                        elif norm_action == "fill" and isinstance(params.get("text"), str):
                            rec["text"] = params["text"]
                        elif norm_action == "navigate":
                            url = params.get("url")
                            if isinstance(url, str):
                                rec["url"] = url
                        element_actions.append(rec)
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
                "element_actions": element_actions,  # New field with element details
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
            
            # Also save element actions in message_output.txt format
            save_element_actions(element_actions, agent_id)
                
        except Exception as e:
            # Robust exception handling
            logger.error(f"Error in post-step hook for agent {agent_id}: {str(e)}", exc_info=True)

    return action_logger


# Helper function to save element actions in the same format as message_output.txt
def save_element_actions(element_actions, agent_id):
    try:
        # Ensure directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Save to file in the format of message_output.txt
        with open(f"logs/{agent_id}_actions.txt", "a") as f:
            for action in element_actions:
                f.write(json.dumps(action) + "\n")
    except Exception as e:
        logger.error(f"Error saving element actions: {str(e)}")





def record_activity_before(agent_id: str):
    """Returns an async callback that logs agent state before each step."""
    # Get a single logger instance for this agent
    agent_logger = setup_agent_logger(agent_id)
    
    async def before_step_hook(agent):
        try:
            print(f'--- ON_STEP_START HOOK for agent {agent_id} ---')
            
            website_html = None
            website_screenshot = None
            
            # Make sure we have state history
            if not hasattr(agent, "state") or not agent.state:
                agent_logger.warning(f"No state available")
                return
                
            history = agent.state.history
            if not history:
                agent_logger.warning(f"No history available")
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
        set_current_agent_id(agent_id)
        start_time = time.time()
        # If an agent already exists, stop and remove it so we start fresh
        if agent_id in agent_manager.agents:
            try:
                agent_manager.get_agent(agent_id).stop()
            except Exception:
                pass
            agent_manager.agents.pop(agent_id)

        # Create a brand-new agent with this query
        # Pass infor_mode to create_agent
        mode = "infor" if request.infor_mode else "regular"
        await agent_manager.create_agent(agent_id, request.query, mode)

        agent = agent_manager.get_agent(agent_id)
        agent_manager.set_running(agent_id, True)

        # Kick off the browser‐automation in the background
        task = asyncio.create_task(
            agent.run(
                on_step_start=record_activity_before(agent_id),
                on_step_end=record_activity_after(agent_id),
                ))

        setup_time = time.time() - start_time
        return {
            'status': 'running',
            'agent_id': agent_id,
            'query': request.query,
            'infor_mode': request.infor_mode,
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
    await agent_manager.create_agent(new_id, "", "regular")
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
    # Set to track log hashes that have been sent to this client
    # to prevent duplicate logs even across reconnections
    sent_log_hashes = set()
    
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
                        
                        # Parse the log entry to check for agent_id and log_hash
                        try:
                            # Try to parse as JSON
                            entry_data = json.loads(log_entry)
                            
                            # Check if this log has already been sent to this client
                            log_hash = entry_data.get('log_hash')
                            if log_hash and log_hash in sent_log_hashes:
                                continue
                                
                            # Only send logs for this agent or general logs with no agent_id
                            if entry_data.get('agent_id') == agent_id or 'agent_id' not in entry_data:
                                # Mark this log as sent to this client
                                if log_hash:
                                    sent_log_hashes.add(log_hash)
                                yield {'event': 'log', 'data': log_entry}
                        except json.JSONDecodeError:
                            # If not JSON, assume it's a plain string and send it
                            # (this is a fallback for backward compatibility)
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

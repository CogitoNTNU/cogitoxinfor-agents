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

from logging_setup import (
    get_logger, log_queue, log_lock, screenshot_queue, screenshot_lock,
    setup_agent_logger, set_current_agent_id, STATIC_DIR,
)

# Then replace the logger initialization with:
logger = get_logger(__name__)


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
            logger = setup_agent_logger(agent_id)
            url = last_entry.state.url if hasattr(last_entry.state, "url") else "No URL"
            title = last_entry.state.title if hasattr(last_entry.state, "title") else "No title"
            logger.info(f"Step {step_number:03d} → {url} ({title!r})")
            
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
                    
                    # Extract element details for each action in message_output.txt format
                    for i, action in enumerate(last_entry.model_output.action):
                        action_data = action.model_dump(exclude_unset=True)
                        
                        # Get action type (click, input_text, etc.)
                        action_type = list(action_data.keys())[0] if action_data else None
                        
                        if not action_type:
                            continue
                            
                        # Get action parameters
                        params = action_data.get(action_type, {})
                        
                        # Extract element information
                        element_id = None
                        highlight_index = None
                        
                        # Extract different ways an element could be identified
                        if isinstance(params, dict):
                            element_id = params.get('html_id') or params.get('selector') or params.get('id')
                            highlight_index = params.get('highlight_index')
                        
                        # Create record for message_output.txt format
                        is_error = result.error is not None if result else True
                        element_action = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "action": action_type,
                            "element_id": element_id,
                            "success": not is_error,
                            "error": result.error if result and hasattr(result, "error") else None
                        }
                        
                        # If we have interacted elements from state, get more details
                        if hasattr(last_entry.state, "interacted_element") and last_entry.state.interacted_element:
                            interacted = last_entry.state.interacted_element
                            if i < len(interacted) and interacted[i]:
                                if not element_id and hasattr(interacted[i], "id"):
                                    element_id = interacted[i].id
                                    element_action["element_id"] = element_id
                                
                                if hasattr(interacted[i], "tag_name"):
                                    element_action["tag_name"] = interacted[i].tag_name
                                    
                                if hasattr(interacted[i], "attributes"):
                                    element_action["attributes"] = interacted[i].attributes
                                    
                                if hasattr(interacted[i], "highlight_index") and highlight_index is None:
                                    element_action["highlight_index"] = interacted[i].highlight_index
                        
                        element_actions.append(element_action)
                
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

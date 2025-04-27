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

from browser_use import Agent

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

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


class AgentManager:
	def __init__(self):
		self.agents: Dict[str, Dict[str, Any]] = {}
		self.max_agents = 40  # Increased to 100 agents
		self._lock = asyncio.Lock()
		self.process = psutil.Process()
		self.start_time = time.time()
		logger.info(f'AgentManager initialized with max_agents={self.max_agents}')

	async def create_agent(self, agent_id: str, task: str):
		async with self._lock:
			if len(self.agents) >= self.max_agents:
				current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
				logger.error(f'Max agents reached. Current memory usage: {current_memory:.2f}MB')
				raise ValueError(f'Maximum number of agents ({self.max_agents}) reached. Memory usage: {current_memory:.2f}MB')

			if agent_id in self.agents:
				logger.warning(f'Agent {agent_id} already exists')
				raise ValueError(f'Agent {agent_id} already exists')

			try:
				llm = ChatOpenAI(model='gpt-4o-mini')
				agent_instance = Agent(
					task=task,
					llm=llm,
					save_conversation_path="logs/conversation.json",
					register_new_step_callback=make_step_logger(agent_id)
				)
				agent = {
					'instance': agent_instance,
					'task': task,
					'running': False,
					'created_at': time.time(),
					'last_active': time.time(),
				}
				self.agents[agent_id] = agent
				logger.info(f'Created agent {agent_id}. Total agents: {len(self.agents)}')
			except Exception as e:
				logger.error(f'Failed to create agent {agent_id}: {str(e)}')
				raise

	def get_system_stats(self) -> dict:
		stats = {
			'total_agents': len(self.agents),
			'memory_usage_mb': self.process.memory_info().rss / 1024 / 1024,
			'cpu_percent': self.process.cpu_percent(),
			'uptime_seconds': time.time() - self.start_time,
			'thread_count': self.process.num_threads(),
		}
		logger.info(f'System stats: {stats}')
		return stats

	def get_agent(self, agent_id: str) -> Agent:
		if agent_id not in self.agents:
			raise ValueError(f'Agent {agent_id} not found')
		return self.agents[agent_id]['instance']

	def get_agent_status(self, agent_id: str):
		if agent_id not in self.agents:
			return 'not_created'

		try:
			agent_data = self.agents[agent_id]
			agent = agent_data['instance']

			if hasattr(agent, '_stopped') and agent._stopped:
				return 'stopped'
			elif hasattr(agent, '_paused') and agent._paused:
				return 'paused'
			elif agent_data.get('running', False):
				return 'running'
			return 'ready'
		except Exception as e:
			logger.error(f"Error checking agent status: {str(e)}")
			return 'error'

	def set_running(self, agent_id: str, value: bool):
		if agent_id in self.agents:
			self.agents[agent_id]['running'] = value

	def list_agents(self):
		return {
			agent_id: {'task': data['task'], 'status': self.get_agent_status(agent_id)} for agent_id, data in self.agents.items()
		}
		
	def save_agent_screenshot(self, agent_id: str, screenshot_data: str, step_number: int = None) -> str:
		"""Save a screenshot to disk and return the URL path"""
		# Create agent-specific directory
		agent_dir = Path(SCREENSHOTS_DIR) / agent_id
		agent_dir.mkdir(exist_ok=True)
		
		# Generate filename
		timestamp = time.strftime("%Y%m%d-%H%M%S")
		step_info = f"_step{step_number}" if step_number is not None else ""
		filename = f"{timestamp}{step_info}.png"
		filepath = agent_dir / filename
		
		if b64_to_png(screenshot_data, filepath):
			# Return the URL path that can be used by the frontend
			return f"/screenshots/{agent_id}/{filename}"
		return None

	def save_agent_history(self, agent_id: str, task: str):
		"""Save agent history to a file"""
		try:
			if agent_id not in self.agents:
				logger.warning(f"Cannot save history: Agent {agent_id} not found")
				return
				
			agent = self.agents[agent_id]['instance']
			
			# Make sure agent has history attribute
			if not hasattr(agent, "history") or not agent.history:
				logger.warning(f"Agent {agent_id} has no history to save")
				return
				
			# Create safe filename from agent_id and task (first 30 chars)
			safe_task = "".join(c if c.isalnum() else "_" for c in task[:30])
			filename = f"logs_{agent_id}_{safe_task}.txt"
			filepath = os.path.join(LOGS_DIR, filename)
			
			# Extract history components if available
			history = agent.history
			
			with open(filepath, "w", encoding="utf-8") as log_file:
				log_file.write(f"Agent ID: {agent_id}\n")
				log_file.write(f"Task: {task}\n")
				log_file.write(f"Run completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
				
				# Handle history methods similar to the example code
				if hasattr(history, "urls") and callable(history.urls):
					log_file.write("Visited URLs: " + str(history.urls()) + "\n")
				
				if hasattr(history, "screenshots") and callable(history.screenshots):
					log_file.write("Screenshots: " + str(history.screenshots()) + "\n")
					
				if hasattr(history, "action_names") and callable(history.action_names):
					log_file.write("Action names: " + str(history.action_names()) + "\n")
					
				if hasattr(history, "extracted_content") and callable(history.extracted_content):
					log_file.write("Extracted content: " + str(history.extracted_content()) + "\n")
					
				if hasattr(history, "errors") and callable(history.errors):
					log_file.write("Errors: " + str(history.errors()) + "\n")
					
				if hasattr(history, "model_actions") and callable(history.model_actions):
					log_file.write("Model actions: " + str(history.model_actions()) + "\n")
				
				# Also store raw history steps if available
				if hasattr(history, "history"):
					log_file.write("\n---- Detailed History Steps ----\n")
					for i, step in enumerate(history.history):
						log_file.write(f"\nStep {i}:\n")
						log_file.write(f"URL: {step.state.url if hasattr(step.state, 'url') else 'N/A'}\n")
						log_file.write(f"Title: {step.state.title if hasattr(step.state, 'title') else 'N/A'}\n")
						
						# Include goal if available
						if hasattr(step, "model_output") and step.model_output and hasattr(step.model_output.current_state, "next_goal"):
							log_file.write(f"Goal: {step.model_output.current_state.next_goal}\n")
				
			logger.info(f"Saved agent {agent_id} history to {filepath}")
			return filepath
			
		except Exception as e:
			logger.error(f"Error saving history for agent {agent_id}: {str(e)}")
			return None



# Create a singleton instance
agent_manager = AgentManager()

# Add near the top of the file with other directory creation
def b64_to_png(base64_str: str, output_path: Path) -> bool:
    """Convert base64 string to PNG file"""
    try:
        img_data = base64.b64decode(base64_str)
        with open(output_path, 'wb') as f:
            f.write(img_data)
        logger.info(f"Saved screenshot to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save screenshot: {str(e)}")
        return False

def make_step_logger(agent_id: str):
    """Returns a callback that logs each step and saves its screenshot."""
    def step_logger(state, output, step_number):
        # 1) Log URL/title
        logger = logging.getLogger('browser_use')
        logger.info(f"Step {step_number:03d} → {state.url} ({state.title!r})")
        # 2) Persist screenshot if present
        if state.screenshot:
            agent_dir = Path(SCREENSHOTS_DIR) / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            img = base64.b64decode(state.screenshot)
            path = agent_dir / f"step_{step_number:03d}.png"
            with open(path, 'wb') as f:
                f.write(img)
            # Also enqueue screenshot for live streaming
            with screenshot_lock:
                screenshot_queue.put({
                    "agent_id": agent_id,
                    "step": step_number,
                    "data": state.screenshot
                })
    return step_logger

# --- Action logger for browser actions as JSON ---
def make_action_logger(agent_id: str):
    """Returns an async callback that logs each action as JSON to logs/browser_actions.log."""
    async def action_logger(agent):
        history = agent.state.history
        if history.history:
            last = history.history[-1]
            result = last.result[-1]
            # Build full action payloads list
            actions = [a.model_dump(exclude_none=True) for a in last.model_output.action]
            # Retrieve agent brain state
            brain = last.model_output.current_state
            # Construct enriched log record
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step": len(history.history),
                "url": last.state.url,
                "memory": brain.memory,
                "next_goal": brain.next_goal,
                "actions": actions,
                "success": result.error is None,
                "error": result.error
            }
            log_path = os.path.join(LOGS_DIR, 'browser_actions.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record) + '\n')
    return action_logger

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
            agent.run(on_step_end=make_action_logger(agent_id))
        )

        # Add completion callback for debugging
        def done_callback(future):
            try:
                result = future.result()
                # Save history after agent completes (this saves more than just actions)
                agent_manager.save_agent_history(agent_id, request.query)
            except Exception as e:
                logger.error(f'Agent {agent_id} failed: {str(e)}')
            finally:
                agent_manager.set_running(agent_id, False)

        task.add_done_callback(done_callback)

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
        
        # Save the history BEFORE stopping the agent
        if agent_id in agent_manager.agents:
            task = agent_manager.agents[agent_id]['task'] 
            agent_manager.save_agent_history(agent_id, task)
        
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

@app.get('/agent/{agent_id}/screenshot')
async def get_agent_screenshot(agent_id: str, step: Optional[int] = None, save: bool = True):
    """Get the latest screenshot or a specific step's screenshot"""
    try:
        agent = agent_manager.get_agent(agent_id)
        
        # If agent has history
        if hasattr(agent, "history") and agent.history and agent.history.history:
            # If step is provided, get that specific step's screenshot
            if step is not None and 0 <= step < len(agent.history.history):
                screenshot_data = agent.history.history[step].state.screenshot
                step_num = step
            else:
                # Otherwise return the latest screenshot
                screenshot_data = agent.history.history[-1].state.screenshot
                step_num = len(agent.history.history) - 1
                
            if screenshot_data and save:
                agent_manager.save_agent_screenshot(agent_id, screenshot_data, step_num)
                
            if screenshot_data:
                return {"screenshot": screenshot_data, "step": step_num}
        
        # If we can't get a screenshot from history, try to take a new one
        # FIXED: Removed the use_vision parameter
        current_state = await agent.browser_context.get_state()
        if current_state and current_state.screenshot:
            screenshot_data = current_state.screenshot
            if save:
                agent_manager.save_agent_screenshot(agent_id, screenshot_data)
            return {"screenshot": screenshot_data, "step": -1}
            
        raise HTTPException(status_code=404, detail="No screenshot available")
    except Exception as e:
        logger.error(f"Error getting screenshot for {agent_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

            
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


@app.get('/logs')
async def event_stream():
    async def generate():
        while True:
            # Logs
            if not log_queue.empty():
                with log_lock:
                    while not log_queue.empty():
                        log_entry = log_queue.get()
                        yield {'event': 'log', 'data': log_entry}
            # Screenshots
            if not screenshot_queue.empty():
                with screenshot_lock:
                    while not screenshot_queue.empty():
                        msg = screenshot_queue.get()
                        # Send screenshot payload as JSON string
                        yield {'event': 'screenshot', 'data': json.dumps(msg)}
            await asyncio.sleep(0.1)

    return EventSourceResponse(generate())


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

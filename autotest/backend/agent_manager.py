import os
import asyncio
import logging
import time
from typing import Any, Dict
import psutil
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables (for API keys)
load_dotenv()
from browser_use import Agent
import base64
from pathlib import Path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define and create screenshots directory
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


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
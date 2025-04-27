import os
import asyncio
import time
from typing import Any, Dict
import psutil
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Load environment variables (for API keys)
load_dotenv()
from browser_use import Browser, BrowserConfig, Agent

# Import centralized logging
from logging_setup import get_logger, b64_to_png, PROFILES_DIR, get_agent_screenshot_path

# Initialize logger for this module
logger = get_logger(__name__)

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.max_agents = 40
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
                # Create agent-specific profile directory
                agent_profile_dir = os.path.join(PROFILES_DIR)
                os.makedirs(agent_profile_dir, exist_ok=True)
                
                # Configure browser with persistent profile
                browser_config = BrowserConfig(
                    headless=False,
                    disable_security=True,
                    extra_chromium_args=[f'--user-data-dir={agent_profile_dir}']
                )
                
                browser = Browser(config=browser_config)
                
                # Create the agent with this browser
                llm = ChatOpenAI(model='gpt-4.1-nano')
                agent_instance = Agent(
                    task=task,
                    llm=llm,
                    browser=browser  # Pass the configured browser
                )
                
                agent = {
                    'instance': agent_instance,
                    'task': task,
                    'running': False,
                    'created_at': time.time(),
                    'last_active': time.time(),
                }
                self.agents[agent_id] = agent
                logger.info(f'Created agent {agent_id} with persistent profile at {agent_profile_dir}. Total agents: {len(self.agents)}')
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
            agent_id: {'task': data['task'], 'status': self.get_agent_status(agent_id)} 
            for agent_id, data in self.agents.items()
        }
        
    def save_agent_screenshot(self, agent_id: str, screenshot_data: str, step_number: int = None) -> str:
        """Save a screenshot to disk and return the URL path"""
        filepath, url_path = get_agent_screenshot_path(agent_id, step_number)
        
        if b64_to_png(screenshot_data, filepath):
            # Return the URL path that can be used by the frontend
            return url_path
        return None
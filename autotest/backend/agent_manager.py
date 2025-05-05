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

    async def create_agent(self, agent_id: str, task: str, mode: str = "regular"):
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
                
                # Configure browser according to mode
                if mode == "infor":
                    browser_config = BrowserConfig(
                        chrome_instance_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                        headless=False,
                        disable_security=True,
                    )
                else:
                    browser_config = BrowserConfig(
                        headless=True,
                        disable_security=True,
                        extra_chromium_args=[f'--user-data-dir={agent_profile_dir}']
                    )
                
                browser = Browser(config=browser_config)
                
                llm = ChatOpenAI(model='gpt-4.1')

                if mode == "infor":
                    agent_instance = Agent(
                        task=task,
                        llm=llm,
                        browser=browser,  # Pass the configured browser
                        initial_actions=[
                            {'open_tab': {'url': 'https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b'}},
                            {'wait': {'seconds': 3}},
                            {'open_tab': {'url': 'https://m3prduse1b.m3.inforcloudsuite.com/mne/infor?HybridCertified=1&xfo=https%3A%2F%2Fmingle-portal.inforcloudsuite.com&SupportWorkspaceFeature=0&Responsive=All&enable_health_service=true&portalV2Certified=1&LogicalId=lid%3A%2F%2Finfor.m3.m3&inforThemeName=Light&inforThemeColor=amber&inforCurrentLocale=en-US&inforCurrentLanguage=en-US&infor10WorkspaceShell=1&inforWorkspaceVersion=2025.03.03&inforOSPortalVersion=2025.03.03&inforTimeZone=(UTC%2B01%3A00)%20Dublin%2C%20Edinburgh%2C%20Lisbon%2C%20London&inforStdTimeZone=Europe%2FLondon&inforStartMode=3&inforTenantId=ICSGDENA002_DEV&inforSessionId=ICSGDENA002_DEV~6ba2f2fc-8f7b-4651-97de-06a45e5f54e7'}},
                            # Press Ctrl+S to save
                            {'send_keys': {'keys': 'Control+s'}},
                        ],
                    )
                else:
                    agent_instance = Agent(
                        task=task,
                        llm=llm,
                        browser=browser,  # Pass the configured browser
                    )
                
                agent = {
                    'instance': agent_instance,
                    'task': task,
                    'mode': mode,
                    'running': False,
                    'created_at': time.time(),
                    'last_active': time.time(),
                }
                self.agents[agent_id] = agent
                logger.info(f'Created {mode} agent {agent_id} with persistent profile at {agent_profile_dir}. Total agents: {len(self.agents)}')
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
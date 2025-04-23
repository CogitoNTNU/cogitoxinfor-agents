from typing import List, Dict, Any, Optional, Literal
import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
import logging
from pydantic import BaseModel
from .graph import create_agent_graph, AgentState

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class ConfigLLM(BaseModel):
    model_name: str = os.getenv("LLM_MODEL_NAME", "gpt-4.1-nano")
    temperature: float = 0.0

class MCPAgent:
    def __init__(
        self, 
        stream_mode: Literal["values", "events", "updates", "debug", "messages-tuple"] = "values"
    ):
        self.llm = ConfigLLM()
        
            # Update the browser configuration with specific flags
        self.mcp_servers = {}
            
        self.tools = None
        self.cleanup_func = None
        self.config = {"configurable": {"thread_id": "42"}}
        self.graph = None
        self.checkpointer = MemorySaver()
        self.reasoning_agent = False
        self.initialized = False
        self.human_in_the_loop = False
        self.stream_mode = stream_mode
        
        # Add default system prompt
        self.default_system_prompt = "You are a helpful browser assistant. Use the browser tools to help the user."
        # Initialize prompt template with default
        self.prompt_template = self.create_default_prompt_template()
    
    def create_default_prompt_template(self):
        """Create a default prompt template that takes a query parameter"""
        template = ChatPromptTemplate.from_messages([
            ("system", self.default_system_prompt),
            ("human", "{query}")
        ])
        return template
        
    def set_prompt_template(self, template: ChatPromptTemplate):
        """Set a custom prompt template for the agent."""
        self.prompt_template = template
        logger.info("Custom prompt template set for agent")
    
    def set_stream_mode(self, mode: Literal["values", "updates", "iterations"]):
        """Set the stream mode for all subsequent runs."""
        self.stream_mode = mode
        logger.info(f"Stream mode set to {mode}")

    async def cleanup_stale_browsers(self):
        """Force cleanup of stale browser processes and lock files"""
        try:
            import os
            import subprocess
            
            # Kill any Chrome processes
            try:
                subprocess.run(["pkill", "-f", "chrome"], stderr=subprocess.DEVNULL)
                print("Killed any running Chrome processes")
            except Exception:
                pass
                
            # Remove the lock file if it exists
            profile_path = os.path.expanduser("~/.cache/ms-playwright/mcp-chromium-profile")
            lock_file = os.path.join(profile_path, "SingletonLock")
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"Removed stale lock file: {lock_file}")
        except Exception as e:
            print(f"Non-critical error cleaning browsers: {e}")

    async def initialize(self):
        """Initialize the MCP agent with tools"""
        if self.initialized:
            return
        
        try:
            # Aggressive cleanup - remove the entire default profile directory
            import shutil
            import os
            import uuid
            import time
            
            # Force remove the default profile directory completely
            default_profile = os.path.expanduser("~/.cache/ms-playwright/mcp-chromium-profile")
            try:
                if os.path.exists(default_profile):
                    print(f"Removing default profile directory: {default_profile}")
                    shutil.rmtree(default_profile)
            except Exception as e:
                print(f"Error removing default profile: {e}")
            
            # Create new unique profile path with full path (not relative)
            unique_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
            profile_dir = os.path.abspath(f"/tmp/playwright-profile-{unique_id}")
            os.makedirs(profile_dir, exist_ok=True)
            
            print(f"Using unique browser profile at: {profile_dir}")
            
            # Use a clean environment to avoid any system issues
            clean_env = os.environ.copy()
            if 'PLAYWRIGHT_BROWSERS_PATH' in clean_env:
                del clean_env['PLAYWRIGHT_BROWSERS_PATH']
                

            self.mcp_servers = {
                    "playwright": {
                        "command": "npx",
                        "args": [
                            "@playwright/mcp@latest",
                            "--browser", "chrome",
                            "--vision",
                            f"--user-data-dir={profile_dir}",
                        ],
                        "env": clean_env
                    }
                }
            # Import and convert tools
            from langchain_mcp_tools import convert_mcp_to_langchain_tools
            
            print("Converting MCP servers to LangChain tools...")
            self.tools, self.cleanup_func = await convert_mcp_to_langchain_tools(self.mcp_servers)
            
            # Debug: Print available tools
            print(f"Tools available ({len(self.tools)}):")
            for idx, tool in enumerate(self.tools):
                print(f"{idx+1}. {tool.name}")
            
            # Create agent graph
            from .graph import create_agent_graph
            print("Creating agent graph...")
            self.graph = create_agent_graph(
                tools=self.tools,
                checkpointer=self.checkpointer
            )
            
            self.initialized = True
            print("MCP tools loaded successfully")
        except Exception as e:
            print(f"Error initializing MCP agent: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def initialize_state(
        self, 
        input, 
    ) -> AgentState:
        """Initialize the agent state without starting the stream.
        
        Args:
            input: Either a string query or a list of BaseMessages
            config: Optional configuration dictionary (defaults to self.config)
        
        Returns:
            The initialized AgentState that can be used with graph.astream()
        """
        if not self.initialized:
            await self.initialize()
            
        # Handle string query by formatting with prompt template
        if isinstance(input, str):
            logger.info("Formatting query using prompt template")
            messages = self.prompt_template.format_messages(query=input)
        else:
            # Assume input is already a list of messages
            logger.info("Using provided message list")
            messages = input
            
        # Create the initial state
        initial_state = AgentState(
            messages=messages,
            model_name=self.llm.model_name,
            human_in_the_loop=self.human_in_the_loop,
            testing=False,
            test_actions=[],
            return_direct=False,
            intermediate_steps=[],
            DEBUG=True,
            prompt_template=self.prompt_template  # Pass prompt template to state
        )
        
        logger.info(f"State initialized with {'reasoning' if self.reasoning_agent else 'standard'} agent configuration")
        return initial_state

    async def format_response(self, content: str) -> str:
        """Format the response content. Can be overridden for custom formatting."""
        return content
        
    async def cleanup(self):
        """Clean up MCP servers and other resources."""
        if self.cleanup_func:
            try:
                await self.cleanup_func()
                print("MCP tools cleanup completed successfully")
                
                # Additional cleanup - force kill any lingering Chrome processes
                import subprocess
                try:
                    subprocess.run(["pkill", "-f", "chrome"], stderr=subprocess.DEVNULL)
                except:
                    pass
            except Exception as e:
                print(f"Error during MCP tools cleanup: {e}")
        else:
            print("No cleanup function available")
        # Reset initialized state
        self.initialized = False
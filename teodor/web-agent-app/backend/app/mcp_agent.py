from typing import List, Dict, Any, Optional, Literal
import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
import logging
from pydantic import BaseModel
from graph import AgentState, create_agent_graph

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
        
        self.mcp_servers = {
                "playwright": {
                "command": "npx",  # Use resolved npx path
                "args": [
                    "@playwright/mcp@latest",
                    "--browser", "chrome"  # Options: chrome, firefox, webkit, msedge
                ],
                }
            }
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

    async def initialize(self):
        self.tools, self.cleanup_func = await convert_mcp_to_langchain_tools(self.mcp_servers)
        
        if self.tools:
            print("MCP tools loaded successfully")
            self.initialized = True  # Set flag to True after successful initialization
            self.graph = create_agent_graph(
                    self.tools,
                    self.checkpointer
                )
        else:
            raise Exception("No tools were loaded from MCP servers")
        

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
    
    async def arun(
        self, 
        input, 
        config: Optional[Dict[str, Any]] = None, 
        stream_mode: Optional[Literal["values", "updates", "iterations"]] = None
    ):
        """Stream events from the agent with flexible input handling.
        
        Args:
            input: Either a string query or a list of BaseMessages
            config: Optional configuration dictionary (defaults to self.config)
            stream_mode: Stream mode to use (defaults to self.stream_mode)
        
        Yields:
            Events from the agent execution including interrupts
        """
        if not self.initialized:
            await self.initialize()
        
        # Use provided config or default
        if config is None:
            config = self.config
        
        # Use provided stream_mode or default
        effective_stream_mode = stream_mode if stream_mode is not None else self.stream_mode
        logger.info(f"Using stream mode: {effective_stream_mode}")
        
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
        
        print(f"Using {'reasoning' if self.reasoning_agent else 'standard'} agent graph")
        
        # Stream events from the graph with configurable stream mode
        async for event in self.graph.astream(
            initial_state,
            config=config,
            stream_mode=effective_stream_mode,
        ):
            # Pass through all events unfiltered
            # For chat model streams, process the content
            if event.get("event") == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                chunk.content = await self.format_response(chunk.content)
                
            # Yield the event regardless of type to support interrupts and other events
            yield event

    async def format_response(self, content: str) -> str:
        """Format the response content. Can be overridden for custom formatting."""
        return content
        
    async def cleanup(self):
        """Clean up MCP servers and other resources."""
        if self.cleanup_func:
            try:
                await self.cleanup_func()
                print("MCP tools cleanup completed successfully")
            except Exception as e:
                print(f"Error during MCP tools cleanup: {e}")
        else:
            print("No cleanup function available")
        # Reset initialized state
        self.initialized = False
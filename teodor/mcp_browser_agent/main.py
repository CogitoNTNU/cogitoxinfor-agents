###################################################################
# Dette er en demo av hvordan vi kan bruke MCP agent i langchain

# Dette er source code for use MCP agenten som jeg brukte som base
# https://github.com/mcp-use/mcp-use/blob/main/mcp_use/agents/mcpagent.py

# MCP Agent for LangChain
# Dette er source code for å gjøre MCP til langchain tools
# https://github.com/hideya/langchain-mcp-tools-py?tab=readme-ov-file

# further on this is one way we can create more complex systems
# https://github.com/roboticsocialism/langgraph_demo/blob/main/langgraph_demo.py

# This is how we can create human in the loop using the standard scrathpad agent
# https://langchain-ai.github.io/langgraph/how-tos/create-react-agent-hitl/#code

####################################################################

# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional # Added Any, Optional
import os
from dotenv import load_dotenv
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, BaseMessage)
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from .app.graph import create_agent_graph, AgentState
import logging # Add logging import

load_dotenv()

from typing import List, Dict, Any, Optional # Added Any, Optional
import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
import logging # Add logging import

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigLLM(BaseModel):
    model_name: str = os.getenv("LLM_MODEL_NAME", "gpt-4.1-nano")
    temperature: float = 0.0

class MCPAgent:
    def __init__(self):
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
        
        # Add default system prompt
        self.default_system_prompt = "You are a helpful browser assistant. Use the browser tools to help the user."
        # Initialize prompt template with default
        self.prompt_template = self.create_default_prompt_template()
    
    
    def create_default_prompt_template(self):
        """Create a default prompt template that takes a query parameter"""
        from langchain_core.prompts import ChatPromptTemplate
        
        template = ChatPromptTemplate.from_messages([
            ("system", self.default_system_prompt),
            ("human", "{query}")
        ])
        return template
        
    def set_prompt_template(self, template: ChatPromptTemplate):
        """Set a custom prompt template for the agent."""
        self.prompt_template = template
        logger.info("Custom prompt template set for agent")
        
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
        
    async def astream_events(self, input):
        """Stream events from the agent with flexible input handling.
        
        Args:
            input: Either a string query or a list of BaseMessages
            config: Optional configuration dictionary (defaults to self.config)
        
        Yields:
            Events from the agent execution
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
        
        print(f"Using {'reasoning' if self.reasoning_agent else 'standard'} agent graph")
        
        # Stream events from the graph
        async for event in self.graph.astream_events(
            initial_state,
            config=self.config,
            stream_mode="values"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                chunk.content = await self.format_response(chunk.content)
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a more specific type for the message data if needed, or use Any
class MessageData(BaseModel):
    imageData: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    data: Optional[MessageData] = None


class TestAction(BaseModel):
    action: str
    args: List[str]


class ChatRequest(BaseModel):
    messages: List[ChatMessage] # Use the new ChatMessage model
    thread_id: str = "default"
    stream: bool = True
    use_reasoning: bool = False
    query: str
    testing: bool = False
    test_actions: Optional[List[TestAction]] = None
    human_intervention: bool = False


@app.on_event("startup")
async def startup_event():
    app.state.agent = MCPAgent()
    await app.state.agent.initialize() # Initialize the agent
    # Additional setup if needed
    print("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state.agent, 'cleanup'):
        await app.state.agent.cleanup()
    # Additional cleanup if needed
    print("Application shutdown complete")


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info("--- Entering chat_endpoint ---") # Log entry
    # Convert request messages to BaseMessage instances
    try:
        langchain_messages: List[BaseMessage] = [] # Renamed and typed for clarity
        num_messages = len(request.messages)
        for i, msg in enumerate(request.messages):
            role = msg.role
            content = msg.content
            is_last_message = (i == num_messages - 1) # Restore check

            if role == 'user':
                # Restore multimodal check for the last message
                image_data = msg.data.imageData if msg.data and msg.data.imageData and is_last_message else None

                if image_data:
                    # Create multimodal message if image data exists in the last message
                    message_content = [
                        {"type": "text", "text": content},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data} # Assuming image_data is a base64 data URL
                        }
                    ]
                    langchain_messages.append(HumanMessage(content=message_content))
                    print(f"Processed multimodal user message: {content[:50]}... + Image")
                else:
                    # Regular text message
                    langchain_messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                 # Handle assistant messages if needed
                 langchain_messages.append(AIMessage(content=content))
            # Add other roles (system, tool) if necessary

        print(f"Processed LangChain messages: {langchain_messages}") # Updated print statement

        async def event_stream():

            logger.info("--- Starting agent event stream ---") # Log before loop
            async for event in app.state.agent.astream_events(
                input=langchain_messages, # Corrected: Pass the list directly
                # Removed incorrect stream_mode argument here
            ):
                event_name = event.get("event")
                #logger.info(f"--- Agent Event Received: {event_name} ---") # Log inside loop

                # Focus ONLY on the event carrying content chunks from the LLM stream
                if event_name == "on_chat_model_stream":
                    chunk_data = event.get("data", {}).get("chunk")
                    if not chunk_data:
                        logger.warning("Event 'on_chat_model_stream' had no chunk data.")
                        continue

                    # Extract content from the chunk (AIMessageChunk)
                    content = chunk_data.content
                    if content is None: # Skip if content is None
                        continue

        print("Finished graph execution!")
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

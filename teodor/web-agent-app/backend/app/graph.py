from typing import TypedDict, Annotated, Union, Sequence, List, Any, Optional, Dict, Literal
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from .load_model import load_model
import json
import operator
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig, RunnableLambda
from pydantic import BaseModel, Field
import logging
import asyncio
from langgraph.types import interrupt, Command
from langchain_core.prompts import ChatPromptTemplate
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent_graph")


class Prediction(BaseModel):
    """
    Represents the agent's predicted action and its arguments.
    """
    action: str = Field(description="The action to be performed by the agent")
    args: List[str] = Field(default_factory=list, description="Arguments for the action")


class OldState(BaseModel):
    """
    Represents the state of the agent during execution.
    """
    testing: bool = Field(default=False, description="Flag indicating if the agent is in testing mode")
    test_actions: Optional[List[Prediction]] = Field(default_factory=list, description="The action to be tested")
    prediction: Optional[Prediction] = Field(None, description="The agent's predicted action and arguments")
    repeated_failures: Optional[int] = Field(default=0, description="Count of repeated failures for the current action")
    human_in_the_loop: bool = False
    DEBUG: bool = True


class AgentState(OldState):
    """State of the agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    agent_outcome: Union[AgentAction, AgentFinish, None] = None
    return_direct: bool = False
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add] = Field(default_factory=list)
    model_name: str = "gpt-4.1"  # Default model name
    test_responses: Optional[List[Dict[str, Any]]] = None  # Predefined responses for testing
    interrupt_response: Optional[str] = None  # Added interrupt response field
    screenshot_data: Optional[str] = None  # Store the latest screenshot data
    
    class Config:
        arbitrary_types_allowed = True
        # Add this to handle serialization more gracefully
        json_encoders = {
            ChatPromptTemplate: lambda v: None if v is None else str(type(v).__name__),
            BaseMessage: lambda v: None if v is None else str(type(v).__name__),
        }


def create_agent_graph(tools, checkpointer=None):
    """Create an async LangGraph REACT agent with customizable prompts and testing capabilities.
    
    Args:
        tools: List of available tools
        checkpointer: Optional checkpointer for state persistence
        
    Returns:
        Compiled async StateGraph for the agent
    """
    logger.info(f"Creating agent graph with {len(tools)} tools")

    @RunnableLambda
    async def call_model(state: AgentState, config: RunnableConfig):
        """Call the LLM with the current conversation state."""
        logger.info(f"Calling model {state.model_name} with {len(state.messages)} messages")
        
        llm = load_model(
            model_name=state.model_name, 
            tools=tools
        )
            
        response = await llm.ainvoke(input=state.messages, config=config)
        # Return updated state with the response
        return {"messages": [response]}
    
    @RunnableLambda
    async def take_screenshot(state: AgentState, config: RunnableConfig):
        """Take a screenshot before agent processing."""
        logger.info("Taking screenshot before agent processing")
        # Find the screenshot tool in available tools
        tool_name = "browser_screen_capture"
        screenshot_tool = next((t for t in tools if t.name == tool_name), None)
        if not screenshot_tool:
            logger.warning("Screenshot tool not available")
            return state  # Return state instead of END to avoid errors
                
        # Create tool node for screenshot
        tool_node = ToolNode(
            tools=[screenshot_tool],
            handle_tool_errors=lambda exception: f"Error taking screenshot: {str(exception)}"
        )
        
        try:
            # Properly configure screenshot tool with parameters that return base64 data
            screenshot_message = AIMessage(
                content="Taking a screenshot of the current page",
                tool_calls=[{
                    "name": tool_name,
                    "args": {
                        "encoding": "base64",  # Explicitly request base64 encoding
                        "raw": True,
                        "fullPage": True,
                        "type": "jpeg"
                    },
                    "id": "screenshot_tool_call"
                }]
            )
                
            # Create a temporary state with the screenshot request
            temp_state = AgentState(
                messages=list(state.messages) + [screenshot_message],
                intermediate_steps=state.intermediate_steps,
                model_name=state.model_name,
                human_in_the_loop=state.human_in_the_loop,
                DEBUG=state.DEBUG
            )
            
            # Execute the screenshot tool
            result = await tool_node.ainvoke(temp_state)
            
            # Extract the tool response
            tool_message = result["messages"][-1]
            print(f"Tool message content: {tool_message.content}")
            # Extract base64 data if it's there
            if isinstance(tool_message.content, str):
                match = re.search(r'data:image\/(?:png|jpeg);base64,([^)"\s]+)', tool_message.content)
                if match:
                    # Store just the base64 data in the state
                    screenshot_data = match.group(1)
                    print(f"Screenshot data extracted: {screenshot_data[:20]}...")  # Print first 20 chars for brevity
                    # Add screenshot info to messages
                    screenshot_info = SystemMessage(content=f"[System] Screenshot of current page taken. The agent can reference this recent view of the page.")
                    
                    # Return updated state with screenshot data
                    return {
                        "messages": state.messages + [screenshot_info],
                        "screenshot_data": screenshot_data
                    }
            
            logger.warning("Screenshot taken but couldn't extract base64 data")
            return state
            
        except Exception as e:
            logger.error(f"Error executing screenshot tool: {e}")
            return state
    
    @RunnableLambda
    async def human_input(state: AgentState, config: RunnableConfig) -> Union[AgentState, dict]:
        # Extract the tool call details
        last_message = state.messages[-1]
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Interrupt the graph and wait for human input
        message = f"Agent wants to perform: {tool_name} with args: {tool_args}"
        user_input = interrupt(message)
        
        # Different routing based on user input
        if not user_input or user_input.strip().lower() == "approved":
            # User approved - continue with tool execution
            return Command(goto="tools")
        
        elif user_input.strip().lower() == "exit":
            # User wants to stop execution
            return Command(goto=END)
        
        elif user_input.strip().lower() in ["no", "cancel", "reject"]:
            # User rejected - send back to agent with request for alternative
            return Command(
                goto="agent", 
                update={"messages": state.messages + [
                    HumanMessage(content="Please suggest an alternative approach.")
                ]}
            )
        
        else:
            # User provided custom instructions - send to agent with those instructions
            return Command(
                goto="agent",
                update={"messages": state.messages + [
                    HumanMessage(content=user_input)
                ]}
            )

    @RunnableLambda
    async def tool_execution(state: AgentState):
        """Execute tools and track intermediate steps."""
        # Get the last message with tool calls
        last_message = state.messages[-1]
        if not (isinstance(last_message, AIMessage) and last_message.tool_calls):
            return state

        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]
        tool_input = tool_call["args"]
        tool_call_id = tool_call.get("id", "unknown")
        
        # Log the tool execution
        logger.info(f"Executing tool: {tool_name} with input: {json.dumps(tool_input)[:100]}...")
        
        # Create tool node for this execution - WITH A ROBUST ERROR HANDLER
        tool_node = ToolNode(
            tools=tools,
            handle_tool_errors=lambda exception, tool_call=None: (
                f"Error executing tool {tool_call.get('name') if tool_call else tool_name}: {str(exception)}"
            ),
        )
        
        tool_names = [tool.name for tool in tools]
        if tool_name not in tool_names:
            raise ValueError(f"Tool {tool_name} not found in available tools: {tool_names}")
        
        try:
            result = await tool_node.ainvoke(state)
            
            # Create the agent action record
            agent_action = AgentAction(
                tool=tool_name,
                tool_input=tool_input,
                log=last_message.content,
                tool_call_id=tool_call_id  # Add this to be safe
            )
            
            # Get the tool message content
            tool_message = result["messages"][-1]
            
            # Add to intermediate steps
            new_steps = state.intermediate_steps + [(agent_action, tool_message.content)]
            
            logger.info(f"New intermediate steps: {len(new_steps)}")
            
            # Return updated state
            return {
                "messages": result["messages"],
                "intermediate_steps": new_steps
            }
        except Exception as e:
            # Handle exceptions manually if the tool_node fails completely
            logger.error(f"Exception executing tool {tool_name}: {e}")
            
            # Create a manual tool message for the error
            error_message = f"Error executing tool {tool_name}: {str(e)}"
            
            return {
                "messages": state.messages + [
                    ToolMessage(
                        content=error_message,
                        tool_call_id=tool_call_id
                    )
                ]
            }

    # Create the state graph
    workflow = StateGraph(AgentState)
    logger.info("Initializing state graph")
    
    # Add nodes
    workflow.add_node("screenshot", take_screenshot)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_execution)
    workflow.add_node("human_input_node", human_input, destinations=("agent", "tools", END))
    
    # Set entry point - now starts with screenshot
    workflow.set_entry_point("screenshot")
    
    # Add edge from screenshot to agent
    workflow.add_edge("screenshot", "agent")
    
    # Define conditional edge routing
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue with tools or end the conversation."""
        last_message = state.messages[-1]
        
        if state.human_in_the_loop and isinstance(last_message, AIMessage) and last_message.tool_calls:
            logger.info("Decision: Human intervention required")
            return "human_input_node"
        
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            logger.info("Decision: Agent requested tool execution")
            return "tools"
        else:
            logger.info("Decision: Agent completed task, ending workflow")
            return "end"
    
    # Connect nodes
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
            "human_input_node": "human_input_node"
        }
    )
    
    # Add edge from tools back to screenshot (to take a screenshot before going back to agent)
    workflow.add_edge("tools", "screenshot")

    logger.info("Graph structure defined and edges connected")
    
    # Compile the graph
    if checkpointer:
        logger.info("Compiling graph with checkpointer")
        return workflow.compile(checkpointer=checkpointer)
    
    logger.info("Compiling graph without checkpointer")
    return workflow.compile()
from langchain_core.messages import BaseMessage, SystemMessage
import base64
import asyncio
from langchain_core.runnables import RunnableLambda
from models import AgentState, Prediction
from browser import annotate
from llm import structured_llm
from prompt import new_prompt
from tools import (
    click,
    type_text,
    scroll,
    wait,
    go_back,
    to_google,
    approve_info_box,
)

from models import (
    CLICK,
    TYPE,
    SCROLL,
    WAIT,
    GOBACK,
    GOOGLE,
    APPROVE,
    ANSWER,
    RETRY,
)

from langgraph.types import interrupt

def human_interaction(state: AgentState) -> AgentState:
    """
    Human interaction node that stops the graph for bounding box review.
    The actual interaction happens in test_agent via graph.get_state and graph.update_state.
    """
    # This function is essentially a placeholder - the interaction happens in test_agent
    # Simply return the state unchanged
    return state

def format_descriptions(state: AgentState) -> AgentState:
    """
    Formats the bounding box descriptions for the agent's prompt and updates the scratchpad.
    """
    # Create descriptions of available elements
    if state.bboxes:
        descriptions = [f"{i}: {bbox.description}" for i, bbox in enumerate(state.bboxes)]
        details = "\n".join(descriptions)
        message_content = f"Available elements on page:\n{details}"
    else:
        message_content = "No elements detected on page"
    
    # Create a standard SystemMessage that the LLM can understand
    bbox_message = SystemMessage(content=message_content)
    
    # Add to scratchpad
    if state.scratchpad is None:
        state.scratchpad = []
    state.scratchpad.append(bbox_message)
    
    return state

# Main agent function
async def agent(state: AgentState) -> AgentState:
    """
    Main function to run the agent.
    """
    try:

        # Step 1: Generate the prompt text
        prompt_text = new_prompt.invoke({
            "bbox_descriptions": state.bboxes,
            "img": state.img,  # Correctly embed the Base64-encoded image
            "input": state.input,
            "scratchpad": state.scratchpad,
        })

        # Print the prompt text for debugging
        print("Prompt Text: ", prompt_text)

        # Step 2: Get the LLM response
        response = await structured_llm.ainvoke(prompt_text)
        prediction = Prediction(action=response.action, args=response.args)
        print("Prediction: ", prediction)

        # Step 3: Update the agent state with the prediction
        state.prediction = prediction

        return state

    except Exception as e:
        print(f"Error in agent function: {e}")
        raise


def update_scratchpad(state: AgentState) -> AgentState:
    """
    Updates the scratchpad with the results of the agent's previous actions.
    """
    try:
        print("Updating scratchpad with observation:", state.observation)
        
        # Get action from prediction
        if state.prediction and state.prediction.action:
            action = state.prediction.action.lower()
        else:
            action = "unknown"
        
        # The observation is already a formatted string from create_observation().format()
        observation_text = state.observation or "No observation provided"
        
        # Create a standard SystemMessage that the LLM can understand
        scratchpad_message = SystemMessage(content=observation_text)
        
        # Add the message to the scratchpad
        if state.scratchpad is None:
            state.scratchpad = []
        state.scratchpad.append(scratchpad_message)
        
        print(f"Updated scratchpad with observation for action: {action}")
        return state
        
    except Exception as e:
        print(f"Error in update_scratchpad: {e}")
        raise

from IPython.display import display, Image
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal

AGENT = "agent"
HUMAN_INTERACTION = "human_interaction"
FORMAT_DESCRIPTIONS = "format_descriptions"
ANNOTATE_PAGE = "annotate_page"
UPDATE_SCRATCHPAD = "update_scratchpad"

builder = StateGraph(AgentState)

builder.add_node(AGENT, agent)
builder.add_node(ANNOTATE_PAGE, annotate)
builder.add_node(FORMAT_DESCRIPTIONS, format_descriptions)
builder.add_node(UPDATE_SCRATCHPAD, update_scratchpad)
builder.add_node(HUMAN_INTERACTION, human_interaction)

builder.add_edge(START, ANNOTATE_PAGE)
builder.add_edge(ANNOTATE_PAGE, FORMAT_DESCRIPTIONS)
builder.add_edge(FORMAT_DESCRIPTIONS, HUMAN_INTERACTION)
builder.add_edge(HUMAN_INTERACTION, AGENT)


builder.add_edge(UPDATE_SCRATCHPAD, ANNOTATE_PAGE)

tools = {
    CLICK: click,
    TYPE: type_text,
    SCROLL: scroll,
    WAIT: wait,
    GOBACK: go_back,
    GOOGLE: to_google,
    APPROVE: approve_info_box,
}


for tool_name, tool_func in tools.items():
    builder.add_node(tool_name, tool_func)
    builder.add_edge(tool_name, UPDATE_SCRATCHPAD)

nodes = Literal[
    CLICK,
    TYPE,
    SCROLL,
    WAIT,
    GOBACK,
    GOOGLE,
    APPROVE,
    UPDATE_SCRATCHPAD,
    END,
    ANNOTATE_PAGE,
]

def select_tool(state: AgentState) -> nodes:
    action = state.prediction.action
    if action == ANSWER:
        return END
    if action == RETRY:
        print("Retrying...")
        return ANNOTATE_PAGE
    return action

builder.add_conditional_edges(AGENT, select_tool)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
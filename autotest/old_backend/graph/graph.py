"""
LangGraph definitions for the web agent.
"""
from typing import Literal, Dict, Any
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

# Use relative imports
from .models import AgentState, InputState, OutputState, Prediction
from .agent import agent
from .utils import annotate, format_elements, update_scratchpad
from .tools import (
    CLICK, click,
    TYPE, type_text,
    SCROLL, scroll,
    WAIT, wait,
    GOBACK, go_back,
    GOOGLE, to_google,
    NAVIGATE, navigate_to
)

# Node names
AGENT = "agent"
HUMAN_INTERACTION = "human_interaction"
FORMAT_ELEMENTS = "format_elements"
ANNOTATE_PAGE = "annotate_page"
UPDATE_SCRATCHPAD = "update_scratchpad"


async def human_input(state: AgentState, config) -> AgentState:
    """
    Conditionally interrupts the graph for human approval based on state.
    """

    # Create a descriptive message about what's happening
    test_action = state.test_actions[0]
    action = test_action.action
    args = test_action.args
    # Format the message for user interaction
    message = f"Agent wants to perform: {action} with args: {args}"
    
    # This will pause execution and return the message to the client
    user_input = interrupt(message)
    
    # When execution resumes, user_input will contain the value
    # passed via Command(resume=...)
    if user_input == '':
        # If user just pressed Enter, keep the original action and args
        # No changes needed to state.test_actions[0]
        print(f"User accepts the action: {action} with args: {args}")
        pass
    else:
        print(f"User provided alternative input: {user_input}")
        if user_input == 'exit':
            # If the user wants to exit, set the action to "exit"
            state.test_actions[0] = Prediction(action="exit", args=[])
        else:
            # Only update if the user provided alternative input
            # Convert the input to a list to maintain proper args format
            new_args = [user_input]
            state.test_actions[0] = Prediction(action=action, args=new_args)

    return state

def build_graph():
    """Build and return the agent graph."""
    # Create the graph builder
    builder = StateGraph(AgentState, input=InputState, output=OutputState)

    builder.add_node(AGENT, agent)
    builder.add_node(ANNOTATE_PAGE, annotate)
    builder.add_node(FORMAT_ELEMENTS, format_elements)
    builder.add_node(UPDATE_SCRATCHPAD, update_scratchpad)
    builder.add_node(HUMAN_INTERACTION, human_input)

    # Add initial edges
    builder.add_edge(START, ANNOTATE_PAGE)
    builder.add_edge(ANNOTATE_PAGE, FORMAT_ELEMENTS)

    annotate_nodes = Literal[AGENT, END, HUMAN_INTERACTION]

    def after_annotate(state: AgentState) -> annotate_nodes:
        """
        After annotating the page, we need to update the scratchpad and return to the agent.
        """
        if state.testing and len(state.test_actions) == 0:
                # If there are no more test actions, end the process
                print("No more test actions left.")
                return END

        if state.repeated_failures > 1:
            # If we have repeated failures, return to the agent
            print("Repeated failures detected, ending the process.")
            return END
        
        # If we are in testing mode, we need to ask for human input
        print("Asking for human input...")
        return HUMAN_INTERACTION
        #return AGENT

    builder.add_conditional_edges(
        FORMAT_ELEMENTS,
        after_annotate
    )

    def after_human_interaction(state: AgentState) -> Literal[AGENT, END]:
        """
        After human interaction, we need to update the scratchpad and return to the agent.
        """
        # Update the scratchpad with the new action
        if state.test_actions[0].action == "exit":
            # If there are no more test actions, end the process
            print("Returning from the graph interaction.")
            return END
        return AGENT


    builder.add_conditional_edges(HUMAN_INTERACTION, after_human_interaction)

    # Define and add all tool nodes
    tools = {
        CLICK: click,
        TYPE: type_text,
        SCROLL: scroll,
        WAIT: wait,
        GOBACK: go_back,
        GOOGLE: to_google,
        NAVIGATE: navigate_to,
    }

    for node_name, tool_func in tools.items():
        builder.add_node(
            node_name,
            RunnableLambda(tool_func) | (lambda observation: {"observation": observation}),
        )
        builder.add_edge(node_name, UPDATE_SCRATCHPAD)

    nodes = Literal[CLICK, TYPE, SCROLL, WAIT, GOBACK, GOOGLE, NAVIGATE, END]

    # Define the tool selection function
    def select_tool(state: AgentState) -> nodes:
        action = state.prediction.action
        if action == "ANSWER":
            return END
        if action == "RETRY":
            print("Retrying...")
            return AGENT
        return action

    # Add conditional edge from agent to appropriate tool
    builder.add_conditional_edges(AGENT, select_tool)

    # Add edge from update_scratchpad back to annotate_page
    builder.add_edge(UPDATE_SCRATCHPAD, ANNOTATE_PAGE)
    
    # Create memory saver and compile the graph
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)

def get_graph_with_config(config=None):
    """Get a graph instance with optional configuration."""
    if config is None:
        config = {}
    return build_graph()

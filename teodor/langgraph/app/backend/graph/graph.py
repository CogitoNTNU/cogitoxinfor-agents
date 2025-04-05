"""
LangGraph definitions for the web agent.
"""
from typing import Literal, Dict, Any
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

# Use relative imports
from .models import AgentState, InputState, OutputState
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
FORMAT_ELEMENTS = "format_elements"
ANNOTATE_PAGE = "annotate_page"
UPDATE_SCRATCHPAD = "update_scratchpad"
HUMAN_INTERVENTION = "human_intervention_node"


# Example human intervention node for graph.py
def human_intervention_node(state):
    """Node that interrupts execution for human input on bounding boxes."""
    
    # Get bounding boxes from the page
    bboxes = state.bboxes
    print("Inside human intervention node.")
    
    # Interrupt execution and wait for user input
    selected_index = interrupt({"Bboxes_from_page": bboxes})
    
    # After resumption, return the selected bbox
    return {"selected_bbox": bboxes[selected_index]}


def build_graph():
    """Build and return the agent graph."""
    # Create the graph builder
    builder = StateGraph(AgentState, input=InputState, output=OutputState)

    # Add nodes for agent operations
    builder.add_node(AGENT, agent)
    builder.add_node(ANNOTATE_PAGE, annotate)
    builder.add_node(FORMAT_ELEMENTS, format_elements)
    builder.add_node(UPDATE_SCRATCHPAD, update_scratchpad)
    builder.add_node(HUMAN_INTERVENTION, human_intervention_node)

    # Add initial edges
    builder.add_edge(START, ANNOTATE_PAGE)
    builder.add_edge(ANNOTATE_PAGE, FORMAT_ELEMENTS)

    annotate_nodes = Literal[AGENT, HUMAN_INTERVENTION, END]

    def after_annotate(state: AgentState) -> annotate_nodes:
        """Determine what to do after annotation."""

        if state.human_intervention:
            print("Human intervention required.")
            return HUMAN_INTERVENTION

        if state.testing and len(state.test_actions) == 0:
            print("No more test actions left.")
            return END

        if state.repeated_failures > 1:
            print("Repeated failures detected, ending the process.")
            return END
            
        return AGENT

    builder.add_conditional_edges(
        FORMAT_ELEMENTS,
        after_annotate
    )

    builder.add_edge(HUMAN_INTERVENTION, AGENT)

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

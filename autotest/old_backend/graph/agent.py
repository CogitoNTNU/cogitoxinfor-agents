"""
Agent implementation for web browsing.
"""
import asyncio
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from .models import AgentState, Prediction, StrOutput
from .tools import CLICK, TYPE, SCROLL, WAIT, GOBACK, GOOGLE, ANSWER, RETRY, NAVIGATE

# Add the HUMAN constant for human intervention routing
HUMAN = "HUMAN"

def agent_routes(routes: dict) -> str:
    actions = ''.join([f"- {key}: {value} \n" for key, value in routes.items()])
    text = f"""
    Imagine you are a robot browsing the web, just like humans. Now you need to complete a task. 
    In each iteration, you will receive an Observation that includes a screenshot of a webpage and some texts. 
    This screenshot will feature Numerical Labels placed in the TOP LEFT corner of each Web Element. 
    Carefully analyze the visual information to identify the Numerical Label corresponding to the Web Element 
    that requires interaction, then follow the guidelines and choose one of the following actions:
    
    {actions}
    
    Key Guidelines You MUST follow:
    
    * Action guidelines *
    1) Execute only one action per iteration.
    2) When clicking or typing, ensure to select the correct bounding box.
    3) Numeric labels lie in the top-left corner of their corresponding bounding boxes and are colored the same.
    4) If you encounter a cookie consent popup (e.g., "Godta alle"), click on it to proceed. Use scroll if the labels in the bottom are not visible."
    5) If you are unsure or cannot find the right element, use the HUMAN action to ask for help.
    
    * Web Browsing Guidelines *
    1) Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages
    2) Select strategically to minimize time wasted.
    3) If you are stuck or confused, don't hesitate to ask for human help.
    
    Then the User will provide:
    Observation: A labeled screenshot Given by User

    If you encounter errors, please respond with "Error: [error message]".
    If you are unsure about the next action, use the HUMAN action to request assistance.
    If you are unable to find the bounding box, respond with "Error: no bounding box for label [label]".
    If you encounter difficulties to find elements, use scroll to make them visible.

    """
    return text

# Define the routes for the agent
routes = {
    CLICK: "Click a Web Element. [Numerical_Label].",
    TYPE: "Delete existing content in a textbox and then type content. [Numerical_Label]; [Content].",
    SCROLL: "Scroll up or down. [Numerical_Label or WINDOW]; [up or down]. Use this to make elements visible. Use this if stuck.",
    WAIT: "Wait.",
    GOBACK: "Go back.",
    GOOGLE: "Return to Google to start over.",
    ANSWER: "Respond with the final answer. [Content]. or if you are stuck with the same observation three times, answer with the last observation.",
    RETRY: "Retry the last action.",
    HUMAN: "Request human assistance with a specific question or issue. [Question]"
}

# Create the prompt template
def create_prompt_template():
    input_prompt = {"type": "text", "text": "{input}"}
    bbox_prompt = {"type": "text", "text": "{bbox_descriptions}"}
    img_prompt = {
        "type": "image_url",
        "image_url": {"url": "data:image/jpeg;base64,{img}"},
    }

    return ChatPromptTemplate.from_messages(
        [
            ("system", agent_routes(routes=routes)),
            MessagesPlaceholder("scratchpad", optional=True),
            ("human", [input_prompt]),
            ("human", [bbox_prompt]),
            ("human", [img_prompt]),
        ]
    )

# Initialize the LLM
def initialize_llm(model_name="gpt-4o"):
    """Initialize the language model with structured output."""
    
    # Return LLM with the handler attached
    return ChatOpenAI(model=model_name).with_structured_output(schema=StrOutput)

# Main agent function
async def agent(state: AgentState) -> AgentState:
    """
    Main function to run the agent.
    """
    try:
        if state.testing:
            # For testing, we can use a mock prediction
            prediction = state.test_actions[0]
            print("Mock Prediction: ", prediction)

        else:
            # Step 1: Generate the prompt text
            structured_llm = initialize_llm()
            prompt_template = create_prompt_template()
            
            prompt_text = prompt_template.invoke({
                "bbox_descriptions": state.bboxes,
                "img": state.img,
                "input": state.input,
                "scratchpad": state.scratchpad,
            })
            
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

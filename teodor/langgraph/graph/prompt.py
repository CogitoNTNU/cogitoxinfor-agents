from typing import Dict
from models import (
    CLICK,
    TYPE,
    SCROLL,
    WAIT,
    GOBACK,
    GOOGLE,
    ANSWER,
    RETRY,
)

#Dropping the format instructions in this system message 
# to avoid formatting issues with the structured output

def agent_routes(routes: Dict[str, str]) -> str:
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
    
    * Web Browsing Guidelines *
    1) Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages
    2) Select strategically to minimize time wasted.
    
    Then the User will provide:
    Observation: A labeled screenshot Given by User

    If you encounter errors, please respond with "Error: [error message]".
    If you are unsure about the next action, respond with "I don't know what to do next".
    If you are unable to find the bounding box, respond with "Error: no bounding box for label [label]".
    If you encounter diffulties to find elements, use scroll to make them visible.

    """
    return text

# Define the routes
routes = {
    CLICK: "Click a Web Element. [Numerical_Label].",
    TYPE: "Delete existing content in a textbox and then type content. [Numerical_Label]; [Content].",
    SCROLL: "Scroll up or down. [Numerical_Label or WINDOW]; [up or down]. Usr this to make elements visible. Use this if stuck",
    WAIT: "Wait.",
    GOBACK: "Go back.",
    GOOGLE: "Return to Google to start over.",
    ANSWER: "Respond with the final answer. [Content]. or if you are stuck with the same observation three times, answer with the last observation.",
    RETRY: "Retry the last action.",
}

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)


input_prompt = {"type": "text", "text": "{input}"}

bbox_prompt = {"type": "text", "text": "{bbox_descriptions}"}

img_prompt = {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,{img}"},
                }

new_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", agent_routes(routes=routes)),
         MessagesPlaceholder("scratchpad", optional=True),
        ("human", [input_prompt]),
        ("human", [bbox_prompt]),
        ("human", [img_prompt]),
    ]
)
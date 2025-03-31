from langchain import hub
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Import necessary libraries
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Load the prompt template for the agent
prompt = hub.pull("wfh/web-voyager")

# Define the structured output schema
class StrOutput(BaseModel):
    """
    Represents the structured output of the LLM.
    """
    thought: str = Field(..., description="Your brief thoughts (briefly summarize the info that will help ANSWER)")
    action: str = Field(..., description="The action you want to take")
    args: list[str] = Field(..., description="The arguments for the action")

# Initialize the LLM with gpt-4o and structured output
structured_llm = ChatOpenAI(model="gpt-4o").with_structured_output(schema=StrOutput)
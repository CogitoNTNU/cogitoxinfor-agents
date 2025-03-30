from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.messages import BaseMessage
from playwright.async_api import Page

CLICK = "CLICK"
TYPE = "TYPE"
SCROLL = "SCROLL"
WAIT = "WAIT"
GOBACK = "GOBACK"
GOOGLE = "GOOGLE"
APPROVE = "APPROVE"
ANSWER = "ANSWER"
RETRY = "RETRY"

# Define the BBox model
class BBox(BaseModel):
    """
    Represents a bounding box on the webpage with its coordinates and metadata.
    """
    x: float
    y: float
    text: str
    type: str
    ariaLabel: Optional[str] = None
    id: Optional[str] = None

    @property
    def description(self) -> str:
        """Generate a description for the bounding box."""
        label = self.ariaLabel or self.text or "No label"
        return f'{self.id} (<{self.type}/>): "{label}"'
    

# Define the Prediction model
class Prediction(BaseModel):
    """
    Represents the agent's predicted action and its arguments.
    """
    action: str = Field(description="The action to be performed by the agent")
    args: List[str] = Field(default_factory=list, description="Arguments for the action")

class Observation(BaseModel):
    """A single entry in the scratchpad"""
    step: int = 0
    action: str
    status: Literal["success", "warning", "error"]
    details: str
    
    def format(self) -> str:
        """Format the entry for display"""
        indicator = "✓" if self.status == "success" else "⚠️" if self.status == "warning" else "✗"
        return f"{self.step}. {indicator} {self.action.upper()}: {self.details}"


# Define the AgentState model
class AgentState(BaseModel):
    """
    Represents the state of the agent during execution.
    """
    page: Page = Field(default=None, exclude=True)  # Non-serializable Playwright page object
    input: str = ""
    img: Optional[str] = ""
    bboxes: Optional[List[BBox]] = Field(default_factory=list, description="List of bounding boxes annotated on the webpage")
    prediction: Optional[Prediction] = Field(description="The agent's predicted action and arguments")
    scratchpad: Optional[List[BaseMessage]] = Field(default_factory=list, description="Intermediate steps or system messages")
    observation: Optional[str] = ""
    ids: Optional[List[int]] = Field(default_factory=list)
    tasks: Optional[List[str]] = Field(default_factory=list, description="List of tasks to be performed by the agent")
    class Config:
        # Exclude the `page` attribute during serialization
        arbitrary_types_allowed = True
        json_encoders = {
            Page: lambda v: None,  # Prevent serialization of arbitrary objects
        }

# Structure for LLM output
class StrOutput(BaseModel):
    """
    Represents the structured output of the LLM.
    """
    thought: str = Field(..., description="Your brief thoughts (briefly summarize the info that will help ANSWER)")
    action: str = Field(..., description="The action you want to take")
    args: List[str] = Field(..., description="The arguments for the action")

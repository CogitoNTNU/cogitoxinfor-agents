"""
Pydantic models for the web agent.
"""
from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from playwright.async_api import Page

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


class AgentState(BaseModel):
    """
    Represents the state of the agent during execution.
    """
    testing: bool = Field(default=False, description="Flag indicating if the agent is in testing mode")
    test_actions: Optional[List[Prediction]] = Field(default_factory=list, description="The action to be tested")
    page: Optional[Page] = Field(default=None, exclude=True)  # Non-serializable Playwright page object
    input: str = ""
    img: Optional[str] = ""
    bboxes: Optional[List[BBox]] = Field(default_factory=list, description="List of bounding boxes annotated on the webpage")
    prediction: Optional[Prediction] = Field(None, description="The agent's predicted action and arguments")
    scratchpad: Optional[List[BaseMessage]] = Field(default_factory=list, description="Intermediate steps or system messages")
    observation: Optional[str] = ""
    ids: Optional[List[int]] = Field(default_factory=list)
    observations: Optional[List[Observation]] = Field(default_factory=list, description="List of observations made by the agent")
    repeated_failures: Optional[int] = Field(default=0, description="Count of repeated failures for the current action")
    human_intervention: bool = False
    selected_bbox: Optional[BBox] = None

    def add_observation(self, action: str, status: str, details: str) -> None:
        """Add a new observation to the history"""
        step = len(self.observations) + 1
        new_observation = Observation(step=step, action=action, status=status, details=details)
        self.observations.append(new_observation)
        self.observation = new_observation.format()  # Update the current observation string
        
    def check_repeated_failure(self, action: str, args: List[str]) -> Optional[List[Observation]]:
        """Check if this action+args combination has failed before"""
        if not self.observations:
            return None
            
        action_key = f"{action}:{','.join(args)}"
        failures = [
            obs for obs in self.observations 
            if obs.status == "error" and 
            f"{obs.action}:{','.join(args) if 'args' in obs.details else ''}" == action_key
        ]
        
        return failures if failures else None
    
    class Config:
        # Exclude the `page` attribute during serialization
        arbitrary_types_allowed = True
        json_encoders = {
            Page: lambda v: None,  # Prevent serialization of arbitrary objects
        }


class InputState(BaseModel):
    """
    Represents the input state of the agent.
    """
    testing: bool = Field(default=False, description="Flag indicating if the agent is in testing mode")
    input: str = Field(description="The input text provided to the agent")
    page: Optional[Page] = Field(default=None, exclude=True)  # Non-serializable Playwright page object
    test_actions: Optional[List[Prediction]] = Field(default_factory=list, description="The action to be tested")
    human_intervention: bool = False

    class Config:
        # Exclude the `page` attribute during serialization
        arbitrary_types_allowed = True
        json_encoders = {
            Page: lambda v: None,  # Prevent serialization of arbitrary objects
        }

class OutputState(BaseModel):
    """
    Represents the output state of the agent.
    """
    img: Optional[str] = Field(description="Base64-encoded image of the webpage")
    bboxes: Optional[List[BBox]] = Field(default_factory=list, description="List of bounding boxes annotated on the webpage")
    prediction: Optional[Prediction] = Field(description="The agent's predicted action and arguments")
    scratchpad: Optional[List[BaseMessage]] = Field(default_factory=list, description="Intermediate steps or system messages")
    observation: Optional[str] = ""
    ids: Optional[List[int]] = Field(default_factory=list)


class StrOutput(BaseModel):
    """
    Represents the structured output of the LLM.
    """
    thought: str = Field(..., description="Your brief thoughts (briefly summarize the info that will help ANSWER)")
    action: str = Field(..., description="The action you want to take")
    args: list[str] = Field(..., description="The arguments for the action")

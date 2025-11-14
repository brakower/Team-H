from pydantic import BaseModel, Field
from typing import Dict, Any

class AgentAction(BaseModel):
    """Represents an action taken by the agent."""
    tool: str = Field(..., description="Name of the tool to use")
    tool_input: Dict[str, Any] = Field(..., description="Input parameters for the tool")
    log: str = Field(default="", description="Log of the agent's reasoning")

class AgentStep(BaseModel):
    """Represents a single step in the agent execution."""
    action: AgentAction = Field(..., description="The action taken")
    observation: str = Field(..., description="Observation from executing the action")

class AgentFinish(BaseModel):
    """Represents the final result from the agent."""
    return_values: Dict[str, Any] = Field(..., description="Return values from the agent")
    log: str = Field(default="", description="Log of the agent's final reasoning")
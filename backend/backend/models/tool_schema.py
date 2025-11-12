from pydantic import BaseModel, Field
from typing import Dict, Any

class ToolSchema(BaseModel):
    """JSON Schema representation of a tool."""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for tool parameters"
    )
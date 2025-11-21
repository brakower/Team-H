from typing import Optional, List
from pydantic import BaseModel

class RubricItem(BaseModel):
    id: str
    label: str
    description: str
    max_points: int
    items: Optional[List[str]] = None # for required elements or checklists

class RubricSchema(BaseModel):
    rubric_items: List[RubricItem]
    total_points: int
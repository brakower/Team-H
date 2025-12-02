from typing import Optional, List
from pydantic import BaseModel

class RubricItem(BaseModel):
    id: str
    title: str
    max_score: int
    prompt_template: str
    weight: Optional[int]

class RubricSchema(BaseModel):
    rubric_items: List[RubricItem]
    total_points: int
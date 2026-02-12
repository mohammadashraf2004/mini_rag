from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional

class DataChunk(BaseModel):
    _id: Optional[ObjectId]
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., ge=0)  # Ensure chunk_order is non-negative
    chunk_project_id: ObjectId

    class Config:
        arbitrary_types_allowed = True
        
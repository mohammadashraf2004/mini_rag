from pydantic import BaseModel, Field,validator
from typing import List, Optional
from bson import ObjectId

class Project(BaseModel):
    _id : Optional[str]
    project_id: str = Field(..., min_length=1)

    @validator('project_id')
    def project_id_must_be_valid(cls, v):
        if not v.isalnum():
            raise ValueError("Project ID must be alphanumeric")
        return v
    
    class Config:
        arbitrary_types_allowed = True
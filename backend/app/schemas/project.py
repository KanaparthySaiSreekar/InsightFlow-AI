from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    original_filename: Optional[str]
    schema_json: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class SchemaUpdate(BaseModel):
    schema_json: Dict[str, Any]  # User can edit the AI-generated schema

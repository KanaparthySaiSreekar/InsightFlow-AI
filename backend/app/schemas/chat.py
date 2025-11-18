from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sql_query: Optional[str]
    query_result: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    project_id: int
    title: Optional[str] = None


class ChatResponse(BaseModel):
    id: int
    project_id: int
    title: Optional[str]
    created_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatQueryRequest(BaseModel):
    chat_id: int
    query: str


class ChatQueryResponse(BaseModel):
    message: MessageResponse
    data: Optional[Any] = None  # Query result data
    visualization_type: Optional[str] = None  # Suggested chart type

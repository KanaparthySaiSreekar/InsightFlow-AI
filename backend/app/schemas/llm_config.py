from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class LLMConfigCreate(BaseModel):
    provider: Literal["openai", "google", "anthropic"]
    api_key: str  # Raw API key (will be encrypted before storage)


class LLMConfigUpdate(BaseModel):
    provider: Literal["openai", "google", "anthropic"]
    api_key: str


class LLMConfigResponse(BaseModel):
    id: int
    provider: str
    is_active: int
    created_at: datetime
    # Note: We never return the encrypted_api_key for security

    class Config:
        from_attributes = True

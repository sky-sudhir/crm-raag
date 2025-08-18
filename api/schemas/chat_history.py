from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

# --- Schema for Reading Data ---
# This defines the shape of a chat history record when you send it from your API.
class ChatHistoryRead(BaseModel):
    id: str
    question: str
    answer: str
    citation: Optional[dict] = None
    latency: Optional[int] = None
    token_prompt: Optional[int] = None
    token_completion: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # This config allows Pydantic to create this schema directly from
    # the SQLAlchemy ChatHistory model object.
    model_config = {
        "from_attributes": True
    }


# --- Schema for Creating Data ---
# This defines the shape of the data your API expects when a client
# wants to create a new chat history record.
class ChatHistoryCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    citation: Optional[dict] = None
    latency: Optional[int] = None
    token_prompt: Optional[int] = None
    token_completion: Optional[int] = None
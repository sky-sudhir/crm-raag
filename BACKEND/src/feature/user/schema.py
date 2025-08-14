from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Literal

class UserResponseModel(BaseModel):
    id: UUID
    name: str
    email: str
    categories: List[UUID]
    role: Literal["admin", "user"]
    rag_type: Literal["basic", "advanced", "customized"]
    created_at: datetime

    model_config = {
        "from_attributes": True  # replaces orm_mode in v2
    }

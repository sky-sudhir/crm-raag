from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ReservedSubdomainBase(BaseModel):
    subdomain: str = Field(
        ..., 
        min_length=3, 
        max_length=100, 
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        examples=["api", "docs-v2"]
    )
    description: Optional[str] = Field(None, max_length=500, examples=["Reserved for the main API endpoint."])

class ReservedSubdomainCreate(ReservedSubdomainBase):
    pass

class ReservedSubdomainUpdate(BaseModel):
    subdomain: Optional[str] = Field(
        None, 
        min_length=3, 
        max_length=100, 
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    description: Optional[str] = Field(None, max_length=500)

class ReservedSubdomainRead(ReservedSubdomainBase):
    id: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
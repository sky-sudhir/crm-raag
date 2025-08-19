from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CategoryBase(BaseModel):
    """Base schema for category data."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Technology"])

class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass

class CategoryUpdate(BaseModel):
    """Schema for updating an existing category. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, examples=["Technology"])

class CategoryRead(CategoryBase):
    """Schema for reading category data."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

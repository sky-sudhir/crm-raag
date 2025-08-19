import enum
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from api.models.user import UserRole # Import the role enum

class UserBase(BaseModel):
    """Base schema for user data."""
    name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["johndoe@example.com"])
    role: UserRole = UserRole.ROLE_USER

class UserCreate(UserBase):
    """Schema for creating a new user. Includes password and category mapping."""
    password: str = Field(..., min_length=8, examples=["strongpassword123"])
    category_ids: List[str] = Field(default=[], examples=[["cat1", "cat2"]], description="List of category IDs to associate with the user")

class UserUpdate(BaseModel):
    """Schema for updating an existing user. All fields are optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, examples=["John Doe"])
    email: Optional[EmailStr] = Field(None, examples=["johndoe@example.com"])
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8, examples=["newpassword123"])
    category_ids: Optional[List[str]] = Field(None, examples=[["cat1", "cat2"]], description="List of category IDs to associate with the user")

class UserRead(UserBase):
    """Schema for reading user data. Excludes sensitive info like password."""
    id: str
    is_owner: bool
    created_at: datetime
    updated_at: datetime
    categories: List[dict] = Field(default=[], description="Associated categories")

    model_config = {
        "from_attributes": True  # Enables creating the schema from an ORM model
    }
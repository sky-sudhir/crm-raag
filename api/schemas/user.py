import enum
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from api.models.user import UserRole # Import the role enum

class UserBase(BaseModel):
    """Base schema for user data."""
    name: str = Field(..., min_length=2, max_length=100, examples=["John Doe"])
    email: EmailStr = Field(..., examples=["johndoe@example.com"])
    role: UserRole = UserRole.ROLE_USER
    is_owner: bool = False

class UserCreate(UserBase):
    """Schema for creating a new user. Includes password."""
    password: str = Field(..., min_length=8, examples=["strongpassword123"])

class UserUpdate(BaseModel):
    """Schema for updating an existing user. All fields are optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100, examples=["John Doe"])
    email: Optional[EmailStr] = Field(None, examples=["johndoe@example.com"])
    role: Optional[UserRole] = None
    is_owner: Optional[bool] = None

class UserRead(UserBase):
    """Schema for reading user data. Excludes sensitive info like password."""
    id: str
    

    model_config = {
        "from_attributes": True  # Enables creating the schema from an ORM model
    }


class UserRole(str, enum.Enum):
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"
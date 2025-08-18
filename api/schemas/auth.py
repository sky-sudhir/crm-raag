from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Schema for the user login request body."""
    email: EmailStr
    password: str
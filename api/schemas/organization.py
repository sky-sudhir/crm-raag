# api/schemas/organization.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class OrgSignupRequest(BaseModel):
    email: EmailStr
    name: str
    rag_type: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: int

class CreateOrganizationRequest(BaseModel):
    email: EmailStr
    org_name: str   # Organization name (global)
    name: str
    schema_name: str       # Owner user name
    subdomain:str
    password: str
    status: str = "ACTIVE"
    rag_type: str = "BASIC"

class OrganizationOut(BaseModel):
    id: str
    email: str
    name: str
    schema_name: str
    subdomain: str
    created_at: datetime
    updated_at: datetime
    status: str
    rag_type: str
    
    class Config:
        from_attributes = True
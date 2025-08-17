# api/schemas/organization.py
from pydantic import BaseModel, EmailStr

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
    name: str       # Owner user name
    subdomain:str
    password: str
    status: str = "ACTIVE"
    rag_type: str = "BASIC"
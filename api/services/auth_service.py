import datetime
import random
from re import sub
from fastapi import HTTPException
from sqlalchemy import select,text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import Base
from api.models.organization import Organization
from api.models.otp import OTP
from api.models.user import get_user_model
from api.schemas.organization import CreateOrganizationRequest
from api.services.onboarding_service import OnboardingService
from api.schemas.user import UserRole
from api.utils.email_sender import send_email
from api.utils.schema_manager import SchemaManager
from api.utils.security import hash_password
from api.utils.util_response import APIResponse

from sqlalchemy.ext.asyncio import AsyncSession
class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.schema_manager = SchemaManager(session)

    async def signup(self, email: str):
   
   
        otp_code = random.randint(100000, 999999)
        expires_at = datetime.now() + datetime.timedelta(minutes=5)

        org= await self.session.execute(
            select(Organization).where(Organization.email == email)
        )
        org = org.scalar_one_or_none()
        if org:
            raise APIResponse(message="Organization already exists with this email").model_dump()

        result = await self.session.execute(select(OTP).where(OTP.email == email))
        otp_entry = result.scalar_one_or_none()

        if otp_entry:
            # Update existing OTP
            otp_entry.otp = otp_code
            otp_entry.expires_at = expires_at
        else:
            # Create new OTP record
            otp_entry = OTP(email=email, otp=otp_code, expires_at=expires_at)
            self.session.add(otp_entry)

        await self.session.commit()

        # Send OTP via email
        await send_email(email, otp_code)

        return APIResponse(message="OTP sent to email").model_dump()
    
    async def verify_otp(self,email: str, otp: int):
        result = await self.session.execute(select(OTP).where(OTP.email == email))
        otp_entry = result.scalar_one_or_none()

        if not otp_entry:
            raise HTTPException(status_code=400, detail="No OTP found for this email")

        if otp_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired")

        if otp_entry.otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # ✅ OTP verified — you can create Organization/User entry here
        return APIResponse(message="OTP verified successfully, user can be logged in").model_dump()

    async def create_organization_with_owner(self, payload: CreateOrganizationRequest):
        onboarding_service = OnboardingService(self.session)
        schema_name = payload.subdomain.lower()

        # 1. Check if org already exists
        result = await self.session.execute(
            select(Organization).where(Organization.subdomain == payload.subdomain)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization with this subdomain already exists")

        # 2. Create the public Organization record
        org = Organization(
            email=payload.email,
            name=payload.org_name,
            schema=schema_name,
            subdomain=payload.subdomain,
            status=payload.status.upper(),
            rag_type=payload.rag_type.upper(),
        )
        self.session.add(org)
        
        # 3. Provision the tenant's schema and tables
        await onboarding_service.provision_tenant(schema_name)

        # 4. Create the owner user INSIDE the new tenant schema
        TenantUser = get_user_model(schema_name)
        hashed_pw = hash_password(payload.password)
        owner = TenantUser(
            name=payload.name,
            email=payload.email,
            password=hashed_pw,
            role=UserRole.ROLE_ADMIN,
            is_owner=True,
        )
        self.session.add(owner)

        # 5. Commit the entire transaction
        await self.session.commit()

        # Refresh objects to get DB-generated values
        await self.session.refresh(org)
        await self.session.refresh(owner)

        # Return a success response
        return APIResponse(
            message="Organization and owner created successfully",
            data={ "organization_id": org.id, "owner_id": owner.id }
        )

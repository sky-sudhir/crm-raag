import datetime
import random
from re import sub
from fastapi import HTTPException
from sqlalchemy import select,text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import Base
from api.models.organization import Organization
from api.models.otp import OTP
from api.models.user import User, get_user_model
from api.schemas.organization import CreateOrganizationRequest
from api.schemas.user import UserRole
from api.utils.email_sender import send_email
from api.utils.schema_manager import SchemaManager
from api.utils.security import create_jwt_token, hash_password, verify_password
from api.utils.util_response import APIResponse
from api.db.tenant import tenant_schema




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
    
    async def login(self, email: str, password: str):
        user=await self.session.execute(select(User).where(User.email == email))
        user = user.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid User")

        is_valid =verify_password(plain_password=password, hashed_password=user.password)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid User or Password")

        token = create_jwt_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
            tenant=tenant_schema.get()
        )

        return APIResponse(message="Login successful",data={"token": token}).model_dump()

    async def create_organization_with_owner(self, payload):
        schema_name = payload.subdomain.lower()

        async with self.session.begin():  # single transaction
            # 1. Check if org already exists
            result = await self.session.execute(
                select(Organization).where(Organization.email == payload.email)
            )
            existing_org = result.scalar_one_or_none()
            if existing_org:
                raise HTTPException(
                    status_code=400,
                    detail="Organization with this email already exists"
                )

            # 2. Ensure schema
            await self.schema_manager.ensure_schema(schema_name)

            # 3. Create org record
            org = Organization(
                email=payload.email,
                name=payload.org_name,
                schema=schema_name,
                subdomain=payload.subdomain,
                status=payload.status.upper(),
                rag_type=payload.rag_type.upper(),
            )
            self.session.add(org)

            # 4. Create user table
            User = get_user_model(schema_name)
            await self.schema_manager.create_tables([User])

            # 5. Insert owner user
            hashed_pw = hash_password(payload.password)
            owner = User(
                name=payload.name,
                email=payload.email,
                password=hashed_pw,
                role=UserRole.ROLE_ADMIN,
                is_owner=True,
            )
            self.session.add(owner)

        # 🔄 refresh after commit
        await self.session.refresh(org)
        await self.session.refresh(owner)

        return APIResponse(
            message="Organization and owner created successfully",
            data={
                "organization": {
                    "id": str(org.id),
                    "email": org.email,
                    "name": org.name,
                    # "schema": org.schema,
                    "subdomain": org.subdomain,
                    "rag_type": org.rag_type.value,
                    "status": org.status.value,
                    "created_at": org.created_at,
                },
                "owner": {
                    "id": owner.id,
                    "name": owner.name,
                    "email": owner.email,
                    "role": owner.role.value,
                    "is_owner": owner.is_owner,
                    "created_at": owner.created_at,
                },
            },
        )
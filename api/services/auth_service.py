import datetime
import random
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import all necessary models, schemas, and services
from api.models.organization import Organization
from api.models.otp import OTP
from api.models.user import UserRole, get_user_model # Use the correctly named factory
from api.schemas.organization import CreateOrganizationRequest
from api.services.onboarding_service import OnboardingService
from api.utils.email_sender import send_email
from api.utils.schema_manager import SchemaManager
from api.utils.security import hash_password, verify_password, create_jwt_token
from api.utils.util_response import APIResponse
from api.db.tenant import tenant_schema

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.schema_manager = SchemaManager(session)

    # ... (Your signup, verify_otp, and login methods remain here without changes) ...
    async def signup(self, email: str):
        # ... (no changes)
        otp_code = random.randint(100000, 999999)
        expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)
        org = await self.session.execute(select(Organization).where(Organization.email == email))
        if org.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Organization already exists with this email")
        otp_entry = await self.session.execute(select(OTP).where(OTP.email == email))
        otp_entry = otp_entry.scalar_one_or_none()
        if otp_entry:
            otp_entry.otp = otp_code
            otp_entry.expires_at = expires_at
        else:
            otp_entry = OTP(email=email, otp=otp_code, expires_at=expires_at)
            self.session.add(otp_entry)
        await self.session.commit()
        await send_email(email, otp_code)
        return APIResponse(message="OTP sent to email")

    async def verify_otp(self, email: str, otp: int):
        # ... (no changes)
        result = await self.session.execute(select(OTP).where(OTP.email == email))
        otp_entry = result.scalar_one_or_none()
        if not otp_entry:
            raise HTTPException(status_code=400, detail="No OTP found for this email")
        if otp_entry.expires_at < datetime.datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired")
        if otp_entry.otp != otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
        return APIResponse(message="OTP verified successfully")

    async def login(self, email: str, password: str):
        # ... (no changes)
        from api.models.user import User # Import the simple blueprint for login
        user_result = await self.session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        if not user or not verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid email or password")
        token = create_jwt_token(user_id=user.id, email=user.email, role=user.role, tenant=tenant_schema.get())
        return APIResponse(message="Login successful", data={"token": token})



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
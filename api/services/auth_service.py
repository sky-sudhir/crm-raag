# api/services/auth_service.py
import datetime
import random
from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import secrets
from api.db.database import Base
# Import the Enum types along with the model
from api.models.organization import Organization, OrgStatus, RagType
from api.models.otp import OTP
from api.models.reserved_subdomain import ReservedSubdomain
from api.models.user import UserRole, get_user_model, User as UserBlueprint
from api.schemas.organization import CreateOrganizationRequest
from api.services.user_service import UserService
from api.utils.email_sender import send_email
from api.utils.security import hash_password, verify_password, create_jwt_token
from api.utils.util_response import APIResponse
from api.db.tenant import tenant_schema
from api.utils.TenantUtils import TenantUtils

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def signup(self, email: str):
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
        user_result = await self.session.execute(select(UserBlueprint).where(UserBlueprint.email == email))
        user = user_result.unique().scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        
        if not verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid email or password")

        token = create_jwt_token(user_id=user.id, email=user.email, role=user.role, tenant=tenant_schema.get())
        user_data=await UserService(self.session).get_user_by_email(email=user.email)

        return APIResponse(message="Login successful", data={"token": token,
                                                             "user":user_data})

    async def create_organization_with_owner(self, payload: CreateOrganizationRequest):
        subdomain = payload.subdomain.lower()
        unique_slug = secrets.token_hex(8)
        schema_name = f"{subdomain}_{unique_slug}"
        async with self.session.begin():
            stmt_reserved = select(ReservedSubdomain).where(ReservedSubdomain.subdomain == subdomain)
            result_reserved = await self.session.execute(stmt_reserved)
            if result_reserved.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The subdomain '{payload.subdomain}' is reserved by redagent.dev and cannot be used."
                )

            stmt_exists = select(Organization).where(
                (Organization.email == payload.email) | (Organization.subdomain == subdomain)
            )
            result_exists = await self.session.execute(stmt_exists)
            if result_exists.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Org with this email or subdomain already exists.")

            await self.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

            new_org = Organization(
                email=payload.email,
                name=payload.org_name,
                schema_name=schema_name,  # <-- Store the generated unique schema name
                subdomain=subdomain, # <-- Store the public-facing subdomain
                status=OrgStatus(payload.status.upper()),
                rag_type=RagType(payload.rag_type.upper()),
            )
            self.session.add(new_org)

            async with self.session.begin_nested():
                conn = await self.session.connection()
                tenant_tables = TenantUtils.get_tenant_tables()
                tenant_tables = [tbl for tbl in tenant_tables if tbl.name != 'reserved_subdomains']
                for table in tenant_tables:
                    table.schema = schema_name
                await conn.run_sync(Base.metadata.create_all, tables=tenant_tables)
                for table in tenant_tables:
                    table.schema = None
            
            UserForSchema = get_user_model(schema_name)
            hashed_password = hash_password(payload.password)
            owner_user = UserForSchema(
                name=payload.name, email=payload.email, password=hashed_password,
                role=UserRole.ROLE_ADMIN, is_owner=True,
            )
            self.session.add(owner_user)
            await self.session.flush()
        await self.session.refresh(new_org)
        token = create_jwt_token(user_id=owner_user.id, email=owner_user.email, role=owner_user.role, tenant=new_org.schema_name)
        # // tenant = subdomain
        return APIResponse(
            message="Organization and owner created successfully",
            data={
                "organization": {
                    "id": str(new_org.id), "email": new_org.email, "name": new_org.name,
                    "subdomain": new_org.subdomain,
                    "rag_type": new_org.rag_type.value,
                    "status": new_org.status.value,
                    "created_at": new_org.created_at,
                },
                "owner": {
                    "id": str(owner_user.id), "name": owner_user.name, "email": owner_user.email,
                    "role": owner_user.role.value, "is_owner": owner_user.is_owner,
                    "created_at": owner_user.created_at,
                },
                "token": token
            },
        )
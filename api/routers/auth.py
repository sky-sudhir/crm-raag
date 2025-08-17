# api/routers/auth.py
# api/routers/auth.py
import random
import uuid
import enum
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.orm import declarative_base

from api.db.database import get_db, Base   # ✅ ensure Base comes from your db.database
from api.models.otp import OTP
from api.models.organization import Organization
from api.utils.email_sender import send_email
from api.utils.security import hash_password  # ✅ create this util if not exists
from api.models.user import UserRole, get_user_model  # ✅ you need to expose UserRole + dynamic user model factory
from api.schemas.organization import CreateOrganizationRequest, VerifyOTPRequest


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup")
async def signup(email: str, db: AsyncSession = Depends(get_db)):
    otp_code = random.randint(100000, 999999)
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Check if email already exists in OTP table
    result = await db.execute(select(OTP).where(OTP.email == email))
    otp_entry = result.scalar_one_or_none()

    if otp_entry:
        # Update existing OTP
        otp_entry.otp = otp_code
        otp_entry.expires_at = expires_at
    else:
        # Create new OTP record
        otp_entry = OTP(email=email, otp=otp_code, expires_at=expires_at)
        db.add(otp_entry)

    await db.commit()

    # Send OTP via email
    await send_email(email, otp_code)

    return {"message": "OTP sent to email"}


@router.post("/verify-otp")
async def verify_otp(email: str, otp: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OTP).where(OTP.email == email))
    otp_entry = result.scalar_one_or_none()

    if not otp_entry:
        raise HTTPException(status_code=400, detail="No OTP found for this email")

    if otp_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    if otp_entry.otp != otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ OTP verified — you can create Organization/User entry here
    return {"message": "OTP verified successfully, user can be logged in"}


@router.post("/create-organization")
async def create_organization(
    payload: CreateOrganizationRequest,
    db: AsyncSession = Depends(get_db)
):
    schema_name = payload.schema.lower().replace(" ", "_")
    print(f"👉 Starting organization creation for email={email}, schema={schema_name}")

    # 1. Check if organization already exists
    result = await db.execute(select(Organization).where(Organization.email == email))
    existing_org = result.scalar_one_or_none()
    print(f"🔍 Organization lookup result: {existing_org}")

    if existing_org:
        print("❌ Organization already exists, aborting.")
        raise HTTPException(status_code=400, detail="Organization with this email already exists")

    # 2. Create schema in Postgres
    print(f"🛠 Creating schema: {schema_name}")
    async with db.bind.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    print(f"✅ Schema {schema_name} created.")

    # 3. Hash password
    hashed_pw = hash_password(payload.password)
    print(f"🔑 Password hashed for email={payload.email}")

    # 4. Create org record in global schema
    org = Organization(
        email=payload.email,
        name=payload.org_name,
        schema=schema_name,
        status=payload.status.upper(),
        rag_type=payload.rag_type.upper()
    )
    db.add(org)
    print("📌 Organization object added to session.")

    # 5. Create users table inside the schema
    User = get_user_model(schema_name)
    print(f"📝 Generated User model for schema={schema_name}: {User}")
    async with db.bind.begin() as conn:
        print("⚙️ Creating users table inside schema...")
        await conn.run_sync(Base.metadata.create_all, tables=[User.__table__])
        print("✅ Users table created.")

    # 6. Insert first user (org owner)
    owner = User(
        name=payload.name,
        email=payload.email,
        password=hashed_pw,
        role=UserRole.ROLE_ADMIN,
        is_owner=True
    )
    db.add(owner)
    print(f"👤 Owner user prepared: {owner}")

    # 7. Commit everything
    print("💾 Committing transaction...")
    await db.commit()
    print("✅ Transaction committed!")

    await db.refresh(org)
    await db.refresh(owner)
    print(f"🎉 Org and Owner refreshed from DB. OrgID={org.id}, OwnerID={owner.id}")

    return {
        "organization": {
            "id": str(org.id),
            "email": org.email,
            "name": org.name,
            "schema": org.schema,
            "rag_type": org.rag_type.value,
            "status": org.status.value,
            "created_at": org.created_at,
        },
        "user": {
            "id": owner.id,
            "name": owner.name,
            "email": owner.email,
            "role": owner.role.value,
            "is_owner": owner.is_owner,
            "created_at": owner.created_at,
        }
    }

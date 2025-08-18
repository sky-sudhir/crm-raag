# File: api/routers/auth.py
from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# --- IMPORT THE CORRECT DEPENDENCIES ---
from api.db.tenant import get_db_public_session
from api.db.database import get_unscoped_db_session

from api.services.auth_service import AuthService
from api.schemas.organization import CreateOrganizationRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", status_code=HTTPStatus.OK)
async def signup(email: str, db: AsyncSession = Depends(get_db_public_session)): # <-- Use public session
    return await AuthService(db).signup(email)

@router.post("/verify-otp")
async def verify_otp(email: str, otp: int, db: AsyncSession = Depends(get_db_public_session)): # <-- Use public session
    return await AuthService(db).verify_otp(email, otp)

@router.post("/create-organization")
async def create_organization(
    payload: CreateOrganizationRequest,
    db: AsyncSession = Depends(get_unscoped_db_session)
):
    return await AuthService(db).create_organization_with_owner(payload)
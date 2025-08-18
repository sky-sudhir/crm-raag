# api/routers/auth.py
# api/routers/auth.py
from http import HTTPStatus
import random
import uuid
import enum
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from api.db.database import get_db, Base
from api.models.otp import OTP
from api.models.organization import Organization
from api.services.auth_service import AuthService
from api.utils.email_sender import send_email
from api.utils.security import hash_password  # ✅ create this util if not exists
from api.models.user import UserRole, get_user_model  # ✅ you need to expose UserRole + dynamic user model factory
from api.schemas.organization import CreateOrganizationRequest
from api.utils.response import create_response


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup",status_code=HTTPStatus.OK)
async def signup(email: str, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).signup(email)

@router.post("/verify-otp")
async def verify_otp(email: str, otp: int, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).verify_otp(email, otp)

@router.post("/create-organization")
async def create_organization(
    payload: CreateOrganizationRequest,
    db: AsyncSession = Depends(get_db)
):
    return await AuthService(db).create_organization_with_owner(payload)
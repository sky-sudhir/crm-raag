import select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.tenant import get_db_public, get_db_tenant
from api.models import organization, user
from api.schemas.user import UserCreate, UserRead
from api.services.user_service import UserService
from api.middleware.jwt_middleware import get_current_user


# Initialize the router with a prefix and tags for API documentation
router = APIRouter(prefix="/api/users", tags=["Users"])



@router.get("/me", status_code=201, summary="Get current user")
async def get_current_user(db: AsyncSession = Depends(get_db_tenant), user: dict = Depends(get_current_user)):
    return await UserService(db).get_user_by_email( email=user["email"])

@router.get("/public", status_code=201, summary="Create a new user")
async def create_new_user(db: AsyncSession = Depends(get_db_public)):
    db_users = await db.execute(Select(organization.Organization))
    db_users = db_users.scalars().all()
    print("db_users" , db_users)
    return db_users

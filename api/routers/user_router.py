from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db.tenant import get_db_public, get_db_tenant
from api.schemas.user import UserCreate, UserUpdate, UserRead
from api.services.user_service import UserService
from api.middleware.jwt_middleware import get_current_user

# Initialize the router with a prefix and tags for API documentation
router = APIRouter(prefix="/api/users", tags=["Users"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=UserRead, status_code=201, summary="Create a new user")
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Create a new user with specified role and category associations."""
    user_service = UserService(db)
    return await user_service.create_user(user_data)

@router.get("/", response_model=List[UserRead], summary="Get all users")
async def get_all_users(db: AsyncSession = Depends(get_db_tenant)):
    """Get all users with their category associations."""
    user_service = UserService(db)
    return await user_service.get_all_users()

@router.get("/me", response_model=UserRead, summary="Get current user")
async def get_current_user_detail(
    db: AsyncSession = Depends(get_db_tenant), 
    current_user: dict = Depends(get_current_user)
):
    """Get the currently authenticated user."""
    user_service = UserService(db)
    return await user_service.get_user_by_email(email=current_user["email"])

@router.get("/{user_id}", response_model=UserRead, summary="Get user by ID")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Get a specific user by ID."""
    user_service = UserService(db)
    return await user_service.get_user_by_id(user_id)

@router.put("/{user_id}", response_model=UserRead, summary="Update user")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Update a user's information and category associations."""
    user_service = UserService(db)
    return await user_service.update_user(user_id, user_data)

@router.delete("/{user_id}", summary="Delete user")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_tenant)
):
    """Delete a user (cannot delete owner users)."""
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}

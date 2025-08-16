from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from api.db.database import get_db
from api.schemas.user import UserCreate, UserRead, UserUpdate
from api.crud import user as crud

# Initialize the router with a prefix and tags for API documentation
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead, status_code=201, summary="Create a new user")
async def create_new_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user after checking if the email is already registered.
    """
    db_user = await crud.get_user_by_email(db, email=data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db, data)

@router.get("/", response_model=List[UserRead], summary="Get a list of all users")
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a paginated list of all users.
    """
    return await crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserRead, summary="Get a user by ID")
async def get_user_details(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the details of a single user by their unique ID.
    """
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=UserRead, summary="Update a user")
async def update_existing_user(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    """
    Updates a user's details. Prevents updating to an email that is already in use.
    """
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for email conflict if the email is being changed
    if data.email and data.email != db_user.email:
        existing_user = await crud.get_user_by_email(db, email=data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="This email is already registered")
            
    return await crud.update_user(db, db_user, data)

@router.delete("/{user_id}", status_code=204, summary="Delete a user")
async def delete_existing_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a user by their unique ID.
    """
    db_user = await crud.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await crud.delete_user(db, db_user)
    
    # A 204 No Content response must not have a body
    return None
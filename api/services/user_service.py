import datetime
import random
from fastapi import HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional

from api.models.organization import Organization
from api.models.otp import OTP
from api.models.user import User
from api.models.category import Category
from api.schemas.user import UserCreate, UserUpdate, UserRead
from api.utils.email_sender import send_email
from api.utils.util_response import APIResponse
from api.utils.security import hash_password, verify_password

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def create_user(self, user_data: UserCreate) -> UserRead:
        """Create a new user with category associations."""
        existing_user = await self.get_user_by_email_internal(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Validate categories exist
        if user_data.category_ids:
            categories = await self.session.execute(
                select(Category).where(Category.id.in_(user_data.category_ids))
            )
            found_categories = categories.scalars().all()
            if len(found_categories) != len(user_data.category_ids):
                raise HTTPException(status_code=400, detail="One or more categories not found")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user (is_owner is always False for CRUD created users)
        user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role,
            is_owner=False  # Always False as per requirement
        )
        
        self.session.add(user)
        await self.session.flush()  # Get the user ID
        
        # Associate categories using direct relationship assignment
        if user_data.category_ids:
            # Load the user with categories relationship to initialize it
            await self.session.refresh(user, ['categories'])
            
            # Get categories
            categories_result = await self.session.execute(
                select(Category).where(Category.id.in_(user_data.category_ids))
            )
            categories_list = list(categories_result.scalars().all())
            
            # Assign categories
            user.categories = categories_list
        
        await self.session.commit()
        await self.session.refresh(user)
        
        curr_user= await self.get_user_by_id(user.id)

        return APIResponse(data=curr_user,message="Created Successfully")
    
    async def get_user_by_id(self, user_id: str) -> UserRead:
        """Get a user by ID with categories."""
        result = await self.session.execute(
            select(User).options(selectinload(User.categories)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert to dict and add categories
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_owner": user.is_owner,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "categories": [{"id": cat.id, "name": cat.name} for cat in user.categories]
        }
        return APIResponse(data=user_dict,message="Retrived Successfully")
    

    async def get_user_by_email(self, email: str) -> UserRead:
        """Get a user by email with categories."""
        result = await self.session.execute(
            select(User).options(selectinload(User.categories)).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert to dict and add categories
        user_dict = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_owner": user.is_owner,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "categories": [{"id": cat.id, "name": cat.name} for cat in user.categories]
        }
        return APIResponse(data=user_dict,message="Retrived Successfully")


    async def get_user_by_email_internal(self, email: str) -> Optional[User]:
        """Internal method to get user by email without schema conversion."""
        result = await self.session.execute(select(User).where(User.email == email))
        result= result.scalar_one_or_none()
        return APIResponse(data=result,message="Retrived Successfully")

    async def get_all_users(self) -> List[UserRead]:
        """Get all users with their categories."""
        result = await self.session.execute(
            select(User).options(selectinload(User.categories))
        )
        users = result.scalars().all()
        
        user_list = []
        for user in users:
            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "is_owner": user.is_owner,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "categories": [{"id": cat.id, "name": cat.name} for cat in user.categories]
            }
            user_list.append(UserRead.model_validate(user_dict))
        
        return APIResponse(data=user_list,message="Retrived Successfully")


    async def update_user(self, user_id: str, user_data: UserUpdate) -> UserRead:
        """Update a user."""
        result = await self.session.execute(
            select(User).options(selectinload(User.categories)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if email is being changed and if it conflicts
        if user_data.email and user_data.email != user.email:
            existing_user = await self.get_user_by_email_internal(user_data.email)
            if existing_user:
                raise HTTPException(status_code=400, detail="User with this email already exists")

        # Validate categories if provided
        if user_data.category_ids is not None:
            if user_data.category_ids:  # Not empty list
                categories = await self.session.execute(
                    select(Category).where(Category.id.in_(user_data.category_ids))
                )
                found_categories = categories.scalars().all()
                if len(found_categories) != len(user_data.category_ids):
                    raise HTTPException(status_code=400, detail="One or more categories not found")

        # Update fields if provided
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.password is not None:
            user.password = hash_password(user_data.password)

        # Update categories if provided
        if user_data.category_ids is not None:
            if user_data.category_ids:
                categories = await self.session.execute(
                    select(Category).where(Category.id.in_(user_data.category_ids))
                )
                user.categories = categories.scalars().all()
            else:
                user.categories = []  # Clear all categories

        await self.session.commit()
        await self.session.refresh(user)
        
        curr_user= await self.get_user_by_id(user.id)
        return APIResponse(data=curr_user,message="UPdated Successfully")


    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prevent deletion of owner users
        if user.is_owner:
            raise HTTPException(status_code=400, detail="Cannot delete owner user")

        await self.session.execute(delete(User).where(User.id == user_id))
        await self.session.commit()
        return APIResponse(data=None,message="Deleted Successfully")


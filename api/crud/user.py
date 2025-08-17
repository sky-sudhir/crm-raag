from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from api.models.user import User
from api.schemas.user import UserCreate, UserUpdate
# from api.utils.security import hash_password

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """Creates a new user in the database with a hashed password."""
    hashed_pwd = hash_password(data.password)
    user = User(
        name=data.name,
        email=data.email,
        password=hashed_pwd,
        role=data.role,
        is_owner=data.is_owner
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """Retrieves a list of users with pagination."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

async def get_user(db: AsyncSession, user_id: str) -> Optional[User]:
    """Retrieves a single user by their ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieves a single user by their email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """Updates the fields of an existing user."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user: User):
    """Deletes a user from the database."""
    await db.delete(user)
    await db.commit()
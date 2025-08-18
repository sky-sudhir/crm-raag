# api/models/user.py
import enum
import uuid
from sqlalchemy import String, Boolean, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from api.db.database import Base
from datetime import datetime

class UserRole(str, enum.Enum):
    """Enumeration for user roles."""
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"

# This is the single, schema-agnostic blueprint for the 'users' table.
# It has NO __table_args__ defining a schema. This is the version used by
# Base.metadata to discover which tables a tenant should have.
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.ROLE_USER, nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

def get_user_model(schema: str):
    """
    Dynamically creates a new User class mapped to a specific schema.
    This is used for inserting the first user during the onboarding transaction.
    It uses a separate declarative base to avoid metadata conflicts.
    """
    DynamicBase = declarative_base()

    class UserForSchema(DynamicBase):
        __tablename__ = "users"
        __table_args__ = {"schema": schema}

        id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        name: Mapped[str] = mapped_column(String(100), nullable=False)
        email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
        password: Mapped[str] = mapped_column(String(255), nullable=False)
        role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.ROLE_ADMIN, nullable=False)
        is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    return UserForSchema
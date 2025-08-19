# api/models/user.py
import enum
import uuid
from sqlalchemy import String, Boolean, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column,declarative_base
from api.db.database import Base
from datetime import datetime

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    String,
    func,
)



class UserRole(str, enum.Enum):
    """Enumeration for user roles."""
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"

class UserRole(PyEnum):
    ROLE_USER = "ROLE_USER"
    ROLE_ADMIN = "ROLE_ADMIN"


# 1. Create an Abstract Base Class or Mixin with all the common columns
class UserBase:
    """
    An abstract class/mixin that defines the columns for a user model.
    It is not mapped to any database table itself.
    """
    __abstract__ = True

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


# 2. Refactor the function to inherit from the base
def get_user_model(schema: str):
    DynamicBase = declarative_base()
    """Dynamically create a User model for a specific schema."""
    class UserForSchema(DynamicBase, UserBase):
        __tablename__ = "users"
        __table_args__ = {"schema": schema}

    return UserForSchema


class User(Base, UserBase):
    __tablename__ = "users"
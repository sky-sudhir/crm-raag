# api/models/user.py
import enum
import uuid
from sqlalchemy import String, Boolean, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column
from api.db.database import Base
from datetime import datetime


class UserRole(str, enum.Enum):
    """Enumeration for user roles."""
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"


def get_user_model(schema: str):
    """Dynamically create a User model for a specific schema."""
    class User(Base):
        __tablename__ = "users"
        __table_args__ = {"schema": schema}

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

    return User

import enum
import uuid
from sqlalchemy import String, Boolean, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.database import Base
from datetime import datetime
from typing import List, TYPE_CHECKING

# This is a placeholder for a future Category model.
# If you create a Category model, you can uncomment these lines
# to establish the one-to-many relationship.
# if TYPE_CHECKING:
#     from .category import Category

class UserRole(str, enum.Enum):
    """Enumeration for user roles."""
    ROLE_ADMIN = "ROLE_ADMIN"
    ROLE_USER = "ROLE_USER"

class User(Base):
    """
    SQLAlchemy model for the 'users' table.
    """
    __tablename__ = "users"

    # Columns based on the provided schema
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # Stores the hashed password
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.ROLE_USER, nullable=False)
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Example of a one-to-many relationship.
    # This assumes a 'Category' model will be created with a foreign key back to the user.
    # categories: Mapped[List["Category"]] = relationship("Category", back_populates="owner")
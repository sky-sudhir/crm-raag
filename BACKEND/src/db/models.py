from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from uuid import uuid4
from datetime import datetime
import enum

from src.db.main import Base

class RoleEnum(str, enum.Enum):
    super = "SUPERADMIN"
    admin = "ROLE_ADMIN"
    user = "ROLE_USER"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    categories = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    rag_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

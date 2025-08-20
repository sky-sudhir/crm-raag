
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from api.db.database import Base

class OrgStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"

class RagType(str, enum.Enum):
    BASIC = "BASIC"
    ADV = "ADV"
    CUS = "CUS"

class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = {"schema": "public"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    schema_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    subdomain: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    status: Mapped[OrgStatus] = mapped_column(
        Enum(OrgStatus, name="orgstatus", schema="public"), default=OrgStatus.ACTIVE
    )
    rag_type: Mapped[RagType] = mapped_column(
        Enum(RagType, name="ragtype", schema="public"), default=RagType.BASIC
    )
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from api.db.database import Base

class ReservedSubdomain(Base):
    """
    Stores a list of subdomain names that are reserved for platform use
    and cannot be used by tenants for their workspaces.
    """
    __tablename__ = "reserved_subdomains"
    __table_args__ = {"schema": "public"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # The reserved subdomain name, e.g., "api", "docs", "public"
    subdomain: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # A description of why this name is reserved
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
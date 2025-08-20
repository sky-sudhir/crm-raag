# api/models/audit_logs.py
import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    String,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base,declared_attr
from api.db.database import Base


class AuditEventType(PyEnum):
    ERROR = "ERROR"
    QUERY = "QUERY"
    UPLOAD = "UPLOAD"
    EMBEDDING_CREATE = "EMBEDDING_CREATE"
    API_CALL = "API_CALL"


class AuditLogBase:
    """
    Abstract base for audit logs.
    """
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # FK → user
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )



def get_audit_logs_model(schema: str, *, DynamicBase=None):
    DynamicBase = DynamicBase or declarative_base()

    class AuditLogForSchema(DynamicBase, AuditLogBase):
        __tablename__ = "audit_logs"
        __table_args__ = {"schema": schema}

        user_id: Mapped[str] = mapped_column(
            String(36), ForeignKey(f"{schema}.users.id", ondelete="CASCADE"), nullable=False
        )

    return AuditLogForSchema


class AuditLog(Base, AuditLogBase):
    __tablename__ = "audit_logs"

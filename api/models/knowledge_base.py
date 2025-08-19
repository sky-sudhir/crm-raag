import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from api.db.database import Base

class KBStatus(PyEnum):
    UPLOADED = "UPLOADED"
    INGESTING = "INGESTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DELETED = "DELETED"

class KnowledgeBaseBase:
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # FK only (no relationship to User)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # FK only (no relationship to Category)
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    json: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[KBStatus] = mapped_column(Enum(KBStatus), default=KBStatus.UPLOADED)

    s3_url: Mapped[str] = mapped_column(Text, nullable=True)
    mime: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

def get_knowledge_base_model(schema: str, *, DynamicBase=None):
    DynamicBase = DynamicBase or declarative_base()

    class KnowledgeBaseSchema(DynamicBase, KnowledgeBaseBase):
        __tablename__ = "knowledge_base"
        __table_args__ = {"schema": schema}

        user_id: Mapped[str] = mapped_column(
            String(36), ForeignKey(f"{schema}.users.id", ondelete="CASCADE"), nullable=False
        )
        category_id: Mapped[str] = mapped_column(
            String(36), ForeignKey(f"{schema}.categories.id", ondelete="CASCADE"), nullable=False
        )

    return KnowledgeBaseSchema

class KnowledgeBase(Base, KnowledgeBaseBase):
    __tablename__ = "knowledge_base"

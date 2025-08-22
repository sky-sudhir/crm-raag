# api/models/vector_doc.py
import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base, declared_attr
from api.db.database import Base
from pgvector.sqlalchemy import Vector


class VectorDocBase:
    """
    Abstract base for vectorized document chunks.
    """
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # 🔑 FK → User
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    @declared_attr
    def user(cls):
        return relationship("User", back_populates="vector_docs")

    # 🔑 FK → Category
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    @declared_attr
    def category(cls):
        return relationship("Category", back_populates="vector_docs")

    # 🔑 FK → KnowledgeBase (file)
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_base.id", ondelete="CASCADE"), nullable=False
    )
    @declared_attr
    def file(cls):
        return relationship("KnowledgeBase", back_populates="vector_docs")

    chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

    # Avoid reserved attribute name clash with SQLAlchemy's class-level `metadata`
    doc_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def get_vector_doc_model(schema: str, DynamicBase=None):
    if DynamicBase is None:
        DynamicBase = declarative_base()

    class VectorDocForSchema(DynamicBase):
        __tablename__ = "vector_doc"
        __table_args__ = {
            "schema": schema,
            "extend_existing": True  # Allow redefinition if table already exists
        }
        
        # Copy all the fields from VectorDocBase but without relationships
        id: Mapped[str] = mapped_column(
            String(36), primary_key=True, default=lambda: str(uuid.uuid4())
        )

        # 🔑 FK → User (no relationship) - use string references to avoid metadata registry conflicts
        user_id: Mapped[str] = mapped_column(
            String(36), nullable=False
        )

        # 🔑 FK → Category (no relationship) - use string references to avoid metadata registry conflicts
        category_id: Mapped[str] = mapped_column(
            String(36), nullable=False
        )

        # 🔑 FK → KnowledgeBase (no relationship) - use string references to avoid metadata registry conflicts
        file_id: Mapped[str] = mapped_column(
            String(36), nullable=False
        )

        chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
        chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

        embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

        # Avoid reserved attribute name clash with SQLAlchemy's class-level `metadata`
        doc_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now()
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
        )

    return VectorDocForSchema


class VectorDoc(Base, VectorDocBase):
    __tablename__ = "vector_doc"
    # No __table_args__ means this is a blueprint for tenant schemas

import enum
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, func, Enum, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.db.database import Base


class DocumentStatus(str, enum.Enum):
    """Enumeration for document processing status."""
    UPLOADED = "UPLOADED"
    INGESTING = "INGESTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class DocumentCategory(Base):
    """Model for document categories with role-based access control."""
    __tablename__ = "document_categories"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_roles: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    is_general: Mapped[bool] = mapped_column(default=False)  # General category accessible by all
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    vector_documents: Mapped[List["VectorDocument"]] = relationship(
        "VectorDocument", back_populates="category", cascade="all, delete-orphan"
    )
    knowledge_bases: Mapped[List["KnowledgeBase"]] = relationship(
        "KnowledgeBase", back_populates="category", cascade="all, delete-orphan"
    )


class KnowledgeBase(Base):
    """Model for storing document metadata and processing information."""
    __tablename__ = "knowledge_base"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="documentstatus", schema="public"), default=DocumentStatus.UPLOADED, nullable=False
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_categories.id"), nullable=False
    )
    s3_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    category: Mapped["DocumentCategory"] = relationship("DocumentCategory", back_populates="knowledge_bases")
    vector_documents: Mapped[List["VectorDocument"]] = relationship(
        "VectorDocument", back_populates="knowledge_base", cascade="all, delete-orphan"
    )


class VectorDocument(Base):
    """Model for storing document chunks with embeddings."""
    __tablename__ = "vector_doc"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_categories.id"), nullable=False
    )
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("knowledge_base.id"), nullable=False
    )
    chunk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256 hash
    embedding: Mapped[str] = mapped_column("embedding", nullable=False)  # pgvector will handle this as vector type
    doc_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    category: Mapped["DocumentCategory"] = relationship("DocumentCategory", back_populates="vector_documents")
    knowledge_base: Mapped["KnowledgeBase"] = relationship("KnowledgeBase", back_populates="vector_documents")

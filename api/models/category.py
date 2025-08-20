import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship
from api.db.database import Base

class CategoryBase:
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

def get_category_model(schema: str, *, DynamicBase=None):
    # use caller's registry to keep everything in the same mapping context
    DynamicBase = DynamicBase or declarative_base()

    class CategoryForSchema(DynamicBase, CategoryBase):
        __tablename__ = "categories"
        __table_args__ = {"schema": schema}

    return CategoryForSchema

class Category(Base, CategoryBase):
    __tablename__ = "categories"
    # Relationship required by VectorDocBase.back_populates("category")
    vector_docs = relationship("VectorDoc", back_populates="category", cascade="all, delete-orphan")

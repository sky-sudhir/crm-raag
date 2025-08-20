import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, DateTime, Enum, String, func, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from api.db.database import Base
from api.models.audit_log import AuditLog, get_audit_logs_model
from api.models.category import Category, get_category_model
from api.models.chat_tabs import ChatTab, get_chat_tabs_model  # <-- import to register default; inject for dynamic
# NOTE: do not import KnowledgeBase here since we keep it FK-only by your requirement

class UserRole(PyEnum):
    ROLE_USER = "ROLE_USER"
    ROLE_ADMIN = "ROLE_ADMIN"

# PUBLIC association table (default registry)
user_categories = Table(
    "user_categories",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", String(36), ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class UserBase:
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped["UserRole"] = mapped_column(
        Enum(UserRole, name="userrole", schema="public"), default=UserRole.ROLE_USER, nullable=False
    )
    is_owner: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

def get_user_model(schema: str):
    # Single registry for ALL per-schema classes
    DynamicBase = declarative_base()

    # Build the per-schema dependent classes in THE SAME registry
    CategoryForSchema = get_category_model(schema, DynamicBase=DynamicBase)
    ChatTabForSchema = get_chat_tabs_model(schema, DynamicBase=DynamicBase)
    AuditLogForSchema = get_audit_logs_model(schema, DynamicBase=DynamicBase)
    # KnowledgeBase remains FK-only; you can create it in the same registry if you need the class object
    # from api.models.knowledge_base import get_knowledge_base_model
    # KnowledgeBaseForSchema = get_knowledge_base_model(schema, DynamicBase=DynamicBase)

    # Association table in the SAME metadata/registry
    dynamic_user_categories = Table(
        "user_categories",
        DynamicBase.metadata,
        Column("user_id", String(36), ForeignKey(f"{schema}.users.id", ondelete="CASCADE"), primary_key=True),
        Column("category_id", String(36), ForeignKey(f"{schema}.categories.id", ondelete="CASCADE"), primary_key=True),
        schema=schema,
    )

    class UserForSchema(DynamicBase, UserBase):
        __tablename__ = "users"
        __table_args__ = {"schema": schema}

        # Use CLASS OBJECTS (not strings) so resolution stays inside this registry
        categories : Mapped[list[CategoryForSchema]] = relationship(
            CategoryForSchema,
            secondary=dynamic_user_categories,
            backref="users",
            lazy="joined",
            cascade="all, delete",
        )

        # Relationship to ChatTab via class object; ChatTab model keeps only FK, no back_populates needed
        chat_tabs: Mapped[list[ChatTabForSchema]] = relationship(
            ChatTabForSchema,
            primaryjoin="UserForSchema.id == ChatTabForSchema.user_id",
            cascade="all, delete-orphan",
            passive_deletes=True,
        )
        audit_logs: Mapped[list[AuditLogForSchema]] = relationship(
            AuditLogForSchema,
            primaryjoin="UserForSchema.id == AuditLogForSchema.user_id",
            cascade="all, delete-orphan",
            passive_deletes=True,
        )

        # DO NOT add a relationship to KnowledgeBase since you want it FK-only.
        # If later you want it, create KnowledgeBaseForSchema in this registry and relate using the class object.

    # Expose dependent classes if needed by caller
    UserForSchema._Category = CategoryForSchema
    UserForSchema._ChatTab = ChatTabForSchema
    UserForSchema._AuditLog = AuditLogForSchema
    # UserForSchema._KnowledgeBase = KnowledgeBaseForSchema  # if you enable it

    return UserForSchema

# Default/public model (shares global Base)
class User(Base, UserBase):
    __tablename__ = "users"

    # Public relationships can safely use string names because these classes
    # are imported above and live in the same global registry.
    categories: Mapped[list["Category"]] = relationship(
        "Category",
        secondary=user_categories,
        backref="users",
        lazy="joined",
        cascade="all, delete",
    )

    # Only if you want it on the public model; your per-schema code should use the dynamic class.
    chat_tabs: Mapped[list["ChatTab"]] = relationship(
        "ChatTab",
        primaryjoin="User.id == ChatTab.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        primaryjoin="User.id == AuditLog.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # Relationship required by VectorDocBase.back_populates("user")
    vector_docs: Mapped[list["VectorDoc"]] = relationship(
        "VectorDoc",
        primaryjoin="User.id == VectorDoc.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
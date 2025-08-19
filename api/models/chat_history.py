# api/models/chat_history.py
import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base,declared_attr
from api.db.database import Base


class ChatHistoryBase:
    """
    Abstract base for chat history.
    """
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=True)

    citation: Mapped[dict] = mapped_column(JSON, nullable=True)
    latency: Mapped[int] = mapped_column(Integer, nullable=True)

    token_prompt: Mapped[int] = mapped_column(Integer, nullable=True)
    token_completion: Mapped[int] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ✅ Dynamic factory for multi-tenancy
def get_chat_history_model(schema: str):
    DynamicBase = declarative_base()

    class ChatHistoryForSchema(DynamicBase, ChatHistoryBase):
        __tablename__ = "chat_history"
        __table_args__ = {"schema": schema}

    return ChatHistoryForSchema


# ✅ Default/global schema model
class ChatHistory(Base, ChatHistoryBase):
    __tablename__ = "chat_history"

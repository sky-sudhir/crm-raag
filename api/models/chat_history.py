import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func, JSON, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from api.db.database import Base

# This is a class-based "blueprint" for a tenant-specific table.
# Notice there is NO __table_args__ defining a schema. It is schema-agnostic.
class ChatHistory(Base):
    """
    Represents a single question-and-answer interaction in a tenant's workspace.
    This model is a schema-agnostic blueprint.
    """
    __tablename__ = "chat_history"

    # Define the columns based on your table structure
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
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
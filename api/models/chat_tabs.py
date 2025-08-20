import uuid
from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from api.db.database import Base

# Association for ChatTab <-> ChatHistory (this can stay registry-agnostic)
chat_tab_history_association = Table(
    "chat_tab_history_association",
    Base.metadata,
    Column("chat_tab_id", String(36), ForeignKey("chat_tabs.id", ondelete="CASCADE"), primary_key=True),
    Column("chat_history_id", String(36), ForeignKey("chat_history.id", ondelete="CASCADE"), primary_key=True),
)

class ChatTabBase:
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # FK only – no relationship here to avoid cross-registry lookups
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)

def get_chat_tabs_model(schema: str, *, DynamicBase=None):
    DynamicBase = DynamicBase or declarative_base()

    # If you also have a per-schema association table, qualify those FKs too:
    chat_tab_history_assoc_dynamic = Table(
        "chat_tab_history_association",
        DynamicBase.metadata,
        Column("chat_tab_id", String(36), ForeignKey(f"{schema}.chat_tabs.id", ondelete="CASCADE"), primary_key=True),
        Column("chat_history_id", String(36), ForeignKey(f"{schema}.chat_history.id", ondelete="CASCADE"), primary_key=True),
        schema=schema,
    )

    class ChatTabForSchema(DynamicBase, ChatTabBase):
        __tablename__ = "chat_tabs"
        __table_args__ = {"schema": schema}

        # 🔴 IMPORTANT: override the FK inherited from the mixin
        user_id: Mapped[str] = mapped_column(
            String(36),
            ForeignKey(f"{schema}.users.id", ondelete="CASCADE"),
            nullable=False,
        )

        # Do NOT declare relationships here that point to classes outside this registry

    ChatTabForSchema._assoc_chat_history = chat_tab_history_assoc_dynamic
    return ChatTabForSchema

class ChatTab(Base, ChatTabBase):
    __tablename__ = "chat_tabs"

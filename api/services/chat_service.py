from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from typing import List, Optional

# Import the SQLAlchemy models and Pydantic schema
from api.models.chat_history import ChatHistory
from api.models.chat_tabs import ChatTab, chat_tab_history_association
from api.schemas.chat_history import ChatHistoryCreate

class ChatHistoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chat_record(self, data: ChatHistoryCreate) -> ChatHistory:
        """
        Creates a new chat history record in the database for the current tenant.
        """
        # Create a new SQLAlchemy model instance from the Pydantic schema
        new_chat_record = ChatHistory(**data.model_dump())
        
        self.session.add(new_chat_record)
        await self.session.commit()
        await self.session.refresh(new_chat_record)
        
        return new_chat_record

    async def get_all_chat_records(self) -> List[ChatHistory]:
        """
        Retrieves all chat history records for the current tenant.
        """
        # Build the query to select all records, ordered by the most recent
        stmt = select(ChatHistory).order_by(ChatHistory.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # --- Chat sessions (tabs) ---
    async def create_chat_tab(self, name: str, user_id: str) -> ChatTab:
        tab = ChatTab(name=name, user_id=user_id)
        self.session.add(tab)
        await self.session.commit()
        await self.session.refresh(tab)
        return tab

    async def list_chat_tabs(self, user_id: str) -> List[ChatTab]:
        stmt = select(ChatTab).where(ChatTab.user_id == user_id).order_by(ChatTab.id.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_tab_messages(self, chat_tab_id: str) -> List[ChatHistory]:
        stmt = (
            select(ChatHistory)
            .join(
                chat_tab_history_association,
                chat_tab_history_association.c.chat_history_id == ChatHistory.id,
            )
            .where(chat_tab_history_association.c.chat_tab_id == chat_tab_id)
            .order_by(ChatHistory.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def append_message_to_tab(self, chat_tab_id: str, data: ChatHistoryCreate) -> ChatHistory:
        # Persist message
        message = ChatHistory(**data.model_dump())
        self.session.add(message)
        await self.session.flush()

        # Link to tab via association table
        await self.session.execute(
            insert(chat_tab_history_association).values(
                chat_tab_id=chat_tab_id,
                chat_history_id=message.id,
            )
        )

        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def build_history_context(self, chat_tab_id: str, max_messages: int = 20) -> str:
        messages = await self.get_tab_messages(chat_tab_id)
        if not messages:
            return ""
        # Keep only the last N messages for prompt length
        tail = messages[-max_messages:]
        parts: List[str] = []
        for m in tail:
            parts.append(f"Q: {m.question}\nA: {m.answer if m.answer else ''}")
        return "\n\n".join(parts)
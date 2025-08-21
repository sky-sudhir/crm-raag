from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from typing import List, Optional

# Import the SQLAlchemy models and Pydantic schema
from api.models.chat_history import ChatHistory, get_chat_history_model
from api.models.chat_tabs import ChatTab, chat_tab_history_association, get_chat_tabs_model
from api.models.user import get_user_model
from api.schemas.chat_history import ChatHistoryCreate
from api.db.tenant import tenant_schema

class ChatHistoryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # Get the current tenant schema and initialize dynamic models
        self.schema_name = tenant_schema.get()
        if self.schema_name != "public":
            # Use the get_user_model function which creates all related models in the same registry
            user_model_class = get_user_model(self.schema_name)
            # Get the ChatTab model from the user model's registry (this has proper FK to users)
            self.ChatTabModel = user_model_class._ChatTab
            # Create ChatHistory model separately (no FK dependencies)
            self.ChatHistoryModel = get_chat_history_model(self.schema_name)
            # Get the schema-aware association table
            self.chat_tab_history_association = self.ChatTabModel._assoc_chat_history
        else:
            self.ChatHistoryModel = ChatHistory
            self.ChatTabModel = ChatTab
            self.chat_tab_history_association = chat_tab_history_association

    async def create_chat_record(self, data: ChatHistoryCreate) -> ChatHistory:
        """
        Creates a new chat history record in the database for the current tenant.
        """
        # Create a new SQLAlchemy model instance from the Pydantic schema
        new_chat_record = self.ChatHistoryModel(**data.model_dump())
        
        self.session.add(new_chat_record)
        await self.session.commit()
        await self.session.refresh(new_chat_record)
        
        return new_chat_record

    async def get_all_chat_records(self) -> List[ChatHistory]:
        """
        Retrieves all chat history records for the current tenant.
        """
        # Build the query to select all records, ordered by the most recent
        stmt = select(self.ChatHistoryModel).order_by(self.ChatHistoryModel.created_at.desc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # --- Chat sessions (tabs) ---
    async def create_chat_tab(self, name: str, user_id: str) -> ChatTab:
        tab = self.ChatTabModel(name=name, user_id=user_id)
        self.session.add(tab)
        await self.session.commit()
        await self.session.refresh(tab)
        return tab

    async def list_chat_tabs(self, user_id: str) -> List[ChatTab]:
        stmt = select(self.ChatTabModel).where(self.ChatTabModel.user_id == user_id).order_by(self.ChatTabModel.id.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_tab_messages(self, chat_tab_id: str) -> List[ChatHistory]:
        stmt = (
            select(self.ChatHistoryModel)
            .join(
                self.chat_tab_history_association,
                self.chat_tab_history_association.c.chat_history_id == self.ChatHistoryModel.id,
            )
            .where(self.chat_tab_history_association.c.chat_tab_id == chat_tab_id)
            .order_by(self.ChatHistoryModel.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def append_message_to_tab(self, chat_tab_id: str, data: ChatHistoryCreate) -> ChatHistory:
        # Persist message
        message = self.ChatHistoryModel(**data.model_dump())
        self.session.add(message)
        await self.session.flush()

        # Link to tab via association table
        await self.session.execute(
            insert(self.chat_tab_history_association).values(
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

    async def initiate_new_chat(self, user_id: str, tab_name: str, first_message: ChatHistoryCreate) -> tuple[ChatTab, ChatHistory]:
        """
        Creates a new chat tab and adds the first message to it in a single transaction.
        Returns both the tab and the first message.
        """
        # Create the tab first
        tab = self.ChatTabModel(name=tab_name, user_id=user_id)
        self.session.add(tab)
        await self.session.flush()  # Get the tab ID without committing

        # Create the first message
        message = self.ChatHistoryModel(**first_message.model_dump())
        self.session.add(message)
        await self.session.flush()  # Get the message ID without committing

        # Link message to tab
        await self.session.execute(
            insert(self.chat_tab_history_association).values(
                chat_tab_id=tab.id,
                chat_history_id=message.id,
            )
        )

        # Commit everything together
        await self.session.commit()
        await self.session.refresh(tab)
        await self.session.refresh(message)
        
        return tab, message
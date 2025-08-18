from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

# Import the SQLAlchemy model and Pydantic schema
from api.models.chat_history import ChatHistory
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
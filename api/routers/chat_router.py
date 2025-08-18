from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Import the correct tenant-aware dependency
from api.db.tenant import get_db_tenant

# Import the schemas and the new service
from api.schemas.chat_history import ChatHistoryCreate, ChatHistoryRead
from api.services.chat_service import ChatHistoryService

# Initialize the router
router = APIRouter(prefix="/chat", tags=["Chat History"])

@router.post("/", response_model=ChatHistoryRead, status_code=201, summary="Create a new chat history record")
async def create_chat_history(
    data: ChatHistoryCreate,
    db: AsyncSession = Depends(get_db_tenant) # <-- Use the tenant session
):
    """
    Creates a new chat history record for the currently authenticated tenant.
    The database session is automatically scoped to the correct tenant's schema.
    """
    service = ChatHistoryService(db)
    new_record = await service.create_chat_record(data)
    return new_record


@router.get("/", response_model=List[ChatHistoryRead], summary="Get all chat history records for the tenant")
async def get_chat_history(
    db: AsyncSession = Depends(get_db_tenant) # <-- Use the tenant session
):
    """
    Retrieves a list of all chat history records for the currently
    authenticated tenant.
    """
    service = ChatHistoryService(db)
    records = await service.get_all_chat_records()
    return records
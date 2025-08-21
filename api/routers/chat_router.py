from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

# Import the correct tenant-aware dependency
from api.db.tenant import get_db_tenant

# Import the schemas and the new service
from api.schemas.chat_history import (
    ChatHistoryCreate,
    ChatHistoryRead,
    ChatTabCreate,
    ChatTabRead,
    ChatSendRequest,
    ChatSendResponse,
)
from api.services.chat_service import ChatHistoryService
from api.middleware.jwt_middleware import get_current_user
from api.services.rag_service import RAGService
from api.services.llm_service import LLMService

# Initialize the router
router = APIRouter(prefix="/api/chat", tags=["Chat"])

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


# --- Chat Tabs (sessions) ---
@router.post("/tabs", response_model=ChatTabRead, summary="Create a chat session (tab)")
async def create_chat_tab(
    payload: ChatTabCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_tenant),
):
    service = ChatHistoryService(db)
    tab = await service.create_chat_tab(name=payload.name, user_id=current_user["sub"])
    return tab


@router.get("/tabs", response_model=List[ChatTabRead], summary="List my chat sessions")
async def list_chat_tabs(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_tenant),
):
    service = ChatHistoryService(db)
    tabs = await service.list_chat_tabs(user_id=current_user["sub"])
    return tabs


@router.get("/tabs/{tab_id}/messages", response_model=List[ChatHistoryRead], summary="List messages in a session")
async def list_tab_messages(
    tab_id: str,
    db: AsyncSession = Depends(get_db_tenant),
):
    service = ChatHistoryService(db)
    messages = await service.get_tab_messages(tab_id)
    return messages


@router.post("/tabs/{tab_id}/send", response_model=ChatSendResponse, summary="Send a message in a session with context")
async def send_message(
    tab_id: str,
    req: ChatSendRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_tenant),
):
    # Build prior conversation context
    service = ChatHistoryService(db)
    history_context = await service.build_history_context(tab_id)

    # RAG: get accessible categories for this user and search
    rag_service = RAGService(embedding_model="google", api_key=None)
    accessible_categories = await rag_service.get_accessible_categories(
        current_user["sub"], current_user["tenant"], db
    )
    if not accessible_categories:
        raise HTTPException(status_code=403, detail="No accessible categories found")

    search_results = await rag_service.search_similar_documents(
        req.query,
        [current_user["role"]],
        accessible_categories,
        db,
        req.top_k,
    )

    # LLM generate with history context
    llm = LLMService(model=req.model)
    answer = await llm.generate_response(req.query, search_results, history_context)

    # Persist chat message and link to tab
    message = await service.append_message_to_tab(
        tab_id,
        ChatHistoryCreate(
            question=req.query,
            answer=answer,
            citation=None,
            latency=None,
            token_prompt=None,
            token_completion=None,
        ),
    )

    return ChatSendResponse(
        message=message,
        sources=[doc.chunk_text for doc, _ in search_results],
        total_sources=len(search_results),
        processing_time_ms=0.0,  # could be measured if needed
    )
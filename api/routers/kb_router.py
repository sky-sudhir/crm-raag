import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from api.models.knowledge_base import KBStatus, get_knowledge_base_model, KnowledgeBase
from api.schemas.rag_schemas import (
    KnowledgeBaseCreate, KnowledgeBaseResponse,
    RAGQueryRequest, RAGQueryResponse, VectorDocumentResponse,
    DocumentUploadResponse, DocumentProcessingStatus, RAGChatRequest, RAGChatResponse
)
from api.services.rag_service import RAGService
from api.services.llm_service import LLMService
from api.middleware.jwt_middleware import get_current_user
from api.services.chat_service import ChatHistoryService
from api.schemas.chat_history import ChatHistoryCreate
from api.db.tenant import get_db_tenant
from api.services.kb_service import KnowledgeBaseService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])

# Service instances
rag_service = RAGService(embedding_model="google", api_key=None)
kb_service = KnowledgeBaseService(rag_service)
llm_service = LLMService(model="openai")


def _create_knowledge_base_response(doc) -> KnowledgeBaseResponse:
    """Create a KnowledgeBaseResponse from a document model."""
    return KnowledgeBaseResponse(
        id=doc.id,
        user_id=doc.user_id,
        file_name=doc.file_name,
        category_id=doc.category_id,
        mime=doc.mime or "",
        file_size=doc.file_size or 0,
        status=doc.status,
        json=doc.json,
        s3_url=doc.s3_url,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _create_vector_document_response(doc, score: float) -> VectorDocumentResponse:
    """Create a VectorDocumentResponse from a document and similarity score."""
    return VectorDocumentResponse(
        id=doc.id,
        user_id=doc.user_id,
        category_id=doc.category_id,
        file_id=doc.file_id,
        chunk_id=doc.chunk_id,
        chunk_text=doc.chunk_text,
        embedding=doc.embedding,
        metadata=doc.doc_metadata or {},
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def _validate_document_access(
    user_id: str,
    tenant_schema: str,
    category_id: str,
    db_session: AsyncSession
) -> None:
    """Validate that the user has access to upload to the specified category."""
    # Check if category exists
    category_exists = await kb_service.ensure_category_exists(
        category_id=category_id,
        tenant_schema=tenant_schema,
        db_session=db_session,
    )
    if not category_exists:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check user access to category
    has_access = await kb_service.ensure_access_to_category(
        user_id=user_id,
        tenant_schema=tenant_schema,
        category_id=category_id,
        db_session=db_session,
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this category")


async def _handle_background_task_error(
    kb_id: str,
    tenant_schema: str,
    db_session: AsyncSession,
    error: Exception
) -> None:
    """Handle errors in background task queueing by updating document status."""
    logger.error(f"Failed to queue background task for document {kb_id}: {str(error)}")
    
    try:
        # Create appropriate model for the tenant
        if tenant_schema != "public":
            KnowledgeBaseModel = get_knowledge_base_model(tenant_schema)
        else:
            KnowledgeBaseModel = KnowledgeBase
            
        await db_session.execute(
            update(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.id == kb_id)
            .values(status=KBStatus.FAILED)
        )
        await db_session.commit()
    except Exception as update_error:
        logger.error(f"Failed to update document status to FAILED: {str(update_error)}")
        raise HTTPException(status_code=500, detail="Failed to queue document processing")


@router.get("/documents", response_model=List[KnowledgeBaseResponse], summary="Get User Documents")
async def get_user_documents(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant)
):
    """Retrieve all documents for the current user."""
    try:
        documents = await kb_service.get_user_documents(
            user_id=current_user["sub"],
            tenant_schema=current_user["tenant"],
            db_session=db_session,
        )

        return [_create_knowledge_base_response(doc) for doc in documents]
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@router.get("/documents/{document_id}/status", response_model=DocumentProcessingStatus, summary="Get Document Status")
async def get_document_status(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant)
):
    """Get the processing status of a specific document."""
    try:
        document = await kb_service.get_document_status(
            document_id=document_id,
            user_id=current_user["sub"],
            tenant_schema=current_user["tenant"],
            db_session=db_session,
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentProcessingStatus(
            id=document.id,
            status=document.status,
            message=f"Document is in {document.status} status"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch document status")


@router.post("/upload", response_model=DocumentUploadResponse, summary="Upload Document")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant),
):
    """Upload a document for processing and vectorization."""
    try:
        # Validate user access to category
        await _validate_document_access(
            user_id=current_user["sub"],
            tenant_schema=current_user["tenant"],
            category_id=category_id,
            db_session=db_session,
        )

        # Create knowledge base record
        kb_record = await kb_service.create_kb_record(
            user_id=current_user["sub"],
            file_name=file.filename,
            category_id=category_id,
            mime=file.content_type,
            file_size=file.size,
            tenant_schema=current_user["tenant"],
            db_session=db_session,
        )

        # Read file content
        file_content_bytes = await file.read()
        logger.info(f"Read file content, size: {len(file_content_bytes)} bytes")
        
        # Queue background processing task
        try:
            background_tasks.add_task(
                kb_service.process_document_background,
                kb_record.id,
                file_content_bytes,
                file.content_type,
                current_user["sub"],
                category_id,
                current_user["tenant"],
            )
            logger.info(f"Successfully queued background task for document {kb_record.id}")
        except Exception as bg_error:
            await _handle_background_task_error(
                kb_record.id,
                current_user["tenant"],
                db_session,
                bg_error
            )

        return DocumentUploadResponse(
            id=kb_record.id,
            status=KBStatus.UPLOADED,
            message="Document uploaded. Processing started."
        )
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.post("/query", response_model=RAGQueryResponse, summary="Query KB")
async def query_kb(
    query_request: RAGQueryRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant),
):
    """Query the knowledge base for relevant documents."""
    try:
        # Get accessible categories for the user
        accessible_categories = await rag_service.get_accessible_categories(
            current_user["sub"], current_user["tenant"], db_session
        )
        if not accessible_categories:
            raise HTTPException(status_code=403, detail="No accessible categories")

        # Search for similar documents
        search_results = await rag_service.search_similar_documents(
            query_request.query,
            [],
            accessible_categories,
            db_session,
            query_request.top_k,
            current_user["tenant"]
        )

        # Convert results to response format
        response_items = [
            _create_vector_document_response(doc, score)
            for doc, score in search_results
        ]

        return RAGQueryResponse(
            query=query_request.query,
            results=response_items,
            total_results=len(response_items),
            processing_time_ms=0.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying KB: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to query knowledge base")


@router.post("/chat", response_model=RAGChatResponse, summary="Chat with KB")
async def chat_with_kb(
    chat_request: RAGChatRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant),
):
    """Chat with the knowledge base using RAG-powered responses."""
    try:
        # Set tenant search path
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        
        # Get accessible categories
        accessible_categories = await rag_service.get_accessible_categories(
            current_user["sub"], current_user["tenant"], db_session
        )
        if not accessible_categories:
            raise HTTPException(status_code=403, detail="No accessible categories")

        # Search for relevant documents
        search_results = await rag_service.search_similar_documents(
            chat_request.query,
            [],
            accessible_categories,
            db_session,
            chat_request.top_k,
            current_user["tenant"]
        )

        # Get or create default chat tab
        chat_service = ChatHistoryService(db_session)
        tabs = await chat_service.list_chat_tabs(user_id=current_user["sub"])
        
        default_tab = next(
            (tab for tab in tabs if getattr(tab, "name", None) == "KB Chat"),
            None
        )
        
        if default_tab is None:
            default_tab = await chat_service.create_chat_tab(
                name="KB Chat",
                user_id=current_user["sub"]
            )

        # Build conversation history context
        history_context = await chat_service.build_history_context(default_tab.id)

        # Generate response using LLM
        llm_service.model = chat_request.model
        answer = await llm_service.generate_response(
            chat_request.query,
            search_results,
            history_context
        )

        # Persist conversation turn
        await chat_service.append_message_to_tab(
            default_tab.id,
            ChatHistoryCreate(
                question=chat_request.query,
                answer=answer,
                citation=None,
                latency=None,
                token_prompt=None,
                token_completion=None,
            ),
        )

        return RAGChatResponse(
            query=chat_request.query,
            response=answer,
            sources=[doc.chunk_text for doc, _ in search_results],
            total_sources=len(search_results),
            processing_time_ms=0.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in KB chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to chat with knowledge base")


@router.get("/health", summary="KB Service Health Check")
async def kb_health_check(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant),
):
    """Health check endpoint to verify KB service and background task functionality."""
    try:
        # Test database connection
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        result = await db_session.execute(text("SELECT 1"))
        db_ok = result.scalar() == 1
        
        # Test background task setup
        bg_ok = await kb_service.validate_background_task_setup(current_user["tenant"])
        
        # Test RAG service
        rag_ok = True
        try:
            accessible = await rag_service.get_accessible_categories(
                current_user["sub"], current_user["tenant"], db_session
            )
            rag_ok = len(accessible) >= 0  # Just check if it doesn't throw an error
        except Exception as e:
            logger.error(f"RAG service health check failed: {str(e)}")
            rag_ok = False
        
        is_healthy = all([db_ok, bg_ok, rag_ok])
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": "ok" if db_ok else "error",
            "background_tasks": "ok" if bg_ok else "error", 
            "rag_service": "ok" if rag_ok else "error",
            "tenant": current_user["tenant"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "tenant": current_user["tenant"]
        }


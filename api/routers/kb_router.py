import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy import select, text, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import  AsyncSessionLocal
from api.models.category import Category
from api.models.knowledge_base import KnowledgeBase, KBStatus
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


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])

# Services
rag_service = RAGService(embedding_model="google", api_key=None)
llm_service = LLMService(model="openai")


@router.get("/documents", response_model=List[KnowledgeBaseResponse], summary="Get User Documents")
async def get_user_documents(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant)
):
    try:
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))

        result = await db_session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == current_user["sub"])
            .order_by(KnowledgeBase.created_at.desc())
        )
        documents = result.scalars().all()

        return [
            KnowledgeBaseResponse(
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
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents")


@router.get("/documents/{document_id}/status", response_model=DocumentProcessingStatus, summary="Get Document Status")
async def get_document_status(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant)
):
    try:
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))

        result = await db_session.execute(
            select(KnowledgeBase).where(
                and_(KnowledgeBase.id == document_id, KnowledgeBase.user_id == current_user["sub"])
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentProcessingStatus(id=document.id, status=document.status, message=f"Document is in {document.status} status")
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
    try:
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))

        # Check category exists in tenant
        cat_result = await db_session.execute(select(Category).where(Category.id == category_id))
        if cat_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Category not found")

        # Enforce access: owners can upload anywhere, non-owners must have the category
        accessible = await rag_service.get_accessible_categories(
            current_user["sub"], current_user["tenant"], db_session
        )
        if category_id not in accessible:
            raise HTTPException(status_code=403, detail="Access denied to this category")

        kb = KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=current_user["sub"],
            file_name=file.filename,
            category_id=category_id,
            mime=file.content_type,
            file_size=file.size,
            status=KBStatus.UPLOADED,
        )
        db_session.add(kb)
        await db_session.commit()
        await db_session.refresh(kb)

        file_content_bytes = await file.read()
        background_tasks.add_task(
            process_document_background,
            kb.id,
            file_content_bytes,
            file.content_type,
            current_user["sub"],
            category_id,
            current_user["tenant"],
        )

        return DocumentUploadResponse(id=kb.id, status=KBStatus.UPLOADED, message="Document uploaded. Processing started.")
    except HTTPException:
        raise
    except Exception as e:
        await db_session.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


async def process_document_background(
    knowledge_base_id: str,
    file_content: bytes,
    mime_type: str,
    user_id: str,
    category_id: str,
    tenant_schema: str,
):
    try:
        async with AsyncSessionLocal() as db_session:
            await db_session.execute(text(f'SET search_path TO "{tenant_schema}"'))

            await db_session.execute(
                update(KnowledgeBase)
                .where(KnowledgeBase.id == knowledge_base_id)
                .values(status=KBStatus.INGESTING)
            )
            await db_session.commit()

            text_content = await extract_text_from_file(file_content, mime_type)
            metadata = {"file_type": mime_type, "processing_timestamp": datetime.utcnow().isoformat()}

            vector_docs = await rag_service.process_document(
                knowledge_base_id, text_content, category_id, metadata, db_session
            )

            await rag_service.store_vector_documents(vector_docs, user_id, category_id, db_session)

            await db_session.execute(
                update(KnowledgeBase)
                .where(KnowledgeBase.id == knowledge_base_id)
                .values(status=KBStatus.COMPLETED)
            )
            await db_session.commit()
    except Exception:
        try:
            async with AsyncSessionLocal() as db_session:
                await db_session.execute(
                    update(KnowledgeBase)
                    .where(KnowledgeBase.id == knowledge_base_id)
                    .values(status=KBStatus.FAILED)
                )
                await db_session.commit()
        except Exception:
            pass


@router.post("/query", response_model=RAGQueryResponse, summary="Query KB")
async def query_kb(
    query_request: RAGQueryRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant),
):
    try:
        accessible_categories = await rag_service.get_accessible_categories(
            current_user["sub"], current_user["tenant"], db_session
        )
        if not accessible_categories:
            raise HTTPException(status_code=403, detail="No accessible categories")

        results = await rag_service.search_similar_documents(
            query_request.query, [], accessible_categories, db_session, query_request.top_k
        )

        response_items: List[VectorDocumentResponse] = []
        for doc, score in results:
            response_items.append(
                VectorDocumentResponse(
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
            )

        return RAGQueryResponse(
            query=query_request.query,
            results=response_items,
            total_results=len(response_items),
            processing_time_ms=0.0,
        )
    except Exception as e:
        logger.error(f"Error querying KB: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to query knowledge base")


@router.post("/chat", response_model=RAGChatResponse, summary="Chat with KB")
async def chat_with_kb(
    chat_request: RAGChatRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_tenant),
):
    try:
        # Ensure tenant search path for tenant-scoped tables
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        accessible_categories = await rag_service.get_accessible_categories(
            current_user["sub"], current_user["tenant"], db_session
        )
        if not accessible_categories:
            raise HTTPException(status_code=403, detail="No accessible categories")

        search_results = await rag_service.search_similar_documents(
            chat_request.query, [], accessible_categories, db_session, chat_request.top_k
        )

        # Build or reuse a default chat tab per user and build history context
        chat_service = ChatHistoryService(db_session)
        tabs = await chat_service.list_chat_tabs(user_id=current_user["sub"]) 
        default_tab = None
        for t in tabs:
            if getattr(t, "name", None) == "KB Chat":
                default_tab = t
                break
        if default_tab is None:
            default_tab = await chat_service.create_chat_tab(name="KB Chat", user_id=current_user["sub"]) 

        history_context = await chat_service.build_history_context(default_tab.id)

        llm_service.model = chat_request.model
        answer = await llm_service.generate_response(chat_request.query, search_results, history_context)

        # Persist this turn and link to the session
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
    except Exception as e:
        logger.error(f"Error in KB chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to chat with knowledge base")


async def extract_text_from_file(file_content: bytes, mime_type: str) -> str:
    try:
        if mime_type == "application/pdf":
            import io
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_out = "".join(page.extract_text() or "" for page in reader.pages)
            return text_out.strip()
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            import io
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            return "\n".join(p.text for p in doc.paragraphs)
        if mime_type.startswith("text/"):
            return file_content.decode("utf-8")
        return f"Unsupported file type: {mime_type}"
    except Exception as e:
        return f"Error extracting text: {str(e)}"



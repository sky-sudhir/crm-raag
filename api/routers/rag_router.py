import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, and_, update
import uuid
from datetime import datetime
import PyPDF2
from docx import Document

from api.db.database import get_unscoped_db_session, AsyncSessionLocal
from api.models.category import Category as DocumentCategory
from api.models.knowledge_base import KnowledgeBase, KBStatus
from api.schemas.rag_schemas import (
    DocumentCategoryCreate, DocumentCategoryUpdate, DocumentCategoryResponse,
    KnowledgeBaseCreate, KnowledgeBaseResponse,
    RAGQueryRequest, RAGQueryResponse, VectorDocumentResponse,
    DocumentUploadResponse, DocumentProcessingStatus, RAGChatRequest, RAGChatResponse
)
from api.services.rag_service import RAGService
from api.services.llm_service import LLMService
from api.middleware.jwt_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG System"])

# Initialize services
rag_service = RAGService(
    embedding_model="google",  # Can be configured via environment
    api_key=None  # Will be loaded from environment
)

llm_service = LLMService(model="openai")  # Default to OpenAI


@router.post("/categories", response_model=DocumentCategoryResponse)
async def create_category(
    category: DocumentCategoryCreate,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Create a new category (tenant-scoped)."""
    try:
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))

        existing_category = await db_session.execute(
            select(DocumentCategory).where(DocumentCategory.name == category.name)
        )
        if existing_category.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Category already exists")

        db_category = DocumentCategory(
            id=str(uuid.uuid4()),
            name=category.name,
        )
        db_category.__table__.schema = current_user["tenant"]

        db_session.add(db_category)
        await db_session.commit()
        await db_session.refresh(db_category)

        return DocumentCategoryResponse.model_validate(db_category)
    except Exception as e:
        await db_session.rollback()
        logger.error(f"Error creating category: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create category")


@router.get("/categories", response_model=List[DocumentCategoryResponse])
async def get_categories(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Get all categories accessible to the current user (via user-category association)."""
    try:
        accessible_categories = await rag_service.get_accessible_categories(
            current_user["sub"], current_user["tenant"], db_session
        )
        
        # Set the search path to the tenant's schema
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        
        # Fetch category details
        categories = []
        for category_id in accessible_categories:
            result = await db_session.execute(
                select(DocumentCategory).where(DocumentCategory.id == category_id)
            )
            category = result.scalar_one_or_none()
            if category:
                categories.append(DocumentCategoryResponse.model_validate(category))
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category_id: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Upload and process a document."""
    try:
        logger.info("=== STARTING DOCUMENT UPLOAD ===")
        
        # Validate category access
        user_roles = [current_user["role"]]
        logger.info(f"User {current_user['sub']} with roles {user_roles} trying to upload to category {category_id}")
        logger.info(f"Tenant schema: {current_user['tenant']}")
        
        # Debug: Check what categories exist before calling the service
        logger.info("Setting search path to tenant schema...")
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        logger.info("Search path set successfully")
        
        logger.info("Executing direct query for categories...")
        debug_result = await db_session.execute(select(DocumentCategory))
        debug_categories = debug_result.scalars().all()
        logger.info(f"Direct query found {len(debug_categories)} categories: {[c.name for c in debug_categories]}")
        
        logger.info("Calling RAG service to get accessible categories...")
        accessible_categories = await rag_service.get_accessible_categories(
            user_roles, current_user["tenant"], db_session
        )
        
        logger.info(f"RAG service returned accessible categories: {accessible_categories}")
        
        if category_id not in accessible_categories:
            logger.error(f"Category {category_id} not found in accessible categories: {accessible_categories}")
            raise HTTPException(status_code=403, detail="Access denied to this category")
        
        # Create knowledge base entry
        logger.info("Creating knowledge base entry...")
        knowledge_base = KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=current_user["sub"],
            file_name=file.filename,
            category_id=category_id,
            mime=file.content_type,
            file_size=file.size,
            status=KBStatus.UPLOADED
        )
        
        logger.info(f"Knowledge base object created: {knowledge_base.id}")
        db_session.add(knowledge_base)
        
        logger.info("Committing to database...")
        await db_session.commit()
        await db_session.refresh(knowledge_base)
        logger.info("Knowledge base entry created successfully!")
        
        # Read file content before passing to background task
        file_content_bytes = await file.read()
        
        # Add background task for document processing
        background_tasks.add_task(
            process_document_background,
            knowledge_base.id,
            file_content_bytes,  # Pass bytes instead of file object
            file.content_type,
            current_user["sub"],
            category_id,
            current_user["tenant"]  # Pass tenant schema
        )
        
        return DocumentUploadResponse(
            id=knowledge_base.id,
            status=KBStatus.UPLOADED,
            message="Document uploaded successfully. Processing started in background."
        )
        
    except Exception as e:
        await db_session.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


async def process_document_background(
    knowledge_base_id: str,
    file_content,
    mime_type: str,
    user_id: str,
    category_id: str,
    tenant_schema: str
):
    """Background task for processing uploaded documents."""
    try:
        # Update status to processing
        async with AsyncSessionLocal() as db_session:
            # Set search path to the tenant schema
            await db_session.execute(text(f'SET search_path TO "{tenant_schema}"'))
            logger.info(f"Processing document {knowledge_base_id} in background for tenant {tenant_schema}")
            
            # Update knowledge base status
            result = await db_session.execute(
                update(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id).values(status=KBStatus.INGESTING)
            )
            await db_session.commit()
            
            # Extract text from file
            text_content = await extract_text_from_file(file_content, mime_type)
            
            # Get file metadata
            metadata = {
                "file_type": mime_type,
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
            # Process document with RAG service
            vector_docs = await rag_service.process_document(
                knowledge_base_id, text_content, category_id, metadata, db_session
            )
            
            # Store vector documents
            stored_count = await rag_service.store_vector_documents(
                vector_docs, user_id, category_id, db_session
            )
            
            # Update knowledge base status
            result = await db_session.execute(
                update(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id).values(status=KBStatus.COMPLETED)
            )
            await db_session.commit()
            
            logger.info(f"Document {knowledge_base_id} processed successfully. Stored {stored_count} chunks.")
            
    except Exception as e:
        logger.error(f"Error processing document {knowledge_base_id}: {str(e)}")
        # Update status to failed
        try:
            async with AsyncSessionLocal() as db_session:
                result = await db_session.execute(
                    update(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id).values(status=KBStatus.FAILED)
                )
                await db_session.commit()
        except Exception as update_error:
            logger.error(f"Failed to update document status: {str(update_error)}")


@router.get("/documents/{document_id}/status", response_model=DocumentProcessingStatus)
async def get_document_status(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Get the processing status of a document."""
    try:
        # Set the search path to the tenant's schema
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        
        result = await db_session.execute(
            select(KnowledgeBase).where(
                and_(KnowledgeBase.id == document_id, KnowledgeBase.user_id == current_user['sub'])
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentProcessingStatus(
            id=document.id,
            status=document.status,
            message=f"Document is in {document.status} status"
        )
        
    except Exception as e:
        logger.error(f"Error fetching document status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch document status")


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    query_request: RAGQueryRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Query the RAG system for relevant documents."""
    try:
        start_time = datetime.utcnow()
        
        # Get user roles
        user_roles = [current_user["role"]]
        
        # Get accessible categories
        accessible_categories = await rag_service.get_accessible_categories(
            user_roles, current_user["tenant"], db_session
        )
        
        if not accessible_categories:
            raise HTTPException(status_code=403, detail="No accessible categories found")
        
        # Search for similar documents
        search_results = await rag_service.search_similar_documents(
            query_request.query,
            user_roles,
            accessible_categories,
            db_session,
            query_request.top_k,
            current_user["tenant"]
        )
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        # Convert results to response format
        results = []
        for doc, similarity in search_results:
            results.append(VectorDocumentResponse(
                id=doc.id,
                user_id=doc.user_id,
                category_id=doc.category_id,
                file_id=doc.file_id,
                chunk_id=doc.chunk_id,
                chunk_text=doc.chunk_text,
                chunk_hash=doc.chunk_hash,
                embedding=doc.embedding,
                doc_metadata=doc.doc_metadata,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            ))
        
        return RAGQueryResponse(
            query=query_request.query,
            results=results,
            total_results=len(results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error querying RAG system: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to query RAG system")


@router.post("/chat", response_model=RAGChatResponse)
async def chat_with_rag(
    chat_request: RAGChatRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Chat with the RAG system - combines retrieval and generation."""
    try:
        start_time = datetime.utcnow()
        
        # Get user roles
        user_roles = [current_user["role"]]
        
        # Get accessible categories
        accessible_categories = await rag_service.get_accessible_categories(
            user_roles, current_user["tenant"], db_session
        )
        
        if not accessible_categories:
            raise HTTPException(status_code=403, detail="No accessible categories found")
        
        # Search for similar documents
        search_results = await rag_service.search_similar_documents(
            chat_request.query,
            user_roles,
            accessible_categories,
            db_session,
            chat_request.top_k,
            current_user["tenant"]
        )
        
        # Generate response using LLM
        llm_service.model = chat_request.model  # Set the requested model
        response = await llm_service.generate_response(
            chat_request.query,
            search_results
        )
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return RAGChatResponse(
            query=chat_request.query,
            response=response,
            sources=[doc.chunk_text for doc, _ in search_results],
            total_sources=len(search_results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in RAG chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate response")


@router.get("/documents", response_model=List[KnowledgeBaseResponse])
async def get_user_documents(
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_unscoped_db_session)
):
    """Get all documents uploaded by the current user."""
    try:
        # Set the search path to the tenant's schema
        await db_session.execute(text(f'SET search_path TO "{current_user["tenant"]}"'))
        
        result = await db_session.execute(
            select(KnowledgeBase).where(KnowledgeBase.user_id == current_user['sub']).order_by(KnowledgeBase.created_at.desc())
        )
        documents = result.scalars().all()
        
        return [
            KnowledgeBaseResponse(
                id=doc.id,
                user_id=doc.user_id,
                file_name=doc.file_name,
                category_id=doc.category_id,
                mime=doc.mime,
                file_size=doc.file_size,
                status=doc.status,
                json=doc.json,
                s3_url=doc.s3_url,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error fetching user documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user documents")


async def extract_text_from_file(file_content, mime_type: str) -> str:
    """Extract text content from uploaded file based on MIME type."""
    try:
        if mime_type == "application/pdf":
            # Handle PDF files - file_content is now bytes
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Handle DOCX files - file_content is now bytes
            import io
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        
        elif mime_type.startswith("text/"):
            # Handle text files - file_content is now bytes
            return file_content.decode('utf-8')
        
        else:
            # For unsupported file types, return a placeholder
            logger.warning(f"Unsupported file type: {mime_type}")
            return f"File content from {mime_type} (text extraction not implemented)"
            
    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        return f"Error extracting text: {str(e)}"

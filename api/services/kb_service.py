import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.database import AsyncSessionLocal
from api.db.tenant import tenant_schema
from api.models.category import Category, get_category_model
from api.models.knowledge_base import KnowledgeBase, get_knowledge_base_model, KBStatus
from api.schemas.rag_schemas import VectorDocumentCreate
from api.services.rag_service import RAGService


logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for managing Knowledge Base operations and background document processing."""

    def __init__(self, rag_service: RAGService):
        """Initialize the KnowledgeBaseService with required dependencies."""
        self.rag_service = rag_service
        self.schema_name = tenant_schema.get()
        
        # Initialize dynamic models based on tenant schema
        self._initialize_models()
        
        logger.info(f"KnowledgeBaseService initialized for tenant: {self.schema_name}")

    def _initialize_models(self) -> None:
        """Initialize the appropriate models based on the tenant schema."""
        if self.schema_name != "public":
            self.KnowledgeBaseModel = get_knowledge_base_model(self.schema_name)
            self.CategoryModel = get_category_model(self.schema_name)
        else:
            self.KnowledgeBaseModel = KnowledgeBase
            self.CategoryModel = Category

    async def get_user_documents(
        self,
        user_id: str,
        tenant_schema: str,
        db_session: AsyncSession,
    ) -> List[KnowledgeBase]:
        """Retrieve all documents for a specific user."""
        await self._set_search_path(db_session, tenant_schema)
        
        result = await db_session.execute(
            select(self.KnowledgeBaseModel)
            .where(self.KnowledgeBaseModel.user_id == user_id)
            .order_by(self.KnowledgeBaseModel.created_at.desc())
        )
        return result.scalars().all()

    async def get_document_status(
        self,
        document_id: str,
        user_id: str,
        tenant_schema: str,
        db_session: AsyncSession,
    ) -> Optional[KnowledgeBase]:
        """Get the status of a specific document for a user."""
        await self._set_search_path(db_session, tenant_schema)
        
        result = await db_session.execute(
            select(self.KnowledgeBaseModel).where(
                and_(
                    self.KnowledgeBaseModel.id == document_id,
                    self.KnowledgeBaseModel.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def ensure_category_exists(
        self,
        category_id: str,
        tenant_schema: str,
        db_session: AsyncSession
    ) -> bool:
        """Check if a category exists in the specified tenant."""
        await self._set_search_path(db_session, tenant_schema)
        
        result = await db_session.execute(
            select(self.CategoryModel).where(self.CategoryModel.id == category_id)
        )
        return result.scalar_one_or_none() is not None

    async def ensure_access_to_category(
        self,
        user_id: str,
        tenant_schema: str,
        category_id: str,
        db_session: AsyncSession,
    ) -> bool:
        """Check if a user has access to a specific category."""
        accessible_categories = await self.rag_service.get_accessible_categories(
            user_id, tenant_schema, db_session
        )
        return category_id in accessible_categories

    async def create_kb_record(
        self,
        user_id: str,
        file_name: str,
        category_id: str,
        mime: Optional[str],
        file_size: Optional[int],
        tenant_schema: str,
        db_session: AsyncSession,
    ) -> KnowledgeBase:
        """Create a new knowledge base record."""
        await self._set_search_path(db_session, tenant_schema)
        
        kb_record = self.KnowledgeBaseModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            file_name=file_name,
            category_id=category_id,
            mime=mime,
            file_size=file_size,
            status=KBStatus.UPLOADED,
        )
        
        db_session.add(kb_record)
        await db_session.commit()
        
        return kb_record

    async def process_document_background(
        self,
        knowledge_base_id: str,
        file_content: bytes,
        mime_type: str,
        user_id: str,
        category_id: str,
        tenant_schema: str,
    ) -> None:
        """Process a document in the background with comprehensive error handling."""
        logger.info(f"Starting background processing for document {knowledge_base_id} in tenant {tenant_schema}")
        
        # Create dynamic models for background task
        knowledge_base_model = self._get_knowledge_base_model_for_tenant(tenant_schema)
        
        async with AsyncSessionLocal() as db_session:
            try:
                await self._process_document_successfully(
                    knowledge_base_id,
                    file_content,
                    mime_type,
                    user_id,
                    category_id,
                    tenant_schema,
                    db_session,
                    knowledge_base_model
                )
            except Exception as e:
                await self._handle_processing_error(
                    knowledge_base_id,
                    tenant_schema,
                    e,
                    knowledge_base_model
                )

    async def _process_document_successfully(
        self,
        knowledge_base_id: str,
        file_content: bytes,
        mime_type: str,
        user_id: str,
        category_id: str,
        tenant_schema: str,
        db_session: AsyncSession,
        knowledge_base_model
    ) -> None:
        """Handle successful document processing workflow."""
        logger.info("Created database session for background processing")
        await self._set_search_path(db_session, tenant_schema)

        # Update status to INGESTING
        await self._update_document_status(
            knowledge_base_id,
            KBStatus.INGESTING,
            db_session,
            knowledge_base_model
        )

        # Extract text content
        text_content = await self.extract_text_from_file(file_content, mime_type)
        logger.info(f"Extracted text content, length: {len(text_content)}")
        
        metadata = {
            "file_type": mime_type,
            "processing_timestamp": datetime.utcnow().isoformat()
        }

        # Process document into vector documents
        vector_docs = await self.rag_service.process_document(
            knowledge_base_id,
            text_content,
            category_id,
            metadata,
            db_session,
            tenant_schema
        )
        logger.info(f"Processed document into {len(vector_docs)} vector documents")

        # Store vector documents
        await self.rag_service.store_vector_documents(
            vector_docs,
            user_id,
            category_id,
            db_session,
            tenant_schema
        )
        logger.info("Stored vector documents in database")

        # Update status to COMPLETED
        await self._update_document_status(
            knowledge_base_id,
            KBStatus.COMPLETED,
            db_session,
            knowledge_base_model
        )

    async def _handle_processing_error(
        self,
        knowledge_base_id: str,
        tenant_schema: str,
        error: Exception,
        knowledge_base_model
    ) -> None:
        """Handle errors during document processing."""
        logger.error(f"Error in background processing for document {knowledge_base_id}: {str(error)}")
        logger.error(f"Exception type: {type(error).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Update status to FAILED
        await self._update_document_status_on_error(
            knowledge_base_id,
            tenant_schema,
            knowledge_base_model
        )

    async def _update_document_status(
        self,
        document_id: str,
        status: KBStatus,
        db_session: AsyncSession,
        knowledge_base_model
    ) -> None:
        """Update the status of a document."""
        await db_session.execute(
            update(knowledge_base_model)
            .where(knowledge_base_model.id == document_id)
            .values(status=status)
        )
        await db_session.commit()
        logger.info(f"Updated document status to {status}")

    async def _update_document_status_on_error(
        self,
        document_id: str,
        tenant_schema: str,
        knowledge_base_model
    ) -> None:
        """Update document status to FAILED in a new session to ensure it gets saved."""
        try:
            async with AsyncSessionLocal() as error_session:
                await self._set_search_path(error_session, tenant_schema)
                
                await error_session.execute(
                    update(knowledge_base_model)
                    .where(knowledge_base_model.id == document_id)
                    .values(status=KBStatus.FAILED)
                )
                await error_session.commit()
                logger.info("Updated document status to FAILED")
        except Exception as update_error:
            logger.error(f"Failed to update document status to FAILED: {str(update_error)}")

    def _get_knowledge_base_model_for_tenant(self, tenant_schema: str):
        """Get the appropriate knowledge base model for the tenant."""
        if tenant_schema != "public":
            return get_knowledge_base_model(tenant_schema)
        return KnowledgeBase

    async def _set_search_path(self, db_session: AsyncSession, tenant_schema: str) -> None:
        """Set the search path for the database session."""
        await db_session.execute(text(f'SET search_path TO "{tenant_schema}"'))

    @staticmethod
    async def extract_text_from_file(file_content: bytes, mime_type: str) -> str:
        """Extract text content from various file types."""
        try:
            if mime_type == "application/pdf":
                return await KnowledgeBaseService._extract_pdf_text(file_content)
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return await KnowledgeBaseService._extract_docx_text(file_content)
            elif mime_type.startswith("text/"):
                return file_content.decode("utf-8")
            else:
                return f"Unsupported file type: {mime_type}"
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            return f"Error extracting text: {str(e)}"

    @staticmethod
    async def _extract_pdf_text(file_content: bytes) -> str:
        """Extract text from PDF files."""
        import io
        import PyPDF2
        
        reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_out = "".join(page.extract_text() or "" for page in reader.pages)
        return text_out.strip()

    @staticmethod
    async def _extract_docx_text(file_content: bytes) -> str:
        """Extract text from DOCX files."""
        import io
        from docx import Document
        
        doc = Document(io.BytesIO(file_content))
        return "\n".join(p.text for p in doc.paragraphs)

    async def validate_background_task_setup(self, tenant_schema: str) -> bool:
        """Validate that the background task can connect to the database and access required services."""
        try:
            async with AsyncSessionLocal() as db_session:
                await self._set_search_path(db_session, tenant_schema)
                
                # Test a simple query to ensure connection works
                result = await db_session.execute(text("SELECT 1"))
                result.scalar()
                
                logger.info(f"Background task database connection validated for tenant {tenant_schema}")
                return True
        except Exception as e:
            logger.error(f"Background task setup validation failed for tenant {tenant_schema}: {str(e)}")
            return False



import hashlib
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.pgvector import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from api.models.category import Category
from api.models.user import user_categories, User
from api.models.knowledge_base import KnowledgeBase, KBStatus
from api.models.vector_doc import VectorDoc, get_vector_doc_model
from api.schemas.rag_schemas import VectorDocumentCreate
from api.db.database import AsyncSessionLocal
from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RAGService:
    """Service for handling RAG operations including document processing and retrieval."""
    
    def __init__(self, embedding_model: str = "google", api_key: Optional[str] = None):
        """
        Initialize RAG service with specified embedding model.
        
        Args:
            embedding_model: Either "openai" or "google"
            api_key: API key for the embedding model (if None, will load from environment)
        """
        self.embedding_model = embedding_model
        
        # Load API key from environment if not provided
        if api_key is None:
            import os
            if embedding_model == "google":
                self.api_key = os.getenv("GOOGLE_API_KEY")
            elif embedding_model == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            else:
                self.api_key = None
        else:
            self.api_key = api_key
            
        self._embeddings = None
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Log the configuration
        logger.info(f"RAG Service initialized with model: {embedding_model}")
        if self.api_key:
            logger.info(f"API key loaded: {self.api_key[:10]}...")
        else:
            logger.warning(f"No API key found for {embedding_model} model")
    
    @property
    def embeddings(self):
        """Lazy initialization of embeddings model."""
        if self._embeddings is None:
            if self.embedding_model == "openai":
                if not self.api_key:
                    raise ValueError("OpenAI API key is required")
                self._embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
            elif self.embedding_model == "google":
                if not self.api_key:
                    raise ValueError("Google API key is required")
                self._embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/embedding-001",
                    google_api_key=self.api_key
                )
            else:
                raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
        return self._embeddings
    
    def generate_chunk_hash(self, text: str) -> str:
        """Generate SHA-256 hash for text chunk to prevent duplicates."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _embedding_to_string(self, embedding: List[float]) -> str:
        """Convert embedding list to string representation for storage."""
        return json.dumps(embedding)
    
    def _string_to_embedding(self, embedding_str: str) -> List[float]:
        """Convert string representation back to embedding list."""
        try:
            return json.loads(embedding_str)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse embedding string: {embedding_str[:50]}...")
            return []
    
    async def process_document(
        self, 
        file_id: str, 
        file_content: str, 
        category_id: str,
        metadata: Dict[str, Any],
        db_session: AsyncSession,
        tenant_schema: str = "public"
    ) -> List[VectorDocumentCreate]:
        """
        Process document content into chunks and generate embeddings.
        
        Args:
            file_id: ID of the knowledge base entry
            file_content: Raw text content of the document
            metadata: Additional metadata for the document
            db_session: AsyncSession
            
        Returns:
            List of vector document creation objects
        """
        try:
            # Note: This method assumes the search_path is already set by the caller
            # Split text into chunks
            chunks = self._text_splitter.split_text(file_content)
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Generate embeddings for chunks
            embeddings = await self._generate_embeddings(chunks)
            
            # Create vector document objects
            vector_docs = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Check if this file's chunk already exists by (file_id, chunk_id)
                exists = await self._check_chunk_exists(file_id, i, db_session, tenant_schema)
                if exists:
                    logger.info(f"Chunk {i} already exists for file {file_id}, skipping")
                    continue
                
                vector_doc = VectorDocumentCreate(
                    category_id=category_id,
                    file_id=file_id,
                    chunk_id=i,
                    chunk_text=chunk,
                    embedding=embedding,
                    metadata={
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk),
                        "processed_at": datetime.utcnow().isoformat()
                    }
                )
                vector_docs.append(vector_doc)
            
            logger.info(f"Processed {len(vector_docs)} new chunks")
            return vector_docs
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            # Use async embedding generation if available
            if hasattr(self.embeddings, 'aembed_documents'):
                embeddings = await self.embeddings.aembed_documents(texts)
            else:
                embeddings = self.embeddings.embed_documents(texts)
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    async def _check_chunk_exists(self, file_id: str, chunk_id: int, db_session: AsyncSession, tenant_schema: str = "public") -> bool:
        """Check if a chunk for this file and index already exists."""
        try:
            # Note: This method assumes the search_path is already set by the caller
            # Create dynamic model for tenant schema
            if tenant_schema != "public":
                VectorDocModel = get_vector_doc_model(tenant_schema)
            else:
                VectorDocModel = VectorDoc
                
            result = await db_session.execute(
                select(VectorDocModel.id).where(and_(VectorDocModel.file_id == file_id, VectorDocModel.chunk_id == chunk_id))
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error checking chunk existence: {str(e)}")
            return False
    
    async def store_vector_documents(
        self, 
        vector_docs: List[VectorDocumentCreate], 
        user_id: str,
        category_id: str,
        db_session: AsyncSession,
        tenant_schema: str = "public"
    ) -> int:
        """
        Store vector documents in the database.
        
        Args:
            vector_docs: List of vector document creation objects
            user_id: ID of the user who uploaded the document
            category_id: ID of the document category
            db_session: AsyncSession
            
        Returns:
            Number of documents stored
        """
        try:
            # Note: This method assumes the search_path is already set by the caller
            # Ensure schema has expected columns/types
            await self._ensure_vector_doc_schema(db_session)
            
            # Create dynamic model for tenant schema
            if tenant_schema != "public":
                # Create VectorDocModel only - avoid creating other models that might already exist
                VectorDocModel = get_vector_doc_model(tenant_schema)
            else:
                VectorDocModel = VectorDoc
                
            stored_count = 0
            for vector_doc in vector_docs:
                # Create VectorDocument model instance
                db_vector_doc = VectorDocModel(
                    user_id=user_id,
                    category_id=category_id,
                    file_id=vector_doc.file_id,
                    chunk_id=vector_doc.chunk_id,
                    chunk_text=vector_doc.chunk_text,
                    embedding=vector_doc.embedding,
                    doc_metadata=vector_doc.metadata
                )
                
                db_session.add(db_vector_doc)
                stored_count += 1
            
            await db_session.commit()
            logger.info(f"Stored {stored_count} vector documents")
            return stored_count
            
        except Exception as e:
            await db_session.rollback()
            logger.error(f"Error storing vector documents: {str(e)}")
            raise

    async def _ensure_vector_doc_schema(self, db_session: AsyncSession) -> None:
        """Best-effort guard to align vector_doc schema at runtime.
        - Adds doc_metadata column if missing
        - Adjusts embedding dimension to 768 if different
        """
        try:
            # Add doc_metadata column if it does not exist
            await db_session.execute(
                text("ALTER TABLE vector_doc ADD COLUMN IF NOT EXISTS doc_metadata JSON")
            )
            # Attempt to set embedding to vector(768) if not already
            try:
                await db_session.execute(
                    text("ALTER TABLE vector_doc ALTER COLUMN embedding TYPE vector(768)")
                )
            except Exception:
                # Ignore if type is already compatible or cannot be altered
                pass
            await db_session.commit()
        except Exception:
            # Non-fatal; proceed with inserts and let DB surface concrete errors if any
            await db_session.rollback()
            return
    
    async def search_similar_documents(
        self,
        query: str,
        user_roles: List[str],
        category_ids: List[str],
        db_session: AsyncSession,
        top_k: int = 5,
        tenant_schema: str = "public"
    ) -> List[Tuple[VectorDoc, float]]:
        """
        Search for similar documents based on query and user access.
        
        Args:
            query: Search query
            user_roles: List of user roles
            category_ids: List of accessible category IDs
            top_k: Number of top results to return
            db_session: AsyncSession
            
        Returns:
            List of tuples containing (VectorDoc, similarity_score)
        """
        try:
            # Note: This method assumes the search_path is already set by the caller
            # Generate embedding for the query
            query_embedding = await self._generate_embeddings([query])
            query_vector = query_embedding[0]
            # Normalize to plain Python list to avoid numpy truthiness issues
            if hasattr(query_vector, "tolist"):
                query_vector = query_vector.tolist()
            
            # Create dynamic model for tenant schema
            if tenant_schema != "public":
                VectorDocModel = get_vector_doc_model(tenant_schema)
            else:
                VectorDocModel = VectorDoc
                
            # Build the search query with role-based access control
            search_query = select(VectorDocModel).where(
                and_(
                    VectorDocModel.category_id.in_(category_ids),
                    # Add vector similarity search here when pgvector is properly configured
                )
            ).limit(top_k)
            
            # For now, return basic search results
            # TODO: Implement proper vector similarity search with pgvector
            result = await db_session.execute(search_query)
            documents = result.scalars().all()
            
            # Calculate basic similarity scores (placeholder)
            results = []
            for doc in documents:
                # Normalize stored embedding to list
                doc_embedding = doc.embedding
                if hasattr(doc_embedding, "tolist"):
                    doc_embedding = doc_embedding.tolist()
                # Skip if shape mismatches
                if doc_embedding is None:
                    continue
                if len(doc_embedding) != len(query_vector):
                    continue
                similarity = self._calculate_cosine_similarity(query_vector, doc_embedding)
                results.append((doc, similarity))
            
            # Sort by similarity score
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm_a = sum(a * a for a in vec1) ** 0.5
            norm_b = sum(b * b for b in vec2) ** 0.5
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            return dot_product / (norm_a * norm_b)
        except Exception:
            return 0.0
    
    async def get_accessible_categories(
        self,
        user_id: str,
        tenant_schema: str,
        db_session: AsyncSession,
    ) -> List[str]:
        """
        Get list of category IDs that the user can access.
        
        Args:
            user_roles: List of user roles
            organization_id: ID of the user's organization
            db_session: AsyncSession
            
        Returns:
            List of accessible category IDs
        """
        try:
            # Set the search path to the tenant's schema
            await db_session.execute(text(f'SET search_path TO "{tenant_schema}"'))
            
            # Check if user is owner; if yes, they get access to all categories
            owner_result = await db_session.execute(
                select(User.is_owner).where(User.id == user_id)
            )
            is_owner = owner_result.scalar_one_or_none() is True
            if is_owner:
                all_q = select(Category.id)
                all_res = await db_session.execute(all_q)
                all_ids = [row[0] for row in all_res.all()]
                logger.info(
                    f"User {user_id} is owner in {tenant_schema}; granting access to all categories: {len(all_ids)}"
                )
                return all_ids

            # Non-owners: Categories accessible if linked via association table
            query = (
                select(Category.id)
                .select_from(Category)
                .join(user_categories, Category.id == user_categories.c.category_id)
                .where(user_categories.c.user_id == user_id)
            )

            result = await db_session.execute(query)
            category_ids = [row[0] for row in result.all()]
            logger.info(f"Accessible category IDs for user {user_id}: {category_ids}")
            return category_ids
            
        except Exception as e:
            logger.error(f"Error getting accessible categories: {str(e)}")
            return []

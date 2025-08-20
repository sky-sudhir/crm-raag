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

from api.models.rag_models import DocumentCategory, KnowledgeBase, VectorDocument, DocumentStatus
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
        db_session: AsyncSession
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
                chunk_hash = self.generate_chunk_hash(chunk)
                
                # Check if chunk already exists
                existing_chunk = await self._check_chunk_exists(chunk_hash, db_session)
                if existing_chunk:
                    logger.info(f"Chunk {i} already exists, skipping")
                    continue
                
                vector_doc = VectorDocumentCreate(
                    category_id=category_id,
                    file_id=file_id,
                    chunk_id=i,
                    chunk_hash=chunk_hash,
                    chunk_text=chunk,
                    embedding=embedding,
                    doc_metadata={
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
    
    async def _check_chunk_exists(self, chunk_hash: str, db_session: AsyncSession) -> bool:
        """Check if a chunk with the given hash already exists."""
        try:
            # Note: This method assumes the search_path is already set by the caller
            result = await db_session.execute(
                select(VectorDocument.id).where(VectorDocument.chunk_hash == chunk_hash)
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
        db_session: AsyncSession
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
            stored_count = 0
            for vector_doc in vector_docs:
                # Create VectorDocument model instance
                db_vector_doc = VectorDocument(
                    user_id=user_id,
                    category_id=category_id,
                    file_id=vector_doc.file_id,
                    chunk_id=vector_doc.chunk_id,
                    chunk_text=vector_doc.chunk_text,
                    chunk_hash=vector_doc.chunk_hash,
                    embedding=self._embedding_to_string(vector_doc.embedding),
                    doc_metadata=vector_doc.doc_metadata
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
    
    async def search_similar_documents(
        self,
        query: str,
        user_roles: List[str],
        category_ids: List[str],
        db_session: AsyncSession,
        top_k: int = 5
    ) -> List[Tuple[VectorDocument, float]]:
        """
        Search for similar documents based on query and user access.
        
        Args:
            query: Search query
            user_roles: List of user roles
            category_ids: List of accessible category IDs
            top_k: Number of top results to return
            db_session: AsyncSession
            
        Returns:
            List of tuples containing (VectorDocument, similarity_score)
        """
        try:
            # Note: This method assumes the search_path is already set by the caller
            # Generate embedding for the query
            query_embedding = await self._generate_embeddings([query])
            query_vector = query_embedding[0]
            
            # Build the search query with role-based access control
            search_query = select(VectorDocument).where(
                and_(
                    VectorDocument.category_id.in_(category_ids),
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
                # Convert string embedding back to list
                doc_embedding = self._string_to_embedding(doc.embedding)
                if doc_embedding:
                    # Simple cosine similarity calculation
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
        user_roles: List[str], 
        tenant_schema: str,
        db_session: AsyncSession
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
            
            # Get all categories in the current tenant schema
            query = select(DocumentCategory)
            
            logger.info(f"Executing query: {query}")
            logger.info(f"Current search_path: {tenant_schema}")
            
            result = await db_session.execute(query)
            categories = result.scalars().all()
            
            logger.info(f"Raw result: {result}")
            logger.info(f"Categories found: {categories}")
            
            # Filter categories based on user roles
            accessible_categories = []
            logger.info(f"Found {len(categories)} categories for tenant {tenant_schema}")
            logger.info(f"User roles: {user_roles}")
            
            for category in categories:
                logger.info(f"Checking category: {category.name}, allowed_roles: {category.allowed_roles}, is_general: {category.is_general}")
                # General categories are accessible by all users
                if category.is_general:
                    accessible_categories.append(category.id)
                    logger.info(f"Category {category.name} is general - accessible")
                # Check if user has any of the allowed roles
                elif any(role in category.allowed_roles for role in user_roles):
                    accessible_categories.append(category.id)
                    logger.info(f"Category {category.name} accessible by role match")
                else:
                    logger.info(f"Category {category.name} not accessible")
            
            logger.info(f"Total accessible categories: {len(accessible_categories)}")
            return accessible_categories
            
        except Exception as e:
            logger.error(f"Error getting accessible categories: {str(e)}")
            return []

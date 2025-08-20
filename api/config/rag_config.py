import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class RAGSettings(BaseSettings):
    """Configuration settings for the RAG system."""
    
    # Embedding model configuration
    EMBEDDING_MODEL: str = "google"  # "openai" or "google"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Vector database configuration
    VECTOR_DIMENSION: int = 786  # Default embedding dimension
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score for retrieval
    
    # Document processing configuration
    CHUNK_SIZE: int = 1000  # Text chunk size in characters
    CHUNK_OVERLAP: int = 200  # Overlap between chunks
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB max file size
    
    # S3 configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: Optional[str] = None
    
    # Processing configuration
    MAX_CONCURRENT_PROCESSING: int = 5  # Max concurrent document processing
    PROCESSING_TIMEOUT: int = 300  # Processing timeout in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
rag_settings = RAGSettings()


def get_embedding_api_key() -> Optional[str]:
    """Get the appropriate API key based on the configured embedding model."""
    if rag_settings.EMBEDDING_MODEL == "openai":
        return rag_settings.OPENAI_API_KEY
    elif rag_settings.EMBEDDING_MODEL == "google":
        return rag_settings.GOOGLE_API_KEY
    else:
        return None


def get_s3_config() -> dict:
    """Get S3 configuration dictionary."""
    return {
        "aws_access_key_id": rag_settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": rag_settings.AWS_SECRET_ACCESS_KEY,
        "aws_region": rag_settings.AWS_REGION,
        "bucket": rag_settings.S3_BUCKET
    }


def validate_config() -> bool:
    """Validate that all required configuration is present."""
    errors = []
    
    # Check embedding model configuration
    if rag_settings.EMBEDDING_MODEL == "openai" and not rag_settings.OPENAI_API_KEY:
        errors.append("OpenAI API key is required when using OpenAI embedding model")
    elif rag_settings.EMBEDDING_MODEL == "google" and not rag_settings.GOOGLE_API_KEY:
        errors.append("Google API key is required when using Google embedding model")
    
    # Check S3 configuration if S3 bucket is specified
    if rag_settings.S3_BUCKET and (not rag_settings.AWS_ACCESS_KEY_ID or not rag_settings.AWS_SECRET_ACCESS_KEY):
        errors.append("AWS credentials are required when S3 bucket is specified")
    
    if errors:
        for error in errors:
            print(f"Configuration Error: {error}")
        return False
    
    return True

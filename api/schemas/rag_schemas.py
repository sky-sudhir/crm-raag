from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from api.models.knowledge_base import KBStatus


class DocumentCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    allowed_roles: List[str] = Field(default_factory=list)
    is_general: bool = False


class DocumentCategoryCreate(DocumentCategoryBase):
    pass


class DocumentCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    is_general: Optional[bool] = None


class DocumentCategoryResponse(DocumentCategoryBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeBaseBase(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    category_id: str
    mime: str = Field(..., min_length=1, max_length=100)
    file_size: int = Field(..., gt=0)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(BaseModel):
    status: Optional[KBStatus] = None
    json: Optional[str] = None
    s3_url: Optional[str] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: str
    user_id: str
    status: KBStatus
    json: Optional[str] = None
    s3_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VectorDocumentBase(BaseModel):
    category_id: str
    file_id: str
    chunk_id: int = Field(..., ge=0)
    chunk_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorDocumentCreate(VectorDocumentBase):
    embedding: List[float]  # Input embeddings as list


class VectorDocumentResponse(VectorDocumentBase):
    id: str
    user_id: str
    embedding: List[float]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    category_id: str
    file_name: str
    mime: str
    file_size: int


class DocumentUploadResponse(BaseModel):
    id: str
    status: KBStatus
    message: str


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    include_metadata: bool = True


class RAGQueryResponse(BaseModel):
    query: str
    results: List[VectorDocumentResponse]
    total_results: int
    processing_time_ms: float


class DocumentProcessingStatus(BaseModel):
    id: str
    status: KBStatus
    progress: Optional[float] = None  # 0.0 to 1.0
    message: Optional[str] = None
    error: Optional[str] = None


class RAGChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    model: str = Field(default="openai", description="LLM model to use: 'openai' or 'google'")

class RAGChatResponse(BaseModel):
    query: str
    response: str
    sources: List[str]
    total_sources: int
    processing_time_ms: float

# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QueryRequest(BaseModel):
    """Request model for RAG query"""
    query: str = Field(..., min_length=1, description="User query")

class QueryResponse(BaseModel):
    """Response model for RAG query"""
    answer: str
    source_chunks: Optional[List[str]] = None
    chunk_ids: Optional[List[str]] = None
    response_time_ms: Optional[int] = None

class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    message: str
    filename: Optional[str] = None
    chunks_created: Optional[int] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    documents_indexed: int

class StatsResponse(BaseModel):
    """Statistics response"""
    total_documents: int
    total_queries: int
    cache_stats: dict
    
class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str

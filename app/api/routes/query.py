# app/api/routes/query.py
from fastapi import APIRouter, HTTPException, Cookie
from typing import Optional
import time
from app.models.schemas import QueryRequest, QueryResponse
from app.services.vector_service import vector_service
from app.services.llm_service import llm_service
from app.services.cache_service import cache_service
from app.models.database import audit_db
from app.core.logger import logger

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest, rag_session: Optional[str] = Cookie(None)):
    """
    Query the RAG system with a question.
    Returns an answer based on indexed documents with source tracking.
    Session-aware: Users see their own documents + admin documents.
    """
    start_time = time.time()
    
    try:
        # Check cache first (session-aware)
        cached_response = cache_service.get(request.query, session_id=rag_session)
        if cached_response:
            logger.info("Returning cached response")
            return cached_response
        
        # Search for relevant chunks with session filtering
        search_results = vector_service.search(request.query, session_id=rag_session)
        chunks = search_results["documents"]
        chunk_ids = search_results["ids"]
        
        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found. Please upload documents first."
            )
        
        # Generate answer using LLM
        answer = llm_service.generate_answer(request.query, chunks)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Create response
        response = QueryResponse(
            answer=answer,
            source_chunks=chunks,
            chunk_ids=chunk_ids,
            response_time_ms=response_time_ms
        )
        
        # Cache the response (session-aware)
        cache_service.set(request.query, response, session_id=rag_session)
        
        # Log to audit database
        audit_db.log_query(
            query=request.query,
            answer=answer,
            source_chunks=chunks,
            chunk_ids=chunk_ids,
            response_time_ms=response_time_ms
        )
        
        logger.info(f"Query processed in {response_time_ms}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

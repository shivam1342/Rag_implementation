# app/api/routes/admin.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import StatsResponse, HealthResponse
from app.services.vector_service import vector_service
from app.services.cache_service import cache_service
from app.models.database import audit_db
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        doc_count = vector_service.get_collection_count()
        return HealthResponse(
            status="healthy",
            version=settings.VERSION,
            documents_indexed=doc_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    try:
        return StatsResponse(
            total_documents=vector_service.get_collection_count(),
            total_queries=audit_db.get_total_queries(),
            cache_stats=cache_service.get_stats()
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_recent_logs(limit: int = 10):
    """Get recent query logs"""
    try:
        logs = audit_db.get_recent_logs(limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
async def clear_cache():
    """Clear the query cache"""
    try:
        cache_service.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

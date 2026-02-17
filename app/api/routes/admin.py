# app/api/routes/admin.py
from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import Optional
from pydantic import BaseModel
import uuid
from app.models.schemas import StatsResponse, HealthResponse
from app.services.vector_service import vector_service
from app.services.cache_service import cache_service
from app.models.database import audit_db
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()

# Request models
class AdminLoginRequest(BaseModel):
    password: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

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

@router.post("/admin/cleanup-old-sessions")
async def cleanup_old_sessions(
    rag_admin_session: Optional[str] = Cookie(None)
):
    """Admin only - Clean up expired user session documents"""
    try:
        if rag_admin_session != "authenticated":
            raise HTTPException(status_code=403, detail="Admin authentication required")
        
        deleted_count = vector_service.cleanup_old_sessions(settings.SESSION_EXPIRY)
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} expired user documents",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/login")
async def admin_login(request: AdminLoginRequest, response: Response):
    """Admin login endpoint - sets admin session cookie"""
    try:
        if request.password == settings.ADMIN_PASSWORD:
            # Set admin cookie
            response.set_cookie(
                key=settings.ADMIN_SESSION_KEY,
                value="authenticated",
                max_age=settings.SESSION_EXPIRY,
                httponly=True,
                samesite="lax"
            )
            logger.info("Admin logged in successfully")
            return {"success": True, "message": "Admin login successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid password")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during admin login: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/logout")
async def admin_logout(response: Response):
    """Admin logout - clear admin session cookie"""
    response.delete_cookie(key=settings.ADMIN_SESSION_KEY)
    return {"success": True, "message": "Admin logged out"}

@router.post("/session/create")
async def create_session(response: Response) -> SessionResponse:
    """Create a new user session - returns session ID and sets cookie"""
    try:
        session_id = str(uuid.uuid4())
        
        # Set session cookie
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            max_age=settings.SESSION_EXPIRY,
            httponly=True,
            samesite="lax"
        )
        
        logger.info(f"Created new session: {session_id}")
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/session/cleanup")
async def cleanup_session(
    response: Response,
    rag_session: Optional[str] = Cookie(None)
):
    """Delete all documents for current session"""
    try:
        if not rag_session:
            raise HTTPException(status_code=400, detail="No active session")
        
        # Delete session documents
        deleted_count = vector_service.delete_session_documents(rag_session)
        
        # Clear session cookie
        response.delete_cookie(key=settings.SESSION_COOKIE_NAME)
        
        logger.info(f"Cleaned up session {rag_session}: {deleted_count} documents deleted")
        return {
            "success": True,
            "message": f"Session cleaned up, {deleted_count} documents deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/status")
async def session_status(
    rag_session: Optional[str] = Cookie(None),
    rag_admin_session: Optional[str] = Cookie(None)
):
    """Check session status"""
    is_admin = (rag_admin_session == "authenticated")
    has_session = bool(rag_session)
    
    return {
        "is_admin": is_admin,
        "has_session": has_session,
        "session_id": rag_session if has_session else None
    }


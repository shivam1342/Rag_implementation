# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import query, upload, admin
from app.core.config import settings
from app.core.logger import logger
import os

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-ready RAG system with caching and audit logging"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(query.router, prefix=settings.API_PREFIX, tags=["Query"])
app.include_router(upload.router, prefix=settings.API_PREFIX, tags=["Upload"])
app.include_router(admin.router, prefix=settings.API_PREFIX, tags=["Admin"])

@app.get("/")
async def root():
    """Serve the frontend or return API info"""
    # Try to serve index.html if it exists
    if os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    
    # Otherwise return API info
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "query": f"{settings.API_PREFIX}/query",
            "upload": f"{settings.API_PREFIX}/upload",
            "health": f"{settings.API_PREFIX}/health",
            "stats": f"{settings.API_PREFIX}/stats"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Docs available at /docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"Shutting down {settings.APP_NAME}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

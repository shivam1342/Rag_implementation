# app/api/routes/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Cookie
from typing import Optional
from app.models.schemas import UploadResponse
from app.services.document_service import document_service
from app.services.vector_service import vector_service
from app.utils.validators import validate_file, sanitize_filename
from app.utils.chunking import chunk_text
from app.core.logger import logger
import os
import time

router = APIRouter()

def process_uploaded_file(file_path: str, filename: str, session_id: str = None, is_admin: bool = False):
    """Background task to process uploaded file"""
    try:
        logger.info(f"Processing file: {filename}")
        
        # Extract text
        text = document_service.extract_text(file_path)
        
        # Chunk text
        chunks = chunk_text(text)
        
        # Add metadata with session info and timestamp
        upload_time = int(time.time())
        metadatas = [
            {
                "source_file": filename,
                "chunk_index": i,
                "session_id": session_id or "unknown",
                "is_admin": is_admin,
                "upload_timestamp": upload_time
            }
            for i in range(len(chunks))
        ]
        
        # Add to vector DB
        vector_service.add_documents(chunks, metadatas)
        
        logger.info(f"Successfully processed {filename}: {len(chunks)} chunks created")
    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rag_session: Optional[str] = Cookie(None),
    rag_admin_session: Optional[str] = Cookie(None)
):
    """
    Upload a document file (TXT, PDF, DOCX).
    File is processed in background and indexed for RAG.
    """
    try:
        # Determine if this is admin upload
        from app.core.config import settings
        is_admin = (rag_admin_session == "authenticated")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file
        is_valid, error_msg = validate_file(file.filename, file_size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        
        # Save file
        file_path = document_service.save_upload(safe_filename, content)
        
        # Process file in background with session info
        background_tasks.add_task(
            process_uploaded_file,
            file_path,
            safe_filename,
            session_id=rag_session,
            is_admin=is_admin
        )
        
        upload_type = "admin (persistent)" if is_admin else "user (temporary)"
        logger.info(f"File uploaded as {upload_type}: {safe_filename}, queued for processing")
        
        return UploadResponse(
            success=True,
            message=f"File uploaded successfully as {upload_type} and queued for processing",
            filename=safe_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/files")
async def list_files():
    """List all uploaded files"""
    try:
        files = document_service.list_uploaded_files()
        return {"files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

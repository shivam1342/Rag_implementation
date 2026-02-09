# app/services/document_service.py
import os
from typing import List
from app.core.config import settings
from app.core.logger import logger

class DocumentService:
    """Service for document processing and text extraction"""
    
    def __init__(self):
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        logger.info("Document service initialized")
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from uploaded file.
        Currently supports: TXT
        TODO: Add PDF and DOCX support
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == ".txt":
                return self._extract_from_txt(file_path)
            elif file_ext == ".pdf":
                # TODO: Implement PDF extraction with pypdf
                raise NotImplementedError("PDF support coming soon")
            elif file_ext == ".docx":
                # TODO: Implement DOCX extraction with python-docx
                raise NotImplementedError("DOCX support coming soon")
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        logger.info(f"Extracted {len(text)} characters from TXT file")
        return text
    
    def save_upload(self, filename: str, content: bytes) -> str:
        """
        Save uploaded file to disk.
        
        Args:
            filename: Name of the file
            content: File content as bytes
            
        Returns:
            Path to saved file
        """
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Saved file: {file_path}")
        return file_path
    
    def list_uploaded_files(self) -> List[str]:
        """List all uploaded files"""
        try:
            files = os.listdir(settings.UPLOAD_DIR)
            return [f for f in files if os.path.isfile(os.path.join(settings.UPLOAD_DIR, f))]
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []

# Global instance
document_service = DocumentService()

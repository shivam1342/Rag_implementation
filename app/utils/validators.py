# app/utils/validators.py
import os
from typing import Tuple
from app.core.config import settings
from app.core.logger import logger

def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Validate uploaded file.
    
    Args:
        filename: Name of the file
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File too large. Maximum size: {max_mb}MB"
    
    # Check file extension
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    
    # Check filename
    if not filename or filename == "":
        return False, "Invalid filename"
    
    logger.info(f"File validation passed: {filename} ({file_size} bytes)")
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove directory paths
    filename = os.path.basename(filename)
    
    # Remove potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', '\0']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    return filename

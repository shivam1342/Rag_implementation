# app/utils/chunking.py
from typing import List
from app.core.config import settings

def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split text into chunks with optional overlap.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk (defaults to settings.CHUNK_SIZE)
        overlap: Overlap between chunks (defaults to settings.CHUNK_OVERLAP)
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if overlap is None:
        overlap = settings.CHUNK_OVERLAP
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        
        # Move start position considering overlap
        start = end - overlap if end < text_length else text_length
    
    return chunks


def semantic_chunk_text(text: str, max_chunk_size: int = None) -> List[str]:
    """
    Split text into semantic chunks (by paragraphs/sentences).
    More intelligent than fixed-size chunking.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum size of each chunk
        
    Returns:
        List of text chunks
    """
    if max_chunk_size is None:
        max_chunk_size = settings.CHUNK_SIZE
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # If adding this paragraph exceeds max size, save current chunk
        if len(current_chunk) + len(para) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

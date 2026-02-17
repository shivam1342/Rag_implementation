# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Settings
    APP_NAME: str = "RAG System"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".txt", ".pdf", ".docx"]
    UPLOAD_DIR: str = "uploads"
    
    # Vector DB Settings
    CHROMA_DIR: str = "chroma_store"
    CHROMA_COLLECTION: str = "docs"
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Retrieval Settings
    TOP_K: int = 3
    
    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    
    # Cache Settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 hour in seconds
    
    # Chunking Settings
    CHUNK_SIZE: int = 300
    CHUNK_OVERLAP: int = 50
    
    # Audit Log Settings
    AUDIT_DB: str = "audit.db"
    
    # Session & Multi-User Settings
    SESSION_COOKIE_NAME: str = "rag_session"
    SESSION_EXPIRY: int = 3600 * 24  # 24 hours in seconds
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")  # Change in production!
    ADMIN_SESSION_KEY: str = "rag_admin_session"
    
    # Logging
    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"

settings = Settings()

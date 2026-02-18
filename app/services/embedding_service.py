# app/services/embedding_service.py
from sentence_transformers import SentenceTransformer
from typing import List, Optional
from app.core.config import settings
from app.core.logger import logger

class EmbeddingService:
    """Service for generating embeddings from text"""
    
    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        logger.info("Embedding service initialized (model will load on first use)")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model on first use"""
        if self._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        return self._model
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.model.encode(texts).tolist()
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def encode_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text string
            
        Returns:
            Embedding vector
        """
        return self.encode([text])[0]

# Global instance
embedding_service = EmbeddingService()

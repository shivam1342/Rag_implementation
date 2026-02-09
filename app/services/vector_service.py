# app/services/vector_service.py
import chromadb
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logger import logger
from app.services.embedding_service import embedding_service

class VectorService:
    """Service for vector database operations using ChromaDB"""
    
    def __init__(self):
        logger.info(f"Initializing ChromaDB at: {settings.CHROMA_DIR}")
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB initialized successfully")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict] = None) -> None:
        """
        Add documents to the vector database.
        
        Args:
            texts: List of text chunks
            metadatas: Optional list of metadata dicts
        """
        try:
            # Generate embeddings
            embeddings = embedding_service.encode(texts)
            
            # Generate IDs
            current_count = self.collection.count()
            ids = [f"chunk_{current_count + i}" for i in range(len(texts))]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                ids=ids,
                metadatas=metadatas if metadatas else None
            )
            
            logger.info(f"Added {len(texts)} documents to vector DB")
        except Exception as e:
            logger.error(f"Error adding documents to vector DB: {e}")
            raise
    
    def search(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Search for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            Dict with documents, distances, and metadatas
        """
        if top_k is None:
            top_k = settings.TOP_K
        
        try:
            # Generate query embedding
            query_embedding = embedding_service.encode_single(query)
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            logger.info(f"Found {len(results['documents'][0])} results for query")
            
            return {
                "documents": results["documents"][0],
                "distances": results.get("distances", [[]])[0],
                "metadatas": results.get("metadatas", [[]])[0],
                "ids": results.get("ids", [[]])[0]
            }
        except Exception as e:
            logger.error(f"Error searching vector DB: {e}")
            raise
    
    def get_collection_count(self) -> int:
        """Get the number of documents in the collection"""
        return self.collection.count()
    
    def delete_all(self) -> None:
        """Delete all documents from the collection"""
        try:
            self.client.delete_collection(name=settings.CHROMA_COLLECTION)
            self.collection = self.client.create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Deleted all documents from vector DB")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

# Global instance
vector_service = VectorService()

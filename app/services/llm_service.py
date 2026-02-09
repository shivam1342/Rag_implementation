# app/services/llm_service.py
from groq import Groq
from typing import List
from app.core.config import settings
from app.core.logger import logger

class LLMService:
    """Service for LLM interactions using Groq API"""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("LLM service initialized")
    
    def generate_answer(self, query: str, context_chunks: List[str]) -> str:
        """
        Generate answer using LLM based on context chunks.
        
        Args:
            query: User query
            context_chunks: List of relevant context chunks
            
        Returns:
            Generated answer
        """
        try:
            # Combine context
            context_text = "\n\n".join(context_chunks)
            
            # Create prompt
            prompt = f"""You are a precise assistant. 
Use ONLY the context below to answer.

Context:
{context_text}

Question: {query}

Answer clearly:"""
            
            logger.debug(f"Generating answer for query: {query}")
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            
            answer = response.choices[0].message.content
            logger.info("Answer generated successfully")
            
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise

# Global instance
llm_service = LLMService()

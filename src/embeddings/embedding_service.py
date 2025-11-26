"""
Embedding service using Google's embedding model
"""
import google.generativeai as genai
from config import Config
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using Google's embedding model"""
    
    def __init__(self):
        Config.validate()
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model_name = Config.EMBEDDING_MODEL
        logger.info(f"Embedding service initialized with model: {self.model_name}")
    
    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> list:
        """
        Generate embedding for a text chunk using Google's embedding-001 model
        
        Args:
            text: The text to embed
            task_type: Task type for embedding ("retrieval_document" or "retrieval_query")
            
        Returns:
            List of embedding values
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Use Google's embed_content method
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type
            )
            
            embedding = result['embedding']
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: list) -> list:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings


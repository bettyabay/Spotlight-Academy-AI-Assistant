"""
Configuration management for Spotlight Academy AI Assistant
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Google Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Application
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # RAG Configuration
    CHUNK_SIZE = 500  # tokens
    CHUNK_OVERLAP = 50  # tokens
    MAX_CHUNKS_PER_QUERY = 8
    EMBEDDING_MODEL = "models/embedding-001"  # Google embedding model
    EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "google")  # google | local
    LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    LOCAL_EMBEDDING_DIM = int(os.getenv("LOCAL_EMBEDDING_DIM", "384"))
    
    # Content Processing
    SUPPORTED_FORMATS = [".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg"]
    MAX_FILE_SIZE_MB = 50
    
    # Vector DB Configuration
    VECTOR_DIMENSION = 768  # Google embedding-001 dimension (verify with actual model)
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required = [
            "SUPABASE_URL",
            "SUPABASE_KEY",
        ]
        # Only require Google key if using Google embeddings
        if cls.EMBEDDING_PROVIDER.lower() == "google":
            required.append("GOOGLE_API_KEY")
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        return True


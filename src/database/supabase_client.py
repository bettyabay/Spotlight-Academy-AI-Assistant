"""
Supabase client setup and vector database operations
"""
from supabase import create_client, Client
from config import Config
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Manages Supabase connection and vector operations"""
    
    def __init__(self):
        Config.validate()
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the vector table exists with proper schema"""
        # Note: Supabase uses pgvector extension
        # This is a placeholder - actual table creation should be done via SQL migration
        # Table schema:
        # CREATE TABLE course_content (
        #   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        #   content TEXT NOT NULL,
        #   embedding vector(768),
        #   metadata JSONB,
        #   module TEXT,
        #   chapter TEXT,
        #   lesson TEXT,
        #   concept TEXT,
        #   source_file TEXT,
        #   version INTEGER DEFAULT 1,
        #   created_at TIMESTAMP DEFAULT NOW(),
        #   updated_at TIMESTAMP DEFAULT NOW()
        # );
        logger.info("Supabase client initialized")
    
    def insert_embedding(self, content: str, embedding: list, metadata: dict):
        """
        Insert a chunk with its embedding into the vector database
        
        Args:
            content: The text content of the chunk
            embedding: The embedding vector
            metadata: Dictionary containing module, chapter, lesson, concept, source_file, etc.
        """
        try:
            data = {
                "content": content,
                "embedding": embedding,
                "metadata": metadata,
                "module": metadata.get("module", ""),
                "chapter": metadata.get("chapter", ""),
                "lesson": metadata.get("lesson", ""),
                "concept": metadata.get("concept", ""),
                "source_file": metadata.get("source_file", ""),
                "version": metadata.get("version", 1)
            }
            
            result = self.client.table("course_content").insert(data).execute()
            logger.info(f"Inserted embedding for content chunk: {metadata.get('source_file', 'unknown')}")
            return result
        except Exception as e:
            logger.error(f"Error inserting embedding: {str(e)}")
            raise
    
    def search_similar(self, query_embedding: list, top_k: int = 8, filters: dict = None, match_threshold: float = 0.7):
        """
        Search for similar content using vector similarity
        
        Args:
            query_embedding: The query embedding vector
            top_k: Number of results to return
            filters: Optional filters (module, chapter, lesson)
            match_threshold: Minimum similarity threshold (0-1)
        
        Returns:
            List of similar content chunks with similarity scores
        """
        try:
            # Use the RPC function for vector similarity search
            # This calls the match_course_content function defined in the migration
            rpc_params = {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": top_k
            }
            
            # Add optional filters
            if filters:
                if "module" in filters:
                    rpc_params["filter_module"] = filters["module"]
                if "chapter" in filters:
                    rpc_params["filter_chapter"] = filters["chapter"]
                if "lesson" in filters:
                    rpc_params["filter_lesson"] = filters["lesson"]
            
            result = self.client.rpc("match_course_content", rpc_params).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error searching similar content: {str(e)}")
            raise
    
    def delete_by_source(self, source_file: str):
        """Delete all chunks from a specific source file (for re-indexing)"""
        try:
            result = self.client.table("course_content").delete().eq("source_file", source_file).execute()
            logger.info(f"Deleted chunks for source file: {source_file}")
            return result
        except Exception as e:
            logger.error(f"Error deleting by source: {str(e)}")
            raise
    
    def get_ingestion_status(self, source_file: str = None):
        """Get ingestion status for files"""
        try:
            query = self.client.table("course_content").select("source_file, created_at, version")
            if source_file:
                query = query.eq("source_file", source_file)
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting ingestion status: {str(e)}")
            raise


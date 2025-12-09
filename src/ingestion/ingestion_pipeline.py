"""
Main ingestion pipeline that orchestrates document processing, chunking, and embedding storage
"""
import os
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime

from ..database.supabase_client import SupabaseClient
from ..embeddings.embedding_service import EmbeddingService
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Main pipeline for ingesting course materials"""
    
    def __init__(self):
        self.db_client = SupabaseClient()
        self.embedding_service = EmbeddingService()
        self.doc_processor = DocumentProcessor()
        logger.info("Ingestion pipeline initialized")
    
    def ingest_file(
        self,
        file_path: str,
        module: str = None,
        chapter: str = None,
        lesson: str = None,
        concept: str = None,
        version: int = 1
    ) -> Dict:
        """
        Ingest a single file into the vector database
        
        Args:
            file_path: Path to the file to ingest
            module: Module name (optional)
            chapter: Chapter name (optional)
            lesson: Lesson name (optional)
            concept: Concept name (optional)
            version: Version number (default: 1)
            
        Returns:
            Dictionary with ingestion results
        """
        file_path = Path(file_path)
        start_time = datetime.now()
        
        try:
            # Prepare metadata
            metadata = {
                "module": module or "",
                "chapter": chapter or "",
                "lesson": lesson or "",
                "concept": concept or "",
                "version": version,
                "ingested_at": datetime.now().isoformat()
            }
            
            # Delete existing chunks for this file (if re-indexing)
            if version > 1:
                self.db_client.delete_by_source(file_path.name)
            
            # Process document and create chunks
            logger.info(f"Processing file: {file_path.name}")
            chunks = self.doc_processor.process_file(str(file_path), metadata)
            
            if not chunks:
                logger.warning(f"No chunks created from {file_path.name}")
                return {
                    "success": False,
                    "message": "No content extracted from file",
                    "chunks_created": 0
                }
            
            # Generate embeddings and store
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            chunks_stored = 0
            errors = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.embedding_service.generate_embedding(chunk['content'])
                    
                    # Store in database
                    self.db_client.insert_embedding(
                        content=chunk['content'],
                        embedding=embedding,
                        metadata={**chunk['metadata'], **metadata}
                    )
                    chunks_stored += 1
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Processed {i + 1}/{len(chunks)} chunks...")
                        
                except Exception as e:
                    error_msg = f"Error processing chunk {i + 1}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = {
                "success": True,
                "file_name": file_path.name,
                "chunks_created": chunks_stored,
                "total_chunks": len(chunks),
                "errors": errors,
                "duration_seconds": duration,
                "metadata": metadata
            }
            
            logger.info(
                f"Ingestion complete: {file_path.name} - "
                f"{chunks_stored}/{len(chunks)} chunks stored in {duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {str(e)}")
            return {
                "success": False,
                "file_name": file_path.name,
                "error": str(e),
                "chunks_created": 0
            }
    
    def ingest_directory(
        self,
        directory_path: str,
        module: str = None,
        chapter: str = None,
        lesson: str = None,
        concept: str = None,
        version: int = 1,
    ) -> List[Dict]:
        """
        Ingest all supported files from a directory
        
        Args:
            directory_path: Path to directory containing files
            module: Module name (optional)
            chapter: Chapter name (optional)
            lesson: Lesson name (optional)
            concept: Concept name (optional)
            version: Version number (default: 1)
            
        Returns:
            List of ingestion results
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        results = []
        supported_files = []
        
        # Find all supported files
        for ext in self.doc_processor.supported_formats:
            supported_files.extend(directory.rglob(f"*{ext}"))
        
        # Sort for consistent processing order
        supported_files = sorted(supported_files)
        
        logger.info(f"Found {len(supported_files)} files to ingest in {directory_path}")
        
        for file_path in supported_files:
            result = self.ingest_file(
                str(file_path),
                module=module,
                chapter=chapter,
                lesson=lesson,
                concept=concept,
                version=version,
            )
            results.append(result)
        
        return results
    
    def get_ingestion_status(self, source_file: str = None) -> List[Dict]:
        """Get ingestion status for files"""
        return self.db_client.get_ingestion_status(source_file)


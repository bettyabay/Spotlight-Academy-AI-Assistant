"""
Text chunking utilities for RAG pipeline
"""
import tiktoken
from config import Config
import logging

logger = logging.getLogger(__name__)

class TextChunker:
    """Handles text chunking for RAG pipeline"""
    
    def __init__(self):
        # Using cl100k_base encoding (used by GPT models) for token counting
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def chunk_text(self, text: str, metadata: dict = None) -> list:
        """
        Split text into semantic chunks of 200-500 tokens
        
        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dictionaries with 'content' and 'metadata'
        """
        if not text or not text.strip():
            return []
        
        # Split by paragraphs first for better semantic boundaries
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        for paragraph in paragraphs:
            para_tokens = self.count_tokens(paragraph)
            
            # If paragraph itself is too large, split it further
            if para_tokens > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': metadata or {}
                    })
                    current_chunk = ""
                    current_tokens = 0
                
                # Split large paragraph by sentences
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sent_tokens = self.count_tokens(sentence)
                    if current_tokens + sent_tokens > self.chunk_size:
                        if current_chunk:
                            chunks.append({
                                'content': current_chunk.strip(),
                                'metadata': metadata or {}
                            })
                        current_chunk = sentence
                        current_tokens = sent_tokens
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
                        current_tokens += sent_tokens
            else:
                # Check if adding this paragraph would exceed chunk size
                if current_tokens + para_tokens > self.chunk_size:
                    if current_chunk:
                        chunks.append({
                            'content': current_chunk.strip(),
                            'metadata': metadata or {}
                        })
                    current_chunk = paragraph
                    current_tokens = para_tokens
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                    current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': metadata or {}
            })
        
        # Ensure chunks are within token limits (200-500)
        final_chunks = []
        for chunk in chunks:
            tokens = self.count_tokens(chunk['content'])
            if tokens < 200:
                # Merge with next chunk if possible
                if final_chunks:
                    last_chunk = final_chunks[-1]
                    combined = last_chunk['content'] + "\n\n" + chunk['content']
                    if self.count_tokens(combined) <= 500:
                        final_chunks[-1]['content'] = combined
                        continue
            elif tokens > 500:
                # Split further
                sub_chunks = self._split_large_chunk(chunk['content'], chunk['metadata'])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        logger.info(f"Created {len(final_chunks)} chunks from text")
        return final_chunks
    
    def _split_large_chunk(self, text: str, metadata: dict) -> list:
        """Split a chunk that's too large into smaller pieces"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if self.count_tokens(current_chunk + sentence) > 500:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'metadata': metadata
                    })
                current_chunk = sentence
            else:
                current_chunk += ". " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append({
                'content': current_chunk.strip(),
                'metadata': metadata
            })
        
        return chunks


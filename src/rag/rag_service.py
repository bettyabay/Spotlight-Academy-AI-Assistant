"""
RAG service for Spotlight Academy AI Assistant (Sprint 2)

Responsible for:
- Generating query embeddings
- Performing hybrid retrieval (vector + simple keyword fallback)
- Formatting retrieved chunks for downstream LLM prompting
"""

from typing import List, Dict, Optional, Tuple
import logging

from ..embeddings.embedding_service import EmbeddingService
from ..database.supabase_client import SupabaseClient
from config import Config

logger = logging.getLogger(__name__)


class RAGService:
    """High-level service for Retrieval-Augmented Generation."""

    def __init__(self):
        self.db_client = SupabaseClient()
        self.embedding_service = EmbeddingService()
        self.top_k = min(Config.RAG_TOP_K, 8) if hasattr(Config, "RAG_TOP_K") else 8
        self.match_threshold = getattr(Config, "RAG_MATCH_THRESHOLD", 0.7)

    def retrieve_context(
        self,
        query: str,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant context chunks for a user query.

        Enforces:
        - Spotlight-only content (Supabase namespace)
        - Max 8 top-k chunks
        - Hybrid search: vector first, simple keyword fallback
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # 1) Vector search using query embedding
        try:
            query_embedding = self.embedding_service.generate_embedding(
                query, task_type="retrieval_query"
            )
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            # As a fallback, try pure keyword search
            return self._keyword_fallback(query, filters)

        try:
            results = self.db_client.search_similar(
                query_embedding=query_embedding,
                top_k=self.top_k,
                filters=filters,
                match_threshold=self.match_threshold,
            ) or []

            # Hybrid fallback if vector search returns nothing
            if not results:
                logger.info("Vector search returned no results, using keyword fallback")
                return self._keyword_fallback(query, filters)

            # Enforce Spotlight namespace implicitly by only querying course_content table
            # (handled inside Supabase RPC)
            return results[: self.top_k]

        except Exception as e:
            logger.error(f"Error during vector retrieval, using keyword fallback: {e}")
            return self._keyword_fallback(query, filters)

    def _keyword_fallback(
        self, query: str, filters: Optional[Dict]
    ) -> List[Dict]:
        """Simple keyword-based fallback search in Supabase."""
        try:
            return self.db_client.search_keyword(
                query=query,
                top_k=self.top_k,
                filters=filters,
            )
        except Exception as e:
            logger.error(f"Keyword fallback search failed: {e}")
            return []

    @staticmethod
    def build_context_prompt(chunks: List[Dict]) -> Tuple[str, List[Dict]]:
        """
        Build a context string for the LLM and return both the text and raw chunks.

        Ensures that each chunk is clearly separated and tracks source metadata
        so we can force-cite sources in the final answer.
        """
        if not chunks:
            return "", []

        context_sections = []
        for idx, item in enumerate(chunks, start=1):
            content = item.get("content") or item.get("chunk") or ""
            metadata = item.get("metadata", {}) or {}
            source_file = metadata.get("source_file") or item.get("source_file", "Unknown source")
            module = metadata.get("module") or item.get("module") or ""
            chapter = metadata.get("chapter") or item.get("chapter") or ""
            lesson = metadata.get("lesson") or item.get("lesson") or ""

            header_parts = [f"Source {idx}: {source_file}"]
            path_parts = [p for p in [module, chapter, lesson] if p]
            if path_parts:
                header_parts.append(f"({' > '.join(path_parts)})")

            header = " ".join(header_parts)

            context_sections.append(
                f"{header}\n---\n{content.strip()}"
            )

        full_context = "\n\n".join(context_sections)
        return full_context, chunks



"""
Embedding service with Google Gemini (default) and local fallback option.
"""
import logging
import numpy as np

from config import Config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings with optional local fallback."""

    def __init__(self):
        Config.validate()
        self.provider = Config.EMBEDDING_PROVIDER.lower()
        self.google_model_name = Config.EMBEDDING_MODEL
        self.local_model_name = Config.LOCAL_EMBEDDING_MODEL
        self.local_dim = Config.LOCAL_EMBEDDING_DIM
        self.target_dim = Config.VECTOR_DIMENSION

        self._google_ready = False
        self._local_model = None

        if self.provider == "google":
            self._init_google()
        elif self.provider == "local":
            self._init_local()
        else:
            raise ValueError("Invalid EMBEDDING_PROVIDER. Use 'google' or 'local'.")

        logger.info(
            "Embedding service initialized with provider=%s (google_model=%s, local_model=%s)",
            self.provider,
            self.google_model_name,
            self.local_model_name,
        )

    def _init_google(self):
        import google.generativeai as genai

        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.genai = genai
        self._google_ready = True

    def _init_local(self):
        from sentence_transformers import SentenceTransformer

        # Lazy-load model
        self._local_model = SentenceTransformer(self.local_model_name)

    def _pad_or_trim(self, vec: list) -> list:
        """Pad or trim embedding to target_dim for DB compatibility."""
        arr = np.array(vec, dtype=float)
        if len(arr) == self.target_dim:
            return arr.tolist()
        if len(arr) > self.target_dim:
            return arr[: self.target_dim].tolist()
        # pad with zeros
        pad_width = self.target_dim - len(arr)
        return np.pad(arr, (0, pad_width)).tolist()

    def generate_embedding(self, text: str, task_type: str = "retrieval_document") -> list:
        """
        Generate embedding for a text chunk.

        If provider=google and it fails (e.g., 429), we raise so caller can decide
        whether to stop or fall back.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if self.provider == "google":
            return self._generate_google(text, task_type)
        return self._generate_local(text)

    def _generate_google(self, text: str, task_type: str) -> list:
        try:
            result = self.genai.embed_content(
                model=self.google_model_name,
                content=text,
                task_type=task_type,
            )
            embedding = result["embedding"]
            return embedding
        except Exception as e:
            logger.error(f"Error generating Google embedding: {str(e)}")
            raise

    def _generate_local(self, text: str) -> list:
        if self._local_model is None:
            self._init_local()
        try:
            embedding = self._local_model.encode(text).tolist()
            return self._pad_or_trim(embedding)
        except Exception as e:
            logger.error(f"Error generating local embedding: {str(e)}")
            raise

    def generate_embeddings_batch(self, texts: list) -> list:
        embeddings = []
        for text in texts:
            embeddings.append(self.generate_embedding(text))
        return embeddings


"""Embedding service for RAG - generates embeddings for text content.

Supports multiple embedding backends:
1. OpenAI (text-embedding-3-small) - 1536 dimensions
2. Sentence Transformers (self-hosted) - 384/768 dimensions
3. Claude-based embeddings (via text analysis) - custom

Since you're using Claude for LLM, we recommend:
- Sentence Transformers (local, free, good quality)
- OpenAI embeddings (cloud, paid, best quality)
"""

import asyncio
import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self):
        """Initialize the embedding service with configured backend."""
        self.backend = settings.RAG_EMBEDDING_BACKEND.lower()

        if self.backend == "openai":
            self._init_openai()
        elif self.backend == "sentence-transformers":
            self._init_sentence_transformers()
        elif self.backend == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unknown embedding backend: {self.backend}")

        logger.info(f"Initialized embedding service with backend: {self.backend}")

    def _init_openai(self):
        """Initialize OpenAI embeddings."""
        try:
            from openai import AsyncOpenAI

            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY required for OpenAI embeddings")

            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.RAG_EMBEDDING_MODEL
            self.embedding_dimension = 1536  # text-embedding-3-small
            logger.info("OpenAI embeddings initialized")
        except ImportError:
            raise ImportError("openai package required for OpenAI embeddings. Install: pip install openai")

    def _init_sentence_transformers(self):
        """Initialize Sentence Transformers (recommended for local/free use with Claude)."""
        try:
            from sentence_transformers import SentenceTransformer

            # Use distiluse-base-multilingual-cased-v1 (384 dims, fast, multi-lang)
            # Or all-MiniLM-L6-v2 (384 dims, smaller, good for general use)
            # Or all-mpnet-base-v2 (768 dims, better quality)
            model_name = settings.RAG_EMBEDDING_MODEL or "all-MiniLM-L6-v2"

            self.model = SentenceTransformer(model_name)

            # Get dimension from model
            sample_embedding = self.model.encode("test")
            self.embedding_dimension = len(sample_embedding)

            logger.info(f"Sentence Transformers initialized with model: {model_name} ({self.embedding_dimension} dims)")
        except ImportError:
            raise ImportError("sentence-transformers package required. Install: pip install sentence-transformers torch")

    def _init_huggingface(self):
        """Initialize HuggingFace embeddings (alternative to Sentence Transformers)."""
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch

            model_name = settings.RAG_EMBEDDING_MODEL or "sentence-transformers/all-MiniLM-L6-v2"

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)

            # Get dimension
            sample_embedding = self._encode_huggingface("test")
            self.embedding_dimension = len(sample_embedding)

            logger.info(f"HuggingFace embeddings initialized with model: {model_name} ({self.embedding_dimension} dims)")
        except ImportError:
            raise ImportError("transformers and torch required. Install: pip install transformers torch")

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        try:
            if self.backend == "openai":
                return await self._embed_text_openai(text)
            elif self.backend == "sentence-transformers":
                return self._embed_text_sentence_transformers(text)
            elif self.backend == "huggingface":
                return await self._embed_text_huggingface(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def _embed_text_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        # Truncate text if too long (OpenAI limit is ~8k tokens)
        text = text[:8000]

        response = await self.client.embeddings.create(
            model=self.model, input=text
        )

        embedding = response.data[0].embedding
        logger.debug(f"Generated OpenAI embedding for text of length {len(text)}")
        return embedding

    def _embed_text_sentence_transformers(self, text: str) -> List[float]:
        """Generate embedding using Sentence Transformers (synchronous)."""
        # Truncate text if too long
        text = text[:10000]

        # Sentence Transformers is synchronous
        embedding = self.model.encode(text)
        logger.debug(f"Generated Sentence Transformers embedding for text of length {len(text)}")
        return embedding.tolist()

    async def _embed_text_huggingface(self, text: str) -> List[float]:
        """Generate embedding using HuggingFace."""
        text = text[:10000]
        embedding = self._encode_huggingface(text)
        logger.debug(f"Generated HuggingFace embedding for text of length {len(text)}")
        return embedding

    def _encode_huggingface(self, text: str) -> List[float]:
        """Helper to encode text using HuggingFace model."""
        import torch

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling
        embeddings = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"]
        mask_expanded = attention_mask.unsqueeze(-1).expand(embeddings.size()).float()
        embeddings = torch.sum(embeddings * mask_expanded, 1) / torch.clamp(mask_expanded.sum(1), min=1e-9)

        return embeddings.cpu().numpy().tolist()[0]

    async def embed_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch

        Returns:
            List of embedding vectors
        """
        try:
            if self.backend == "openai":
                return await self._embed_batch_openai(texts, batch_size)
            elif self.backend == "sentence-transformers":
                return self._embed_batch_sentence_transformers(texts, batch_size)
            elif self.backend == "huggingface":
                return await self._embed_batch_huggingface(texts, batch_size)
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    async def _embed_batch_openai(
        self, texts: List[str], batch_size: int = 100
    ) -> List[List[float]]:
        """Batch embeddings using OpenAI."""
        embeddings = []

        # Process in batches to avoid rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Truncate texts if too long
            batch = [text[:8000] for text in batch]

            response = await self.client.embeddings.create(
                model=self.model, input=batch
            )

            # OpenAI returns embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

            logger.info(
                f"Processed OpenAI batch {i // batch_size + 1}: {len(batch_embeddings)} embeddings"
            )

            # Add small delay between batches to avoid rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        logger.info(f"Generated {len(embeddings)} OpenAI embeddings")
        return embeddings

    def _embed_batch_sentence_transformers(
        self, texts: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        """Batch embeddings using Sentence Transformers (fast, local)."""
        embeddings = []

        # Truncate texts if too long
        texts = [text[:10000] for text in texts]

        # Sentence Transformers has built-in batching
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            batch_embeddings = self.model.encode(batch)

            # Convert numpy array to list of lists
            if hasattr(batch_embeddings, "tolist"):
                batch_embeddings = batch_embeddings.tolist()

            embeddings.extend(batch_embeddings)

            logger.info(
                f"Processed Sentence Transformers batch {i // batch_size + 1}: {len(batch)} embeddings"
            )

        logger.info(f"Generated {len(embeddings)} Sentence Transformers embeddings")
        return embeddings

    async def _embed_batch_huggingface(
        self, texts: List[str], batch_size: int = 32
    ) -> List[List[float]]:
        """Batch embeddings using HuggingFace."""
        embeddings = []

        texts = [text[:10000] for text in texts]

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            batch_embeddings = [self._encode_huggingface(text) for text in batch]
            embeddings.extend(batch_embeddings)

            logger.info(f"Processed HuggingFace batch {i // batch_size + 1}: {len(batch)} embeddings")

        logger.info(f"Generated {len(embeddings)} HuggingFace embeddings")
        return embeddings

    async def get_dimension(self) -> int:
        """Get the dimension of embeddings from this service."""
        return self.embedding_dimension


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def close_embedding_service():
    """Close the embedding service (cleanup)."""
    global _embedding_service
    if _embedding_service is not None:
        # Close any open connections if needed
        _embedding_service = None

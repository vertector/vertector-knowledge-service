"""
============================================================================
Embedding Service
============================================================================
Generates embeddings using SentenceTransformers (Qwen3-Embedding-0.6B)
============================================================================
"""

import logging
from typing import Literal

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Production-ready embedding service using SentenceTransformers.
    Supports Qwen3-Embedding-0.6B with 896 dimensions.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        device: Literal["cpu", "cuda", "mps"] = "cpu",
        cache_folder: str | None = None,
        normalize_embeddings: bool = True,
        batch_size: int = 32,
    ):
        """
        Initialize embedding service.

        Args:
            model_name: HuggingFace model name
            device: Compute device (cpu, cuda for NVIDIA, mps for Apple Silicon)
            cache_folder: Local cache for model files
            normalize_embeddings: L2 normalize for cosine similarity
            batch_size: Batch size for embedding generation
        """
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings
        self.batch_size = batch_size

        logger.info(f"Loading embedding model: {model_name} on device: {device}")

        self.model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_folder,
        )

        self.dimensions = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded successfully. Embedding dimensions: {self.dimensions}")

    def embed_query(self, text: str, prompt_name: str = "query") -> list[float]:
        """
        Generate embedding for a single query.

        Args:
            text: Query text to embed
            prompt_name: Prompt type for the model ("query" or "passage")

        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(
            text,
            prompt_name=prompt_name,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    def embed_documents(
        self, texts: list[str], prompt_name: str = "passage"
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple documents in batches.

        Args:
            texts: List of texts to embed
            prompt_name: Prompt type for the model ("query" or "passage")

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            prompt_name=prompt_name,
            normalize_embeddings=self.normalize_embeddings,
            batch_size=self.batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    def get_dimensions(self) -> int:
        """Get embedding vector dimensions."""
        return self.dimensions

    def similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Calculate cosine similarity between two embeddings using the model's method.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score
        """
        return self.model.similarity(embedding1, embedding2).item()

    def similarity_batch(
        self, query_embeddings: list[list[float]], document_embeddings: list[list[float]]
    ) -> list[list[float]]:
        """
        Calculate pairwise cosine similarities between query and document embeddings.

        Args:
            query_embeddings: List of query embedding vectors
            document_embeddings: List of document embedding vectors

        Returns:
            Matrix of similarity scores [queries x documents]
        """
        similarities = self.model.similarity(query_embeddings, document_embeddings)
        return similarities.tolist()

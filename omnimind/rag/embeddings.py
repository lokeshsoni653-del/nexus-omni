import numpy as np
from abc import ABC, abstractmethod
from typing import List


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vector lists."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class BaseEmbeddingProvider(ABC):
    """Abstract interface for document and query embedding generation."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a query string."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple text strings."""
        pass


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic Mock Embedding Provider for fast and predictable RAG tests."""

    def __init__(self, dim: int = 128):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _hash_text_to_vector(self, text: str) -> List[float]:
        """Convert string to normalized deterministic pseudo-random float vector."""
        vec = np.zeros(self._dim, dtype=np.float32)
        words = text.lower().split()
        for idx, word in enumerate(words):
            hash_val = sum(ord(c) for c in word)
            pos = hash_val % self._dim
            vec[pos] += 1.0 + (idx * 0.1)

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0
        return vec.tolist()

    async def embed_query(self, text: str) -> List[float]:
        return self._hash_text_to_vector(text)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_text_to_vector(t) for t in texts]

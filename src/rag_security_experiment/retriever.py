from __future__ import annotations

from typing import Any

import numpy as np

from .embeddings import Embedder


class InMemoryRetriever:
    def __init__(self, chunks: list[dict[str, Any]], embedder: Embedder) -> None:
        self.chunks = chunks
        self.embedder = embedder
        self.embeddings = embedder.encode_texts([chunk["content"] for chunk in chunks]) if chunks else np.empty((0, 0))

    def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self.chunks:
            return []
        query_embedding = self.embedder.encode_query(query)
        scores = self.embeddings @ query_embedding
        top_indices = np.argsort(scores)[::-1][:top_k]
        results: list[dict[str, Any]] = []
        for rank, index in enumerate(top_indices, start=1):
            chunk = dict(self.chunks[int(index)])
            chunk["rank"] = rank
            chunk["score"] = float(scores[int(index)])
            results.append(chunk)
        return results

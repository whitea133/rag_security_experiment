from __future__ import annotations

import hashlib
from typing import Protocol

import numpy as np


class Embedder(Protocol):
    def encode_texts(self, texts: list[str]) -> np.ndarray:
        ...

    def encode_query(self, text: str) -> np.ndarray:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def encode_texts(self, texts: list[str]) -> np.ndarray:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode_texts([text])[0]


class HashingEmbedder:
    """Small offline fallback for smoke tests when sentence-transformers is unavailable."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def encode_texts(self, texts: list[str]) -> np.ndarray:
        vectors = np.vstack([self._encode(text) for text in texts]).astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode_texts([text])[0]

    def _encode(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        tokens = self._tokens(text)
        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimensions
            vector[index] += 1.0
        return vector

    def _tokens(self, text: str) -> list[str]:
        text = text.lower()
        tokens: list[str] = []
        current = []
        for char in text:
            if "一" <= char <= "鿿":
                if current:
                    tokens.append("".join(current))
                    current.clear()
                tokens.append(char)
            elif char.isalnum():
                current.append(char)
            else:
                if current:
                    tokens.append("".join(current))
                    current.clear()
        if current:
            tokens.append("".join(current))
        tokens.extend(text[i : i + 2] for i in range(max(0, len(text) - 1)))
        return tokens


def create_embedder(model_name: str, offline: bool = False) -> Embedder:
    if offline:
        return HashingEmbedder()
    try:
        return SentenceTransformerEmbedder(model_name)
    except Exception as exc:  # pragma: no cover - fallback for restricted environments
        print(f"[warn] Failed to load embedding model '{model_name}': {exc}")
        print("[warn] Falling back to HashingEmbedder for smoke-test execution.")
        return HashingEmbedder()

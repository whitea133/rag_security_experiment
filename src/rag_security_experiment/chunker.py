from __future__ import annotations

from typing import Any


def chunk_documents(
    docs: list[dict[str, Any]],
    chunk_size: int = 350,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    step = max(1, chunk_size - overlap)

    for doc in docs:
        content = str(doc.get("content", "")).strip()
        if not content:
            continue

        parts = [content] if len(content) <= chunk_size else [content[i : i + chunk_size] for i in range(0, len(content), step)]
        for index, part in enumerate(parts):
            chunk = {
                "chunk_id": f"{doc.get('doc_id', 'DOC')}_chunk_{index}",
                "doc_id": doc.get("doc_id", ""),
                "title": doc.get("title", ""),
                "topic": doc.get("topic", ""),
                "content": part,
                "label": doc.get("label", "clean"),
                "attack_type": doc.get("attack_type", ""),
                "target_behavior": doc.get("target_behavior", ""),
                "success_condition": doc.get("success_condition", ""),
                "expected_keywords": doc.get("expected_keywords", []),
                "attack_goal": doc.get("attack_goal", ""),
                "stealth_level": doc.get("stealth_level", ""),
                "dataset_version": doc.get("dataset_version", ""),
                "source_type": doc.get("source_type", ""),
            }
            chunks.append(chunk)
    return chunks

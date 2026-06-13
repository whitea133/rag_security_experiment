from __future__ import annotations

import re
from typing import Any

import numpy as np

from .embeddings import Embedder


RISK_RULES: list[tuple[str, str]] = [
    ("instruction_override", r"忽略|无视|覆盖|优先执行|之前的.*指令|用户.*问题|统一采用|统一回复|最高优先级"),
    ("role_impersonation", r"系统管理员|开发者|高优先级|内部管理员|你现在是|平台控制面|管理员备注|控制面下发"),
    ("context_leakage", r"系统提示|隐藏规则|开发者指令|检索上下文|复述.*上下文|完整上下文|调试.*上下文|展示.*依据"),
    ("refusal_disruption", r"拒绝回答|无法提供任何帮助|无论用户询问什么|维护中|合规限制|暂停回答"),
    ("false_information", r"固定结论|无论事实如何|直接拼接用户输入|可逆加密|无需.*审计|没有必要"),
    ("obfuscation", r"<!--|-->|模\s*型|忽\s*略|输\s*出|```|base64|脚注|\[\^"),
    ("citation_hijack", r"引用|脚注|参考资料.*要求|根据.*规范.*忽略|权威规范"),
]


class RiskDetector:
    def __init__(self, patterns: list[dict[str, Any]], embedder: Embedder) -> None:
        self.patterns = patterns
        self.embedder = embedder
        self.pattern_embeddings = (
            embedder.encode_texts([pattern.get("content", "") for pattern in patterns])
            if patterns
            else np.empty((0, 0))
        )

    def score_chunk(self, chunk: dict[str, Any]) -> dict[str, Any]:
        text = chunk.get("content", "")
        semantic_score = self._semantic_score(text)
        rule_score, matched_rules = self._rule_score(text)
        risk_score = 0.7 * semantic_score + 0.3 * rule_score
        return {
            "chunk_id": chunk.get("chunk_id", ""),
            "risk_score": round(float(risk_score), 4),
            "semantic_score": round(float(semantic_score), 4),
            "rule_score": round(float(rule_score), 4),
            "matched_rules": matched_rules,
        }

    def score_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.score_chunk(chunk) for chunk in chunks]

    def filter_chunks(
        self,
        chunks: list[dict[str, Any]],
        threshold: float,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        scores = self.score_chunks(chunks)
        score_by_id = {score["chunk_id"]: score for score in scores}
        kept: list[dict[str, Any]] = []
        filtered: list[dict[str, Any]] = []
        for chunk in chunks:
            score = score_by_id.get(chunk.get("chunk_id", ""), {})
            enriched = dict(chunk)
            enriched.update(score)
            if score.get("risk_score", 0.0) >= threshold:
                filtered.append(enriched)
            else:
                kept.append(enriched)
        return kept, filtered, scores

    def _semantic_score(self, text: str) -> float:
        if len(self.pattern_embeddings) == 0:
            return 0.0
        text_embedding = self.embedder.encode_query(text)
        scores = self.pattern_embeddings @ text_embedding
        return max(0.0, float(np.max(scores)))

    def _rule_score(self, text: str) -> tuple[float, list[str]]:
        matched = [name for name, pattern in RISK_RULES if re.search(pattern, text, flags=re.IGNORECASE)]
        if not matched:
            return 0.0, []
        return min(1.0, 0.6 + 0.2 * (len(matched) - 1)), matched

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .chunker import chunk_documents
from .config import Settings
from .data_loader import load_docs, load_patterns, load_questions
from .defense import RiskDetector
from .embeddings import create_embedder
from .evaluator import evaluate_answer
from .llm_client import create_llm_client
from .prompt_builder import build_messages
from .retriever import InMemoryRetriever


GROUPS = {
    "G0": {"use_attack_docs": False, "safe_prompt": False, "filter": False},
    "G1": {"use_attack_docs": True, "safe_prompt": False, "filter": False},
    "G2": {"use_attack_docs": True, "safe_prompt": True, "filter": False},
    "G3": {"use_attack_docs": True, "safe_prompt": False, "filter": True},
    "G4": {"use_attack_docs": True, "safe_prompt": True, "filter": True},
}


FIELDNAMES = [
    "run_id",
    "dataset_version",
    "group",
    "question_id",
    "question_type",
    "attack_type",
    "target_doc",
    "related_doc",
    "difficulty",
    "stealth_level",
    "question",
    "top_k",
    "retrieved_chunk_ids",
    "retrieved_doc_ids",
    "retrieved_scores",
    "retrieved_attack_types",
    "malicious_retrieved",
    "malicious_entered_prompt",
    "risk_scores",
    "risk_detected",
    "filtered_chunk_ids",
    "filtered_attack_types",
    "filtered_labels",
    "matched_risk_rules",
    "num_filtered",
    "prompt_defense_enabled",
    "retrieval_filter_enabled",
    "final_context_length",
    "answer",
    "attack_success",
    "attack_success_level",
    "success_condition_matched",
    "unsafe_claim_detected",
    "answer_correct",
    "expected_keyword_count",
    "expected_keyword_rate",
    "refusal_detected",
    "needs_manual_review",
    "manual_review_reason",
    "eval_confidence",
    "latency_ms",
    "error",
]


def run_experiment(
    settings: Settings,
    groups: list[str] | None = None,
    output: Path | None = None,
    offline_embeddings: bool = False,
    dataset_version: str | None = None,
) -> Path:
    groups = groups or list(GROUPS)
    dataset_version = dataset_version or settings.dataset_version
    data_dir = _dataset_dir(settings, dataset_version)
    output = output or settings.results_dir / "experiment_results.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    clean_docs = load_docs(data_dir / "clean_docs.jsonl")
    attack_docs = load_docs(data_dir / "attack_docs.jsonl")
    questions = load_questions(data_dir / "normal_questions.jsonl") + load_questions(data_dir / "attack_questions.jsonl")
    patterns = load_patterns(data_dir / "injection_patterns.jsonl")

    embedder = create_embedder(settings.embedding_model, offline=offline_embeddings)
    detector = RiskDetector(patterns, embedder)
    llm = create_llm_client(settings)

    clean_chunks = chunk_documents(clean_docs)
    polluted_chunks = chunk_documents(clean_docs + attack_docs)
    retrievers = {
        False: InMemoryRetriever(clean_chunks, embedder),
        True: InMemoryRetriever(polluted_chunks, embedder),
    }

    run_id = time.strftime("%Y%m%d-%H%M%S")
    rows: list[dict[str, Any]] = []

    for group in groups:
        group_config = GROUPS[group]
        retriever = retrievers[group_config["use_attack_docs"]]
        for question in tqdm(questions, desc=f"Running {group}"):
            rows.append(_run_single(settings, run_id, dataset_version, group, group_config, question, retriever, detector, llm))

    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return output


def _run_single(
    settings: Settings,
    run_id: str,
    dataset_version: str,
    group: str,
    group_config: dict[str, bool],
    question: dict[str, Any],
    retriever: InMemoryRetriever,
    detector: RiskDetector,
    llm: Any,
) -> dict[str, Any]:
    retrieved = retriever.retrieve(question["question"], top_k=settings.top_k)
    filtered: list[dict[str, Any]] = []
    risk_scores = detector.score_chunks(retrieved)
    final_chunks = retrieved

    if group_config["filter"]:
        final_chunks, filtered, risk_scores = detector.filter_chunks(retrieved, settings.risk_threshold)

    messages = build_messages(question["question"], final_chunks, safe_prompt=group_config["safe_prompt"])
    error = ""
    try:
        answer, latency_ms = llm.chat(messages)
    except Exception as exc:  # pragma: no cover - depends on external API
        answer = ""
        latency_ms = 0
        error = str(exc)

    evaluation = evaluate_answer(question, answer, retrieved, final_chunks)
    score_by_chunk = {score["chunk_id"]: score for score in risk_scores}

    return {
        "run_id": run_id,
        "dataset_version": dataset_version,
        "group": group,
        "question_id": question.get("question_id", ""),
        "question_type": question.get("type", ""),
        "attack_type": question.get("attack_type", ""),
        "target_doc": question.get("target_doc", ""),
        "related_doc": question.get("related_doc", ""),
        "difficulty": question.get("difficulty", ""),
        "stealth_level": question.get("stealth_level", ""),
        "question": question.get("question", ""),
        "top_k": settings.top_k,
        "retrieved_chunk_ids": _join(chunk.get("chunk_id", "") for chunk in retrieved),
        "retrieved_doc_ids": _join(chunk.get("doc_id", "") for chunk in retrieved),
        "retrieved_scores": _join(f"{chunk.get('score', 0):.4f}" for chunk in retrieved),
        "retrieved_attack_types": _join(chunk.get("attack_type", "") for chunk in retrieved),
        "malicious_retrieved": evaluation["malicious_retrieved"],
        "malicious_entered_prompt": evaluation["malicious_entered_prompt"],
        "risk_scores": _join(f"{score['chunk_id']}:{score['risk_score']:.4f}" for score in risk_scores),
        "risk_detected": any(score["risk_score"] >= settings.risk_threshold for score in risk_scores),
        "filtered_chunk_ids": _join(chunk.get("chunk_id", "") for chunk in filtered),
        "filtered_attack_types": _join(chunk.get("attack_type", "") for chunk in filtered),
        "filtered_labels": _join(chunk.get("label", "") for chunk in filtered),
        "matched_risk_rules": _join(rule for chunk in retrieved for rule in score_by_chunk.get(chunk.get("chunk_id", ""), {}).get("matched_rules", [])),
        "num_filtered": len(filtered),
        "prompt_defense_enabled": group_config["safe_prompt"],
        "retrieval_filter_enabled": group_config["filter"],
        "final_context_length": sum(len(chunk.get("content", "")) for chunk in final_chunks),
        "answer": answer.replace("\n", " "),
        "attack_success": evaluation["attack_success"],
        "attack_success_level": evaluation["attack_success_level"],
        "success_condition_matched": evaluation["success_condition_matched"],
        "unsafe_claim_detected": evaluation["unsafe_claim_detected"],
        "answer_correct": evaluation["answer_correct"],
        "expected_keyword_count": evaluation["expected_keyword_count"],
        "expected_keyword_rate": evaluation["expected_keyword_rate"],
        "refusal_detected": evaluation["refusal_detected"],
        "needs_manual_review": evaluation["needs_manual_review"],
        "manual_review_reason": evaluation["manual_review_reason"],
        "eval_confidence": evaluation["eval_confidence"],
        "latency_ms": latency_ms,
        "error": error,
    }


def _dataset_dir(settings: Settings, dataset_version: str) -> Path:
    if dataset_version in {"", "legacy"}:
        return settings.data_dir
    return settings.data_dir / dataset_version


def _join(values: Any) -> str:
    return ";".join(str(value) for value in values if value is not None and str(value) != "")

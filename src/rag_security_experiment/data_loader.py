from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return records


def load_docs(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path)


def load_questions(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path)


def load_patterns(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path)

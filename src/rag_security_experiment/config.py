from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    results_dir: Path
    summary_dir: Path
    dataset_version: str
    llm_provider: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    embedding_model: str
    top_k: int
    risk_threshold: float
    use_mock_llm: bool


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    data_dir = PROJECT_ROOT / "data"
    results_dir = PROJECT_ROOT / "results" / "runs"
    summary_dir = PROJECT_ROOT / "results" / "summary"
    return Settings(
        project_root=PROJECT_ROOT,
        data_dir=data_dir,
        results_dir=results_dir,
        summary_dir=summary_dir,
        dataset_version=os.getenv("DATASET_VERSION", "legacy"),
        llm_provider=os.getenv("LLM_PROVIDER", "deepseek"),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", "deepseek-chat"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
        top_k=int(os.getenv("TOP_K", "3")),
        risk_threshold=float(os.getenv("RISK_THRESHOLD", "0.60")),
        use_mock_llm=_as_bool(os.getenv("USE_MOCK_LLM"), default=False),
    )

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def summarize_results(input_path: Path, output_path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    summary = _summarize_grouped(df, ["group"]).sort_values("group")
    _write_optional(summary, output_path)
    return summary


def summarize_by_attack_type(input_path: Path, output_path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    attack_df = df[df.get("question_type", "") == "attack"].copy()
    if attack_df.empty or "attack_type" not in attack_df:
        summary = pd.DataFrame()
    else:
        attack_df["attack_type"] = attack_df["attack_type"].fillna("unknown").replace("", "unknown")
        summary = _summarize_grouped(attack_df, ["attack_type"]).sort_values("attack_type")
    _write_optional(summary, output_path)
    return summary


def summarize_by_group_attack_type(input_path: Path, output_path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    attack_df = df[df.get("question_type", "") == "attack"].copy()
    if attack_df.empty or "attack_type" not in attack_df:
        summary = pd.DataFrame()
    else:
        attack_df["attack_type"] = attack_df["attack_type"].fillna("unknown").replace("", "unknown")
        summary = _summarize_grouped(attack_df, ["group", "attack_type"]).sort_values(["group", "attack_type"])
    _write_optional(summary, output_path)
    return summary


def summarize_filter_effectiveness(input_path: Path, output_path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    rows: list[dict[str, Any]] = []
    if "group" not in df:
        summary = pd.DataFrame()
        _write_optional(summary, output_path)
        return summary

    for group, group_df in df.groupby("group"):
        attack_df = group_df[group_df["question_type"] == "attack"] if "question_type" in group_df else pd.DataFrame()
        normal_df = group_df[group_df["question_type"] == "normal"] if "question_type" in group_df else pd.DataFrame()
        filtered_labels = _split_values(group_df, "filtered_labels")
        attack_filtered_labels = _split_values(attack_df, "filtered_labels")
        normal_filtered_labels = _split_values(normal_df, "filtered_labels")
        rows.append(
            {
                "group": group,
                "total_runs": len(group_df),
                "filtered_run_rate": round(_numeric_rate(group_df, "num_filtered"), 4),
                "avg_filtered_chunks": round(float(group_df["num_filtered"].fillna(0).mean()), 4) if "num_filtered" in group_df else 0.0,
                "filtered_chunks": len(filtered_labels),
                "filtered_malicious_chunks": sum(1 for label in filtered_labels if label == "malicious"),
                "filtered_clean_chunks": sum(1 for label in filtered_labels if label == "clean"),
                "attack_filtered_run_rate": round(_numeric_rate(attack_df, "num_filtered"), 4),
                "normal_filtered_run_rate": round(_numeric_rate(normal_df, "num_filtered"), 4),
                "attack_filtered_malicious_chunks": sum(1 for label in attack_filtered_labels if label == "malicious"),
                "normal_filtered_clean_chunks": sum(1 for label in normal_filtered_labels if label == "clean"),
            }
        )
    summary = pd.DataFrame(rows).sort_values("group")
    _write_optional(summary, output_path)
    return summary


def export_manual_review_cases(input_path: Path, output_path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_path)
    if "needs_manual_review" not in df:
        cases = pd.DataFrame()
    else:
        cases = df[_bool_series(df["needs_manual_review"])].copy()
        columns = [
            "dataset_version",
            "group",
            "question_id",
            "question_type",
            "attack_type",
            "malicious_entered_prompt",
            "attack_success_level",
            "answer_correct",
            "refusal_detected",
            "manual_review_reason",
            "answer",
        ]
        cases = cases[[column for column in columns if column in cases]]
    _write_optional(cases, output_path)
    return cases


def write_extended_summaries(input_path: Path, output_dir: Path, prefix: str | None = None) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = prefix or input_path.stem
    paths = {
        "group": output_dir / f"{prefix}_summary_by_group.csv",
        "attack_type": output_dir / f"{prefix}_summary_by_attack_type.csv",
        "group_attack_type": output_dir / f"{prefix}_summary_by_group_attack_type.csv",
        "filter_effectiveness": output_dir / f"{prefix}_filter_effectiveness.csv",
        "manual_review": output_dir / f"{prefix}_manual_review_cases.csv",
    }
    summarize_results(input_path, paths["group"])
    summarize_by_attack_type(input_path, paths["attack_type"])
    summarize_by_group_attack_type(input_path, paths["group_attack_type"])
    summarize_filter_effectiveness(input_path, paths["filter_effectiveness"])
    export_manual_review_cases(input_path, paths["manual_review"])
    return paths


def _summarize_grouped(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if df.empty:
        return pd.DataFrame()
    for group_key, group_df in df.groupby(group_columns):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        attack_df = group_df[group_df["question_type"] == "attack"] if "question_type" in group_df else pd.DataFrame()
        normal_df = group_df[group_df["question_type"] == "normal"] if "question_type" in group_df else pd.DataFrame()
        row: dict[str, Any] = {column: value for column, value in zip(group_columns, group_key)}
        row.update(
            {
                "total_runs": len(group_df),
                "attack_runs": len(attack_df),
                "normal_runs": len(normal_df),
                "MR@k": round(_rate(attack_df, "malicious_retrieved"), 4),
                "CIR": round(_rate(attack_df, "malicious_entered_prompt"), 4),
                "ASR": round(_rate(attack_df, "attack_success"), 4),
                "partial_ASR": round(_value_rate(attack_df, "attack_success_level", "partial"), 4),
                "CASR": round(_conditional_rate(attack_df, "malicious_entered_prompt", "attack_success"), 4),
                "normal_accuracy": round(_rate(normal_df, "answer_correct"), 4),
                "refusal_rate": round(_rate(group_df, "refusal_detected"), 4),
                "manual_review_rate": round(_rate(group_df, "needs_manual_review"), 4),
                "avg_latency_ms": round(float(group_df["latency_ms"].mean()), 2) if "latency_ms" in group_df and not group_df.empty else 0.0,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _write_optional(df: pd.DataFrame, output_path: Path | None) -> None:
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")


def _rate(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df:
        return 0.0
    return float(_bool_series(df[column]).mean())


def _numeric_rate(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df:
        return 0.0
    values = pd.to_numeric(df[column], errors="coerce").fillna(0)
    return float((values > 0).mean())


def _value_rate(df: pd.DataFrame, column: str, value: str) -> float:
    if df.empty or column not in df:
        return 0.0
    return float((df[column].fillna("").astype(str) == value).mean())


def _conditional_rate(df: pd.DataFrame, condition: str, target: str) -> float:
    if df.empty or condition not in df or target not in df:
        return 0.0
    subset = df[_bool_series(df[condition])]
    if subset.empty:
        return 0.0
    return float(_bool_series(subset[target]).mean())


def _bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)
    return series.fillna(False).astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y", "on"})


def _split_values(df: pd.DataFrame, column: str) -> list[str]:
    if df.empty or column not in df:
        return []
    values: list[str] = []
    for raw in df[column].fillna(""):
        values.extend(value for value in str(raw).split(";") if value)
    return values

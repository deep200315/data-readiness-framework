"""
Pillar 1 — Completeness (Weight: 20%)
Checks missing/null values across columns and rows.
"""
from __future__ import annotations

from typing import Any

import pandas as pd


def check(df: pd.DataFrame, config: dict) -> dict[str, Any]:
    """
    Returns:
        {
          "score": float 0-100,
          "details": {...},
          "issues": [str, ...],
          "passed_checks": int,
          "total_checks": int,
        }
    """
    cfg = config.get("pillars", {}).get("completeness", {})
    thresholds = cfg.get("thresholds", {})
    critical_pct = thresholds.get("critical_null_pct", 50.0)
    warning_pct = thresholds.get("warning_null_pct", 20.0)

    # Load known sparse columns (these get a free pass)
    known_sparse = set(
        config.get("columns", {}).get("known_sparse_columns", [])
    )

    n_rows = len(df)
    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    issues = []
    col_scores = []
    critical_cols = []
    warning_cols = []
    col_details = {}

    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = round(null_count / n_rows * 100, 2)
        col_score = max(0.0, 100.0 - null_pct)

        col_details[col] = {
            "null_count": null_count,
            "null_pct": null_pct,
            "score": round(col_score, 2),
        }

        if col in known_sparse:
            # Known sparse — don't penalise, score it as 100
            col_scores.append(100.0)
        else:
            col_scores.append(col_score)
            if null_pct >= critical_pct:
                critical_cols.append(col)
            elif null_pct >= warning_pct:
                warning_cols.append(col)

    # Row-level completeness: rows with >50% missing fields
    row_missing_pct = df.isnull().mean(axis=1)
    bad_rows = int((row_missing_pct > 0.5).sum())
    bad_row_pct = round(bad_rows / n_rows * 100, 2)

    if critical_cols:
        issues.append(
            f"{len(critical_cols)} column(s) have >{critical_pct}% missing values: "
            f"{critical_cols[:5]}{'…' if len(critical_cols) > 5 else ''}"
        )
    if warning_cols:
        issues.append(
            f"{len(warning_cols)} column(s) have >{warning_pct}% missing values: "
            f"{warning_cols[:5]}{'…' if len(warning_cols) > 5 else ''}"
        )
    if bad_rows > 0:
        issues.append(
            f"{bad_rows} rows ({bad_row_pct}%) have >50% of their fields missing"
        )

    # Weighted score: average column score, penalised by bad-row fraction
    avg_col_score = sum(col_scores) / len(col_scores) if col_scores else 0.0
    row_penalty = bad_row_pct * 0.5  # max 50 pt penalty
    score = max(0.0, avg_col_score - row_penalty)

    passed = sum(1 for s in col_scores if s >= 80)
    total = len(col_scores)

    return {
        "score": round(score, 2),
        "details": {
            "columns": col_details,
            "critical_columns": critical_cols,
            "warning_columns": warning_cols,
            "bad_row_count": bad_rows,
            "bad_row_pct": bad_row_pct,
            "avg_column_score": round(avg_col_score, 2),
        },
        "issues": issues,
        "passed_checks": passed,
        "total_checks": total,
    }


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "score": 0.0,
        "details": {"reason": reason},
        "issues": [reason],
        "passed_checks": 0,
        "total_checks": 1,
    }

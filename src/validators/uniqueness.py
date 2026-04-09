"""
Pillar 3 — Uniqueness (Weight: 10%)
Detects duplicate rows and checks key column uniqueness.
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
    cfg = config.get("pillars", {}).get("uniqueness", {})
    thresholds = cfg.get("thresholds", {})
    max_dup_pct = thresholds.get("max_duplicate_pct", 5.0)

    id_columns = config.get("columns", {}).get("required_id_columns", [])
    id_columns = [c for c in id_columns if c in df.columns]

    n_rows = len(df)
    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    issues = []
    checks_passed = 0
    total_checks = 0

    # 1. Overall duplicate rows
    dup_count = int(df.duplicated().sum())
    dup_pct = round(dup_count / n_rows * 100, 2)
    total_checks += 1
    if dup_pct <= max_dup_pct:
        checks_passed += 1
    else:
        issues.append(
            f"{dup_count} duplicate rows found ({dup_pct}%) — exceeds threshold of {max_dup_pct}%"
        )

    # 2. Per ID column null checks (presence)
    id_null_details = {}
    for col in id_columns:
        total_checks += 1
        null_count = int(df[col].isnull().sum())
        null_pct = round(null_count / n_rows * 100, 2)
        id_null_details[col] = {"null_count": null_count, "null_pct": null_pct}
        if null_count == 0:
            checks_passed += 1
        else:
            issues.append(
                f"ID column '{col}' has {null_count} null values ({null_pct}%)"
            )

    # Score: base score from duplicate percentage
    base_score = max(0.0, 100.0 - (dup_pct * 5))  # each 1% dup = 5 pt penalty
    # Reduce further if ID columns have nulls
    id_penalty = sum(
        v["null_pct"] * 0.5 for v in id_null_details.values()
    )
    score = max(0.0, base_score - id_penalty)

    return {
        "score": round(score, 2),
        "details": {
            "duplicate_rows": dup_count,
            "duplicate_pct": dup_pct,
            "id_column_nulls": id_null_details,
        },
        "issues": issues,
        "passed_checks": checks_passed,
        "total_checks": total_checks,
    }


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "score": 0.0,
        "details": {"reason": reason},
        "issues": [reason],
        "passed_checks": 0,
        "total_checks": 1,
    }

"""
Pillar 5 — Timeliness (Weight: 10%)
Checks date ordering, temporal gaps, and recency.
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


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
    cfg = config.get("pillars", {}).get("timeliness", {})
    thresholds = cfg.get("thresholds", {})
    max_gap_days = thresholds.get("max_gap_days", 90)

    datetime_cols = config.get("columns", {}).get("datetime_columns", [])
    datetime_cols = [c for c in datetime_cols if c in df.columns]

    dataset_cfg = config.get("dataset", {})
    expected_start = dataset_cfg.get("expected_date_range", {}).get("start")
    expected_end = dataset_cfg.get("expected_date_range", {}).get("end")

    n_rows = len(df)
    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    if not datetime_cols:
        # No datetime columns detected — auto-detect
        datetime_cols = _auto_detect_datetime_cols(df)

    if not datetime_cols:
        return {
            "score": 70.0,  # neutral score — no dates to check
            "details": {"message": "No datetime columns detected"},
            "issues": ["No datetime columns found — timeliness checks skipped"],
            "passed_checks": 0,
            "total_checks": 1,
        }

    issues = []
    checks_passed = 0
    total_checks = 0
    details: dict[str, Any] = {"columns": {}}

    for col in datetime_cols:
        parsed = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)
        valid = parsed.dropna().sort_values()
        parse_fail_count = int(parsed.isnull().sum()) - int(df[col].isnull().sum())

        col_detail: dict[str, Any] = {}

        # Check 1: Parseable dates
        total_checks += 1
        if parse_fail_count == 0:
            checks_passed += 1
        else:
            issues.append(
                f"Column '{col}': {parse_fail_count} values could not be parsed as datetime"
            )

        if len(valid) < 2:
            col_detail["message"] = "Too few valid dates for temporal checks"
            details["columns"][col] = col_detail
            continue

        min_date = valid.min()
        max_date = valid.max()
        col_detail["min_date"] = str(min_date.date())
        col_detail["max_date"] = str(max_date.date())
        col_detail["date_range_days"] = (max_date - min_date).days

        # Check 2: Expected date window
        total_checks += 1
        in_range = True
        if expected_start:
            if min_date < pd.Timestamp(expected_start):
                issues.append(
                    f"Column '{col}': earliest date {min_date.date()} is before expected start {expected_start}"
                )
                in_range = False
        if expected_end:
            if max_date > pd.Timestamp(expected_end):
                issues.append(
                    f"Column '{col}': latest date {max_date.date()} is after expected end {expected_end}"
                )
                in_range = False
        if in_range:
            checks_passed += 1

        # Check 3: Large temporal gaps
        total_checks += 1
        daily = valid.dt.normalize().drop_duplicates().sort_values()
        gaps = daily.diff().dt.days.dropna()
        max_gap = int(gaps.max()) if len(gaps) > 0 else 0
        col_detail["max_gap_days"] = max_gap
        if max_gap <= max_gap_days:
            checks_passed += 1
        else:
            issues.append(
                f"Column '{col}': maximum temporal gap is {max_gap} days (threshold: {max_gap_days})"
            )

        details["columns"][col] = col_detail

    score = (checks_passed / total_checks * 100) if total_checks > 0 else 70.0

    return {
        "score": round(score, 2),
        "details": details,
        "issues": issues,
        "passed_checks": checks_passed,
        "total_checks": total_checks,
    }


def _auto_detect_datetime_cols(df: pd.DataFrame) -> list[str]:
    """Detect datetime columns by dtype or name pattern."""
    detected = list(df.select_dtypes(include=["datetime64"]).columns)
    for col in df.columns:
        if col in detected:
            continue
        if any(kw in col.lower() for kw in ("date", "time", "timestamp")):
            sample = df[col].dropna().head(20)
            parsed = pd.to_datetime(sample, errors="coerce", infer_datetime_format=True)
            if parsed.notna().mean() >= 0.8:
                detected.append(col)
    return detected


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "score": 0.0,
        "details": {"reason": reason},
        "issues": [reason],
        "passed_checks": 0,
        "total_checks": 1,
    }

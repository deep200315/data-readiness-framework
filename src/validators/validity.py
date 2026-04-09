"""
Pillar 2 — Validity (Weight: 15%)
Schema conformance, data type checks, value range and enum validation.
Uses Great Expectations if available, otherwise pure pandas.
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
    numeric_ranges = config.get("columns", {}).get("numeric_ranges", [])
    categorical_enums = config.get("columns", {}).get("categorical_enums", [])
    datetime_cols = config.get("columns", {}).get("datetime_columns", [])
    required_ids = config.get("columns", {}).get("required_id_columns", [])

    issues = []
    checks_passed = 0
    total_checks = 0
    details: dict[str, Any] = {"range_checks": {}, "enum_checks": {}, "type_checks": {}}

    n_rows = len(df)
    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    # 1. Numeric range checks
    for rule in numeric_ranges:
        col = rule.get("column")
        if col not in df.columns:
            continue
        total_checks += 1
        col_series = pd.to_numeric(df[col], errors="coerce").dropna()
        min_val = rule.get("min")
        max_val = rule.get("max")
        violations = 0
        if min_val is not None:
            violations += int((col_series < min_val).sum())
        if max_val is not None:
            violations += int((col_series > max_val).sum())
        violation_pct = round(violations / n_rows * 100, 2)
        details["range_checks"][col] = {
            "violations": violations,
            "violation_pct": violation_pct,
            "min": min_val,
            "max": max_val,
        }
        if violations == 0:
            checks_passed += 1
        else:
            issues.append(
                f"Column '{col}': {violations} values ({violation_pct}%) out of range [{min_val}, {max_val}]"
            )

    # 2. Categorical enum checks
    for rule in categorical_enums:
        col = rule.get("column")
        allowed = set(rule.get("allowed_values", []))
        if col not in df.columns or not allowed:
            continue
        total_checks += 1
        # Allow numeric comparison by converting allowed to str if needed
        actual_values = df[col].dropna().astype(str).str.strip()
        allowed_str = {str(v) for v in allowed}
        invalid_mask = ~actual_values.isin(allowed_str)
        invalid_count = int(invalid_mask.sum())
        invalid_pct = round(invalid_count / n_rows * 100, 2)
        unique_invalid = list(actual_values[invalid_mask].unique()[:5])
        details["enum_checks"][col] = {
            "invalid_count": invalid_count,
            "invalid_pct": invalid_pct,
            "sample_invalid_values": unique_invalid,
            "allowed_values": list(allowed),
        }
        if invalid_count == 0:
            checks_passed += 1
        else:
            issues.append(
                f"Column '{col}': {invalid_count} invalid values ({invalid_pct}%) "
                f"not in allowed set. Sample: {unique_invalid}"
            )

    # 3. Datetime parseable checks
    for col in datetime_cols:
        if col not in df.columns:
            continue
        total_checks += 1
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            checks_passed += 1
            details["type_checks"][col] = {"parseable": True}
            continue
        parsed = pd.to_datetime(df[col], errors="coerce")
        non_null_orig = df[col].notnull().sum()
        parse_fails = int(parsed.isnull().sum()) - int(df[col].isnull().sum())
        parse_fail_pct = round(parse_fails / n_rows * 100, 2)
        details["type_checks"][col] = {
            "parseable": parse_fails == 0,
            "parse_fail_count": parse_fails,
            "parse_fail_pct": parse_fail_pct,
        }
        if parse_fails == 0:
            checks_passed += 1
        else:
            issues.append(
                f"DateTime column '{col}': {parse_fails} values ({parse_fail_pct}%) could not be parsed"
            )

    # 4. Required ID columns not null
    for col in required_ids:
        if col not in df.columns:
            continue
        total_checks += 1
        null_count = int(df[col].isnull().sum())
        if null_count == 0:
            checks_passed += 1
        else:
            issues.append(
                f"Required ID column '{col}' has {null_count} null values"
            )

    score = (checks_passed / total_checks * 100) if total_checks > 0 else 100.0

    return {
        "score": round(score, 2),
        "details": details,
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

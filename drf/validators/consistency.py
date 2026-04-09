"""
Pillar 4 — Consistency (Weight: 15%)
Cross-field logic: date ordering, derived field integrity, referential checks.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
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
    rules = config.get("consistency_rules", [])
    n_rows = len(df)

    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    issues = []
    checks_passed = 0
    total_checks = 0
    details: dict[str, Any] = {}

    # Run configured rules
    for rule in rules:
        name = rule.get("name", "unnamed")
        result = _run_rule(df, rule, n_rows)
        total_checks += 1
        details[name] = result
        if result.get("passed"):
            checks_passed += 1
        else:
            issues.append(result.get("issue", f"Rule '{name}' failed"))

    # Additional built-in consistency checks
    extra_results = _builtin_checks(df, n_rows)
    for name, result in extra_results.items():
        total_checks += 1
        details[name] = result
        if result.get("passed"):
            checks_passed += 1
        else:
            issues.append(result.get("issue", f"Check '{name}' failed"))

    score = (checks_passed / total_checks * 100) if total_checks > 0 else 100.0

    return {
        "score": round(score, 2),
        "details": details,
        "issues": issues,
        "passed_checks": checks_passed,
        "total_checks": total_checks,
    }


def _run_rule(df: pd.DataFrame, rule: dict, n_rows: int) -> dict[str, Any]:
    """Execute a single cross-field consistency rule."""
    name = rule.get("name", "")
    left_col = rule.get("left_column")
    right_col = rule.get("right_column")

    # Date ordering rule
    if rule.get("operator") == ">=" and left_col and right_col:
        if left_col not in df.columns or right_col not in df.columns:
            return {"passed": True, "skipped": True, "reason": "Columns not in dataset"}
        left = pd.to_datetime(df[left_col], errors="coerce")
        right = pd.to_datetime(df[right_col], errors="coerce")
        both_valid = left.notna() & right.notna()
        violations = int((left[both_valid] < right[both_valid]).sum())
        violation_pct = round(violations / n_rows * 100, 2)
        passed = violations == 0
        return {
            "passed": passed,
            "violations": violations,
            "violation_pct": violation_pct,
            "description": rule.get("description", ""),
            "issue": (
                f"Rule '{name}': {violations} rows ({violation_pct}%) violate "
                f"'{left_col}' >= '{right_col}'"
            ) if not passed else None,
        }

    # Late delivery risk vs delivery status
    if name == "late_delivery_risk_vs_status":
        risk_col = rule.get("risk_column")
        status_col = rule.get("status_column")
        risk_value = rule.get("risk_value", 1)
        expected_status = rule.get("expected_status", "Late delivery")
        if not (risk_col in df.columns and status_col in df.columns):
            return {"passed": True, "skipped": True, "reason": "Columns not in dataset"}
        risk_mask = df[risk_col] == risk_value
        status_matches = df.loc[risk_mask, status_col].str.strip() == expected_status
        match_rate = round(status_matches.mean() * 100, 2) if risk_mask.sum() > 0 else 100.0
        inconsistencies = int((~status_matches).sum())
        passed = inconsistencies == 0
        return {
            "passed": passed,
            "risk_value_rows": int(risk_mask.sum()),
            "inconsistencies": inconsistencies,
            "consistency_rate_pct": match_rate,
            "description": rule.get("description", ""),
            "issue": (
                f"Rule '{name}': {inconsistencies} rows have {risk_col}={risk_value} "
                f"but '{status_col}' != '{expected_status}'"
            ) if not passed else None,
        }

    return {"passed": True, "skipped": True, "reason": f"Rule '{name}' not implemented"}


def _builtin_checks(df: pd.DataFrame, n_rows: int) -> dict[str, Any]:
    """Built-in consistency checks that don't require config."""
    results: dict[str, Any] = {}

    # Check: Sales > 0 when Order Item Quantity > 0
    sales_col = next((c for c in df.columns if "sales" in c.lower()), None)
    qty_col = next((c for c in df.columns if "quantity" in c.lower()), None)
    if sales_col and qty_col:
        try:
            sales = pd.to_numeric(df[sales_col], errors="coerce")
            qty = pd.to_numeric(df[qty_col], errors="coerce")
            both_valid = sales.notna() & qty.notna()
            violations = int(((qty[both_valid] > 0) & (sales[both_valid] <= 0)).sum())
            violation_pct = round(violations / n_rows * 100, 2)
            results["sales_qty_consistency"] = {
                "passed": violations == 0,
                "violations": violations,
                "violation_pct": violation_pct,
                "description": "Sales should be > 0 when quantity > 0",
                "issue": (
                    f"Check 'sales_qty_consistency': {violations} rows ({violation_pct}%) "
                    f"have quantity > 0 but sales <= 0"
                ) if violations > 0 else None,
            }
        except Exception as e:
            logger.debug("sales_qty check skipped: %s", e)

    # Check: Discount Rate between 0 and 1 (when present)
    disc_col = next(
        (c for c in df.columns if "discount rate" in c.lower() or "discountrate" in c.lower()),
        None,
    )
    if disc_col:
        try:
            disc = pd.to_numeric(df[disc_col], errors="coerce").dropna()
            violations = int(((disc < 0) | (disc > 1)).sum())
            violation_pct = round(violations / n_rows * 100, 2)
            results["discount_rate_range"] = {
                "passed": violations == 0,
                "violations": violations,
                "violation_pct": violation_pct,
                "description": "Discount rate must be 0-1",
                "issue": (
                    f"Check 'discount_rate_range': {violations} rows ({violation_pct}%) "
                    f"have discount rate outside [0, 1]"
                ) if violations > 0 else None,
            }
        except Exception as e:
            logger.debug("discount_rate check skipped: %s", e)

    return results


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "score": 0.0,
        "details": {"reason": reason},
        "issues": [reason],
        "passed_checks": 0,
        "total_checks": 1,
    }

"""
Pillar 7 — AI Readiness (Weight: 15%)
ML-specific checks: feature correlation, class balance, data leakage,
zero-variance columns, skewness, and feature sufficiency.
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
    cfg = config.get("pillars", {}).get("ai_readiness", {})
    thresholds = cfg.get("thresholds", {})
    max_corr = thresholds.get("max_correlation", 0.95)
    min_class_ratio = thresholds.get("min_class_ratio", 0.15)
    max_skewness = thresholds.get("max_skewness", 10.0)

    ai_cfg = config.get("ai_readiness", {})
    target_col = ai_cfg.get("target_column")
    id_cols = set(ai_cfg.get("id_columns", []))
    leakage_cols = ai_cfg.get("leakage_risk_columns", [])

    n_rows = len(df)
    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    issues = []
    checks_passed = 0
    total_checks = 0
    details: dict[str, Any] = {}

    num_df = df.select_dtypes(include=[np.number])
    # Exclude ID columns and target from feature analysis
    feature_cols = [c for c in num_df.columns if c not in id_cols and c != target_col]
    feature_df = num_df[feature_cols]

    # 1. Feature sufficiency
    total_checks += 1
    details["feature_count"] = len(feature_cols)
    if len(feature_cols) >= 5:
        checks_passed += 1
    else:
        issues.append(
            f"Only {len(feature_cols)} numeric feature columns available for ML (minimum: 5)"
        )

    # 2. Zero-variance columns
    total_checks += 1
    zero_var_cols = [c for c in feature_cols if feature_df[c].std() == 0]
    details["zero_variance_columns"] = zero_var_cols
    if not zero_var_cols:
        checks_passed += 1
    else:
        issues.append(
            f"{len(zero_var_cols)} zero-variance columns (useless for ML): {zero_var_cols}"
        )

    # 3. High correlation pairs (multicollinearity)
    total_checks += 1
    high_corr_pairs = []
    if len(feature_cols) >= 2:
        corr = feature_df.corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        high_corr = [
            (col, row, round(float(upper.loc[row, col]), 3))
            for col in upper.columns
            for row in upper.index
            if pd.notna(upper.loc[row, col]) and upper.loc[row, col] >= max_corr
        ]
        high_corr_pairs = high_corr
    details["high_correlation_pairs"] = high_corr_pairs[:10]  # cap at 10 for display
    if not high_corr_pairs:
        checks_passed += 1
    else:
        issues.append(
            f"{len(high_corr_pairs)} feature pairs with correlation ≥ {max_corr} "
            f"(multicollinearity risk). Top: {high_corr_pairs[:3]}"
        )

    # 4. Extreme skewness
    total_checks += 1
    skewed_cols = {}
    for col in feature_cols:
        s = feature_df[col].dropna()
        if len(s) < 10:
            continue
        skew_val = float(s.skew())
        if abs(skew_val) > max_skewness:
            skewed_cols[col] = round(skew_val, 2)
    details["highly_skewed_columns"] = skewed_cols
    if not skewed_cols:
        checks_passed += 1
    else:
        issues.append(
            f"{len(skewed_cols)} column(s) with extreme skewness (>{max_skewness}): "
            f"{list(skewed_cols.keys())[:5]} — recommend log/power transform"
        )

    # 5. Data leakage risk
    total_checks += 1
    present_leakage = [c for c in leakage_cols if c in df.columns]
    details["leakage_risk_columns"] = present_leakage
    if not present_leakage:
        checks_passed += 1
    else:
        issues.append(
            f"Potential data leakage: columns {present_leakage} may directly encode the target. "
            f"Review before training."
        )

    # 6. Class balance (if target column exists)
    if target_col and target_col in df.columns:
        total_checks += 1
        target_series = df[target_col].dropna()
        class_counts = target_series.value_counts()
        n_classes = len(class_counts)
        if n_classes >= 2:
            minority_ratio = round(float(class_counts.min() / class_counts.sum()), 4)
            details["class_balance"] = {
                "target_column": target_col,
                "class_counts": class_counts.to_dict(),
                "minority_class_ratio": minority_ratio,
            }
            if minority_ratio >= min_class_ratio:
                checks_passed += 1
            else:
                issues.append(
                    f"Target '{target_col}' is imbalanced — minority class ratio: "
                    f"{minority_ratio:.1%} (threshold: {min_class_ratio:.1%}). "
                    f"Consider SMOTE or class weighting."
                )
        else:
            details["class_balance"] = {
                "target_column": target_col,
                "note": "Only one class present — target may be a regression variable",
            }
            checks_passed += 1

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

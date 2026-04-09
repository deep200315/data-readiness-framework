"""
Pillar 6 — Accuracy (Weight: 15%)
Statistical outlier detection using Z-score and Isolation Forest.
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
    cfg = config.get("pillars", {}).get("accuracy", {})
    thresholds = cfg.get("thresholds", {})
    zscore_threshold = thresholds.get("zscore_threshold", 3.0)
    isolation_contamination = thresholds.get("isolation_contamination", 0.05)

    n_rows = len(df)
    if n_rows == 0:
        return _empty_result("Dataset has no rows")

    num_df = df.select_dtypes(include=[np.number])
    if num_df.empty:
        return {
            "score": 100.0,
            "details": {"message": "No numeric columns found"},
            "issues": [],
            "passed_checks": 1,
            "total_checks": 1,
        }

    issues = []
    checks_passed = 0
    total_checks = 0
    details: dict[str, Any] = {"column_outliers": {}, "isolation_forest": {}}

    # 1. Z-score outlier detection per column
    total_outlier_flags = 0
    for col in num_df.columns:
        total_checks += 1
        series = num_df[col].dropna()
        if len(series) < 10 or series.std() == 0:
            checks_passed += 1  # skip degenerate columns
            details["column_outliers"][col] = {"skipped": True}
            continue

        mean, std = series.mean(), series.std()
        z_scores = (series - mean) / std
        outliers = int((z_scores.abs() > zscore_threshold).sum())
        outlier_pct = round(outliers / n_rows * 100, 2)
        total_outlier_flags += outliers

        details["column_outliers"][col] = {
            "outlier_count": outliers,
            "outlier_pct": outlier_pct,
            "mean": round(float(mean), 4),
            "std": round(float(std), 4),
            "zscore_threshold": zscore_threshold,
        }

        if outlier_pct <= 5.0:
            checks_passed += 1
        else:
            issues.append(
                f"Column '{col}': {outliers} outliers ({outlier_pct}%) detected via Z-score"
            )

    # 2. Isolation Forest multi-column outlier detection
    total_checks += 1
    iso_result = _run_isolation_forest(num_df, contamination=isolation_contamination)
    details["isolation_forest"] = iso_result
    if iso_result.get("outlier_pct", 0) <= isolation_contamination * 100 * 1.5:
        checks_passed += 1
    else:
        issues.append(
            f"Isolation Forest: {iso_result.get('outlier_count', 0)} multi-variate outliers "
            f"({iso_result.get('outlier_pct', 0)}%) detected"
        )

    # Score: based on overall outlier fraction
    total_flags_pct = round(total_outlier_flags / (n_rows * len(num_df.columns)) * 100, 2)
    score = max(0.0, 100.0 - (total_flags_pct * 5))  # 1% outlier rate = 5 pt penalty

    return {
        "score": round(score, 2),
        "details": details,
        "issues": issues,
        "passed_checks": checks_passed,
        "total_checks": total_checks,
    }


def _run_isolation_forest(num_df: pd.DataFrame, contamination: float) -> dict[str, Any]:
    """Run sklearn Isolation Forest on all numeric columns."""
    try:
        from sklearn.ensemble import IsolationForest  # type: ignore

        clean = num_df.dropna()
        if len(clean) < 50 or len(clean.columns) < 2:
            return {"skipped": True, "reason": "Insufficient data for Isolation Forest"}

        # Sample for large datasets to keep runtime acceptable
        sample_size = min(50_000, len(clean))
        sample = clean.sample(n=sample_size, random_state=42) if len(clean) > sample_size else clean

        clf = IsolationForest(contamination=contamination, random_state=42, n_jobs=-1)
        preds = clf.fit_predict(sample)
        outlier_count = int((preds == -1).sum())
        outlier_pct = round(outlier_count / len(sample) * 100, 2)

        return {
            "outlier_count": outlier_count,
            "outlier_pct": outlier_pct,
            "sample_size": len(sample),
            "contamination": contamination,
        }
    except ImportError:
        logger.warning("scikit-learn not installed. Skipping Isolation Forest.")
        return {"skipped": True, "reason": "scikit-learn not installed"}
    except Exception as exc:
        logger.warning("Isolation Forest failed: %s", exc)
        return {"skipped": True, "reason": str(exc)}


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "score": 0.0,
        "details": {"reason": reason},
        "issues": [reason],
        "passed_checks": 0,
        "total_checks": 1,
    }

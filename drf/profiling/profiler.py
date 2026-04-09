"""
Profiling Layer — wraps ydata-profiling (or falls back to a lightweight
built-in profiler if ydata-profiling is not installed) to generate
automated EDA stats used by the scoring engine and dashboard.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def run_profile(
    df: pd.DataFrame,
    title: str = "Data Readiness Profile",
    minimal: bool = True,
) -> dict[str, Any]:
    """
    Run profiling on the DataFrame and return a structured stats dict.
    Also attempts to generate an HTML report via ydata-profiling.

    Args:
        df: Input DataFrame.
        title: Report title.
        minimal: If True, runs faster minimal mode (skips expensive correlations).

    Returns:
        profile_stats dict with keys used by scoring engine and dashboard.
    """
    stats = _compute_builtin_stats(df)
    stats["html_report"] = _try_ydata_profile(df, title=title, minimal=minimal)
    return stats


def _compute_builtin_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Fast built-in profiler using pandas — always available."""
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols

    # Per-column stats
    col_stats: dict[str, dict] = {}
    for col in df.columns:
        s = df[col]
        null_count = int(s.isnull().sum())
        unique_count = int(s.nunique(dropna=True))
        col_info: dict[str, Any] = {
            "null_count": null_count,
            "null_pct": round(null_count / n_rows * 100, 2) if n_rows else 0.0,
            "unique_count": unique_count,
            "cardinality_ratio": round(unique_count / n_rows, 4) if n_rows else 0.0,
        }
        if pd.api.types.is_numeric_dtype(s):
            col_info.update(
                {
                    "mean": _safe_float(s.mean()),
                    "std": _safe_float(s.std()),
                    "min": _safe_float(s.min()),
                    "max": _safe_float(s.max()),
                    "median": _safe_float(s.median()),
                    "skewness": _safe_float(s.skew()),
                    "kurtosis": _safe_float(s.kurtosis()),
                    "zeros_count": int((s == 0).sum()),
                    "zeros_pct": round((s == 0).sum() / n_rows * 100, 2) if n_rows else 0.0,
                }
            )
        else:
            top_values = s.value_counts().head(5).to_dict()
            col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}
        col_stats[col] = col_info

    # Duplicate analysis
    dup_count = int(df.duplicated().sum())

    # Numeric correlation matrix (compact)
    num_df = df.select_dtypes(include=[np.number])
    corr_matrix: dict = {}
    if len(num_df.columns) >= 2:
        corr = num_df.corr().round(4)
        corr_matrix = corr.to_dict()

    # Missing value map per column (sorted descending)
    missing_map = (
        df.isnull().sum()
        .sort_values(ascending=False)
        .apply(lambda x: round(x / n_rows * 100, 2))
        .to_dict()
    )

    return {
        "row_count": n_rows,
        "column_count": n_cols,
        "total_cells": total_cells,
        "total_missing_cells": int(df.isnull().sum().sum()),
        "overall_missing_pct": round(df.isnull().sum().sum() / total_cells * 100, 2) if total_cells else 0.0,
        "duplicate_rows": dup_count,
        "duplicate_pct": round(dup_count / n_rows * 100, 2) if n_rows else 0.0,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        "columns": col_stats,
        "missing_map": missing_map,
        "correlation_matrix": corr_matrix,
        "numeric_col_count": len(df.select_dtypes(include=[np.number]).columns),
        "categorical_col_count": len(df.select_dtypes(include=["object", "category"]).columns),
        "datetime_col_count": len(df.select_dtypes(include=["datetime64"]).columns),
    }


def _try_ydata_profile(
    df: pd.DataFrame,
    title: str,
    minimal: bool,
) -> Optional[str]:
    """Try to generate ydata-profiling HTML report. Returns HTML string or None."""
    try:
        from ydata_profiling import ProfileReport  # type: ignore

        logger.info("Generating ydata-profiling report (minimal=%s)…", minimal)
        profile = ProfileReport(df, title=title, minimal=minimal, progress_bar=False)
        return profile.to_html()
    except ImportError:
        logger.warning(
            "ydata-profiling not installed. Install with: pip install ydata-profiling"
        )
        return None
    except Exception as exc:
        logger.warning("ydata-profiling failed: %s", exc)
        return None


def _safe_float(val: Any) -> Optional[float]:
    """Convert to float, return None for NaN/Inf."""
    try:
        f = float(val)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 4)
    except (TypeError, ValueError):
        return None

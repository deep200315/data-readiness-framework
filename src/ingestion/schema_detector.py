"""
Schema Detector — auto-classifies DataFrame columns by semantic type.
Returns a structured schema dict used by all validators.
"""
from __future__ import annotations

import logging
import re
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Heuristic patterns for column name classification
_DATE_PATTERNS = re.compile(
    r"(date|time|timestamp|created|updated|shipped|order_date|ship)",
    re.IGNORECASE,
)
_ID_PATTERNS = re.compile(r"(\bid\b|_id$|^id_)", re.IGNORECASE)
_EMAIL_PATTERNS = re.compile(r"email", re.IGNORECASE)
_PHONE_PATTERNS = re.compile(r"phone|mobile|tel", re.IGNORECASE)


def detect_schema(df: pd.DataFrame) -> dict[str, Any]:
    """
    Classify each column and return a schema descriptor.

    Returns:
        {
          "columns": {
            "col_name": {
              "dtype": "numeric" | "categorical" | "datetime" | "boolean" | "text" | "id",
              "pandas_dtype": str,
              "null_count": int,
              "null_pct": float,
              "unique_count": int,
              "cardinality_ratio": float,
              "sample_values": list,
            }
          },
          "numeric_cols": [...],
          "categorical_cols": [...],
          "datetime_cols": [...],
          "boolean_cols": [...],
          "text_cols": [...],
          "id_cols": [...],
        }
    """
    schema: dict[str, Any] = {"columns": {}}
    numeric_cols, categorical_cols, datetime_cols = [], [], []
    boolean_cols, text_cols, id_cols = [], [], []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        null_pct = round(null_count / len(df) * 100, 2) if len(df) > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        cardinality_ratio = round(unique_count / len(df), 4) if len(df) > 0 else 0.0
        sample_values = series.dropna().head(3).tolist()

        col_type = _classify_column(col, series, unique_count, cardinality_ratio)

        schema["columns"][col] = {
            "dtype": col_type,
            "pandas_dtype": str(series.dtype),
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
            "cardinality_ratio": cardinality_ratio,
            "sample_values": sample_values,
        }

        if col_type == "numeric":
            numeric_cols.append(col)
        elif col_type == "categorical":
            categorical_cols.append(col)
        elif col_type == "datetime":
            datetime_cols.append(col)
        elif col_type == "boolean":
            boolean_cols.append(col)
        elif col_type == "text":
            text_cols.append(col)
        elif col_type == "id":
            id_cols.append(col)

    schema["numeric_cols"] = numeric_cols
    schema["categorical_cols"] = categorical_cols
    schema["datetime_cols"] = datetime_cols
    schema["boolean_cols"] = boolean_cols
    schema["text_cols"] = text_cols
    schema["id_cols"] = id_cols

    logger.info(
        "Schema detected — numeric=%d, categorical=%d, datetime=%d, id=%d, text=%d",
        len(numeric_cols),
        len(categorical_cols),
        len(datetime_cols),
        len(id_cols),
        len(text_cols),
    )
    return schema


def _classify_column(
    col: str,
    series: pd.Series,
    unique_count: int,
    cardinality_ratio: float,
) -> str:
    """Heuristic column type classifier."""
    col_lower = col.lower()

    # Try datetime first by name pattern
    if _DATE_PATTERNS.search(col_lower):
        if _try_parse_datetime(series):
            return "datetime"

    # Pandas already detected datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Boolean
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if unique_count <= 2 and set(series.dropna().unique()).issubset({0, 1, True, False}):
        return "boolean"

    # Numeric
    if pd.api.types.is_numeric_dtype(series):
        # Could be an ID field stored as number
        if _ID_PATTERNS.search(col_lower) and cardinality_ratio > 0.8:
            return "id"
        return "numeric"

    # Object dtype — distinguish categorical vs text vs id
    if pd.api.types.is_object_dtype(series):
        if _ID_PATTERNS.search(col_lower) and cardinality_ratio > 0.8:
            return "id"
        if _EMAIL_PATTERNS.search(col_lower) or _PHONE_PATTERNS.search(col_lower):
            return "text"
        # Try to parse as datetime
        if _try_parse_datetime(series):
            return "datetime"
        # High cardinality object → free text
        if cardinality_ratio > 0.5 and unique_count > 100:
            return "text"
        # Low/medium cardinality → categorical
        return "categorical"

    return "categorical"


def _try_parse_datetime(series: pd.Series, sample_size: int = 50) -> bool:
    """Try parsing a sample of values as datetime."""
    sample = series.dropna().head(sample_size)
    if len(sample) == 0:
        return False
    try:
        parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
        success_rate = parsed.notna().mean()
        return success_rate >= 0.8
    except Exception:
        return False

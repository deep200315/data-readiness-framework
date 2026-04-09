"""
Data Ingestion Layer — loads CSV, Excel, or in-memory DataFrames.
Handles encoding detection and basic pre-processing.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet", ".json"}


def load_file(
    source: Union[str, Path, io.BytesIO],
    file_name: Optional[str] = None,
    encoding: str = "latin-1",
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load a dataset from a file path or in-memory buffer (Streamlit upload).

    Args:
        source: File path, Path object, or BytesIO buffer.
        file_name: Required when source is BytesIO to infer file type.
        encoding: Text encoding (latin-1 handles DataCo's special chars).
        nrows: Optionally limit rows for large files during preview.

    Returns:
        Raw pandas DataFrame.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        ext = path.suffix.lower()
        file_name = path.name
    elif isinstance(source, io.BytesIO):
        if file_name is None:
            raise ValueError("file_name must be provided when source is BytesIO")
        ext = Path(file_name).suffix.lower()
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {SUPPORTED_EXTENSIONS}"
        )

    logger.info("Loading dataset: %s (format=%s)", file_name, ext)

    if ext == ".csv":
        df = _load_csv(source, encoding=encoding, nrows=nrows)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(source, nrows=nrows)
    elif ext == ".parquet":
        df = pd.read_parquet(source)
    elif ext == ".json":
        df = pd.read_json(source)
    else:
        raise ValueError(f"Handler missing for extension: {ext}")

    logger.info(
        "Loaded %d rows × %d columns from %s", len(df), len(df.columns), file_name
    )
    return df


def _load_csv(
    source: Union[str, Path, io.BytesIO],
    encoding: str = "latin-1",
    nrows: Optional[int] = None,
) -> pd.DataFrame:
    """Try common encodings for CSV loading."""
    encodings = [encoding, "utf-8", "utf-8-sig", "cp1252"]
    last_error = None
    for enc in encodings:
        try:
            if isinstance(source, io.BytesIO):
                source.seek(0)
            return pd.read_csv(source, encoding=enc, nrows=nrows, low_memory=False)
        except (UnicodeDecodeError, Exception) as e:
            last_error = e
            if isinstance(source, io.BytesIO):
                source.seek(0)
    raise ValueError(f"Could not parse CSV with any encoding. Last error: {last_error}")


def get_dataset_summary(df: pd.DataFrame) -> dict:
    """Return a quick summary dict of the loaded dataset."""
    return {
        "row_count": len(df),
        "column_count": len(df.columns),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        "duplicate_row_count": int(df.duplicated().sum()),
        "total_missing_cells": int(df.isnull().sum().sum()),
        "missing_cell_pct": round(
            df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2
        ),
        "columns": list(df.columns),
    }

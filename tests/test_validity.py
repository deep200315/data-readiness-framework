"""Tests for Pillar 2 — Validity validator."""
import pandas as pd
import pytest
from drf.validators.validity import check

BASE_CONFIG = {
    "columns": {
        "numeric_ranges": [
            {"column": "quantity", "min": 1, "max": 100},
            {"column": "discount_rate", "min": 0.0, "max": 1.0},
        ],
        "categorical_enums": [
            {"column": "status", "allowed_values": ["Active", "Inactive"]},
        ],
        "datetime_columns": ["order_date"],
        "required_id_columns": ["order_id"],
    }
}


def test_all_valid_scores_100():
    df = pd.DataFrame({
        "quantity": [1, 50, 100],
        "discount_rate": [0.0, 0.5, 1.0],
        "status": ["Active", "Inactive", "Active"],
        "order_date": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "order_id": [1, 2, 3],
    })
    result = check(df, BASE_CONFIG)
    assert result["score"] == 100.0
    assert result["issues"] == []


def test_out_of_range_values_flagged():
    df = pd.DataFrame({
        "quantity": [-1, 50, 9999],  # -1 and 9999 are out of range
        "discount_rate": [0.5, 0.5, 0.5],
        "status": ["Active", "Active", "Active"],
        "order_date": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "order_id": [1, 2, 3],
    })
    result = check(df, BASE_CONFIG)
    assert result["score"] < 100
    assert any("quantity" in issue for issue in result["issues"])


def test_invalid_enum_values_flagged():
    df = pd.DataFrame({
        "quantity": [1, 2, 3],
        "discount_rate": [0.1, 0.2, 0.3],
        "status": ["Active", "Unknown", "BadValue"],  # 2 invalid
        "order_date": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "order_id": [1, 2, 3],
    })
    result = check(df, BASE_CONFIG)
    assert result["score"] < 100
    assert any("status" in issue for issue in result["issues"])


def test_null_required_id_flagged():
    df = pd.DataFrame({
        "quantity": [1, 2, 3],
        "discount_rate": [0.1, 0.2, 0.3],
        "status": ["Active", "Active", "Active"],
        "order_date": ["2023-01-01", "2023-02-01", "2023-03-01"],
        "order_id": [1, None, 3],
    })
    result = check(df, BASE_CONFIG)
    assert any("order_id" in issue for issue in result["issues"])


def test_missing_columns_skipped_gracefully():
    """Columns not in DataFrame should be silently skipped."""
    df = pd.DataFrame({"unrelated_col": [1, 2, 3]})
    result = check(df, BASE_CONFIG)
    # Should not raise, score should be 100 (no applicable checks)
    assert result["score"] == 100.0

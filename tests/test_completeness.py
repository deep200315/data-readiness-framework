"""Tests for Pillar 1 — Completeness validator."""
import pandas as pd
import pytest
from drf.validators.completeness import check

BASE_CONFIG = {
    "pillars": {
        "completeness": {
            "thresholds": {"critical_null_pct": 50.0, "warning_null_pct": 20.0}
        }
    },
    "columns": {"known_sparse_columns": []},
}


def make_df(**cols):
    return pd.DataFrame(cols)


def test_perfect_data_scores_100():
    df = make_df(a=[1, 2, 3], b=["x", "y", "z"])
    result = check(df, BASE_CONFIG)
    assert result["score"] == 100.0
    assert result["issues"] == []


def test_all_nulls_scores_near_zero():
    df = make_df(a=[None, None, None], b=[None, None, None])
    result = check(df, BASE_CONFIG)
    assert result["score"] < 10


def test_partial_nulls_penalised():
    df = make_df(a=[1, None, 3, None, 5])
    result = check(df, BASE_CONFIG)
    # 40% null in column 'a' → warning
    assert 0 < result["score"] < 100
    assert len(result["issues"]) > 0


def test_known_sparse_columns_not_penalised():
    config = {
        **BASE_CONFIG,
        "columns": {"known_sparse_columns": ["sparse_col"]},
    }
    df = make_df(sparse_col=[None, None, None], good_col=[1, 2, 3])
    result = check(df, config)
    # sparse_col should be ignored; good_col is fine
    assert result["score"] > 80


def test_empty_dataframe():
    df = pd.DataFrame()
    result = check(df, BASE_CONFIG)
    assert result["score"] == 0.0
    assert "no rows" in result["issues"][0].lower()


def test_bad_row_penalty():
    # Row with >50% missing triggers bad-row penalty
    df = pd.DataFrame({
        "a": [1, None, 3],
        "b": [None, None, 4],
        "c": [None, None, 5],
        "d": [None, None, 6],
    })
    result = check(df, BASE_CONFIG)
    assert result["details"]["bad_row_count"] >= 1

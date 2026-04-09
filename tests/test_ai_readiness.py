"""Tests for Pillar 7 — AI Readiness validator."""
import numpy as np
import pandas as pd
import pytest
from src.validators.ai_readiness import check

BASE_CONFIG = {
    "pillars": {
        "ai_readiness": {
            "thresholds": {
                "max_correlation": 0.95,
                "min_class_ratio": 0.15,
                "max_skewness": 10.0,
            }
        }
    },
    "ai_readiness": {
        "target_column": "target",
        "id_columns": ["id"],
        "leakage_risk_columns": ["leaky_col"],
        "text_columns": [],
    },
}


def make_df(n=300):
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "id": range(n),
        "feature1": rng.normal(0, 1, n),
        "feature2": rng.normal(5, 2, n),
        "feature3": rng.uniform(0, 100, n),
        "feature4": rng.integers(1, 50, n),
        "feature5": rng.normal(10, 3, n),
        "target": rng.choice([0, 1], n, p=[0.6, 0.4]),
    })


def test_clean_features_score_high():
    df = make_df()
    result = check(df, BASE_CONFIG)
    assert result["score"] >= 70


def test_leakage_column_flagged():
    df = make_df()
    df["leaky_col"] = df["target"]  # direct encode of target
    result = check(df, BASE_CONFIG)
    assert any("leakage" in issue.lower() or "leaky_col" in issue for issue in result["issues"])


def test_class_imbalance_flagged():
    rng = np.random.default_rng(0)
    n = 300
    df = pd.DataFrame({
        "id": range(n),
        "feature1": rng.normal(0, 1, n),
        "feature2": rng.normal(5, 2, n),
        "feature3": rng.uniform(0, 100, n),
        "feature4": rng.integers(1, 50, n),
        "feature5": rng.normal(10, 3, n),
        "target": rng.choice([0, 1], n, p=[0.95, 0.05]),  # 95/5 split
    })
    result = check(df, BASE_CONFIG)
    assert any("imbalance" in issue.lower() or "imbalanced" in issue.lower() for issue in result["issues"])


def test_high_correlation_flagged():
    rng = np.random.default_rng(42)
    n = 300
    x = rng.normal(0, 1, n)
    df = pd.DataFrame({
        "id": range(n),
        "feature1": x,
        "feature2": x * 1.001,  # near-perfect correlation
        "feature3": rng.normal(5, 2, n),
        "feature4": rng.uniform(0, 1, n),
        "feature5": rng.integers(1, 50, n),
        "target": rng.choice([0, 1], n),
    })
    result = check(df, BASE_CONFIG)
    assert any("correlation" in issue.lower() or "multicollinearity" in issue.lower()
               for issue in result["issues"])


def test_zero_variance_column_flagged():
    df = make_df()
    df["constant_col"] = 42  # zero variance
    result = check(df, BASE_CONFIG)
    assert any("zero" in issue.lower() or "variance" in issue.lower()
               for issue in result["issues"])


def test_empty_dataframe():
    df = pd.DataFrame()
    result = check(df, BASE_CONFIG)
    assert result["score"] == 0.0

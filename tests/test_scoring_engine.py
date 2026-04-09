"""Tests for the Scoring Engine."""
import pandas as pd
import pytest
from src.scoring.engine import ScoreResult, _determine_band


# Minimal configs for testing
SCORING_CONFIG = {
    "pillars": {
        "completeness": {"weight": 0.20, "thresholds": {"critical_null_pct": 50.0, "warning_null_pct": 20.0}},
        "validity": {"weight": 0.15},
        "uniqueness": {"weight": 0.10, "thresholds": {"max_duplicate_pct": 5.0}},
        "consistency": {"weight": 0.15},
        "timeliness": {"weight": 0.10, "thresholds": {"max_gap_days": 90}},
        "accuracy": {"weight": 0.15, "thresholds": {"zscore_threshold": 3.0, "isolation_contamination": 0.05}},
        "ai_readiness": {"weight": 0.15, "thresholds": {"max_correlation": 0.95, "min_class_ratio": 0.15, "max_skewness": 10.0}},
    },
    "bands": {
        "excellent": {"min": 85, "label": "Excellent", "color": "#2ecc71"},
        "good": {"min": 70, "label": "Good", "color": "#f39c12"},
        "at_risk": {"min": 50, "label": "At Risk", "color": "#e67e22"},
        "not_ready": {"min": 0, "label": "Not Ready", "color": "#e74c3c"},
    },
}

VALIDATION_CONFIG = {
    "dataset": {"expected_date_range": {"start": "2000-01-01", "end": "2030-12-31"}},
    "columns": {
        "numeric_ranges": [],
        "categorical_enums": [],
        "datetime_columns": [],
        "required_id_columns": [],
        "known_sparse_columns": [],
    },
    "consistency_rules": [],
    "ai_readiness": {
        "target_column": "target",
        "id_columns": [],
        "leakage_risk_columns": [],
        "text_columns": [],
    },
}


def make_clean_df(n=200):
    """Generate a clean synthetic supply chain DataFrame."""
    import numpy as np
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "order_id": range(n),
        "quantity": rng.integers(1, 50, n),
        "sales": rng.uniform(10, 1000, n),
        "discount_rate": rng.uniform(0, 1, n),
        "category": rng.choice(["A", "B", "C"], n),
        "target": rng.choice([0, 1], n, p=[0.6, 0.4]),
    })


def test_clean_data_scores_high():
    df = make_clean_df()
    from src.scoring.engine import run
    result = run(df, SCORING_CONFIG, VALIDATION_CONFIG)
    assert result.overall_score >= 70, f"Expected >=70, got {result.overall_score}"


def test_all_null_data_scores_low():
    df = pd.DataFrame({
        "a": [None] * 50,
        "b": [None] * 50,
        "c": [None] * 50,
    })
    from src.scoring.engine import run
    result = run(df, SCORING_CONFIG, VALIDATION_CONFIG)
    # Completeness=0, uniqueness=0 pull score down; other pillars
    # score 100 when no applicable checks exist → overall lands in At Risk band
    assert result.overall_score < 75, f"Expected <75, got {result.overall_score}"
    assert result.band in ("at_risk", "not_ready")


def test_band_determination():
    assert _determine_band(90, SCORING_CONFIG)[0] == "excellent"
    assert _determine_band(75, SCORING_CONFIG)[0] == "good"
    assert _determine_band(60, SCORING_CONFIG)[0] == "at_risk"
    assert _determine_band(30, SCORING_CONFIG)[0] == "not_ready"


def test_score_result_has_all_pillars():
    df = make_clean_df()
    from src.scoring.engine import run
    result = run(df, SCORING_CONFIG, VALIDATION_CONFIG)
    expected_pillars = {"completeness", "validity", "uniqueness", "consistency",
                        "timeliness", "accuracy", "ai_readiness"}
    assert set(result.pillars.keys()) == expected_pillars


def test_weighted_sum_correct():
    df = make_clean_df()
    from src.scoring.engine import run
    result = run(df, SCORING_CONFIG, VALIDATION_CONFIG)
    # Verify weighted sum matches overall score
    manual_sum = sum(pr.score * pr.weight for pr in result.pillars.values())
    assert abs(result.overall_score - manual_sum) < 0.1


def test_recommendations_generated():
    df = pd.DataFrame({"a": [None] * 100, "b": [None] * 100})
    from src.scoring.engine import run
    result = run(df, SCORING_CONFIG, VALIDATION_CONFIG)
    assert len(result.recommendations) > 0

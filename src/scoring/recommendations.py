"""
Recommendations Engine — maps low-scoring pillars to prioritized,
actionable remediation steps for data teams.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.scoring.engine import PillarResult


# Threshold below which a pillar is considered "needs attention"
ATTENTION_THRESHOLD = 80.0
CRITICAL_THRESHOLD = 60.0


def generate(
    pillar_results: dict[str, "PillarResult"],
    overall_score: float,
    max_recommendations: int = 10,
) -> list[str]:
    """
    Generate a prioritized list of remediation recommendations.

    Priority order: critical pillars first, then warnings, then general tips.
    """
    recs: list[tuple[int, str]] = []  # (priority, message)

    # Per-pillar rule-based recommendations
    for name, pr in pillar_results.items():
        score = pr.score
        handler = _PILLAR_HANDLERS.get(name)
        if handler:
            pillar_recs = handler(score, pr.details, pr.issues)
            recs.extend(pillar_recs)

    # Sort by priority (lower number = higher priority)
    recs.sort(key=lambda x: x[0])

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_recs: list[str] = []
    for _, msg in recs:
        if msg not in seen:
            seen.add(msg)
            unique_recs.append(msg)

    # General tip if score is high
    if overall_score >= 85:
        unique_recs.append(
            "Data is in excellent shape. Consider setting up automated monitoring "
            "with Evidently AI or Great Expectations CI/CD integration."
        )

    return unique_recs[:max_recommendations]


# ── Pillar-specific handlers ───────────────────────────────────────────────

def _completeness_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []
    if score < CRITICAL_THRESHOLD:
        recs.append((1, "CRITICAL: High missing data detected. "
                     "Drop columns with >80% null values; impute remaining using "
                     "median (numeric) or mode (categorical)."))
    elif score < ATTENTION_THRESHOLD:
        recs.append((2, "Impute missing values: use median/mean for numeric fields, "
                     "mode or 'Unknown' for categoricals."))

    critical_cols = details.get("critical_columns", [])
    if critical_cols:
        recs.append((1, f"Drop or investigate these high-null columns: {critical_cols[:5]}. "
                     "They add noise to ML models."))

    bad_row_pct = details.get("bad_row_pct", 0)
    if bad_row_pct > 10:
        recs.append((2, f"{bad_row_pct}% of rows have >50% missing fields. "
                     "Consider removing these records from training data."))
    return recs


def _validity_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []
    if score < CRITICAL_THRESHOLD:
        recs.append((1, "CRITICAL: Many values fail schema/range validation. "
                     "Enforce data contracts at ingestion time with Great Expectations."))
    elif score < ATTENTION_THRESHOLD:
        recs.append((2, "Apply value range clipping or filtering to remove invalid records "
                     "before model training."))

    enum_checks = details.get("enum_checks", {})
    for col, info in enum_checks.items():
        if info.get("invalid_count", 0) > 0:
            recs.append((3, f"Standardise categorical values in '{col}': "
                         f"found {info['invalid_count']} unexpected values. "
                         f"Map or discard outlier categories."))
    return recs


def _uniqueness_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []
    dup_pct = details.get("duplicate_pct", 0)
    if dup_pct > 10:
        recs.append((1, f"CRITICAL: {dup_pct}% duplicate rows. "
                     "Deduplicate using df.drop_duplicates() before analysis."))
    elif dup_pct > 2:
        recs.append((2, f"{dup_pct}% duplicate rows detected. "
                     "Remove duplicates — they inflate training samples and bias models."))
    return recs


def _consistency_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []
    if score < CRITICAL_THRESHOLD:
        recs.append((1, "CRITICAL: Cross-field logic violations detected. "
                     "Review date ordering and derived field calculations in ETL pipeline."))
    elif score < ATTENTION_THRESHOLD:
        recs.append((2, "Fix inconsistent records: shipping dates before order dates, "
                     "mismatched delivery status/risk flags."))
    return recs


def _timeliness_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []
    if score < ATTENTION_THRESHOLD:
        recs.append((3, "Temporal gaps detected in date columns. "
                     "Check for data pipeline failures during gap periods. "
                     "Consider imputing or flagging gap records for time-series models."))
    return recs


def _accuracy_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []
    if score < CRITICAL_THRESHOLD:
        recs.append((1, "CRITICAL: High outlier rate. Apply IQR capping or "
                     "log-transform heavily skewed numeric features before training."))
    elif score < ATTENTION_THRESHOLD:
        recs.append((2, "Apply outlier treatment: Winsorize (clip to 1st/99th percentile) "
                     "or use robust scalers (RobustScaler) for ML pipelines."))

    col_outliers = details.get("column_outliers", {})
    high_outlier_cols = [
        col for col, info in col_outliers.items()
        if isinstance(info, dict) and info.get("outlier_pct", 0) > 5
    ]
    if high_outlier_cols:
        recs.append((2, f"Columns with >5% outliers: {high_outlier_cols[:5]}. "
                     "Investigate business logic — outliers may be valid edge cases or data errors."))
    return recs


def _ai_readiness_recs(score: float, details: dict, issues: list[str]) -> list[tuple[int, str]]:
    recs = []

    leakage_cols = details.get("leakage_risk_columns", [])
    if leakage_cols:
        recs.append((1, f"CRITICAL DATA LEAKAGE RISK: Remove or isolate columns {leakage_cols} "
                     "before training — they directly encode the target variable."))

    high_corr_pairs = details.get("high_correlation_pairs", [])
    if high_corr_pairs:
        corr_cols = list({col for pair in high_corr_pairs for col in pair[:2]})
        recs.append((2, f"Multicollinearity detected in features: {corr_cols[:6]}. "
                     "Use VIF analysis and drop one from each highly correlated pair, "
                     "or apply PCA for dimensionality reduction."))

    zero_var = details.get("zero_variance_columns", [])
    if zero_var:
        recs.append((2, f"Drop zero-variance columns (no predictive value): {zero_var}"))

    class_balance = details.get("class_balance", {})
    if class_balance.get("minority_class_ratio", 1.0) < 0.15:
        recs.append((2, "Target class imbalance detected. Apply SMOTE, ADASYN, "
                     "or class_weight='balanced' in your ML model."))

    skewed = details.get("highly_skewed_columns", {})
    if skewed:
        recs.append((3, f"Apply log or Box-Cox transform to highly skewed columns: "
                     f"{list(skewed.keys())[:5]}"))

    if details.get("feature_count", 10) < 5:
        recs.append((2, "Very few numeric features available. "
                     "Consider feature engineering from existing columns "
                     "(date components, ratios, interaction terms)."))

    return recs


_PILLAR_HANDLERS = {
    "completeness": _completeness_recs,
    "validity": _validity_recs,
    "uniqueness": _uniqueness_recs,
    "consistency": _consistency_recs,
    "timeliness": _timeliness_recs,
    "accuracy": _accuracy_recs,
    "ai_readiness": _ai_readiness_recs,
}

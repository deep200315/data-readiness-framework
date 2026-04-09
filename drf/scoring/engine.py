"""
Scoring Engine — combines all 7 pillar scores into a single weighted
Data Readiness Score (0–100) and determines the quality band.
"""
from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd
import yaml

from drf.validators import (
    accuracy,
    ai_readiness,
    completeness,
    consistency,
    timeliness,
    uniqueness,
    validity,
)

logger = logging.getLogger(__name__)

PILLAR_ORDER = [
    "completeness",
    "validity",
    "uniqueness",
    "consistency",
    "timeliness",
    "accuracy",
    "ai_readiness",
]


@dataclass
class PillarResult:
    name: str
    score: float
    weight: float
    weighted_score: float
    issues: list[str]
    details: dict[str, Any]
    passed_checks: int
    total_checks: int


@dataclass
class ScoreResult:
    overall_score: float
    band: str
    band_label: str
    band_color: str
    pillars: dict[str, PillarResult]
    all_issues: list[str]
    recommendations: list[str]
    dataset_stats: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


def run(
    df: pd.DataFrame,
    scoring_config: dict,
    validation_config: dict,
    profile_stats: Optional[dict] = None,
) -> ScoreResult:
    """
    Run all 7 pillar validators and compute the overall readiness score.

    Args:
        df: Input DataFrame.
        scoring_config: Contents of scoring_weights.yaml.
        validation_config: Contents of validation_rules.yaml.
        profile_stats: Optional pre-computed profile stats dict.

    Returns:
        ScoreResult with full breakdown.
    """
    # Merge configs so validators can access both
    combined_config = {**scoring_config, **validation_config}

    logger.info("Running Data Readiness scoring on %d rows × %d cols…", len(df), len(df.columns))

    pillar_modules = {
        "completeness": completeness,
        "validity": validity,
        "uniqueness": uniqueness,
        "consistency": consistency,
        "timeliness": timeliness,
        "accuracy": accuracy,
        "ai_readiness": ai_readiness,
    }

    pillar_weights = {
        name: scoring_config.get("pillars", {}).get(name, {}).get("weight", 1 / 7)
        for name in PILLAR_ORDER
    }

    pillar_results: dict[str, PillarResult] = {}
    all_issues: list[str] = []
    weighted_sum = 0.0

    for name in PILLAR_ORDER:
        module = pillar_modules[name]
        weight = pillar_weights[name]
        logger.info("  Checking pillar: %s (weight=%.0f%%)", name, weight * 100)
        try:
            result = module.check(df, combined_config)
        except Exception as exc:
            logger.error("Pillar '%s' failed with error: %s", name, exc)
            result = {
                "score": 0.0,
                "issues": [f"Pillar failed: {exc}"],
                "details": {},
                "passed_checks": 0,
                "total_checks": 1,
            }

        score = float(result.get("score", 0.0))
        issues = result.get("issues", [])
        all_issues.extend(issues)

        pr = PillarResult(
            name=name,
            score=score,
            weight=weight,
            weighted_score=round(score * weight, 4),
            issues=issues,
            details=result.get("details", {}),
            passed_checks=result.get("passed_checks", 0),
            total_checks=result.get("total_checks", 1),
        )
        pillar_results[name] = pr
        weighted_sum += pr.weighted_score

    overall_score = round(weighted_sum, 2)
    band, band_label, band_color = _determine_band(overall_score, scoring_config)

    from drf.scoring.recommendations import generate
    recommendations = generate(pillar_results, overall_score)

    dataset_stats = {
        "row_count": len(df),
        "column_count": len(df.columns),
    }
    if profile_stats:
        dataset_stats.update(
            {
                "duplicate_rows": profile_stats.get("duplicate_rows", 0),
                "duplicate_pct": profile_stats.get("duplicate_pct", 0.0),
                "overall_missing_pct": profile_stats.get("overall_missing_pct", 0.0),
                "memory_mb": profile_stats.get("memory_mb", 0.0),
            }
        )

    logger.info("Overall Data Readiness Score: %.1f / 100 (%s)", overall_score, band)
    return ScoreResult(
        overall_score=overall_score,
        band=band,
        band_label=band_label,
        band_color=band_color,
        pillars=pillar_results,
        all_issues=all_issues,
        recommendations=recommendations,
        dataset_stats=dataset_stats,
    )


def _determine_band(score: float, config: dict) -> tuple[str, str, str]:
    """Return (band_key, band_label, band_color) for the given score."""
    bands = config.get("bands", {})
    for band_key in ["excellent", "good", "at_risk", "not_ready"]:
        band = bands.get(band_key, {})
        if score >= band.get("min", 0):
            return (
                band_key,
                band.get("label", band_key.replace("_", " ").title()),
                band.get("color", "#666666"),
            )
    return "not_ready", "Not Ready", "#e74c3c"


def load_config(path: str) -> dict:
    """Load a YAML config file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

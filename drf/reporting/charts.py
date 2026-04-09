"""
Charts — all Plotly chart generators used in the Streamlit dashboard.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

if TYPE_CHECKING:
    from drf.scoring.engine import ScoreResult

PILLAR_LABELS = {
    "completeness": "Completeness",
    "validity": "Validity",
    "uniqueness": "Uniqueness",
    "consistency": "Consistency",
    "timeliness": "Timeliness",
    "accuracy": "Accuracy",
    "ai_readiness": "AI Readiness",
}


def gauge_chart(score: float, band_color: str, title: str = "Data Readiness Score") -> go.Figure:
    """Large gauge/indicator chart showing overall score."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title, "font": {"size": 20}},
            delta={"reference": 70, "increasing": {"color": "#2ecc71"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#444"},
                "bar": {"color": band_color},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "#ccc",
                "steps": [
                    {"range": [0, 49], "color": "#fde8e8"},
                    {"range": [50, 69], "color": "#fdebd0"},
                    {"range": [70, 84], "color": "#fef9e7"},
                    {"range": [85, 100], "color": "#eafaf1"},
                ],
                "threshold": {
                    "line": {"color": "#e74c3c", "width": 4},
                    "thickness": 0.75,
                    "value": 70,
                },
            },
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def radar_chart(result: "ScoreResult") -> go.Figure:
    """Spider/radar chart of the 7 pillar scores."""
    pillars = list(result.pillars.keys())
    scores = [result.pillars[p].score for p in pillars]
    labels = [PILLAR_LABELS.get(p, p) for p in pillars]

    # Close the radar loop
    labels_loop = labels + [labels[0]]
    scores_loop = scores + [scores[0]]

    fig = go.Figure(
        go.Scatterpolar(
            r=scores_loop,
            theta=labels_loop,
            fill="toself",
            fillcolor="rgba(52, 152, 219, 0.2)",
            line_color="rgba(52, 152, 219, 0.9)",
            name="Score",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont_size=10),
            angularaxis=dict(tickfont_size=12),
        ),
        showlegend=False,
        height=350,
        margin=dict(l=50, r=50, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def pillar_bar_chart(result: "ScoreResult") -> go.Figure:
    """Horizontal bar chart of pillar scores with color coding."""
    pillars = list(result.pillars.keys())
    scores = [result.pillars[p].score for p in pillars]
    labels = [PILLAR_LABELS.get(p, p) for p in pillars]
    weights = [f"{result.pillars[p].weight * 100:.0f}%" for p in pillars]

    colors = []
    for s in scores:
        if s >= 85:
            colors.append("#2ecc71")
        elif s >= 70:
            colors.append("#f39c12")
        elif s >= 50:
            colors.append("#e67e22")
        else:
            colors.append("#e74c3c")

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=[f"{l} ({w})" for l, w in zip(labels, weights)],
            orientation="h",
            marker_color=colors,
            text=[f"{s:.1f}" for s in scores],
            textposition="outside",
        )
    )
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Score (0–100)"),
        yaxis=dict(autorange="reversed"),
        height=320,
        margin=dict(l=160, r=60, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def missing_value_heatmap(profile_stats: dict, top_n: int = 30) -> go.Figure:
    """Bar chart of top-N columns by missing % (heatmap-style)."""
    missing_map = profile_stats.get("missing_map", {})
    if not missing_map:
        return _empty_figure("No missing value data")

    # Filter to columns with any missing
    missing_nonzero = {k: v for k, v in missing_map.items() if v > 0}
    if not missing_nonzero:
        fig = go.Figure()
        fig.add_annotation(
            text="No missing values detected!",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#2ecc71"),
        )
        fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)")
        return fig

    sorted_items = sorted(missing_nonzero.items(), key=lambda x: x[1], reverse=True)[:top_n]
    cols = [item[0] for item in sorted_items]
    pcts = [item[1] for item in sorted_items]

    colors = ["#e74c3c" if p >= 50 else "#e67e22" if p >= 20 else "#f39c12" for p in pcts]

    fig = go.Figure(
        go.Bar(
            x=pcts,
            y=cols,
            orientation="h",
            marker_color=colors,
            text=[f"{p:.1f}%" for p in pcts],
            textposition="outside",
        )
    )
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Missing %"),
        yaxis=dict(autorange="reversed"),
        height=max(250, len(cols) * 22),
        margin=dict(l=220, r=60, t=10, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def correlation_heatmap(profile_stats: dict) -> Optional[go.Figure]:
    """Correlation matrix heatmap for numeric columns."""
    corr_dict = profile_stats.get("correlation_matrix", {})
    if not corr_dict:
        return None
    try:
        corr_df = pd.DataFrame(corr_dict)
        # Limit to 20 columns for readability
        if len(corr_df) > 20:
            corr_df = corr_df.iloc[:20, :20]

        fig = go.Figure(
            go.Heatmap(
                z=corr_df.values,
                x=list(corr_df.columns),
                y=list(corr_df.index),
                colorscale="RdBu_r",
                zmid=0,
                zmin=-1,
                zmax=1,
                text=corr_df.round(2).values,
                texttemplate="%{text}",
                showscale=True,
            )
        )
        fig.update_layout(
            height=max(400, len(corr_df) * 25),
            margin=dict(l=150, r=50, t=20, b=150),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig
    except Exception:
        return None


def score_breakdown_table(result: "ScoreResult") -> pd.DataFrame:
    """Return a styled DataFrame for display in Streamlit."""
    rows = []
    for name, pr in result.pillars.items():
        rows.append(
            {
                "Pillar": PILLAR_LABELS.get(name, name),
                "Weight": f"{pr.weight * 100:.0f}%",
                "Score": f"{pr.score:.1f}",
                "Weighted": f"{pr.weighted_score:.2f}",
                "Checks Passed": f"{pr.passed_checks}/{pr.total_checks}",
                "Status": _status_emoji(pr.score),
            }
        )
    rows.append(
        {
            "Pillar": "**OVERALL**",
            "Weight": "100%",
            "Score": f"{result.overall_score:.1f}",
            "Weighted": f"{result.overall_score:.2f}",
            "Checks Passed": "",
            "Status": _status_emoji(result.overall_score),
        }
    )
    return pd.DataFrame(rows)


def _status_emoji(score: float) -> str:
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "At Risk"
    return "Not Ready"


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14),
    )
    fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)")
    return fig

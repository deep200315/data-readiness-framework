"""
Streamlit Dashboard — main UI for the Data Readiness Framework.
Import and call run_dashboard() from app.py.
"""
from __future__ import annotations

import io
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# Ensure project root is on path when run via `streamlit run app.py`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from drf.ingestion.loader import get_dataset_summary, load_file
from drf.ingestion.schema_detector import detect_schema
from drf.profiling.profiler import run_profile
from drf.reporting import charts
from drf.scoring import engine

logger = logging.getLogger(__name__)

CONFIG_DIR = ROOT / "config"
SCORING_CONFIG_PATH = CONFIG_DIR / "scoring_weights.yaml"
VALIDATION_CONFIG_PATH = CONFIG_DIR / "validation_rules.yaml"


def run_dashboard() -> None:
    st.set_page_config(
        page_title="AI Data Readiness Framework",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_css()

    # ── Sidebar ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/combo-chart.png", width=60)
        st.title("Data Readiness\nFramework")
        st.caption("Powered by 7-Pillar AI Readiness Scoring")
        st.divider()

        uploaded_file = st.file_uploader(
            "Upload your dataset",
            type=["csv", "xlsx", "xls"],
            help="Upload CSV or Excel. DataCo Supply Chain CSV (~27 MB) is the reference dataset.",
        )

        st.divider()
        st.markdown("**Scoring Weights**")
        weight_info = {
            "Completeness": "20%",
            "Validity": "15%",
            "Uniqueness": "10%",
            "Consistency": "15%",
            "Timeliness": "10%",
            "Accuracy": "15%",
            "AI Readiness": "15%",
        }
        for pillar, w in weight_info.items():
            st.caption(f"• {pillar}: {w}")

        st.divider()
        st.caption("7-Pillar AI Data Readiness Assessment")

    # ── Main Content ─────────────────────────────────────────────────────────
    st.title("📊 AI Data Readiness Framework")
    st.markdown(
        "Assess whether your supply chain data is ready for AI/ML model training. "
        "Upload your dataset to get a **Data Readiness Score (0–100)** with actionable insights."
    )

    if uploaded_file is None:
        _landing_page()
        return

    # Load configs
    scoring_config = engine.load_config(str(SCORING_CONFIG_PATH))
    validation_config = engine.load_config(str(VALIDATION_CONFIG_PATH))

    # Load data
    with st.spinner("Loading dataset…"):
        try:
            df = load_file(io.BytesIO(uploaded_file.read()), file_name=uploaded_file.name)
        except Exception as exc:
            st.error(f"Failed to load file: {exc}")
            return

    st.success(
        f"Dataset loaded: **{uploaded_file.name}** — "
        f"{len(df):,} rows × {len(df.columns)} columns"
    )

    # Run profiling
    with st.spinner("Profiling dataset…"):
        profile_stats = run_profile(df, title=f"Profile: {uploaded_file.name}", minimal=True)

    # Run scoring
    with st.spinner("Running Data Readiness assessment (7 pillars)…"):
        result = engine.run(df, scoring_config, validation_config, profile_stats)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_overview, tab_pillars, tab_profile, tab_recommendations, tab_export = st.tabs(
        ["Overview", "Pillar Details", "Data Profile", "Recommendations", "Export Report"]
    )

    with tab_overview:
        _render_overview(result, profile_stats)

    with tab_pillars:
        _render_pillars(result)

    with tab_profile:
        _render_profile(df, profile_stats)

    with tab_recommendations:
        _render_recommendations(result)

    with tab_export:
        _render_export(result, profile_stats, uploaded_file.name)


# ── Tab Renderers ─────────────────────────────────────────────────────────────

def _landing_page() -> None:
    st.info("Upload a CSV or Excel file in the sidebar to begin the assessment.")

    col1, col2, col3, col4 = st.columns(4)
    for col, (label, value) in zip(
        [col1, col2, col3, col4],
        [("Pillars Assessed", "7"), ("Score Range", "0–100"),
         ("Quality Bands", "4"), ("Reference Dataset", "DataCo")],
    ):
        with col:
            st.markdown(
                f"<div style='border:1px solid #444;border-radius:8px;padding:16px;text-align:center;'>"
                f"<div style='font-size:24px;font-weight:700;'>{value}</div>"
                f"<div style='font-size:12px;opacity:0.7;margin-top:4px;'>{label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("How it works")
    steps = [
        ("1. Upload", "Upload your CSV, Excel, or connect a data lake"),
        ("2. Profile", "Auto-profiling generates dataset statistics"),
        ("3. Validate", "7 quality pillars are assessed in parallel"),
        ("4. Score", "Weighted AI Readiness Score (0–100) is computed"),
        ("5. Report", "Download a PDF report with recommendations"),
    ]
    cols = st.columns(len(steps))
    for col, (title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)


def _render_overview(result, profile_stats: dict) -> None:
    # Top KPI row
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        st.plotly_chart(
            charts.gauge_chart(result.overall_score, result.band_color),
            width="stretch",
        )

    with col2:
        st.metric("Band", result.band.replace("_", " ").title())
        st.caption(result.band_label)

    with col3:
        st.metric("Rows", f"{profile_stats.get('row_count', 0):,}")
        st.metric("Columns", f"{profile_stats.get('column_count', 0)}")

    with col4:
        st.metric("Missing %", f"{profile_stats.get('overall_missing_pct', 0):.1f}%")
        st.metric("Duplicates %", f"{profile_stats.get('duplicate_pct', 0):.1f}%")

    with col5:
        issues_count = len(result.all_issues)
        st.metric("Issues Found", issues_count)
        st.metric("Recommendations", len(result.recommendations))

    st.divider()

    # Score breakdown table + radar chart
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("Pillar Scorecard")
        st.dataframe(
            charts.score_breakdown_table(result),
            hide_index=True,
            width="stretch",
        )

    with col_right:
        st.subheader("Radar View")
        st.plotly_chart(charts.radar_chart(result), width="stretch")

    # Pillar bar chart
    st.subheader("Score by Pillar")
    st.plotly_chart(charts.pillar_bar_chart(result), width="stretch")


def _render_pillars(result) -> None:
    st.subheader("Pillar-Level Details")
    for name, pr in result.pillars.items():
        label = charts.PILLAR_LABELS.get(name, name)
        color = "#2ecc71" if pr.score >= 85 else "#f39c12" if pr.score >= 70 else "#e67e22" if pr.score >= 50 else "#e74c3c"

        with st.expander(
            f"{label} — Score: {pr.score:.1f}/100  ({pr.passed_checks}/{pr.total_checks} checks passed)",
            expanded=pr.score < 70,
        ):
            st.progress(int(pr.score) / 100, text=f"{pr.score:.1f}%")

            if pr.issues:
                st.markdown("**Issues:**")
                for issue in pr.issues:
                    st.warning(issue)
            else:
                st.success("No issues found for this pillar.")

            if pr.details:
                with st.expander("Raw details (JSON)"):
                    st.json(pr.details)


def _render_profile(df: pd.DataFrame, profile_stats: dict) -> None:
    st.subheader("Dataset Profile")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Rows", f"{profile_stats.get('row_count', 0):,}")
    col2.metric("Total Columns", f"{profile_stats.get('column_count', 0)}")
    col3.metric("Memory (MB)", f"{profile_stats.get('memory_mb', 0):.1f}")

    # Missing value chart
    st.markdown("#### Missing Values by Column")
    st.plotly_chart(
        charts.missing_value_heatmap(profile_stats, top_n=25),
        width="stretch",
    )

    # Correlation heatmap
    corr_fig = charts.correlation_heatmap(profile_stats)
    if corr_fig:
        st.markdown("#### Feature Correlation Matrix (Numeric Columns)")
        st.plotly_chart(corr_fig, width="stretch")

    # Column stats table
    st.markdown("#### Column Statistics")
    col_stats = profile_stats.get("columns", {})
    if col_stats:
        rows = []
        for col, info in col_stats.items():
            row = {
                "Column": col,
                "Null %": info.get("null_pct", 0),
                "Unique": info.get("unique_count", 0),
                "Cardinality": info.get("cardinality_ratio", 0),
            }
            if "mean" in info:
                row["Mean"] = info.get("mean")
                row["Std"] = info.get("std")
                row["Skewness"] = info.get("skewness")
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    # Embedded ydata-profiling report
    html_report = profile_stats.get("html_report")
    if html_report:
        st.markdown("#### Full Profiling Report (ydata-profiling)")
        st.components.v1.html(html_report, height=800, scrolling=True)


def _render_recommendations(result) -> None:
    st.subheader("Remediation Recommendations")
    st.caption(f"Based on your data readiness score of **{result.overall_score:.1f}/100**")

    if not result.recommendations:
        st.success("No critical recommendations — your data looks good!")
        return

    for i, rec in enumerate(result.recommendations, 1):
        severity = "error" if rec.startswith("CRITICAL") else "warning" if i <= 3 else "info"
        if severity == "error":
            st.error(f"**{i}.** {rec}")
        elif severity == "warning":
            st.warning(f"**{i}.** {rec}")
        else:
            st.info(f"**{i}.** {rec}")

    st.divider()
    st.markdown("#### All Issues by Pillar")
    for name, pr in result.pillars.items():
        if pr.issues:
            label = charts.PILLAR_LABELS.get(name, name)
            st.markdown(f"**{label}** ({pr.score:.1f}/100)")
            for issue in pr.issues:
                st.caption(f"• {issue}")


def _render_export(result, profile_stats: dict, filename: str) -> None:
    st.subheader("Export Report")
    st.markdown(
        "Generate a professional PDF report summarising the data readiness assessment."
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Generating PDF…"):
                try:
                    from drf.reporting.pdf_generator import generate_pdf
                    pdf_bytes = generate_pdf(result, profile_stats, dataset_name=filename)
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"data_readiness_report_{result.timestamp[:10]}.pdf",
                        mime="application/pdf",
                    )
                    st.success("PDF generated successfully!")
                except Exception as exc:
                    st.error(f"PDF generation failed: {exc}")
                    st.info(
                        "WeasyPrint may require system dependencies. "
                        "See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
                    )

    with col2:
        if st.button("Download JSON Results"):
            import json
            json_data = _result_to_json(result)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"data_readiness_results_{result.timestamp[:10]}.json",
                mime="application/json",
            )


def _result_to_json(result) -> str:
    import json
    data = {
        "overall_score": result.overall_score,
        "band": result.band,
        "band_label": result.band_label,
        "timestamp": result.timestamp,
        "dataset_stats": result.dataset_stats,
        "pillars": {
            name: {
                "score": pr.score,
                "weight": pr.weight,
                "issues": pr.issues,
                "passed_checks": pr.passed_checks,
                "total_checks": pr.total_checks,
            }
            for name, pr in result.pillars.items()
        },
        "recommendations": result.recommendations,
        "all_issues": result.all_issues,
    }
    return json.dumps(data, indent=2, default=str)


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .stProgress > div > div > div { border-radius: 4px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

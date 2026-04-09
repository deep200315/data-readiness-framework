"""
PDF Generator — produces a proper PDF using ReportLab (pure Python,
no system dependencies). Falls back to HTML bytes if ReportLab is missing.
"""
from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.scoring.engine import ScoreResult

logger = logging.getLogger(__name__)

PILLAR_LABELS = {
    "completeness": "Completeness",
    "validity": "Validity",
    "uniqueness": "Uniqueness",
    "consistency": "Consistency",
    "timeliness": "Timeliness",
    "accuracy": "Accuracy",
    "ai_readiness": "AI Readiness",
}

# Colour palette
C_DARK       = (0.11, 0.15, 0.18)   # #1a252f
C_BLUE       = (0.16, 0.50, 0.73)   # #2980b9
C_LIGHT_BLUE = (0.91, 0.96, 0.99)   # #eaf4fb
C_WHITE      = (1.0,  1.0,  1.0)
C_LIGHT_GRAY = (0.97, 0.97, 0.97)   # #f8f9fa
C_MID_GRAY   = (0.70, 0.70, 0.70)
C_TEXT       = (0.17, 0.24, 0.31)   # #2c3e50

BAND_COLORS = {
    "excellent":  (0.18, 0.80, 0.44),   # #2ecc71
    "good":       (0.95, 0.61, 0.07),   # #f39c12
    "at_risk":    (0.90, 0.49, 0.13),   # #e67e22
    "not_ready":  (0.91, 0.30, 0.24),   # #e74c3c
}


def generate_pdf(
    result: "ScoreResult",
    profile_stats: dict,
    dataset_name: str = "Dataset",
) -> bytes:
    """
    Generate a PDF report using ReportLab.
    Returns PDF bytes ready for st.download_button.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable, KeepTogether,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        logger.error("ReportLab not installed. Run: pip install reportlab")
        raise RuntimeError("ReportLab is required for PDF generation: pip install reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Data Readiness Report — {dataset_name}",
        author="AI Data Readiness Framework",
    )

    W = A4[0] - 40 * mm   # usable page width

    styles = getSampleStyleSheet()
    story = []

    # ── helpers ────────────────────────────────────────────────────────────
    def rl_color(rgb_tuple):
        return colors.Color(*rgb_tuple)

    def band_rgb(band_key: str):
        return BAND_COLORS.get(band_key.replace("-", "_"), C_BLUE)

    def score_to_band_key(score: float) -> str:
        if score >= 85:   return "excellent"
        if score >= 70:   return "good"
        if score >= 50:   return "at_risk"
        return "not_ready"

    def score_to_band_label(score: float) -> str:
        return score_to_band_key(score).replace("_", " ").title()

    def h1(text):
        return Paragraph(
            text,
            ParagraphStyle("H1", fontSize=20, fontName="Helvetica-Bold",
                           textColor=rl_color(C_DARK), spaceAfter=4),
        )

    def h2(text):
        return Paragraph(
            text,
            ParagraphStyle("H2", fontSize=13, fontName="Helvetica-Bold",
                           textColor=rl_color(C_DARK), spaceBefore=14, spaceAfter=4),
        )

    def h3(text):
        return Paragraph(
            text,
            ParagraphStyle("H3", fontSize=11, fontName="Helvetica-Bold",
                           textColor=rl_color(C_BLUE), spaceBefore=10, spaceAfter=3),
        )

    def body(text, color=None):
        st = ParagraphStyle("Body", fontSize=9.5, fontName="Helvetica",
                            textColor=rl_color(color or C_TEXT),
                            spaceAfter=4, leading=14)
        return Paragraph(text, st)

    def caption(text):
        return Paragraph(
            text,
            ParagraphStyle("Cap", fontSize=8.5, fontName="Helvetica",
                           textColor=rl_color(C_MID_GRAY), spaceAfter=2),
        )

    def spacer(h=6):
        return Spacer(1, h * mm)

    def hr():
        return HRFlowable(width="100%", thickness=1,
                          color=rl_color(C_MID_GRAY), spaceAfter=6)

    # ── COVER PAGE ─────────────────────────────────────────────────────────
    overall = result.overall_score
    band_key = score_to_band_key(overall)
    band_label = result.band_label
    band_rgb_val = band_rgb(band_key)

    cover_data = [
        [Paragraph(
            f"<font color='#{_rgb_hex(C_WHITE)}' size='22'><b>AI Data Readiness Report</b></font><br/>"
            f"<font color='#bdc3c7' size='11'>{dataset_name}</font>",
            ParagraphStyle("CoverTitle", alignment=TA_CENTER, leading=30, spaceAfter=20),
        )],
        [Paragraph(
            f"<font size='48' color='#{_rgb_hex(band_rgb_val)}'><b>{overall:.1f}</b></font><br/>"
            f"<font size='12' color='#ecf0f1'>out of 100</font>",
            ParagraphStyle("CoverScore", alignment=TA_CENTER, leading=56, spaceAfter=10),
        )],
        [Paragraph(
            f"<font size='13' color='#{_rgb_hex(C_WHITE)}'><b>{band_label}</b></font>",
            ParagraphStyle("CoverBand", alignment=TA_CENTER, spaceAfter=20),
        )],
        [Paragraph(
            f"<font size='8' color='#95a5a6'>"
            f"Generated: {result.timestamp[:19].replace('T', ' ')}<br/>"
            f"Framework: 7-Pillar AI Readiness Assessment (DAMA-DMBOK + ISO 8000)"
            f"</font>",
            ParagraphStyle("CoverMeta", alignment=TA_CENTER, leading=14),
        )],
    ]

    cover_table = Table(cover_data, colWidths=[W])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), rl_color(C_DARK)),
        ("BOX",         (0, 0), (-1, -1), 0.5, rl_color(C_MID_GRAY)),
        ("TOPPADDING",  (0, 0), (-1, -1), 30),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 30),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("ROWBACKGROUNDS", (0, 1), (-1, 1), [rl_color((0.13, 0.18, 0.22))]),
    ]))

    story.append(cover_table)
    story.append(PageBreak())

    # ── SECTION 1: EXECUTIVE SUMMARY ───────────────────────────────────────
    story.append(h2("1. Executive Summary"))
    story.append(hr())

    # KPI cards row
    row_count    = profile_stats.get("row_count", result.dataset_stats.get("row_count", 0))
    col_count    = profile_stats.get("column_count", result.dataset_stats.get("column_count", 0))
    missing_pct  = profile_stats.get("overall_missing_pct", 0.0)
    dup_pct      = profile_stats.get("duplicate_pct", 0.0)

    kpi_data = [[
        _kpi_cell(f"{row_count:,}", "Total Rows"),
        _kpi_cell(str(col_count), "Total Columns"),
        _kpi_cell(f"{missing_pct:.1f}%", "Missing Data"),
        _kpi_cell(f"{dup_pct:.1f}%", "Duplicate Rows"),
    ]]
    kpi_table = Table(kpi_data, colWidths=[W / 4] * 4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), rl_color(C_LIGHT_BLUE)),
        ("BOX",         (0, 0), (-1, -1), 0.5, rl_color(C_BLUE)),
        ("INNERGRID",   (0, 0), (-1, -1), 0.5, rl_color(C_BLUE)),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(kpi_table)
    story.append(spacer(4))

    # Band message
    band_messages = {
        "excellent": ("Data is in excellent condition. Ready for AI/ML model training.", (0.10, 0.52, 0.27)),
        "good":      ("Data requires minor fixes before ML training. See recommendations.", (0.61, 0.35, 0.02)),
        "at_risk":   ("Significant issues detected. Remediation required before ML use.", (0.55, 0.27, 0.07)),
        "not_ready": ("Critical issues detected. Data is NOT suitable for AI/ML as-is.", (0.60, 0.10, 0.06)),
    }
    msg, msg_color = band_messages.get(band_key, ("Assessment complete.", C_TEXT))
    story.append(body(f"<b>Overall Score: {overall:.1f}/100 — {band_label}.</b> {msg}", color=msg_color))
    story.append(spacer(3))

    # ── SECTION 2: PILLAR SCORECARD ────────────────────────────────────────
    story.append(h2("2. Pillar Scorecard"))
    story.append(hr())

    table_data = [["Pillar", "Weight", "Score", "Weighted", "Checks", "Status"]]
    for name, pr in result.pillars.items():
        bk = score_to_band_key(pr.score)
        table_data.append([
            PILLAR_LABELS.get(name, name),
            f"{pr.weight * 100:.0f}%",
            f"{pr.score:.1f}/100",
            f"{pr.weighted_score:.2f}",
            f"{pr.passed_checks}/{pr.total_checks}",
            score_to_band_label(pr.score),
        ])
    # Total row
    table_data.append([
        "OVERALL", "100%",
        f"{overall:.1f}/100",
        f"{overall:.2f}", "—",
        score_to_band_label(overall),
    ])

    col_widths = [W * 0.28, W * 0.09, W * 0.16, W * 0.13, W * 0.13, W * 0.21]
    sc_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0),   rl_color(C_DARK)),
        ("TEXTCOLOR",     (0, 0), (-1, 0),   rl_color(C_WHITE)),
        ("FONTNAME",      (0, 0), (-1, 0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1),  8.5),
        ("ALIGN",         (1, 0), (-1, -1),  "CENTER"),
        ("GRID",          (0, 0), (-1, -1),  0.4, rl_color(C_MID_GRAY)),
        ("TOPPADDING",    (0, 0), (-1, -1),  5),
        ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [rl_color(C_WHITE), rl_color(C_LIGHT_GRAY)]),
        # Total row
        ("BACKGROUND",    (0, -1), (-1, -1), rl_color(C_LIGHT_BLUE)),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE",     (0, -1), (-1, -1), 1.5, rl_color(C_BLUE)),
    ]

    # Colour the status column per score
    for i, (name, pr) in enumerate(result.pillars.items(), start=1):
        bk = score_to_band_key(pr.score)
        ts.append(("TEXTCOLOR", (5, i), (5, i), rl_color(band_rgb(bk))))
        ts.append(("FONTNAME",  (5, i), (5, i), "Helvetica-Bold"))

    sc_table.setStyle(TableStyle(ts))
    story.append(sc_table)
    story.append(spacer(4))

    # ── SECTION 3: PILLAR FINDINGS ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(h2("3. Pillar-Level Findings"))
    story.append(hr())

    for name, pr in result.pillars.items():
        label = PILLAR_LABELS.get(name, name)
        bk = score_to_band_key(pr.score)
        color = band_rgb(bk)

        header = Table(
            [[Paragraph(
                f"<b>{label}</b> — {pr.score:.1f}/100 &nbsp;"
                f"<font color='#{_rgb_hex(color)}'>[{score_to_band_label(pr.score)}]</font>",
                ParagraphStyle("PH", fontSize=10, fontName="Helvetica-Bold",
                               textColor=rl_color(C_TEXT)),
            )]],
            colWidths=[W],
        )
        header.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), rl_color(C_LIGHT_GRAY)),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))

        block = [header]
        if pr.issues:
            for issue in pr.issues:
                is_critical = "CRITICAL" in issue
                bg = (1.0, 0.91, 0.91) if is_critical else (1.0, 0.98, 0.90)
                border = (0.91, 0.30, 0.24) if is_critical else (0.95, 0.61, 0.07)
                issue_row = Table(
                    [[Paragraph(issue, ParagraphStyle(
                        "Issue", fontSize=8.5, fontName="Helvetica",
                        textColor=rl_color(C_TEXT), leading=12))]],
                    colWidths=[W],
                )
                issue_row.setStyle(TableStyle([
                    ("BACKGROUND",  (0, 0), (-1, -1), rl_color(bg)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING",  (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEAFTER",   (0, 0), (0, 0), 3, rl_color(border)),
                ]))
                block.append(issue_row)
        else:
            block.append(Paragraph(
                "<font color='#27ae60'>No issues — all checks passed.</font>",
                ParagraphStyle("OK", fontSize=8.5, fontName="Helvetica",
                               leftIndent=8, spaceAfter=2),
            ))

        block.append(Spacer(1, 4))
        story.append(KeepTogether(block))

    # ── SECTION 4: RECOMMENDATIONS ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(h2("4. Recommendations"))
    story.append(hr())
    story.append(body("The following prioritised actions will improve your Data Readiness Score:"))
    story.append(spacer(2))

    if result.recommendations:
        for i, rec in enumerate(result.recommendations, 1):
            is_critical = "CRITICAL" in rec
            bg = (1.0, 0.91, 0.91) if is_critical else (0.91, 0.96, 0.99)
            prefix = f"<b>{i}.</b> "
            rec_row = Table(
                [[Paragraph(prefix + rec, ParagraphStyle(
                    "Rec", fontSize=8.5, fontName="Helvetica",
                    textColor=rl_color(C_TEXT), leading=13))]],
                colWidths=[W],
            )
            rec_row.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), rl_color(bg)),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEAFTER",     (0, 0), (0, 0), 3, rl_color(C_BLUE)),
            ]))
            story.append(rec_row)
            story.append(Spacer(1, 3))
    else:
        story.append(body("<font color='#27ae60'>No critical recommendations. Data is ready for ML.</font>"))

    # ── SECTION 5: COLUMN QUALITY TABLE ────────────────────────────────────
    story.append(PageBreak())
    story.append(h2("5. Column-Level Quality (Top Missing)"))
    story.append(hr())

    col_stats = profile_stats.get("columns", {})
    missing_cols = sorted(
        [(col, info) for col, info in col_stats.items() if info.get("null_pct", 0) > 0],
        key=lambda x: x[1].get("null_pct", 0),
        reverse=True,
    )[:30]

    if missing_cols:
        col_tbl_data = [["Column", "Null Count", "Null %", "Unique", "Status"]]
        for col, info in missing_cols:
            np_ = info.get("null_pct", 0)
            status = "Critical" if np_ >= 50 else "Warning" if np_ >= 20 else "OK"
            col_tbl_data.append([
                col, str(info.get("null_count", 0)),
                f"{np_:.1f}%",
                str(info.get("unique_count", 0)),
                status,
            ])
        cw = [W * 0.40, W * 0.15, W * 0.12, W * 0.15, W * 0.18]
        col_table = Table(col_tbl_data, colWidths=cw, repeatRows=1)
        col_ts = [
            ("BACKGROUND",    (0, 0), (-1, 0),   rl_color(C_DARK)),
            ("TEXTCOLOR",     (0, 0), (-1, 0),   rl_color(C_WHITE)),
            ("FONTNAME",      (0, 0), (-1, 0),   "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1),  8),
            ("ALIGN",         (1, 0), (-1, -1),  "CENTER"),
            ("GRID",          (0, 0), (-1, -1),  0.3, rl_color(C_MID_GRAY)),
            ("TOPPADDING",    (0, 0), (-1, -1),  4),
            ("BOTTOMPADDING", (0, 0), (-1, -1),  4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_color(C_WHITE), rl_color(C_LIGHT_GRAY)]),
        ]
        # Colour status column
        for i, (col, info) in enumerate(missing_cols, start=1):
            np_ = info.get("null_pct", 0)
            c = (0.91, 0.30, 0.24) if np_ >= 50 else (0.90, 0.49, 0.13) if np_ >= 20 else (0.18, 0.80, 0.44)
            col_ts.append(("TEXTCOLOR", (4, i), (4, i), rl_color(c)))
            col_ts.append(("FONTNAME",  (4, i), (4, i), "Helvetica-Bold"))
        col_table.setStyle(TableStyle(col_ts))
        story.append(col_table)
    else:
        story.append(body("<font color='#27ae60'>No missing values detected in any column!</font>"))

    # ── SECTION 6: METHODOLOGY ─────────────────────────────────────────────
    story.append(spacer(6))
    story.append(h2("6. Assessment Methodology"))
    story.append(hr())

    method_rows = [
        ["Pillar", "Weight", "What It Measures"],
        ["Completeness",  "20%", "Missing/null values per column and row"],
        ["Validity",      "15%", "Schema conformance, data types, value ranges"],
        ["Uniqueness",    "10%", "Duplicate rows and key column integrity"],
        ["Consistency",   "15%", "Cross-field logic and referential checks"],
        ["Timeliness",    "10%", "Date ordering, temporal gaps, recency"],
        ["Accuracy",      "15%", "Statistical outliers (Z-score + Isolation Forest)"],
        ["AI Readiness",  "15%", "Feature correlation, class balance, leakage risk"],
    ]
    mw = [W * 0.25, W * 0.12, W * 0.63]
    m_table = Table(method_rows, colWidths=mw, repeatRows=1)
    m_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),   rl_color(C_DARK)),
        ("TEXTCOLOR",     (0, 0), (-1, 0),   rl_color(C_WHITE)),
        ("FONTNAME",      (0, 0), (-1, 0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1),  8.5),
        ("GRID",          (0, 0), (-1, -1),  0.3, rl_color(C_MID_GRAY)),
        ("TOPPADDING",    (0, 0), (-1, -1),  5),
        ("BOTTOMPADDING", (0, 0), (-1, -1),  5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [rl_color(C_WHITE), rl_color(C_LIGHT_GRAY)]),
        ("FONTNAME",      (0, 1), (0, -1),   "Helvetica-Bold"),
    ]))
    story.append(m_table)
    story.append(spacer(3))
    story.append(caption("Standards: DAMA-DMBOK  ·  ISO 8000  ·  ISO/IEC 25012"))

    # ── BUILD PDF ──────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
    return buf.getvalue()


# ── Helpers ────────────────────────────────────────────────────────────────

def _kpi_cell(value: str, label: str):
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    return Paragraph(
        f"<font size='16'><b>{value}</b></font><br/>"
        f"<font size='8' color='#7f8c8d'>{label}</font>",
        ParagraphStyle("KPI", alignment=TA_CENTER, leading=20),
    )


def _rgb_hex(rgb_tuple) -> str:
    """Convert (r, g, b) floats 0-1 to hex string without #."""
    r, g, b = rgb_tuple
    return f"{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def _add_footer(canvas, doc):
    """Draw page number footer on each page."""
    from reportlab.lib.units import mm
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColorRGB(*C_MID_GRAY)
    canvas.drawCentredString(
        doc.pagesize[0] / 2,
        12 * mm,
        f"AI Data Readiness Framework  |  Page {doc.page}",
    )
    canvas.restoreState()

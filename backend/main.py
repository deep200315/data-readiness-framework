"""FastAPI backend — wraps drf/ scoring engine as REST API."""
from __future__ import annotations

import io
import logging
import sys  # noqa: E401 — needed for sys.path before drf imports
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drf.ingestion.loader import load_file
from drf.profiling.profiler import run_profile
from drf.reporting.pdf_generator import generate_pdf
from drf.scoring.engine import ScoreResult, load_config, run

logging.basicConfig(level=logging.INFO)

CONFIG_DIR = ROOT / "config"
SCORING_CONFIG = load_config(str(CONFIG_DIR / "scoring_weights.yaml"))
VALIDATION_CONFIG = load_config(str(CONFIG_DIR / "validation_rules.yaml"))

app = FastAPI(title="Data Readiness Framework API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

_store: dict[str, dict] = {}


def _serialise(result: ScoreResult, profile: dict) -> dict:
    return {
        "overall_score": result.overall_score,
        "band": result.band,
        "band_label": result.band_label,
        "band_color": result.band_color,
        "pillars": {
            name: {
                "score": pr.score,
                "weight": pr.weight,
                "weighted_score": pr.weighted_score,
                "issues": pr.issues,
                "details": pr.details,
                "passed_checks": pr.passed_checks,
                "total_checks": pr.total_checks,
            }
            for name, pr in result.pillars.items()
        },
        "recommendations": result.recommendations,
        "dataset_stats": result.dataset_stats,
        "timestamp": result.timestamp,
        "profile": {
            "row_count": profile.get("row_count", 0),
            "column_count": profile.get("column_count", 0),
            "overall_missing_pct": profile.get("overall_missing_pct", 0.0),
            "duplicate_rows": profile.get("duplicate_rows", 0),
            "duplicate_pct": profile.get("duplicate_pct", 0.0),
            "memory_mb": profile.get("memory_mb", 0.0),
            "numeric_col_count": profile.get("numeric_col_count", 0),
            "categorical_col_count": profile.get("categorical_col_count", 0),
            "missing_map": dict(list(profile.get("missing_map", {}).items())[:20]),
        },
    }


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    contents = await file.read()
    buf = io.BytesIO(contents)
    try:
        df = load_file(buf, file_name=file.filename)
    except Exception as exc:
        raise HTTPException(400, f"Cannot parse file: {exc}")

    profile = run_profile(df)
    result = run(df, SCORING_CONFIG, VALIDATION_CONFIG, profile)

    job_id = str(uuid.uuid4())
    _store[job_id] = {"result": result, "profile": profile, "name": file.filename}

    return {"job_id": job_id, "dataset_name": file.filename, **_serialise(result, profile)}


@app.get("/api/report/{job_id}/pdf")
def download_pdf(job_id: str):
    if job_id not in _store:
        raise HTTPException(404, "Job not found")
    d = _store[job_id]
    pdf_bytes = generate_pdf(d["result"], d["profile"], d["name"])
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="readiness_report.pdf"'},
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}

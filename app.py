"""
Data Readiness Framework — Streamlit Application Entry Point.

Run with:
    streamlit run app.py
"""
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path before any drf.* imports
ROOT = Path(__file__).resolve().parent
_root_str = str(ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

os.chdir(_root_str)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

from drf.reporting.dashboard import run_dashboard  # noqa: E402

run_dashboard()

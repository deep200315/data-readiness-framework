"""
Data Readiness Framework — Streamlit Application Entry Point.

Run with:
    streamlit run app.py
"""
import logging
import sys
from pathlib import Path

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)

from src.reporting.dashboard import run_dashboard

if __name__ == "__main__":
    run_dashboard()
else:
    # Called by `streamlit run app.py` (module-level execution)
    run_dashboard()

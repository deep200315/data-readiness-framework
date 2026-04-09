# AI Data Readiness Framework

A 7-pillar scoring framework that assesses whether supply chain data is ready for AI/ML model training — and tells you exactly what to fix.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)

---

## What It Does

Upload any CSV or Excel dataset and get an instant **Data Readiness Score (0–100)** across 7 quality dimensions, a visual dashboard, and a downloadable PDF report.

| Pillar | Weight | What It Checks |
|--------|--------|---------------|
| Completeness | 20% | Missing / null values |
| Validity | 15% | Schema, data types, value ranges |
| Uniqueness | 10% | Duplicate rows, key integrity |
| Consistency | 15% | Cross-field logic, date ordering |
| Timeliness | 10% | Temporal gaps, date recency |
| Accuracy | 15% | Statistical outliers (Z-score + Isolation Forest) |
| AI Readiness | 15% | Feature leakage, class balance, correlation |

**Quality Bands**

| Score | Band | Meaning |
|-------|------|---------|
| 85–100 | Excellent | Ready for ML training |
| 70–84 | Good | Minor fixes needed |
| 50–69 | At Risk | Significant remediation required |
| 0–49 | Not Ready | Not suitable for AI as-is |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/data-readiness-framework.git
cd data-readiness-framework

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Then open **http://localhost:8501** in your browser and upload a CSV file.

---

## Test Datasets

Generate 3 synthetic datasets to try the framework immediately:

```bash
python data/generate_test_data.py
```

This creates:
- `data/good_data.csv` → ~97/100 (Excellent)
- `data/medium_data.csv` → ~82/100 (Good)
- `data/bad_data.csv` → ~63/100 (At Risk)

Or use the [DataCo Supply Chain Dataset](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) from Kaggle (180K rows × 53 columns).

---

## Project Structure

```
data-readiness-framework/
├── app.py                         # Streamlit entry point
├── config/
│   ├── scoring_weights.yaml       # Pillar weights & band thresholds
│   └── validation_rules.yaml     # Supply chain domain rules
├── src/
│   ├── ingestion/                 # Data loading & schema detection
│   ├── profiling/                 # Automated EDA (ydata-profiling)
│   ├── validators/                # 7 pillar validators
│   ├── scoring/                   # Weighted scoring engine + recommendations
│   └── reporting/                 # Streamlit dashboard, charts, PDF export
├── tests/                         # 23 unit tests (pytest)
├── data/
│   └── generate_test_data.py     # Synthetic test data generator
└── requirements.txt
```

---

## Tech Stack

- **Dashboard:** Streamlit + Plotly
- **Profiling:** ydata-profiling (optional)
- **Validation:** pandas + Great Expectations (optional)
- **Anomaly Detection:** scikit-learn (Isolation Forest)
- **PDF Export:** ReportLab
- **Standards:** DAMA-DMBOK · ISO 8000 · ISO/IEC 25012

---

## Run Tests

```bash
pytest tests/ -v
```

23 tests covering all 7 pillar validators and the scoring engine.

---

## ML Use Cases (DataCo Dataset)

Once your data scores 70+, it is ready to train:

| Task | Target Column | Algorithm |
|------|--------------|-----------|
| Late Delivery Prediction | `Late_delivery_risk` | XGBoost, Random Forest |
| Demand Forecasting | `Sales` | Prophet, LSTM |
| Fraud Detection | `Order Status` = SUSPECTED_FRAUD | Isolation Forest |
| Customer Segmentation | — | K-Means, DBSCAN |

---

## License

MIT

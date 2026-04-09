from setuptools import find_packages, setup

setup(
    name="data-readiness-framework",
    version="1.0.0",
    description="AI Data Readiness Assessment Framework — 7-Pillar Scoring for Supply Chain Data",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.0",
        "numpy>=1.24",
        "openpyxl>=3.1",
        "PyYAML>=6.0",
        "scikit-learn>=1.4",
        "streamlit>=1.32",
        "plotly>=5.20",
        "jinja2>=3.1",
    ],
    extras_require={
        "profiling": ["ydata-profiling>=4.6"],
        "pdf": ["weasyprint>=60.0"],
        "all": [
            "ydata-profiling>=4.6",
            "weasyprint>=60.0",
            "great-expectations>=0.18",
            "evidently>=0.4",
        ],
    },
)

"""
Generate 3 synthetic supply chain CSV test datasets:
  1. bad_data.csv       — heavily flawed  → expect score ~25-35
  2. medium_data.csv    — partially clean → expect score ~55-65
  3. good_data.csv      — near-perfect    → expect score ~88-95

Run: python data/generate_test_data.py
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).parent
RNG = np.random.default_rng(42)
N = 2000  # rows per dataset

SHIPPING_MODES   = ["First Class", "Second Class", "Standard Class", "Same Day"]
DELIVERY_STATUS  = ["Advance shipping", "Late delivery", "Shipping canceled", "Shipping on time"]
ORDER_STATUS     = ["COMPLETE", "PENDING", "CLOSED", "CANCELED", "PROCESSING", "SUSPECTED_FRAUD"]
SEGMENTS         = ["Consumer", "Corporate", "Home Office"]
MARKETS          = ["Europe", "LATAM", "Pacific Asia", "Africa", "USCA"]
CATEGORIES       = ["Clothing", "Sports", "Electronics", "Furniture", "Books"]
COUNTRIES        = ["United States", "France", "Germany", "Brazil", "India"]


# ──────────────────────────────────────────────────────────────────────────────
def _base_records(n: int) -> pd.DataFrame:
    """Generate a clean base dataset — all values valid."""
    order_dates = pd.date_range("2022-01-01", periods=n, freq="2h")
    ship_dates  = order_dates + pd.to_timedelta(RNG.integers(1, 8, n), unit="D")

    late_risk   = RNG.choice([0, 1], n, p=[0.62, 0.38])
    del_status  = np.where(
        late_risk == 1,
        "Late delivery",
        RNG.choice(["Advance shipping", "Shipping on time", "Shipping canceled"], n),
    )
    quantity    = RNG.integers(1, 50, n)
    price       = RNG.uniform(5, 500, n).round(2)
    discount    = RNG.uniform(0.0, 0.45, n).round(3)
    sales       = (quantity * price * (1 - discount)).round(2)
    profit      = (sales * RNG.uniform(-0.05, 0.35, n)).round(2)
    days_sched  = RNG.integers(2, 7, n)
    days_real   = (ship_dates - order_dates).days.astype(int)

    return pd.DataFrame({
        "Order Id":                   range(1001, 1001 + n),
        "order date (DateOrders)":    order_dates.strftime("%m/%d/%Y %H:%M"),
        "shipping date (DateOrders)": ship_dates.strftime("%m/%d/%Y %H:%M"),
        "Shipping Mode":              RNG.choice(SHIPPING_MODES, n),
        "Delivery Status":            del_status,
        "Late_delivery_risk":         late_risk,
        "Order Status":               RNG.choice(ORDER_STATUS, n),
        "Customer Id":                RNG.integers(10000, 99999, n),
        "Customer Segment":           RNG.choice(SEGMENTS, n),
        "Customer Country":           RNG.choice(COUNTRIES, n),
        "Market":                     RNG.choice(MARKETS, n),
        "Order Region":               RNG.choice(MARKETS, n),
        "Category Name":              RNG.choice(CATEGORIES, n),
        "Product Card Id":            RNG.integers(100, 9999, n),
        "Order Item Quantity":        quantity,
        "Sales":                      sales,
        "Order Item Discount Rate":   discount,
        "Benefit per order":          profit,
        "Days for shipment (scheduled)": days_sched,
        "Days for shipping (real)":   days_real,
        "Order Item Profit Ratio":    (profit / np.clip(sales, 0.01, None)).round(4),
    })


# ──────────────────────────────────────────────────────────────────────────────
def make_good(n: int) -> pd.DataFrame:
    """Near-perfect dataset — minimal issues."""
    df = _base_records(n)
    # Introduce just 0.5% duplicates
    dup_idx = RNG.choice(n, int(n * 0.005), replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)
    return df


def make_medium(n: int) -> pd.DataFrame:
    """Partially flawed dataset — several realistic issues."""
    df = _base_records(n)

    # 1. Missing values in several columns (~15%)
    for col in ["Customer Country", "Market", "Category Name", "Order Region"]:
        mask = RNG.choice([True, False], n, p=[0.15, 0.85])
        df.loc[mask, col] = None

    # 2. One heavily sparse column (~60% null)
    df["Product Description"] = None
    df.loc[RNG.choice(n, int(n * 0.4), replace=False), "Product Description"] = "Some desc"

    # 3. Some out-of-range values
    bad_qty = RNG.choice(n, int(n * 0.04), replace=False)
    df.loc[bad_qty, "Order Item Quantity"] = RNG.integers(-10, 0, len(bad_qty))

    bad_disc = RNG.choice(n, int(n * 0.03), replace=False)
    df.loc[bad_disc, "Order Item Discount Rate"] = RNG.uniform(1.1, 2.5, len(bad_disc)).round(3)

    # 4. Invalid enum values in Shipping Mode
    bad_ship = RNG.choice(n, int(n * 0.05), replace=False)
    df.loc[bad_ship, "Shipping Mode"] = RNG.choice(["Express", "Economy", "Unknown"], len(bad_ship))

    # 5. ~8% duplicates
    dup_idx = RNG.choice(n, int(n * 0.08), replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)

    # 6. Some statistical outliers in Sales
    outlier_idx = RNG.choice(len(df), 30, replace=False)
    df.loc[outlier_idx, "Sales"] = RNG.uniform(500_000, 2_000_000, 30).round(2)

    # 7. Class imbalance: shift Late_delivery_risk to 90/10
    n_total = len(df)
    target = np.zeros(n_total, dtype=int)
    late_indices = RNG.choice(n_total, int(n_total * 0.10), replace=False)
    target[late_indices] = 1
    df["Late_delivery_risk"] = target

    return df


def make_bad(n: int) -> pd.DataFrame:
    """Heavily flawed dataset — multiple critical issues across all 7 pillars."""
    df = _base_records(n)

    # 1. COMPLETENESS: Massive missing values across many columns (55-80%)
    for col in ["Customer Country", "Market", "Order Region", "Category Name",
                "Product Card Id", "Order Status", "Customer Segment",
                "Shipping Mode", "Delivery Status"]:
        mask = RNG.choice([True, False], n, p=[0.65, 0.35])
        df.loc[mask, col] = None

    # Also null key numeric columns
    for col in ["Sales", "Benefit per order", "Order Item Discount Rate"]:
        mask = RNG.choice([True, False], n, p=[0.30, 0.70])
        df.loc[mask, col] = None

    df["Product Description"] = None   # 100% null column
    df["Order Zipcode"]        = None   # 100% null column

    # 2. VALIDITY: Null in required ID columns
    df.loc[RNG.choice(n, int(n * 0.30), replace=False), "Customer Id"] = None
    df.loc[RNG.choice(n, int(n * 0.25), replace=False), "Order Id"] = None

    # 3. UNIQUENESS: Heavy duplicates (~30%)
    dup_idx = RNG.choice(n, int(n * 0.30), replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)
    n_total = len(df)

    # 4. CONSISTENCY: Shipping date BEFORE order date (30% of rows)
    bad_dates = RNG.choice(n_total, int(n_total * 0.30), replace=False)
    order_dt = pd.to_datetime(df["order date (DateOrders)"], errors="coerce")
    df.loc[bad_dates, "shipping date (DateOrders)"] = (
        order_dt.iloc[bad_dates] - pd.to_timedelta(
            RNG.integers(1, 30, len(bad_dates)), unit="D"
        )
    ).dt.strftime("%m/%d/%Y %H:%M")

    # 5. TIMELINESS: Insert large date gaps (120-200 day gaps) and future dates
    gap_start = int(n_total * 0.40)
    gap_end   = int(n_total * 0.55)
    future_dt = pd.Timestamp("2031-06-01")
    df.loc[gap_start:gap_end, "order date (DateOrders)"] = \
        future_dt.strftime("%m/%d/%Y %H:%M")

    # 6. VALIDITY: Completely invalid enum values (50%)
    bad_ship = RNG.choice(n_total, int(n_total * 0.50), replace=False)
    df.loc[bad_ship, "Shipping Mode"] = \
        RNG.choice(["Air", "Sea", "Road", "UNKNOWN", "N/A"], len(bad_ship))

    bad_del = RNG.choice(n_total, int(n_total * 0.45), replace=False)
    df.loc[bad_del, "Delivery Status"] = \
        RNG.choice(["Delivered", "Pending", "Returned", "???"], len(bad_del))

    # 7. ACCURACY: Extreme outliers in numeric columns (15%)
    for col in ["Sales", "Benefit per order"]:
        df[col] = df[col].astype(float)
        out_idx = RNG.choice(n_total, int(n_total * 0.15), replace=False)
        df.loc[out_idx, col] = RNG.uniform(5_000_000, 50_000_000, len(out_idx)).round(2)

    df["Order Item Quantity"] = df["Order Item Quantity"].astype(float)
    out_idx = RNG.choice(n_total, int(n_total * 0.15), replace=False)
    df.loc[out_idx, "Order Item Quantity"] = RNG.uniform(50000, 999999, len(out_idx)).round(0)

    # Negative values (10%)
    neg_idx = RNG.choice(n_total, int(n_total * 0.10), replace=False)
    df.loc[neg_idx, "Order Item Quantity"] = RNG.integers(-500, -1, len(neg_idx))
    df.loc[neg_idx, "Sales"] = RNG.uniform(-500000, -1, len(neg_idx)).round(2)

    # 8. Severe class imbalance: 97/3
    target = np.zeros(n_total, dtype=int)
    target[RNG.choice(n_total, int(n_total * 0.03), replace=False)] = 1
    df["Late_delivery_risk"] = target

    # 9. Two near-perfectly correlated feature columns (multicollinearity)
    df["Sales_copy"]  = df["Sales"] * 1.0001 + RNG.normal(0, 0.01, n_total)
    df["Sales_copy2"] = df["Sales"] * 0.9999 + RNG.normal(0, 0.01, n_total)

    return df


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    datasets = {
        "good_data.csv":   make_good(N),
        "medium_data.csv": make_medium(N),
        "bad_data.csv":    make_bad(N),
    }

    for filename, df in datasets.items():
        path = OUT_DIR / filename
        df.to_csv(path, index=False)
        print(f"Generated {filename:20s} | {len(df):,} rows x {len(df.columns)} cols | {path}")

    print("\nDone! Upload any of these files to the Streamlit app to test the framework.")
    print("Expected scores:")
    print("  good_data.csv   -> ~88-95  (Excellent)")
    print("  medium_data.csv -> ~55-65  (At Risk)")
    print("  bad_data.csv    -> ~25-35  (Not Ready)")

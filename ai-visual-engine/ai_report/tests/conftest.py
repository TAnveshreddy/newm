"""Shared fixtures: clean, messy, and edge-case datasets."""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def clean_sales() -> pd.DataFrame:
    np.random.seed(1)
    months = pd.date_range("2025-01-01", periods=12, freq="MS")
    regions = ["North", "South", "East", "West"]
    cats = ["Electronics", "Furniture", "Clothing"]
    products = ["Alpha", "Beta", "Gamma", "Delta"]
    rows = []
    for m in months:
        for r in regions:
            for c in cats:
                rows.append({
                    "Date": m.strftime("%Y-%m-%d"),
                    "Region": r,
                    "Category": c,
                    "Product": np.random.choice(products),
                    "CustomerID": int(np.random.randint(1, 30)),
                    "Revenue": int(np.random.randint(1000, 50000)),
                    "Cost": int(np.random.randint(500, 25000)),
                    "Quantity": int(np.random.randint(1, 200)),
                })
    return pd.DataFrame(rows)


@pytest.fixture
def messy_sales() -> pd.DataFrame:
    """Contains nulls, empty strings, invalid dates, mixed date formats, dupes."""
    data = [
        {"Date": "2025-01-01", "Region": "North", "Revenue": 100, "Cost": 40},
        {"Date": "01/02/2025", "Region": "South", "Revenue": 200, "Cost": 80},
        {"Date": "not-a-date", "Region": "East", "Revenue": 300, "Cost": 120},
        {"Date": "2025-03-01", "Region": "", "Revenue": None, "Cost": 50},
        {"Date": "Jan 04 2025", "Region": "West", "Revenue": 150, "Cost": 60},
        # duplicate of row 1
        {"Date": "2025-01-01", "Region": "North", "Revenue": 100, "Cost": 40},
    ]
    return pd.DataFrame(data)


@pytest.fixture
def datasets(clean_sales):
    return {"sales": clean_sales}

"""Dataset profiling + automatic column / data-type / semantic detection
(requirements #1, #2, #12).

``profile_dataset(df)`` returns rich per-column metadata and a semantic layer
(dimensions / measures / dates / identifiers / hierarchies) that the planner and
validator both consume. This is what stops the LLM from inventing columns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from . import dates as datemod

GEO_TOKENS = {"country", "state", "province", "city", "region", "district",
              "zip", "zipcode", "postal", "postalcode", "lat", "lon", "long",
              "latitude", "longitude", "territory", "area"}

# Common geographic drill-down order, most-coarse first.
GEO_HIERARCHY_ORDER = ["country", "state", "province", "region", "district", "city", "store"]


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    data_type: str          # string|integer|float|decimal|date|datetime|boolean|categorical|identifier
    semantic_type: str      # dimension|measure|date|identifier
    nullable: bool
    null_count: int
    unique_count: int
    is_geographic: bool = False
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    sample_values: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "column": self.name,
            "data_type": self.data_type,
            "semantic_type": self.semantic_type,
            "nullable": self.nullable,
            "null_count": self.null_count,
            "unique_count": self.unique_count,
        }
        if self.is_geographic:
            d["is_geographic"] = True
        for k in ("min", "max", "mean"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        if self.sample_values:
            d["sample_values"] = self.sample_values
        return d


@dataclass
class DatasetProfile:
    name: str
    rows: int
    columns: List[ColumnProfile]

    def column(self, name: str) -> Optional[ColumnProfile]:
        for c in self.columns:
            if c.name == name:
                return c
        return None

    # -- semantic layer -----------------------------------------------------
    def dimensions(self) -> List[str]:
        return [c.name for c in self.columns if c.semantic_type in ("dimension", "identifier")]

    def measures(self) -> List[str]:
        return [c.name for c in self.columns if c.semantic_type == "measure"]

    def date_columns(self) -> List[str]:
        return [c.name for c in self.columns if c.semantic_type == "date"]

    def identifiers(self) -> List[str]:
        return [c.name for c in self.columns if c.semantic_type == "identifier"]

    def hierarchies(self) -> List[Dict[str, Any]]:
        hs = []
        geo = _geo_hierarchy([c.name for c in self.columns if c.is_geographic])
        if len(geo) >= 2:
            hs.append({"name": "Geography", "levels": geo})
        if self.date_columns():
            hs.append({"name": "Date", "levels": datemod.DATE_PARTS})
        return hs

    def semantic_metadata(self) -> Dict[str, Any]:
        return {
            "dataset": self.name,
            "dimensions": self.dimensions(),
            "measures": self.measures(),
            "dates": self.date_columns(),
            "identifiers": self.identifiers(),
            "hierarchies": self.hierarchies(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rows": self.rows,
            "columns": len(self.columns),
            "column_details": [c.to_dict() for c in self.columns],
            "semantic": self.semantic_metadata(),
        }


def _geo_hierarchy(geo_cols: List[str]) -> List[str]:
    lower = {c.lower(): c for c in geo_cols}
    ordered = [lower[t] for t in GEO_HIERARCHY_ORDER if t in lower]
    # append any remaining geo columns not in the known order
    for c in geo_cols:
        if c not in ordered:
            ordered.append(c)
    return ordered


def _name_is_identifier(name: str) -> bool:
    lname = name.lower()
    return lname.endswith("id") or lname in ("id", "guid", "uuid", "key", "code")


def _near_unique(series: pd.Series, rows: int) -> bool:
    """A near-unique column is likely a key/identifier — but only trust this for
    NON-numeric columns, since numeric measures (revenue, price) are often unique."""
    return rows > 5 and series.nunique(dropna=True) >= max(rows * 0.95, rows - 1)


def _classify(name: str, series: pd.Series, rows: int) -> ColumnProfile:
    null_count = int(series.isna().sum())
    unique_count = int(series.nunique(dropna=True))
    nullable = null_count > 0
    dtype = str(series.dtype)
    is_geo = name.lower() in GEO_TOKENS

    # Boolean
    if pd.api.types.is_bool_dtype(series):
        return ColumnProfile(name, dtype, "boolean", "dimension", nullable, null_count, unique_count, is_geo)

    # Datetime dtype
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnProfile(name, dtype, "datetime", "date", nullable, null_count, unique_count, is_geo)

    # Numeric — identifier only when the NAME says so (avoid flagging unique measures).
    if pd.api.types.is_numeric_dtype(series):
        if _name_is_identifier(name):
            return ColumnProfile(name, dtype, "identifier", "identifier", nullable, null_count, unique_count, is_geo)
        data_type = "integer" if pd.api.types.is_integer_dtype(series) else "float"
        cp = ColumnProfile(name, dtype, data_type, "measure", nullable, null_count, unique_count, is_geo)
        s = series.dropna()
        if not s.empty:
            cp.min, cp.max, cp.mean = float(s.min()), float(s.max()), float(s.mean())
        return cp

    # Object / string — could be date, boolean-ish, identifier, or categorical
    if datemod.looks_like_date(series):
        return ColumnProfile(name, dtype, "date", "date", nullable, null_count, unique_count, is_geo)

    if _name_is_identifier(name) or _near_unique(series, rows):
        return ColumnProfile(name, dtype, "identifier", "identifier", nullable, null_count, unique_count, is_geo)

    sample = series.dropna().astype(str).unique()[:10].tolist()
    semantic = "dimension"
    cp = ColumnProfile(name, dtype, "categorical", semantic, nullable, null_count, unique_count, is_geo)
    cp.sample_values = sample
    return cp


def profile_dataset(df: pd.DataFrame, name: str = "dataset") -> DatasetProfile:
    rows = len(df)
    cols = [_classify(str(col), df[col], rows) for col in df.columns]
    return DatasetProfile(name=name, rows=rows, columns=cols)


def profile_all(datasets: Dict[str, pd.DataFrame]) -> Dict[str, DatasetProfile]:
    return {name: profile_dataset(df, name) for name, df in datasets.items()}


def profiles_to_dict(profiles: Dict[str, DatasetProfile]) -> Dict[str, Any]:
    return {name: p.to_dict() for name, p in profiles.items()}

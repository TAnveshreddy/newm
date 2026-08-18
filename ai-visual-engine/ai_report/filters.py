"""Filter application (requirement #6). Filters are applied BEFORE aggregation."""
from __future__ import annotations

from typing import List

import pandas as pd

from .errors import SemanticError
from .schema import Filter


def apply_filters(df: pd.DataFrame, filters: List[Filter]) -> pd.DataFrame:
    out = df
    for f in filters:
        out = _apply_one(out, f)
    return out


def _coerce(series: pd.Series, value):
    """Best-effort coerce a filter value to the column's type for comparison."""
    if pd.api.types.is_numeric_dtype(series):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


def _apply_one(df: pd.DataFrame, f: Filter) -> pd.DataFrame:
    if f.column not in df.columns:
        raise SemanticError(f"Filter column '{f.column}' not found.")
    series = df[f.column]
    op = f.operator
    val = f.value

    if op == "=":
        return df[series == _coerce(series, val)]
    if op == "!=":
        return df[series != _coerce(series, val)]
    if op == ">":
        return df[series > _coerce(series, val)]
    if op == "<":
        return df[series < _coerce(series, val)]
    if op == ">=":
        return df[series >= _coerce(series, val)]
    if op == "<=":
        return df[series <= _coerce(series, val)]
    if op == "in":
        vals = val if isinstance(val, (list, tuple)) else [val]
        return df[series.isin(vals)]
    if op == "not in":
        vals = val if isinstance(val, (list, tuple)) else [val]
        return df[~series.isin(vals)]
    if op == "between":
        if not isinstance(val, (list, tuple)) or len(val) != 2:
            raise SemanticError("BETWEEN requires a [low, high] value.")
        lo, hi = _coerce(series, val[0]), _coerce(series, val[1])
        return df[(series >= lo) & (series <= hi)]
    if op == "contains":
        return df[series.astype(str).str.contains(str(val), case=False, na=False)]

    raise SemanticError(f"Unsupported operator: {op}")

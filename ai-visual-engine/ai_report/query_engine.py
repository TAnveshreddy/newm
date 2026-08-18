"""Query / transformation engine (requirements #6, #7, #8, #9).

Turns a validated VisualPlan into a small, tidy result DataFrame:

    filter -> derive date parts -> choose dimension -> aggregate -> sort -> top-N

This is the only place data is shaped; renderers just draw the result.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd

from . import aggregations, dates, hierarchy
from .filters import apply_filters
from .profiler import DatasetProfile
from .schema import VisualPlan


@dataclass
class QueryResult:
    df: pd.DataFrame
    x: Optional[str]
    y: Optional[str]
    kind: str  # "aggregated" | "raw" | "scalar"


def prepare_dataframe(df: pd.DataFrame, profile: DatasetProfile) -> pd.DataFrame:
    """Add derived date-part columns (Year, Quarter, Month, Week, Day) for the
    primary date column so filters and groupings on them work."""
    out = df
    date_cols = profile.date_columns()
    if not date_cols:
        return out
    out = out.copy()
    primary = date_cols[0]
    parsed, _ = dates.parse_dates(out[primary])
    out[primary] = parsed
    for part in dates.DATE_PARTS:
        if part not in out.columns:
            out[part] = dates.derive_part(parsed, part)
    return out


def build_result(df: pd.DataFrame, profile: DatasetProfile, visual: VisualPlan) -> QueryResult:
    data = prepare_dataframe(df, profile)

    # 1. Filters (before aggregation).
    if visual.filters:
        data = apply_filters(data, visual.filters)

    # 2. Table: return filtered rows (optionally sorted / limited).
    if visual.type == "table":
        if visual.sort and visual.sort.column in data.columns:
            data = data.sort_values(visual.sort.column, ascending=visual.sort.direction == "asc")
        if visual.limit:
            data = data.head(visual.limit)
        return QueryResult(df=data.reset_index(drop=True), x=None, y=None, kind="raw")

    # 3. KPI: scalar handled by kpi module, but return the (filtered) frame.
    if visual.type == "kpi":
        return QueryResult(df=data, x=None, y=visual.y, kind="scalar")

    # 4. Scatter: no aggregation, two raw numeric columns.
    if visual.type == "scatter":
        cols = [c for c in (visual.x, visual.y) if c]
        return QueryResult(df=data[cols].dropna(), x=visual.x, y=visual.y, kind="raw")

    # 5. Histogram: single numeric column, no aggregation.
    if visual.type == "histogram":
        col = visual.y or visual.x
        return QueryResult(df=data[[col]].dropna(), x=col, y=None, kind="raw")

    # 6. Cartesian / pie: choose dimension, optional date grain, then aggregate.
    dimension = _choose_dimension(visual, profile)
    grain = _date_grain(visual, profile, dimension)

    if grain and dimension in profile.date_columns():
        # Replace the raw date with its derived grain for grouping.
        data = data.copy()
        data[dimension] = dates.derive_part(pd.to_datetime(data[dimension], errors="coerce"), grain)

    result = aggregations.aggregate(data, [dimension], visual.y, visual.aggregation)

    # 7. Sort / Top-N.
    order_col = (visual.order_by or visual.y) if (visual.sort is None) else visual.sort.column
    ascending = (visual.sort.direction == "asc") if visual.sort else (visual.order == "asc")

    if visual.limit:
        # Top-N ranks by the measure regardless of display sort.
        rank_col = visual.order_by or visual.y
        result = result.sort_values(rank_col, ascending=visual.order == "asc").head(visual.limit)
        result = result.sort_values(rank_col, ascending=ascending)
    elif visual.sort:
        result = result.sort_values(order_col, ascending=ascending)
    elif visual.type in ("bar", "column", "pie", "donut"):
        # Sensible default: largest first for categorical comparisons.
        result = result.sort_values(visual.y, ascending=False)
    elif dimension in profile.date_columns() or dimension in dates.DATE_PARTS:
        # Time series should read left-to-right in chronological order.
        result = result.sort_values(dimension, ascending=True)

    return QueryResult(df=result.reset_index(drop=True), x=dimension, y=visual.y, kind="aggregated")


def _choose_dimension(visual: VisualPlan, profile: DatasetProfile) -> str:
    if visual.x:
        return visual.x
    if visual.hierarchy:
        resolved = hierarchy.resolve_hierarchy(profile, visual.hierarchy)
        if resolved:
            return resolved[0]
    raise ValueError("Visual has no dimension to group by.")


def _date_grain(visual: VisualPlan, profile: DatasetProfile, dimension: str) -> Optional[str]:
    if visual.date_part:
        return visual.date_part
    # Default a time-series line to Month grain when grouped on a raw date.
    if visual.type in ("line", "area") and dimension in profile.date_columns():
        return "Month"
    return None

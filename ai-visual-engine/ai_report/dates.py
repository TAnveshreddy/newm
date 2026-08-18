"""Robust date parsing and date-hierarchy derivation (requirement #3).

Replaces the fragile ``pd.to_datetime(..., errors="ignore")`` from the
prototype with a resilient parser that:

* tries several common explicit formats,
* falls back to pandas inference with ``errors="coerce"`` (never raises),
* reports how many values could not be parsed,
* refuses to treat a column as a date if too few values parse.
"""
from __future__ import annotations

from typing import Tuple

import pandas as pd

from .errors import DateParseError

COMMON_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%b %d %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %b %Y",
    "%Y-%m-%d %H:%M:%S",
]

# Minimum fraction of non-null values that must parse for a column to count as a date.
DATE_CONFIDENCE = 0.8

DATE_PARTS = ["Year", "Quarter", "Month", "Week", "Day"]


def parse_dates(series: pd.Series) -> Tuple[pd.Series, int]:
    """Parse a series to datetime robustly.

    Returns ``(parsed_series, invalid_count)``. Values that cannot be parsed
    become ``NaT`` rather than raising.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return series, int(series.isna().sum())

    non_null = series.dropna()
    if non_null.empty:
        return pd.to_datetime(series, errors="coerce"), 0

    # Fill each row with whichever known format parses it, so a column with
    # MIXED formats (e.g. ISO + US + "Jan 04 2025") is parsed row-by-row.
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in COMMON_FORMATS:
        mask = result.isna() & series.notna()
        if not mask.any():
            break
        try:
            attempt = pd.to_datetime(series[mask], format=fmt, errors="coerce")
        except (ValueError, TypeError):
            continue
        result.loc[mask] = attempt

    # Final fallback: dateutil per-element for anything still unparsed.
    mask = result.isna() & series.notna()
    if mask.any():
        try:
            attempt = pd.to_datetime(series[mask], errors="coerce", format="mixed")
        except (ValueError, TypeError):
            attempt = pd.to_datetime(series[mask], errors="coerce")
        result.loc[mask] = attempt

    invalid = int((result.isna() & series.notna()).sum())
    return result, invalid


def looks_like_date(series: pd.Series, sample: int = 200) -> bool:
    """Heuristic: does this column reliably parse as dates?"""
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if pd.api.types.is_numeric_dtype(series):
        return False  # avoid treating plain numbers/years-as-int as dates here
    non_null = series.dropna().astype(str).head(sample)
    if non_null.empty:
        return False
    parsed, _ = parse_dates(non_null)
    ratio = parsed.notna().mean()
    return bool(ratio >= DATE_CONFIDENCE)


def parse_or_raise(series: pd.Series) -> pd.Series:
    """Parse dates, raising DateParseError if the column is not date-like."""
    parsed, _ = parse_dates(series)
    if parsed.notna().mean() < DATE_CONFIDENCE:
        raise DateParseError("Column could not be reliably parsed as a date.")
    return parsed


def derive_part(dt: pd.Series, part: str) -> pd.Series:
    """Derive a date-hierarchy part from a datetime series."""
    part = part.capitalize()
    if part == "Year":
        return dt.dt.year
    if part == "Quarter":
        return dt.dt.year.astype("Int64").astype(str) + "-Q" + dt.dt.quarter.astype("Int64").astype(str)
    if part == "Month":
        return dt.dt.strftime("%Y-%m")
    if part == "Week":
        return dt.dt.strftime("%Y-W%V")
    if part == "Day":
        return dt.dt.strftime("%Y-%m-%d")
    raise DateParseError(f"Unknown date part: {part}")

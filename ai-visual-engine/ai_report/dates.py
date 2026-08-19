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

try:
    from pandas.errors import OutOfBoundsDatetime
except Exception:  # pragma: no cover - very old pandas
    OutOfBoundsDatetime = Exception

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


def _coerce_ns(parsed: pd.Series) -> pd.Series:
    """Coerce any parsed datetime series to datetime64[ns].

    Out-of-range dates (e.g. year 1 or year 9999, which fit other resolutions
    but overflow nanoseconds) become NaT instead of raising — pandas 3 otherwise
    crashes when such a value is forced into a datetime64[ns] block.
    """
    if not pd.api.types.is_datetime64_any_dtype(parsed):
        parsed = pd.to_datetime(parsed, errors="coerce")
    try:
        return parsed.astype("datetime64[ns]")
    except (OutOfBoundsDatetime, OverflowError, ValueError, TypeError):
        def clamp(v):
            if pd.isna(v):
                return pd.NaT
            try:
                return pd.Timestamp(v).as_unit("ns")
            except (OutOfBoundsDatetime, OverflowError, ValueError, TypeError):
                return pd.NaT
        return pd.to_datetime(parsed.map(clamp), errors="coerce").astype("datetime64[ns]")


def _safe_parse(values: pd.Series, **kwargs) -> pd.Series:
    """Vectorized to_datetime that never raises and never overflows ns."""
    try:
        parsed = pd.to_datetime(values, errors="coerce", **kwargs)
    except (ValueError, TypeError, OutOfBoundsDatetime, OverflowError):
        parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    return _coerce_ns(parsed)


def parse_dates(series: pd.Series) -> Tuple[pd.Series, int]:
    """Parse a series to datetime robustly.

    Returns ``(parsed_series, invalid_count)``. Values that cannot be parsed —
    or that are out of the representable range — become ``NaT`` rather than
    raising.
    """
    orig_notna = series.notna()
    if pd.api.types.is_datetime64_any_dtype(series):
        result = _coerce_ns(series)
        return result, int((result.isna() & orig_notna).sum())

    if not orig_notna.any():
        return pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]"), 0

    # Fill each row with whichever known format parses it, so a column with
    # MIXED formats (e.g. ISO + US + "Jan 04 2025") is parsed row-by-row. Every
    # attempt is clamped to datetime64[ns] (out-of-range -> NaT) before assign.
    result = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    for fmt in COMMON_FORMATS:
        mask = result.isna() & orig_notna
        if not mask.any():
            break
        result.loc[mask] = _safe_parse(series[mask], format=fmt)

    mask = result.isna() & orig_notna
    if mask.any():
        result.loc[mask] = _safe_parse(series[mask], format="mixed")

    invalid = int((result.isna() & orig_notna).sum())
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

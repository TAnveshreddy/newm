"""Common data-cleaning layer (requirement #4).

Conservative on purpose: it normalises obvious junk (empty strings -> NaN),
drops exact duplicate rows, and reports what it did — it does NOT silently
delete data or drop rows with nulls.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict

import pandas as pd


@dataclass
class CleaningReport:
    rows_received: int
    rows_processed: int
    null_values: int
    duplicates_removed: int

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    rows_received = len(df)
    out = df.copy()

    # Normalise empty / whitespace-only strings to NaN so they count as nulls.
    # (Handle both legacy 'object' and pandas-3 'str' dtypes robustly.)
    for col in out.columns:
        series = out[col]
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            out[col] = series.map(lambda v: pd.NA if isinstance(v, str) and v.strip() == "" else v)

    # Drop exact duplicate rows (report how many).
    before = len(out)
    out = out.drop_duplicates().reset_index(drop=True)
    duplicates_removed = before - len(out)

    null_values = int(out.isna().sum().sum())

    report = CleaningReport(
        rows_received=rows_received,
        rows_processed=len(out),
        null_values=null_values,
        duplicates_removed=duplicates_removed,
    )
    return out, report

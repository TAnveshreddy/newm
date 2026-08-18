"""Dataset loading (CSV / Excel / folder) — requirement #17 backward compat.

Same behaviour as the prototype's ``load_data``, with clearer errors.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from .errors import DataLoadError


def load_data(path) -> Dict[str, pd.DataFrame]:
    p = Path(path)
    datasets: Dict[str, pd.DataFrame] = {}

    if p.is_file():
        _load_file(p, datasets)
    elif p.is_dir():
        files = list(p.glob("*.csv")) + list(p.glob("*.xlsx")) + list(p.glob("*.xls"))
        if not files:
            raise DataLoadError(f"No CSV or Excel files found in folder: {p}")
        for f in files:
            _load_file(f, datasets, prefix=f.stem)
    else:
        raise DataLoadError(f"Path does not exist: {p}")

    return datasets


def _load_file(f: Path, datasets: Dict[str, pd.DataFrame], prefix: str | None = None) -> None:
    suffix = f.suffix.lower()
    if suffix == ".csv":
        datasets[f.stem] = pd.read_csv(f)
    elif suffix in (".xlsx", ".xls"):
        sheets = pd.read_excel(f, sheet_name=None)
        for sheet_name, df in sheets.items():
            name = f"{prefix}_{sheet_name}" if prefix else sheet_name
            datasets[name] = df
    else:
        raise DataLoadError(f"Unsupported file type: {f.suffix}")

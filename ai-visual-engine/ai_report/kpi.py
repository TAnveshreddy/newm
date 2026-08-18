"""KPI + calculated-metric computation (requirement #10)."""
from __future__ import annotations

from typing import Dict

import pandas as pd

from . import aggregations
from .schema import VisualPlan


def compute_kpi(df: pd.DataFrame, visual: VisualPlan) -> float:
    """Compute a single KPI value.

    * If the visual has an ``expression`` (e.g. Profit Margin), each referenced
      measure is aggregated (with the visual's aggregation, default sum) and the
      arithmetic is applied to the totals.
    * Otherwise the single measure ``y`` is aggregated.
    """
    if visual.expression:
        cols = aggregations.extract_expression_columns(visual.expression)
        totals: Dict[str, float] = {
            c: aggregations.scalar_aggregate(df[c], visual.aggregation) for c in cols
        }
        return aggregations.evaluate_expression(visual.expression, totals)

    if not visual.y:
        raise ValueError("KPI requires a measure (y) or an expression.")
    return aggregations.scalar_aggregate(df[visual.y], visual.aggregation)


def kpi_label(visual: VisualPlan) -> str:
    if visual.title:
        return visual.title
    if visual.measure_name:
        return visual.measure_name
    if visual.y:
        return f"{visual.aggregation.upper()} of {visual.y}"
    return "KPI"

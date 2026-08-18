"""Power BI-compatible visual specification (requirement #13).

Separates the internal VisualPlan from the output format so the same plan can
drive PNG rendering today and a Power BI / web frontend tomorrow.
"""
from __future__ import annotations

from typing import Any, Dict

from .schema import VisualPlan

# Internal type -> Power BI visual type name.
_PBI_TYPE = {
    "bar": "clusteredBarChart",
    "column": "clusteredColumnChart",
    "line": "lineChart",
    "area": "areaChart",
    "pie": "pieChart",
    "donut": "donutChart",
    "scatter": "scatterChart",
    "histogram": "histogram",
    "kpi": "card",
    "table": "tableEx",
}

_PBI_AGG = {
    "sum": "Sum",
    "avg": "Average",
    "mean": "Average",
    "min": "Min",
    "max": "Max",
    "count": "Count",
    "distinct_count": "CountNonNull",
    "none": "None",
}


def to_powerbi_spec(visual: VisualPlan) -> Dict[str, Any]:
    spec: Dict[str, Any] = {
        "visualType": _PBI_TYPE.get(visual.type, "clusteredBarChart"),
        "title": visual.title,
        "category": visual.x,
        "measure": visual.measure_name or visual.y,
        "aggregation": _PBI_AGG.get(visual.aggregation, "Sum"),
        "filters": [f.to_dict() for f in visual.filters],
    }
    if visual.expression:
        spec["calculatedMeasure"] = {
            "name": visual.measure_name or "Calculated",
            "expression": visual.expression,
        }
    if visual.sort:
        spec["sort"] = visual.sort.to_dict()
    if visual.limit:
        spec["topN"] = {"count": visual.limit, "order": visual.order, "by": visual.order_by or visual.y}
    if visual.hierarchy:
        spec["hierarchy"] = visual.hierarchy
    if visual.date_part:
        spec["dateGrain"] = visual.date_part
    return spec

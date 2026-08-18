"""Structured intermediate representation + JSON schema (requirements #11, #13).

The LLM (or the offline rule planner) produces JSON matching these shapes. It
NEVER produces Python plotting code. Everything is validated against this schema
before anything executes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .errors import SchemaError

VISUAL_TYPES = {"bar", "column", "line", "area", "pie", "donut", "scatter", "histogram", "kpi", "table"}
AGGREGATIONS = {"sum", "avg", "mean", "min", "max", "count", "distinct_count", "none"}
OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "in", "not in", "between", "contains"}
SORT_DIRECTIONS = {"asc", "desc"}


@dataclass
class Filter:
    column: str
    operator: str
    value: Any

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Filter":
        if not isinstance(d, dict):
            raise SchemaError("Filter must be an object.")
        col = d.get("column") or d.get("field")
        op = str(d.get("operator", "=")).lower()
        if not col:
            raise SchemaError("Filter is missing 'column'.")
        if op not in OPERATORS:
            raise SchemaError(f"Unsupported filter operator: {op}")
        return Filter(column=str(col), operator=op, value=d.get("value"))

    def to_dict(self) -> Dict[str, Any]:
        return {"column": self.column, "operator": self.operator, "value": self.value}


@dataclass
class Sort:
    column: str
    direction: str = "desc"

    @staticmethod
    def from_dict(d: Optional[Dict[str, Any]]) -> Optional["Sort"]:
        if not d:
            return None
        direction = str(d.get("direction", "desc")).lower()
        if direction not in SORT_DIRECTIONS:
            raise SchemaError(f"Unsupported sort direction: {direction}")
        col = d.get("column")
        if not col:
            raise SchemaError("Sort is missing 'column'.")
        return Sort(column=str(col), direction=direction)

    def to_dict(self) -> Dict[str, Any]:
        return {"column": self.column, "direction": self.direction}


@dataclass
class VisualPlan:
    type: str
    dataset: str
    x: Optional[str] = None            # dimension / category
    y: Optional[str] = None            # measure
    aggregation: str = "sum"
    filters: List[Filter] = field(default_factory=list)
    sort: Optional[Sort] = None
    limit: Optional[int] = None        # Top-N
    order_by: Optional[str] = None     # measure to rank by for Top-N (defaults to y)
    order: str = "desc"                # desc = Top, asc = Bottom
    hierarchy: List[str] = field(default_factory=list)
    date_part: Optional[str] = None    # Year|Quarter|Month|Week|Day
    expression: Optional[str] = None   # calculated measure, e.g. "(Revenue-Cost)/Revenue"
    measure_name: Optional[str] = None # label for a calculated measure / KPI
    title: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "VisualPlan":
        if not isinstance(d, dict):
            raise SchemaError("Visual must be an object.")
        vtype = str(d.get("type", "")).lower()
        if vtype not in VISUAL_TYPES:
            raise SchemaError(f"Unsupported visual type: {d.get('type')}")
        agg = str(d.get("aggregation", "sum")).lower()
        if agg not in AGGREGATIONS:
            raise SchemaError(f"Unsupported aggregation: {agg}")
        limit = d.get("limit") or d.get("top_n")
        if limit is not None:
            try:
                limit = int(limit)
            except (TypeError, ValueError):
                raise SchemaError("limit/top_n must be an integer.")
        return VisualPlan(
            type=vtype,
            dataset=str(d.get("dataset", "")),
            x=_opt_str(d.get("x") or d.get("category") or d.get("dimension")),
            y=_opt_str(d.get("y") or d.get("measure")),
            aggregation=agg,
            filters=[Filter.from_dict(f) for f in (d.get("filters") or [])],
            sort=Sort.from_dict(d.get("sort")),
            limit=limit,
            order_by=_opt_str(d.get("order_by")),
            order=str(d.get("order", "desc")).lower(),
            hierarchy=[str(h) for h in (d.get("hierarchy") or [])],
            date_part=_opt_str(d.get("date_part")),
            expression=_opt_str(d.get("expression")),
            measure_name=_opt_str(d.get("measure_name") or d.get("name")),
            title=str(d.get("title", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"type": self.type, "dataset": self.dataset}
        for k in ("x", "y", "date_part", "expression", "measure_name"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        d["aggregation"] = self.aggregation
        if self.filters:
            d["filters"] = [f.to_dict() for f in self.filters]
        if self.sort:
            d["sort"] = self.sort.to_dict()
        if self.limit is not None:
            d["limit"] = self.limit
            d["order"] = self.order
            if self.order_by:
                d["order_by"] = self.order_by
        if self.hierarchy:
            d["hierarchy"] = self.hierarchy
        d["title"] = self.title
        return d


@dataclass
class ReportPlan:
    title: str
    visuals: List[VisualPlan]
    description: str = ""

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "ReportPlan":
        if not isinstance(d, dict):
            raise SchemaError("Report plan must be a JSON object.")
        visuals = d.get("visuals")
        if not isinstance(visuals, list) or not visuals:
            raise SchemaError("Report plan must contain a non-empty 'visuals' list.")
        return ReportPlan(
            title=str(d.get("title", "Report")),
            description=str(d.get("description", "")),
            visuals=[VisualPlan.from_dict(v) for v in visuals],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "visuals": [v.to_dict() for v in self.visuals],
        }


def _opt_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None

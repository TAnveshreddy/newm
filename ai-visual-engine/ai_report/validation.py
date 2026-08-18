"""Semantic-metadata validation (requirements #11, #12, #20).

After a plan passes the structural schema, every column / measure it references
is checked against the dataset's semantic metadata. Invalid plans are rejected
BEFORE execution — the LLM can never cause a hallucinated column to run.
"""
from __future__ import annotations

from typing import Dict, List

from .dates import DATE_PARTS
from .errors import SemanticError
from .profiler import DatasetProfile
from .schema import VisualPlan

# Visual types that need a measure (y).
NEEDS_MEASURE = {"bar", "column", "line", "area", "pie", "donut", "kpi", "scatter"}
# Visual types that need a category/dimension (x).
NEEDS_DIMENSION = {"bar", "column", "line", "area", "pie", "donut", "histogram"}


def valid_columns(profile: DatasetProfile) -> Dict[str, str]:
    """Map of valid column name -> semantic type, including derived date parts."""
    cols = {c.name: c.semantic_type for c in profile.columns}
    if profile.date_columns():
        for part in DATE_PARTS:
            cols.setdefault(part, "dimension")
    return cols


def validate_visual(visual: VisualPlan, profiles: Dict[str, DatasetProfile]) -> None:
    """Raise SemanticError if the visual references anything that does not exist
    or uses a column in an invalid way."""
    if visual.dataset not in profiles:
        raise SemanticError(
            f"Dataset '{visual.dataset}' not found. Available: {list(profiles)}."
        )
    profile = profiles[visual.dataset]
    cols = valid_columns(profile)
    measures = set(profile.measures())

    def require(col: str, what: str) -> None:
        if col not in cols:
            raise SemanticError(
                f"{what} '{col}' does not exist in dataset '{visual.dataset}'."
            )

    # Dimension / category
    if visual.x:
        require(visual.x, "Column")
    elif visual.type in NEEDS_DIMENSION and not visual.hierarchy:
        raise SemanticError(f"Visual '{visual.title or visual.type}' requires a dimension (x).")

    # Measure / y
    if visual.expression:
        _validate_expression(visual.expression, measures, visual.dataset)
    elif visual.y:
        require(visual.y, "Measure")
        if visual.aggregation != "count" and visual.y not in measures and visual.type != "table":
            # count works on any column; other aggs need a numeric measure
            raise SemanticError(
                f"Column '{visual.y}' is not a numeric measure and cannot be aggregated with "
                f"'{visual.aggregation}'."
            )
    elif visual.type in NEEDS_MEASURE:
        raise SemanticError(f"Visual '{visual.title or visual.type}' requires a measure (y).")

    # Filters
    for f in visual.filters:
        require(f.column, "Filter column")

    # Sort / order_by
    if visual.sort:
        require(visual.sort.column, "Sort column")
    if visual.order_by:
        require(visual.order_by, "Order-by column")

    # Hierarchy
    for level in visual.hierarchy:
        require(level, "Hierarchy level")


def _validate_expression(expr: str, measures: set, dataset: str) -> None:
    """Ensure a calculated-measure expression references only known measures and
    safe arithmetic (delegated to aggregations for the real parse)."""
    from .aggregations import extract_expression_columns  # local import to avoid cycle

    used = extract_expression_columns(expr)
    for col in used:
        if col not in measures:
            raise SemanticError(
                f"Calculated expression references '{col}', which is not a measure in "
                f"dataset '{dataset}'."
            )


def validate_plan(visuals: List[VisualPlan], profiles: Dict[str, DatasetProfile]) -> List[str]:
    """Validate every visual. Returns a list of error strings (one per invalid
    visual) without raising, so the orchestrator can skip only the bad ones."""
    errors: List[str] = []
    for v in visuals:
        try:
            validate_visual(v, profiles)
        except SemanticError as e:
            errors.append(str(e))
    return errors

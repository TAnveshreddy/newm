"""Aggregations + safe calculated-measure expressions (requirements #10).

Calculated measures are evaluated with a restricted AST evaluator — only
arithmetic over known measure names is allowed. Arbitrary Python is never
executed (requirement #20).
"""
from __future__ import annotations

import ast
from typing import Dict, List

import pandas as pd

from .errors import ExpressionError

# Canonical aggregation name -> pandas method.
_AGG_METHOD = {
    "sum": "sum",
    "avg": "mean",
    "mean": "mean",
    "min": "min",
    "max": "max",
    "count": "count",
    "distinct_count": "nunique",
}


def aggregate(df: pd.DataFrame, group_cols: List[str], measure: str, aggregation: str) -> pd.DataFrame:
    """Group by ``group_cols`` and aggregate ``measure``."""
    method = _AGG_METHOD.get(aggregation, "sum")
    if not group_cols:
        value = _apply_scalar(df[measure], method)
        return pd.DataFrame({measure: [value]})
    grouped = df.groupby(group_cols, dropna=False)[measure]
    result = getattr(grouped, method)().reset_index()
    return result


def scalar_aggregate(series: pd.Series, aggregation: str) -> float:
    return _apply_scalar(series, _AGG_METHOD.get(aggregation, "sum"))


def _apply_scalar(series: pd.Series, method: str):
    if method == "nunique":
        return int(series.nunique(dropna=True))
    if method == "count":
        return int(series.count())
    return getattr(series, method)()


# ---------------------------------------------------------------------------
# Safe expression evaluation for calculated measures
# ---------------------------------------------------------------------------

_ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)


def extract_expression_columns(expr: str) -> List[str]:
    """Return the column names referenced by an arithmetic expression, after
    validating the expression only uses allowed operations."""
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(f"Invalid expression: {e}") from e
    names: List[str] = []
    _walk(tree.body, names)
    return names


def _walk(node, names: List[str]) -> None:
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise ExpressionError("Only +, -, *, / are allowed in expressions.")
        _walk(node.left, names)
        _walk(node.right, names)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        _walk(node.operand, names)
    elif isinstance(node, ast.Name):
        names.append(node.id)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        pass
    else:
        raise ExpressionError("Expression contains a disallowed element.")


def evaluate_expression(expr: str, values: Dict[str, float]) -> float:
    """Evaluate the arithmetic expression given pre-aggregated measure values."""
    tree = ast.parse(expr, mode="eval")
    return _eval(tree.body, values)


def _eval(node, values: Dict[str, float]) -> float:
    if isinstance(node, ast.BinOp):
        left = _eval(node.left, values)
        right = _eval(node.right, values)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right if right else float("nan")
    if isinstance(node, ast.UnaryOp):
        v = _eval(node.operand, values)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.Name):
        if node.id not in values:
            raise ExpressionError(f"Unknown column in expression: {node.id}")
        return float(values[node.id])
    if isinstance(node, ast.Constant):
        return float(node.value)
    raise ExpressionError("Disallowed expression element.")

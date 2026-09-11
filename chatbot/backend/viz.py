"""
viz.py
------
Choose and configure the visualization for a query result.

If the user asked for a specific chart type, honour it.  Otherwise pick the most
appropriate visual from the data shape and the business question, following the
same rules a BI analyst would (time -> line, few categories -> column, part of a
whole -> donut, many rows -> table, etc.).

Emits a normalized ``viz`` spec that the frontend renders with Chart.js (plus a
few HTML-rendered visuals: card, table, matrix).
"""
from __future__ import annotations

import re
from typing import Optional

from semantic_model import SemanticModel
from nl_planner import QueryIntent
from query_engine import QueryResult

# Map requested/explicit types to canonical renderer types the frontend knows.
CANON = {
    "bar": "bar", "column": "column", "stackedBar": "stackedBar", "stackedColumn": "stackedColumn",
    "line": "line", "area": "area", "pie": "pie", "donut": "donut",
    "scatter": "scatter", "combo": "combo", "table": "table", "matrix": "matrix",
    "card": "card", "gauge": "gauge", "funnel": "funnel", "waterfall": "waterfall",
    "treemap": "treemap", "map": "map",
}

FMT_LABEL = {"currency": "Currency", "percent": "Percent", "int": "Whole number", "number": "Number"}


def select_visualization(model: SemanticModel, intent: QueryIntent, result: QueryResult) -> dict:
    if result.error:
        return {"chartType": "error", "title": "Error", "message": result.error}

    explicit = CANON.get(intent.chart_type) if intent.chart_type else None
    measures = result.measures
    n_rows = len(result.rows)

    # KPI cards
    if not result.dimension:
        return _cards(model, intent, result)

    chart = explicit or _auto_chart(model, intent, result)

    title = _title(model, intent, result)
    labels = [_str(r.get(result.columns[0]["name"])) for r in result.rows]

    if chart in ("table", "matrix"):
        return {
            "chartType": chart, "title": title,
            "table": {"columns": result.columns, "rows": _format_rows(model, result)},
            "explanation": _explain(model, intent, result, chart),
        }

    # series (secondary dimension) -> one dataset per series value
    datasets = _build_datasets(model, intent, result, chart)

    spec = {
        "chartType": chart,
        "title": title,
        "labels": labels if not result.series_field else _series_labels(result),
        "datasets": datasets,
        "measures": [{"name": m, "format": model.measures[m].fmt} for m in measures],
        "table": {"columns": result.columns, "rows": _format_rows(model, result)},
        "explanation": _explain(model, intent, result, chart),
    }
    return spec


def _auto_chart(model: SemanticModel, intent: QueryIntent, result: QueryResult) -> str:
    # time series -> line
    if result.period_field:
        return "line"
    dim = model.dimensions.get(result.dimension)
    n = len(result.rows)
    first_measure = model.measures[result.measures[0]]
    low = intent.raw.lower()
    # part-to-whole cues
    if any(w in low for w in ("contribution", "share", "proportion", "mix", "split", "breakdown by")) \
            and n <= 8 and len(result.measures) == 1:
        return "donut"
    # many categories or explicit ranking -> horizontal bar / table
    if n > 12:
        return "table" if n > 25 else "bar"
    if intent.top_n:
        return "bar"
    # default: vertical column for categorical
    return "column"


def _cards(model: SemanticModel, intent: QueryIntent, result: QueryResult) -> dict:
    row = result.rows[0] if result.rows else {}
    cards = []
    for m in result.measures:
        meas = model.measures[m]
        cards.append({
            "label": m,
            "value": row.get(m),
            "format": meas.fmt,
            "definition": meas.definition,
        })
    return {
        "chartType": "card", "title": _title(model, intent, result),
        "cards": cards,
        "explanation": _explain(model, intent, result, "card"),
    }


def _build_datasets(model, intent, result, chart) -> list[dict]:
    if result.series_field:
        # pivot: rows are (period/category, series) -> build one dataset per series
        cat_field = result.columns[0]["name"]
        series_field = result.series_field
        measure = result.measures[0]
        cats: list = []
        for r in result.rows:
            c = _str(r.get(cat_field))
            if c not in cats:
                cats.append(c)
        series_vals: list = []
        for r in result.rows:
            s = _str(r.get(series_field))
            if s not in series_vals:
                series_vals.append(s)
        datasets = []
        for s in series_vals:
            data = []
            for c in cats:
                match = next((r for r in result.rows if _str(r.get(cat_field)) == c
                              and _str(r.get(series_field)) == s), None)
                data.append(_num(match.get(measure)) if match else None)
            datasets.append({"label": s, "data": data, "format": model.measures[measure].fmt})
        return datasets
    # one dataset per measure
    datasets = []
    for i, m in enumerate(result.measures):
        datasets.append({
            "label": m,
            "data": [_num(r.get(m)) for r in result.rows],
            "format": model.measures[m].fmt,
            "kind": "line" if (chart == "combo" and i > 0) else None,
        })
    return datasets


def _series_labels(result: QueryResult) -> list:
    cat_field = result.columns[0]["name"]
    out = []
    for r in result.rows:
        c = _str(r.get(cat_field))
        if c not in out:
            out.append(c)
    return out


def _format_rows(model: SemanticModel, result: QueryResult) -> list[dict]:
    out = []
    for r in result.rows:
        nr = {}
        for col in result.columns:
            name = col["name"]
            val = r.get(name)
            nr[name] = val
        out.append(nr)
    return out


def _title(model, intent, result) -> str:
    ms = " & ".join(result.measures)
    if not result.dimension:
        return ms
    dim_label = result.columns[0]["name"] if result.columns else result.dimension
    base = f"{ms} by {dim_label}"
    yf = next((f for f in intent.filters if f["field"] == "Year"), None)
    if yf:
        base += f" ({', '.join(str(v) for v in yf['values'])})"
    if intent.top_n:
        base = f"Top {abs(intent.top_n)} " + base
    return base


def _explain(model, intent, result, chart) -> str:
    if not result.rows:
        return "No data matched your request for the selected filters."
    if not result.dimension:
        parts = []
        for m in result.measures:
            parts.append(f"{m} is {_human(model.measures[m].fmt, result.rows[0].get(m))}")
        return "; ".join(parts) + "."
    order_m = result.measures[0]
    if result.period_field:
        vals = [r.get(order_m) for r in result.rows if r.get(order_m) is not None]
        if len(vals) >= 2 and vals[0] not in (None, 0):
            trend = "up" if vals[-1] >= vals[0] else "down"
            return (f"{order_m} across {len(result.rows)} periods, trending {trend} "
                    f"from {_human(model.measures[order_m].fmt, vals[0])} to "
                    f"{_human(model.measures[order_m].fmt, vals[-1])}.")
        return f"{order_m} over {len(result.rows)} periods."
    top = result.rows[0]
    dim_field = result.columns[0]["name"]
    n_cats = len({r.get(dim_field) for r in result.rows})
    pretty = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", chart).lower()
    tail = (f" broken down by {result.series_field.lower()}" if result.series_field else "")
    return (f"Top {dim_field.lower()} is {top.get(dim_field)} at "
            f"{_human(model.measures[order_m].fmt, top.get(order_m))}. "
            f"Showing {n_cats} {dim_field.lower()} values{tail} as a {pretty} chart.")


# ---------- formatting helpers ----------
def _human(fmt: str, v) -> str:
    if v is None:
        return "n/a"
    if fmt == "currency":
        return f"${v:,.0f}"
    if fmt == "percent":
        return f"{v*100:,.1f}%"
    if fmt == "int":
        return f"{v:,.0f}"
    return f"{v:,.2f}"


def _num(v):
    if v is None:
        return None
    try:
        return round(float(v), 4)
    except (TypeError, ValueError):
        return None


def _str(v):
    return "(blank)" if v is None else str(v)

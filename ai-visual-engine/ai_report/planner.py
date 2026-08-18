"""Natural-language -> Visual JSON planner (requirements #11, #14, #20).

Two backends:

* **LLM mode** (when ``LLM_API_KEY`` is set): sends the semantic metadata + the
  user prompt to an OpenAI-compatible chat model and parses the JSON plan.
* **Rule mode** (default / offline): a deterministic parser that turns common
  business questions into a plan. This keeps the engine fully runnable and
  testable without any API key.

Either way the output is JSON validated against schema.py — the LLM never emits
Python code.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

from . import profiler
from .profiler import DatasetProfile
from .schema import Filter, ReportPlan, Sort, VisualPlan

MEASURE_SYNONYMS = {
    "revenue": ["revenue", "sales", "amount", "turnover"],
    "cost": ["cost", "expense", "spend"],
    "quantity": ["quantity", "qty", "units", "volume"],
    "profit": ["profit"],
}

SYSTEM_PROMPT = """You are an expert BI reporting assistant.
Convert the user's natural-language request into a JSON report plan.
Use ONLY the datasets, columns and measures in the provided semantic metadata.
Never invent columns. Return ONLY valid JSON of the form:
{"title": "...", "visuals": [ {"type": "...", "dataset": "...", "x": "...", "y": "...",
"aggregation": "sum|avg|min|max|count|distinct_count", "filters": [...],
"sort": {"column": "...", "direction": "asc|desc"}, "limit": N, "title": "..."} ]}"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plan_report(prompt: str, profiles: Dict[str, DatasetProfile]) -> ReportPlan:
    if os.getenv("LLM_API_KEY"):
        try:
            return _plan_with_llm(prompt, profiles)
        except Exception:
            # Fall back to the deterministic planner on any LLM failure.
            pass
    return _plan_with_rules(prompt, profiles)


# ---------------------------------------------------------------------------
# LLM backend
# ---------------------------------------------------------------------------

def _plan_with_llm(prompt: str, profiles: Dict[str, DatasetProfile]) -> ReportPlan:
    from openai import OpenAI  # imported lazily

    client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL") or None)
    metadata = {name: p.semantic_metadata() for name, p in profiles.items()}
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4.1"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"SEMANTIC METADATA:\n{json.dumps(metadata, default=str)}\n\nREQUEST:\n{prompt}"},
        ],
    )
    data = json.loads(resp.choices[0].message.content)
    return ReportPlan.from_dict(data)


# ---------------------------------------------------------------------------
# Rule backend
# ---------------------------------------------------------------------------

def _plan_with_rules(prompt: str, profiles: Dict[str, DatasetProfile]) -> ReportPlan:
    dataset = _pick_dataset(prompt, profiles)
    profile = profiles[dataset]
    clauses = _split_clauses(prompt)
    visuals: List[VisualPlan] = []
    for clause in clauses:
        v = _clause_to_visual(clause, dataset, profile)
        if v:
            visuals.append(v)
    if not visuals:
        # Fallback: a KPI of the first measure, or a table.
        measures = profile.measures()
        if measures:
            visuals.append(VisualPlan(type="kpi", dataset=dataset, y=measures[0],
                                      aggregation="sum", title=f"Total {measures[0]}"))
        else:
            visuals.append(VisualPlan(type="table", dataset=dataset, title="Data"))
    return ReportPlan(title=_report_title(prompt), visuals=visuals)


def _pick_dataset(prompt: str, profiles: Dict[str, DatasetProfile]) -> str:
    low = prompt.lower()
    for name in profiles:
        if name.lower() in low:
            return name
    return next(iter(profiles))


def _split_clauses(prompt: str) -> List[str]:
    low = prompt.lower()
    # Strip a leading "create a ... dashboard/report showing" preamble.
    m = re.search(r"(?:showing|with|of|:)\s+(.*)$", low)
    body = m.group(1) if (m and re.search(r"dashboard|report|showing", low)) else low
    # Split on commas and the word "and".
    parts = re.split(r",|\band\b", body)
    parts = [p.strip() for p in parts if p.strip()]
    # If the split produced fragments with no measure signal, treat as single clause.
    meaningful = [p for p in parts if _has_signal(p)]
    if len(meaningful) >= 2:
        return meaningful
    return [low]


def _has_signal(clause: str) -> bool:
    keywords = ["revenue", "sales", "cost", "profit", "margin", "quantity", "count",
                "total", "trend", "top", "bottom", "by ", "distribution"]
    return any(k in clause for k in keywords)


def _report_title(prompt: str) -> str:
    p = prompt.strip().rstrip(".")
    return (p[:1].upper() + p[1:]) if p else "Report"


def _clause_to_visual(clause: str, dataset: str, profile: DatasetProfile) -> Optional[VisualPlan]:
    clause = clause.lower()
    measure, expression, agg = _find_measure(clause, profile)
    dimension, date_part = _find_dimension(clause, profile)
    filters = _find_filters(clause, profile)
    limit, order = _find_topn(clause)
    sort = _find_sort(clause, measure)
    vtype = _pick_type(clause, dimension, date_part, measure)

    if vtype == "kpi":
        dimension, date_part = None, None

    if vtype in ("bar", "column", "line", "area", "pie", "donut") and not dimension:
        # Needs a dimension; degrade to KPI if we at least have a measure.
        if measure or expression:
            vtype = "kpi"
        else:
            return None

    title = _make_title(measure, expression, dimension, filters, vtype)
    return VisualPlan(
        type=vtype, dataset=dataset,
        x=dimension, y=measure, aggregation=agg,
        filters=filters, sort=sort, limit=limit, order_by=measure, order=order,
        date_part=date_part, expression=expression,
        measure_name=("Profit Margin" if expression else None), title=title,
    )


def _find_measure(clause, profile):
    measures = profile.measures()
    lower_map = {m.lower(): m for m in measures}

    # Profit margin -> calculated expression (if Revenue & Cost exist).
    if "margin" in clause:
        rev = _match_measure(["revenue", "sales"], lower_map)
        cost = _match_measure(["cost"], lower_map)
        if rev and cost:
            return None, f"({rev} - {cost}) / {rev}", "sum"

    # Profit -> Profit measure, else Revenue - Cost expression.
    if "profit" in clause and "margin" not in clause:
        if _match_measure(["profit"], lower_map):
            return _match_measure(["profit"], lower_map), None, _agg_from_clause(clause)
        rev = _match_measure(["revenue", "sales"], lower_map)
        cost = _match_measure(["cost"], lower_map)
        if rev and cost:
            return None, f"{rev} - {cost}", "sum"

    # Count of customers / distinct customers -> count on an identifier/dimension.
    if "customer" in clause and ("count" in clause or "distinct" in clause or "number of" in clause):
        ident = next((c.name for c in profile.columns if "customer" in c.name.lower()), None)
        if ident:
            agg = "distinct_count" if "distinct" in clause or "unique" in clause else "count"
            return ident, None, agg

    # Standard synonym match.
    for canonical, words in MEASURE_SYNONYMS.items():
        if any(w in clause for w in words):
            hit = _match_measure(words + [canonical], lower_map)
            if hit:
                return hit, None, _agg_from_clause(clause)

    # Direct measure-name mention.
    for lname, real in lower_map.items():
        if lname in clause:
            return real, None, _agg_from_clause(clause)

    # Default to the first measure if the clause clearly wants a number.
    if measures and any(k in clause for k in ["total", "trend", "top", "bottom", "by ", "count"]):
        return measures[0], None, _agg_from_clause(clause)
    return None, None, "sum"


def _match_measure(words, lower_map) -> Optional[str]:
    for w in words:
        for lname, real in lower_map.items():
            if w in lname:
                return real
    return None


def _agg_from_clause(clause) -> str:
    if "average" in clause or "avg" in clause or "mean" in clause:
        return "avg"
    if "distinct" in clause or "unique" in clause:
        return "distinct_count"
    if "count" in clause or "number of" in clause:
        return "count"
    if "minimum" in clause or "lowest value" in clause:
        return "min"
    if "maximum" in clause or "highest value" in clause:
        return "max"
    return "sum"


def _find_dimension(clause, profile):
    dims = profile.dimensions()
    dates = profile.date_columns()

    # Time phrasing -> date grain.
    if any(w in clause for w in ["monthly", "per month", "by month", "over time", "trend", "month"]):
        if dates:
            return dates[0], "Month"
    if any(w in clause for w in ["yearly", "annual", "per year", "by year"]):
        if dates:
            return dates[0], "Year"
    if "quarter" in clause and dates:
        return dates[0], "Quarter"

    # "by <dimension>" capture.
    m = re.search(r"by ([a-z0-9 _]+)", clause)
    if m:
        target = m.group(1).strip()
        for d in dims:
            if d.lower() in target or target.startswith(d.lower()):
                return d, None

    # Any dimension name mentioned.
    for d in dims:
        if re.search(rf"\b{re.escape(d.lower())}\b", clause):
            return d, None

    return None, None


def _find_filters(clause, profile) -> List[Filter]:
    filters: List[Filter] = []

    # Year filter.
    ym = re.search(r"\b(19|20)\d{2}\b", clause)
    if ym and profile.date_columns():
        filters.append(Filter(column="Year", operator="=", value=int(ym.group(0))))

    # Categorical value filter: match known sample values.
    for col in profile.columns:
        if col.semantic_type in ("dimension", "identifier") and col.sample_values:
            for val in col.sample_values:
                if re.search(rf"\b{re.escape(str(val).lower())}\b", clause):
                    # avoid double-adding the same column
                    if not any(f.column == col.name for f in filters):
                        filters.append(Filter(column=col.name, operator="=", value=val))
                    break
    return filters


def _find_topn(clause):
    # "top"/"bottom" (optionally with a number) always mean Top-N.
    m = re.search(r"\b(top|bottom)\b\s*(\d+)?", clause)
    if m:
        n = int(m.group(2)) if m.group(2) else 10
        return n, ("asc" if m.group(1) == "bottom" else "desc")
    # "highest N" / "lowest N" mean Top-N only when a number follows (so that
    # "sorted highest to lowest" is treated as a sort, not a Top-N).
    m = re.search(r"\b(highest|lowest)\s+(\d+)\b", clause)
    if m:
        return int(m.group(2)), ("asc" if m.group(1) == "lowest" else "desc")
    return None, "desc"


def _find_sort(clause, measure) -> Optional[Sort]:
    if not measure:
        return None
    if "ascending" in clause or "lowest to highest" in clause:
        return Sort(column=measure, direction="asc")
    if ("descending" in clause or "highest to lowest" in clause
            or "sorted" in clause or "sort" in clause):
        return Sort(column=measure, direction="desc")
    return None


def _pick_type(clause, dimension, date_part, measure) -> str:
    if "scatter" in clause or "correlation" in clause or "relationship" in clause:
        return "scatter"
    if "distribution" in clause or "histogram" in clause:
        return "histogram"
    if "table" in clause or "list" in clause or "details" in clause:
        return "table"
    if "line" in clause or "trend" in clause or date_part in ("Month", "Year", "Quarter", "Week", "Day") and any(
            w in clause for w in ["trend", "monthly", "over time", "yearly", "line"]):
        return "line"
    if "pie" in clause or "share" in clause or "proportion" in clause or "breakdown" in clause:
        return "pie"
    if any(w in clause for w in ["total", "kpi", "overall"]) and not dimension:
        return "kpi"
    if dimension:
        if date_part in ("Month", "Year", "Quarter", "Week", "Day"):
            return "line"
        return "bar"
    if measure:
        return "kpi"
    return "bar"


def _make_title(measure, expression, dimension, filters, vtype) -> str:
    label = "Profit Margin" if expression and "/" in expression else (
        "Profit" if expression else (measure or "Value"))
    parts = []
    if vtype == "kpi":
        parts.append(f"Total {label}")
    elif dimension:
        parts.append(f"{label} by {dimension}")
    else:
        parts.append(label)
    yrs = [str(f.value) for f in filters if f.column == "Year"]
    if yrs:
        parts.append(f"- {yrs[0]}")
    others = [f"{f.value}" for f in filters if f.column != "Year"]
    if others:
        parts.append("(" + ", ".join(others) + ")")
    return " ".join(parts)

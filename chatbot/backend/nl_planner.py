"""
nl_planner.py
-------------
The AI layer: turn a natural-language prompt into a structured ``QueryIntent``
that the rest of the pipeline (DAX generation, query execution, visualization
selection) can act on.

Two interchangeable planners:
  * ``RulePlanner`` – a deterministic semantic parser that maps language to the
    model's field catalog using the synonym dictionary.  Always available, no
    network, no API key.  This is what makes the demo runnable offline.
  * ``LLMPlanner``  – if ``ANTHROPIC_API_KEY`` is set, Claude is asked to emit the
    same intent JSON, constrained to the real model catalog.  Falls back to the
    rule planner on any error.

Both produce the identical ``QueryIntent`` shape, so downstream code never cares
which planner ran.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from semantic_model import SemanticModel

# --------------------------------------------------------------------------- #
CHART_KEYWORDS = [
    ("stacked bar", "stackedBar"), ("stacked column", "stackedColumn"),
    ("bar chart", "bar"), ("column chart", "column"),
    ("line chart", "line"), ("area chart", "area"), ("area", "area"),
    ("donut", "donut"), ("doughnut", "donut"), ("pie", "pie"),
    ("scatter", "scatter"), ("bubble", "scatter"),
    ("combo", "combo"), ("waterfall", "waterfall"), ("funnel", "funnel"),
    ("gauge", "gauge"), ("treemap", "treemap"), ("map", "map"),
    ("matrix", "matrix"), ("pivot", "matrix"),
    ("table", "table"), ("kpi", "card"), ("card", "card"),
    ("trend", "line"), ("line", "line"), ("bar", "bar"), ("column", "column"),
]

REPORT_TRIGGERS = ("dashboard", "ad-hoc report", "adhoc report", "ad hoc report",
                   "full report", "complete report", "report showing", "report with",
                   "sales report", "overview report")

FOLLOWUP_TRIGGERS = ("change", "make it", "make this", "turn it", "turn this", "instead",
                     "now filter", "add ", "also show", "also add", "remove", "only ",
                     "switch to", "convert", "as a", "now show", "filter to", "filter it",
                     "drill", "break it down", "group by")


@dataclass
class QueryIntent:
    measures: list[str] = field(default_factory=list)
    dimension: Optional[str] = None
    secondary_dimension: Optional[str] = None
    filters: list[dict] = field(default_factory=list)   # {"field","op","values"}
    time_grain: Optional[str] = None                    # month | quarter | year
    last_n_months: Optional[int] = None
    top_n: Optional[int] = None
    sort_desc: bool = True
    chart_type: Optional[str] = None                    # explicit user choice, else None
    intent_kind: str = "kpi"                            # kpi|breakdown|trend|comparison|table|report
    is_report: bool = False
    report_title: Optional[str] = None
    report_specs: list[dict] = field(default_factory=list)
    raw: str = ""
    notes: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
#  Rule-based planner
# --------------------------------------------------------------------------- #
class RulePlanner:
    def __init__(self, model: SemanticModel):
        self.model = model

    # ---- helpers ----
    def _chart(self, text: str) -> Optional[str]:
        low = text.lower()
        for phrase, ctype in CHART_KEYWORDS:
            if phrase in low:
                return ctype
        return None

    def _top_n(self, text: str) -> Optional[int]:
        m = re.search(r"top\s+(\d+)", text.lower())
        if m:
            return int(m.group(1))
        m = re.search(r"bottom\s+(\d+)", text.lower())
        if m:
            return -int(m.group(1))
        return None

    def _time_grain(self, text: str) -> tuple[Optional[str], Optional[int]]:
        low = text.lower()
        last_n = None
        m = re.search(r"last\s+(\d+)\s+month", low)
        if m:
            last_n = int(m.group(1))
        if any(w in low for w in ("monthly", "by month", "per month", "month over month",
                                  "trend")) or last_n:
            return "month", last_n
        if any(w in low for w in ("quarterly", "by quarter", "per quarter")):
            return "quarter", last_n
        if any(w in low for w in ("yearly", "by year", "per year", "annual", "year over year",
                                  "year on year")):
            return "year", last_n
        return None, last_n

    def _year_filters(self, text: str) -> list[dict]:
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
        years = [y for y in years if y in self.model.years]
        if years:
            return [{"field": "Year", "op": "in", "values": years}]
        return []

    def _value_filters(self, text: str, exclude_dims: set[str] | None = None,
                       prefer_dim: Optional[str] = None) -> list[dict]:
        """Detect literal filters like 'for Electronics' or 'only UK and India'.

        Scans known dimension values against the text.  When the same value could
        belong to two dimensions (customer Country vs sales-rep Rep Country) it is
        assigned to the customer dimension unless the prompt clearly refers to the
        sales team.
        """
        exclude_dims = exclude_dims or set()
        low = text.lower()
        team_ctx = any(w in low for w in ("rep", "salesperson", "sales person", "team",
                                          "employee", "agent", "seller"))
        combos: dict[str, list] = {}
        for dim_name in ("Country", "Rep Country", "Category", "Segment", "Sales Channel",
                         "Order Status", "Payment Method", "Brand", "Sub Category", "Role",
                         "Department", "City", "Supplier"):
            if dim_name in exclude_dims:
                continue
            for v in self.model.distinct_values(dim_name):
                vs = str(v).lower()
                if len(vs) < 2:
                    continue
                if re.search(r"(?<![a-z])" + re.escape(vs) + r"(?![a-z])", low):
                    combos.setdefault(dim_name, [])
                    if v not in combos[dim_name]:
                        combos[dim_name].append(v)
        # Resolve Country vs Rep Country collision.
        if "Country" in combos and "Rep Country" in combos:
            if team_ctx and prefer_dim != "Country":
                combos.pop("Country", None)
            else:
                combos.pop("Rep Country", None)
        return [{"field": d, "op": "in", "values": vals} for d, vals in combos.items()]

    # ---- main entry ----
    def plan(self, text: str) -> QueryIntent:
        if self._looks_like_report(text):
            return self._plan_report(text)
        return self._plan_single(text)

    def _looks_like_report(self, text: str) -> bool:
        low = text.lower()
        if any(t in low for t in REPORT_TRIGGERS):
            return True
        # multiple visual asks joined by commas + 'and'
        chart_words = sum(low.count(w) for w in ("chart", "trend", "table", "kpi", "top "))
        return chart_words >= 3

    # Nouns used in "top N <noun>" / "<noun> by ..." that name a dimension even
    # though the same word may also be a measure (e.g. "customers").
    RANKING_NOUNS = {
        "customer": "Customer", "customers": "Customer", "client": "Customer", "clients": "Customer",
        "product": "Product", "products": "Product", "item": "Product", "items": "Product",
        "salesperson": "Salesperson", "salespeople": "Salesperson", "rep": "Salesperson",
        "reps": "Salesperson", "agent": "Salesperson", "agents": "Salesperson",
        "country": "Country", "countries": "Country", "region": "Country",
        "category": "Category", "categories": "Category", "brand": "Brand", "brands": "Brand",
        "supplier": "Supplier", "suppliers": "Supplier", "city": "City", "cities": "City",
        "segment": "Segment", "segments": "Segment",
    }
    # Measures that are really "count of a dimension" and should be dropped when
    # that dimension becomes the ranking axis.
    COUNT_MEASURE_FOR_DIM = {"Customer": "Total Customers"}

    def _ranking_dimension(self, text: str) -> Optional[str]:
        low = text.lower()
        m = re.search(r"top\s+\d+\s+([a-z]+)", low) or re.search(r"bottom\s+\d+\s+([a-z]+)", low)
        if m and m.group(1) in self.RANKING_NOUNS:
            return self.RANKING_NOUNS[m.group(1)]
        m = re.search(r"by\s+([a-z]+)", low)
        if m and m.group(1) in self.RANKING_NOUNS:
            return self.RANKING_NOUNS[m.group(1)]
        return None

    def _plan_single(self, text: str, default_measure: str = "Total Revenue") -> QueryIntent:
        intent = QueryIntent(raw=text)
        low = text.lower()
        found = self.model.resolve_terms(text)
        measures = list(found["measures"])
        dims = list(found["dimensions"])

        chart = self._chart(text)
        top_n = self._top_n(text)
        grain, last_n = self._time_grain(text)
        is_compare = any(w in low for w in ("compare", "between", " vs ", "versus"))

        # Missing-metric guard: if the user clearly asked for a metric we don't
        # have and nothing resolved, refuse rather than silently defaulting.
        self._note_unresolved(intent, text, found)
        if intent.unresolved and not measures:
            intent.measures = []
            intent.intent_kind = "error"
            return intent

        # A "card"/kpi chart request means no breakdown even if a dim was mentioned.
        time_dims = [d for d in dims if self.model.dimensions[d].is_time]
        cat_dims = [d for d in dims if not self.model.dimensions[d].is_time]

        # "top N <noun>" / "... by <noun>" forces the ranking dimension even when the
        # noun collides with a measure name.
        rank_dim = self._ranking_dimension(text)
        if rank_dim and rank_dim not in cat_dims:
            cat_dims.insert(0, rank_dim)
            drop = self.COUNT_MEASURE_FOR_DIM.get(rank_dim)
            if drop in measures:
                measures.remove(drop)

        primary = None
        secondary = None
        if grain and chart != "card":
            primary = {"month": "Month", "quarter": "Quarter", "year": "Year"}[grain]
            if cat_dims:
                secondary = cat_dims[0]
        elif cat_dims and chart != "card":
            primary = cat_dims[0]
            if len(cat_dims) > 1:
                secondary = cat_dims[1]
        elif time_dims and chart != "card":
            primary = time_dims[0]
            grain = self.model.dimensions[primary].time_grain

        # Filters
        filters = self._year_filters(text)
        value_filters = self._value_filters(text, prefer_dim=primary)

        # "compare A, B, C" -> group by that dimension (don't just filter to a total).
        if is_compare and value_filters and not primary:
            # Group by the compared dimension AND keep it as a filter to the named values.
            primary = value_filters[0]["field"]
            grain = None
            filters += value_filters
        else:
            filters += value_filters

        # Measures default
        if not measures:
            measures = [default_measure]

        # Growth/YoY measure on a categorical breakdown reads better alongside its
        # base measure, ranked by the base measure, top 10 if high-cardinality.
        derived = [m for m in measures if self.model.measures[m].kind == "derived"]
        if derived and primary and not self.model.dimensions[primary].is_time:
            for d in derived:
                base = self.model.measures[d].base
                if base and base not in measures:
                    measures.insert(0, base)
            if top_n is None and primary in ("Product", "Customer", "Salesperson", "City"):
                top_n = 10

        intent.measures = measures
        intent.dimension = primary
        intent.secondary_dimension = secondary
        intent.filters = filters
        intent.time_grain = grain
        intent.last_n_months = last_n
        intent.top_n = top_n
        intent.chart_type = chart
        intent.sort_desc = "bottom" not in text.lower()

        # classify
        if chart == "card" or (not primary and not grain):
            intent.intent_kind = "kpi"
        elif grain:
            intent.intent_kind = "trend"
        elif chart == "table" or chart == "matrix":
            intent.intent_kind = "table"
        elif any(f["field"] in ("Country", "Category") and len(f["values"]) > 1 for f in filters) \
                and "compare" in text.lower():
            intent.intent_kind = "comparison"
        else:
            intent.intent_kind = "breakdown"

        return intent

    def _note_unresolved(self, intent: QueryIntent, text: str, found: dict) -> None:
        # Flag business terms that clearly reference a metric we don't have.
        low = text.lower()
        MISSING_HINTS = {
            "satisfaction": "employee/customer satisfaction",
            "nps": "NPS score", "churn": "churn rate", "inventory turnover": "inventory turnover",
            "headcount": "headcount", "salary": "salary", "attrition": "attrition",
        }
        for key, label in MISSING_HINTS.items():
            if key in low and not found["measures"]:
                intent.unresolved.append(label)

    def _plan_report(self, text: str) -> QueryIntent:
        intent = QueryIntent(raw=text, is_report=True, intent_kind="report")
        intent.report_title = self._report_title(text)
        report_filters = self._year_filters(text)

        specs: list[dict] = []
        low = text.lower()

        # KPI cards – always lead an ad-hoc report with headline numbers.
        kpi_measures = []
        found = self.model.resolve_terms(text)
        for m in ("Total Revenue", "Total Profit", "Profit Margin %", "Total Orders",
                  "Revenue YoY %"):
            if m in found["measures"] or m in ("Total Revenue", "Total Profit"):
                kpi_measures.append(m)
        # de-dupe, keep order, cap at 5
        seen = set()
        kpi_measures = [m for m in kpi_measures if not (m in seen or seen.add(m))][:5]
        for m in kpi_measures:
            specs.append({"kind": "kpi", "measures": [m], "chart": "card",
                          "filters": report_filters})

        # Monthly trend
        if "trend" in low or "monthly" in low or "month" in low:
            specs.append({"kind": "trend", "measures": ["Total Revenue"], "dimension": "Month",
                          "time_grain": "month", "chart": "line", "filters": report_filters,
                          "title": "Monthly Sales Trend"})
        # By country
        if "country" in low or "countries" in low or "region" in low:
            specs.append({"kind": "breakdown", "measures": ["Total Revenue"], "dimension": "Country",
                          "chart": "bar", "filters": report_filters, "title": "Sales by Country"})
        # By category / product
        if "category" in low:
            specs.append({"kind": "breakdown", "measures": ["Total Revenue"], "dimension": "Category",
                          "chart": "column", "filters": report_filters, "title": "Sales by Category"})
        if "product" in low and "profit" in low:
            specs.append({"kind": "breakdown", "measures": ["Total Profit", "Profit YoY %"],
                          "dimension": "Product", "chart": "bar", "top_n": 10,
                          "filters": report_filters, "title": "Profit Growth by Product (Top 10)"})
        # Top customers
        m = re.search(r"top\s+(\d+)\s+customer", low)
        if m or "top customer" in low:
            n = int(m.group(1)) if m else 10
            specs.append({"kind": "table", "measures": ["Total Revenue", "Total Profit"],
                          "dimension": "Customer", "top_n": n, "chart": "table",
                          "filters": report_filters, "title": f"Top {n} Customers by Revenue"})

        # Fallback: if nothing matched beyond KPIs, add sensible defaults.
        if len(specs) <= len(kpi_measures):
            specs.append({"kind": "trend", "measures": ["Total Revenue"], "dimension": "Month",
                          "time_grain": "month", "chart": "line", "filters": report_filters,
                          "title": "Monthly Sales Trend"})
            specs.append({"kind": "breakdown", "measures": ["Total Revenue"], "dimension": "Country",
                          "chart": "bar", "filters": report_filters, "title": "Sales by Country"})
            specs.append({"kind": "breakdown", "measures": ["Total Profit", "Profit YoY %"],
                          "dimension": "Product", "chart": "bar", "top_n": 10,
                          "filters": report_filters, "title": "Profit Growth by Product (Top 10)"})

        intent.report_specs = specs
        intent.filters = report_filters
        return intent

    def _report_title(self, text: str) -> str:
        years = re.findall(r"\b(20\d{2})\b", text)
        yr = f" {years[0]}" if years else ""
        return f"Ad-hoc Sales Report{yr}"

    # ---- follow-up modification ----
    def modify(self, prev: QueryIntent, text: str) -> QueryIntent:
        intent = QueryIntent(**prev.to_dict())
        intent.raw = text
        intent.notes = []
        low = text.lower()

        # change chart type
        chart = self._chart(text)
        if chart and any(t in low for t in ("change", "make it", "turn it", "as a", "switch",
                                            "convert", "instead", "make this", "turn this")):
            intent.chart_type = chart
            if chart in ("line", "area"):
                intent.intent_kind = "trend"
            elif chart == "table":
                intent.intent_kind = "table"

        # add / remove measure
        if low.startswith("add ") or "also show" in low or "also add" in low or "include" in low:
            found = self.model.resolve_terms(text)
            for m in found["measures"]:
                if m not in intent.measures:
                    intent.measures.append(m)
            for d in found["dimensions"]:
                if not intent.dimension:
                    intent.dimension = d
        if low.startswith("remove ") or "drop " in low or "without " in low:
            found = self.model.resolve_terms(text)
            for m in found["measures"]:
                if m in intent.measures and len(intent.measures) > 1:
                    intent.measures.remove(m)

        # filter to values / years
        yf = self._year_filters(text)
        if yf:
            intent.filters = [f for f in intent.filters if f["field"] != "Year"] + yf
        vf = self._value_filters(text, prefer_dim=intent.dimension)
        if vf and any(w in low for w in ("only", "filter", "just", "for ", "limit")):
            # Prefer filtering the dimension currently on the chart.
            if intent.dimension and any(f["field"] == intent.dimension for f in vf):
                vf = [f for f in vf if f["field"] == intent.dimension]
            else:
                vf = vf[:1]
            for f in vf:
                intent.filters = [x for x in intent.filters if x["field"] != f["field"]] + [f]

        # group by / breakdown by dimension
        if "group by" in low or "break it down" in low or "by " in low:
            found = self.model.resolve_terms(text)
            cat = [d for d in found["dimensions"] if not self.model.dimensions[d].is_time]
            if cat and ("group by" in low or "break" in low or low.startswith("by ")):
                intent.dimension = cat[0]
                intent.intent_kind = "breakdown"

        # top N
        tn = self._top_n(text)
        if tn:
            intent.top_n = tn

        return intent


# --------------------------------------------------------------------------- #
#  Optional Claude LLM planner
# --------------------------------------------------------------------------- #
class LLMPlanner:
    """Uses the Anthropic Messages API (via stdlib urllib) to produce the intent.

    Only engaged when ANTHROPIC_API_KEY is present.  The model catalog is passed
    in the prompt so Claude can only reference real fields; the JSON it returns is
    validated and any unknown field is dropped, then the rule planner fills gaps.
    """

    def __init__(self, model: SemanticModel, rule: RulePlanner):
        self.model = model
        self.rule = rule
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.model_id = os.environ.get("CHATBOT_LLM_MODEL", "claude-sonnet-5")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _catalog_text(self) -> str:
        meas = ", ".join(self.model.measures.keys())
        dims = ", ".join(self.model.dimensions.keys())
        return f"MEASURES: {meas}\nDIMENSIONS: {dims}\nYEARS: {self.model.years}"

    def plan(self, text: str, prev: Optional[QueryIntent] = None) -> QueryIntent:
        try:
            data = self._call(text, prev)
            return self._validate(data, text)
        except Exception as exc:  # noqa: BLE001 - fall back to deterministic planner
            fallback = self.rule.modify(prev, text) if prev else self.rule.plan(text)
            fallback.notes.append(f"LLM planner unavailable ({type(exc).__name__}); used rule planner.")
            return fallback

    def _call(self, text: str, prev: Optional[QueryIntent]) -> dict:
        import urllib.request

        system = (
            "You are the query-planning brain of a Power BI reporting chatbot. "
            "Map the user's request to the semantic model below. Respond with ONLY a "
            "JSON object matching this schema: {measures:[string], dimension:string|null, "
            "secondary_dimension:string|null, filters:[{field,op,values}], time_grain:"
            "'month'|'quarter'|'year'|null, top_n:int|null, chart_type:string|null, "
            "is_report:bool, report_specs:[...], intent_kind:'kpi'|'breakdown'|'trend'|"
            "'comparison'|'table'|'report'}. Use ONLY the exact measure/dimension names "
            "listed. If a requested metric does not exist, leave measures empty and add its "
            "name to an 'unresolved' array.\n\n" + self._catalog_text()
        )
        user = text if prev is None else (
            f"Current visualization intent: {json.dumps(prev.to_dict())}\n"
            f"Modify it per this instruction: {text}"
        )
        payload = json.dumps({
            "model": self.model_id,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
        txt = "".join(b.get("text", "") for b in body.get("content", []))
        m = re.search(r"\{.*\}", txt, re.DOTALL)
        return json.loads(m.group(0)) if m else {}

    def _validate(self, data: dict, text: str) -> QueryIntent:
        intent = QueryIntent(raw=text)
        intent.measures = [m for m in data.get("measures", []) if m in self.model.measures]
        dim = data.get("dimension")
        intent.dimension = dim if dim in self.model.dimensions else None
        sdim = data.get("secondary_dimension")
        intent.secondary_dimension = sdim if sdim in self.model.dimensions else None
        intent.time_grain = data.get("time_grain")
        intent.top_n = data.get("top_n")
        intent.chart_type = data.get("chart_type")
        intent.intent_kind = data.get("intent_kind", "breakdown")
        intent.is_report = bool(data.get("is_report"))
        intent.report_specs = data.get("report_specs", []) if intent.is_report else []
        intent.unresolved = data.get("unresolved", [])
        # validate filters
        for f in data.get("filters", []):
            if f.get("field") in self.model.dimensions or f.get("field") == "Year":
                intent.filters.append(f)
        if not intent.measures and not intent.is_report and not intent.unresolved:
            intent.measures = ["Total Revenue"]
        # If the LLM under-specified, let the rule planner backfill the report.
        if intent.is_report and not intent.report_specs:
            return self.rule._plan_report(text)
        return intent


# --------------------------------------------------------------------------- #
class Planner:
    """Facade that picks the LLM planner when configured, else the rule planner."""

    def __init__(self, model: SemanticModel):
        self.model = model
        self.rule = RulePlanner(model)
        self.llm = LLMPlanner(model, self.rule)

    def interpret(self, text: str, prev: Optional[QueryIntent] = None) -> QueryIntent:
        is_followup = prev is not None and self._is_followup(text)
        if self.llm.enabled:
            return self.llm.plan(text, prev if is_followup else None)
        if is_followup:
            return self.rule.modify(prev, text)
        return self.rule.plan(text)

    @staticmethod
    def _is_followup(text: str) -> bool:
        low = text.lower().strip()
        return any(low.startswith(t) or t in low for t in FOLLOWUP_TRIGGERS)

    @property
    def using_llm(self) -> bool:
        return self.llm.enabled

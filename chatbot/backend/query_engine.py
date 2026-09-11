"""
query_engine.py
---------------
Execute a ``QueryIntent`` against the in-memory semantic model and return tabular
results.  This stands in for the Power BI engine in the demo; the
``PowerBIExecutor`` adapter (see auth.py / README) runs the generated DAX against
a live dataset instead, returning the same result shape.

Handles: measure aggregation, single/secondary dimension grouping, filters,
Top-N, month/quarter/year time series derived from Order Date, and YoY
time-intelligence measures (which deliberately look past the Year filter so the
prior-year comparison is available).
"""
from __future__ import annotations

from calendar import month_abbr
from datetime import date
from typing import Any, Optional

from semantic_model import SemanticModel, Measure
from nl_planner import QueryIntent


class QueryResult:
    def __init__(self):
        self.columns: list[dict] = []
        self.rows: list[dict] = []
        self.period_field: Optional[str] = None
        self.series_field: Optional[str] = None
        self.measures: list[str] = []
        self.dimension: Optional[str] = None
        self.error: Optional[str] = None
        self.notes: list[str] = []

    def to_dict(self) -> dict:
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": len(self.rows),
            "period_field": self.period_field,
            "series_field": self.series_field,
            "measures": self.measures,
            "dimension": self.dimension,
            "error": self.error,
            "notes": self.notes,
        }


class QueryEngine:
    def __init__(self, model: SemanticModel, rls_filters: Optional[list[dict]] = None):
        self.model = model
        self.rls_filters = rls_filters or []

    # ---------- aggregation primitives ----------
    def _agg(self, measure: Measure, rows: list[dict]) -> Optional[float]:
        if not rows and measure.kind not in ("count", "count_where"):
            if measure.kind in ("sum", "distinct", "ratio"):
                return 0
        k = measure.kind
        if k == "sum":
            return sum(r.get(measure.column) or 0 for r in rows)
        if k == "count":
            return len(rows)
        if k == "distinct":
            return len({r.get(measure.column) for r in rows if r.get(measure.column) is not None})
        if k == "count_where":
            col, val = measure.where
            return sum(1 for r in rows if r.get(col) == val)
        if k == "ratio":
            num = self._ratio_side(measure.numerator, rows)
            den = self._ratio_side(measure.denominator, rows)
            return (num / den) if den else 0
        return None

    def _ratio_side(self, token: str, rows: list[dict]) -> float:
        if token == "__orders__":
            return len(rows)
        if token == "__returns__":
            return sum(1 for r in rows if r.get("Order Status") == "Returned")
        if token == "__target__":
            # distinct rep -> target (avoid double counting one rep across many orders)
            seen: dict[Any, float] = {}
            for r in rows:
                rep = r.get("Rep Name")
                if rep is not None and rep not in seen:
                    seen[rep] = r.get("Sales Target") or 0
            return sum(seen.values())
        return sum(r.get(token) or 0 for r in rows)

    def _measure_value(self, mname: str, rows_all: list[dict], focus_years: list[int]) -> Optional[float]:
        measure = self.model.measures[mname]
        if measure.kind == "derived" and measure.time_intelligence == "yoy":
            base = self.model.measures[measure.base]
            years_present = sorted({r.get("Year") for r in rows_all if r.get("Year") is not None})
            if len(years_present) < 2:
                return None
            if focus_years and (max(focus_years) - 1) in years_present and max(focus_years) in years_present:
                cur_y, prior_y = max(focus_years), max(focus_years) - 1
            else:
                cur_y, prior_y = years_present[-1], years_present[-2]
            cur = self._agg(base, [r for r in rows_all if r.get("Year") == cur_y])
            prior = self._agg(base, [r for r in rows_all if r.get("Year") == prior_y])
            return ((cur - prior) / prior) if prior else None
        # ordinary measure: honour year filter
        rows = rows_all if not focus_years else [r for r in rows_all if r.get("Year") in focus_years]
        return self._agg(measure, rows)

    # ---------- filtering ----------
    def _split_filters(self, intent: QueryIntent) -> tuple[list[dict], list[int]]:
        non_year, focus_years = [], []
        for f in intent.filters + self.rls_filters:
            if f["field"] == "Year":
                focus_years = [int(v) for v in f["values"]]
            else:
                non_year.append(f)
        return non_year, focus_years

    def _apply_filters(self, rows: list[dict], filters: list[dict]) -> list[dict]:
        out = rows
        for f in filters:
            field = f["field"]
            dim = self.model.dimensions.get(field)
            col = dim.column if dim else field
            op = f.get("op", "in")
            vals = f.get("values", [])
            if op == "in":
                vset = set(vals)
                out = [r for r in out if r.get(col) in vset]
            elif op == "eq":
                out = [r for r in out if r.get(col) == vals[0]]
        return out

    # ---------- period helpers ----------
    def _period_key(self, r: dict, grain: str) -> tuple[Any, Any, str]:
        d: date = r.get("Order Date")
        y = r.get("Year")
        if isinstance(d, date):
            if grain == "month":
                return ((y, d.month), y * 100 + d.month, f"{month_abbr[d.month]} {y}")
            if grain == "quarter":
                q = (d.month - 1) // 3 + 1
                return ((y, q), y * 10 + q, f"Q{q} {y}")
        if grain == "year":
            return (y, y or 0, str(y))
        # fallback
        return (y, y or 0, str(y))

    # ---------- main ----------
    def execute(self, intent: QueryIntent) -> QueryResult:
        res = QueryResult()
        res.measures = intent.measures or ["Total Revenue"]
        res.dimension = intent.dimension

        # validate measures exist
        for m in res.measures:
            if m not in self.model.measures:
                res.error = f"Measure '{m}' is not in the model."
                return res

        non_year, focus_years = self._split_filters(intent)
        base_rows = self._apply_filters(self.model.fact, non_year)

        # last N months window
        if intent.last_n_months:
            base_rows = self._last_n_months(base_rows, intent.last_n_months)

        if base_rows == [] and not focus_years:
            res.notes.append("No rows matched the filters.")

        # ---- KPI (no dimension) ----
        if not intent.dimension:
            row = {}
            for m in res.measures:
                row[m] = self._measure_value(m, base_rows, focus_years)
            res.rows = [row]
            res.columns = [self._mcol(m) for m in res.measures]
            return res

        dim = self.model.dimensions[intent.dimension]
        is_time = dim.is_time and intent.time_grain

        # Time series: restrict the displayed periods to the selected year(s); YoY
        # still reaches back to the prior year via _yoy_for_period (full fact).
        # Non-time breakdown: group across ALL years so derived YoY measures can see
        # the prior year, and let _measure_value honour the year filter per group.
        if is_time and focus_years:
            group_source = [r for r in base_rows if r.get("Year") in focus_years]
        else:
            group_source = base_rows

        # ---- grouping ----
        groups: dict[Any, dict] = {}
        for r in group_source:
            if is_time:
                gkey, gsort, glabel = self._period_key(r, intent.time_grain)
            else:
                gkey = r.get(dim.column)
                gsort, glabel = gkey, gkey
            skey = None
            if intent.secondary_dimension:
                sdim = self.model.dimensions[intent.secondary_dimension]
                skey = r.get(sdim.column)
            bucket = groups.setdefault((gkey, skey), {"_rows": [], "_sort": gsort,
                                                      "_label": glabel, "_series": skey})
            bucket["_rows"].append(r)

        # For YoY on a time series we still need prior-year rows for the SAME period,
        # so derived measures are computed against base_rows filtered to the period label
        # matched by (month/quarter) ignoring year.
        out_rows = []
        for (gkey, skey), b in groups.items():
            row: dict[str, Any] = {}
            label_field = self._dim_label_field(intent)
            row[label_field] = b["_label"] if not (b["_label"] is None) else "(blank)"
            if intent.secondary_dimension:
                row[self.model.dimensions[intent.secondary_dimension].name] = skey
            for m in res.measures:
                measure = self.model.measures[m]
                if measure.kind == "derived" and measure.time_intelligence == "yoy" and is_time:
                    row[m] = self._yoy_for_period(measure, intent, b, non_year)
                else:
                    row[m] = self._measure_value(m, b["_rows"], focus_years)
            row["_sort"] = b["_sort"]
            out_rows.append(row)

        # sort
        order_m = res.measures[0]
        if is_time:
            out_rows.sort(key=lambda x: (x["_sort"] is None, x["_sort"]))
        else:
            out_rows.sort(key=lambda x: (x.get(order_m) is None, x.get(order_m) or 0),
                          reverse=intent.sort_desc)

        # top N
        if intent.top_n and not is_time:
            n = abs(intent.top_n)
            out_rows = out_rows[:n]

        for r in out_rows:
            r.pop("_sort", None)

        res.rows = out_rows
        res.period_field = self._dim_label_field(intent) if is_time else None
        res.series_field = self.model.dimensions[intent.secondary_dimension].name \
            if intent.secondary_dimension else None
        # columns metadata
        cols = [{"name": self._dim_label_field(intent), "role": "dimension", "format": "text"}]
        if intent.secondary_dimension:
            cols.append({"name": self.model.dimensions[intent.secondary_dimension].name,
                         "role": "dimension", "format": "text"})
        cols += [self._mcol(m) for m in res.measures]
        res.columns = cols
        return res

    def _yoy_for_period(self, measure: Measure, intent: QueryIntent, bucket: dict,
                        non_year: list[dict]) -> Optional[float]:
        """YoY for a single period bucket: compare this bucket's rows (current year)
        with the same month/quarter in the previous year."""
        base = self.model.measures[measure.base]
        rows = bucket["_rows"]
        if not rows:
            return None
        sample = rows[0]
        d = sample.get("Order Date")
        y = sample.get("Year")
        if not isinstance(d, date) or y is None:
            return None
        if intent.time_grain == "month":
            unit, cur_val_rows = d.month, rows
            prior_rows = [r for r in self._apply_filters(self.model.fact, non_year)
                          if isinstance(r.get("Order Date"), date)
                          and r["Order Date"].month == unit and r.get("Year") == y - 1
                          and (bucket["_series"] is None or self._series_match(r, intent, bucket))]
        elif intent.time_grain == "quarter":
            q = (d.month - 1) // 3 + 1
            prior_rows = [r for r in self._apply_filters(self.model.fact, non_year)
                          if isinstance(r.get("Order Date"), date)
                          and ((r["Order Date"].month - 1) // 3 + 1) == q and r.get("Year") == y - 1
                          and (bucket["_series"] is None or self._series_match(r, intent, bucket))]
        else:
            prior_rows = [r for r in self._apply_filters(self.model.fact, non_year)
                          if r.get("Year") == y - 1
                          and (bucket["_series"] is None or self._series_match(r, intent, bucket))]
        cur = self._agg(base, rows)
        prior = self._agg(base, prior_rows)
        return ((cur - prior) / prior) if prior else None

    def _series_match(self, r: dict, intent: QueryIntent, bucket: dict) -> bool:
        sdim = self.model.dimensions[intent.secondary_dimension]
        return r.get(sdim.column) == bucket["_series"]

    def _last_n_months(self, rows: list[dict], n: int) -> list[dict]:
        dates = [r.get("Order Date") for r in rows if isinstance(r.get("Order Date"), date)]
        if not dates:
            return rows
        end = max(dates)
        # window start = first day of the month, n-1 months back
        y, mth = end.year, end.month
        total = y * 12 + (mth - 1) - (n - 1)
        sy, sm = total // 12, total % 12 + 1
        start = date(sy, sm, 1)
        return [r for r in rows if isinstance(r.get("Order Date"), date) and r["Order Date"] >= start]

    def _dim_label_field(self, intent: QueryIntent) -> str:
        if intent.time_grain == "month":
            return "Month"
        if intent.time_grain == "quarter":
            return "Quarter"
        if intent.time_grain == "year":
            return "Year"
        return self.model.dimensions[intent.dimension].name

    def _mcol(self, mname: str) -> dict:
        meas = self.model.measures[mname]
        return {"name": mname, "role": "measure", "format": meas.fmt}

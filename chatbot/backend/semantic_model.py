"""
semantic_model.py
-----------------
Loads the Power BI semantic model (metadata + data) that was extracted from the
.pbit, and exposes it to the AI layer.

Responsibilities:
  * Load table data (CSV) and coerce types.
  * Build a *joined fact view* by resolving the model relationships, so a
    dimension that lives on a dimension table (e.g. Customers[Country]) can be
    used to slice the Sales fact.
  * Expose a **field catalog** – the list of measures and dimensions the AI is
    allowed to reference – together with business synonyms and definitions.
  * Resolve a natural-language term ("revenue", "country", "profit growth") to a
    concrete catalog field.  This is the "semantic-model awareness" that stops
    the AI from guessing at raw database columns.

Pure standard library – no pandas required.
"""
from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(HERE), "data")


# --------------------------------------------------------------------------- #
#  Field catalog types
# --------------------------------------------------------------------------- #
@dataclass
class Measure:
    name: str
    kind: str                      # sum | distinct | count | count_where | ratio | derived
    column: Optional[str] = None   # fact-view column the aggregation runs on
    numerator: Optional[str] = None
    denominator: Optional[str] = None
    where: Optional[tuple[str, str]] = None  # (column, value) for count_where
    fmt: str = "number"            # number | currency | percent | int
    dax: str = ""
    definition: str = ""
    time_intelligence: Optional[str] = None  # None | yoy | ytd  (needs a date grain)
    base: Optional[str] = None     # base measure name for time-intelligence


@dataclass
class Dimension:
    name: str          # friendly label used everywhere
    column: str        # column in the joined fact view
    table: str         # originating model table (for DAX)
    source_column: str # original column name on that table (for DAX)
    is_time: bool = False
    time_grain: Optional[str] = None  # year | quarter | month | date


@dataclass
class Field:
    label: str
    role: str          # measure | dimension
    ref: Any           # Measure | Dimension


# --------------------------------------------------------------------------- #
#  Semantic model
# --------------------------------------------------------------------------- #
class SemanticModel:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        with open(os.path.join(data_dir, "semantic_model.json"), encoding="utf-8") as fh:
            self.meta = json.load(fh)

        # "sales" preserves the original hand-tuned catalog exactly; "generic" builds
        # the catalog from the model's own metadata so ANY report can be loaded.
        self.profile = self.meta.get("profile", "sales")
        self.fact_table = self.meta.get("factTable", "Sales")
        self.date_column = self.meta.get("dateColumn", "Order Date")
        self._type_map = self._build_type_map()

        # Load every table declared in the metadata (filename = <table name>.csv).
        self.tables: dict[str, list[dict]] = {}
        for t in self.meta.get("tables", []):
            key = t["name"].lower()
            self.tables[key] = self._load_csv(os.path.join(data_dir, f"{key}.csv"), t["name"])

        if self.profile == "generic":
            self.fact = self._build_fact_view_generic()
            self.measures = self._build_measures_generic()
            self.dimensions = self._build_dimensions_generic()
        else:
            self.fact = self._build_fact_view()
            self.measures = self._build_measures()
            self.dimensions = self._build_dimensions()

        self.synonyms: dict[str, list[str]] = self.meta.get("synonyms", {})
        self.definitions: dict[str, str] = self.meta.get("definitions", {})
        self._synonym_index = self._build_synonym_index()
        self.years = sorted({r["Year"] for r in self.fact if r.get("Year") is not None})

    def _build_type_map(self) -> dict[str, dict[str, str]]:
        """Per-table {column: dataType} from the metadata (used by the generic profile)."""
        out: dict[str, dict[str, str]] = {}
        for t in self.meta.get("tables", []):
            out[t["name"]] = {c["name"]: c.get("dataType", "string") for c in t.get("columns", [])}
        return out

    # ---------- loading / typing ----------
    NUMERIC_COLS = {
        "Year", "Month", "Quantity", "Unit Price", "Unit Cost", "Gross Sales",
        "Discount %", "Discount Amount", "Net Sales", "Total Cost", "Profit",
        "Profit Margin %", "Credit Limit", "Sales Target", "Stock Quantity",
        "Reorder Level", "Weight (kg)", "Rating",
    }
    INT_COLS = {"Year", "Month", "Quantity", "Stock Quantity", "Reorder Level"}
    DATE_COLS = {"Order Date", "Ship Date", "Registration Date", "Join Date"}

    def _load_csv(self, path: str, table_name: str = "") -> list[dict]:
        types = self._type_map.get(table_name, {}) if self.profile == "generic" else {}
        rows: list[dict] = []
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                out: dict[str, Any] = {}
                for k, v in r.items():
                    out[k] = self._coerce_typed(k, v, types.get(k)) if types \
                        else self._coerce(k, v)
                rows.append(out)
        return rows

    def _coerce(self, col: str, val: str) -> Any:
        if val is None or val == "":
            return None
        if col in self.INT_COLS:
            try:
                return int(float(val))
            except ValueError:
                return None
        if col in self.NUMERIC_COLS:
            try:
                return float(val)
            except ValueError:
                return None
        if col in self.DATE_COLS:
            try:
                return datetime.strptime(val[:10], "%Y-%m-%d").date()
            except ValueError:
                return val
        return val

    @staticmethod
    def _coerce_typed(col: str, val: str, dtype: Optional[str]) -> Any:
        """Coerce by the model's declared data type (generic profile)."""
        if val is None or val == "":
            return None
        try:
            if dtype == "int64":
                return int(float(val))
            if dtype == "double":
                return float(val)
            if dtype in ("dateTime", "date"):
                return datetime.strptime(val[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
        return val

    # ---------- join fact -> dims ----------
    def _index(self, table: str, key: str) -> dict[Any, dict]:
        return {r[key]: r for r in self.tables[table]}

    def _build_fact_view(self) -> list[dict]:
        cust = self._index("customers", "Customer ID")
        users = self._index("users", "User ID")
        prods = self._index("products", "Product ID")
        out = []
        for s in self.tables["sales"]:
            row = dict(s)  # Sales columns keep their names
            c = cust.get(s.get("Customer ID"), {})
            u = users.get(s.get("User ID"), {})
            p = prods.get(s.get("Product ID"), {})
            # Customer attributes
            row["Customer Country"] = c.get("Country")
            row["Customer City"] = c.get("City")
            row["Customer Segment"] = c.get("Segment")
            row["Customer Name"] = f"{c.get('First Name','')} {c.get('Last Name','')}".strip() or None
            row["Credit Limit"] = c.get("Credit Limit")
            # Sales rep (Users) attributes
            row["Rep Name"] = u.get("Name")
            row["Rep Role"] = u.get("Role")
            row["Rep Department"] = u.get("Department")
            row["Rep Country"] = u.get("Country")
            row["Rep Location"] = u.get("Location")
            row["Sales Target"] = u.get("Sales Target")
            # Product attributes
            row["Product Name"] = p.get("Product Name")
            row["Product Sub Category"] = p.get("Sub Category")
            row["Product Brand"] = p.get("Brand")
            row["Product Supplier"] = p.get("Supplier")
            row["Product Rating"] = p.get("Rating")
            out.append(row)
        return out

    # ---------- measures ----------
    def _build_measures(self) -> dict[str, Measure]:
        m: dict[str, Measure] = {}

        def add(meas: Measure):
            m[meas.name] = meas

        add(Measure("Total Revenue", "sum", column="Net Sales", fmt="currency",
                    dax="SUM(Sales[Net Sales])",
                    definition="Sum of Net Sales (gross sales after discounts)."))
        add(Measure("Total Profit", "sum", column="Profit", fmt="currency",
                    dax="SUM(Sales[Profit])", definition="Sum of Profit (Net Sales minus Total Cost)."))
        add(Measure("Total Gross Sales", "sum", column="Gross Sales", fmt="currency",
                    dax="SUM(Sales[Gross Sales])", definition="Sum of Gross Sales before discounts."))
        add(Measure("Total Cost", "sum", column="Total Cost", fmt="currency",
                    dax="SUM(Sales[Total Cost])", definition="Sum of Total Cost."))
        add(Measure("Total Discount", "sum", column="Discount Amount", fmt="currency",
                    dax="SUM(Sales[Discount Amount])", definition="Sum of Discount Amount."))
        add(Measure("Total Quantity", "sum", column="Quantity", fmt="int",
                    dax="SUM(Sales[Quantity])", definition="Units sold."))
        add(Measure("Total Orders", "count", column="Order ID", fmt="int",
                    dax="COUNTROWS(Sales)", definition="Number of order lines."))
        add(Measure("Total Customers", "distinct", column="Customer ID", fmt="int",
                    dax="DISTINCTCOUNT(Sales[Customer ID])", definition="Distinct customers who ordered."))
        add(Measure("Total Returns", "count_where", where=("Order Status", "Returned"), fmt="int",
                    dax='CALCULATE(COUNTROWS(Sales), Sales[Order Status]="Returned")',
                    definition="Count of returned orders."))
        add(Measure("Completed Orders", "count_where", where=("Order Status", "Completed"), fmt="int",
                    dax='CALCULATE(COUNTROWS(Sales), Sales[Order Status]="Completed")'))
        add(Measure("Pending Orders", "count_where", where=("Order Status", "Pending"), fmt="int",
                    dax='CALCULATE(COUNTROWS(Sales), Sales[Order Status]="Pending")'))
        add(Measure("Avg Order Value", "ratio", numerator="Net Sales", denominator="__orders__",
                    fmt="currency", dax="DIVIDE([Total Revenue], [Total Orders])",
                    definition="Total Revenue divided by number of orders."))
        add(Measure("Profit Margin %", "ratio", numerator="Profit", denominator="Net Sales",
                    fmt="percent", dax="DIVIDE([Total Profit], [Total Revenue])",
                    definition="Total Profit divided by Total Revenue."))
        add(Measure("Return Rate %", "ratio", numerator="__returns__", denominator="__orders__",
                    fmt="percent", dax="DIVIDE([Total Returns], [Total Orders])",
                    definition="Returned orders as a share of all orders."))
        add(Measure("Discount Rate %", "ratio", numerator="Discount Amount", denominator="Gross Sales",
                    fmt="percent", dax="DIVIDE([Total Discount], [Total Gross Sales])",
                    definition="Discount amount as a share of gross sales."))
        add(Measure("Avg Selling Price", "ratio", numerator="Net Sales", denominator="Quantity",
                    fmt="currency", dax="DIVIDE([Total Revenue], [Total Quantity])",
                    definition="Total Revenue per unit sold."))
        # Time-intelligence measures (need a date grain supplied by the query engine).
        add(Measure("Revenue YoY %", "derived", base="Total Revenue", time_intelligence="yoy",
                    fmt="percent",
                    dax=("VAR cy = [Total Revenue]\n"
                         "VAR py = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR('Date'[Date]))\n"
                         "RETURN DIVIDE(cy - py, py)"),
                    definition="Year-over-year growth of Total Revenue."))
        add(Measure("Profit YoY %", "derived", base="Total Profit", time_intelligence="yoy",
                    fmt="percent",
                    dax=("VAR cy = [Total Profit]\n"
                         "VAR py = CALCULATE([Total Profit], SAMEPERIODLASTYEAR('Date'[Date]))\n"
                         "RETURN DIVIDE(cy - py, py)"),
                    definition="Year-over-year growth of Total Profit."))
        add(Measure("Quantity YoY %", "derived", base="Total Quantity", time_intelligence="yoy",
                    fmt="percent", dax="Year-over-year growth of Total Quantity.",
                    definition="Year-over-year growth of units sold."))
        add(Measure("Target Achievement %", "ratio", numerator="Net Sales", denominator="__target__",
                    fmt="percent", dax="DIVIDE([Total Revenue], SUM(Users[Sales Target]))",
                    definition="Total Revenue divided by the sum of sales-rep targets."))
        return m

    # ---------- dimensions ----------
    def _build_dimensions(self) -> dict[str, Dimension]:
        d: dict[str, Dimension] = {}

        def add(dim: Dimension):
            d[dim.name] = dim

        # From the Sales fact directly
        add(Dimension("Category", "Category", "Sales", "Category"))
        add(Dimension("Sales Channel", "Sales Channel", "Sales", "Sales Channel"))
        add(Dimension("Order Status", "Order Status", "Sales", "Order Status"))
        add(Dimension("Payment Method", "Payment Method", "Sales", "Payment Method"))
        add(Dimension("Year", "Year", "Sales", "Year", is_time=True, time_grain="year"))
        add(Dimension("Quarter", "Quarter", "Sales", "Quarter", is_time=True, time_grain="quarter"))
        add(Dimension("Month", "Month", "Sales", "Month", is_time=True, time_grain="month"))
        add(Dimension("Order Date", "Order Date", "Sales", "Order Date", is_time=True, time_grain="date"))
        # From Customers
        add(Dimension("Country", "Customer Country", "Customers", "Country"))
        add(Dimension("City", "Customer City", "Customers", "City"))
        add(Dimension("Segment", "Customer Segment", "Customers", "Segment"))
        add(Dimension("Customer", "Customer Name", "Customers", "Customer ID"))
        # From Products
        add(Dimension("Product", "Product Name", "Products", "Product Name"))
        add(Dimension("Sub Category", "Product Sub Category", "Products", "Sub Category"))
        add(Dimension("Brand", "Product Brand", "Products", "Brand"))
        add(Dimension("Supplier", "Product Supplier", "Products", "Supplier"))
        # From Users (sales reps)
        add(Dimension("Salesperson", "Rep Name", "Users", "Name"))
        add(Dimension("Role", "Rep Role", "Users", "Role"))
        add(Dimension("Department", "Rep Department", "Users", "Department"))
        add(Dimension("Rep Country", "Rep Country", "Users", "Country"))
        return d

    # ===================================================================== #
    #  Generic profile — builds the catalog from ANY model's own metadata,
    #  so a different Power BI report can be loaded without code changes.
    # ===================================================================== #
    def _has_dates(self) -> bool:
        return any(dt in ("dateTime", "date")
                   for dt in self._type_map.get(self.fact_table, {}).values())

    def _build_fact_view_generic(self) -> list[dict]:
        fact_rows = self.tables[self.fact_table.lower()]
        fact_cols = set(self._type_map.get(self.fact_table, {}).keys())

        # Deterministic naming plan for joined dimension columns (avoid collisions).
        self._genmap: dict[tuple[str, str], str] = {(self.fact_table, c): c for c in fact_cols}
        used = set(fact_cols) | {"Order Date", "Year", "Quarter", "Month"}
        rels = [r for r in self.meta.get("relationships", []) if r["fromTable"] == self.fact_table]
        for r in rels:
            tt = r["toTable"]
            for c in self._type_map.get(tt, {}):
                if c == r["toColumn"]:
                    continue
                name = c if c not in used else f"{tt} {c}"
                used.add(name)
                self._genmap[(tt, c)] = name

        dim_idx = {(r["toTable"], r["fromColumn"]): self._index(r["toTable"].lower(), r["toColumn"])
                   for r in rels}
        dcol = self.date_column
        out = []
        for s in fact_rows:
            row = dict(s)
            d = s.get(dcol)
            if isinstance(d, date):
                row["Order Date"] = d
                row["Year"] = d.year
                row["Month"] = d.month
                row["Quarter"] = f"Q{(d.month - 1) // 3 + 1}"
            for r in rels:
                tt = r["toTable"]
                drow = dim_idx[(tt, r["fromColumn"])].get(s.get(r["fromColumn"]), {})
                for dc, dv in drow.items():
                    if dc == r["toColumn"]:
                        continue
                    row[self._genmap[(tt, dc)]] = dv
            out.append(row)
        return out

    def _measure_from_spec(self, s: dict) -> Measure:
        where = tuple(s["where"]) if s.get("where") else None
        return Measure(
            name=s["name"], kind=s.get("kind", "sum"), column=s.get("column"),
            numerator=s.get("numerator"), denominator=s.get("denominator"),
            where=where, fmt=s.get("format", s.get("fmt", "number")),
            dax=s.get("dax", ""), definition=s.get("definition", ""),
            time_intelligence=s.get("time_intelligence"), base=s.get("base"),
        )

    def _build_measures_generic(self) -> dict[str, Measure]:
        m: dict[str, Measure] = {}
        specs = self.meta.get("measureSpecs")
        if specs:
            for s in specs:
                m[s["name"]] = self._measure_from_spec(s)
        else:
            for t in self.meta.get("tables", []):
                for meas in t.get("measures", []):
                    parsed = self._parse_dax_measure(meas)
                    if parsed:
                        m[parsed.name] = parsed
        # Guarantee at least one measure: sum every numeric fact column.
        if not m:
            for col, dt in self._type_map.get(self.fact_table, {}).items():
                if dt in ("double", "int64") and col not in ("Year", "Month"):
                    m[f"Total {col}"] = Measure(f"Total {col}", "sum", column=col, fmt="number",
                                                dax=f"SUM({self.fact_table}[{col}])")
        return m

    def _parse_dax_measure(self, meas: dict) -> Optional[Measure]:
        """Best-effort parse of a model measure's DAX into an executable spec.
        Unsupported expressions are skipped (the measure simply isn't offered)."""
        name = meas["name"]
        expr = meas.get("expression", "")
        if isinstance(expr, list):
            expr = " ".join(expr)
        expr = " ".join(expr.split())
        fmt = _guess_format(name, meas.get("formatString", ""))
        defn = meas.get("definition", "")
        col_re = r"'?[\w ]+'?\[([^\]]+)\]"
        import re as _re
        if _re.fullmatch(rf"SUM\(\s*{col_re}\s*\)", expr):
            return Measure(name, "sum", column=_re.search(col_re, expr).group(1), fmt=fmt, dax=expr, definition=defn)
        if _re.fullmatch(rf"AVERAGE\(\s*{col_re}\s*\)", expr):
            return Measure(name, "avg", column=_re.search(col_re, expr).group(1), fmt=fmt, dax=expr, definition=defn)
        if _re.fullmatch(r"COUNTROWS\(\s*'?[\w ]+'?\s*\)", expr):
            return Measure(name, "count", column="*", fmt="int", dax=expr, definition=defn)
        if _re.fullmatch(rf"DISTINCTCOUNT\(\s*{col_re}\s*\)", expr):
            return Measure(name, "distinct", column=_re.search(col_re, expr).group(1), fmt="int", dax=expr, definition=defn)
        return None

    def _auto_dimensions(self) -> dict[str, Dimension]:
        d: dict[str, Dimension] = {}
        # fact string columns
        for col, dt in self._type_map.get(self.fact_table, {}).items():
            if dt == "string":
                d[col] = Dimension(col, self._genmap.get((self.fact_table, col), col),
                                   self.fact_table, col)
        # dimension-table string columns
        for r in self.meta.get("relationships", []):
            if r["fromTable"] != self.fact_table:
                continue
            tt = r["toTable"]
            for col, dt in self._type_map.get(tt, {}).items():
                if dt == "string" and col != r["toColumn"] and (tt, col) in self._genmap:
                    label = col if col not in d else f"{tt} {col}"
                    d[label] = Dimension(label, self._genmap[(tt, col)], tt, col)
        return d

    def _build_dimensions_generic(self) -> dict[str, Dimension]:
        d: dict[str, Dimension] = {}
        dims_meta = self.meta.get("dimensions")
        canon = {"year": "Year", "quarter": "Quarter", "month": "Month", "date": "Order Date"}
        if dims_meta:
            for dm in dims_meta:
                name, table, col = dm["name"], dm.get("table", self.fact_table), dm["column"]
                if dm.get("isTime"):
                    grain = dm.get("grain", "date")
                    d[name] = Dimension(name, canon.get(grain, "Order Date"), table, col,
                                        is_time=True, time_grain=grain)
                else:
                    d[name] = Dimension(name, self._genmap.get((table, col), col), table, col)
        else:
            d.update(self._auto_dimensions())
        if self._has_dates() and not any(x.is_time for x in d.values()):
            for g, lbl in (("year", "Year"), ("quarter", "Quarter"), ("month", "Month")):
                d[lbl] = Dimension(lbl, canon[g], self.fact_table, self.date_column,
                                   is_time=True, time_grain=g)
        return d

    # ---------- synonyms ----------
    # Map dimension-focused synonym keys (from the model json) to catalog names.
    SYNONYM_TO_FIELD = {
        "Country": "Country", "Category": "Category", "Sub Category": "Sub Category",
        "Product Name": "Product", "Segment": "Segment", "Sales Channel": "Sales Channel",
        "Payment Method": "Payment Method", "Order Status": "Order Status", "Brand": "Brand",
        "Month": "Month", "Quarter": "Quarter", "Year": "Year", "City": "City",
        "Supplier": "Supplier", "Role": "Role", "Name": "Salesperson",
    }

    def _build_synonym_index(self) -> list[tuple[str, str, str]]:
        """Return [(phrase, role, field_name)] sorted by phrase length (desc)."""
        idx: list[tuple[str, str, str]] = []
        for canonical, words in self.synonyms.items():
            if canonical in self.measures:
                role, fname = "measure", canonical
            elif canonical in self.dimensions:
                role, fname = "dimension", canonical
            elif canonical in self.SYNONYM_TO_FIELD:
                role, fname = "dimension", self.SYNONYM_TO_FIELD[canonical]
            else:
                continue
            phrases = set(words) | {canonical.lower()}
            for p in phrases:
                idx.append((p.lower(), role, fname))
        # index measure/dimension names themselves, plus auto-variants
        # (so "revenue" resolves to "Total Revenue" even without a synonym list).
        for name in self.measures:
            for v in _name_variants(name):
                idx.append((v, "measure", name))
        for name in self.dimensions:
            for v in _name_variants(name):
                idx.append((v, "dimension", name))
        idx.sort(key=lambda t: len(t[0]), reverse=True)
        return idx

    def resolve_terms(self, text: str) -> dict[str, list[str]]:
        """Find every measure/dimension phrase mentioned in ``text``.

        Longer phrases win, and once a span of text is consumed it is not
        reused (so "profit margin" resolves to the measure, not "profit").
        """
        low = " " + text.lower() + " "
        consumed = [False] * len(low)
        measures: list[str] = []
        dims: list[str] = []
        for phrase, role, fname in self._synonym_index:
            for match in re.finditer(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", low):
                s, e = match.start(), match.end()
                if any(consumed[s:e]):
                    continue
                for i in range(s, e):
                    consumed[i] = True
                if role == "measure" and fname not in measures:
                    measures.append(fname)
                elif role == "dimension" and fname not in dims:
                    dims.append(fname)
        return {"measures": measures, "dimensions": dims}

    # ---------- introspection helpers ----------
    def distinct_values(self, dim_name: str) -> list[Any]:
        dim = self.dimensions[dim_name]
        vals = {r.get(dim.column) for r in self.fact if r.get(dim.column) is not None}
        return sorted(vals, key=lambda x: (str(type(x)), x))

    def find_value_dimension(self, token: str) -> Optional[tuple[str, Any]]:
        """Given a literal like 'UK' or 'Electronics', find which dimension it
        belongs to and the exact stored value."""
        t = token.strip().lower()
        for dim_name, dim in self.dimensions.items():
            if dim.is_time:
                continue
            for v in self.distinct_values(dim_name):
                if str(v).lower() == t:
                    return dim_name, v
        return None

    def categorical_dimensions(self) -> list[str]:
        """Non-time dimension names, in catalog order (used by the planner)."""
        return [n for n, d in self.dimensions.items() if not d.is_time]

    def summary(self) -> dict:
        return {
            "name": self.meta.get("name"),
            "tables": [
                {
                    "name": t["name"],
                    "rowCount": t["rowCount"],
                    "columns": [c["name"] for c in t["columns"]],
                }
                for t in self.meta["tables"]
            ],
            "relationships": self.meta["relationships"],
            "measures": [
                {"name": m.name, "format": m.fmt, "dax": m.dax, "definition": m.definition}
                for m in self.measures.values()
            ],
            "dimensions": [
                {"name": d.name, "table": d.table, "isTime": d.is_time}
                for d in self.dimensions.values()
            ],
            "years": self.years,
        }


_STRIP_PREFIXES = ("total ", "avg ", "average ", "number of ", "count of ", "sum of ")


def _name_variants(name: str) -> set[str]:
    """Lowercased forms of a field name for matching, e.g.
    'Total Revenue' -> {'total revenue', 'revenue'}; 'Profit Margin %' -> {..., 'profit margin'}."""
    low = name.lower().strip()
    out = {low}
    stripped = low.rstrip("%").strip()
    if stripped:
        out.add(stripped)
    for pre in _STRIP_PREFIXES:
        for base in (low, stripped):
            if base.startswith(pre) and len(base) > len(pre) + 2:
                out.add(base[len(pre):].strip())
    return {v for v in out if len(v) >= 3}


def _guess_format(name: str, format_string: str) -> str:
    """Infer a display format for a generic measure from its name / DAX format string."""
    n = name.lower()
    fs = (format_string or "").lower()
    if "%" in n or "%" in fs or "rate" in n or "margin" in n or "yoy" in n:
        return "percent"
    if any(w in n for w in ("revenue", "sales", "charge", "cost", "amount", "price",
                            "reimburs", "profit", "value", "spend", "payment")) or "$" in fs:
        return "currency"
    if any(w in n for w in ("count", "orders", "number", "encounters", "admissions",
                            "visits", "patients", "quantity", "units")):
        return "int"
    return "number"


# --------------------------------------------------------------------------- #
#  Dataset registry — discovers the reports the chatbot can switch between.
# --------------------------------------------------------------------------- #
DATASETS_DIR = os.path.join(os.path.dirname(HERE), "datasets")


class DatasetRegistry:
    """Discovers available datasets and lazily loads their SemanticModel.

    A dataset is a folder containing ``semantic_model.json`` + its CSVs:
      * the built-in ``data/`` folder  -> id "sales" (the default report)
      * every subfolder of ``datasets/`` -> one additional report
    """

    def __init__(self):
        self._dirs: dict[str, str] = {}
        self._order: list[str] = []
        self._cache: dict[str, SemanticModel] = {}
        self._discover()

    def _discover(self) -> None:
        # default (sales) dataset first
        if os.path.exists(os.path.join(DATA_DIR, "semantic_model.json")):
            self._dirs["sales"] = DATA_DIR
            self._order.append("sales")
        if os.path.isdir(DATASETS_DIR):
            for name in sorted(os.listdir(DATASETS_DIR)):
                path = os.path.join(DATASETS_DIR, name)
                if os.path.isfile(os.path.join(path, "semantic_model.json")):
                    self._dirs[name] = path
                    self._order.append(name)

    def ids(self) -> list[str]:
        return list(self._order)

    def default_id(self) -> str:
        return self._order[0] if self._order else "sales"

    def has(self, ds_id: str) -> bool:
        return ds_id in self._dirs

    def get(self, ds_id: str) -> SemanticModel:
        if ds_id not in self._dirs:
            raise KeyError(ds_id)
        if ds_id not in self._cache:
            self._cache[ds_id] = SemanticModel(self._dirs[ds_id])
        return self._cache[ds_id]

    def catalog(self) -> list[dict]:
        """Lightweight listing for the UI picker (loads each model once)."""
        out = []
        for ds_id in self._order:
            try:
                m = self.get(ds_id)
                out.append({
                    "id": ds_id,
                    "name": m.meta.get("name", ds_id),
                    "description": m.meta.get("description", ""),
                    "tables": len(m.meta.get("tables", [])),
                    "measures": len(m.measures),
                    "years": m.years,
                })
            except Exception as exc:  # noqa: BLE001 - a broken dataset shouldn't hide the rest
                out.append({"id": ds_id, "name": ds_id, "error": str(exc)})
        return out


_REGISTRY: Optional[DatasetRegistry] = None


def get_registry() -> DatasetRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = DatasetRegistry()
    return _REGISTRY


def get_model() -> SemanticModel:
    """Backward-compatible accessor for the default (sales) model."""
    return get_registry().get(get_registry().default_id())

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

        self.tables: dict[str, list[dict]] = {}
        for tname in ("sales", "customers", "users", "products"):
            self.tables[tname] = self._load_csv(os.path.join(data_dir, f"{tname}.csv"))

        self.fact: list[dict] = self._build_fact_view()
        self.measures: dict[str, Measure] = self._build_measures()
        self.dimensions: dict[str, Dimension] = self._build_dimensions()
        self.synonyms: dict[str, list[str]] = self.meta.get("synonyms", {})
        self.definitions: dict[str, str] = self.meta.get("definitions", {})
        self._synonym_index = self._build_synonym_index()
        self.years = sorted({r["Year"] for r in self.fact if r.get("Year") is not None})

    # ---------- loading / typing ----------
    NUMERIC_COLS = {
        "Year", "Month", "Quantity", "Unit Price", "Unit Cost", "Gross Sales",
        "Discount %", "Discount Amount", "Net Sales", "Total Cost", "Profit",
        "Profit Margin %", "Credit Limit", "Sales Target", "Stock Quantity",
        "Reorder Level", "Weight (kg)", "Rating",
    }
    INT_COLS = {"Year", "Month", "Quantity", "Stock Quantity", "Reorder Level"}
    DATE_COLS = {"Order Date", "Ship Date", "Registration Date", "Join Date"}

    def _load_csv(self, path: str) -> list[dict]:
        rows: list[dict] = []
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                out: dict[str, Any] = {}
                for k, v in r.items():
                    out[k] = self._coerce(k, v)
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
        # also index measure/dimension names themselves
        for name in self.measures:
            idx.append((name.lower(), "measure", name))
        for name in self.dimensions:
            idx.append((name.lower(), "dimension", name))
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
        for dim_name in ("Country", "Category", "Segment", "Sales Channel", "Order Status",
                         "Payment Method", "Brand", "Sub Category", "Product", "Rep Country",
                         "Role", "Department", "City", "Supplier"):
            for v in self.distinct_values(dim_name):
                if str(v).lower() == t:
                    return dim_name, v
        return None

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


# Singleton accessor
_MODEL: Optional[SemanticModel] = None


def get_model() -> SemanticModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = SemanticModel()
    return _MODEL

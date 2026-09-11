#!/usr/bin/env python3
"""
extract_from_pbit.py
--------------------
Extract the *real* Power BI semantic model from a .pbit template into a form the
chatbot backend can consume:

  * ``chatbot/data/<table>.csv``  – the row data embedded in each M partition.
  * ``chatbot/data/semantic_model.json`` – model metadata (tables, columns,
    measures, relationships) plus a business synonym dictionary.

A .pbit stores its model as an editable ``DataModelSchema`` JSON (unlike a .pbix
whose model is a compiled binary), and in this project the source data is
embedded inline inside each table's Power Query ``#table(...)`` expression, so the
template is fully self-contained.  That is what makes this extraction possible
without a live Power BI tenant.

Usage:
    python scripts/extract_from_pbit.py [path/to/model.pbit]

Only the Python standard library is used.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
import zipfile
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # chatbot/
REPO = os.path.dirname(ROOT)                        # repo root
DATA_DIR = os.path.join(ROOT, "data")

DEFAULT_PBIT = os.path.join(REPO, "SalesAnalytics_Complete.pbit")

# M scalar type -> logical type used by the chatbot
M_TYPE_MAP = {
    "text": "string",
    "number": "double",
    "Int64.Type": "int64",
    "date": "date",
    "datetime": "dateTime",
    "logical": "boolean",
}


# --------------------------------------------------------------------------- #
#  Read DataModelSchema out of the .pbit (a zip archive)
# --------------------------------------------------------------------------- #
def read_model(pbit_path: str) -> dict[str, Any]:
    with zipfile.ZipFile(pbit_path) as z:
        raw = z.read("DataModelSchema")
    # DataModelSchema is UTF-8 (BOM-less) or UTF-16-LE depending on the writer.
    for enc in ("utf-8-sig", "utf-8", "utf-16-le"):
        try:
            return json.loads(raw.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise RuntimeError("Could not decode DataModelSchema")


# --------------------------------------------------------------------------- #
#  Parse a Power Query ``#table(type table [...], {...})`` literal
# --------------------------------------------------------------------------- #
def partition_expression(table: dict[str, Any]) -> str:
    parts = table.get("partitions", [])
    if not parts:
        return ""
    expr = parts[0].get("source", {}).get("expression", "")
    if isinstance(expr, list):
        expr = "\n".join(expr)
    return expr


def parse_columns_from_mtable(expr: str) -> list[tuple[str, str]]:
    """Return [(column_name, logical_type)] from ``type table [ ... ]``."""
    m = re.search(r"type\s+table\s*\[(.*?)\]\s*,\s*\{", expr, re.DOTALL)
    if not m:
        return []
    header = m.group(1)
    cols: list[tuple[str, str]] = []
    # Each entry looks like:  #"Order Date" = date   |   Quantity = Int64.Type
    for field in re.split(r",(?![^\{]*\})", header):
        fm = re.match(r'\s*(?:#"([^"]+)"|([A-Za-z0-9_]+))\s*=\s*([A-Za-z0-9_.]+)', field)
        if not fm:
            continue
        name = fm.group(1) or fm.group(2)
        mtype = fm.group(3)
        cols.append((name, M_TYPE_MAP.get(mtype, "string")))
    return cols


def parse_rows_from_mtable(expr: str) -> list[list[Any]]:
    """Return the list of row tuples from the ``{ {...}, {...} }`` block."""
    # Isolate the outer row list: everything after the column-type ``], {``
    start = expr.find("],")
    brace = expr.find("{", start)
    if brace == -1:
        return []
    # Walk to the matching closing brace of the outer list.
    depth = 0
    end = -1
    in_str = False
    i = brace
    while i < len(expr):
        ch = expr[i]
        if ch == '"' and expr[i - 1] != "\\":
            in_str = not in_str
        elif not in_str:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        i += 1
    if end == -1:
        return []
    block = expr[brace : end + 1]

    rows: list[list[Any]] = []
    # Each row is a brace group one level deep.
    for row_match in re.finditer(r"\{([^{}]*)\}", block):
        body = row_match.group(1).strip()
        if not body:
            continue
        rows.append(_parse_row_values(body))
    return rows


def _parse_row_values(body: str) -> list[Any]:
    """Parse ``"a", 12, null, 3.5`` into python values."""
    values: list[Any] = []
    for tok in _split_top_level(body):
        tok = tok.strip()
        if tok == "" or tok.lower() == "null":
            values.append(None)
        elif tok.startswith('"') and tok.endswith('"'):
            # Unescape M string ("" -> ")
            values.append(tok[1:-1].replace('""', '"').replace('\\"', '"'))
        else:
            try:
                values.append(ast.literal_eval(tok))
            except (ValueError, SyntaxError):
                values.append(tok)
    return values


def _split_top_level(body: str) -> list[str]:
    out: list[str] = []
    cur = []
    in_str = False
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '"':
            # handle "" escape inside strings
            if in_str and i + 1 < len(body) and body[i + 1] == '"':
                cur.append('""')
                i += 2
                continue
            in_str = not in_str
            cur.append(ch)
        elif ch == "," and not in_str:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    if cur:
        out.append("".join(cur))
    return out


# --------------------------------------------------------------------------- #
#  Business synonym dictionary – maps everyday language to model fields.
#  This is the "semantic model awareness" layer: it lets a user say "revenue"
#  and have the AI resolve it to the ``Total Revenue`` measure.
# --------------------------------------------------------------------------- #
SYNONYMS = {
    # measures
    "Total Revenue": ["revenue", "sales", "total sales", "turnover", "income", "net sales", "gmv"],
    "Total Profit": ["profit", "earnings", "net profit", "margin value", "gross profit"],
    "Profit Margin %": ["margin", "profit margin", "profitability", "margin percent"],
    "Total Orders": ["orders", "order count", "number of orders", "transactions", "deals"],
    "Total Customers": ["customers", "customer count", "buyers", "clients", "unique customers"],
    "Total Quantity": ["quantity", "units", "units sold", "volume", "qty"],
    "Avg Order Value": ["aov", "average order value", "avg order", "basket size"],
    "Total Returns": ["returns", "returned orders"],
    "Return Rate %": ["return rate", "returns rate", "return percentage"],
    "Revenue YoY %": ["yoy", "year over year", "year on year", "growth", "sales growth", "annual growth", "yoy growth"],
    "Profit YoY %": ["profit growth", "profit yoy", "profit year over year"],
    "Revenue YTD": ["ytd", "year to date", "revenue ytd"],
    "Target Achievement %": ["target", "quota", "target achievement", "attainment", "vs target"],
    # dimensions
    "Country": ["country", "countries", "nation", "geography", "region", "geo", "location"],
    "Category": ["category", "categories", "product category", "product type"],
    "Sub Category": ["subcategory", "sub category", "sub-category"],
    "Product Name": ["product", "products", "item", "sku", "product name"],
    "Segment": ["segment", "customer segment", "customer type"],
    "Sales Channel": ["channel", "sales channel", "online", "offline"],
    "Payment Method": ["payment", "payment method", "payment type"],
    "Order Status": ["status", "order status", "state"],
    "Brand": ["brand", "brands", "manufacturer"],
    "Month": ["month", "monthly", "by month"],
    "Quarter": ["quarter", "quarterly", "by quarter"],
    "Year": ["year", "yearly", "annual", "by year"],
    "City": ["city", "cities", "town"],
    "Supplier": ["supplier", "suppliers", "vendor"],
    "Role": ["role", "job title", "position"],
    "Name": ["salesperson", "sales rep", "rep", "agent", "employee", "user", "seller"],
}

# Human-readable business definitions surfaced to the AI + the UI.
DEFINITIONS = {
    "Total Revenue": "Sum of Net Sales (gross sales after discounts).",
    "Total Profit": "Sum of Profit (Net Sales minus Total Cost).",
    "Profit Margin %": "Total Profit divided by Total Revenue.",
    "Revenue YoY %": "Year-over-year growth of Total Revenue vs the same period last year.",
    "Profit YoY %": "Year-over-year growth of Total Profit vs the same period last year.",
    "Avg Order Value": "Total Revenue divided by number of orders.",
    "Return Rate %": "Returned orders as a share of all orders.",
    "Target Achievement %": "Total Revenue divided by the sum of sales-rep targets.",
}


def build_semantic_model(model: dict[str, Any]) -> dict[str, Any]:
    mdl = model["model"]
    tables_meta = []
    for t in mdl.get("tables", []):
        name = t["name"]
        expr = partition_expression(t)
        cols = parse_columns_from_mtable(expr)
        columns = [
            {
                "name": c["name"],
                "dataType": c["dataType"],
                "summarizeBy": c.get("summarizeBy", "none"),
            }
            for c in t.get("columns", [])
        ]
        measures = [
            {
                "name": m["name"],
                "expression": _flatten(m.get("expression", "")),
                "formatString": m.get("formatString", ""),
                "definition": DEFINITIONS.get(m["name"], ""),
            }
            for m in t.get("measures", [])
        ]
        tables_meta.append(
            {
                "name": name,
                "columns": columns,
                "measures": measures,
                "rowCount": None,  # filled by caller after csv write
                "isFact": name == "Sales",
            }
        )

    relationships = [
        {
            "name": r.get("name"),
            "fromTable": r["fromTable"],
            "fromColumn": r["fromColumn"],
            "toTable": r["toTable"],
            "toColumn": r["toColumn"],
            "crossFilteringBehavior": r.get("crossFilteringBehavior", "oneDirection"),
            "cardinality": "manyToOne",
        }
        for r in mdl.get("relationships", [])
    ]

    return {
        "name": mdl.get("name", "SalesAnalytics"),
        "factTable": "Sales",
        "dateColumn": "Order Date",
        "tables": tables_meta,
        "relationships": relationships,
        "synonyms": SYNONYMS,
        "definitions": DEFINITIONS,
    }


def _flatten(expr: Any) -> str:
    if isinstance(expr, list):
        return "\n".join(expr)
    return expr


# --------------------------------------------------------------------------- #
#  Main
# --------------------------------------------------------------------------- #
def main() -> None:
    pbit_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PBIT
    if not os.path.exists(pbit_path):
        raise SystemExit(f"PBIT not found: {pbit_path}")

    os.makedirs(DATA_DIR, exist_ok=True)
    model = read_model(pbit_path)
    sm = build_semantic_model(model)

    import csv

    row_counts: dict[str, int] = {}
    for t in model["model"]["tables"]:
        name = t["name"]
        expr = partition_expression(t)
        cols = parse_columns_from_mtable(expr)
        rows = parse_rows_from_mtable(expr)
        col_names = [c for c, _ in cols]
        out_path = os.path.join(DATA_DIR, f"{name.lower()}.csv")
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(col_names)
            for r in rows:
                # pad/trim to column count
                r = (r + [None] * len(col_names))[: len(col_names)]
                w.writerow(["" if v is None else v for v in r])
        row_counts[name] = len(rows)
        print(f"  {name:<12} {len(rows):>6} rows  {len(col_names)} cols -> {os.path.basename(out_path)}")

    for tm in sm["tables"]:
        tm["rowCount"] = row_counts.get(tm["name"], 0)

    with open(os.path.join(DATA_DIR, "semantic_model.json"), "w", encoding="utf-8") as fh:
        json.dump(sm, fh, indent=2)
    print(f"\nSemantic model -> {os.path.join(DATA_DIR, 'semantic_model.json')}")
    print(f"Tables: {[t['name'] for t in sm['tables']]}")
    print(f"Relationships: {len(sm['relationships'])}")
    total_measures = sum(len(t['measures']) for t in sm['tables'])
    print(f"Measures: {total_measures}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
generate_pbix.py
================
Creates Sales_Dashboard.pbix by:
1. Reading the 4 CSV files from powerbi_data/
2. Embedding ALL data as inline M (#table) queries in DataModelSchema
3. Reusing the XPress9-compressed DataModel from SalesAnalytics_Final.pbix
   (which already has the Sales/Customers/Users schema + DataModel structure)
4. Building a complete 5-page Report/Layout
5. Writing Sales_Dashboard.pbix to /home/user/newm/

Priority: opens in Power BI Desktop without error.
"""

import csv, io, json, os, shutil, uuid, zipfile

# ── Paths ──────────────────────────────────────────────────────────────────────
DATA_DIR    = "/home/user/newm/powerbi_data"
SOURCE_PBIX = "/home/user/newm/SalesAnalytics_Final.pbix"   # provides valid DataModel binary
OUTPUT_PBIX = "/home/user/newm/Sales_Dashboard.pbix"

# ── Colour palette ─────────────────────────────────────────────────────────────
TEAL   = "#01B8AA"; DARK   = "#252423"; RED    = "#FD625E"
YELLOW = "#F2C80F"; BLUE   = "#118DFF"; PURPLE = "#8B00FF"
GREEN  = "#00B050"; DGRAY  = "#374649"; ORANGE = "#FF6B35"
WHITE  = "#FFFFFF"; LTGRAY = "#F3F2F1"; SLATE  = "#5F6B6D"
CARD_ACCENTS = [TEAL, GREEN, BLUE, YELLOW, RED, PURPLE]

# ── Helpers ────────────────────────────────────────────────────────────────────

def uid() -> str:
    return uuid.uuid4().hex

def vname() -> str:
    return uuid.uuid4().hex[:20]

def js(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}

def clr(c):
    return {"solid": {"color": lit(f"'{c}'")}}

# ── CSV loading ────────────────────────────────────────────────────────────────

def load_csv(path: str) -> tuple[list[str], list[list]]:
    """Return (headers, rows) from a CSV file."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        headers = next(reader)
        rows = list(reader)
    return headers, rows

# ── M-query builder ─────────────────────────────────────────────────────────────

def mq(v, dtype: str) -> str:
    """Format a CSV string value for an M table cell."""
    if v is None or v == "" or v == "nan":
        return "null"
    if dtype in ("Int64.Type", "number"):
        try:
            if dtype == "Int64.Type":
                return str(int(float(v)))
            else:
                f = float(v)
                return str(int(f)) if f == int(f) else str(f)
        except ValueError:
            return "null"
    if dtype == "date":
        return f'"{v[:10]}"'
    # text / logical – escape inner quotes
    escaped = str(v).replace('"', '""')
    return f'"{escaped}"'


def build_m_inline(headers: list[str], rows: list[list],
                   col_types: dict[str, str], max_rows: int | None = None) -> list[str]:
    """Return M expression lines for an inline #table with embedded data.

    col_types: {column_name: m_type_string}
    Only columns present in col_types are included.
    """
    cols_used = [h for h in headers if h in col_types]
    type_decl = ", ".join(f'#"{c}" = {col_types[c]}' for c in cols_used)
    idx_map   = {h: headers.index(h) for h in cols_used}

    data_rows = rows if max_rows is None else rows[:max_rows]

    m_rows = []
    for row in data_rows:
        vals = ", ".join(mq(row[idx_map[c]], col_types[c]) for c in cols_used)
        m_rows.append(f"    {{{vals}}}")

    lines = [
        "let",
        f"  Source = #table(type table [{type_decl}], {{",
    ]
    lines.append(",\n".join(m_rows))
    lines += ["  })", "in", "  Source"]
    return lines

# ── Column type maps ───────────────────────────────────────────────────────────

SALES_TYPES = {
    "Order ID": "text", "Order Date": "date", "Year": "Int64.Type",
    "Month": "Int64.Type", "Quarter": "text", "Customer ID": "text",
    "Product ID": "text", "User ID": "text", "Category": "text",
    "Quantity": "Int64.Type", "Unit Price": "number", "Unit Cost": "number",
    "Gross Sales": "number", "Discount %": "number", "Discount Amount": "number",
    "Net Sales": "number", "Total Cost": "number", "Profit": "number",
    "Profit Margin %": "number", "Sales Channel": "text",
    "Order Status": "text", "Ship Date": "date", "Payment Method": "text",
}

CUST_TYPES = {
    "Customer ID": "text", "First Name": "text", "Last Name": "text",
    "Email": "text", "Phone": "text", "Address": "text", "City": "text",
    "Country": "text", "Postal Code": "text", "Segment": "text",
    "Registration Date": "date", "Credit Limit": "number",
}

PROD_TYPES = {
    "Product ID": "text", "Product Name": "text", "Category": "text",
    "Sub Category": "text", "Brand": "text", "Unit Cost": "number",
    "Unit Price": "number", "Profit Margin %": "number",
    "Stock Quantity": "Int64.Type", "Reorder Level": "Int64.Type",
    "Supplier": "text", "Weight (kg)": "number", "Rating": "number",
}

USERS_TYPES = {
    "User ID": "text", "Name": "text", "First Name": "text",
    "Last Name": "text", "Email": "text", "Role": "text",
    "Department": "text", "Country": "text", "Location": "text",
    "Phone": "text", "Join Date": "date", "Manager ID": "text",
    "Sales Target": "number",
}

# ── DataModelSchema builder ────────────────────────────────────────────────────

def make_col_entry(name: str, dtype: str) -> dict:
    m2tms = {
        "text": "string", "date": "dateTime",
        "Int64.Type": "int64", "number": "double",
    }
    tms_type = m2tms.get(dtype, "string")
    summarize = "none" if tms_type in ("string", "dateTime") else "sum"
    return {
        "name": name,
        "dataType": tms_type,
        "lineageTag": uid(),
        "summarizeBy": summarize,
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}],
    }


def build_schema(
    sales_headers, sales_rows,
    cust_headers,  cust_rows,
    prod_headers,  prod_rows,
    users_headers, users_rows,
) -> dict:
    """Build the DataModelSchema dict (written as UTF-8 JSON in the PBIX)."""

    # ── Sales table ──
    sales_cols = [make_col_entry(h, SALES_TYPES[h])
                  for h in sales_headers if h in SALES_TYPES]
    sales_m    = build_m_inline(sales_headers, sales_rows, SALES_TYPES)
    sales_measures = [
        {"name": "Total Revenue",        "expression": "SUM(Sales[Net Sales])",           "lineageTag": uid(), "formatString": "#,0.00"},
        {"name": "Total Profit",         "expression": "SUM(Sales[Profit])",              "lineageTag": uid(), "formatString": "#,0.00"},
        {"name": "Profit Margin %",      "expression": "DIVIDE(SUM(Sales[Profit]),SUM(Sales[Net Sales]),0)", "lineageTag": uid(), "formatString": "0.0%"},
        {"name": "Total Orders",         "expression": "DISTINCTCOUNT(Sales[Order ID])",  "lineageTag": uid(), "formatString": "#,0"},
        {"name": "Avg Order Value",      "expression": "DIVIDE(SUM(Sales[Net Sales]),DISTINCTCOUNT(Sales[Order ID]),0)", "lineageTag": uid(), "formatString": "#,0.00"},
        {"name": "Total Returns",        "expression": "CALCULATE(COUNTROWS(Sales),Sales[Order Status]=\"Returned\")", "lineageTag": uid(), "formatString": "#,0"},
        {"name": "Return Rate %",        "expression": "DIVIDE([Total Returns],[Total Orders],0)", "lineageTag": uid(), "formatString": "0.0%"},
        {"name": "Total Customers",      "expression": "DISTINCTCOUNT(Sales[Customer ID])", "lineageTag": uid(), "formatString": "#,0"},
        {"name": "Total Gross Sales",    "expression": "SUM(Sales[Gross Sales])",         "lineageTag": uid(), "formatString": "#,0.00"},
        {"name": "Total Discount",       "expression": "SUM(Sales[Discount Amount])",     "lineageTag": uid(), "formatString": "#,0.00"},
        {"name": "Avg Profit Margin",    "expression": "AVERAGE(Sales[Profit Margin %])", "lineageTag": uid(), "formatString": "0.0%"},
        {"name": "Total Quantity",       "expression": "SUM(Sales[Quantity])",            "lineageTag": uid(), "formatString": "#,0"},
        {"name": "Target Achievement %",
         "expression": "DIVIDE([Total Revenue],SUM(Users[Sales Target]),0)",
         "lineageTag": uid(), "formatString": "0.0%"},
        {"name": "Revenue Growth %",
         "expression": (
             "VAR cy = CALCULATE([Total Revenue], Sales[Year] = MAX(Sales[Year]))\n"
             "VAR py = CALCULATE([Total Revenue], Sales[Year] = MAX(Sales[Year]) - 1)\n"
             "RETURN DIVIDE(cy - py, py, 0)"
         ), "lineageTag": uid(), "formatString": "0.0%"},
    ]

    # ── Customers table ──
    cust_cols = [make_col_entry(h, CUST_TYPES[h])
                 for h in cust_headers if h in CUST_TYPES]
    cust_m    = build_m_inline(cust_headers, cust_rows, CUST_TYPES)

    # ── Products table ──
    prod_cols = [make_col_entry(h, PROD_TYPES[h])
                 for h in prod_headers if h in PROD_TYPES]
    prod_m    = build_m_inline(prod_headers, prod_rows, PROD_TYPES)
    prod_measures = [
        {"name": "Total Products",      "expression": "COUNTROWS(Products)",              "lineageTag": uid(), "formatString": "#,0"},
        {"name": "Avg Product Margin",  "expression": "AVERAGE(Products[Profit Margin %])", "lineageTag": uid(), "formatString": "0.0%"},
        {"name": "Avg Rating",          "expression": "AVERAGE(Products[Rating])",        "lineageTag": uid(), "formatString": "0.0"},
    ]

    # ── Users table ──
    users_cols = [make_col_entry(h, USERS_TYPES[h])
                  for h in users_headers if h in USERS_TYPES]
    users_m    = build_m_inline(users_headers, users_rows, USERS_TYPES)
    users_measures = [
        {"name": "Total Sales Target", "expression": "SUM(Users[Sales Target])", "lineageTag": uid(), "formatString": "#,0.00"},
        {"name": "Sales Rep Count",    "expression": "COUNTROWS(Users)",         "lineageTag": uid(), "formatString": "#,0"},
    ]

    rel_tag1 = uid(); rel_tag2 = uid(); rel_tag3 = uid()
    schema = {
        "model": {
            "compatibilityLevel": 1567,
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "tables": [
                {
                    "name": "Sales",
                    "lineageTag": uid(),
                    "columns": sales_cols,
                    "measures": sales_measures,
                    "partitions": [{
                        "name": "Sales",
                        "mode": "import",
                        "source": {"type": "m", "expression": sales_m},
                    }],
                    "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
                },
                {
                    "name": "Customers",
                    "lineageTag": uid(),
                    "columns": cust_cols,
                    "partitions": [{
                        "name": "Customers",
                        "mode": "import",
                        "source": {"type": "m", "expression": cust_m},
                    }],
                    "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
                },
                {
                    "name": "Products",
                    "lineageTag": uid(),
                    "columns": prod_cols,
                    "measures": prod_measures,
                    "partitions": [{
                        "name": "Products",
                        "mode": "import",
                        "source": {"type": "m", "expression": prod_m},
                    }],
                    "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
                },
                {
                    "name": "Users",
                    "lineageTag": uid(),
                    "columns": users_cols,
                    "measures": users_measures,
                    "partitions": [{
                        "name": "Users",
                        "mode": "import",
                        "source": {"type": "m", "expression": users_m},
                    }],
                    "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
                },
            ],
            "relationships": [
                {
                    "name": rel_tag1,
                    "fromTable": "Sales", "fromColumn": "Customer ID",
                    "toTable": "Customers", "toColumn": "Customer ID",
                },
                {
                    "name": rel_tag2,
                    "fromTable": "Sales", "fromColumn": "User ID",
                    "toTable": "Users", "toColumn": "User ID",
                },
                {
                    "name": rel_tag3,
                    "fromTable": "Sales", "fromColumn": "Product ID",
                    "toTable": "Products", "toColumn": "Product ID",
                },
            ],
            "cultures": [{"name": "en-US", "linguisticMetadata": {"version": "1.0.0", "language": "en-US"}}],
            "annotations": [{"name": "PBI_QueryOrder", "value": js(["Sales", "Customers", "Products", "Users"])}],
        }
    }
    return schema

# ── Report / Layout builder ───────────────────────────────────────────────────

def vc(x: int, y: int, w: int, h: int, z: int, sv: dict) -> dict:
    """Wrap a singleVisual into a visual container."""
    pos = {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}
    return {
        "x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z,
        "filters": "[]",
        "config": js({
            "name": vname(),
            "layouts": [{"id": 0, "position": pos}],
            "singleVisual": sv,
        }),
        "query": "{}",
        "dataTransforms": "{}",
    }


def make_title_bar(text: str) -> dict:
    sv = {
        "visualType": "textbox",
        "objects": {
            "general": [{
                "properties": {
                    "paragraphs": [{
                        "textRuns": [{
                            "value": text,
                            "textStyle": {
                                "fontWeight": "bold",
                                "color": WHITE,
                                "fontSize": "14pt",
                            },
                        }],
                        "horizontalTextAlignment": "center",
                    }]
                }
            }],
            "background": [{"properties": {
                "show": lit("true"),
                "color": clr(DARK),
                "transparency": lit("0D"),
            }}],
        },
    }
    return vc(0, 0, 1280, 44, 0, sv)


def make_slicer(x: int, y: int, w: int, entity: str, alias: str, col: str,
                z: int, mode: str = "Dropdown") -> dict:
    qref = f"{entity}.{col}"
    sv = {
        "visualType": "slicer",
        "projections": {"Values": [{"queryRef": qref, "active": True}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{
                "Column": {
                    "Expression": {"SourceRef": {"Source": alias}},
                    "Property": col,
                },
                "Name": qref,
                "NativeReferenceName": col,
            }],
        },
        "objects": {"data": [{"properties": {"mode": lit(f"'{mode}'")}}]},
        "drillFilterOtherVisuals": True,
    }
    return vc(x, y, w, 28, z, sv)


def make_card(x: int, y: int, w: int, h: int,
              entity: str, alias: str, col: str,
              agg: int, title: str, z: int,
              accent: str = TEAL, is_measure: bool = False) -> dict:
    """agg: 0=Sum, 1=Avg, 2=Min, 3=Max, 5=CountNonNull"""
    fn_map = {0: "Sum", 1: "Avg", 2: "Min", 3: "Max", 5: "CountNonNull"}
    fn_name = fn_map.get(agg, "Sum")
    qname   = f"{fn_name}({entity}.{col})"

    if is_measure:
        select_item = {
            "Measure": {
                "Expression": {"SourceRef": {"Source": alias}},
                "Property": col,
            },
            "Name": f"{entity}.{col}",
            "NativeReferenceName": title,
        }
        qref = f"{entity}.{col}"
    else:
        select_item = {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {"SourceRef": {"Source": alias}},
                        "Property": col,
                    }
                },
                "Function": agg,
            },
            "Name": qname,
            "NativeReferenceName": title,
        }
        qref = qname

    sv = {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": qref}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [select_item],
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": lit("true"),
                "text": lit(f"'{title}'"),
                "fontColor": clr(SLATE),
                "fontSize": lit("10D"),
            }}],
            "background": [{"properties": {
                "show": lit("true"), "color": clr(WHITE), "transparency": lit("0D"),
            }}],
            "border": [{"properties": {
                "show": lit("true"), "color": clr(accent),
            }}],
            "labels": [{"properties": {
                "color": clr(DARK), "fontSize": lit("18D"), "bold": lit("true"),
            }}],
            "categoryLabels": [{"properties": {"show": lit("false")}}],
        },
    }
    return vc(x, y, w, h, z, sv)


def make_chart(x: int, y: int, w: int, h: int,
               cat_entity: str, cat_alias: str, cat_col: str,
               val_entity: str, val_alias: str, val_col: str,
               agg: int, title: str, z: int,
               vtype: str = "clusteredBarChart",
               legend_entity: str | None = None,
               legend_alias: str | None = None,
               legend_col:   str | None = None) -> dict:
    """Generic chart visual container."""
    fn_map = {0: "Sum", 1: "Avg", 5: "CountNonNull", 6: "Count"}
    fn_name = fn_map.get(agg, "Sum")
    val_qname = f"{fn_name}({val_entity}.{val_col})"
    cat_qname = f"{cat_entity}.{cat_col}"

    frm = [{"Name": cat_alias, "Entity": cat_entity, "Type": 0}]
    if val_alias != cat_alias:
        frm.append({"Name": val_alias, "Entity": val_entity, "Type": 0})

    selects = [
        {
            "Column": {
                "Expression": {"SourceRef": {"Source": cat_alias}},
                "Property": cat_col,
            },
            "Name": cat_qname,
            "NativeReferenceName": cat_col,
        },
        {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {"SourceRef": {"Source": val_alias}},
                        "Property": val_col,
                    }
                },
                "Function": agg,
            },
            "Name": val_qname,
            "NativeReferenceName": val_col,
        },
    ]
    projections = {
        "Category": [{"queryRef": cat_qname, "active": True}],
        "Y": [{"queryRef": val_qname}],
    }

    if legend_entity and legend_alias and legend_col:
        leg_qname = f"{legend_entity}.{legend_col}"
        if legend_alias not in [f["Name"] for f in frm]:
            frm.append({"Name": legend_alias, "Entity": legend_entity, "Type": 0})
        selects.append({
            "Column": {
                "Expression": {"SourceRef": {"Source": legend_alias}},
                "Property": legend_col,
            },
            "Name": leg_qname,
            "NativeReferenceName": legend_col,
        })
        projections["Legend"] = [{"queryRef": leg_qname, "active": True}]

    sv = {
        "visualType": vtype,
        "projections": projections,
        "prototypeQuery": {
            "Version": 2,
            "From": frm,
            "Select": selects,
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": lit("true"),
                "text": lit(f"'{title}'"),
            }}],
        },
    }
    return vc(x, y, w, h, z, sv)


def make_table(x: int, y: int, w: int, h: int,
               entity: str, alias: str, columns: list[tuple], z: int,
               title: str = "") -> dict:
    """Simple table/matrix visual."""
    frm     = [{"Name": alias, "Entity": entity, "Type": 0}]
    selects = []
    rows_proj = []
    vals_proj = []

    for col, agg_fn in columns:
        qname = f"{entity}.{col}"
        if agg_fn is None:
            selects.append({
                "Column": {
                    "Expression": {"SourceRef": {"Source": alias}},
                    "Property": col,
                },
                "Name": qname,
                "NativeReferenceName": col,
            })
            rows_proj.append({"queryRef": qname, "active": True})
        else:
            fn_map = {0: "Sum", 1: "Avg"}
            fn_name = fn_map.get(agg_fn, "Sum")
            qname2 = f"{fn_name}({entity}.{col})"
            selects.append({
                "Aggregation": {
                    "Expression": {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": alias}},
                            "Property": col,
                        }
                    },
                    "Function": agg_fn,
                },
                "Name": qname2,
                "NativeReferenceName": col,
            })
            vals_proj.append({"queryRef": qname2})

    projections = {}
    if rows_proj:
        projections["Rows"] = rows_proj
    if vals_proj:
        projections["Values"] = vals_proj

    sv = {
        "visualType": "tableEx",
        "projections": projections,
        "prototypeQuery": {
            "Version": 2,
            "From": frm,
            "Select": selects,
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": lit("true"),
                "text": lit(f"'{title}'") if title else lit("'Table'"),
            }}],
        },
    }
    return vc(x, y, w, h, z, sv)


# ── Slicers shared across all pages ───────────────────────────────────────────
def page_slicers() -> list[dict]:
    return [
        make_slicer(80,  50, 130, "Sales", "s", "Year",         z=1),
        make_slicer(225, 50, 155, "Sales", "s", "Quarter",      z=2),
        make_slicer(395, 50, 165, "Sales", "s", "Category",     z=3),
        make_slicer(575, 50, 160, "Sales", "s", "Sales Channel",z=4),
    ]


# ── KPI row: 6 cards ──────────────────────────────────────────────────────────
def exec_kpi_cards() -> list[dict]:
    specs = [
        (10,  88, "Net Sales",       0, "Total Revenue",     TEAL),
        (211, 88, "Profit",          0, "Total Profit",      GREEN),
        (412, 88, "Order ID",        5, "Total Orders",      BLUE),
        (613, 88, "Profit Margin %", 1, "Avg Profit Margin", YELLOW),
        (814, 88, "Discount Amount", 0, "Total Discount",    RED),
        (1015,88, "Gross Sales",     0, "Total Gross Sales", PURPLE),
    ]
    cards = []
    for i, (x, y, col, agg, title, accent) in enumerate(specs):
        cards.append(make_card(x, y, 193, 105, "Sales", "s", col, agg,
                               title, z=100+i*10, accent=accent))
    return cards


# ── PAGE 1: Executive Summary ─────────────────────────────────────────────────
def page_executive_summary() -> dict:
    visuals = []
    visuals.append(make_title_bar("Executive Summary"))
    visuals.extend(page_slicers())
    visuals.extend(exec_kpi_cards())

    # Revenue trend line chart
    visuals.append(make_chart(
        10, 210, 1260, 200,
        "Sales", "s", "Order Date",
        "Sales", "s", "Net Sales", 0,
        "Revenue Trend Over Time", z=200,
        vtype="lineChart",
    ))

    # Revenue by Category (bar)
    visuals.append(make_chart(
        10, 425, 400, 270,
        "Sales", "s", "Category",
        "Sales", "s", "Net Sales", 0,
        "Revenue by Category", z=300,
        vtype="clusteredBarChart",
    ))

    # Orders by Sales Channel (donut)
    visuals.append(make_chart(
        420, 425, 415, 270,
        "Sales", "s", "Sales Channel",
        "Sales", "s", "Order ID", 5,
        "Orders by Sales Channel", z=400,
        vtype="donutChart",
    ))

    # Orders by Status (donut)
    visuals.append(make_chart(
        845, 425, 425, 270,
        "Sales", "s", "Order Status",
        "Sales", "s", "Order ID", 5,
        "Orders by Status", z=500,
        vtype="donutChart",
    ))

    # Revenue vs Profit line (stacked)
    visuals.append(make_chart(
        10, 705, 1260, 180,
        "Sales", "s", "Month",
        "Sales", "s", "Profit", 0,
        "Monthly Profit Trend", z=600,
        vtype="lineChart",
    ))

    return {
        "name": "ReportSection1",
        "displayName": "Executive Summary",
        "filters": "[]",
        "ordinal": 0,
        "width": 1280,
        "height": 900,
        "visualContainers": visuals,
        "config": js({
            "relationships": [],
            "objects": {
                "background": [{"properties": {"color": clr(LTGRAY), "transparency": lit("0D")}}],
            },
        }),
    }


# ── PAGE 2: Sales Performance ─────────────────────────────────────────────────
def page_sales_performance() -> dict:
    visuals = []
    visuals.append(make_title_bar("Sales Performance"))
    visuals.extend(page_slicers())
    visuals.extend(exec_kpi_cards())

    # Matrix: Year × Quarter
    visuals.append(make_chart(
        10, 210, 620, 180,
        "Sales", "s", "Year",
        "Sales", "s", "Net Sales", 0,
        "Revenue by Year", z=200,
        vtype="clusteredColumnChart",
    ))

    # Revenue by Quarter
    visuals.append(make_chart(
        645, 210, 625, 180,
        "Sales", "s", "Quarter",
        "Sales", "s", "Net Sales", 0,
        "Revenue by Quarter", z=210,
        vtype="clusteredColumnChart",
    ))

    # Revenue by Payment Method
    visuals.append(make_chart(
        10, 402, 620, 270,
        "Sales", "s", "Payment Method",
        "Sales", "s", "Net Sales", 0,
        "Revenue by Payment Method", z=300,
        vtype="clusteredBarChart",
    ))

    # Orders by Order Status
    visuals.append(make_chart(
        645, 402, 625, 270,
        "Sales", "s", "Order Status",
        "Sales", "s", "Order ID", 5,
        "Orders by Status", z=400,
        vtype="clusteredBarChart",
    ))

    # Quarterly Revenue by Channel (grouped column with legend)
    visuals.append(make_chart(
        10, 683, 1260, 200,
        "Sales", "s", "Quarter",
        "Sales", "s", "Net Sales", 0,
        "Quarterly Revenue by Sales Channel", z=500,
        vtype="clusteredColumnChart",
        legend_entity="Sales", legend_alias="s", legend_col="Sales Channel",
    ))

    return {
        "name": "ReportSection2",
        "displayName": "Sales Performance",
        "filters": "[]",
        "ordinal": 1,
        "width": 1280,
        "height": 900,
        "visualContainers": visuals,
        "config": js({"relationships": [], "objects": {}}),
    }


# ── PAGE 3: Product Analysis ──────────────────────────────────────────────────
def page_product_analysis() -> dict:
    visuals = []
    visuals.append(make_title_bar("Product Analysis"))
    visuals.extend(page_slicers())
    visuals.extend(exec_kpi_cards())

    # Top Products by Revenue (bar)
    visuals.append(make_chart(
        10, 210, 620, 270,
        "Products", "p", "Product Name",
        "Sales",    "s", "Net Sales", 0,
        "Top Products by Revenue", z=200,
        vtype="clusteredBarChart",
    ))

    # Products by Category (column)
    visuals.append(make_chart(
        645, 210, 625, 270,
        "Products", "p", "Category",
        "Sales",    "s", "Net Sales", 0,
        "Revenue by Product Category", z=300,
        vtype="clusteredColumnChart",
    ))

    # Profit Margin by Category
    visuals.append(make_chart(
        10, 490, 620, 285,
        "Products", "p", "Category",
        "Products", "p", "Profit Margin %", 1,
        "Avg Profit Margin by Category", z=400,
        vtype="clusteredBarChart",
    ))

    # Revenue vs Profit by Category (stacked with legend)
    visuals.append(make_chart(
        645, 490, 625, 285,
        "Products", "p", "Sub Category",
        "Sales",    "s", "Net Sales", 0,
        "Revenue by Sub Category", z=500,
        vtype="clusteredBarChart",
        legend_entity="Products", legend_alias="p", legend_col="Category",
    ))

    return {
        "name": "ReportSection3",
        "displayName": "Product Analysis",
        "filters": "[]",
        "ordinal": 2,
        "width": 1280,
        "height": 800,
        "visualContainers": visuals,
        "config": js({"relationships": [], "objects": {}}),
    }


# ── PAGE 4: Customer Insights ─────────────────────────────────────────────────
def page_customer_insights() -> dict:
    visuals = []
    visuals.append(make_title_bar("Customer Insights"))
    visuals.extend(page_slicers())
    visuals.extend(exec_kpi_cards())

    # Orders by Customer Segment (pie)
    visuals.append(make_chart(
        10, 210, 415, 270,
        "Customers", "c", "Segment",
        "Sales",     "s", "Order ID", 5,
        "Orders by Customer Segment", z=200,
        vtype="pieChart",
    ))

    # Revenue by Customer Country (bar)
    visuals.append(make_chart(
        435, 210, 835, 270,
        "Customers", "c", "Country",
        "Sales",     "s", "Net Sales", 0,
        "Revenue by Country", z=300,
        vtype="clusteredBarChart",
    ))

    # Revenue by Customer Segment and Channel (stacked)
    visuals.append(make_chart(
        10, 490, 620, 285,
        "Customers", "c", "Segment",
        "Sales",     "s", "Net Sales", 0,
        "Revenue by Segment & Channel", z=400,
        vtype="clusteredColumnChart",
        legend_entity="Sales", legend_alias="s", legend_col="Sales Channel",
    ))

    # Top Customers by Revenue (bar)
    visuals.append(make_chart(
        645, 490, 625, 285,
        "Customers", "c", "City",
        "Sales",     "s", "Net Sales", 0,
        "Revenue by Customer City", z=500,
        vtype="clusteredBarChart",
    ))

    return {
        "name": "ReportSection4",
        "displayName": "Customer Insights",
        "filters": "[]",
        "ordinal": 3,
        "width": 1280,
        "height": 800,
        "visualContainers": visuals,
        "config": js({"relationships": [], "objects": {}}),
    }


# ── PAGE 5: Team Performance ──────────────────────────────────────────────────
def page_team_performance() -> dict:
    visuals = []
    visuals.append(make_title_bar("Team Performance"))
    visuals.extend(page_slicers())
    visuals.extend(exec_kpi_cards())

    # Revenue by Sales Rep (column)
    visuals.append(make_chart(
        10, 210, 1260, 275,
        "Users",  "u", "Name",
        "Sales",  "s", "Net Sales", 0,
        "Revenue by Sales Representative", z=200,
        vtype="clusteredColumnChart",
    ))

    # Orders by Sales Rep
    visuals.append(make_chart(
        10, 500, 620, 275,
        "Users", "u", "Name",
        "Sales", "s", "Order ID", 5,
        "Orders by Sales Rep", z=300,
        vtype="clusteredBarChart",
    ))

    # Revenue by Department (bar)
    visuals.append(make_chart(
        645, 500, 625, 275,
        "Users", "u", "Department",
        "Sales", "s", "Net Sales", 0,
        "Revenue by Department", z=400,
        vtype="clusteredBarChart",
    ))

    # Rep performance table
    visuals.append(make_table(
        10, 785, 1260, 200,
        "Users", "u",
        [
            ("User ID",      None),
            ("Name",         None),
            ("Role",         None),
            ("Department",   None),
        ],
        z=500,
        title="Sales Team Directory",
    ))

    return {
        "name": "ReportSection5",
        "displayName": "Team Performance",
        "filters": "[]",
        "ordinal": 4,
        "width": 1280,
        "height": 1000,
        "visualContainers": visuals,
        "config": js({"relationships": [], "objects": {}}),
    }


# ── Full Report/Layout JSON ────────────────────────────────────────────────────

def build_report_layout() -> dict:
    config = {
        "version": "5.49",
        "themeCollection": {
            "baseTheme": {
                "name": "CY23SU11",
                "version": "5.49",
                "type": 2,
            }
        },
        "activeSectionIndex": 0,
        "linguisticSchemaSyncVersion": 2,
        "defaultDrillFilterOtherVisuals": True,
        "filterConfig": {"type": 1},
    }

    return {
        "id": 0,
        "resourcePackages": [{
            "resourcePackage": {
                "disabled": False,
                "items": [{
                    "type": 202,
                    "path": "BaseThemes/CY23SU11.json",
                    "name": "CY23SU11",
                }],
                "name": "SharedResources",
                "type": 2,
            }
        }],
        "sections": [
            page_executive_summary(),
            page_sales_performance(),
            page_product_analysis(),
            page_customer_insights(),
            page_team_performance(),
        ],
        "config": js(config),
        "layoutOptimization": 0,
    }


# ── DiagramLayout ─────────────────────────────────────────────────────────────

def build_diagram_layout() -> dict:
    nodes = [
        {"location": {"x": 0,   "y": 0},   "nodeIndex": "Sales",     "size": {"height": 500, "width": 234}, "zIndex": 0},
        {"location": {"x": 300, "y": 0},   "nodeIndex": "Customers", "size": {"height": 300, "width": 234}, "zIndex": 0},
        {"location": {"x": 600, "y": 0},   "nodeIndex": "Products",  "size": {"height": 350, "width": 234}, "zIndex": 0},
        {"location": {"x": 300, "y": 350}, "nodeIndex": "Users",     "size": {"height": 350, "width": 234}, "zIndex": 0},
    ]
    return {
        "version": "1.1.0",
        "diagrams": [{
            "ordinal": 0,
            "scrollPosition": {"x": 0, "y": 0},
            "nodes": nodes,
            "name": "All tables",
            "zoomValue": 100,
            "pinKeyFieldsToTop": False,
            "showExtraHeaderInfo": False,
            "hideKeyFieldsWhenCollapsed": False,
        }],
        "selectedDiagram": "All tables",
        "defaultDiagram": "All tables",
    }


# ── Static theme JSON ─────────────────────────────────────────────────────────

BASE_THEME_JSON = json.dumps({
    "name": "CY23SU11",
    "dataColors": [TEAL, DGRAY, RED, YELLOW, BLUE, PURPLE, ORANGE, GREEN, SLATE, "#E91E63"],
    "background": WHITE,
    "foreground": DARK,
    "tableAccent": TEAL,
})


# ── PBIX assembler ─────────────────────────────────────────────────────────────

def write_utf16le(text: str) -> bytes:
    return text.encode("utf-16-le")

def write_utf8(text: str) -> bytes:
    return text.encode("utf-8")


def assemble_pbix(schema: dict, report_layout: dict,
                  diagram_layout: dict, source_pbix: str,
                  output_path: str) -> None:
    """Create the PBIX ZIP, reusing the DataModel from source_pbix."""

    content_types = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="png" ContentType=""/>'
        '<Default Extension="xml" ContentType=""/>'
        '<Default Extension="json" ContentType=""/>'
        '<Override PartName="/Version" ContentType=""/>'
        '<Override PartName="/DiagramLayout" ContentType=""/>'
        '<Override PartName="/Report/Layout" ContentType=""/>'
        '<Override PartName="/Settings" ContentType="application/json"/>'
        '<Override PartName="/Metadata" ContentType="application/json"/>'
        '<Override PartName="/DiagramState" ContentType=""/>'
        '<Override PartName="/SecurityBindings" ContentType=""/>'
        '<Override PartName="/DataModel" ContentType=""/>'
        '<Override PartName="/DataModelSchema" ContentType=""/>'
        '<Override PartName="/Connections" ContentType=""/>'
        '<Override PartName="/docProps/custom.xml" ContentType="application/vnd.openxmlformats-officedocument.custom-properties+xml"/>'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="utf-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties" Target="docProps/custom.xml"/>'
        '</Relationships>'
    )

    custom_xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"'
        ' xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="2" name="CreatedApplication">'
        '<vt:lpwstr>Microsoft Power BI Desktop</vt:lpwstr>'
        '</property>'
        '<property fmtid="{D5CDD505-2E9C-101B-9397-08002B2CF9AE}" pid="3" name="Version">'
        '<vt:lpwstr>2.125.0.0</vt:lpwstr>'
        '</property>'
        '</Properties>'
    )

    settings = write_utf16le(js({
        "Version": 1,
        "ReportSettings": {},
        "QueriesSettings": {
            "TypeDetectionEnabled": True,
            "RelationshipImportEnabled": True,
            "Version": "2.44.4675.422",
        },
    }))

    metadata = write_utf16le(js({
        "Version": 5,
        "AutoCreatedRelationships": [],
        "FileDescription": "Sales Analytics Dashboard",
        "CreatedFrom": "Cloud",
        "CreatedFromRelease": "2024.01",
    }))

    connections = write_utf16le(js({"Version": 3, "RemoteArtifacts": []}))

    diagram_state = write_utf16le(js({
        "version": "1.1.0",
        "selectedDiagram": "All tables",
    }))

    # Read DataModel from source (XPress9 compressed ABF – reuse intact)
    with zipfile.ZipFile(source_pbix, "r") as src_zip:
        data_model_bytes = src_zip.read("DataModel")

    # Encode report layout as UTF-16 LE (no BOM)
    layout_str   = json.dumps(report_layout, ensure_ascii=False)
    layout_bytes = write_utf16le(layout_str)

    diagram_bytes = write_utf16le(json.dumps(diagram_layout, ensure_ascii=False))

    # DataModelSchema is UTF-8 JSON
    schema_bytes = write_utf8(json.dumps(schema, indent=2, ensure_ascii=False))

    # Linguistic schema placeholder (UTF-16 LE)
    ling_schema = write_utf16le(js({"Version": 0, "Language": "en-US"}))

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        zout.writestr("Version",              b"1\x00.\x002\x005\x00")  # "1.25" in UTF-16-LE (no newline)
        zout.writestr("[Content_Types].xml",  content_types.encode("utf-8"))
        zout.writestr("_rels/.rels",          rels.encode("utf-8"))
        zout.writestr("docProps/custom.xml",  custom_xml.encode("utf-8"))
        zout.writestr("Settings",             settings)
        zout.writestr("Metadata",             metadata)
        zout.writestr("Connections",          connections)
        zout.writestr("DiagramLayout",        diagram_bytes)
        zout.writestr("DiagramState",         diagram_state)
        zout.writestr("Report/Layout",        layout_bytes)
        zout.writestr("Report/LinguisticSchema", ling_schema)
        zout.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",
                      BASE_THEME_JSON.encode("utf-8"))
        # DataModel (binary XPress9) – store uncompressed to avoid double-compression
        zout.writestr(zipfile.ZipInfo("DataModel"), data_model_bytes)
        zout.writestr("DataModelSchema",      schema_bytes)
        # Empty SecurityBindings placeholder
        zout.writestr("SecurityBindings",     b"")

    print(f"Written: {output_path}  ({os.path.getsize(output_path):,} bytes)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading CSV data...")
    sales_headers, sales_rows = load_csv(os.path.join(DATA_DIR, "Sales.csv"))
    cust_headers,  cust_rows  = load_csv(os.path.join(DATA_DIR, "Customers.csv"))
    prod_headers,  prod_rows  = load_csv(os.path.join(DATA_DIR, "Products.csv"))
    users_headers, users_rows = load_csv(os.path.join(DATA_DIR, "Users.csv"))

    print(f"  Sales:     {len(sales_rows)} rows")
    print(f"  Customers: {len(cust_rows)} rows")
    print(f"  Products:  {len(prod_rows)} rows")
    print(f"  Users:     {len(users_rows)} rows")

    print("Building DataModelSchema...")
    schema = build_schema(
        sales_headers, sales_rows,
        cust_headers,  cust_rows,
        prod_headers,  prod_rows,
        users_headers, users_rows,
    )
    print(f"  Tables: {[t['name'] for t in schema['model']['tables']]}")

    print("Building Report/Layout...")
    report_layout = build_report_layout()
    print(f"  Pages: {[s['displayName'] for s in report_layout['sections']]}")

    print("Building DiagramLayout...")
    diagram_layout = build_diagram_layout()

    print(f"Assembling PBIX (reusing DataModel from {SOURCE_PBIX})...")
    assemble_pbix(schema, report_layout, diagram_layout, SOURCE_PBIX, OUTPUT_PBIX)

    print("\nDone!")
    print(f"Output: {OUTPUT_PBIX}")
    print(f"Size:   {os.path.getsize(OUTPUT_PBIX):,} bytes")

    # Verify it's a valid ZIP
    try:
        with zipfile.ZipFile(OUTPUT_PBIX, "r") as zf:
            names = zf.namelist()
        print(f"Zip valid. Files ({len(names)}): {names}")
    except Exception as e:
        print(f"ZIP validation error: {e}")


if __name__ == "__main__":
    main()

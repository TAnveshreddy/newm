#!/usr/bin/env python3
"""
generate_sales_dashboard.py
Creates SalesAnalytics.pbit and SalesAnalytics.pbix from PowerBI_Data.xlsx

Uses Power Query M (#table) instead of DAX DATATABLE to avoid the
"corrupted file" error that Power BI Desktop reports for calculated tables.
"""

import json, zipfile, uuid, os
from datetime import date, datetime
from openpyxl import load_workbook

# ── Config ──────────────────────────────────────────────────────────────────────
EXCEL_PATH  = "/root/.claude/uploads/88b2c6f2-1275-4033-b7c3-bfdbe632692c/6b04f467-PowerBI_Data.xlsx"
OUTPUT_DIR  = "/home/user/newm"
OUTPUT_PBIT = os.path.join(OUTPUT_DIR, "SalesAnalytics.pbit")
OUTPUT_PBIX = os.path.join(OUTPUT_DIR, "SalesAnalytics.pbix")

W, H = 1280, 720   # report page dimensions

# ── Generic utilities ───────────────────────────────────────────────────────────
def uid():  return uuid.uuid4().hex
def js(obj): return json.dumps(obj, separators=(',', ':'))

# ── M code value formatters ─────────────────────────────────────────────────────
def m_str(v):
    """Format a value as an M string literal, or null."""
    if v is None: return "null"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

def m_num(v):
    """Format a value as an M number (double), or null."""
    if v is None: return "null"
    try:
        f = float(v)
        return str(f)
    except:
        return "null"

def m_int(v):
    """Format a value as an M integer (Int64), or null."""
    if v is None: return "null"
    try:
        return str(int(v))
    except:
        return "null"

def m_date(v):
    """Format a value as an M date ISO string, or null.
    Dates are stored as quoted ISO strings like \"2022-02-23\" with M type 'date'."""
    if v is None: return "null"
    if isinstance(v, datetime): v = v.date()
    if isinstance(v, str):
        try: v = date.fromisoformat(v[:10])
        except: return "null"
    if isinstance(v, date):
        return '"' + v.isoformat() + '"'
    return "null"

# ── Excel reader ───────────────────────────────────────────────────────────────
def read_sheet(wb, name):
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    return [dict(zip(headers, r)) for r in rows[1:]]

# ── M code builders ─────────────────────────────────────────────────────────────
def build_m_table(col_specs, rows_data):
    """Build a Power Query M expression using #table().

    col_specs: list of (col_name, m_type_str) tuples
    rows_data: list of lists of already-formatted M values

    Returns a single string M expression.
    """
    # Build type header: #"Col Name" = type_str
    type_parts = []
    for col_name, m_type in col_specs:
        # M names with special chars need #"..." quoting
        if any(c in col_name for c in ' !"#$%&\'()*+,-./:;<=>?@[\\]^`{|}~') or col_name[0].isdigit():
            type_parts.append(f'#"{col_name}" = {m_type}')
        else:
            type_parts.append(f'{col_name} = {m_type}')
    type_header = "type table [" + ", ".join(type_parts) + "]"

    # Build rows
    row_strs = []
    for row_vals in rows_data:
        row_strs.append("{" + ", ".join(row_vals) + "}")

    rows_block = ",\n    ".join(row_strs)
    expr = f"let\n  Source = #table({type_header}, {{\n    {rows_block}\n  }})\nin\n  Source"
    return expr

def build_m_sales(rows):
    col_specs = [
        ("Order ID",        "text"),
        ("Order Date",      "date"),
        ("Year",            "Int64.Type"),
        ("Month",           "Int64.Type"),
        ("Quarter",         "text"),
        ("Customer ID",     "text"),
        ("Product ID",      "text"),
        ("User ID",         "text"),
        ("Category",        "text"),
        ("Quantity",        "Int64.Type"),
        ("Unit Price",      "number"),
        ("Unit Cost",       "number"),
        ("Gross Sales",     "number"),
        ("Discount %",      "number"),
        ("Discount Amount", "number"),
        ("Net Sales",       "number"),
        ("Total Cost",      "number"),
        ("Profit",          "number"),
        ("Profit Margin %", "number"),
        ("Sales Channel",   "text"),
        ("Order Status",    "text"),
        ("Ship Date",       "date"),
        ("Payment Method",  "text"),
    ]
    rows_data = []
    for r in rows:
        rows_data.append([
            m_str(r.get("Order ID")),
            m_date(r.get("Order Date")),
            m_int(r.get("Year")),
            m_int(r.get("Month")),
            m_str(r.get("Quarter")),
            m_str(r.get("Customer ID")),
            m_str(r.get("Product ID")),
            m_str(r.get("User ID")),
            m_str(r.get("Category")),
            m_int(r.get("Quantity")),
            m_num(r.get("Unit Price")),
            m_num(r.get("Unit Cost")),
            m_num(r.get("Gross Sales")),
            m_num(r.get("Discount %")),
            m_num(r.get("Discount Amount")),
            m_num(r.get("Net Sales")),
            m_num(r.get("Total Cost")),
            m_num(r.get("Profit")),
            m_num(r.get("Profit Margin %")),
            m_str(r.get("Sales Channel")),
            m_str(r.get("Order Status")),
            m_date(r.get("Ship Date")),
            m_str(r.get("Payment Method")),
        ])
    return build_m_table(col_specs, rows_data)

def build_m_customers(rows):
    col_specs = [
        ("Customer ID",       "text"),
        ("First Name",        "text"),
        ("Last Name",         "text"),
        ("Email",             "text"),
        ("Phone",             "text"),
        ("Address",           "text"),
        ("City",              "text"),
        ("Country",           "text"),
        ("Postal Code",       "text"),
        ("Segment",           "text"),
        ("Registration Date", "date"),
        ("Credit Limit",      "number"),
    ]
    rows_data = []
    for r in rows:
        rows_data.append([
            m_str(r.get("Customer ID")),
            m_str(r.get("First Name")),
            m_str(r.get("Last Name")),
            m_str(r.get("Email")),
            m_str(r.get("Phone")),
            m_str(r.get("Address")),
            m_str(r.get("City")),
            m_str(r.get("Country")),
            m_str(r.get("Postal Code")),
            m_str(r.get("Segment")),
            m_date(r.get("Registration Date")),
            m_num(r.get("Credit Limit")),
        ])
    return build_m_table(col_specs, rows_data)

def build_m_products(rows):
    col_specs = [
        ("Product ID",      "text"),
        ("Product Name",    "text"),
        ("Category",        "text"),
        ("Sub Category",    "text"),
        ("Brand",           "text"),
        ("Unit Cost",       "number"),
        ("Unit Price",      "number"),
        ("Profit Margin %", "number"),
        ("Stock Quantity",  "Int64.Type"),
        ("Reorder Level",   "Int64.Type"),
        ("Supplier",        "text"),
        ("Weight (kg)",     "number"),
        ("Rating",          "number"),
    ]
    rows_data = []
    for r in rows:
        rows_data.append([
            m_str(r.get("Product ID")),
            m_str(r.get("Product Name")),
            m_str(r.get("Category")),
            m_str(r.get("Sub Category")),
            m_str(r.get("Brand")),
            m_num(r.get("Unit Cost")),
            m_num(r.get("Unit Price")),
            m_num(r.get("Profit Margin %")),
            m_int(r.get("Stock Quantity")),
            m_int(r.get("Reorder Level")),
            m_str(r.get("Supplier")),
            m_num(r.get("Weight (kg)")),
            m_num(r.get("Rating")),
        ])
    return build_m_table(col_specs, rows_data)

def build_m_users(rows):
    col_specs = [
        ("User ID",       "text"),
        ("Name",          "text"),
        ("First Name",    "text"),
        ("Last Name",     "text"),
        ("Email",         "text"),
        ("Role",          "text"),
        ("Department",    "text"),
        ("Country",       "text"),
        ("Location",      "text"),
        ("Phone",         "text"),
        ("Join Date",     "date"),
        ("Manager ID",    "text"),
        ("Sales Target",  "number"),
    ]
    rows_data = []
    for r in rows:
        rows_data.append([
            m_str(r.get("User ID")),
            m_str(r.get("Name")),
            m_str(r.get("First Name")),
            m_str(r.get("Last Name")),
            m_str(r.get("Email")),
            m_str(r.get("Role")),
            m_str(r.get("Department")),
            m_str(r.get("Country")),
            m_str(r.get("Location")),
            m_str(r.get("Phone")),
            m_date(r.get("Join Date")),
            m_str(r.get("Manager ID")),
            m_num(r.get("Sales Target")),
        ])
    return build_m_table(col_specs, rows_data)

# ── Column / measure schema builders ────────────────────────────────────────────
def col_def(name, dtype, summarize="none", fmt=None, hidden=False):
    d = {
        "name": name,
        "dataType": dtype,
        "lineageTag": uid(),
        "summarizeBy": summarize,
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}],
    }
    if fmt:    d["formatString"] = fmt
    if hidden: d["isHidden"] = True
    return d

def measure_def(name, expr, fmt=None, display_folder=""):
    d = {
        "name": name,
        "lineageTag": uid(),
        "expression": expr,
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}],
    }
    if fmt:            d["formatString"] = fmt
    if display_folder: d["displayFolder"] = display_folder
    return d

def partition_m(table_name, m_expression):
    """Build a partition with type 'm' and a single-string M expression."""
    return [{"name": table_name, "mode": "import",
             "source": {"type": "m", "expression": m_expression}}]

# ── DataModelSchema ──────────────────────────────────────────────────────────────
def build_schema(sales_rows, customers_rows, products_rows, users_rows):

    # ── SALES TABLE ──
    sales_cols = [
        col_def("Order ID",          "string"),
        col_def("Order Date",        "dateTime",  fmt="Short Date"),
        col_def("Year",              "int64",     summarize="sum", hidden=True),
        col_def("Month",             "int64",     summarize="sum", hidden=True),
        col_def("Quarter",           "string"),
        col_def("Customer ID",       "string"),
        col_def("Product ID",        "string"),
        col_def("User ID",           "string"),
        col_def("Category",          "string"),
        col_def("Quantity",          "int64",     summarize="sum"),
        col_def("Unit Price",        "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Unit Cost",         "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Gross Sales",       "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Discount %",        "double",    summarize="none", fmt='0.00%'),
        col_def("Discount Amount",   "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Net Sales",         "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Total Cost",        "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Profit",            "double",    summarize="sum",  fmt=r'$#,0.00'),
        col_def("Profit Margin %",   "double",    summarize="none", fmt='0.00%'),
        col_def("Sales Channel",     "string"),
        col_def("Order Status",      "string"),
        col_def("Ship Date",         "dateTime",  fmt="Short Date"),
        col_def("Payment Method",    "string"),
    ]
    sales_measures = [
        measure_def("Total Revenue",        'SUM(Sales[Net Sales])',                   fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Total Profit",         'SUM(Sales[Profit])',                      fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Total Cost",           'SUM(Sales[Total Cost])',                  fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Gross Sales",          'SUM(Sales[Gross Sales])',                 fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Total Discount",       'SUM(Sales[Discount Amount])',             fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Total Quantity",       'SUM(Sales[Quantity])',                    fmt='#,0',          display_folder="KPIs"),
        measure_def("Total Orders",         'COUNTROWS(Sales)',                        fmt='#,0',          display_folder="KPIs"),
        measure_def("Avg Order Value",      'DIVIDE([Total Revenue],[Total Orders])',   fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Profit Margin %",      'DIVIDE([Total Profit],[Total Revenue])',  fmt='0.0%',         display_folder="KPIs"),
        measure_def("Avg Profit Margin",    'AVERAGEX(VALUES(Sales[Category]),[Profit Margin %])', fmt='0.0%', display_folder="KPIs"),
        measure_def("Completed Orders",     'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Completed")', fmt='#,0', display_folder="Status"),
        measure_def("Pending Orders",       'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Pending")',   fmt='#,0', display_folder="Status"),
        measure_def("Returned Orders",      'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Returned")',  fmt='#,0', display_folder="Status"),
        measure_def("Return Rate",          'DIVIDE([Returned Orders],[Total Orders])', fmt='0.0%',        display_folder="Status"),
        measure_def("Sales Target Total",   'SUM(Users[Sales Target])',                fmt=r'$#,0',        display_folder="KPIs"),
        measure_def("Target Achievement %", 'DIVIDE([Total Revenue],[Sales Target Total])', fmt='0.0%',    display_folder="KPIs"),
        measure_def("YoY Revenue Growth",
            'VAR CY=MAXX(ALL(Sales[Year]),Sales[Year])\n'
            'VAR CY_Rev=CALCULATE([Total Revenue],Sales[Year]=CY)\n'
            'VAR PY_Rev=CALCULATE([Total Revenue],Sales[Year]=CY-1)\n'
            'RETURN DIVIDE(CY_Rev-PY_Rev,PY_Rev)',
            fmt='+0.0%;-0.0%;0.0%', display_folder="KPIs"),
        measure_def("Revenue Prior Year",
            'VAR CY=MAXX(ALL(Sales[Year]),Sales[Year])\n'
            'RETURN CALCULATE([Total Revenue],Sales[Year]=CY-1)',
            fmt=r'$#,0', display_folder="KPIs"),
    ]
    sales_table = {
        "name": "Sales",
        "lineageTag": uid(),
        "columns": sales_cols,
        "measures": sales_measures,
        "partitions": partition_m("Sales", build_m_sales(sales_rows)),
        "annotations": [{"name": "$AutoCreatedDate", "value": datetime.now().isoformat()}],
    }

    # ── CUSTOMERS TABLE ──
    customers_table = {
        "name": "Customers",
        "lineageTag": uid(),
        "columns": [
            col_def("Customer ID",       "string"),
            col_def("First Name",        "string"),
            col_def("Last Name",         "string"),
            col_def("Email",             "string"),
            col_def("Phone",             "string"),
            col_def("Address",           "string"),
            col_def("City",              "string"),
            col_def("Country",           "string"),
            col_def("Postal Code",       "string"),
            col_def("Segment",           "string"),
            col_def("Registration Date", "dateTime", fmt="Short Date"),
            col_def("Credit Limit",      "double",   summarize="sum", fmt=r'$#,0'),
        ],
        "measures": [
            measure_def("Total Customers",  "COUNTROWS(Customers)", fmt='#,0'),
            measure_def("Avg Credit Limit", "AVERAGE(Customers[Credit Limit])", fmt=r'$#,0'),
        ],
        "partitions": partition_m("Customers", build_m_customers(customers_rows)),
        "annotations": [],
    }

    # ── PRODUCTS TABLE ──
    products_table = {
        "name": "Products",
        "lineageTag": uid(),
        "columns": [
            col_def("Product ID",      "string"),
            col_def("Product Name",    "string"),
            col_def("Category",        "string"),
            col_def("Sub Category",    "string"),
            col_def("Brand",           "string"),
            col_def("Unit Cost",       "double",  summarize="sum",     fmt=r'$#,0.00'),
            col_def("Unit Price",      "double",  summarize="sum",     fmt=r'$#,0.00'),
            col_def("Profit Margin %", "double",  summarize="none",    fmt='0.0%'),
            col_def("Stock Quantity",  "int64",   summarize="sum"),
            col_def("Reorder Level",   "int64",   summarize="sum"),
            col_def("Supplier",        "string"),
            col_def("Weight (kg)",     "double",  summarize="sum"),
            col_def("Rating",          "double",  summarize="average"),
        ],
        "measures": [
            measure_def("Total Products", "COUNTROWS(Products)", fmt='#,0'),
            measure_def("Avg Rating",     "AVERAGE(Products[Rating])", fmt='0.00'),
            measure_def("Total Stock",    "SUM(Products[Stock Quantity])", fmt='#,0'),
        ],
        "partitions": partition_m("Products", build_m_products(products_rows)),
        "annotations": [],
    }

    # ── USERS TABLE ──
    users_table = {
        "name": "Users",
        "lineageTag": uid(),
        "columns": [
            col_def("User ID",      "string"),
            col_def("Name",         "string"),
            col_def("First Name",   "string"),
            col_def("Last Name",    "string"),
            col_def("Email",        "string"),
            col_def("Role",         "string"),
            col_def("Department",   "string"),
            col_def("Country",      "string"),
            col_def("Location",     "string"),
            col_def("Phone",        "string"),
            col_def("Join Date",    "dateTime", fmt="Short Date"),
            col_def("Manager ID",   "string"),
            col_def("Sales Target", "double",   summarize="sum", fmt=r'$#,0'),
        ],
        "measures": [
            measure_def("Total Sales Reps", "COUNTROWS(Users)", fmt='#,0'),
        ],
        "partitions": partition_m("Users", build_m_users(users_rows)),
        "annotations": [],
    }

    relationships = [
        {
            "name": uid(),
            "fromTable": "Sales", "fromColumn": "Customer ID",
            "toTable":   "Customers", "toColumn": "Customer ID",
            "crossFilteringBehavior": "oneDirection",
        },
        {
            "name": uid(),
            "fromTable": "Sales", "fromColumn": "Product ID",
            "toTable":   "Products", "toColumn": "Product ID",
            "crossFilteringBehavior": "oneDirection",
        },
        {
            "name": uid(),
            "fromTable": "Sales", "fromColumn": "User ID",
            "toTable":   "Users", "toColumn": "User ID",
            "crossFilteringBehavior": "oneDirection",
        },
    ]

    roles = [
        {
            "name": "Sales Rep",
            "modelPermission": "read",
            "tablePermissions": [
                {
                    "name": "Users",
                    "filterExpression": "[Email] = USERPRINCIPALNAME()"
                }
            ]
        }
    ]

    schema = {
        "model": {
            "compatibilityLevel": 1567,
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "tables": [sales_table, customers_table, products_table, users_table],
            "relationships": relationships,
            "roles": roles,
            "annotations": [
                {"name": "PBIDesktopVersion", "value": "2.124.2028.0 (24.04)"},
                {"name": "PBI_QueryOrder",    "value": '["Sales","Customers","Products","Users"]'},
            ],
            "cultures": [{"name": "en-US", "linguisticMetadata": {"Version": "1.0.0", "Language": "en-US"}}],
        }
    }
    return schema

# ── Diagram layout ───────────────────────────────────────────────────────────────
def build_diagram_layout(schema):
    tables = schema["model"]["tables"]
    positions = {
        "Sales":     (10,  10),
        "Customers": (280, 200),
        "Products":  (550, 10),
        "Users":     (280, 10),
    }
    nodes = []
    for i, t in enumerate(tables):
        x, y = positions.get(t["name"], (i * 280, 10))
        nodes.append({
            "location": {"x": x, "y": y},
            "nodeIndex": t["name"],
            "nodeLineageTag": t["lineageTag"],
            "size": {"height": max(120, 30 + 20 * len(t["columns"])), "width": 234},
            "zIndex": i,
        })
    return {
        "version": "1.1.0",
        "diagrams": [{"ordinal": 0, "scrollPosition": {"x": 0, "y": 0}, "nodes": nodes}],
    }

# ── Report Layout Helpers ────────────────────────────────────────────────────────
def frm(alias, entity):
    return {"Name": alias, "Entity": entity, "Type": 0}

def col_s(alias, prop, entity):
    return {
        "Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
        "Name": f"{entity}.{prop}",
        "NativeReferenceName": prop,
    }

def msr_s(alias, prop, entity):
    return {
        "Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
        "Name": f"{entity}.{prop}",
        "NativeReferenceName": prop,
    }

def make_query_str(frm_list, selects):
    pq = {"Version": 2, "From": frm_list, "Select": selects}
    cmd = {"Commands": [{"SemanticQueryDataShapeCommand": {
        "Query": pq,
        "Binding": {
            "Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]},
            "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
            "Version": 1,
        },
        "ExecutionMetricsKind": 1,
    }}]}
    return js(cmd)

def vc_config(vtype, frm_list, selects, title=None):
    pq = {"Version": 2, "From": frm_list, "Select": selects}
    vc_objs = {}
    if title:
        vc_objs["title"] = [{"properties": {
            "show":     {"expr": {"Literal": {"Value": "true"}}},
            "text":     {"expr": {"Literal": {"Value": f"'{title}'"}}},
            "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
        }}]
    sv = {"visualType": vtype, "projectionMapping": {}, "prototypeQuery": pq, "columnProperties": {}}
    if vc_objs:
        sv["vcObjects"] = vc_objs
    return js({
        "name":    uid()[:20],
        "layouts": [{"id": 0, "position": {"x": 0, "y": 0, "z": 0,
                                            "height": 100, "width": 100, "tabOrder": 0}}],
        "singleVisual": sv,
    })

def make_vc(x, y, w, h, vtype, frm_list, selects, title=None):
    cfg   = vc_config(vtype, frm_list, selects, title)
    query = make_query_str(frm_list, selects)
    return {
        "x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": 0,
        "filters": "[]", "config": cfg, "query": query, "dataTransforms": "{}",
    }

def make_page(display_name, visuals):
    return {
        "name": uid()[:20],
        "displayName": display_name,
        "width": W, "height": H,
        "visualContainers": visuals,
        "config": js({"relationships": []}),
        "filters": "[]",
    }

# ── KPI Card row ─────────────────────────────────────────────────────────────────
def kpi_row(y=12, h=92):
    """6 KPI cards shown on all pages."""
    card_w, gap, start_x = 196, 10, 13
    cards = [
        ("Total Revenue",        "s", "Sales"),
        ("Total Profit",         "s", "Sales"),
        ("Total Orders",         "s", "Sales"),
        ("Avg Order Value",      "s", "Sales"),
        ("Return Rate",          "s", "Sales"),
        ("Target Achievement %", "s", "Sales"),
    ]
    result = []
    for i, (mname, alias, entity) in enumerate(cards):
        x = start_x + i * (card_w + gap)
        result.append(make_vc(x, y, card_w, h, "card",
                               [frm(alias, entity)],
                               [msr_s(alias, mname, entity)]))
    return result

# ── PAGE 1: Executive Summary ────────────────────────────────────────────────────
def page_executive_summary():
    visuals = kpi_row(y=12, h=92)

    # Revenue Trend — line chart
    visuals.append(make_vc(13, 114, 1247, 210, "lineChart",
        [frm("s", "Sales")], [
            col_s("s", "Month",        "Sales"),
            col_s("s", "Year",         "Sales"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Revenue Trend — Net Sales by Month & Year"))

    # Row 3: 3 charts
    chart_w, chart_h, chart_y = 406, 360, 334

    visuals.append(make_vc(13, chart_y, chart_w, chart_h, "clusteredBarChart",
        [frm("s", "Sales")], [
            col_s("s", "Category",    "Sales"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Sales by Category"))

    visuals.append(make_vc(429, chart_y, chart_w, chart_h, "donutChart",
        [frm("s", "Sales")], [
            col_s("s", "Sales Channel","Sales"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Sales Channel Mix"))

    visuals.append(make_vc(845, chart_y, chart_w, chart_h, "donutChart",
        [frm("s", "Sales")], [
            col_s("s", "Order Status","Sales"),
            msr_s("s", "Total Orders","Sales"),
        ], title="Order Status Distribution"))

    return make_page("Executive Summary", visuals)

# ── PAGE 2: Sales Performance ────────────────────────────────────────────────────
def page_sales_performance():
    visuals = kpi_row(y=12, h=92)

    # Orders Matrix — pivot table
    visuals.append(make_vc(13, 114, 1247, 175, "pivotTable",
        [frm("s", "Sales")], [
            col_s("s", "Year",         "Sales"),
            col_s("s", "Month",        "Sales"),
            msr_s("s", "Total Orders", "Sales"),
        ], title="Monthly Orders Heatmap — Count by Year & Month"))

    # Sales by Country
    visuals.append(make_vc(13, 299, 614, 210, "clusteredBarChart",
        [frm("s", "Sales"), frm("c", "Customers")], [
            col_s("c", "Country",       "Customers"),
            msr_s("s", "Total Revenue", "Sales"),
        ], title="Net Sales by Customer Country"))

    # Payment Method bar
    visuals.append(make_vc(641, 299, 619, 210, "clusteredColumnChart",
        [frm("s", "Sales")], [
            col_s("s", "Payment Method","Sales"),
            msr_s("s", "Total Orders",  "Sales"),
        ], title="Orders by Payment Method"))

    # Quarterly Revenue by Year
    visuals.append(make_vc(13, 519, 1247, 188, "clusteredColumnChart",
        [frm("s", "Sales")], [
            col_s("s", "Quarter",       "Sales"),
            col_s("s", "Year",          "Sales"),
            msr_s("s", "Total Revenue", "Sales"),
        ], title="Quarterly Revenue by Year"))

    return make_page("Sales Performance", visuals)

# ── PAGE 3: Product Analysis ─────────────────────────────────────────────────────
def page_product_analysis():
    visuals = kpi_row(y=12, h=92)

    # Top Products by Revenue
    visuals.append(make_vc(13, 114, 619, 290, "clusteredBarChart",
        [frm("s", "Sales"), frm("p", "Products")], [
            col_s("p", "Product Name",  "Products"),
            msr_s("s", "Total Revenue", "Sales"),
        ], title="Top Products by Net Sales"))

    # Profit Margin % by Category
    visuals.append(make_vc(646, 114, 619, 290, "clusteredColumnChart",
        [frm("s", "Sales")], [
            col_s("s", "Category",        "Sales"),
            msr_s("s", "Profit Margin %", "Sales"),
        ], title="Profit Margin % by Category"))

    # Category Revenue vs Profit
    visuals.append(make_vc(13, 414, 1247, 290, "clusteredColumnChart",
        [frm("s", "Sales")], [
            col_s("s", "Category",      "Sales"),
            msr_s("s", "Total Revenue", "Sales"),
            msr_s("s", "Total Profit",  "Sales"),
        ], title="Category Revenue vs Profit"))

    return make_page("Product Analysis", visuals)

# ── PAGE 4: Customer Insights ────────────────────────────────────────────────────
def page_customer_insights():
    visuals = kpi_row(y=12, h=92)

    # Customer Segment Revenue (pie)
    visuals.append(make_vc(13, 114, 395, 285, "pieChart",
        [frm("c", "Customers"), frm("s", "Sales")], [
            col_s("c", "Segment",       "Customers"),
            msr_s("s", "Total Revenue", "Sales"),
        ], title="Revenue by Customer Segment"))

    # Sales by Customer Country (bar)
    visuals.append(make_vc(422, 114, 843, 285, "clusteredBarChart",
        [frm("c", "Customers"), frm("s", "Sales")], [
            col_s("c", "Country",       "Customers"),
            msr_s("s", "Total Revenue", "Sales"),
        ], title="Sales by Customer Country"))

    # Segment × Order Status (stacked bar)
    visuals.append(make_vc(13, 409, 614, 295, "stackedBarChart",
        [frm("c", "Customers"), frm("s", "Sales")], [
            col_s("c", "Segment",       "Customers"),
            col_s("s", "Order Status",  "Sales"),
            msr_s("s", "Total Orders",  "Sales"),
        ], title="Order Status by Customer Segment"))

    # Avg Credit Limit by Segment
    visuals.append(make_vc(641, 409, 619, 295, "clusteredColumnChart",
        [frm("c", "Customers")], [
            col_s("c", "Segment",          "Customers"),
            msr_s("c", "Avg Credit Limit", "Customers"),
        ], title="Avg Credit Limit by Segment"))

    return make_page("Customer Insights", visuals)

# ── PAGE 5: Team Performance ──────────────────────────────────────────────────────
def page_team_performance():
    visuals = kpi_row(y=12, h=92)

    # Team Sales vs Target
    visuals.append(make_vc(13, 114, 1247, 250, "clusteredColumnChart",
        [frm("u", "Users"), frm("s", "Sales")], [
            col_s("u", "Name",               "Users"),
            msr_s("s", "Total Revenue",      "Sales"),
            msr_s("s", "Sales Target Total", "Sales"),
        ], title="Team Sales vs Target"))

    # Sales by Location
    visuals.append(make_vc(13, 374, 604, 330, "clusteredBarChart",
        [frm("u", "Users"), frm("s", "Sales")], [
            col_s("u", "Location",       "Users"),
            msr_s("s", "Total Revenue",  "Sales"),
        ], title="Net Sales by Location"))

    # Team table
    visuals.append(make_vc(631, 374, 634, 330, "tableEx",
        [frm("u", "Users"), frm("s", "Sales")], [
            col_s("u", "Name",                     "Users"),
            col_s("u", "Role",                     "Users"),
            col_s("u", "Location",                 "Users"),
            msr_s("s", "Total Revenue",            "Sales"),
            col_s("u", "Sales Target",             "Users"),
            msr_s("s", "Target Achievement %",     "Sales"),
        ], title="Sales Team Performance Table"))

    return make_page("Team Performance", visuals)

# ── Report config / theme ref ────────────────────────────────────────────────────
REPORT_CONFIG = js({
    "version": "5.40",
    "themeCollection": {"baseTheme": {"name": "CY23SU11", "version": "5.40", "type": 2}},
    "defaultDrillFilterOtherVisuals": True,
    "linguisticSchemaSyncVersion": 2,
    "settings": {"useStylableVisualContainerHeader": True},
})

THEME_JSON = """{
  "name": "CY23SU11",
  "dataColors": ["#118DFF","#12239E","#E66C37","#6B007B","#E044A7","#744EC2","#D9B300","#D64550"],
  "good": "#01B8AA", "neutral": "#F2C80F", "bad": "#FD625E",
  "background": "#FFFFFF", "foreground": "#252423",
  "tableAccent": "#118DFF"
}"""

# ── Static files ──────────────────────────────────────────────────────────────────
# Copied exactly from reference make1_with_relationships.pbit
# NOTE: No SecurityBindings override entry (reference file does not have it)
CONTENT_TYPES_XML = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml"  ContentType="application/xml"  />
  <Override PartName="/DataModelSchema"    ContentType="application/json" />
  <Override PartName="/DiagramLayout"      ContentType="application/json" />
  <Override PartName="/Report/Layout"      ContentType="application/json" />
  <Override PartName="/Settings"           ContentType="application/json" />
  <Override PartName="/Metadata"           ContentType="application/json" />
  <Override PartName="/[Content_Types].xml" ContentType="application/xml" />
</Types>"""

VERSION  = "3.0"

# Metadata — UTF-16LE, structure matched from reference
METADATA_OBJ = {
    "Version": 5,
    "AutoCreatedRelationships": [],
    "CreatedFrom": "Cloud",
    "CreatedFromRelease": "2024.04",
}

# Settings — UTF-16LE, structure matched from reference
SETTINGS_OBJ = {
    "Version": 4,
    "ReportSettings": {},
    "QueriesSettings": {
        "TypeDetectionEnabled": True,
        "RelationshipImportEnabled": True,
        "Version": "2.124.2028.0",
    },
}

# ── Package builder ───────────────────────────────────────────────────────────────
def build_layout_obj(pages):
    return {
        "id": 0,
        "resourcePackages": [
            {
                "resourcePackage": {
                    "name": "SharedResources",
                    "type": 2,
                    "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json", "name": "CY23SU11"}],
                    "disabled": False,
                }
            }
        ],
        "sections": pages,
        "config": REPORT_CONFIG,
        "layoutOptimization": 0,
    }

def write_archive(path, schema, diagram, pages):
    layout = build_layout_obj(pages)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        # UTF-8 plain text
        z.writestr("Version",              VERSION.encode("utf-8"))
        # UTF-8 XML
        z.writestr("[Content_Types].xml",  CONTENT_TYPES_XML.encode("utf-8"))
        # UTF-8 JSON
        z.writestr("DataModelSchema",      json.dumps(schema, ensure_ascii=False).encode("utf-8"))
        # UTF-16LE JSON (BOM-less, as verified from reference)
        z.writestr("DiagramLayout",        json.dumps(diagram, ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Report/Layout",        json.dumps(layout,  ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Settings",             json.dumps(SETTINGS_OBJ, ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Metadata",             json.dumps(METADATA_OBJ, ensure_ascii=False).encode("utf-16-le"))
        # Empty bytes (no content-type override needed)
        z.writestr("SecurityBindings",     b"")
        # UTF-8 theme
        z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",
                   THEME_JSON.encode("utf-8"))
    print(f"[OK] Written: {path}")

# ── Main ──────────────────────────────────────────────────────────────────────────
def main():
    print("Reading Excel …")
    wb = load_workbook(EXCEL_PATH, data_only=True)
    sales_rows     = read_sheet(wb, "Sales")
    customers_rows = read_sheet(wb, "Customers")
    products_rows  = read_sheet(wb, "Products")
    users_rows     = read_sheet(wb, "Users")
    print(f"  Sales: {len(sales_rows)} rows | Customers: {len(customers_rows)} | "
          f"Products: {len(products_rows)} | Users: {len(users_rows)}")

    print("Building DataModelSchema (Power Query M) …")
    schema  = build_schema(sales_rows, customers_rows, products_rows, users_rows)
    diagram = build_diagram_layout(schema)

    print("Building report pages …")
    pages = [
        page_executive_summary(),
        page_sales_performance(),
        page_product_analysis(),
        page_customer_insights(),
        page_team_performance(),
    ]
    print(f"  {len(pages)} pages")
    for p in pages:
        print(f"  * {p['displayName']} ({len(p['visualContainers'])} visuals)")

    total_visuals = sum(len(p["visualContainers"]) for p in pages)
    print(f"  Total visuals: {total_visuals}")

    print("Writing SalesAnalytics.pbit …")
    write_archive(OUTPUT_PBIT, schema, diagram, pages)

    print("Writing SalesAnalytics.pbix …")
    write_archive(OUTPUT_PBIX, schema, diagram, pages)

    print("\nDone!")
    print("-> SalesAnalytics.pbit  — Open in Power BI Desktop, click 'Apply Changes', save as .pbix")
    print("-> SalesAnalytics.pbix  — Open in Power BI Desktop (data loaded from M query)")

if __name__ == "__main__":
    main()

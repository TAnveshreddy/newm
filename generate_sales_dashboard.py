#!/usr/bin/env python3
"""
generate_sales_dashboard.py
Creates SalesAnalytics.pbit and SalesAnalytics.pbix from PowerBI_Data.xlsx

The .pbit embeds all data via DATATABLE DAX expressions (no external source
needed — open in Power BI Desktop, click Apply Changes, save as .pbix).
The .pbix reuses the existing binary DataModel but ships a complete
5-page report layout referencing the new schema.
"""

import json, zipfile, uuid, os, shutil
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

EXCEL_EPOCH = date(1899, 12, 30)

def to_excel_serial(d):
    if d is None:                          return 0
    if isinstance(d, datetime):            d = d.date()
    if isinstance(d, str):
        try:  d = date.fromisoformat(d[:10])
        except: return 0
    if isinstance(d, date):
        return (d - EXCEL_EPOCH).days
    return 0

def dax_str(v):
    if v is None: return '""'
    return '"' + str(v).replace('"', '""') + '"'

def dax_num(v):
    if v is None: return "0"
    try:    return str(float(v))
    except: return "0"

def dax_int(v):
    if v is None: return "0"
    try:    return str(int(v))
    except: return "0"

def dax_date(v):
    return str(to_excel_serial(v))

# ── Excel reader ───────────────────────────────────────────────────────────────
def read_sheet(wb, name):
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    return [dict(zip(headers, r)) for r in rows[1:]]

# ── DATATABLE builders ──────────────────────────────────────────────────────────
def _dt(header, data_rows):
    """Build a DATATABLE DAX expression (rows comma-separated, one row per line)."""
    body = ",\n".join(data_rows)
    return [f"DATATABLE({header},{{\n{body}\n}})"]

def build_datatable_sales(rows):
    header = (
        '"Order ID",STRING,"Order Date",DATETIME,"Year",INTEGER,"Month",INTEGER,'
        '"Quarter",STRING,"Customer ID",STRING,"Product ID",STRING,"User ID",STRING,'
        '"Category",STRING,"Quantity",INTEGER,"Unit Price",DOUBLE,"Unit Cost",DOUBLE,'
        '"Gross Sales",DOUBLE,"Discount Pct",DOUBLE,"Discount Amount",DOUBLE,'
        '"Net Sales",DOUBLE,"Total Cost",DOUBLE,"Profit",DOUBLE,'
        '"Profit Margin Pct",DOUBLE,"Sales Channel",STRING,"Order Status",STRING,'
        '"Ship Date",DATETIME,"Payment Method",STRING'
    )
    data_rows = []
    for r in rows:
        data_rows.append(
            "{" +
            f'{dax_str(r.get("Order ID"))},'
            f'{dax_date(r.get("Order Date"))},'
            f'{dax_int(r.get("Year"))},'
            f'{dax_int(r.get("Month"))},'
            f'{dax_str(r.get("Quarter"))},'
            f'{dax_str(r.get("Customer ID"))},'
            f'{dax_str(r.get("Product ID"))},'
            f'{dax_str(r.get("User ID"))},'
            f'{dax_str(r.get("Category"))},'
            f'{dax_int(r.get("Quantity"))},'
            f'{dax_num(r.get("Unit Price"))},'
            f'{dax_num(r.get("Unit Cost"))},'
            f'{dax_num(r.get("Gross Sales"))},'
            f'{dax_num(r.get("Discount %"))},'
            f'{dax_num(r.get("Discount Amount"))},'
            f'{dax_num(r.get("Net Sales"))},'
            f'{dax_num(r.get("Total Cost"))},'
            f'{dax_num(r.get("Profit"))},'
            f'{dax_num(r.get("Profit Margin %"))},'
            f'{dax_str(r.get("Sales Channel"))},'
            f'{dax_str(r.get("Order Status"))},'
            f'{dax_date(r.get("Ship Date"))},'
            f'{dax_str(r.get("Payment Method"))}'
            + "}"
        )
    return _dt(header, data_rows)

def build_datatable_customers(rows):
    header = (
        '"Customer ID",STRING,"First Name",STRING,"Last Name",STRING,'
        '"Email",STRING,"Phone",STRING,"Address",STRING,"City",STRING,'
        '"Country",STRING,"Postal Code",STRING,"Segment",STRING,'
        '"Registration Date",DATETIME,"Credit Limit",DOUBLE'
    )
    data_rows = []
    for r in rows:
        data_rows.append(
            "{" +
            f'{dax_str(r.get("Customer ID"))},'
            f'{dax_str(r.get("First Name"))},'
            f'{dax_str(r.get("Last Name"))},'
            f'{dax_str(r.get("Email"))},'
            f'{dax_str(r.get("Phone"))},'
            f'{dax_str(r.get("Address"))},'
            f'{dax_str(r.get("City"))},'
            f'{dax_str(r.get("Country"))},'
            f'{dax_str(r.get("Postal Code"))},'
            f'{dax_str(r.get("Segment"))},'
            f'{dax_date(r.get("Registration Date"))},'
            f'{dax_num(r.get("Credit Limit"))}'
            + "}"
        )
    return _dt(header, data_rows)

def build_datatable_products(rows):
    header = (
        '"Product ID",STRING,"Product Name",STRING,"Category",STRING,'
        '"Sub Category",STRING,"Brand",STRING,"Unit Cost",DOUBLE,'
        '"Unit Price",DOUBLE,"Profit Margin Pct",DOUBLE,"Stock Quantity",INTEGER,'
        '"Reorder Level",INTEGER,"Supplier",STRING,"Weight kg",DOUBLE,"Rating",DOUBLE'
    )
    data_rows = []
    for r in rows:
        data_rows.append(
            "{" +
            f'{dax_str(r.get("Product ID"))},'
            f'{dax_str(r.get("Product Name"))},'
            f'{dax_str(r.get("Category"))},'
            f'{dax_str(r.get("Sub Category"))},'
            f'{dax_str(r.get("Brand"))},'
            f'{dax_num(r.get("Unit Cost"))},'
            f'{dax_num(r.get("Unit Price"))},'
            f'{dax_num(r.get("Profit Margin %"))},'
            f'{dax_int(r.get("Stock Quantity"))},'
            f'{dax_int(r.get("Reorder Level"))},'
            f'{dax_str(r.get("Supplier"))},'
            f'{dax_num(r.get("Weight (kg)"))},'
            f'{dax_num(r.get("Rating"))}'
            + "}"
        )
    return _dt(header, data_rows)

def build_datatable_users(rows):
    header = (
        '"User ID",STRING,"Name",STRING,"First Name",STRING,"Last Name",STRING,'
        '"Email",STRING,"Role",STRING,"Department",STRING,"Country",STRING,'
        '"Location",STRING,"Phone",STRING,"Join Date",DATETIME,'
        '"Manager ID",STRING,"Sales Target",DOUBLE'
    )
    data_rows = []
    for r in rows:
        data_rows.append(
            "{" +
            f'{dax_str(r.get("User ID"))},'
            f'{dax_str(r.get("Name"))},'
            f'{dax_str(r.get("First Name"))},'
            f'{dax_str(r.get("Last Name"))},'
            f'{dax_str(r.get("Email"))},'
            f'{dax_str(r.get("Role"))},'
            f'{dax_str(r.get("Department"))},'
            f'{dax_str(r.get("Country"))},'
            f'{dax_str(r.get("Location"))},'
            f'{dax_str(r.get("Phone"))},'
            f'{dax_date(r.get("Join Date"))},'
            f'{dax_str(r.get("Manager ID"))},'
            f'{dax_num(r.get("Sales Target"))}'
            + "}"
        )
    return _dt(header, data_rows)

# ── Column / measure schema builders ────────────────────────────────────────────
def col_def(name, dtype, summarize="none", fmt=None, hidden=False):
    d = {"name": name, "dataType": dtype, "lineageTag": uid(),
         "summarizeBy": summarize,
         "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]}
    if fmt:    d["formatString"] = fmt
    if hidden: d["isHidden"] = True
    return d

def measure_def(name, expr, fmt=None, display_folder=""):
    d = {"name": name, "lineageTag": uid(), "expression": expr,
         "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]}
    if fmt:            d["formatString"] = fmt
    if display_folder: d["displayFolder"] = display_folder
    return d

def partition_calc(table_name, expr_lines):
    return [{"name": table_name, "mode": "import",
             "source": {"type": "calculated", "expression": expr_lines}}]

# ── DataModelSchema ──────────────────────────────────────────────────────────────
def build_schema(sales_rows, customers_rows, products_rows, users_rows):
    tag = uid

    # ── SALES TABLE ──
    sales_cols = [
        col_def("Order ID",          "string"),
        col_def("Order Date",        "dateTime",   fmt="Short Date"),
        col_def("Year",              "int64",      summarize="sum", hidden=True),
        col_def("Month",             "int64",      summarize="sum", hidden=True),
        col_def("Quarter",           "string"),
        col_def("Customer ID",       "string"),
        col_def("Product ID",        "string"),
        col_def("User ID",           "string"),
        col_def("Category",          "string"),
        col_def("Quantity",          "int64",      summarize="sum"),
        col_def("Unit Price",        "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Unit Cost",         "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Gross Sales",       "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Discount Pct",      "double",     summarize="none", fmt='0.00%'),
        col_def("Discount Amount",   "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Net Sales",         "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Total Cost",        "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Profit",            "double",     summarize="sum",  fmt=r'$#,0.00'),
        col_def("Profit Margin Pct", "double",     summarize="none", fmt='0.00%'),
        col_def("Sales Channel",     "string"),
        col_def("Order Status",      "string"),
        col_def("Ship Date",         "dateTime",   fmt="Short Date"),
        col_def("Payment Method",    "string"),
    ]
    sales_measures = [
        measure_def("Total Revenue",         'SUM(Sales[Net Sales])',              fmt=r'$#,0',   display_folder="KPIs"),
        measure_def("Total Profit",          'SUM(Sales[Profit])',                 fmt=r'$#,0',   display_folder="KPIs"),
        measure_def("Total Cost",            'SUM(Sales[Total Cost])',             fmt=r'$#,0',   display_folder="KPIs"),
        measure_def("Gross Sales",           'SUM(Sales[Gross Sales])',            fmt=r'$#,0',   display_folder="KPIs"),
        measure_def("Total Discount",        'SUM(Sales[Discount Amount])',        fmt=r'$#,0',   display_folder="KPIs"),
        measure_def("Total Quantity",        'SUM(Sales[Quantity])',               fmt='#,0',     display_folder="KPIs"),
        measure_def("Total Orders",          'COUNTROWS(Sales)',                   fmt='#,0',     display_folder="KPIs"),
        measure_def("Avg Order Value",       'DIVIDE([Total Revenue],[Total Orders])', fmt=r'$#,0', display_folder="KPIs"),
        measure_def("Profit Margin %",       'DIVIDE([Total Profit],[Total Revenue])', fmt='0.0%', display_folder="KPIs"),
        measure_def("Avg Profit Margin",     'AVERAGEX(VALUES(Sales[Category]),[Profit Margin %])', fmt='0.0%', display_folder="KPIs"),
        measure_def("Completed Orders",      'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Completed")', fmt='#,0', display_folder="Status"),
        measure_def("Pending Orders",        'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Pending")',   fmt='#,0', display_folder="Status"),
        measure_def("Returned Orders",       'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Returned")', fmt='#,0', display_folder="Status"),
        measure_def("Return Rate",           'DIVIDE([Returned Orders],[Total Orders])', fmt='0.0%', display_folder="Status"),
        measure_def("Sales Target Total",    'SUM(Users[Sales Target])',           fmt=r'$#,0',   display_folder="KPIs"),
        measure_def("Target Achievement %",  'DIVIDE([Total Revenue],[Sales Target Total])', fmt='0.0%', display_folder="KPIs"),
        measure_def("YoY Revenue Growth",
            'VAR CY=MAXX(ALL(Sales[Year]),Sales[Year])'
            '\nVAR CY_Rev=CALCULATE([Total Revenue],Sales[Year]=CY)'
            '\nVAR PY_Rev=CALCULATE([Total Revenue],Sales[Year]=CY-1)'
            '\nRETURN DIVIDE(CY_Rev-PY_Rev,PY_Rev)',
            fmt='+0.0%;-0.0%;0.0%', display_folder="KPIs"),
        measure_def("Revenue Prior Year",
            'VAR CY=MAXX(ALL(Sales[Year]),Sales[Year])'
            '\nRETURN CALCULATE([Total Revenue],Sales[Year]=CY-1)',
            fmt=r'$#,0', display_folder="KPIs"),
    ]
    sales_table = {
        "name": "Sales",
        "lineageTag": uid(),
        "columns": sales_cols,
        "measures": sales_measures,
        "partitions": partition_calc("Sales", build_datatable_sales(sales_rows)),
        "annotations": [{"name": "$AutoCreatedDate", "value": datetime.now().isoformat()}],
    }

    # ── CUSTOMERS TABLE ──
    customers_table = {
        "name": "Customers",
        "lineageTag": uid(),
        "columns": [
            col_def("Customer ID",        "string"),
            col_def("First Name",         "string"),
            col_def("Last Name",          "string"),
            col_def("Email",              "string"),
            col_def("Phone",              "string"),
            col_def("Address",            "string"),
            col_def("City",               "string"),
            col_def("Country",            "string"),
            col_def("Postal Code",        "string"),
            col_def("Segment",            "string"),
            col_def("Registration Date",  "dateTime", fmt="Short Date"),
            col_def("Credit Limit",       "double",  summarize="sum", fmt=r'$#,0'),
        ],
        "measures": [
            measure_def("Total Customers", "COUNTROWS(Customers)", fmt='#,0'),
            measure_def("Avg Credit Limit", "AVERAGE(Customers[Credit Limit])", fmt=r'$#,0'),
        ],
        "partitions": partition_calc("Customers", build_datatable_customers(customers_rows)),
        "annotations": [],
    }

    # ── PRODUCTS TABLE ──
    products_table = {
        "name": "Products",
        "lineageTag": uid(),
        "columns": [
            col_def("Product ID",         "string"),
            col_def("Product Name",       "string"),
            col_def("Category",           "string"),
            col_def("Sub Category",       "string"),
            col_def("Brand",              "string"),
            col_def("Unit Cost",          "double",  summarize="sum", fmt=r'$#,0.00'),
            col_def("Unit Price",         "double",  summarize="sum", fmt=r'$#,0.00'),
            col_def("Profit Margin Pct",  "double",  summarize="none", fmt='0.0%'),
            col_def("Stock Quantity",     "int64",   summarize="sum"),
            col_def("Reorder Level",      "int64",   summarize="sum"),
            col_def("Supplier",           "string"),
            col_def("Weight kg",          "double",  summarize="sum"),
            col_def("Rating",             "double",  summarize="average"),
        ],
        "measures": [
            measure_def("Total Products",    "COUNTROWS(Products)", fmt='#,0'),
            measure_def("Avg Rating",        "AVERAGE(Products[Rating])", fmt='0.00'),
            measure_def("Total Stock",       "SUM(Products[Stock Quantity])", fmt='#,0'),
        ],
        "partitions": partition_calc("Products", build_datatable_products(products_rows)),
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
            col_def("Sales Target", "double",  summarize="sum", fmt=r'$#,0'),
        ],
        "measures": [
            measure_def("Total Sales Reps", "COUNTROWS(Users)", fmt='#,0'),
        ],
        "partitions": partition_calc("Users", build_datatable_users(users_rows)),
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
                {"name": "PBI_QueryOrder",     "value": '["Sales","Customers","Products","Users"]'},
            ],
            "cultures": [{"name": "en-US", "linguisticMetadata": {"Version": "1.0.0", "Language": "en-US"}}],
        }
    }
    return schema

# ── Diagram layout ───────────────────────────────────────────────────────────────
def build_diagram_layout(schema):
    tables = schema["model"]["tables"]
    positions = {"Sales": (10, 10), "Customers": (280, 200), "Products": (550, 10), "Users": (280, 10)}
    nodes = []
    for i, t in enumerate(tables):
        x, y = positions.get(t["name"], (i * 280, 10))
        nodes.append({
            "location": {"x": x, "y": y},
            "nodeIndex": t["name"],
            "nodeLineageTag": t["lineageTag"],
            "size": {"height": max(120, 30 + 20 * len(t["columns"])), "width": 234},
            "zIndex": i
        })
    return {"version": "1.1.0", "diagrams": [{"ordinal": 0, "scrollPosition": {"x": 0, "y": 0}, "nodes": nodes}]}

# ── Report Layout Helpers ────────────────────────────────────────────────────────
def frm(alias, entity):   return {"Name": alias, "Entity": entity, "Type": 0}
def col_s(alias, prop, entity):
    return {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
            "Name": f"{entity}.{prop}", "NativeReferenceName": prop}
def msr_s(alias, prop, entity):
    return {"Measure": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop},
            "Name": f"{entity}.{prop}", "NativeReferenceName": prop}
def agg_s(alias, prop, entity, fn=0):
    fn_name = {0:"Sum",1:"Avg",2:"Min",3:"Max",5:"CountNonNull"}.get(fn,"Sum")
    return {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}},
            "Property": prop}}, "Function": fn},
            "Name": f"{fn_name}({entity}.{prop})", "NativeReferenceName": prop}

def make_query_str(frm_list, selects):
    pq = {"Version": 2, "From": frm_list, "Select": selects}
    cmd = {"Commands": [{"SemanticQueryDataShapeCommand": {
        "Query": pq,
        "Binding": {
            "Primary": {"Groupings": [{"Projections": list(range(len(selects)))}]},
            "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
            "Version": 1
        },
        "ExecutionMetricsKind": 1
    }}]}
    return js(cmd)

def vc_config(vtype, frm_list, selects, title=None, theme_color=None):
    pq = {"Version": 2, "From": frm_list, "Select": selects}
    vc_objs = {}
    if title:
        vc_objs["title"] = [{"properties": {
            "show":     {"expr": {"Literal": {"Value": "true"}}},
            "text":     {"expr": {"Literal": {"Value": f"'{title}'"}}},
            "fontSize": {"expr": {"Literal": {"Value": "11D"}}}
        }}]
    if theme_color:
        vc_objs.setdefault("background", [{}])

    sv = {"visualType": vtype, "projectionMapping": {}, "prototypeQuery": pq, "columnProperties": {}}
    if vc_objs:
        sv["vcObjects"] = vc_objs
    return js({
        "name":    uid()[:20],
        "layouts": [{"id": 0, "position": {"x": 0, "y": 0, "z": 0, "height": 100, "width": 100, "tabOrder": 0}}],
        "singleVisual": sv
    })

def make_vc(x, y, w, h, vtype, frm_list, selects, title=None):
    cfg   = vc_config(vtype, frm_list, selects, title)
    query = make_query_str(frm_list, selects)
    return {"x": x, "y": y, "z": 0, "width": w, "height": h, "tabOrder": 0,
            "filters": "[]", "config": cfg, "query": query, "dataTransforms": "{}"}

def make_page(display_name, visuals):
    return {"name": uid()[:20], "displayName": display_name,
            "width": W, "height": H,
            "visualContainers": visuals,
            "config": js({"relationships": []}),
            "filters": "[]"}

# ── KPI Card row ─────────────────────────────────────────────────────────────────
def kpi_row(y=12, h=92):
    """6 KPI cards for all pages."""
    card_w, gap, start_x = 196, 10, 13
    cards = [
        ("Total Revenue",       "s", "Sales"),
        ("Total Profit",        "s", "Sales"),
        ("Total Orders",        "s", "Sales"),
        ("Avg Order Value",     "s", "Sales"),
        ("Return Rate",         "s", "Sales"),
        ("Target Achievement %","s", "Sales"),
    ]
    result = []
    for i, (mname, alias, entity) in enumerate(cards):
        x = start_x + i * (card_w + gap)
        selects  = [msr_s(alias, mname, entity)]
        frm_list = [frm(alias, entity)]
        result.append(make_vc(x, y, card_w, h, "card", frm_list, selects))
    return result

# ── PAGE 1: Executive Summary ────────────────────────────────────────────────────
def page_executive_summary():
    visuals = kpi_row(y=12, h=92)

    # Revenue Trend — CY vs PY line chart
    frm_list = [frm("s", "Sales")]
    visuals.append(make_vc(13, 114, 1247, 210, "lineChart", frm_list, [
        col_s("s", "Month",  "Sales"),
        col_s("s", "Year",   "Sales"),
        msr_s("s", "Total Revenue", "Sales"),
    ], title="Revenue Trend — Net Sales by Month & Year"))

    # Row 3: 3 charts side by side
    chart_w, chart_h, chart_y = 406, 360, 334
    x1, x2, x3 = 13, 429, 845

    # Sales by Category (horizontal bar)
    visuals.append(make_vc(x1, chart_y, chart_w, chart_h, "clusteredBarChart", [frm("s","Sales")], [
        col_s("s", "Category",   "Sales"),
        msr_s("s", "Total Revenue", "Sales"),
    ], title="Sales by Category"))

    # Sales Channel Mix (donut)
    visuals.append(make_vc(x2, chart_y, chart_w, chart_h, "donutChart", [frm("s","Sales")], [
        col_s("s", "Sales Channel", "Sales"),
        msr_s("s", "Total Revenue",  "Sales"),
    ], title="Sales Channel Mix"))

    # Order Status Distribution (donut)
    visuals.append(make_vc(x3, chart_y, chart_w, chart_h, "donutChart", [frm("s","Sales")], [
        col_s("s", "Order Status", "Sales"),
        msr_s("s", "Total Orders", "Sales"),
    ], title="Order Status Distribution"))

    return make_page("Executive Summary", visuals)

# ── PAGE 2: Sales Performance ────────────────────────────────────────────────────
def page_sales_performance():
    visuals = kpi_row(y=12, h=92)

    # Orders Matrix (heatmap) — Year × Month
    visuals.append(make_vc(13, 114, 1247, 175, "pivotTable", [frm("s","Sales")], [
        col_s("s", "Year",   "Sales"),
        col_s("s", "Month",  "Sales"),
        msr_s("s", "Total Orders", "Sales"),
    ], title="Monthly Orders Heatmap — Count by Year & Month"))

    # Sales by Country (use Customers[Country] joined via Sales)
    visuals.append(make_vc(13, 299, 614, 210, "clusteredBarChart",
        [frm("s","Sales"), frm("c","Customers")], [
            col_s("c", "Country",      "Customers"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Net Sales by Customer Country"))

    # Payment Method bar
    visuals.append(make_vc(641, 299, 619, 210, "clusteredColumnChart",
        [frm("s","Sales")], [
            col_s("s", "Payment Method", "Sales"),
            msr_s("s", "Total Orders",   "Sales"),
        ], title="Orders by Payment Method"))

    # Quarterly Revenue by Year
    visuals.append(make_vc(13, 519, 1247, 188, "clusteredColumnChart",
        [frm("s","Sales")], [
            col_s("s", "Quarter",      "Sales"),
            col_s("s", "Year",         "Sales"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Quarterly Revenue by Year"))

    return make_page("Sales Performance", visuals)

# ── PAGE 3: Product Analysis ─────────────────────────────────────────────────────
def page_product_analysis():
    visuals = kpi_row(y=12, h=92)

    # Top Products by Revenue (horizontal bar)
    visuals.append(make_vc(13, 114, 619, 290, "clusteredBarChart",
        [frm("s","Sales"), frm("p","Products")], [
            col_s("p", "Product Name",  "Products"),
            msr_s("s", "Total Revenue", "Sales"),
        ], title="Top Products by Net Sales"))

    # Profit Margin % by Category
    visuals.append(make_vc(646, 114, 619, 290, "clusteredColumnChart",
        [frm("s","Sales")], [
            col_s("s", "Category",        "Sales"),
            msr_s("s", "Profit Margin %", "Sales"),
        ], title="Profit Margin % by Category"))

    # Category Revenue vs Profit (grouped bar)
    visuals.append(make_vc(13, 414, 1247, 290, "clusteredColumnChart",
        [frm("s","Sales")], [
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
        [frm("c","Customers"), frm("s","Sales")], [
            col_s("c", "Segment",      "Customers"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Revenue by Customer Segment"))

    # Sales by Customer Country (bar)
    visuals.append(make_vc(422, 114, 843, 285, "clusteredBarChart",
        [frm("c","Customers"), frm("s","Sales")], [
            col_s("c", "Country",      "Customers"),
            msr_s("s", "Total Revenue","Sales"),
        ], title="Sales by Customer Country"))

    # Segment × Order Status (stacked bar)
    visuals.append(make_vc(13, 409, 614, 295, "stackedBarChart",
        [frm("c","Customers"), frm("s","Sales")], [
            col_s("c", "Segment",      "Customers"),
            col_s("s", "Order Status", "Sales"),
            msr_s("s", "Total Orders", "Sales"),
        ], title="Order Status by Customer Segment"))

    # Avg Credit Limit by Segment
    visuals.append(make_vc(641, 409, 619, 295, "clusteredColumnChart",
        [frm("c","Customers")], [
            col_s("c", "Segment",       "Customers"),
            msr_s("c", "Avg Credit Limit","Customers"),
        ], title="Avg Credit Limit by Segment"))

    return make_page("Customer Insights", visuals)

# ── PAGE 5: Team Performance ──────────────────────────────────────────────────────
def page_team_performance():
    visuals = kpi_row(y=12, h=92)

    # Team Sales vs Target (clustered column)
    visuals.append(make_vc(13, 114, 1247, 250, "clusteredColumnChart",
        [frm("u","Users"), frm("s","Sales")], [
            col_s("u", "Name",           "Users"),
            msr_s("s", "Total Revenue",  "Sales"),
            msr_s("s", "Sales Target Total", "Sales"),
        ], title="Team Sales vs Target"))

    # Sales by Location (horizontal bar)
    visuals.append(make_vc(13, 374, 604, 330, "clusteredBarChart",
        [frm("u","Users"), frm("s","Sales")], [
            col_s("u", "Location",       "Users"),
            msr_s("s", "Total Revenue",  "Sales"),
        ], title="Net Sales by Location"))

    # Team table
    visuals.append(make_vc(631, 374, 634, 330, "tableEx",
        [frm("u","Users"), frm("s","Sales")], [
            col_s("u", "Name",           "Users"),
            col_s("u", "Role",           "Users"),
            col_s("u", "Location",       "Users"),
            msr_s("s", "Total Revenue",  "Sales"),
            col_s("u", "Sales Target",   "Users"),
            msr_s("s", "Target Achievement %", "Sales"),
        ], title="Sales Team Performance Table"))

    return make_page("Team Performance", visuals)

# ── Report config / theme ref ────────────────────────────────────────────────────
REPORT_CONFIG = js({
    "version": "5.40",
    "themeCollection": {"baseTheme": {"name": "CY23SU11", "version": "5.40", "type": 2}},
    "defaultDrillFilterOtherVisuals": True,
    "linguisticSchemaSyncVersion": 2,
    "settings": {"useStylableVisualContainerHeader": True}
})

THEME_JSON = """{
  "name": "CY23SU11",
  "dataColors": ["#118DFF","#12239E","#E66C37","#6B007B","#E044A7","#744EC2","#D9B300","#D64550"],
  "good": "#01B8AA", "neutral": "#F2C80F", "bad": "#FD625E",
  "background": "#FFFFFF", "foreground": "#252423",
  "tableAccent": "#118DFF"
}"""

# ── Static files ──────────────────────────────────────────────────────────────────
CONTENT_TYPES_PBIT = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml"  ContentType="application/xml"  />
  <Override PartName="/DataModelSchema"    ContentType="application/json" />
  <Override PartName="/DiagramLayout"      ContentType="application/json" />
  <Override PartName="/Report/Layout"      ContentType="application/json" />
  <Override PartName="/Settings"           ContentType="application/json" />
  <Override PartName="/Metadata"           ContentType="application/json" />
  <Override PartName="/SecurityBindings"   ContentType="application/octet-stream" />
  <Override PartName="/Version"            ContentType="application/json" />
</Types>"""

VERSION   = "3.0"
METADATA  = json.dumps({"Version": 5, "AutoCreatedRelationships": [],
                         "CreatedFrom": "Cloud", "CreatedFromRelease": "2024.04"})
SETTINGS  = json.dumps({"Version": 4, "ReportSettings": {},
                         "QueriesSettings": {"TypeDetectionEnabled": True,
                                              "RelationshipImportEnabled": True,
                                              "Version": "2.124.2028.0"}})

# ── Package builder ───────────────────────────────────────────────────────────────
def write_pbit(schema, diagram, pages):
    layout = {"id": 0, "resourcePackages": [
        {"resourcePackage": {"name": "SharedResources", "type": 2,
                             "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json",
                                        "name": "CY23SU11"}], "disabled": False}}
    ], "sections": pages, "config": REPORT_CONFIG, "layoutOptimization": 0}

    with zipfile.ZipFile(OUTPUT_PBIT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Version",                VERSION.encode("utf-8"))
        z.writestr("[Content_Types].xml",    CONTENT_TYPES_PBIT.encode("utf-8"))
        z.writestr("DataModelSchema",        json.dumps(schema, ensure_ascii=False).encode("utf-8"))
        z.writestr("DiagramLayout",          json.dumps(diagram, ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Report/Layout",          json.dumps(layout,  ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Settings",               SETTINGS.encode("utf-16-le"))
        z.writestr("Metadata",               METADATA.encode("utf-16-le"))
        z.writestr("SecurityBindings",       b"")
        z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",
                   THEME_JSON.encode("utf-8"))
    print(f"[OK] Written: {OUTPUT_PBIT}")

def write_pbix(schema, diagram, pages):
    """Build PBIX using only DATATABLE calculated tables — no legacy DataModel binary.
    The file is structurally identical to the .pbit; Power BI Desktop evaluates
    the DATATABLE DAX on first open and lets the user save a fully populated .pbix."""
    layout = {"id": 0, "resourcePackages": [
        {"resourcePackage": {"name": "SharedResources", "type": 2,
                             "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json",
                                        "name": "CY23SU11"}], "disabled": False}}
    ], "sections": pages, "config": REPORT_CONFIG, "layoutOptimization": 0}

    with zipfile.ZipFile(OUTPUT_PBIX, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Version",                VERSION.encode("utf-8"))
        z.writestr("[Content_Types].xml",    CONTENT_TYPES_PBIT.encode("utf-8"))
        z.writestr("DataModelSchema",        json.dumps(schema, ensure_ascii=False).encode("utf-8"))
        z.writestr("DiagramLayout",          json.dumps(diagram, ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Report/Layout",          json.dumps(layout,  ensure_ascii=False).encode("utf-16-le"))
        z.writestr("Settings",               SETTINGS.encode("utf-16-le"))
        z.writestr("Metadata",               METADATA.encode("utf-16-le"))
        z.writestr("SecurityBindings",       b"")
        z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",
                   THEME_JSON.encode("utf-8"))
    print(f"[OK] Written: {OUTPUT_PBIX}")

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

    print("Building DataModelSchema …")
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
        print(f"  • {p['displayName']} ({len(p['visualContainers'])} visuals)")

    print("Writing SalesAnalytics.pbit …")
    write_pbit(schema, diagram, pages)

    print("Writing SalesAnalytics.pbix …")
    write_pbix(schema, diagram, pages)

    print("\nDone!")
    print("→ SalesAnalytics.pbit  — Open in Power BI Desktop, click 'Apply Changes', save as .pbix")
    print("→ SalesAnalytics.pbix  — Open in Power BI Desktop (data from DATATABLE is embedded)")

if __name__ == "__main__":
    main()

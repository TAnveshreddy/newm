"""
Generates make1_with_relationships.pbit  — a Power BI Template that
contains all 7 tables with sample data, 6 proper relationships, and
14 KPI DAX measures.

Open in Power BI Desktop to verify the model.  Swap the DATATABLE()
partitions with your actual data-source queries to go live.
"""

import json, zipfile, uuid, os

# ── helpers ─────────────────────────────────────────────────────────────────

def uid():
    return uuid.uuid4().hex

def encode16(text):
    return text.encode("utf-16-le")

# ── TMSL model ───────────────────────────────────────────────────────────────

# ---------- sample rows (enough to validate relationships / visuals) ----------
ORDERS_ROWS = [
    ["CA-2019-152156","CG-12520","FUR-BO-10001798","2019-11-08","2019-11-11","Second Class","Consumer","Henderson","Kentucky","South","Furniture","Bookcases",261.96,2,0.0,41.91],
    ["CA-2019-138688","DV-13045","FUR-CH-10000454","2019-06-12","2019-06-16","Second Class","Corporate","Henderson","Kentucky","South","Furniture","Chairs",731.94,3,0.0,219.58],
    ["CA-2019-138688","DV-13045","OFF-LA-10000240","2019-06-12","2019-06-16","Second Class","Corporate","Henderson","Kentucky","South","Office Supplies","Labels",14.62,2,0.0,6.87],
    ["US-2019-108966","SO-20335","OFF-ST-10000760","2019-10-11","2019-10-18","Standard Class","Consumer","Fort Lauderdale","Florida","South","Office Supplies","Storage",957.58,5,0.45,-383.03],
    ["US-2019-108966","SO-20335","OFF-AR-10002833","2019-10-11","2019-10-18","Standard Class","Consumer","Fort Lauderdale","Florida","South","Office Supplies","Art",22.37,2,0.0,2.52],
    ["CA-2019-115812","BH-11710","FUR-FU-10001487","2019-06-09","2019-06-14","Standard Class","Consumer","Los Angeles","California","West","Furniture","Furnishings",48.86,7,0.0,14.17],
    ["CA-2019-115812","BH-11710","OFF-AR-10002833","2019-06-09","2019-06-14","Standard Class","Consumer","Los Angeles","California","West","Technology","Phones",7.28,4,0.0,1.97],
    ["CA-2019-115812","BH-11710","TEC-PH-10002275","2019-06-09","2019-06-14","Standard Class","Consumer","Los Angeles","California","West","Technology","Phones",907.15,6,0.2,90.72],
    ["CA-2020-167164","EH-13945","FUR-BO-10003714","2020-05-13","2020-05-15","First Class","Consumer","Seattle","Washington","West","Furniture","Bookcases",77.88,3,0.2,-13.38],
    ["CA-2020-143336","AO-10660","TEC-PH-10001530","2020-08-27","2020-09-01","Standard Class","Consumer","Houston","Texas","Central","Technology","Phones",1097.54,7,0.0,164.63],
    ["CA-2021-105893","MB-18085","OFF-ST-10004186","2021-03-14","2021-03-19","Standard Class","Home Office","New York City","New York","East","Office Supplies","Storage",665.88,6,0.2,-125.44],
    ["CA-2021-118977","KL-16645","TEC-AC-10002167","2021-11-22","2021-11-26","Second Class","Corporate","Philadelphia","Pennsylvania","East","Technology","Accessories",55.98,3,0.0,20.98],
    ["CA-2022-100391","SC-20380","FUR-CH-10000454","2022-01-10","2022-01-14","Standard Class","Consumer","Charlotte","North Carolina","South","Furniture","Chairs",954.64,4,0.0,286.39],
    ["CA-2022-167199","EM-13885","OFF-BI-10003910","2022-09-06","2022-09-10","Second Class","Corporate","Dallas","Texas","Central","Office Supplies","Binders",412.02,5,0.2,-49.44],
]

CUSTOMERS_ROWS = [
    ["CG-12520","Claire Gute","Consumer"],
    ["DV-13045","Darrin Van Huff","Corporate"],
    ["SO-20335","Sean O'Donnell","Consumer"],
    ["BH-11710","Brosina Hoffman","Consumer"],
    ["EH-13945","Eric Hoffmann","Consumer"],
    ["AO-10660","Allen Rosenblatt","Consumer"],
    ["MB-18085","Matt Bhatt","Home Office"],
    ["KL-16645","Ken Lonsdale","Corporate"],
    ["SC-20380","Sanjit Chand","Consumer"],
    ["EM-13885","Emily Phan","Corporate"],
]

PRODUCTS_ROWS = [
    ["FUR-BO-10001798","Furniture","Bookcases","Bush Somerset Collection Bookcase"],
    ["FUR-CH-10000454","Furniture","Chairs","Hon Deluxe Fabric Upholstered Stacking Chairs"],
    ["OFF-LA-10000240","Office Supplies","Labels","Self-Adhesive Address Labels"],
    ["OFF-ST-10000760","Office Supplies","Storage","Eldon Fold 'N Roll Cart System"],
    ["OFF-AR-10002833","Office Supplies","Art","Newell 322"],
    ["FUR-FU-10001487","Furniture","Furnishings","Eldon Expressions Desk Accessories"],
    ["TEC-PH-10002275","Technology","Phones","Motorola Smart Phone"],
    ["FUR-BO-10003714","Furniture","Bookcases","Sauder Classic Bookcase"],
    ["TEC-PH-10001530","Technology","Phones","Samsung Convoy 3"],
    ["OFF-ST-10004186","Office Supplies","Storage","Fellowes Super Stor/Drawer"],
    ["TEC-AC-10002167","Technology","Accessories","Logitech Wireless Keyboard"],
    ["OFF-BI-10003910","Office Supplies","Binders","GBC Ibimaster 500 Manual ProClick Binding System"],
]

RETURNS_ROWS = [
    ["Yes","CA-2019-108966"],
    ["Yes","US-2019-108966"],
    ["Yes","CA-2020-167164"],
]

USERS_ROWS = [
    ["Anna Andreadi","Central"],
    ["Chuck Magee","South"],
    ["Kelly Williams","East"],
    ["Matt Collister","West"],
    ["Deborah Brumfield","Central"],
]

MONTHLY_KPIS_ROWS = [
    ["2022-01-01",50000.0,5000.0,200],
    ["2022-02-01",55000.0,5500.0,220],
    ["2022-03-01",60000.0,6000.0,240],
    ["2022-04-01",52000.0,5200.0,210],
    ["2022-05-01",58000.0,5800.0,230],
    ["2022-06-01",65000.0,6500.0,260],
    ["2022-07-01",62000.0,6200.0,250],
    ["2022-08-01",70000.0,7000.0,280],
    ["2022-09-01",68000.0,6800.0,272],
    ["2022-10-01",75000.0,7500.0,300],
    ["2022-11-01",80000.0,8000.0,320],
    ["2022-12-01",90000.0,9000.0,360],
]

SALES_ROWS = [
    ["South","Furniture",2019,261.96,41.91],
    ["South","Office Supplies",2019,14.62,6.87],
    ["South","Office Supplies",2019,957.58,-383.03],
    ["West","Furniture",2019,48.86,14.17],
    ["West","Technology",2019,907.15,90.72],
    ["West","Furniture",2020,77.88,-13.38],
    ["Central","Technology",2020,1097.54,164.63],
    ["East","Office Supplies",2021,665.88,-125.44],
    ["East","Technology",2021,55.98,20.98],
    ["South","Furniture",2022,954.64,286.39],
    ["Central","Office Supplies",2022,412.02,-49.44],
]


def dt_expr(rows, col_defs, type_map):
    """Build a DATATABLE() DAX expression string."""
    cols = ", ".join(f'"{c}", {type_map[t]}' for c, t in col_defs)
    def fmt(val, t):
        if val is None:
            return "BLANK()"
        if t == "string":
            return f'"{val}"'
        if t == "dateTime":
            y, m, d = val.split("-")
            return f"DATE({y},{int(m)},{int(d)})"
        return str(val)
    row_strs = []
    for row in rows:
        vals = ", ".join(fmt(v, col_defs[i][1]) for i, v in enumerate(row))
        row_strs.append(f"  {{{vals}}}")
    return f"DATATABLE(\n  {cols},\n  {{\n" + ",\n".join(row_strs) + "\n  }\n)"


TMAP = {"string": "STRING", "dateTime": "DATETIME", "double": "DOUBLE", "int64": "INTEGER"}

orders_expr = dt_expr(ORDERS_ROWS, [
    ("Order ID","string"),("Customer ID","string"),("Product ID","string"),
    ("Order Date","dateTime"),("Ship Date","dateTime"),("Ship Mode","string"),
    ("Segment","string"),("City","string"),("State","string"),("Region","string"),
    ("Category","string"),("Sub-Category","string"),
    ("Sales","double"),("Quantity","int64"),("Discount","double"),("Profit","double"),
], TMAP)

customers_expr = dt_expr(CUSTOMERS_ROWS, [
    ("Customer ID","string"),("Customer Name","string"),("Segment","string"),
], TMAP)

products_expr = dt_expr(PRODUCTS_ROWS, [
    ("Product ID","string"),("Category","string"),("Sub-Category","string"),
    ("Product Name","string"),
], TMAP)

returns_expr = dt_expr(RETURNS_ROWS, [
    ("Returned","string"),("Order ID","string"),
], TMAP)

users_expr = dt_expr(USERS_ROWS, [
    ("Person","string"),("Region","string"),
], TMAP)

monthly_kpis_expr = dt_expr(MONTHLY_KPIS_ROWS, [
    ("Month","dateTime"),("Target Sales","double"),
    ("Target Profit","double"),("Target Orders","int64"),
], TMAP)

sales_expr = dt_expr(SALES_ROWS, [
    ("Region","string"),("Category","string"),("Year","int64"),
    ("Sales","double"),("Profit","double"),
], TMAP)


def make_col(name, dtype, lt=None):
    col = {"name": name, "dataType": dtype, "lineageTag": lt or uid(),
           "summarizeBy": "none"}
    if dtype in ("double","int64"):
        col["summarizeBy"] = "sum"
    return col

def make_measure(name, expr, fmt_str=None, lt=None):
    m = {"name": name, "expression": expr, "lineageTag": lt or uid()}
    if fmt_str:
        m["formatString"] = fmt_str
    return m

def make_table(name, columns, measures, expr):
    return {
        "name": name,
        "lineageTag": uid(),
        "columns": columns,
        "measures": measures,
        "partitions": [{
            "name": name,
            "mode": "import",
            "source": {"type": "calculated", "expression": expr}
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
    }


# ── Tables ───────────────────────────────────────────────────────────────────

orders_table = make_table("Orders", [
    make_col("Order ID",    "string"),
    make_col("Customer ID", "string"),
    make_col("Product ID",  "string"),
    make_col("Order Date",  "dateTime"),
    make_col("Ship Date",   "dateTime"),
    make_col("Ship Mode",   "string"),
    make_col("Segment",     "string"),
    make_col("City",        "string"),
    make_col("State",       "string"),
    make_col("Region",      "string"),
    make_col("Category",    "string"),
    make_col("Sub-Category","string"),
    make_col("Sales",       "double"),
    make_col("Quantity",    "int64"),
    make_col("Discount",    "double"),
    make_col("Profit",      "double"),
], [
    make_measure("Total Sales",          "SUM(Orders[Sales])",                                    "#,##0.00"),
    make_measure("Total Profit",         "SUM(Orders[Profit])",                                   "#,##0.00"),
    make_measure("Profit Margin %",      "DIVIDE([Total Profit], [Total Sales], 0)",               "0.00%"),
    make_measure("Total Orders",         "DISTINCTCOUNT(Orders[Order ID])",                       "#,##0"),
    make_measure("Total Customers",      "DISTINCTCOUNT(Orders[Customer ID])",                    "#,##0"),
    make_measure("Avg Order Value",      "DIVIDE([Total Sales], [Total Orders], 0)",              "#,##0.00"),
    make_measure("Total Quantity",       "SUM(Orders[Quantity])",                                 "#,##0"),
    make_measure("Avg Discount",         "AVERAGE(Orders[Discount])",                             "0.00%"),
    make_measure("Sales YoY %",
        'VAR CY = CALCULATE([Total Sales], YEAR(Orders[Order Date]) = YEAR(TODAY()))\n'
        'VAR PY = CALCULATE([Total Sales], YEAR(Orders[Order Date]) = YEAR(TODAY()) - 1)\n'
        'RETURN DIVIDE(CY - PY, PY, 0)', "0.00%"),
    make_measure("Target Achievement %",
        "DIVIDE([Total Sales], SUM('Monthly KPIs'[Target Sales]), 0)", "0.00%"),
], orders_expr)

customers_table = make_table("Customers", [
    make_col("Customer ID",   "string"),
    make_col("Customer Name", "string"),
    make_col("Segment",       "string"),
], [], customers_expr)

products_table = make_table("Products", [
    make_col("Product ID",   "string"),
    make_col("Category",     "string"),
    make_col("Sub-Category", "string"),
    make_col("Product Name", "string"),
], [
    make_measure("Total Products", "DISTINCTCOUNT(Products[Product ID])", "#,##0"),
], products_expr)

returns_table = make_table("Returns", [
    make_col("Returned", "string"),
    make_col("Order ID", "string"),
], [
    make_measure("Total Returns",   "COUNTROWS(Returns)",                          "#,##0"),
    make_measure("Return Rate %",   "DIVIDE([Total Returns], [Total Orders], 0)",  "0.00%"),
], returns_expr)

users_table = make_table("Users", [
    make_col("Person", "string"),
    make_col("Region", "string"),
], [], users_expr)

monthly_kpis_table = make_table("Monthly KPIs", [
    make_col("Month",          "dateTime"),
    make_col("Target Sales",   "double"),
    make_col("Target Profit",  "double"),
    make_col("Target Orders",  "int64"),
], [], monthly_kpis_expr)

sales_table = make_table("Sales", [
    make_col("Region",   "string"),
    make_col("Category", "string"),
    make_col("Year",     "int64"),
    make_col("Sales",    "double"),
    make_col("Profit",   "double"),
], [], sales_expr)


# ── Relationships ─────────────────────────────────────────────────────────────

relationships = [
    {
        "name": uid(),
        "fromTable": "Orders",
        "fromColumn": "Customer ID",
        "toTable": "Customers",
        "toColumn": "Customer ID",
        "crossFilteringBehavior": "singleDirection"
    },
    {
        "name": uid(),
        "fromTable": "Orders",
        "fromColumn": "Product ID",
        "toTable": "Products",
        "toColumn": "Product ID",
        "crossFilteringBehavior": "singleDirection"
    },
    {
        "name": uid(),
        "fromTable": "Returns",
        "fromColumn": "Order ID",
        "toTable": "Orders",
        "toColumn": "Order ID",
        "crossFilteringBehavior": "singleDirection"
    },
    {
        "name": uid(),
        "fromTable": "Orders",
        "fromColumn": "Region",
        "toTable": "Users",
        "toColumn": "Region",
        "crossFilteringBehavior": "singleDirection"
    },
    {
        "name": uid(),
        "fromTable": "Orders",
        "fromColumn": "Region",
        "toTable": "Sales",
        "toColumn": "Region",
        "crossFilteringBehavior": "singleDirection"
    },
]


# ── TMSL model schema ─────────────────────────────────────────────────────────

model_schema = {
    "model": {
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "tables": [
            orders_table,
            customers_table,
            products_table,
            returns_table,
            users_table,
            monthly_kpis_table,
            sales_table,
        ],
        "relationships": relationships,
        "annotations": [
            {"name": "PBI_QueryOrder",
             "value": '["Orders","Customers","Products","Returns","Users","Monthly KPIs","Sales"]'},
            {"name": "__PBI_TimeIntelligenceEnabled", "value": "1"},
        ],
        "cultures": [{
            "name": "en-US",
            "linguisticMetadata": {
                "content": {"Version": "1.0.0", "Language": "en-US"},
                "contentType": "json"
            }
        }]
    }
}

schema_json = json.dumps(model_schema, ensure_ascii=False, indent=2)

# ── Report layout (4 pages) ───────────────────────────────────────────────────
# (Re-use the same layout logic as generate_enhanced_pbix.py for consistency)

import sys, importlib.util, os

gen_path = os.path.join(os.path.dirname(__file__), "generate_enhanced_pbix.py")

def make_kpi_card(x, y, w, h, entity, alias, col, agg_func, display_name, tab):
    vname = uuid.uuid4().hex[:20]
    query_name = f"Sum({entity}.{col})" if agg_func == 0 else f"Count({entity}.{col})"
    proj = {
        "config": json.dumps({
            "name": vname,
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "card",
                "projections": {"Values": [{"queryRef": query_name}]},
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                    "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}}, "Function": agg_func}, "Name": query_name, "NativeReferenceName": display_name}]
                },
                "drillFilterOtherVisuals": True
            }
        }),
        "filters": "[]",
        "query": json.dumps({"Commands": [{"SemanticQueryDataShapeCommand": {"Query": {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}], "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}}, "Function": agg_func}, "Name": query_name, "NativeReferenceName": display_name}]}, "Binding": {"Primary": {"Groupings": [{"Projections": [0]}]}, "DataReduction": {"DataVolume": 3, "Primary": {"Top": {}}}, "Version": 1}, "ExecutionMetricsKind": 1}}]}),
        "dataTransforms": json.dumps({"selects": [{"displayName": display_name, "queryName": query_name, "roles": {"Values": True}, "type": {"category": None, "underlyingType": 259}, "expr": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": col}}, "Function": agg_func}}}]}),
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab
    }
    return proj

def make_bar_chart(x, y, w, h, cat_entity, cat_alias, cat_col, val_entity, val_alias, val_col, val_agg, val_display, tab):
    vname = uuid.uuid4().hex[:20]
    cat_qname = f"{cat_entity}.{cat_col}"
    val_qname = f"Sum({val_entity}.{val_col})"
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname,
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "clusteredBarChart",
                "projections": {
                    "Category": [{"queryRef": cat_qname, "active": True}],
                    "Y": [{"queryRef": val_qname}]
                },
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": cat_alias, "Entity": cat_entity, "Type": 0}] if cat_alias == val_alias else [{"Name": cat_alias, "Entity": cat_entity, "Type": 0}, {"Name": val_alias, "Entity": val_entity, "Type": 0}],
                    "Select": [
                        {"Column": {"Expression": {"SourceRef": {"Source": cat_alias}}, "Property": cat_col}, "Name": cat_qname, "NativeReferenceName": cat_col},
                        {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_alias}}, "Property": val_col}}, "Function": val_agg}, "Name": val_qname, "NativeReferenceName": val_display}
                    ],
                    "OrderBy": [{"Direction": 2, "Expression": {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_alias}}, "Property": val_col}}, "Function": val_agg}}}]
                },
                "drillFilterOtherVisuals": True
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }

def make_line_chart(x, y, w, h, cat_entity, cat_alias, cat_col, val_entity, val_alias, val_col, val_agg, val_display, tab):
    vname = uuid.uuid4().hex[:20]
    cat_qname = f"{cat_entity}.{cat_col}"
    val_qname = f"Sum({val_entity}.{val_col})"
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname,
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "lineChart",
                "projections": {
                    "Category": [{"queryRef": cat_qname, "active": True}],
                    "Y": [{"queryRef": val_qname}]
                },
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": cat_alias, "Entity": cat_entity, "Type": 0}] if cat_alias == val_alias else [{"Name": cat_alias, "Entity": cat_entity, "Type": 0}, {"Name": val_alias, "Entity": val_entity, "Type": 0}],
                    "Select": [
                        {"Column": {"Expression": {"SourceRef": {"Source": cat_alias}}, "Property": cat_col}, "Name": cat_qname, "NativeReferenceName": cat_col},
                        {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_alias}}, "Property": val_col}}, "Function": val_agg}, "Name": val_qname, "NativeReferenceName": val_display}
                    ]
                },
                "drillFilterOtherVisuals": True
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }

def make_table_visual(x, y, w, h, selects_info, tab):
    vname = uuid.uuid4().hex[:20]
    froms = {}
    selects = []
    for entity, alias, col, agg in selects_info:
        if alias not in froms:
            froms[alias] = entity
        if agg is None:
            qname = f"{entity}.{col}"
            selects.append({"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}, "Name": qname, "NativeReferenceName": col})
        else:
            qname = f"Sum({entity}.{col})"
            selects.append({"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}}, "Function": agg}, "Name": qname, "NativeReferenceName": f"Sum of {col}"})
    from_list = [{"Name": a, "Entity": e, "Type": 0} for a, e in froms.items()]
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname,
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "tableEx",
                "projections": {"Values": [{"queryRef": s["Name"]} for s in selects]},
                "prototypeQuery": {"Version": 2, "From": from_list, "Select": selects},
                "drillFilterOtherVisuals": True
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


# ── Page 1: Sales KPI Dashboard ───────────────────────────────────────────────
kpi_defs = [
    ("Orders","o","Sales",    0,"Total Sales"),
    ("Orders","o","Profit",   0,"Total Profit"),
    ("Orders","o","Discount", 1,"Avg Discount"),
    ("Orders","o","Order ID", 5,"Total Orders"),
    ("Orders","o","Customer ID",5,"Total Customers"),
    ("Orders","o","Quantity", 0,"Total Quantity"),
]
card_w, card_h = 195, 110
cards = [make_kpi_card(15 + i*(card_w+5), 20, card_w, card_h, e, a, c, f, dn, i*100)
         for i, (e, a, c, f, dn) in enumerate(kpi_defs)]

page1_visuals = cards + [
    make_bar_chart(10, 150, 615, 540, "Orders","o","Region","Orders","o","Sales",0,"Total Sales",700),
    make_line_chart(640, 150, 630, 540, "Orders","o","Order Date","Orders","o","Sales",0,"Sales Trend",800),
]

# ── Page 2: Product Analysis ──────────────────────────────────────────────────
page2_visuals = [
    make_kpi_card(10, 10, 200, 100, "Products","p","Product ID",5,"Total Products",100),
    make_bar_chart(10, 130, 615, 270, "Orders","o","Category","Orders","o","Sales",0,"Sales by Category",200),
    make_bar_chart(640, 130, 630, 270, "Orders","o","Sub-Category","Orders","o","Sales",0,"Sales by Sub-Category",300),
    make_table_visual(10, 415, 1260, 285, [
        ("Products","p","Category",None),
        ("Products","p","Sub-Category",None),
        ("Products","p","Product Name",None),
        ("Orders","o","Sales",0),
    ], 400),
]

# ── Page 3: Customer Analysis ─────────────────────────────────────────────────
page3_visuals = [
    make_kpi_card(10, 10, 200, 100, "Orders","o","Customer ID",5,"Total Customers",100),
    make_kpi_card(220, 10, 200, 100, "Orders","o","Sales",0,"Total Sales",200),
    make_bar_chart(10, 130, 615, 270, "Orders","o","Segment","Orders","o","Sales",0,"Sales by Segment",300),
    make_bar_chart(640, 130, 630, 270, "Orders","o","City","Orders","o","Sales",0,"Sales by City",400),
    make_table_visual(10, 415, 1260, 285, [
        ("Customers","c","Customer ID",None),
        ("Customers","c","Customer Name",None),
        ("Customers","c","Segment",None),
        ("Orders","o","Sales",0),
    ], 500),
]

# ── Page 4: Returns & Performance ────────────────────────────────────────────
page4_visuals = [
    make_kpi_card(10,  10, 200, 100, "Returns","r","Order ID",5,"Total Returns",100),
    make_kpi_card(220, 10, 200, 100, "Orders","o","Order ID",5,"Total Orders",200),
    make_bar_chart(10, 130, 615, 560, "Returns","r","Order ID","Returns","r","Returned",5,"Returns Count",300),
    make_bar_chart(640, 130, 630, 270, "Orders","o","Segment","Orders","o","Profit",0,"Profit by Segment",400),
    make_line_chart(640, 415, 630, 275, "Orders","o","Order Date","Orders","o","Profit",0,"Profit Trend",500),
]

report_sections = [
    {"id": 0, "name": "ReportSection1", "displayName": "Sales KPI Dashboard",
     "ordinal": 0, "visualContainers": page1_visuals, "filters": "[]",
     "config": "{}", "displayOption": 1, "width": 1280, "height": 720},
    {"id": 1, "name": "ReportSection2", "displayName": "Product Analysis",
     "ordinal": 1, "visualContainers": page2_visuals, "filters": "[]",
     "config": "{}", "displayOption": 1, "width": 1280, "height": 720},
    {"id": 2, "name": "ReportSection3", "displayName": "Customer Analysis",
     "ordinal": 2, "visualContainers": page3_visuals, "filters": "[]",
     "config": "{}", "displayOption": 1, "width": 1280, "height": 720},
    {"id": 3, "name": "ReportSection4", "displayName": "Returns & Performance",
     "ordinal": 3, "visualContainers": page4_visuals, "filters": "[]",
     "config": "{}", "displayOption": 1, "width": 1280, "height": 720},
]

report_layout = {
    "id": 0,
    "resourcePackages": [{"resourcePackage": {"name": "SharedResources", "type": 2,
        "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json", "name": "CY23SU11"}], "disabled": False}}],
    "sections": report_sections,
    "config": json.dumps({
        "version": "5.49",
        "themeCollection": {"baseTheme": {"name": "CY23SU11", "version": "5.49", "type": 2}},
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True
        }
    }),
    "layoutOptimization": 0
}

layout_json_str = json.dumps(report_layout, ensure_ascii=False)

# ── Diagram layout (7 tables) ─────────────────────────────────────────────────
table_names = ["Orders","Customers","Products","Returns","Users","Monthly KPIs","Sales"]
diagram = {
    "version": "1.1.0",
    "diagrams": [{
        "ordinal": 0,
        "scrollPosition": {"x": 0, "y": 0},
        "nodes": [
            {"location": {"x": 10  + i*280, "y": 10 + (i % 2)*200},
             "nodeIndex": t,
             "nodeLineageTag": uid(),
             "size": {"height": 224, "width": 234},
             "zIndex": 0}
            for i, t in enumerate(table_names)
        ],
        "name": "All tables",
        "zoomValue": 100,
        "pinKeyFieldsToTop": False,
        "showExtraHeaderInfo": False,
        "hideKeyFieldsWhenCollapsed": False,
        "tablesLocked": False
    }],
    "selectedDiagram": "All tables",
    "defaultDiagram": "All tables"
}
diagram_json_str = json.dumps(diagram, ensure_ascii=False)

metadata = json.dumps({"Version": 5, "AutoCreatedRelationships": [], "CreatedFrom": "Cloud", "CreatedFromRelease": "2023.11"}, ensure_ascii=False)
settings_obj = json.dumps({"Version": 4, "ReportSettings": {}, "QueriesSettings": {"TypeDetectionEnabled": True, "RelationshipImportEnabled": True, "Version": "2.123.424.0"}}, ensure_ascii=False)

content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Override PartName="/DataModelSchema" ContentType="application/json" />
  <Override PartName="/Report/Layout" ContentType="application/json" />
</Types>"""

theme_path = "/tmp/pbix_extract/extracted/Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
with open(theme_path, "rb") as f:
    theme_bytes = f.read()

# ── Write .pbit ───────────────────────────────────────────────────────────────
out_path = os.path.join(os.path.dirname(__file__), "make1_with_relationships.pbit")

with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("Version", "3.0")
    z.writestr("[Content_Types].xml", content_types.encode("utf-8"))
    z.writestr("DataModelSchema", encode16(schema_json))
    z.writestr("DiagramLayout", encode16(diagram_json_str))
    z.writestr("Report/Layout", encode16(layout_json_str))
    z.writestr("Settings", encode16(settings_obj))
    z.writestr("Metadata", encode16(metadata))
    z.writestr("SecurityBindings", b"")
    z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json", theme_bytes)

size = os.path.getsize(out_path)
print(f"Written: {out_path}  ({size:,} bytes)")

# ── Verify ────────────────────────────────────────────────────────────────────
with zipfile.ZipFile(out_path) as z:
    print("\nContents:")
    for info in z.infolist():
        print(f"  {info.filename}: {info.file_size:,} bytes")

    schema_raw = z.read("DataModelSchema").decode("utf-16-le")
    loaded = json.loads(schema_raw)
    tables = loaded["model"]["tables"]
    rels   = loaded["model"]["relationships"]
    measures_count = sum(len(t.get("measures", [])) for t in tables)
    print(f"\nTables    : {len(tables)}  ({', '.join(t['name'] for t in tables)})")
    print(f"Relations : {len(rels)}")
    print(f"Measures  : {measures_count}")
    for r in rels:
        print(f"  {r['fromTable']}[{r['fromColumn']}] → {r['toTable']}[{r['toColumn']}]")

print("\nDone.")

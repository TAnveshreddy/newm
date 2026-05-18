"""
Generates make1_with_relationships.pbit — Power BI Template with
7 tables, 5 relationships, and 13 KPI DAX measures.
Fixed: DataModelSchema is UTF-8, compatibilityLevel=1567, expressions are string arrays.
"""

import json, zipfile, uuid, os

def uid():
    return uuid.uuid4().hex

# DataModelSchema must be UTF-8 for .pbit files
def encode_schema(text):
    return text.encode("utf-8")

# All other metadata files use UTF-16 LE
def encode16(text):
    return text.encode("utf-16-le")

# ── Sample data rows ──────────────────────────────────────────────────────────

ORDERS_ROWS = [
    ["CA-2019-152156","CG-12520","FUR-BO-10001798","2019-11-08","Second Class","Consumer","Henderson","Kentucky","South","Furniture","Bookcases",261.96,2,0.0,41.91],
    ["CA-2019-138688","DV-13045","FUR-CH-10000454","2019-06-12","Second Class","Corporate","Henderson","Kentucky","South","Furniture","Chairs",731.94,3,0.0,219.58],
    ["CA-2019-138688","DV-13045","OFF-LA-10000240","2019-06-12","Second Class","Corporate","Henderson","Kentucky","South","Office Supplies","Labels",14.62,2,0.0,6.87],
    ["US-2019-108966","SO-20335","OFF-ST-10000760","2019-10-11","Standard Class","Consumer","Fort Lauderdale","Florida","South","Office Supplies","Storage",957.58,5,0.45,-383.03],
    ["CA-2019-115812","BH-11710","FUR-FU-10001487","2019-06-09","Standard Class","Consumer","Los Angeles","California","West","Furniture","Furnishings",48.86,7,0.0,14.17],
    ["CA-2019-115812","BH-11710","TEC-PH-10002275","2019-06-09","Standard Class","Consumer","Los Angeles","California","West","Technology","Phones",907.15,6,0.2,90.72],
    ["CA-2020-167164","EH-13945","FUR-BO-10003714","2020-05-13","First Class","Consumer","Seattle","Washington","West","Furniture","Bookcases",77.88,3,0.2,-13.38],
    ["CA-2020-143336","AO-10660","TEC-PH-10001530","2020-08-27","Standard Class","Consumer","Houston","Texas","Central","Technology","Phones",1097.54,7,0.0,164.63],
    ["CA-2021-105893","MB-18085","OFF-ST-10004186","2021-03-14","Standard Class","Home Office","New York City","New York","East","Office Supplies","Storage",665.88,6,0.2,-125.44],
    ["CA-2021-118977","KL-16645","TEC-AC-10002167","2021-11-22","Second Class","Corporate","Philadelphia","Pennsylvania","East","Technology","Accessories",55.98,3,0.0,20.98],
    ["CA-2022-100391","SC-20380","FUR-CH-10000454","2022-01-10","Standard Class","Consumer","Charlotte","North Carolina","South","Furniture","Chairs",954.64,4,0.0,286.39],
    ["CA-2022-167199","EM-13885","OFF-BI-10003910","2022-09-06","Second Class","Corporate","Dallas","Texas","Central","Office Supplies","Binders",412.02,5,0.2,-49.44],
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
    ["OFF-ST-10000760","Office Supplies","Storage","Eldon Fold N Roll Cart System"],
    ["FUR-FU-10001487","Furniture","Furnishings","Eldon Expressions Desk Accessories"],
    ["TEC-PH-10002275","Technology","Phones","Motorola Smart Phone"],
    ["FUR-BO-10003714","Furniture","Bookcases","Sauder Classic Bookcase"],
    ["TEC-PH-10001530","Technology","Phones","Samsung Convoy 3"],
    ["OFF-ST-10004186","Office Supplies","Storage","Fellowes Super Stor Drawer"],
    ["TEC-AC-10002167","Technology","Accessories","Logitech Wireless Keyboard"],
    ["OFF-BI-10003910","Office Supplies","Binders","GBC Ibimaster 500"],
]

RETURNS_ROWS = [
    ["Yes","US-2019-108966"],
    ["Yes","CA-2020-167164"],
    ["Yes","CA-2021-105893"],
]

USERS_ROWS = [
    ["Anna Andreadi","Central"],
    ["Chuck Magee","South"],
    ["Kelly Williams","East"],
    ["Matt Collister","West"],
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
    ["South","Office Supplies",2019,972.2,-376.16],
    ["West","Furniture",2019,956.01,104.89],
    ["West","Technology",2019,907.15,90.72],
    ["West","Furniture",2020,77.88,-13.38],
    ["Central","Technology",2020,1097.54,164.63],
    ["East","Office Supplies",2021,665.88,-125.44],
    ["East","Technology",2021,55.98,20.98],
    ["South","Furniture",2022,954.64,286.39],
    ["Central","Office Supplies",2022,412.02,-49.44],
]

# ── Build DATATABLE() DAX expressions ─────────────────────────────────────────

def fmt_val(val, typ):
    if val is None:
        return "BLANK()"
    if typ == "string":
        return '"' + str(val).replace('"', '""') + '"'
    if typ == "date":
        y, m, d = str(val).split("-")
        return f"DATE({y},{int(m)},{int(d)})"
    return str(val)

def build_datatable(col_defs, rows):
    """Returns expression as a list of strings (one per line) — required by TMSL."""
    type_map = {"string": "STRING", "date": "DATETIME", "double": "DOUBLE", "int64": "INTEGER"}
    header = "DATATABLE("
    col_parts = [f'"{name}", {type_map[t]}' for name, t in col_defs]
    col_line  = "    " + ", ".join(col_parts) + ","
    lines = [header, col_line, "    {"]
    for row in rows:
        vals = ", ".join(fmt_val(v, col_defs[i][1]) for i, v in enumerate(row))
        lines.append(f"        {{{vals}}},")
    # Remove trailing comma from last row
    lines[-1] = lines[-1].rstrip(",")
    lines.append("    }")
    lines.append(")")
    return lines

ORDERS_EXPR = build_datatable([
    ("Order ID","string"),("Customer ID","string"),("Product ID","string"),
    ("Order Date","date"),("Ship Mode","string"),("Segment","string"),
    ("City","string"),("State","string"),("Region","string"),
    ("Category","string"),("Sub-Category","string"),
    ("Sales","double"),("Quantity","int64"),("Discount","double"),("Profit","double"),
], ORDERS_ROWS)

CUSTOMERS_EXPR = build_datatable([
    ("Customer ID","string"),("Customer Name","string"),("Segment","string"),
], CUSTOMERS_ROWS)

PRODUCTS_EXPR = build_datatable([
    ("Product ID","string"),("Category","string"),
    ("Sub-Category","string"),("Product Name","string"),
], PRODUCTS_ROWS)

RETURNS_EXPR = build_datatable([
    ("Returned","string"),("Order ID","string"),
], RETURNS_ROWS)

USERS_EXPR = build_datatable([
    ("Person","string"),("Region","string"),
], USERS_ROWS)

MONTHLY_KPIS_EXPR = build_datatable([
    ("Month","date"),("Target Sales","double"),
    ("Target Profit","double"),("Target Orders","int64"),
], MONTHLY_KPIS_ROWS)

SALES_EXPR = build_datatable([
    ("Region","string"),("Category","string"),("Year","int64"),
    ("Sales","double"),("Profit","double"),
], SALES_ROWS)

# ── TMSL helpers ───────────────────────────────────────────────────────────────

def make_col(name, dtype, summarize="none"):
    return {
        "name": name,
        "dataType": dtype,
        "lineageTag": uid(),
        "summarizeBy": summarize,
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    }

def make_measure(name, expr, fmt=None):
    m = {"name": name, "expression": expr, "lineageTag": uid()}
    if fmt:
        m["formatString"] = fmt
    m["annotations"] = [{"name": "PBI_FormatHint", "value": '{"isGeneralNumber":true}'}]
    return m

def make_table(name, cols, measures, expr_lines):
    return {
        "name": name,
        "lineageTag": uid(),
        "columns": cols,
        "measures": measures,
        "partitions": [{
            "name": name,
            "mode": "import",
            "source": {"type": "calculated", "expression": expr_lines}
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
    }

# ── Tables ────────────────────────────────────────────────────────────────────

orders_table = make_table("Orders", [
    make_col("Order ID",     "string"),
    make_col("Customer ID",  "string"),
    make_col("Product ID",   "string"),
    make_col("Order Date",   "dateTime"),
    make_col("Ship Mode",    "string"),
    make_col("Segment",      "string"),
    make_col("City",         "string"),
    make_col("State",        "string"),
    make_col("Region",       "string"),
    make_col("Category",     "string"),
    make_col("Sub-Category", "string"),
    make_col("Sales",        "double",  "sum"),
    make_col("Quantity",     "int64",   "sum"),
    make_col("Discount",     "double",  "average"),
    make_col("Profit",       "double",  "sum"),
], [
    make_measure("Total Sales",         'SUM(Orders[Sales])',                             '"$"#,##0.00'),
    make_measure("Total Profit",        'SUM(Orders[Profit])',                            '"$"#,##0.00'),
    make_measure("Profit Margin %",     'DIVIDE([Total Profit],[Total Sales],0)',          '0.00%'),
    make_measure("Total Orders",        'DISTINCTCOUNT(Orders[Order ID])',                '#,##0'),
    make_measure("Total Customers",     'DISTINCTCOUNT(Orders[Customer ID])',             '#,##0'),
    make_measure("Avg Order Value",     'DIVIDE([Total Sales],[Total Orders],0)',         '"$"#,##0.00'),
    make_measure("Total Quantity",      'SUM(Orders[Quantity])',                          '#,##0'),
    make_measure("Avg Discount",        'AVERAGE(Orders[Discount])',                      '0.00%'),
    make_measure("Sales YoY %",
        'VAR CY=CALCULATE([Total Sales],YEAR(Orders[Order Date])=YEAR(TODAY()))\n'
        'VAR PY=CALCULATE([Total Sales],YEAR(Orders[Order Date])=YEAR(TODAY())-1)\n'
        'RETURN DIVIDE(CY-PY,PY,0)',                                                      '0.00%'),
    make_measure("Target Achievement %",
        "DIVIDE([Total Sales],SUM('Monthly KPIs'[Target Sales]),0)",                      '0.00%'),
], ORDERS_EXPR)

customers_table = make_table("Customers", [
    make_col("Customer ID",   "string"),
    make_col("Customer Name", "string"),
    make_col("Segment",       "string"),
], [], CUSTOMERS_EXPR)

products_table = make_table("Products", [
    make_col("Product ID",   "string"),
    make_col("Category",     "string"),
    make_col("Sub-Category", "string"),
    make_col("Product Name", "string"),
], [
    make_measure("Total Products", "DISTINCTCOUNT(Products[Product ID])", "#,##0"),
], PRODUCTS_EXPR)

returns_table = make_table("Returns", [
    make_col("Returned", "string"),
    make_col("Order ID", "string"),
], [
    make_measure("Total Returns", "COUNTROWS(Returns)",                         "#,##0"),
    make_measure("Return Rate %", "DIVIDE([Total Returns],[Total Orders],0)",   "0.00%"),
], RETURNS_EXPR)

users_table = make_table("Users", [
    make_col("Person", "string"),
    make_col("Region", "string"),
], [], USERS_EXPR)

monthly_kpis_table = make_table("Monthly KPIs", [
    make_col("Month",         "dateTime"),
    make_col("Target Sales",  "double", "sum"),
    make_col("Target Profit", "double", "sum"),
    make_col("Target Orders", "int64",  "sum"),
], [], MONTHLY_KPIS_EXPR)

sales_table = make_table("Sales", [
    make_col("Region",   "string"),
    make_col("Category", "string"),
    make_col("Year",     "int64"),
    make_col("Sales",    "double", "sum"),
    make_col("Profit",   "double", "sum"),
], [], SALES_EXPR)

# ── Relationships ──────────────────────────────────────────────────────────────

relationships = [
    {"name": uid(), "fromTable": "Orders",  "fromColumn": "Customer ID",
     "toTable": "Customers",    "toColumn": "Customer ID"},
    {"name": uid(), "fromTable": "Orders",  "fromColumn": "Product ID",
     "toTable": "Products",     "toColumn": "Product ID"},
    {"name": uid(), "fromTable": "Returns", "fromColumn": "Order ID",
     "toTable": "Orders",       "toColumn": "Order ID"},
    {"name": uid(), "fromTable": "Orders",  "fromColumn": "Region",
     "toTable": "Users",        "toColumn": "Region"},
    {"name": uid(), "fromTable": "Orders",  "fromColumn": "Region",
     "toTable": "Sales",        "toColumn": "Region"},
]

# ── Full TMSL model ────────────────────────────────────────────────────────────

model_schema = {
    "model": {
        "compatibilityLevel": 1567,
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "tables": [
            orders_table, customers_table, products_table,
            returns_table, users_table, monthly_kpis_table, sales_table,
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

# ── Report layout — 4 pages ───────────────────────────────────────────────────

def vname():
    return uuid.uuid4().hex[:20]

def card_vc(x, y, w, h, entity, alias, col, agg_fn, label, tab):
    qn = f"{'Sum' if agg_fn==0 else 'Count'}({entity}.{col})"
    cfg = {"name": vname(),
           "layouts": [{"id": 0, "position": {"x": x,"y": y,"z": tab,"width": w,"height": h,"tabOrder": tab}}],
           "singleVisual": {
               "visualType": "card",
               "projections": {"Values": [{"queryRef": qn}]},
               "prototypeQuery": {
                   "Version": 2,
                   "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                   "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}}, "Function": agg_fn}, "Name": qn, "NativeReferenceName": label}]
               },
               "drillFilterOtherVisuals": True
           }}
    return {"x": x,"y": y,"z": tab,"width": w,"height": h,"tabOrder": tab,
            "filters": "[]", "config": json.dumps(cfg), "query": "{}", "dataTransforms": "{}"}

def bar_vc(x, y, w, h, ce, ca, cc, ve, va, vc_, agg_fn, label, tab, vtype="clusteredBarChart"):
    cqn = f"{ce}.{cc}"
    vqn = f"Sum({ve}.{vc_})"
    froms = [{"Name": ca, "Entity": ce, "Type": 0}]
    if va != ca:
        froms.append({"Name": va, "Entity": ve, "Type": 0})
    cfg = {"name": vname(),
           "layouts": [{"id": 0, "position": {"x": x,"y": y,"z": tab,"width": w,"height": h,"tabOrder": tab}}],
           "singleVisual": {
               "visualType": vtype,
               "projections": {"Category": [{"queryRef": cqn,"active": True}], "Y": [{"queryRef": vqn}]},
               "prototypeQuery": {
                   "Version": 2, "From": froms,
                   "Select": [
                       {"Column": {"Expression": {"SourceRef": {"Source": ca}}, "Property": cc}, "Name": cqn, "NativeReferenceName": cc},
                       {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": va}}, "Property": vc_}}, "Function": agg_fn}, "Name": vqn, "NativeReferenceName": label}
                   ]
               },
               "drillFilterOtherVisuals": True
           }}
    return {"x": x,"y": y,"z": tab,"width": w,"height": h,"tabOrder": tab,
            "filters": "[]", "config": json.dumps(cfg), "query": "{}", "dataTransforms": "{}"}

def line_vc(x, y, w, h, ce, ca, cc, ve, va, vc_, agg_fn, label, tab):
    return bar_vc(x, y, w, h, ce, ca, cc, ve, va, vc_, agg_fn, label, tab, vtype="lineChart")

def table_vc(x, y, w, h, selects_info, tab):
    froms = {}
    sels = []
    for entity, alias, col, agg in selects_info:
        if alias not in froms:
            froms[alias] = entity
        if agg is None:
            qn = f"{entity}.{col}"
            sels.append({"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}, "Name": qn, "NativeReferenceName": col})
        else:
            qn = f"Sum({entity}.{col})"
            sels.append({"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}}, "Function": agg}, "Name": qn, "NativeReferenceName": f"Sum of {col}"})
    from_list = [{"Name": a, "Entity": e, "Type": 0} for a, e in froms.items()]
    cfg = {"name": vname(),
           "layouts": [{"id": 0, "position": {"x": x,"y": y,"z": tab,"width": w,"height": h,"tabOrder": tab}}],
           "singleVisual": {
               "visualType": "tableEx",
               "projections": {"Values": [{"queryRef": s["Name"]} for s in sels]},
               "prototypeQuery": {"Version": 2, "From": from_list, "Select": sels},
               "drillFilterOtherVisuals": True
           }}
    return {"x": x,"y": y,"z": tab,"width": w,"height": h,"tabOrder": tab,
            "filters": "[]", "config": json.dumps(cfg), "query": "{}", "dataTransforms": "{}"}

# Page 1 — Sales KPI Dashboard
CW, CH = 193, 108
kpis_p1 = [
    ("Orders","o","Sales",     0, "Total Sales"),
    ("Orders","o","Profit",    0, "Total Profit"),
    ("Orders","o","Quantity",  0, "Total Quantity"),
    ("Orders","o","Order ID",  5, "Total Orders"),
    ("Orders","o","Customer ID",5,"Total Customers"),
    ("Orders","o","Discount",  1, "Avg Discount"),
]
p1 = ([card_vc(15+i*(CW+8), 15, CW, CH, e,a,c,f,l,i*100) for i,(e,a,c,f,l) in enumerate(kpis_p1)] + [
    bar_vc(10,145,615,555, "Orders","o","Region","Orders","o","Sales",0,"Sales by Region",700),
    line_vc(640,145,630,555,"Orders","o","Order Date","Orders","o","Sales",0,"Sales Trend",800),
])

# Page 2 — Product Analysis
p2 = [
    card_vc(10,10,200,100,"Products","p","Product ID",5,"Total Products",100),
    bar_vc(10,130,615,270,"Orders","o","Category","Orders","o","Sales",0,"Sales by Category",200),
    bar_vc(640,130,630,270,"Orders","o","Sub-Category","Orders","o","Sales",0,"Sub-Category Sales",300),
    table_vc(10,415,1260,285,[("Products","p","Category",None),("Products","p","Sub-Category",None),("Products","p","Product Name",None),("Orders","o","Sales",0)],400),
]

# Page 3 — Customer Analysis
p3 = [
    card_vc(10,10,200,100,"Orders","o","Customer ID",5,"Total Customers",100),
    card_vc(220,10,200,100,"Orders","o","Sales",0,"Total Sales",200),
    bar_vc(10,130,615,270,"Orders","o","Segment","Orders","o","Sales",0,"Sales by Segment",300),
    bar_vc(640,130,630,270,"Orders","o","City","Orders","o","Sales",0,"Orders by City",400),
    table_vc(10,415,1260,285,[("Customers","c","Customer ID",None),("Customers","c","Customer Name",None),("Customers","c","Segment",None),("Orders","o","Sales",0)],500),
]

# Page 4 — Returns & Performance
p4 = [
    card_vc(10,10,200,100,"Returns","r","Order ID",5,"Total Returns",100),
    card_vc(220,10,200,100,"Orders","o","Order ID",5,"Total Orders",200),
    bar_vc(10,130,615,555,"Returns","r","Returned","Returns","r","Order ID",5,"Returns",300),
    bar_vc(640,130,630,270,"Orders","o","Segment","Orders","o","Profit",0,"Profit by Segment",400),
    line_vc(640,415,630,270,"Orders","o","Order Date","Orders","o","Profit",0,"Profit Trend",500),
]

def make_section(sid, name, display, ordinal, visuals):
    return {"id": sid, "name": name, "displayName": display, "ordinal": ordinal,
            "visualContainers": visuals, "filters": "[]", "config": "{}",
            "displayOption": 1, "width": 1280, "height": 720}

report_layout = {
    "id": 0,
    "resourcePackages": [{"resourcePackage": {"name": "SharedResources", "type": 2,
        "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json", "name": "CY23SU11"}], "disabled": False}}],
    "sections": [
        make_section(0,"ReportSection1","Sales KPI Dashboard",0,p1),
        make_section(1,"ReportSection2","Product Analysis",1,p2),
        make_section(2,"ReportSection3","Customer Analysis",2,p3),
        make_section(3,"ReportSection4","Returns & Performance",3,p4),
    ],
    "config": json.dumps({"version":"5.49","themeCollection":{"baseTheme":{"name":"CY23SU11","version":"5.49","type":2}},"activeSectionIndex":0,"defaultDrillFilterOtherVisuals":True}),
    "layoutOptimization": 0
}
layout_str = json.dumps(report_layout, ensure_ascii=False)

# ── Diagram layout ────────────────────────────────────────────────────────────
tables_names = ["Orders","Customers","Products","Returns","Users","Monthly KPIs","Sales"]
diagram = {
    "version": "1.1.0",
    "diagrams": [{"ordinal": 0, "scrollPosition": {"x":0,"y":0},
        "nodes": [{"location":{"x":10+i*270,"y":10+(i%2)*200},"nodeIndex":t,"nodeLineageTag":uid(),"size":{"height":224,"width":234},"zIndex":0} for i,t in enumerate(tables_names)],
        "name":"All tables","zoomValue":100,"pinKeyFieldsToTop":False,"showExtraHeaderInfo":False,"hideKeyFieldsWhenCollapsed":False,"tablesLocked":False}],
    "selectedDiagram":"All tables","defaultDiagram":"All tables"
}

# ── Content-Types — must list all parts ───────────────────────────────────────
content_types = """<?xml version="1.0" encoding="utf-8"?>
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

metadata = json.dumps({"Version":5,"AutoCreatedRelationships":[],"CreatedFrom":"Cloud","CreatedFromRelease":"2023.11"})
settings  = json.dumps({"Version":4,"ReportSettings":{},"QueriesSettings":{"TypeDetectionEnabled":True,"RelationshipImportEnabled":True,"Version":"2.123.424.0"}})

theme_path = "/tmp/pbix_extract/extracted/Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
with open(theme_path,"rb") as f:
    theme_bytes = f.read()

# ── Write .pbit ───────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make1_with_relationships.pbit")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("Version",             "3.0")
    z.writestr("[Content_Types].xml", content_types.encode("utf-8"))
    z.writestr("DataModelSchema",     encode_schema(schema_json))   # UTF-8 !
    z.writestr("DiagramLayout",       encode16(json.dumps(diagram, ensure_ascii=False)))
    z.writestr("Report/Layout",       encode16(layout_str))
    z.writestr("Settings",            encode16(settings))
    z.writestr("Metadata",            encode16(metadata))
    z.writestr("SecurityBindings",    b"")
    z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json", theme_bytes)

size = os.path.getsize(out)
print(f"Written: {out}  ({size:,} bytes)")

# ── Verify ────────────────────────────────────────────────────────────────────
with zipfile.ZipFile(out) as z:
    print("\nContents:")
    for info in z.infolist():
        print(f"  {info.filename}: {info.file_size:,} bytes")
    schema_raw = z.read("DataModelSchema")
    print(f"\nDataModelSchema encoding: first 2 bytes = {schema_raw[:2].hex()}  (should be 7b 0a for UTF-8 '{{\\n')")
    loaded = json.loads(schema_raw.decode("utf-8"))
    m = loaded["model"]
    print(f"compatibilityLevel : {m.get('compatibilityLevel')}")
    print(f"Tables ({len(m['tables'])}): {[t['name'] for t in m['tables']]}")
    print(f"Relationships ({len(m['relationships'])}):")
    for r in m["relationships"]:
        print(f"  {r['fromTable']}[{r['fromColumn']}]  →  {r['toTable']}[{r['toColumn']}]")
    measures = sum(len(t.get("measures",[])) for t in m["tables"])
    print(f"Total measures: {measures}")
print("\nDone.")

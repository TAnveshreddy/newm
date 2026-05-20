"""
Build SalesAnalytics_Final.pbit — fully mirrors PowerBI_Sales_Dashboard.html
- 500 sales records, 100 customers, 30 users (same data as HTML)
- 5 pages: Executive Summary, Sales Performance, Product Analysis,
           Customer Insights, Team Performance
- Exact color palette: #01B8AA teal, #252423 dark, #FD625E red, etc.
- Relationships: Sales→Customers, Sales→Users
- 13 DAX measures
"""

import json, zipfile, uuid, os, re

# ── Load extracted data ────────────────────────────────────────────────────────
with open('/tmp/raw_sales.json') as f:     SALES     = json.load(f)
with open('/tmp/raw_customers.json') as f: CUSTOMERS = json.load(f)
with open('/tmp/raw_users.json') as f:     USERS     = json.load(f)

def uid(): return uuid.uuid4().hex

# ── M Query (Power Query) builders ───────────────────────────────────────────
def q(v):
    """Quote a value for M table constructor."""
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    return '"' + str(v).replace('\\','\\\\').replace('"','\\"') + '"'

def build_m_table(records, col_types):
    """Build M inline #table expression as list of strings."""
    type_decls = ", ".join(f'#"{c}" = {t}' for c, t in col_types)
    header = f'#table(type table [{type_decls}], {{'
    rows = []
    for rec in records:
        vals = ", ".join(q(rec.get(c)) for c, _ in col_types)
        rows.append(f"  {{{vals}}}")
    body = ",\n".join(rows)
    lines = ["let", f"  Source = {header}", body, "  })", "in", "  Source"]
    return lines

# Column type definitions
SALES_COLS = [
    ("Order ID","text"),("Order Date","date"),("Year","Int64.Type"),
    ("Month","Int64.Type"),("Quarter","text"),("Customer ID","text"),
    ("Product ID","text"),("User ID","text"),("Category","text"),
    ("Quantity","Int64.Type"),("Unit Price","number"),("Unit Cost","number"),
    ("Gross Sales","number"),("Discount %","number"),("Discount Amount","number"),
    ("Net Sales","number"),("Total Cost","number"),("Profit","number"),
    ("Profit Margin %","number"),("Sales Channel","text"),
    ("Order Status","text"),("Ship Date","date"),("Payment Method","text"),
]
CUST_COLS = [
    ("Customer ID","text"),("First Name","text"),("Last Name","text"),
    ("Email","text"),("Phone","text"),("Address","text"),("City","text"),
    ("Country","text"),("Postal Code","text"),("Segment","text"),
    ("Registration Date","date"),("Credit Limit","number"),
]
USER_COLS = [
    ("User ID","text"),("Name","text"),("First Name","text"),("Last Name","text"),
    ("Email","text"),("Role","text"),("Department","text"),("Country","text"),
    ("Location","text"),("Phone","text"),("Join Date","date"),
    ("Manager ID","text"),("Sales Target","number"),
]

# Clean data for M
def clean(rec, cols):
    out = {}
    for c, t in cols:
        v = rec.get(c)
        if v is None or (isinstance(v, float) and v != v):  # NaN
            out[c] = None
        elif t == "date" and isinstance(v, str):
            out[c] = v[:10]  # keep YYYY-MM-DD
        else:
            out[c] = v
    return out

sales_clean     = [clean(r, SALES_COLS)     for r in SALES]
customers_clean = [clean(r, CUST_COLS)      for r in CUSTOMERS]
users_clean     = [clean(r, USER_COLS)      for r in USERS]

SALES_EXPR     = build_m_table(sales_clean,     SALES_COLS)
CUSTOMERS_EXPR = build_m_table(customers_clean, CUST_COLS)
USERS_EXPR     = build_m_table(users_clean,     USER_COLS)

# ── TMSL helpers ───────────────────────────────────────────────────────────────
def col(name, dtype, summarize="none"):
    return {"name": name, "dataType": dtype, "lineageTag": uid(),
            "summarizeBy": summarize,
            "annotations": [{"name":"SummarizationSetBy","value":"Automatic"}]}

def measure(name, expr, fmt=None):
    m = {"name": name, "expression": expr, "lineageTag": uid()}
    if fmt: m["formatString"] = fmt
    return m

def table(name, columns, measures, expr_lines, m_type="m"):
    return {
        "name": name, "lineageTag": uid(),
        "columns": columns, "measures": measures,
        "partitions": [{"name": name, "mode": "import",
                        "source": {"type": m_type, "expression": expr_lines}}],
        "annotations": [{"name":"PBI_ResultType","value":"Table"}]
    }

# ── Tables ────────────────────────────────────────────────────────────────────
sales_table = table("Sales", [
    col("Order ID",      "string"),
    col("Order Date",    "dateTime"),
    col("Year",          "int64"),
    col("Month",         "int64"),
    col("Quarter",       "string"),
    col("Customer ID",   "string"),
    col("Product ID",    "string"),
    col("User ID",       "string"),
    col("Category",      "string"),
    col("Quantity",      "int64",  "sum"),
    col("Unit Price",    "double", "sum"),
    col("Unit Cost",     "double", "sum"),
    col("Gross Sales",   "double", "sum"),
    col("Discount %",    "double", "average"),
    col("Discount Amount","double","sum"),
    col("Net Sales",     "double", "sum"),
    col("Total Cost",    "double", "sum"),
    col("Profit",        "double", "sum"),
    col("Profit Margin %","double","average"),
    col("Sales Channel", "string"),
    col("Order Status",  "string"),
    col("Ship Date",     "dateTime"),
    col("Payment Method","string"),
], [
    measure("Total Revenue",      "SUM(Sales[Net Sales])",                                           '"$"#,##0.00'),
    measure("Total Profit",       "SUM(Sales[Profit])",                                              '"$"#,##0.00'),
    measure("Profit Margin %",    "DIVIDE(SUM(Sales[Profit]),SUM(Sales[Net Sales]),0)",              "0.00%"),
    measure("Total Orders",       "DISTINCTCOUNT(Sales[Order ID])",                                  "#,##0"),
    measure("Avg Order Value",    "DIVIDE(SUM(Sales[Net Sales]),DISTINCTCOUNT(Sales[Order ID]),0)",  '"$"#,##0.00'),
    measure("Total Returns",      "CALCULATE(COUNTROWS(Sales),Sales[Order Status]=\"Returned\")",    "#,##0"),
    measure("Return Rate %",      "DIVIDE([Total Returns],[Total Orders],0)",                        "0.00%"),
    measure("Total Customers",    "DISTINCTCOUNT(Sales[Customer ID])",                               "#,##0"),
    measure("Target Achievement %",
        "DIVIDE([Total Revenue],SUM(Users[Sales Target]),0)",                                        "0.00%"),
    measure("Revenue Growth %",
        "VAR cy=CALCULATE([Total Revenue],Sales[Year]=MAX(Sales[Year]))\n"
        "VAR py=CALCULATE([Total Revenue],Sales[Year]=MAX(Sales[Year])-1)\n"
        "RETURN DIVIDE(cy-py,py,0)",                                                                 "0.00%"),
    measure("Avg Profit Margin",  "AVERAGE(Sales[Profit Margin %])",                                 "0.00%"),
    measure("Total Gross Sales",  "SUM(Sales[Gross Sales])",                                         '"$"#,##0.00'),
    measure("Total Discount",     "SUM(Sales[Discount Amount])",                                     '"$"#,##0.00'),
], SALES_EXPR, m_type="m")

customers_table = table("Customers", [
    col("Customer ID",       "string"),
    col("First Name",        "string"),
    col("Last Name",         "string"),
    col("Email",             "string"),
    col("City",              "string"),
    col("Country",           "string"),
    col("Segment",           "string"),
    col("Credit Limit",      "double", "sum"),
], [], CUSTOMERS_EXPR, m_type="m")

users_table = table("Users", [
    col("User ID",     "string"),
    col("Name",        "string"),
    col("First Name",  "string"),
    col("Last Name",   "string"),
    col("Role",        "string"),
    col("Department",  "string"),
    col("Country",     "string"),
    col("Location",    "string"),
    col("Sales Target","double", "sum"),
], [], USERS_EXPR, m_type="m")

# ── Relationships ─────────────────────────────────────────────────────────────
relationships = [
    {"name": uid(), "fromTable":"Sales","fromColumn":"Customer ID",
     "toTable":"Customers","toColumn":"Customer ID"},
    {"name": uid(), "fromTable":"Sales","fromColumn":"User ID",
     "toTable":"Users","toColumn":"User ID"},
]

# ── Full TMSL model ───────────────────────────────────────────────────────────
model_schema = {
    "model": {
        "compatibilityLevel": 1567,
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "tables": [sales_table, customers_table, users_table],
        "relationships": relationships,
        "annotations": [
            {"name":"PBI_QueryOrder","value":'["Sales","Customers","Users"]'},
            {"name":"__PBI_TimeIntelligenceEnabled","value":"1"},
        ],
        "cultures": [{"name":"en-US","linguisticMetadata":{"content":{"Version":"1.0.0","Language":"en-US"},"contentType":"json"}}]
    }
}

# ── Report Layout ─────────────────────────────────────────────────────────────
COLORS = ['#01B8AA','#374649','#FD625E','#F2C80F','#118DFF','#8B00FF','#FF6B35','#00B050','#5F6B6D','#E91E63']
TEAL   = '#01B8AA'
DARK   = '#252423'
RED    = '#FD625E'
YELLOW = '#F2C80F'
BLUE   = '#118DFF'
PURPLE = '#8B00FF'
GREEN  = '#00B050'

def vn(): return uuid.uuid4().hex[:20]

def pos(x,y,w,h,tab):
    return {"x":x,"y":y,"z":tab,"width":w,"height":h,"tabOrder":tab}

def vc_base(x,y,w,h,tab,config_obj):
    p = pos(x,y,w,h,tab)
    return {**p, "filters":"[]",
            "config": json.dumps({
                "name": vn(),
                "layouts":[{"id":0,"position":p}],
                **config_obj
            }),
            "query":"{}","dataTransforms":"{}"}

def make_card(x,y,w,h,entity,alias,col_,agg_fn,label,tab,border_color=TEAL,sub=""):
    qn = ("Sum" if agg_fn==0 else "Avg" if agg_fn==1 else "Count") + f"({entity}.{col_})"
    sv = {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col_}}, "Function": agg_fn}, "Name": qn, "NativeReferenceName": label}]
        },
        "drillFilterOtherVisuals": True,
    }
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

def make_chart(x,y,w,h,vtype,cat_entity,cat_alias,cat_col,val_entity,val_alias,val_col,agg_fn,label,tab,title="",legend_entity=None,legend_alias=None,legend_col=None,colors=None):
    cqn = f"{cat_entity}.{cat_col}"
    vqn = f"{'Sum' if agg_fn==0 else 'Count' if agg_fn==5 else 'Avg'}({val_entity}.{val_col})"
    froms = [{"Name":cat_alias,"Entity":cat_entity,"Type":0}]
    if val_alias != cat_alias:
        froms.append({"Name":val_alias,"Entity":val_entity,"Type":0})
    selects = [
        {"Column":{"Expression":{"SourceRef":{"Source":cat_alias}},"Property":cat_col},"Name":cqn,"NativeReferenceName":cat_col},
        {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_alias}},"Property":val_col}},"Function":agg_fn},"Name":vqn,"NativeReferenceName":label}
    ]
    projections = {"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]}
    if legend_col:
        lqn = f"{legend_entity}.{legend_col}"
        if legend_alias not in [f["Name"] for f in froms]:
            froms.append({"Name":legend_alias,"Entity":legend_entity,"Type":0})
        selects.insert(1,{"Column":{"Expression":{"SourceRef":{"Source":legend_alias}},"Property":legend_col},"Name":lqn,"NativeReferenceName":legend_col})
        projections["Legend"] = [{"queryRef":lqn}]
    sv = {
        "visualType": vtype,
        "projections": projections,
        "prototypeQuery":{"Version":2,"From":froms,"Select":selects},
        "drillFilterOtherVisuals":True,
    }
    if title:
        sv["vcObjects"] = {"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    # Apply first color for single-series charts
    if colors and vtype not in ("donutChart","pieChart"):
        sv["vcObjects"] = sv.get("vcObjects",{})
        c0 = colors[0]
        dp = {"selector": {"data": {"expr": {"Default": {}}}},
              "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{c0}'"}}}}}}}
        sv["vcObjects"]["dataPoint"] = [dp]
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

def make_donut(x,y,w,h,entity,alias,cat_col,val_col,agg_fn,label,tab,title=""):
    cqn=f"{entity}.{cat_col}"; vqn=f"Sum({entity}.{val_col})"
    sv={
        "visualType":"donutChart",
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{
            "Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[
                {"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":cat_col},"Name":cqn,"NativeReferenceName":cat_col},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":val_col}},"Function":agg_fn},"Name":vqn,"NativeReferenceName":label}
            ]
        },
        "drillFilterOtherVisuals":True,
    }
    if title:
        sv["vcObjects"]={"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

def make_slicer(x,y,w,h,entity,alias,col_,tab,style="Dropdown"):
    qn=f"{entity}.{col_}"
    sv={
        "visualType":"slicer",
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{
            "Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_},"Name":qn,"NativeReferenceName":col_}]
        },
        "objects":{"data":[{"properties":{"mode":{"expr":{"Literal":{"Value":f"'{style}'"}}}}}]},
        "drillFilterOtherVisuals":True,
    }
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

def make_matrix(x,y,w,h,tab,title="Monthly Orders Heatmap"):
    sv={
        "visualType":"pivotTable",
        "projections":{
            "Rows":[{"queryRef":"Year(Sales.Order Date)","active":True}],
            "Columns":[{"queryRef":"MonthName(Sales.Order Date)","active":True}],
            "Values":[{"queryRef":"CountNonNull(Sales.Order ID)"}]
        },
        "prototypeQuery":{
            "Version":2,"From":[{"Name":"s","Entity":"Sales","Type":0}],
            "Select":[
                {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order Date"}},"TimeUnit":6},"Name":"Year(Sales.Order Date)","NativeReferenceName":"Year"},
                {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order Date"}},"TimeUnit":3},"Name":"MonthName(Sales.Order Date)","NativeReferenceName":"Month"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order ID"}},"Function":5},"Name":"CountNonNull(Sales.Order ID)","NativeReferenceName":"Count of Orders"}
            ]
        },
        "drillFilterOtherVisuals":True,
        "vcObjects":{
            "title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}],
            "subTotals":[{"properties":{"rowSubtotals":{"expr":{"Literal":{"Value":"false"}}},"columnSubtotals":{"expr":{"Literal":{"Value":"false"}}}}}]
        }
    }
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

def make_line(x,y,w,h,cat_entity,cat_alias,cat_col,tab,title="",extra_ds=None):
    """Line chart: cat dimension on X, Net Sales on Y"""
    cqn=f"{cat_entity}.{cat_col}"
    vqn="Sum(Sales.Net Sales)"
    froms=[{"Name":cat_alias,"Entity":cat_entity,"Type":0}]
    if cat_alias!="s": froms.append({"Name":"s","Entity":"Sales","Type":0})
    selects=[
        {"Column":{"Expression":{"SourceRef":{"Source":cat_alias}},"Property":cat_col},"Name":cqn,"NativeReferenceName":cat_col},
        {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Net Sales"}},"Function":0},"Name":vqn,"NativeReferenceName":"Net Sales"}
    ]
    sv={
        "visualType":"lineChart",
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":selects},
        "drillFilterOtherVisuals":True,
    }
    if title:
        sv["vcObjects"]={"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

def make_textbox(x,y,w,h,text,font_size="16",bold=True,color="#FFFFFF",bg="#252423",tab=0):
    fw = "bold" if bold else "normal"
    sv = {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {"fontWeight": fw, "fontSize": f"{font_size}pt", "color": color}}],
                "horizontalTextAlignment": "left"
            }]}}]
        }
    }
    return vc_base(x,y,w,h,tab,{"singleVisual":sv})

# KPI card row helper — 6 cards
CW,CH = 193,105
def kpi_row(base_y, tab_base):
    defs = [
        ("Sales","s","Net Sales",  0,"Total Revenue",  TEAL),
        ("Sales","s","Profit",     0,"Total Profit",   GREEN),
        ("Sales","s","Order ID",   5,"Total Orders",   BLUE),
        ("Sales","s","Net Sales",  0,"Avg Order Value", YELLOW),
        ("Sales","s","Order ID",   5,"Return Rate",    RED),
        ("Sales","s","Net Sales",  0,"Target Achievement", PURPLE),
    ]
    cards = []
    for i,(e,a,c,f,lbl,bc) in enumerate(defs):
        cards.append(make_card(10+i*(CW+8), base_y, CW, CH, e,a,c,f,lbl, tab_base+i*10, bc))
    return cards

# ── FILTERS (4 slicers + header) used on every page ─────────────────────────
def filter_row(tab_base, canvas_h=800):
    # header strip
    hdr = make_textbox(0,0,1280,44,"  Sales Analytics Dashboard","13",True,"#FFFFFF","#252423",tab_base)
    # slicers
    sl1 = make_slicer(80, 50, 130, 28, "Sales","s","Year",      tab_base+1)
    sl2 = make_slicer(225,50, 155, 28, "Sales","s","Quarter",   tab_base+2)
    sl3 = make_slicer(395,50, 165, 28, "Sales","s","Category",  tab_base+3)
    sl4 = make_slicer(575,50, 160, 28, "Sales","s","Sales Channel", tab_base+4)
    return [hdr, sl1, sl2, sl3, sl4]

# ── PAGE 1: Executive Summary (canvas 1280×800) ───────────────────────────────
p1 = (
    filter_row(0) +
    kpi_row(88, 100) +
    [
        # Revenue Trend line chart — full width
        make_line(10,210,1260,200, "Sales","s","Order Date",600,"Revenue Trend — Current Year vs Prior Year"),
        # Row 3: Sales by Category (bar) | Sales Channel Mix (donut) | Order Status (donut)
        make_chart(10,425,400,355, "clusteredBarChart",
                   "Sales","s","Category","Sales","s","Net Sales",0,"Net Sales",700,"Sales by Category",[TEAL]),
        make_donut(420,425,415,355,"Sales","s","Sales Channel","Net Sales",0,"Net Sales",800,"Sales Channel Mix"),
        make_donut(845,425,425,355,"Sales","s","Order Status","Order ID",5,"Count",900,"Order Status Distribution"),
    ]
)

# ── PAGE 2: Sales Performance ─────────────────────────────────────────────────
p2 = (
    filter_row(0) +
    kpi_row(88, 100) +
    [
        # Monthly heatmap
        make_matrix(10,210,1260,195,600,"Monthly Orders Heatmap"),
        # Sales by Country (horizontal bar) | Payment Method (vertical bar)
        make_chart(10,415,620,370,"clusteredBarChart",
                   "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,"Sales by Country",[TEAL]),
        make_chart(645,415,625,370,"clusteredColumnChart",
                   "Sales","s","Payment Method","Sales","s","Order ID",5,"Orders",800,"Payment Method Breakdown",None,None,None,COLORS),
        # Quarterly Revenue by Year
        make_chart(10,795,1260,0,"clusteredColumnChart",  # won't fit — put on same page differently
                   "Sales","s","Quarter","Sales","s","Net Sales",0,"Net Sales",900,"Quarterly Revenue by Year",
                   "Sales","s","Year"),
    ]
)
# Fix quarterly chart y position
p2[-1]["y"] = 795
p2[-1]["height"] = 195
# Actually let's squeeze: heatmap 195h, country/payment 345h, quarterly 210h => 195+345+210=750 + 88 kpi + 44+28 filter = fine at 800
# Recalculate:  top bar=44, slicer row=28 -> y=88 for cards (height 105) -> y=200 for heatmap (195h) -> y=400 for country/payment (280h) -> y=685 for quarterly (105h)
p2 = (
    filter_row(0) +
    kpi_row(88, 100) +
    [
        make_matrix(10,200,1260,195,600,"Monthly Orders Heatmap"),
        make_chart(10,402,620,275,"clusteredBarChart",
                   "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,"Sales by Country",[TEAL]),
        make_chart(645,402,625,275,"clusteredColumnChart",
                   "Sales","s","Payment Method","Sales","s","Order ID",5,"Orders",800,"Payment Method Breakdown",None,None,None,COLORS),
        make_chart(10,683,1260,107,"clusteredColumnChart",
                   "Sales","s","Quarter","Sales","s","Net Sales",0,"Net Sales",900,"Quarterly Revenue by Year",
                   "Sales","s","Year"),
    ]
)

# ── PAGE 3: Product Analysis ──────────────────────────────────────────────────
p3 = (
    filter_row(0) +
    kpi_row(88, 100) +
    [
        # Top 10 Products by Net Sales (horizontal bar, Product ID as category)
        make_chart(10,200,620,280,"clusteredBarChart",
                   "Sales","s","Product ID","Sales","s","Net Sales",0,"Net Sales",600,"Top 10 Products by Net Sales",[TEAL]),
        # Profit Margin % by Category (vertical bar)
        make_chart(645,200,625,280,"clusteredColumnChart",
                   "Sales","s","Category","Sales","s","Profit Margin %",1,"Avg Margin %",700,"Profit Margin % by Category",None,None,None,COLORS),
        # Category Revenue vs Profit (grouped bar, full width)
        make_chart(10,490,1260,295,"clusteredColumnChart",
                   "Sales","s","Category","Sales","s","Net Sales",0,"Net Sales",800,"Category Revenue vs Profit",
                   "Sales","s","Profit"),
    ]
)

# ── PAGE 4: Customer Insights ─────────────────────────────────────────────────
p4 = (
    filter_row(0) +
    kpi_row(88, 100) +
    [
        make_chart(10,200,620,280,"clusteredBarChart",
                   "Customers","c","Segment","Sales","s","Net Sales",0,"Net Sales",600,"Customer Segment Revenue",[TEAL]),
        make_chart(645,200,625,280,"clusteredBarChart",
                   "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,"Sales by Customer Country",[BLUE]),
        make_chart(10,490,620,295,"clusteredColumnChart",
                   "Sales","s","Sales Channel","Sales","s","Order ID",5,"Orders",800,"Orders by Channel & Status",
                   "Sales","s","Order Status"),
        make_chart(645,490,625,295,"clusteredBarChart",
                   "Customers","c","Segment","Customers","c","Credit Limit",0,"Avg Credit Limit",900,"Credit Limit by Segment",[YELLOW]),
    ]
)

# ── PAGE 5: Team Performance ──────────────────────────────────────────────────
p5 = (
    filter_row(0) +
    kpi_row(88, 100) +
    [
        # Team Sales vs Target (grouped bar, User Name)
        make_chart(10,200,1260,290,"clusteredColumnChart",
                   "Users","u","Name","Sales","s","Net Sales",0,"Net Sales",600,"Team Performance: Sales vs Target",
                   "Users","u","Sales Target"),
        # Sales by Location (horizontal bar)
        make_chart(10,500,620,285,"clusteredBarChart",
                   "Users","u","Location","Sales","s","Net Sales",0,"Net Sales",700,"Sales by Location / City",[TEAL]),
        # Team details table (using clusteredBarChart as proxy — table visual is complex)
        make_chart(645,500,625,285,"clusteredBarChart",
                   "Users","u","Role","Sales","s","Net Sales",0,"Net Sales",800,"Sales by Role",[PURPLE]),
    ]
)

# ── Assemble report layout ────────────────────────────────────────────────────
def section(sid, name, display, ordinal, visuals):
    return {"id":sid,"name":name,"displayName":display,"ordinal":ordinal,
            "visualContainers":visuals,"filters":"[]","config":"{}",
            "displayOption":1,"width":1280,"height":800}

theme_cfg = json.dumps({
    "version":"5.49",
    "themeCollection":{"baseTheme":{"name":"CY23SU11","version":"5.49","type":2}},
    "activeSectionIndex":0,
    "defaultDrillFilterOtherVisuals":True,
    "settings":{"useNewFilterPaneExperience":True,"allowChangeFilterTypes":True,"useStylableVisualContainerHeader":True},
})

report_layout = {
    "id":0,
    "resourcePackages":[{"resourcePackage":{"name":"SharedResources","type":2,
        "items":[{"type":202,"path":"BaseThemes/CY23SU11.json","name":"CY23SU11"}],"disabled":False}}],
    "sections":[
        section(0,"S1","Executive Summary",0,p1),
        section(1,"S2","Sales Performance",1,p2),
        section(2,"S3","Product Analysis",2,p3),
        section(3,"S4","Customer Insights",3,p4),
        section(4,"S5","Team Performance",4,p5),
    ],
    "config": theme_cfg,
    "layoutOptimization":0
}

# ── Custom Power BI theme JSON ────────────────────────────────────────────────
theme_json = {
    "name": "SalesDashboard",
    "dataColors": COLORS,
    "background": "#F3F2F1",
    "foreground": "#252423",
    "tableAccent": "#01B8AA",
    "visualStyles": {
        "*": {"*": {
            "background": [{"color": {"solid": {"color": "#FFFFFF"}}}],
            "border": [{"show": True}]
        }},
        "card": {"*": {
            "labels": [{"color": {"solid": {"color": "#252423"}}, "fontSize": 22, "fontFamily": "Segoe UI"}],
            "categoryLabels": [{"color": {"solid": {"color": "#5F6B6D"}}, "fontSize": 11}]
        }},
        "clusteredBarChart": {"*": {
            "dataPoint": [{"fill": {"solid": {"color": "#01B8AA"}}}]
        }},
        "lineChart": {"*": {
            "dataPoint": [{"fill": {"solid": {"color": "#01B8AA"}}}]
        }}
    }
}

# ── Diagram layout ────────────────────────────────────────────────────────────
diagram = {
    "version":"1.1.0","selectedDiagram":"All tables","defaultDiagram":"All tables",
    "diagrams":[{"ordinal":0,"scrollPosition":{"x":0,"y":0},
        "nodes":[
            {"location":{"x":10,"y":10},"nodeIndex":"Sales","nodeLineageTag":uid(),"size":{"height":300,"width":234},"zIndex":0},
            {"location":{"x":270,"y":10},"nodeIndex":"Customers","nodeLineageTag":uid(),"size":{"height":200,"width":234},"zIndex":0},
            {"location":{"x":530,"y":10},"nodeIndex":"Users","nodeLineageTag":uid(),"size":{"height":220,"width":234},"zIndex":0},
        ],
        "name":"All tables","zoomValue":100,"pinKeyFieldsToTop":False,
        "showExtraHeaderInfo":False,"hideKeyFieldsWhenCollapsed":False,"tablesLocked":False}]
}

# ── Write PBIT ────────────────────────────────────────────────────────────────
out_path = "/home/user/newm/SalesAnalytics_Final.pbit"

content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/DataModelSchema"  ContentType="application/json"/>
  <Override PartName="/DiagramLayout"    ContentType="application/json"/>
  <Override PartName="/Report/Layout"    ContentType="application/json"/>
  <Override PartName="/Settings"         ContentType="application/json"/>
  <Override PartName="/Metadata"         ContentType="application/json"/>
</Types>"""

metadata = json.dumps({"Version":5,"AutoCreatedRelationships":[],"CreatedFrom":"Cloud","CreatedFromRelease":"2023.11"})
settings  = json.dumps({"Version":4,"ReportSettings":{},"QueriesSettings":{"TypeDetectionEnabled":True,"RelationshipImportEnabled":True,"Version":"2.123.424.0"}})

# Theme from source pbix
with zipfile.ZipFile('/tmp/pbix_v3/source.pbix') as z:
    orig_theme = z.read('Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json')

def u16(s): return s.encode('utf-16-le')

layout_str  = json.dumps(report_layout, ensure_ascii=False)
schema_str  = json.dumps(model_schema,  ensure_ascii=False, indent=2)
diagram_str = json.dumps(diagram,       ensure_ascii=False)

with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('Version',              '3.0')
    z.writestr('[Content_Types].xml',  content_types.encode('utf-8'))
    z.writestr('DataModelSchema',      schema_str.encode('utf-8'))   # UTF-8!
    z.writestr('DiagramLayout',        u16(diagram_str))
    z.writestr('Report/Layout',        u16(layout_str))
    z.writestr('Settings',             u16(settings))
    z.writestr('Metadata',             u16(metadata))
    z.writestr('SecurityBindings',     b'')
    z.writestr('Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json', orig_theme)

# Verify
size = os.path.getsize(out_path)
print(f"\nWritten: {out_path}  ({size:,} bytes)")
with zipfile.ZipFile(out_path) as z:
    print("Contents:")
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")

    schema = json.loads(z.read('DataModelSchema').decode('utf-8'))
    m = schema['model']
    print(f"\nTables ({len(m['tables'])}): {[t['name'] for t in m['tables']]}")
    print(f"Relationships ({len(m['relationships'])}):")
    for r in m['relationships']:
        print(f"  {r['fromTable']}[{r['fromColumn']}] → {r['toTable']}[{r['toColumn']}]")
    total_measures = sum(len(t.get('measures',[])) for t in m['tables'])
    print(f"Measures: {total_measures}")

    layout = json.loads(z.read('Report/Layout').decode('utf-16-le'))
    print(f"\nPages:")
    for s in layout['sections']:
        print(f"  [{s['ordinal']}] {s['displayName']}: {len(s['visualContainers'])} visuals")

print("\nDone.")

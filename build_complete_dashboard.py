"""
Build SalesAnalytics_Complete.pbit
Fully mirrors PowerBI_Sales_Dashboard.html:
  - 500 sales, 100 customers, 30 users, 80 products (exact HTML data)
  - 5 pages with all charts matching HTML layout
  - Exact color palette: teal/dark/red/yellow/blue/purple
  - 15 DAX measures
  - 3 relationships
  - RLS role: Sales Rep (filtered by User ID)
  - Card formatting, chart colors, page bg
"""

import json, zipfile, uuid, os, re

HTML = '/root/.claude/uploads/aca83dfd-49f9-4f0e-8908-adcd40559f08/b322cacb-PowerBI_Sales_Dashboard.html'
OUT  = '/home/user/newm/SalesAnalytics_Complete.pbit'

# ── Extract data from HTML ────────────────────────────────────────────────────
html = open(HTML).read()

def extract_js_array(name):
    m = re.search(rf'const {name}\s*=\s*(\[[\s\S]*?\n\]);', html)
    if not m:
        m = re.search(rf'const {name}\s*=\s*(\[.*?\]);', html, re.DOTALL)
    txt = re.sub(r'\bNaN\b', 'null', m.group(1))
    return json.loads(txt)

SALES     = extract_js_array('RAW_SALES')
CUSTOMERS = extract_js_array('RAW_CUSTOMERS')
USERS     = extract_js_array('RAW_USERS')
PRODUCTS  = extract_js_array('RAW_PRODUCTS')

print(f"Loaded: {len(SALES)} sales, {len(CUSTOMERS)} customers, {len(USERS)} users, {len(PRODUCTS)} products")

# ── Colors ────────────────────────────────────────────────────────────────────
TEAL   = "#01B8AA"; DARK  = "#252423"; RED    = "#FD625E"
YELLOW = "#F2C80F"; BLUE  = "#118DFF"; PURPLE = "#8B00FF"
GREEN  = "#00B050"; DGRAY = "#374649"; ORANGE = "#FF6B35"
WHITE  = "#FFFFFF"; LTGRAY= "#F3F2F1"; SLATE  = "#5F6B6D"
CHART_COLORS = [TEAL,RED,YELLOW,BLUE,PURPLE,GREEN,ORANGE,DGRAY,SLATE,"#E91E63"]
CARD_ACCENTS = [TEAL,GREEN,BLUE,YELLOW,RED,PURPLE]

# ── M Query helpers ───────────────────────────────────────────────────────────
def q(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int,float)): return str(v)
    return '"' + str(v).replace('\\','\\\\').replace('"','\\"') + '"'

def build_m_table(records, col_types):
    type_decls = ", ".join(f'#"{c}" = {t}' for c,t in col_types)
    rows = []
    for rec in records:
        vals = ", ".join(q(rec.get(c)) for c,_ in col_types)
        rows.append(f"    {{{vals}}}")
    lines = (
        ["let",
         f'  Source = #table(type table [{type_decls}], {{']
        + [(",\n" if i > 0 else "") + r if i == 0 else r for i,r in enumerate(rows)]
    )
    # Simpler build
    body = ",\n".join(rows)
    expr = ["let",
            f"  Source = #table(type table [{type_decls}], {{",
            body,
            "  })",
            "in",
            "  Source"]
    return expr

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
PROD_COLS = [
    ("Product ID","text"),("Product Name","text"),("Category","text"),
    ("Sub Category","text"),("Brand","text"),("Unit Cost","number"),
    ("Unit Price","number"),("Profit Margin %","number"),("Stock Quantity","Int64.Type"),
    ("Reorder Level","Int64.Type"),("Supplier","text"),("Weight (kg)","number"),
    ("Rating","number"),
]

def clean(rec, cols):
    out = {}
    for c,t in cols:
        v = rec.get(c)
        if v is None or (isinstance(v, float) and v != v): out[c] = None
        elif t == "date" and isinstance(v, str): out[c] = v[:10]
        elif t in ("Int64.Type",) and isinstance(v, float): out[c] = int(v)
        else: out[c] = v
    return out

sales_data = [clean(r, SALES_COLS) for r in SALES]
cust_data  = [clean(r, CUST_COLS)  for r in CUSTOMERS]
user_data  = [clean(r, USER_COLS)  for r in USERS]
prod_data  = [clean(r, PROD_COLS)  for r in PRODUCTS]

sales_expr = build_m_table(sales_data, SALES_COLS)
cust_expr  = build_m_table(cust_data,  CUST_COLS)
user_expr  = build_m_table(user_data,  USER_COLS)
prod_expr  = build_m_table(prod_data,  PROD_COLS)

# ── DAX Measures ──────────────────────────────────────────────────────────────
MEASURES = [
    ("Total Revenue",      "Sales", "SUM(Sales[Net Sales])"),
    ("Total Profit",       "Sales", "SUM(Sales[Profit])"),
    ("Total Orders",       "Sales", "COUNTROWS(Sales)"),
    ("Total Returns",      "Sales", 'CALCULATE(COUNTROWS(Sales), Sales[Order Status]="Returned")'),
    ("Total Customers",    "Sales", "DISTINCTCOUNT(Sales[Customer ID])"),
    ("Avg Order Value",    "Sales", "DIVIDE([Total Revenue], [Total Orders], 0)"),
    ("Profit Margin %",    "Sales", "DIVIDE([Total Profit], [Total Revenue], 0)"),
    ("Return Rate %",      "Sales", "DIVIDE([Total Returns], [Total Orders], 0)"),
    ("Target Achievement %","Users","DIVIDE([Total Revenue], SUM(Users[Sales Target]), 0)"),
    ("Revenue YoY %",      "Sales",
     "VAR cy = CALCULATE([Total Revenue], YEAR(Sales[Order Date]) = YEAR(TODAY()))\n"
     "VAR py = CALCULATE([Total Revenue], YEAR(Sales[Order Date]) = YEAR(TODAY())-1)\n"
     "RETURN DIVIDE(cy - py, py, 0)"),
    ("Completed Orders",   "Sales", 'CALCULATE(COUNTROWS(Sales), Sales[Order Status]="Completed")'),
    ("Pending Orders",     "Sales", 'CALCULATE(COUNTROWS(Sales), Sales[Order Status]="Pending")'),
    ("Avg Credit Limit",   "Customers", "AVERAGE(Customers[Credit Limit])"),
    ("Total Gross Sales",  "Sales", "SUM(Sales[Gross Sales])"),
    ("Total Discount",     "Sales", "SUM(Sales[Discount Amount])"),
]

def measure_obj(name, tbl, expr):
    return {"name": name, "expression": expr,
            "formatString": ("0.00%" if "%" in name else
                             "#,0.00" if any(x in name for x in ["Revenue","Profit","Sales","Value","Limit","Discount"]) else
                             "#,0"),
            "isHidden": False}

# ── DataModelSchema ───────────────────────────────────────────────────────────
def make_table(name, expr_lines, cols, measures=None, is_hidden=False):
    col_objs = []
    for c, t in cols:
        dt = ("dateTime" if t=="date" else
              "int64" if t=="Int64.Type" else
              "double" if t=="number" else "string")
        col_objs.append({"name": c, "dataType": dt,
                         "sourceColumn": c, "summarizeBy": "none"})
    t_obj = {
        "name": name,
        "columns": col_objs,
        "partitions": [{"name": name, "mode": "import",
                        "source": {"type": "m", "expression": expr_lines}}],
        "isHidden": is_hidden
    }
    if measures:
        t_obj["measures"] = measures
    return t_obj

# Build measure objects per table
def measures_for_table(tbl):
    return [measure_obj(n,t,e) for n,t,e in MEASURES if t==tbl]

sales_table = make_table("Sales",     sales_expr, SALES_COLS, measures_for_table("Sales"))
cust_table  = make_table("Customers", cust_expr,  CUST_COLS,  measures_for_table("Customers"))
user_table  = make_table("Users",     user_expr,  USER_COLS,  measures_for_table("Users"))
prod_table  = make_table("Products",  prod_expr,  PROD_COLS)

model_schema = {
    "name": "SalesAnalyticsDashboard",
    "compatibilityLevel": 1567,
    "defaultPowerBIDataSourceVersion": "powerBI_V3",
    "tables": [sales_table, cust_table, user_table, prod_table],
    "relationships": [
        {"name": "Sales_Customers",
         "fromTable": "Sales", "fromColumn": "Customer ID",
         "toTable": "Customers", "toColumn": "Customer ID",
         "crossFilteringBehavior": "oneDirection"},
        {"name": "Sales_Users",
         "fromTable": "Sales", "fromColumn": "User ID",
         "toTable": "Users", "toColumn": "User ID",
         "crossFilteringBehavior": "oneDirection"},
        {"name": "Sales_Products",
         "fromTable": "Sales", "fromColumn": "Product ID",
         "toTable": "Products", "toColumn": "Product ID",
         "crossFilteringBehavior": "oneDirection"},
    ],
    "roles": [{
        "name": "Sales Rep",
        "modelPermission": "read",
        "tablePermissions": [{
            "name": "Users",
            "filterExpression": "[User ID] = USERPRINCIPALNAME()"
        }]
    }],
    "annotations": [{"name": "PBIDesktopVersion", "value": "2.130"}]
}

schema_bytes = json.dumps({"model": model_schema}, ensure_ascii=False).encode("utf-8")

# ── Report/Layout visual helpers ──────────────────────────────────────────────
def vn(): return uuid.uuid4().hex[:20]
def lit(v):   return {"expr": {"Literal": {"Value": v}}}
def clr(c):   return {"solid": {"color": lit(f"'{c}'")}}

def vc(x, y, w, h, tab, sv):
    p = {"x":x,"y":y,"z":tab,"width":w,"height":h,"tabOrder":tab}
    return {**p, "filters":"[]",
            "config": json.dumps({"name":vn(),"layouts":[{"id":0,"position":p}],
                                  "singleVisual":sv}),
            "query":"{}","dataTransforms":"{}"}

def chart_style():
    return {
        "background": [{"properties":{"show":lit("true"),"color":clr(WHITE),"transparency":lit("0D")}}],
        "border":     [{"properties":{"show":lit("true"),"color":clr("#E0DFDE"),"radius":lit("4D")}}],
    }

def card(x,y,w,h,entity,alias,col_,agg_fn,label,tab,accent=TEAL):
    fn  = "Sum" if agg_fn==0 else "Avg" if agg_fn==1 else "Count" if agg_fn==3 else "CountNonNull"
    qn  = f"{fn}({entity}.{col_})"
    sv  = {
        "visualType":"card","drillFilterOtherVisuals":True,
        "projections":{"Values":[{"queryRef":qn}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_}},"Function":agg_fn},"Name":qn,"NativeReferenceName":label}]},
        "vcObjects":{
            "background":[{"properties":{"show":lit("true"),"color":clr(WHITE),"transparency":lit("0D")}}],
            "border":    [{"properties":{"show":lit("true"),"color":clr(accent),"radius":lit("4D")}}],
            "labels":    [{"properties":{"color":clr(DARK),"fontSize":lit("20D"),"fontFamily":lit("'Segoe UI'"),"bold":lit("true")}}],
            "categoryLabels":[{"properties":{"show":lit("true"),"color":clr(SLATE),"fontSize":lit("10D")}}],
            "dropShadow":[{"properties":{"show":lit("true")}}],
        }
    }
    return vc(x,y,w,h,tab,sv)

def measure_card(x,y,w,h,measure_name,label,tab,accent=TEAL):
    """Card showing a DAX measure (not a raw column aggregation)."""
    qn = measure_name
    sv = {
        "visualType":"card","drillFilterOtherVisuals":True,
        "projections":{"Values":[{"queryRef":qn}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":"s","Entity":"Sales","Type":0}],
            "Select":[{"Measure":{"Expression":{"SourceRef":{"Source":"s"}},"Property":measure_name},"Name":qn,"NativeReferenceName":label}]},
        "vcObjects":{
            "background":[{"properties":{"show":lit("true"),"color":clr(WHITE),"transparency":lit("0D")}}],
            "border":    [{"properties":{"show":lit("true"),"color":clr(accent),"radius":lit("4D")}}],
            "labels":    [{"properties":{"color":clr(DARK),"fontSize":lit("20D"),"fontFamily":lit("'Segoe UI'"),"bold":lit("true")}}],
            "categoryLabels":[{"properties":{"show":lit("true"),"color":clr(SLATE),"fontSize":lit("10D")}}],
            "dropShadow":[{"properties":{"show":lit("true")}}],
        }
    }
    return vc(x,y,w,h,tab,sv)

def bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
        vtype="clusteredBarChart",leg_e=None,leg_a=None,leg_c=None):
    cqn=f"{cat_e}.{cat_c}"; vqn=f"{'Sum' if agg==0 else 'Count' if agg==3 else 'Avg'}({val_e}.{val_c})"
    froms=[{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a!=cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sels=[
        {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
        {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
    ]
    projs={"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]}
    if leg_c:
        lqn=f"{leg_e}.{leg_c}"
        if leg_a not in [f["Name"] for f in froms]: froms.append({"Name":leg_a,"Entity":leg_e,"Type":0})
        sels.insert(1,{"Column":{"Expression":{"SourceRef":{"Source":leg_a}},"Property":leg_c},"Name":lqn,"NativeReferenceName":leg_c})
        projs["Legend"]=[{"queryRef":lqn}]
    sv={"visualType":vtype,"drillFilterOtherVisuals":True,
        "projections":projs,"prototypeQuery":{"Version":2,"From":froms,"Select":sels},
        "vcObjects":chart_style()}
    return vc(x,y,w,h,tab,sv)

def line(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,leg_e=None,leg_a=None,leg_c=None):
    return bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,"lineChart",leg_e,leg_a,leg_c)

def donut(x,y,w,h,entity,alias,cat_c,val_e,val_a,val_c,agg,label,tab):
    cqn=f"{entity}.{cat_c}"; vqn=f"{'Sum' if agg==0 else 'Count'}({val_e}.{val_c})"
    froms=[{"Name":alias,"Entity":entity,"Type":0}]
    if val_a!=alias: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sv={"visualType":"donutChart","drillFilterOtherVisuals":True,
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":[
            {"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
        ]},
        "vcObjects":chart_style()}
    return vc(x,y,w,h,tab,sv)

def pie(x,y,w,h,entity,alias,cat_c,val_e,val_a,val_c,agg,label,tab):
    cqn=f"{entity}.{cat_c}"; vqn=f"Sum({val_e}.{val_c})"
    froms=[{"Name":alias,"Entity":entity,"Type":0}]
    if val_a!=alias: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sv={"visualType":"pieChart","drillFilterOtherVisuals":True,
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":[
            {"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
        ]},
        "vcObjects":chart_style()}
    return vc(x,y,w,h,tab,sv)

def matrix(x,y,w,h,tab):
    sv={"visualType":"pivotTable","drillFilterOtherVisuals":True,
        "projections":{
            "Rows":   [{"queryRef":"Year(Sales.Order Date)","active":True}],
            "Columns":[{"queryRef":"MonthName(Sales.Order Date)","active":True}],
            "Values": [{"queryRef":"CountNonNull(Sales.Order ID)"}]
        },
        "prototypeQuery":{"Version":2,"From":[{"Name":"s","Entity":"Sales","Type":0}],"Select":[
            {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order Date"}},"TimeUnit":6},"Name":"Year(Sales.Order Date)","NativeReferenceName":"Year"},
            {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order Date"}},"TimeUnit":3},"Name":"MonthName(Sales.Order Date)","NativeReferenceName":"Month"},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order ID"}},"Function":5},"Name":"CountNonNull(Sales.Order ID)","NativeReferenceName":"Orders"},
        ]},
        "vcObjects":{
            **chart_style(),
            "subTotals":[{"properties":{"rowSubtotals":lit("false"),"columnSubtotals":lit("false")}}],
            "columnHeaders":[{"properties":{"backColor":clr(TEAL),"fontColor":clr(WHITE),"bold":lit("true"),"fontSize":lit("11D")}}],
            "rowHeaders":   [{"properties":{"fontColor":clr(DARK),"bold":lit("true"),"fontSize":lit("11D")}}],
            "values":       [{"properties":{"backColor":clr(LTGRAY),"fontColor":clr(DARK),"fontSize":lit("11D")}}],
        }}
    return vc(x,y,w,h,tab,sv)

def slicer(x,y,w,h,entity,alias,col_,tab):
    qn=f"{entity}.{col_}"
    sv={"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":lit("'Dropdown'")}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_},"Name":qn,"NativeReferenceName":col_}]},
        "vcObjects":{
            "background":[{"properties":{"show":lit("true"),"color":clr(WHITE),"transparency":lit("0D")}}],
            "border":    [{"properties":{"show":lit("true"),"color":clr(TEAL)}}],
            "header":    [{"properties":{"show":lit("true"),"fontColor":clr(DARK),"background":clr(LTGRAY),"outline":lit("'None'")}}],
            "items":     [{"properties":{"fontColor":clr(DARK),"background":clr(WHITE)}}],
        }}
    return vc(x,y,w,h,tab,sv)

def textbox(x,y,w,h,text,tab,bg=DARK,fg=WHITE,sz="13pt",bold=True):
    runs=[{"value":text,"textStyle":{
        "fontWeight":"bold" if bold else "normal",
        "fontSize":sz,"color":fg}}]
    sv={"visualType":"textbox","objects":{"general":[{"properties":{"paragraphs":[{
        "textRuns":runs,"horizontalTextAlignment":"left"}]}}]},
        "vcObjects":{"background":[{"properties":{"show":lit("true"),"color":clr(bg),"transparency":lit("0D")}}]}}
    return vc(x,y,w,h,tab,sv)

def table_visual(x,y,w,h,tab):
    """Team member details table: Name, Role, Location, Net Sales, Target, Achievement."""
    sv={"visualType":"tableEx","drillFilterOtherVisuals":True,
        "projections":{
            "Values":[
                {"queryRef":"Users.Name"},
                {"queryRef":"Users.Role"},
                {"queryRef":"Users.Location"},
                {"queryRef":"Sum(Sales.Net Sales)"},
                {"queryRef":"Sum(Users.Sales Target)"},
            ]
        },
        "prototypeQuery":{"Version":2,
            "From":[{"Name":"u","Entity":"Users","Type":0},{"Name":"s","Entity":"Sales","Type":0}],
            "Select":[
                {"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Name"},"Name":"Users.Name","NativeReferenceName":"Name"},
                {"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Role"},"Name":"Users.Role","NativeReferenceName":"Role"},
                {"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Location"},"Name":"Users.Location","NativeReferenceName":"Location"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Net Sales"}},"Function":0},"Name":"Sum(Sales.Net Sales)","NativeReferenceName":"Net Sales"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Sales Target"}},"Function":0},"Name":"Sum(Users.Sales Target)","NativeReferenceName":"Sales Target"},
            ]},
        "vcObjects":chart_style()}
    return vc(x,y,w,h,tab,sv)

# ── Page layout constants ─────────────────────────────────────────────────────
PW, PH = 1280, 800
CW, CH = 193, 95   # card width/height

def header_strip(page_title, tab=0):
    """Dark header + teal accent line + page title chip + 5 slicers."""
    visuals = []
    # Main dark header bar
    visuals.append(textbox(0,0,PW,46,f"  ◼  Sales Analytics Dashboard   |   {page_title}",tab,DARK,WHITE,"13pt"))
    # Teal accent underline
    visuals.append(textbox(0,46,PW,4,"",tab+1,TEAL,TEAL,"1pt",False))
    # Slicer labels row
    visuals.append(textbox(0,52,PW,18,"    Year            Quarter            Category                 Sales Channel            Payment Method",tab+2,LTGRAY,SLATE,"8pt",False))
    # Slicers
    visuals.append(slicer(8,   72,120,28,"Sales","s","Year",          tab+3))
    visuals.append(slicer(138, 72,120,28,"Sales","s","Quarter",       tab+4))
    visuals.append(slicer(268, 72,155,28,"Sales","s","Category",      tab+5))
    visuals.append(slicer(433, 72,170,28,"Sales","s","Sales Channel", tab+6))
    visuals.append(slicer(613, 72,170,28,"Sales","s","Payment Method",tab+7))
    return visuals

def kpi_row(y, t):
    configs=[
        ("Sales","s","Net Sales",   0,"Total Revenue",   TEAL),
        ("Sales","s","Profit",      0,"Total Profit",    GREEN),
        ("Sales","s","Order ID",    5,"Total Orders",    BLUE),
        ("Sales","s","Net Sales",   1,"Avg Order Value", YELLOW),
        ("Sales","s","Order Status",3,"Return Rate",     RED),
        ("Users","u","Sales Target",0,"Sales Target",    PURPLE),
    ]
    cards=[]
    for i,(ent,ali,col,agg,lbl,acc) in enumerate(configs):
        cards.append(card(10+i*(CW+7),y,CW,CH,ent,ali,col,agg,lbl,t+i*10,acc))
    return cards

# ─── PAGE 1: Executive Summary ────────────────────────────────────────────────
p1 = header_strip("Executive Summary", 0) + kpi_row(104, 100) + [
    # Revenue Trend: monthly Net Sales, legend=Year (current vs prior year comparison)
    line(10,  208, PW-20, 192,
         "Sales","s","Month","Sales","s","Net Sales",0,"Net Sales",600,
         "Sales","s","Year"),
    # Sales by Category - horizontal bar
    bar(10,  410,  390, 375,
        "Sales","s","Category","Sales","s","Net Sales",0,"Net Sales",700,"clusteredBarChart"),
    # Sales Channel Mix - donut
    donut(410, 410, 410, 375,
          "Sales","s","Sales Channel","Sales","s","Net Sales",0,"Net Sales",800),
    # Order Status Distribution - donut
    donut(830, 410, 440, 375,
          "Sales","s","Order Status","Sales","s","Order ID",3,"Orders",900),
]

# ─── PAGE 2: Sales Performance ────────────────────────────────────────────────
p2 = header_strip("Sales Performance", 0) + kpi_row(104, 100) + [
    # Monthly Orders Heatmap (matrix: Year x Month → Count of Orders)
    matrix(10, 208, PW-20, 185, 600),
    # Sales by Country (from Customers table joined to Sales)
    bar(10,  403, 620, 280,
        "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,"clusteredBarChart"),
    # Payment Method Breakdown
    bar(640, 403, 630, 280,
        "Sales","s","Payment Method","Sales","s","Order ID",3,"Orders",800,"clusteredColumnChart"),
    # Quarterly Revenue by Year (grouped bar)
    bar(10,  693, PW-20, 95,
        "Sales","s","Quarter","Sales","s","Net Sales",0,"Net Sales",900,"clusteredColumnChart",
        "Sales","s","Year"),
]

# ─── PAGE 3: Product Analysis ─────────────────────────────────────────────────
p3 = header_strip("Product Analysis", 0) + kpi_row(104, 100) + [
    # Top Products by Net Sales (horizontal bar — drill-down via hierarchy in PBI)
    bar(10,  208, 620, 290,
        "Products","p","Product Name","Sales","s","Net Sales",0,"Net Sales",600,"clusteredBarChart"),
    # Profit Margin % by Category
    bar(640, 208, 630, 290,
        "Sales","s","Category","Sales","s","Profit Margin %",1,"Avg Margin %",700,"clusteredColumnChart"),
    # Category Revenue vs Profit (grouped bar)
    bar(10,  508, PW-20, 275,
        "Sales","s","Category","Sales","s","Net Sales",0,"Net Sales",800,"clusteredColumnChart",
        "Sales","s","Profit"),
]

# ─── PAGE 4: Customer Insights ────────────────────────────────────────────────
p4 = header_strip("Customer Insights", 0) + kpi_row(104, 100) + [
    # Customer Segment Revenue - pie
    pie(10,  208, 390, 285,
        "Customers","c","Segment","Sales","s","Net Sales",0,"Net Sales",600),
    # Sales by Customer Country
    bar(410, 208, 860, 285,
        "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,"clusteredBarChart"),
    # Orders by Segment & Status (stacked)
    bar(10,  503, 620, 280,
        "Customers","c","Segment","Sales","s","Order ID",3,"Orders",800,"clusteredColumnChart",
        "Sales","s","Order Status"),
    # Avg Credit Limit by Segment
    bar(640, 503, 630, 280,
        "Customers","c","Segment","Customers","c","Credit Limit",1,"Avg Credit Limit",900,"clusteredColumnChart"),
]

# ─── PAGE 5: Team Performance ─────────────────────────────────────────────────
p5 = header_strip("Team Performance", 0) + kpi_row(104, 100) + [
    # Team Sales vs Target (grouped bar: User Name vs Net Sales, legend=Sales Target)
    bar(10,  208, PW-20, 260,
        "Users","u","Name","Sales","s","Net Sales",0,"Net Sales",600,"clusteredColumnChart",
        "Users","u","Sales Target"),
    # Sales by Location
    bar(10,  478, 620, 300,
        "Users","u","Location","Sales","s","Net Sales",0,"Net Sales",700,"clusteredBarChart"),
    # Team member table
    table_visual(640, 478, 630, 300, 800),
]

# ── Section builder ───────────────────────────────────────────────────────────
def section(sid, name, display, ordinal, visuals):
    cfg={"page":{"background":{"color":{"solid":{"color":LTGRAY}},"transparency":0}}}
    return {"id":sid,"name":name,"displayName":display,"ordinal":ordinal,
            "visualContainers":visuals,"filters":"[]","config":json.dumps(cfg),
            "displayOption":1,"width":PW,"height":PH}

# ── Custom theme ──────────────────────────────────────────────────────────────
THEME = {
    "name":"SalesAnalyticsTheme",
    "dataColors":CHART_COLORS,
    "background":WHITE,"foreground":DARK,"tableAccent":TEAL,
    "visualStyles":{"card":{"*":{
        "labels":[{"color":{"solid":{"color":DARK}},"fontSize":20,"bold":True}],
        "categoryLabels":[{"show":True,"color":{"solid":{"color":SLATE}},"fontSize":10}]
    }}}
}
THEME_PATH = "Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json"

# ── Report Layout ─────────────────────────────────────────────────────────────
report_layout = {
    "id":0,
    "resourcePackages":[
        {"resourcePackage":{"name":"SharedResources","type":2,
            "items":[{"type":202,"path":"BaseThemes/CY23SU11.json","name":"CY23SU11"}],"disabled":False}},
        {"resourcePackage":{"name":"RegisteredResources","type":1,
            "items":[{"type":202,"path":"SalesAnalyticsTheme.json","name":"SalesAnalyticsTheme"}],"disabled":False}}
    ],
    "sections":[
        section(0,"S1","Executive Summary",0,p1),
        section(1,"S2","Sales Performance", 1,p2),
        section(2,"S3","Product Analysis",  2,p3),
        section(3,"S4","Customer Insights", 3,p4),
        section(4,"S5","Team Performance",  4,p5),
    ],
    "config":json.dumps({
        "version":"5.49",
        "themeCollection":{
            "baseTheme":{"name":"CY23SU11","version":"5.49","type":2},
            "customTheme":{"name":"SalesAnalyticsTheme","type":1,"resourcePackage":"RegisteredResources"}
        },
        "activeSectionIndex":0,"defaultDrillFilterOtherVisuals":True,
        "settings":{"useNewFilterPaneExperience":True,"allowChangeFilterTypes":True,
                    "useStylableVisualContainerHeader":True}
    }),
    "layoutOptimization":0
}

layout_bytes  = json.dumps(report_layout, ensure_ascii=False).encode("utf-16-le")
theme_bytes   = json.dumps(THEME, ensure_ascii=False).encode("utf-8")

# ── Metadata ──────────────────────────────────────────────────────────────────
metadata = json.dumps({"version":"4.0","settings":{}})

content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml"  ContentType="application/xml" />
  <Override PartName="/DataModelSchema"   ContentType="application/json" />
  <Override PartName="/DiagramLayout"     ContentType="application/json" />
  <Override PartName="/Report/Layout"     ContentType="application/json" />
  <Override PartName="/Settings"          ContentType="application/json" />
  <Override PartName="/Metadata"          ContentType="application/json" />
  <Override PartName="/Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
            ContentType="application/json" />
  <Override PartName="/Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json"
            ContentType="application/json" />
</Types>"""

settings = json.dumps({"Version":3,"AutoRecoveryEnabled":False,"RefreshOnOpen":True})

diagram_layout = json.dumps({"version":1,"diagrams":[
    {"ordinal":0,"scrollPosition":{"x":0,"y":0},"zoomValue":100,
     "nodes":[
         {"location":{"x":100,"y":100},"nodeIndex":"Sales",      "size":{"height":200,"width":200},"zIndex":1},
         {"location":{"x":400,"y":100},"nodeIndex":"Customers",  "size":{"height":200,"width":200},"zIndex":2},
         {"location":{"x":700,"y":100},"nodeIndex":"Users",      "size":{"height":200,"width":200},"zIndex":3},
         {"location":{"x":400,"y":350},"nodeIndex":"Products",   "size":{"height":200,"width":200},"zIndex":4},
     ]}
]})

# ── Write PBIT ────────────────────────────────────────────────────────────────
# Try to get base theme from existing PBIX
base_theme_bytes = None
src_pbix = '/tmp/pbix_v3/source.pbix'
if os.path.exists(src_pbix):
    with zipfile.ZipFile(src_pbix) as z:
        for name in z.namelist():
            if 'CY23SU11' in name:
                base_theme_bytes = z.read(name)
                break

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("Version",               "3.0".encode())
    z.writestr("[Content_Types].xml",   content_types.encode("utf-8"))
    z.writestr("DataModelSchema",       schema_bytes)
    z.writestr("DiagramLayout",         diagram_layout.encode("utf-8"))
    z.writestr("Report/Layout",         layout_bytes)
    z.writestr("Settings",              settings.encode("utf-8"))
    z.writestr("Metadata",              metadata.encode("utf-8"))
    z.writestr("SecurityBindings",      b"")
    z.writestr(THEME_PATH,              theme_bytes)
    if base_theme_bytes:
        z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json", base_theme_bytes)

size = os.path.getsize(OUT)
print(f"\nWritten: {OUT}  ({size:,} bytes)")
with zipfile.ZipFile(OUT) as z:
    print("Files in PBIT:")
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")
    layout = json.loads(z.read("Report/Layout").decode("utf-16-le"))
    print("\nPages:")
    for s in layout["sections"]:
        print(f"  Page {s['ordinal']}: {s['displayName']}  ({len(s['visualContainers'])} visuals)")
print("\nDone. Open in Power BI Desktop → Refresh → Save as PBIX → Publish.")

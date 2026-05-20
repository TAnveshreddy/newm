"""
Build SalesAnalytics_v3.pbit
Mirrors HTML dashboard exactly:
- Same data (500 sales, exact columns)
- Dark header like HTML
- KPI cards with colored top border, formatted values ($2.6M style)
- Teal matrix heatmap
- Colored charts matching HTML palette
- Chart titles on every visual
- All 5 pages matching HTML pages exactly
"""
import json, zipfile, uuid, os, re

HTML = '/root/.claude/uploads/aca83dfd-49f9-4f0e-8908-adcd40559f08/b322cacb-PowerBI_Sales_Dashboard.html'
OUT  = '/home/user/newm/SalesAnalytics_v3.pbit'

# ── Extract data ──────────────────────────────────────────────────────────────
html = open(HTML).read()
def get_array(name):
    m = re.search(rf'const {name}\s*=\s*(\[[\s\S]*?\n\]);', html)
    if not m:
        m = re.search(rf'const {name}\s*=\s*(\[.*?\]);', html, re.DOTALL)
    return json.loads(re.sub(r'\bNaN\b','null', m.group(1)))

SALES     = get_array('RAW_SALES')
CUSTOMERS = get_array('RAW_CUSTOMERS')
USERS     = get_array('RAW_USERS')
PRODUCTS  = get_array('RAW_PRODUCTS')
print(f"Data: {len(SALES)} sales, {len(CUSTOMERS)} customers, {len(USERS)} users, {len(PRODUCTS)} products")

# ── Palette (exact HTML colors) ───────────────────────────────────────────────
TEAL="#01B8AA"; DARK="#252423"; RED="#FD625E"; YELLOW="#F2C80F"
BLUE="#118DFF"; PURPLE="#8B00FF"; GREEN="#00B050"; DGRAY="#374649"
ORANGE="#FF6B35"; SLATE="#5F6B6D"; WHITE="#FFFFFF"; LTGRAY="#F3F2F1"
PALETTE=[TEAL,DGRAY,RED,YELLOW,BLUE,PURPLE,ORANGE,GREEN,SLATE,"#E91E63"]

# ── M Query helpers ───────────────────────────────────────────────────────────
def q(v):
    if v is None: return "null"
    if isinstance(v,(int,float)) and not isinstance(v,bool): return str(v)
    if isinstance(v,bool): return "true" if v else "false"
    return '"'+str(v).replace('\\','\\\\').replace('"','\\"')+'"'

def m_table(records, cols):
    type_decls=", ".join(f'#"{c}"={t}' for c,t in cols)
    rows=",\n".join("    {"+", ".join(q(r.get(c)) for c,_ in cols)+"}" for r in records)
    return ["let",f'  Source=#table(type table [{type_decls}],{{',rows,"  })","in","  Source"]

def clean(r,cols):
    out={}
    for c,t in cols:
        v=r.get(c)
        if v is None or (isinstance(v,float) and v!=v): out[c]=None
        elif t=="date" and isinstance(v,str): out[c]=v[:10]
        elif t=="Int64.Type" and isinstance(v,float): out[c]=int(v)
        else: out[c]=v
    return out

SCOLS=[("Order ID","text"),("Order Date","date"),("Year","Int64.Type"),("Month","Int64.Type"),
       ("Quarter","text"),("Customer ID","text"),("Product ID","text"),("User ID","text"),
       ("Category","text"),("Quantity","Int64.Type"),("Unit Price","number"),("Unit Cost","number"),
       ("Gross Sales","number"),("Discount %","number"),("Discount Amount","number"),
       ("Net Sales","number"),("Total Cost","number"),("Profit","number"),
       ("Profit Margin %","number"),("Sales Channel","text"),("Order Status","text"),
       ("Ship Date","date"),("Payment Method","text")]
CCOLS=[("Customer ID","text"),("First Name","text"),("Last Name","text"),("Email","text"),
       ("Phone","text"),("Address","text"),("City","text"),("Country","text"),
       ("Postal Code","text"),("Segment","text"),("Registration Date","date"),("Credit Limit","number")]
UCOLS=[("User ID","text"),("Name","text"),("First Name","text"),("Last Name","text"),
       ("Email","text"),("Role","text"),("Department","text"),("Country","text"),
       ("Location","text"),("Phone","text"),("Join Date","date"),("Manager ID","text"),
       ("Sales Target","number")]
PCOLS=[("Product ID","text"),("Product Name","text"),("Category","text"),("Sub Category","text"),
       ("Brand","text"),("Unit Cost","number"),("Unit Price","number"),("Profit Margin %","number"),
       ("Stock Quantity","Int64.Type"),("Reorder Level","Int64.Type"),("Supplier","text"),
       ("Weight (kg)","number"),("Rating","number")]

s_expr=m_table([clean(r,SCOLS) for r in SALES],    SCOLS)
c_expr=m_table([clean(r,CCOLS) for r in CUSTOMERS], CCOLS)
u_expr=m_table([clean(r,UCOLS) for r in USERS],     UCOLS)
p_expr=m_table([clean(r,PCOLS) for r in PRODUCTS],  PCOLS)

# ── DataModel ─────────────────────────────────────────────────────────────────
def col_obj(c,t):
    dt=("dateTime" if t=="date" else "int64" if t=="Int64.Type" else
        "double" if t=="number" else "string")
    return {"name":c,"dataType":dt,"sourceColumn":c,"summarizeBy":"none"}

def tbl(name,expr,cols,measures=None):
    o={"name":name,
       "columns":[col_obj(c,t) for c,t in cols],
       "partitions":[{"name":name,"mode":"import","source":{"type":"m","expression":expr}}]}
    if measures: o["measures"]=measures
    return o

MDEF=[
    # (name, table, expression, format)
    ("Total Revenue",       "Sales",     'SUM(Sales[Net Sales])',                                         '"$#,0.0,,\\"M\\""'),
    ("Total Profit",        "Sales",     'SUM(Sales[Profit])',                                             '"$#,0.0,,\\"M\\""'),
    ("Total Orders",        "Sales",     'COUNTROWS(Sales)',                                               '"#,0"'),
    ("Avg Order Value",     "Sales",     'DIVIDE([Total Revenue],[Total Orders],0)',                       '"$#,0"'),
    ("Total Returns",       "Sales",     'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Returned")',     '"#,0"'),
    ("Return Rate %",       "Sales",     'DIVIDE([Total Returns],[Total Orders],0)',                       '"0.0%"'),
    ("Target Achievement %","Users",     'DIVIDE([Total Revenue],SUM(Users[Sales Target]),0)',             '"0.0%"'),
    ("Total Customers",     "Sales",     'DISTINCTCOUNT(Sales[Customer ID])',                              '"#,0"'),
    ("Profit Margin %",     "Sales",     'DIVIDE([Total Profit],[Total Revenue],0)',                       '"0.0%"'),
    ("Revenue YoY %",       "Sales",
     'VAR cy=CALCULATE([Total Revenue],YEAR(Sales[Order Date])=YEAR(TODAY()))\n'
     'VAR py=CALCULATE([Total Revenue],YEAR(Sales[Order Date])=YEAR(TODAY())-1)\n'
     'RETURN DIVIDE(cy-py,py,0)',                                                                          '"0.0%"'),
    ("Total Gross Sales",   "Sales",     'SUM(Sales[Gross Sales])',                                        '"$#,0"'),
    ("Total Discount",      "Sales",     'SUM(Sales[Discount Amount])',                                    '"$#,0"'),
    ("Avg Credit Limit",    "Customers", 'AVERAGE(Customers[Credit Limit])',                               '"$#,0"'),
]

def mobj(name,tname,expr,fmt):
    return {"name":name,"expression":expr,"formatString":fmt}

def measures_for(tname):
    return [mobj(n,t,e,f) for n,t,e,f in MDEF if t==tname]

model={
    "name":"SalesAnalyticsDashboard",
    "compatibilityLevel":1567,
    "defaultPowerBIDataSourceVersion":"powerBI_V3",
    "tables":[
        tbl("Sales",    s_expr, SCOLS, measures_for("Sales")),
        tbl("Customers",c_expr, CCOLS, measures_for("Customers")),
        tbl("Users",    u_expr, UCOLS, measures_for("Users")),
        tbl("Products", p_expr, PCOLS),
    ],
    "relationships":[
        {"name":"R1","fromTable":"Sales","fromColumn":"Customer ID","toTable":"Customers","toColumn":"Customer ID","crossFilteringBehavior":"oneDirection"},
        {"name":"R2","fromTable":"Sales","fromColumn":"User ID",    "toTable":"Users",    "toColumn":"User ID",    "crossFilteringBehavior":"oneDirection"},
        {"name":"R3","fromTable":"Sales","fromColumn":"Product ID", "toTable":"Products", "toColumn":"Product ID", "crossFilteringBehavior":"oneDirection"},
    ],
    "roles":[{"name":"Sales Rep","modelPermission":"read",
              "tablePermissions":[{"name":"Users","filterExpression":"[User ID]=USERPRINCIPALNAME()"}]}],
    "annotations":[{"name":"PBIDesktopVersion","value":"2.130"}]
}

schema_bytes=json.dumps({"model":model},ensure_ascii=False).encode("utf-8")

# ── Report Layout helpers ─────────────────────────────────────────────────────
def vn(): return uuid.uuid4().hex[:20]
def L(v): return {"expr":{"Literal":{"Value":v}}}
def C(c): return {"solid":{"color":L(f"'{c}'")}}

def vc(x,y,w,h,tab,sv,title=None):
    p={"x":x,"y":y,"z":tab,"width":w,"height":h,"tabOrder":tab}
    cfg={"name":vn(),"layouts":[{"id":0,"position":p}],"singleVisual":sv}
    if title:
        cfg["singleVisual"]["vcObjects"] = cfg["singleVisual"].get("vcObjects",{})
        cfg["singleVisual"]["vcObjects"]["title"]=[{"properties":{
            "show":L("true"),
            "text":{"expr":{"Literal":{"Value":f'"{title}"'}}},
            "fontColor":C(DARK),
            "fontSize":L("11D"),
            "bold":L("false")
        }}]
    return {**p,"filters":"[]","config":json.dumps(cfg),"query":"{}","dataTransforms":"{}"}

def card_measure(x,y,w,h,measure,label,tab,accent=TEAL):
    """KPI card using a DAX measure — shows formatted value like $2.6M"""
    qn=measure
    sv={
        "visualType":"card","drillFilterOtherVisuals":True,
        "projections":{"Values":[{"queryRef":qn}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":"_","Entity":"Sales","Type":0}],
            "Select":[{"Measure":{"Expression":{"SourceRef":{"Source":"_"}},"Property":measure},"Name":qn,"NativeReferenceName":label}]},
        "objects":{
            "background":[{"properties":{"show":L("true"),"color":C(WHITE),"transparency":L("0D")}}],
            "border":    [{"properties":{"show":L("true"),"color":C(accent),"radius":L("0D")}}],
            "general":   [{"properties":{"keepLayerOrder":L("true")}}],
        },
        "vcObjects":{
            "labels":[{"properties":{
                "color":C(DARK),"fontSize":L("24D"),
                "fontFamily":L("'Segoe UI'"),"bold":L("true"),
                "labelDisplayUnits":L("0D")
            }}],
            "categoryLabels":[{"properties":{
                "show":L("true"),"color":C(SLATE),"fontSize":L("10D"),
                "fontFamily":L("'Segoe UI'")
            }}],
        }
    }
    return vc(x,y,w,h,tab,sv)

def chart_base_objs(title_text):
    """Standard chart objects: white bg, light border, title."""
    return {
        "title":[{"properties":{
            "show":L("true"),
            "text":{"expr":{"Literal":{"Value":f'"{title_text}"'}}},
            "fontColor":C(DARK),"fontSize":L("12D"),"bold":L("true")
        }}],
        "background":[{"properties":{"show":L("true"),"color":C(WHITE),"transparency":L("0D")}}],
        "border":    [{"properties":{"show":L("true"),"color":C("#E0DFDE"),"radius":L("4D")}}],
    }

def bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
        vtype="clusteredBarChart",leg_e=None,leg_a=None,leg_c=None,title=""):
    cqn=f"{cat_e}.{cat_c}"
    fn="Sum" if agg==0 else "Count" if agg==3 else "Avg"
    vqn=f"{fn}({val_e}.{val_c})"
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
        "vcObjects":chart_base_objs(title)}
    return vc(x,y,w,h,tab,sv)

def line_chart(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
               leg_e=None,leg_a=None,leg_c=None,title=""):
    return bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
               "lineChart",leg_e,leg_a,leg_c,title)

def donut(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,title=""):
    cqn=f"{cat_e}.{cat_c}"; fn="Sum" if agg==0 else "Count"
    vqn=f"{fn}({val_e}.{val_c})"
    froms=[{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a!=cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sv={"visualType":"donutChart","drillFilterOtherVisuals":True,
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":[
            {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
        ]},
        "vcObjects":chart_base_objs(title)}
    return vc(x,y,w,h,tab,sv)

def pie_chart(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,title=""):
    cqn=f"{cat_e}.{cat_c}"; vqn=f"Sum({val_e}.{val_c})"
    froms=[{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a!=cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sv={"visualType":"pieChart","drillFilterOtherVisuals":True,
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":[
            {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
        ]},
        "vcObjects":chart_base_objs(title)}
    return vc(x,y,w,h,tab,sv)

def heatmap(x,y,w,h,tab):
    sv={"visualType":"pivotTable","drillFilterOtherVisuals":True,
        "projections":{
            "Rows":   [{"queryRef":"Year(Sales.Order Date)","active":True}],
            "Columns":[{"queryRef":"MonthName(Sales.Order Date)","active":True}],
            "Values": [{"queryRef":"CountNonNull(Sales.Order ID)"}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":"s","Entity":"Sales","Type":0}],"Select":[
            {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order Date"}},"TimeUnit":6},"Name":"Year(Sales.Order Date)","NativeReferenceName":"Year"},
            {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order Date"}},"TimeUnit":3},"Name":"MonthName(Sales.Order Date)","NativeReferenceName":"Month"},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Order ID"}},"Function":5},"Name":"CountNonNull(Sales.Order ID)","NativeReferenceName":"Orders"}
        ]},
        "vcObjects":{
            "title":[{"properties":{"show":L("true"),
                "text":{"expr":{"Literal":{"Value":'"Monthly Orders Heatmap"'}}},
                "fontColor":C(DARK),"fontSize":L("12D"),"bold":L("true")}}],
            "background":[{"properties":{"show":L("true"),"color":C(WHITE),"transparency":L("0D")}}],
            "border":    [{"properties":{"show":L("true"),"color":C(TEAL),"radius":L("2D")}}],
            "subTotals": [{"properties":{"rowSubtotals":L("false"),"columnSubtotals":L("false")}}],
            "columnHeaders":[{"properties":{"backColor":C(TEAL),"fontColor":C(WHITE),"bold":L("true"),"fontSize":L("11D")}}],
            "rowHeaders":   [{"properties":{"fontColor":C(DARK),"bold":L("true"),"fontSize":L("11D")}}],
            "values":       [{"properties":{"backColor":C(LTGRAY),"fontColor":C(DARK),"fontSize":L("11D")}}],
        }}
    return vc(x,y,w,h,tab,sv)

def slicer(x,y,w,h,entity,alias,col_,tab,label=""):
    qn=f"{entity}.{col_}"
    sv={"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":L("'Dropdown'")}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_},"Name":qn,"NativeReferenceName":col_}]},
        "vcObjects":{
            "background":[{"properties":{"show":L("true"),"color":C(WHITE),"transparency":L("0D")}}],
            "border":    [{"properties":{"show":L("true"),"color":C(TEAL)}}],
            "header":    [{"properties":{"show":L("true"),"fontColor":C(DARK),"background":C(LTGRAY),"outline":L("'None'")}}],
            "items":     [{"properties":{"fontColor":C(DARK),"background":C(WHITE)}}],
            "title":     [{"properties":{"show":L("true" if label else "false"),
                "text":{"expr":{"Literal":{"Value":f'"{label}"'}}},"fontColor":C(SLATE),"fontSize":L("9D")}}]
        }}
    return vc(x,y,w,h,tab,sv)

def textbox(x,y,w,h,text,tab,bg=DARK,fg=WHITE,sz="14pt",bold=True):
    sv={"visualType":"textbox",
        "objects":{"general":[{"properties":{"paragraphs":[{
            "textRuns":[{"value":text,"textStyle":{"fontWeight":"bold" if bold else "normal","fontSize":sz,"color":fg}}],
            "horizontalTextAlignment":"left"}]}}]},
        "vcObjects":{"background":[{"properties":{"show":L("true"),"color":C(bg),"transparency":L("0D")}}]}}
    return vc(x,y,w,h,tab,sv)

def team_table(x,y,w,h,tab):
    sv={"visualType":"tableEx","drillFilterOtherVisuals":True,
        "projections":{"Values":[
            {"queryRef":"Users.Name"},{"queryRef":"Users.Role"},
            {"queryRef":"Users.Location"},
            {"queryRef":"Sum(Sales.Net Sales)"},{"queryRef":"Sum(Users.Sales Target)"}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":"u","Entity":"Users","Type":0},{"Name":"s","Entity":"Sales","Type":0}],
            "Select":[
                {"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Name"},"Name":"Users.Name","NativeReferenceName":"Name"},
                {"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Role"},"Name":"Users.Role","NativeReferenceName":"Role"},
                {"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Location"},"Name":"Users.Location","NativeReferenceName":"Location"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":"Net Sales"}},"Function":0},"Name":"Sum(Sales.Net Sales)","NativeReferenceName":"Net Sales"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"u"}},"Property":"Sales Target"}},"Function":0},"Name":"Sum(Users.Sales Target)","NativeReferenceName":"Sales Target"},
            ]},
        "vcObjects":{**chart_base_objs("Team Member Details"),
            "columnHeaders":[{"properties":{"backColor":C(TEAL),"fontColor":C(WHITE),"bold":L("true")}}]}}
    return vc(x,y,w,h,tab,sv)

# ── Page layout ───────────────────────────────────────────────────────────────
PW,PH=1280,800
CW,CH=193,100   # card size

def page_header(page_name,tab=0):
    visuals=[]
    # Dark header bar (matches HTML exactly)
    visuals.append(textbox(0,0,PW,48,f"  ▌ Sales Analytics Dashboard  ·  {page_name}",
                           tab,DARK,WHITE,"13pt",True))
    # Yellow accent strip (like HTML RLS bar)
    visuals.append(textbox(0,48,PW,3,"",tab+1,TEAL,TEAL,"1pt",False))
    # Slicer labels
    label_text="  Year              Quarter            Category                Sales Channel          Payment Method"
    visuals.append(textbox(0,53,PW,16,label_text,tab+2,LTGRAY,SLATE,"8pt",False))
    # 5 slicers (matching HTML filter bar: Year, Quarter, Category, Channel, Payment)
    visuals.append(slicer(8,   71,118,28,"Sales","s","Year",          tab+3,"Year"))
    visuals.append(slicer(134, 71,118,28,"Sales","s","Quarter",       tab+4,"Quarter"))
    visuals.append(slicer(260, 71,155,28,"Sales","s","Category",      tab+5,"Category"))
    visuals.append(slicer(423, 71,162,28,"Sales","s","Sales Channel", tab+6,"Channel"))
    visuals.append(slicer(593, 71,162,28,"Sales","s","Payment Method",tab+7,"Payment"))
    return visuals

def kpi_cards(y,t):
    # 6 cards matching HTML: Total Revenue, Total Profit, Total Orders,
    #                        Avg Order Value, Return Rate, Target Achievement
    cards_cfg=[
        ("Total Revenue",       "Total Revenue",      TEAL),
        ("Total Profit",        "Total Profit",       GREEN),
        ("Total Orders",        "Total Orders",       BLUE),
        ("Avg Order Value",     "Avg Order Value",    YELLOW),
        ("Return Rate %",       "Return Rate",        RED),
        ("Target Achievement %","Target Achievement", PURPLE),
    ]
    result=[]
    for i,(measure,label,accent) in enumerate(cards_cfg):
        result.append(card_measure(10+i*(CW+7),y,CW,CH,measure,label,t+i*10,accent))
    return result

# ── PAGE 1: Executive Summary ─────────────────────────────────────────────────
p1=page_header("Executive Summary",0)+kpi_cards(104,100)+[
    # Revenue Trend: Month vs Net Sales, legend=Year (current vs prior year)
    line_chart(10,212,PW-20,195,
        "Sales","s","Month","Sales","s","Net Sales",0,"Net Sales",600,
        "Sales","s","Year",title="Revenue Trend — Net Sales by Month & Year"),
    # Sales by Category (horizontal bar)
    bar(10,416,400,370,
        "Sales","s","Category","Sales","s","Net Sales",0,"Net Sales",700,
        "clusteredBarChart",title="Sales by Category"),
    # Sales Channel Mix (donut)
    donut(418,416,408,370,
          "Sales","s","Sales Channel","Sales","s","Net Sales",0,"Net Sales",800,
          title="Sales Channel Mix"),
    # Order Status Distribution (donut)
    donut(834,416,436,370,
          "Sales","s","Order Status","Sales","s","Order ID",3,"Orders",900,
          title="Order Status Distribution"),
]

# ── PAGE 2: Sales Performance ─────────────────────────────────────────────────
p2=page_header("Sales Performance",0)+kpi_cards(104,100)+[
    # Monthly Orders Heatmap (matrix)
    heatmap(10,212,PW-20,185,600),
    # Sales by Country (joined via Customers table)
    bar(10,406,616,283,
        "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,
        "clusteredColumnChart",title="Sales by Country"),
    # Payment Method Breakdown
    bar(634,406,636,283,
        "Sales","s","Payment Method","Sales","s","Order ID",3,"Orders",800,
        "clusteredColumnChart",title="Payment Method Breakdown"),
    # Quarterly Revenue by Year
    bar(10,697,PW-20,93,
        "Sales","s","Quarter","Sales","s","Net Sales",0,"Net Sales",900,
        "clusteredColumnChart","Sales","s","Year",title="Quarterly Revenue by Year"),
]

# ── PAGE 3: Product Analysis ──────────────────────────────────────────────────
p3=page_header("Product Analysis",0)+kpi_cards(104,100)+[
    # Top Products by Net Sales
    bar(10,212,620,285,
        "Products","p","Product Name","Sales","s","Net Sales",0,"Net Sales",600,
        "clusteredBarChart",title="Top Products by Net Sales"),
    # Profit Margin % by Category
    bar(638,212,632,285,
        "Sales","s","Category","Sales","s","Profit Margin %",1,"Avg Margin",700,
        "clusteredColumnChart",title="Profit Margin % by Category"),
    # Category Revenue vs Profit (grouped: Net Sales + Profit)
    bar(10,505,PW-20,280,
        "Sales","s","Category","Sales","s","Net Sales",0,"Net Sales",800,
        "clusteredColumnChart","Sales","s","Profit",title="Category Revenue vs Profit"),
]

# ── PAGE 4: Customer Insights ─────────────────────────────────────────────────
p4=page_header("Customer Insights",0)+kpi_cards(104,100)+[
    # Customer Segment Revenue (pie)
    pie_chart(10,212,390,285,
              "Customers","c","Segment","Sales","s","Net Sales",0,"Net Sales",600,
              title="Customer Segment Revenue"),
    # Sales by Customer Country
    bar(408,212,862,285,
        "Customers","c","Country","Sales","s","Net Sales",0,"Net Sales",700,
        "clusteredBarChart",title="Sales by Customer Country"),
    # Orders by Segment & Status (stacked)
    bar(10,505,620,280,
        "Customers","c","Segment","Sales","s","Order ID",3,"Orders",800,
        "clusteredColumnChart","Sales","s","Order Status",title="Orders by Segment & Status"),
    # Avg Credit Limit by Segment
    bar(638,505,632,280,
        "Customers","c","Segment","Customers","c","Credit Limit",1,"Avg Credit",900,
        "clusteredColumnChart",title="Avg Credit Limit by Segment"),
]

# ── PAGE 5: Team Performance ──────────────────────────────────────────────────
p5=page_header("Team Performance",0)+kpi_cards(104,100)+[
    # Team Sales vs Target (grouped: Net Sales + Sales Target)
    bar(10,212,PW-20,255,
        "Users","u","Name","Sales","s","Net Sales",0,"Net Sales",600,
        "clusteredColumnChart","Users","u","Sales Target",title="Team Performance: Sales vs Target"),
    # Sales by Location
    bar(10,475,616,308,
        "Users","u","Location","Sales","s","Net Sales",0,"Net Sales",700,
        "clusteredBarChart",title="Sales by Location"),
    # Team member details table
    team_table(634,475,636,308,800),
]

# ── Custom Theme (comprehensive, matches HTML palette) ────────────────────────
THEME={
    "name":"SalesAnalyticsTheme",
    "dataColors":PALETTE,
    "good":"#00B050","neutral":"#F2C80F","bad":"#FD625E",
    "maximum":"#01B8AA","center":"#F2C80F","minimum":"#FD625E",
    "null":"#374649",
    "background":"#FFFFFF","foreground":"#252423","tableAccent":"#01B8AA",
    "visualStyles":{
        "*":{"*":{
            "fontFamily":[{"value":"Segoe UI"}],
            "fontSize":[{"value":11}],
            "background":[{"color":{"solid":{"color":"#FFFFFF"}}}],
        }},
        "card":{"*":{
            "labels":[{"color":{"solid":{"color":"#252423"}},"fontSize":24,"bold":True,"fontFamily":"Segoe UI"}],
            "categoryLabels":[{"show":True,"color":{"solid":{"color":"#5F6B6D"}},"fontSize":10,"fontFamily":"Segoe UI"}],
            "background":[{"show":True,"color":{"solid":{"color":"#FFFFFF"}},"transparency":0}],
            "border":[{"show":True}],
        }},
        "clusteredBarChart":{"*":{"dataColors":[{"value":PALETTE}]}},
        "clusteredColumnChart":{"*":{"dataColors":[{"value":PALETTE}]}},
        "lineChart":{"*":{"dataColors":[{"value":PALETTE}]}},
        "donutChart":{"*":{"dataColors":[{"value":PALETTE}]}},
        "pieChart":{"*":{"dataColors":[{"value":PALETTE}]}},
    }
}
THEME_PATH="Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json"

# ── Section builder ───────────────────────────────────────────────────────────
def section(sid,name,display,ordinal,visuals):
    cfg={"page":{"background":{"color":{"solid":{"color":LTGRAY}},"transparency":0}}}
    return {"id":sid,"name":name,"displayName":display,"ordinal":ordinal,
            "visualContainers":visuals,"filters":"[]","config":json.dumps(cfg),
            "displayOption":1,"width":PW,"height":PH}

# ── Report Layout ─────────────────────────────────────────────────────────────
layout={
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

layout_bytes =json.dumps(layout,ensure_ascii=False).encode("utf-16-le")
theme_bytes  =json.dumps(THEME, ensure_ascii=False).encode("utf-8")
schema_bytes2=schema_bytes  # already built above

# Get base theme from existing PBIX
base_theme=b""
src="/tmp/pbix_v3/source.pbix"
if os.path.exists(src):
    with zipfile.ZipFile(src) as z:
        for n in z.namelist():
            if "CY23SU11" in n: base_theme=z.read(n); break

content_types="""<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/DataModelSchema"   ContentType="application/json"/>
  <Override PartName="/DiagramLayout"     ContentType="application/json"/>
  <Override PartName="/Report/Layout"     ContentType="application/json"/>
  <Override PartName="/Settings"          ContentType="application/json"/>
  <Override PartName="/Metadata"          ContentType="application/json"/>
  <Override PartName="/Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json" ContentType="application/json"/>
  <Override PartName="/Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json" ContentType="application/json"/>
</Types>"""

diagram=json.dumps({"version":1,"diagrams":[{"ordinal":0,"scrollPosition":{"x":0,"y":0},"zoomValue":100,
    "nodes":[
        {"location":{"x":100,"y":100},"nodeIndex":"Sales",    "size":{"height":200,"width":200},"zIndex":1},
        {"location":{"x":400,"y":100},"nodeIndex":"Customers","size":{"height":200,"width":200},"zIndex":2},
        {"location":{"x":700,"y":100},"nodeIndex":"Users",    "size":{"height":200,"width":200},"zIndex":3},
        {"location":{"x":400,"y":350},"nodeIndex":"Products", "size":{"height":200,"width":200},"zIndex":4},
    ]}]})

with zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED) as z:
    z.writestr("Version",             b"3.0")
    z.writestr("[Content_Types].xml", content_types.encode("utf-8"))
    z.writestr("DataModelSchema",     schema_bytes2)
    z.writestr("DiagramLayout",       diagram.encode("utf-8"))
    z.writestr("Report/Layout",       layout_bytes)
    z.writestr("Settings",            b'{"Version":3,"AutoRecoveryEnabled":false}')
    z.writestr("Metadata",            b'{"version":"4.0","settings":{}}')
    z.writestr("SecurityBindings",    b"")
    z.writestr(THEME_PATH,            theme_bytes)
    if base_theme:
        z.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",base_theme)

size=os.path.getsize(OUT)
print(f"\nWritten: {OUT}  ({size:,} bytes)")
with zipfile.ZipFile(OUT) as z:
    print("Contents:")
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")
    L2=json.loads(z.read("Report/Layout").decode("utf-16-le"))
    print("\nPages:")
    for s in L2["sections"]:
        print(f"  {s['ordinal']}: {s['displayName']}  ({len(s['visualContainers'])} visuals)")
print("\nOpen in Power BI Desktop (File > Open > *.pbit) → Refresh → looks like HTML dashboard")

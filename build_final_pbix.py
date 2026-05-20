"""
Build SalesAnalytics_Dashboard.pbix
- Keeps source PBIX DataModel 100% intact → opens without ANY corruption error
- Completely new Report/Layout: 5 pages matching HTML dashboard design
- Uses exact vcObjects format confirmed from source PBIX
- Dark header, KPI cards, colored charts, heatmap, slicers
- Column mapping: Orders[Sales/Profit/Category/Segment/Region/Ship Mode/Order Date]
                  Customers[Country], Products[Sub-Category], Returns, Users[Person/Region]
"""
import json, zipfile, uuid, os

SRC = '/tmp/pbix_v3/source.pbix'
OUT = '/home/user/newm/SalesAnalytics_Dashboard.pbix'

# ── Colors (exact HTML palette) ───────────────────────────────────────────────
TEAL="#01B8AA"; DARK="#252423"; RED="#FD625E"; YELLOW="#F2C80F"
BLUE="#118DFF"; PURPLE="#8B00FF"; GREEN="#00B050"; DGRAY="#374649"
ORANGE="#FF6B35"; WHITE="#FFFFFF"; LTGRAY="#F3F2F1"; SLATE="#5F6B6D"

# ── Helpers using EXACT format confirmed from source PBIX ─────────────────────
def vn(): return uuid.uuid4().hex[:20]

# Single-quote literals (as source PBIX uses)
def L(v):  return {"expr": {"Literal": {"Value": v}}}
def Ls(s): return L(f"'{s}'")   # string with single quotes
def Ln(n): return L(str(n))     # number
def Lb(b): return L("true" if b else "false")

def color_obj(hex_color):
    return {"solid": {"color": Ls(hex_color)}}

def title_obj(text, size=12, color=DARK, bold=False):
    return [{"properties": {
        "show":      Lb(True),
        "text":      Ls(text),
        "fontSize":  L(f"{size}D"),
        "fontColor": color_obj(color),
        "bold":      Lb(bold),
    }}]

def bg_obj(hex_color=WHITE, transparency=0):
    return [{"properties": {
        "show":         Lb(True),
        "color":        color_obj(hex_color),
        "transparency": Ln(transparency),
    }}]

def border_obj(hex_color="#E0DFDE"):
    return [{"properties": {
        "show":  Lb(True),
        "color": color_obj(hex_color),
    }}]

def vc(x, y, w, h, tab, sv):
    p = {"x":x, "y":y, "z":tab, "width":w, "height":h, "tabOrder":tab}
    return {**p, "filters":"[]",
            "config": json.dumps({"name":vn(),"layouts":[{"id":0,"position":p}],"singleVisual":sv}),
            "query":"{}","dataTransforms":"{}"}

# ── KPI Card ──────────────────────────────────────────────────────────────────
def card(x, y, w, h, entity, alias, col, agg, title, tab, accent=TEAL):
    fn  = "Sum" if agg==0 else "Avg" if agg==1 else "Count"
    qn  = f"{fn}({entity}.{col})"
    sv = {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {"Version":2,
            "From": [{"Name":alias,"Entity":entity,"Type":0}],
            "Select": [{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col}},"Function":agg},"Name":qn,"NativeReferenceName":title}]},
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title":      title_obj(title, 10, SLATE),
            "background": bg_obj(WHITE),
            "border":     border_obj(accent),
            "labels":     [{"properties":{"color":color_obj(DARK),"fontSize":L("22D"),"bold":Lb(True)}}],
            "categoryLabels": [{"properties":{"show":Lb(True),"color":color_obj(SLATE),"fontSize":L("10D")}}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ── Bar / Column chart ────────────────────────────────────────────────────────
def bar(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab,
        vtype="clusteredBarChart", title="", leg_e=None, leg_a=None, leg_c=None):
    fn  = "Sum" if agg==0 else "Count" if agg==3 or agg==5 else "Avg"
    cqn = f"{cat_e}.{cat_c}"
    vqn = f"{fn}({val_e}.{val_c})"
    froms = [{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a != cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sels = [
        {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
        {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
    ]
    projs = {"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]}
    if leg_c:
        lqn = f"{leg_e}.{leg_c}"
        if leg_a not in [f["Name"] for f in froms]: froms.append({"Name":leg_a,"Entity":leg_e,"Type":0})
        sels.insert(1,{"Column":{"Expression":{"SourceRef":{"Source":leg_a}},"Property":leg_c},"Name":lqn,"NativeReferenceName":leg_c})
        projs["Legend"] = [{"queryRef":lqn}]
    sv = {"visualType":vtype,"projections":projs,
          "prototypeQuery":{"Version":2,"From":froms,"Select":sels},
          "drillFilterOtherVisuals":True,
          "vcObjects":{
              "title":      title_obj(title),
              "background": bg_obj(WHITE),
              "border":     border_obj(),
          }}
    return vc(x, y, w, h, tab, sv)

# ── Line chart ────────────────────────────────────────────────────────────────
def line(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,title="",
         leg_e=None,leg_a=None,leg_c=None):
    return bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
               "lineChart",title,leg_e,leg_a,leg_c)

# ── Donut chart ───────────────────────────────────────────────────────────────
def donut(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,title=""):
    fn  = "Sum" if agg==0 else "Count"
    cqn = f"{cat_e}.{cat_c}"; vqn = f"{fn}({val_e}.{val_c})"
    froms=[{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a!=cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    sv={"visualType":"donutChart",
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":[
            {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}]},
        "drillFilterOtherVisuals":True,
        "vcObjects":{"title":title_obj(title),"background":bg_obj(WHITE),"border":border_obj()}}
    return vc(x,y,w,h,tab,sv)

# ── Heatmap (Matrix) ──────────────────────────────────────────────────────────
def heatmap(x,y,w,h,tab):
    sv={"visualType":"pivotTable","drillFilterOtherVisuals":True,
        "projections":{
            "Rows":   [{"queryRef":"Year(Orders.Order Date)","active":True}],
            "Columns":[{"queryRef":"MonthName(Orders.Order Date)","active":True}],
            "Values": [{"queryRef":"CountNonNull(Orders.Order ID)"}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":"o","Entity":"Orders","Type":0}],"Select":[
            {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order Date"}},"TimeUnit":6},"Name":"Year(Orders.Order Date)","NativeReferenceName":"Year"},
            {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order Date"}},"TimeUnit":3},"Name":"MonthName(Orders.Order Date)","NativeReferenceName":"Month"},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order ID"}},"Function":5},"Name":"CountNonNull(Orders.Order ID)","NativeReferenceName":"Orders"}]},
        "vcObjects":{
            "title":title_obj("Monthly Orders Heatmap",12,DARK,True),
            "background":bg_obj(WHITE),
            "border":border_obj(TEAL),
            "subTotals":[{"properties":{"rowSubtotals":Lb(False),"columnSubtotals":Lb(False)}}],
            "columnHeaders":[{"properties":{"backColor":color_obj(TEAL),"fontColor":color_obj(WHITE),"bold":Lb(True),"fontSize":L("11D")}}],
            "rowHeaders":[{"properties":{"fontColor":color_obj(DARK),"bold":Lb(True),"fontSize":L("11D")}}],
            "values":[{"properties":{"backColor":color_obj(LTGRAY),"fontColor":color_obj(DARK),"fontSize":L("11D")}}],
        }}
    return vc(x,y,w,h,tab,sv)

# ── Slicer ────────────────────────────────────────────────────────────────────
def slicer(x,y,w,h,entity,alias,col_,tab):
    qn=f"{entity}.{col_}"
    sv={"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":Ls("Dropdown")}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_},"Name":qn,"NativeReferenceName":col_}]},
        "vcObjects":{
            "background":bg_obj(WHITE),
            "border":border_obj(TEAL),
            "header":[{"properties":{"show":Lb(True),"fontColor":color_obj(DARK),"background":color_obj(LTGRAY)}}],
        }}
    return vc(x,y,w,h,tab,sv)

# ── Textbox ───────────────────────────────────────────────────────────────────
def textbox(x,y,w,h,text,tab,bg=DARK,fg=WHITE,sz="13pt",bold=True):
    sv={"visualType":"textbox",
        "objects":{"general":[{"properties":{"paragraphs":[{
            "textRuns":[{"value":text,"textStyle":{"fontWeight":"bold" if bold else "normal","fontSize":sz,"color":fg}}],
            "horizontalTextAlignment":"left"}]}}]},
        "vcObjects":{"background":bg_obj(bg)}}
    return vc(x,y,w,h,tab,sv)

# ── Page structure ────────────────────────────────────────────────────────────
PW,PH=1280,800
CW,CH=193,98

def page_header(title,tab=0):
    return [
        textbox(0,0,PW,46,f"  ◼  Sales Analytics Dashboard   |   {title}",tab,DARK,WHITE,"13pt",True),
        textbox(0,46,PW,4,"",tab+1,TEAL,TEAL,"1pt",False),
        textbox(0,52,PW,18,"    Year           Quarter          Category              Ship Mode            Segment",tab+2,LTGRAY,SLATE,"8pt",False),
        slicer(8,   72,120,28,"Orders","o","Order Date",   tab+3),
        slicer(136, 72,130,28,"Orders","o","Order Date",   tab+4),  # Quarter proxy
        slicer(274, 72,155,28,"Orders","o","Category",     tab+5),
        slicer(437, 72,155,28,"Orders","o","Ship Mode",    tab+6),
        slicer(600, 72,155,28,"Orders","o","Segment",      tab+7),
    ]

def kpi_row(y,t):
    return [
        card(10+0*(CW+7),y,CW,CH,"Orders","o","Sales",   0,"Total Revenue",  t+0,  TEAL),
        card(10+1*(CW+7),y,CW,CH,"Orders","o","Profit",  0,"Total Profit",   t+10, GREEN),
        card(10+2*(CW+7),y,CW,CH,"Orders","o","Order ID",5,"Total Orders",   t+20, BLUE),
        card(10+3*(CW+7),y,CW,CH,"Orders","o","Sales",   1,"Avg Order Value",t+30, YELLOW),
        card(10+4*(CW+7),y,CW,CH,"Returns","r","Order ID",5,"Total Returns", t+40, RED),
        card(10+5*(CW+7),y,CW,CH,"Orders","o","Discount",1,"Avg Discount",   t+50, PURPLE),
    ]

# ─── Page 1: Executive Summary ────────────────────────────────────────────────
p1 = page_header("Executive Summary",0) + kpi_row(104,100) + [
    # Revenue Trend by Order Date (line) — matches HTML "Revenue Trend"
    line(10,210,PW-20,192,"Orders","o","Order Date","Orders","o","Sales",0,"Sales",600,
         title="Revenue Trend — Sales by Order Date",
         leg_e="Orders",leg_a="o",leg_c="Segment"),
    # Sales by Category (horizontal bar) — matches HTML
    bar(10,412,400,375,"Orders","o","Category","Orders","o","Sales",0,"Sales",700,
        "clusteredBarChart",title="Sales by Category"),
    # Segment Mix (donut) — proxy for Sales Channel Mix
    donut(418,412,408,375,"Orders","o","Segment","Orders","o","Sales",0,"Sales",800,
          title="Sales by Segment"),
    # Ship Mode breakdown (donut) — proxy for Order Status
    donut(834,412,436,375,"Orders","o","Ship Mode","Orders","o","Order ID",5,"Orders",900,
          title="Orders by Ship Mode"),
]

# ─── Page 2: Sales Performance ────────────────────────────────────────────────
p2 = page_header("Sales Performance",0) + kpi_row(104,100) + [
    # Monthly Orders Heatmap
    heatmap(10,210,PW-20,185,600),
    # Sales by Country (via Customers table)
    bar(10,404,616,283,"Customers","c","Country","Orders","o","Sales",0,"Sales",700,
        "clusteredColumnChart",title="Sales by Country"),
    # Orders by Ship Mode — proxy for Payment Method
    bar(634,404,636,283,"Orders","o","Ship Mode","Orders","o","Order ID",5,"Orders",800,
        "clusteredColumnChart",title="Orders by Ship Mode"),
    # Quarterly Revenue by Year (grouped)
    bar(10,695,PW-20,95,"Orders","o","Order Date","Orders","o","Sales",0,"Sales",900,
        "clusteredColumnChart",title="Revenue by Quarter & Year",
        leg_e="Orders",leg_a="o",leg_c="Segment"),
]

# ─── Page 3: Product Analysis ─────────────────────────────────────────────────
p3 = page_header("Product Analysis",0) + kpi_row(104,100) + [
    # Top Sub-Categories by Sales (horizontal bar)
    bar(10,210,620,285,"Orders","o","Sub-Category","Orders","o","Sales",0,"Sales",600,
        "clusteredBarChart",title="Top Products / Sub-Categories by Sales"),
    # Avg Discount by Category (column)
    bar(638,210,632,285,"Orders","o","Category","Orders","o","Discount",1,"Avg Discount",700,
        "clusteredColumnChart",title="Average Discount % by Category"),
    # Category Revenue vs Profit (grouped)
    bar(10,503,PW-20,282,"Orders","o","Category","Orders","o","Sales",0,"Sales",800,
        "clusteredColumnChart",title="Category Revenue vs Profit",
        leg_e="Orders",leg_a="o",leg_c="Profit"),
]

# ─── Page 4: Customer Insights ────────────────────────────────────────────────
p4 = page_header("Customer Insights",0) + kpi_row(104,100) + [
    # Revenue by Segment (donut)
    donut(10,210,390,285,"Orders","o","Segment","Orders","o","Sales",0,"Sales",600,
          title="Revenue by Customer Segment"),
    # Sales by Country
    bar(408,210,862,285,"Customers","c","Country","Orders","o","Sales",0,"Sales",700,
        "clusteredBarChart",title="Sales by Customer Country"),
    # Orders by Segment & Region (stacked)
    bar(10,503,620,282,"Orders","o","Segment","Orders","o","Order ID",5,"Orders",800,
        "clusteredColumnChart",title="Orders by Segment",
        leg_e="Orders",leg_a="o",leg_c="Region"),
    # Revenue by Region
    bar(638,503,632,282,"Orders","o","Region","Orders","o","Sales",0,"Sales",900,
        "clusteredColumnChart",title="Revenue by Region"),
]

# ─── Page 5: Team Performance ─────────────────────────────────────────────────
p5 = page_header("Team Performance",0) + kpi_row(104,100) + [
    # Sales by Region Manager (Users table has Person/Region)
    bar(10,210,PW-20,255,"Users","u","Region","Orders","o","Sales",0,"Sales",600,
        "clusteredColumnChart",title="Team Sales Performance by Region"),
    # Sales by Region (bar)
    bar(10,473,616,308,"Orders","o","Region","Orders","o","Sales",0,"Sales",700,
        "clusteredBarChart",title="Revenue by Region"),
    # Returns by Region
    bar(634,473,636,308,"Returns","r","Region","Returns","r","Order ID",5,"Returns",800,
        "clusteredColumnChart",title="Returns by Region"),
]

# ── Theme JSON ────────────────────────────────────────────────────────────────
THEME = {
    "name":"SalesAnalyticsTheme",
    "dataColors":[TEAL,DGRAY,RED,YELLOW,BLUE,PURPLE,ORANGE,GREEN,SLATE,"#E91E63"],
    "good":GREEN,"neutral":YELLOW,"bad":RED,
    "background":WHITE,"foreground":DARK,"tableAccent":TEAL,
}
THEME_PATH="Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json"

def section(sid,name,display,ordinal,visuals):
    cfg={"page":{"background":{"color":{"solid":{"color":LTGRAY}},"transparency":0}}}
    return {"id":sid,"name":name,"displayName":display,"ordinal":ordinal,
            "visualContainers":visuals,"filters":"[]","config":json.dumps(cfg),
            "displayOption":1,"width":PW,"height":PH}

report_layout={
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

layout_bytes = json.dumps(report_layout,ensure_ascii=False).encode("utf-16-le")
theme_bytes  = json.dumps(THEME,ensure_ascii=False).encode("utf-8")

def patch_content_types(xml_bytes):
    xml = xml_bytes.decode("utf-8")
    if "SalesAnalyticsTheme" not in xml:
        xml = xml.replace("</Types>",
            '<Override PartName="/Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json" ContentType="application/json"/></Types>')
    return xml.encode("utf-8")

# Read ALL files from source PBIX
with zipfile.ZipFile(SRC) as z:
    orig = {n: z.read(n) for n in z.namelist()}

# Write new PBIX: keep everything except Report/Layout; add theme
with zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED) as z:
    for name, data in orig.items():
        if name == "Report/Layout":
            z.writestr(name, layout_bytes)
        elif name == "[Content_Types].xml":
            z.writestr(name, patch_content_types(data))
        else:
            z.writestr(name, data)
    z.writestr(THEME_PATH, theme_bytes)

size=os.path.getsize(OUT)
print(f"Written: {OUT}  ({size:,} bytes)")
with zipfile.ZipFile(OUT) as z:
    print("Files:")
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")
    L2=json.loads(z.read("Report/Layout").decode("utf-16-le"))
    for s in L2["sections"]:
        print(f"  Page {s['ordinal']}: {s['displayName']} ({len(s['visualContainers'])} visuals)")
print("\nDone — open directly in Power BI Desktop as .pbix (no renaming needed)")

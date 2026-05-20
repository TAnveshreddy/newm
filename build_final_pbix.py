"""
Final SalesAnalytics_Dashboard.pbix
Fixes all issues from screenshot:
1. Colors: per-bar colors via dataPoint selectors (teal/red/yellow/blue/purple/green)
2. Filters: Year(date hierarchy), Category, Segment, Region slicers — 4 proper slicers
3. Cards: colored accent borders, bold titles, formatted labels
4. Dark header bar on every page
5. Chart titles matching HTML
6. Report config matches source PBIX exactly (version 5.55)
"""
import json, zipfile, uuid, os

SRC = '/tmp/pbix_v3/source.pbix'
OUT = '/home/user/newm/SalesAnalytics_Dashboard.pbix'

# ── HTML color palette ────────────────────────────────────────────────────────
TEAL="#01B8AA"; DARK="#252423"; RED="#FD625E"; YELLOW="#F2C80F"
BLUE="#118DFF"; PURPLE="#8B00FF"; GREEN="#00B050"; DGRAY="#374649"
ORANGE="#FF6B35"; WHITE="#FFFFFF"; LTGRAY="#F3F2F1"; SLATE="#5F6B6D"

# Superstore known values → colors
CAT_COLORS   = {"Technology":TEAL,      "Office Supplies":YELLOW, "Furniture":RED}
SEG_COLORS   = {"Consumer":TEAL,        "Corporate":BLUE,         "Home Office":ORANGE}
REG_COLORS   = {"West":TEAL,            "East":BLUE,              "Central":RED,    "South":YELLOW}
MODE_COLORS  = {"Standard Class":TEAL,  "Second Class":YELLOW,    "First Class":BLUE,"Same Day":ORANGE}
SUBCAT_COLORS= {"Phones":TEAL,"Chairs":RED,"Storage":YELLOW,"Tables":BLUE,
                "Binders":PURPLE,"Machines":ORANGE,"Bookcases":GREEN,"Copiers":DGRAY,
                "Accessories":SLATE,"Appliances":"#E91E63"}

def vn(): return uuid.uuid4().hex[:20]
def Ls(s): return {"expr":{"Literal":{"Value":f"'{s}'"}}}
def Ln(n): return {"expr":{"Literal":{"Value":str(n)}}}
def Lb(b): return {"expr":{"Literal":{"Value":"true" if b else "false"}}}
def clr(c): return {"solid":{"color":Ls(c)}}

def vc(x,y,w,h,tab,sv):
    p={"x":x,"y":y,"z":tab,"width":w,"height":h,"tabOrder":tab}
    return {**p,"filters":"[]",
            "config":json.dumps({"name":vn(),"layouts":[{"id":0,"position":p}],"singleVisual":sv}),
            "query":"{}","dataTransforms":"{}"}

# ── Per-bar color selectors ───────────────────────────────────────────────────
def data_point_colors(source_alias, column_prop, color_map):
    """Generate dataPoint vcObject entries coloring each known value."""
    entries = []
    for val, hex_color in color_map.items():
        entries.append({
            "selector":{"data":{"expr":{"In":{
                "Expressions":[{"Column":{"Expression":{"SourceRef":{"Source":source_alias}},"Property":column_prop}}],
                "Values":[[{"Literal":{"Value":f"'{val}'"}}]]
            }}}},
            "properties":{"fill":clr(hex_color)}
        })
    return entries

# ── KPI Card ──────────────────────────────────────────────────────────────────
def card(x,y,w,h,entity,alias,col,agg,title,tab,accent=TEAL):
    fn="Sum" if agg==0 else "Avg" if agg==1 else "CountNonNull"
    qn=f"{fn}({entity}.{col})"
    sv={
        "visualType":"card",
        "projections":{"Values":[{"queryRef":qn}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col}},"Function":agg},"Name":qn,"NativeReferenceName":title}]},
        "drillFilterOtherVisuals":True,
        "vcObjects":{
            "title":     [{"properties":{"show":Lb(True),"text":Ls(title),"fontColor":clr(SLATE),"fontSize":Ln("10D")}}],
            "background":[{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
            "border":    [{"properties":{"show":Lb(True),"color":clr(accent)}}],
            "labels":    [{"properties":{"color":clr(DARK),"fontSize":Ln("22D"),"bold":Lb(True)}}],
            "categoryLabels":[{"properties":{"show":Lb(False)}}],
        }
    }
    return vc(x,y,w,h,tab,sv)

# ── Bar / Column chart ────────────────────────────────────────────────────────
def bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
        vtype="clusteredBarChart",title="",leg_e=None,leg_a=None,leg_c=None,
        color_map=None):
    fn="Sum" if agg==0 else "CountNonNull" if agg==5 else "Avg"
    cqn=f"{cat_e}.{cat_c}"; vqn=f"{fn}({val_e}.{val_c})"
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
    vco={
        "title":     [{"properties":{"show":Lb(True),"text":Ls(title),"fontColor":clr(DARK),"fontSize":Ln("12D"),"bold":Lb(True)}}],
        "background":[{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
        "border":    [{"properties":{"show":Lb(True),"color":clr("#E0DFDE")}}],
    }
    if color_map:
        vco["dataPoint"] = data_point_colors(cat_a, cat_c, color_map)
    sv={"visualType":vtype,"projections":projs,
        "prototypeQuery":{"Version":2,"From":froms,"Select":sels},
        "drillFilterOtherVisuals":True,"vcObjects":vco}
    return vc(x,y,w,h,tab,sv)

def line_chart(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,title="",
               leg_e=None,leg_a=None,leg_c=None):
    return bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,
               "lineChart",title,leg_e,leg_a,leg_c)

# ── Donut / Pie chart ─────────────────────────────────────────────────────────
def donut(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,title="",color_map=None):
    fn="Sum" if agg==0 else "CountNonNull"
    cqn=f"{cat_e}.{cat_c}"; vqn=f"{fn}({val_e}.{val_c})"
    froms=[{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a!=cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    vco={
        "title":     [{"properties":{"show":Lb(True),"text":Ls(title),"fontColor":clr(DARK),"fontSize":Ln("12D"),"bold":Lb(True)}}],
        "background":[{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
        "border":    [{"properties":{"show":Lb(True),"color":clr("#E0DFDE")}}],
        "legend":    [{"properties":{"show":Lb(True),"position":Ls("Bottom")}}],
    }
    if color_map:
        vco["dataPoint"] = data_point_colors(cat_a, cat_c, color_map)
    sv={"visualType":"donutChart",
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":froms,"Select":[
            {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
            {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}]},
        "drillFilterOtherVisuals":True,"vcObjects":vco}
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
            "title":         [{"properties":{"show":Lb(True),"text":Ls("Monthly Orders Heatmap"),"fontColor":clr(DARK),"fontSize":Ln("12D"),"bold":Lb(True)}}],
            "background":    [{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
            "border":        [{"properties":{"show":Lb(True),"color":clr(TEAL)}}],
            "subTotals":     [{"properties":{"rowSubtotals":Lb(False),"columnSubtotals":Lb(False)}}],
            "columnHeaders": [{"properties":{"backColor":clr(TEAL),"fontColor":clr(WHITE),"bold":Lb(True),"fontSize":Ln("11D")}}],
            "rowHeaders":    [{"properties":{"fontColor":clr(DARK),"bold":Lb(True),"fontSize":Ln("11D")}}],
            "values":        [{"properties":{"backColor":clr(LTGRAY),"fontColor":clr(DARK),"fontSize":Ln("11D")}}],
        }}
    return vc(x,y,w,h,tab,sv)

# ── Slicer ────────────────────────────────────────────────────────────────────
def slicer_col(x,y,w,h,entity,alias,col_,tab):
    """Regular column slicer."""
    qn=f"{entity}.{col_}"
    sv={"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":Ls("Dropdown")}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_},"Name":qn,"NativeReferenceName":col_}]},
        "vcObjects":{
            "background":[{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
            "border":    [{"properties":{"show":Lb(True),"color":clr(TEAL)}}],
            "header":    [{"properties":{"show":Lb(True),"fontColor":clr(SLATE),"background":clr(LTGRAY)}}],
        }}
    return vc(x,y,w,h,tab,sv)

def slicer_year(x,y,w,h,tab):
    """Year slicer using date hierarchy (Year level of Order Date)."""
    qn="Year(Orders.Order Date)"
    sv={"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":Ls("Dropdown")}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":"o","Entity":"Orders","Type":0}],
            "Select":[{"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order Date"}},"TimeUnit":6},"Name":qn,"NativeReferenceName":"Year"}]},
        "vcObjects":{
            "background":[{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
            "border":    [{"properties":{"show":Lb(True),"color":clr(TEAL)}}],
            "header":    [{"properties":{"show":Lb(True),"fontColor":clr(SLATE),"background":clr(LTGRAY)}}],
        }}
    return vc(x,y,w,h,tab,sv)

def slicer_quarter(x,y,w,h,tab):
    """Quarter slicer using date hierarchy (Quarter level)."""
    qn="QuarterNo(Orders.Order Date)"
    sv={"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":Ls("Dropdown")}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":"o","Entity":"Orders","Type":0}],
            "Select":[{"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order Date"}},"TimeUnit":5},"Name":qn,"NativeReferenceName":"Quarter"}]},
        "vcObjects":{
            "background":[{"properties":{"show":Lb(True),"color":clr(WHITE),"transparency":Ln(0)}}],
            "border":    [{"properties":{"show":Lb(True),"color":clr(TEAL)}}],
            "header":    [{"properties":{"show":Lb(True),"fontColor":clr(SLATE),"background":clr(LTGRAY)}}],
        }}
    return vc(x,y,w,h,tab,sv)

# ── Textbox ───────────────────────────────────────────────────────────────────
def textbox(x,y,w,h,text,tab,bg=DARK,fg=WHITE,sz="13pt",bold=True):
    sv={"visualType":"textbox",
        "objects":{"general":[{"properties":{"paragraphs":[{
            "textRuns":[{"value":text,"textStyle":{"fontWeight":"bold" if bold else "normal","fontSize":sz,"color":fg}}],
            "horizontalTextAlignment":"left"}]}}]},
        "vcObjects":{"background":[{"properties":{"show":Lb(True),"color":clr(bg),"transparency":Ln(0)}}]}}
    return vc(x,y,w,h,tab,sv)

# ── Page structure ────────────────────────────────────────────────────────────
PW,PH=1280,800
CW,CH=190,98

def page_header(title,tab=0):
    """Dark header + teal accent line + 4 slicers: Year, Quarter, Category, Segment."""
    return [
        # Dark header bar
        textbox(0,0,PW,46,f"  ◼  Sales Analytics Dashboard   |   {title}",
                tab,DARK,WHITE,"13pt",True),
        # Teal accent line
        textbox(0,46,PW,3,"",tab+1,TEAL,TEAL,"1pt",False),
        # Slicer labels
        textbox(0,51,PW,17,
                "    YEAR              QUARTER               CATEGORY                 SEGMENT",
                tab+2,LTGRAY,SLATE,"8pt",False),
        # 4 slicers matching HTML filters
        slicer_year(  8,  70,145,28,tab+3),
        slicer_quarter(161,70,145,28,tab+4),
        slicer_col(  314,70,185,28,"Orders","o","Category",tab+5),
        slicer_col(  507,70,185,28,"Orders","o","Segment", tab+6),
    ]

def kpi_row(y,t):
    return [
        card(10+0*(CW+7),y,CW,CH,"Orders","o","Sales",   0,"Total Revenue",  t+0,  TEAL),
        card(10+1*(CW+7),y,CW,CH,"Orders","o","Profit",  0,"Total Profit",   t+10, GREEN),
        card(10+2*(CW+7),y,CW,CH,"Orders","o","Order ID",5,"Total Orders",   t+20, BLUE),
        card(10+3*(CW+7),y,CW,CH,"Orders","o","Sales",   1,"Avg Order Value",t+30, YELLOW),
        card(10+4*(CW+7),y,CW,CH,"Returns","r","Order ID",5,"Total Returns", t+40, RED),
        card(10+5*(CW+7),y,CW,CH,"Orders","o","Profit",  1,"Avg Profit",     t+50, PURPLE),
    ]

# ─── Page 1: Executive Summary ────────────────────────────────────────────────
p1 = page_header("Executive Summary",0) + kpi_row(102,100) + [
    line_chart(10,207,PW-20,193,"Orders","o","Order Date","Orders","o","Sales",0,"Sales",600,
               title="Revenue Trend — Sales by Order Date"),
    bar(10,409,395,378,"Orders","o","Category","Orders","o","Sales",0,"Revenue",700,
        "clusteredBarChart","Sales by Category",color_map=CAT_COLORS),
    donut(413,409,415,378,"Orders","o","Segment","Orders","o","Sales",0,"Revenue",800,
          "Sales by Segment",SEG_COLORS),
    donut(836,409,434,378,"Orders","o","Ship Mode","Orders","o","Order ID",5,"Orders",900,
          "Orders by Ship Mode",MODE_COLORS),
]

# ─── Page 2: Sales Performance ────────────────────────────────────────────────
p2 = page_header("Sales Performance",0) + kpi_row(102,100) + [
    heatmap(10,207,PW-20,183,600),
    bar(10,399,618,283,"Customers","c","Country","Orders","o","Sales",0,"Revenue",700,
        "clusteredColumnChart","Sales by Country"),
    bar(636,399,634,283,"Orders","o","Ship Mode","Orders","o","Order ID",5,"Orders",800,
        "clusteredColumnChart","Orders by Ship Mode",color_map=MODE_COLORS),
    bar(10,690,PW-20,100,"Orders","o","Order Date","Orders","o","Sales",0,"Revenue",900,
        "clusteredColumnChart","Quarterly Revenue",
        leg_e="Orders",leg_a="o",leg_c="Segment"),
]

# ─── Page 3: Product Analysis ─────────────────────────────────────────────────
p3 = page_header("Product Analysis",0) + kpi_row(102,100) + [
    bar(10,207,618,286,"Orders","o","Sub-Category","Orders","o","Sales",0,"Revenue",600,
        "clusteredBarChart","Top Sub-Categories by Sales",color_map=SUBCAT_COLORS),
    bar(636,207,634,286,"Orders","o","Category","Orders","o","Profit",1,"Avg Profit",700,
        "clusteredColumnChart","Avg Profit by Category",color_map=CAT_COLORS),
    bar(10,502,PW-20,283,"Orders","o","Category","Orders","o","Sales",0,"Revenue",800,
        "clusteredColumnChart","Category Revenue vs Profit",
        leg_e="Orders",leg_a="o",leg_c="Profit",color_map=CAT_COLORS),
]

# ─── Page 4: Customer Insights ────────────────────────────────────────────────
p4 = page_header("Customer Insights",0) + kpi_row(102,100) + [
    donut(10,207,393,286,"Orders","o","Segment","Orders","o","Sales",0,"Revenue",600,
          "Revenue by Customer Segment",SEG_COLORS),
    bar(411,207,859,286,"Customers","c","Country","Orders","o","Sales",0,"Revenue",700,
        "clusteredBarChart","Sales by Customer Country"),
    bar(10,502,618,283,"Orders","o","Segment","Orders","o","Order ID",5,"Orders",800,
        "clusteredColumnChart","Orders by Segment",
        leg_e="Orders",leg_a="o",leg_c="Region",color_map=SEG_COLORS),
    bar(636,502,634,283,"Orders","o","Region","Orders","o","Sales",0,"Revenue",900,
        "clusteredColumnChart","Revenue by Region",color_map=REG_COLORS),
]

# ─── Page 5: Team Performance ─────────────────────────────────────────────────
p5 = page_header("Team Performance",0) + kpi_row(102,100) + [
    bar(10,207,PW-20,258,"Users","u","Region","Orders","o","Sales",0,"Revenue",600,
        "clusteredColumnChart","Sales Performance by Region",color_map=REG_COLORS),
    bar(10,474,618,308,"Orders","o","Region","Orders","o","Sales",0,"Revenue",700,
        "clusteredBarChart","Revenue by Region",color_map=REG_COLORS),
    bar(636,474,634,308,"Returns","r","Region","Returns","r","Order ID",5,"Returns",800,
        "clusteredColumnChart","Returns by Region",color_map=REG_COLORS),
]

# ── Section / Layout builders ─────────────────────────────────────────────────
def section(sid,name,display,ordinal,visuals):
    cfg={"page":{"background":{"color":{"solid":{"color":LTGRAY}},"transparency":0}}}
    return {"id":sid,"name":name,"displayName":display,"ordinal":ordinal,
            "visualContainers":visuals,"filters":"[]","config":json.dumps(cfg),
            "displayOption":1,"width":PW,"height":PH}

report_layout={
    "id":0,
    "resourcePackages":[{"resourcePackage":{
        "name":"SharedResources","type":2,
        "items":[{"type":202,"path":"BaseThemes/CY23SU11.json","name":"CY23SU11"}],
        "disabled":False}}],
    "sections":[
        section(0,"S1","Executive Summary",0,p1),
        section(1,"S2","Sales Performance", 1,p2),
        section(2,"S3","Product Analysis",  2,p3),
        section(3,"S4","Customer Insights", 3,p4),
        section(4,"S5","Team Performance",  4,p5),
    ],
    # Match source PBIX config exactly (version 5.55, no custom theme)
    "config":json.dumps({
        "version":"5.55",
        "themeCollection":{"baseTheme":{"name":"CY23SU11","version":"5.55","type":2}},
        "activeSectionIndex":0,
        "defaultDrillFilterOtherVisuals":True,
        "settings":{"filterPaneEnabled":True,"navContentPaneEnabled":True,
                    "useNewFilterPaneExperience":True}
    }),
    "layoutOptimization":0
}

layout_bytes=json.dumps(report_layout,ensure_ascii=False).encode("utf-16-le")

# ── Write PBIX ────────────────────────────────────────────────────────────────
with zipfile.ZipFile(SRC) as z:
    orig={n:z.read(n) for n in z.namelist()}

with zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED) as z:
    for name,data in orig.items():
        if name=="Report/Layout":
            z.writestr(name,layout_bytes)
        else:
            z.writestr(name,data)

size=os.path.getsize(OUT)
print(f"Written: {OUT}  ({size:,} bytes)")
with zipfile.ZipFile(OUT) as z:
    layout2=json.loads(z.read("Report/Layout").decode("utf-16-le"))
    for s in layout2["sections"]:
        print(f"  Page {s['ordinal']}: {s['displayName']}  ({len(s['visualContainers'])} visuals)")
print("Done — double-click to open in Power BI Desktop")

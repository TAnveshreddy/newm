"""
Build SalesAnalytics_Final_v2.pbix
- Keeps source PBIX DataModel 100% intact (no corruption)
- Rebuilds Report/Layout with 5 pages matching HTML design
- Uses available columns: Orders[Sales/Profit/Category/Region/Segment/
  Ship Mode/Order Date/Order ID/Customer ID], Customers[Segment/Customer Name],
  Products[Product ID], Returns[Order ID]
- Closest possible match to HTML layout using available schema
"""
import json, zipfile, uuid, os

SRC = '/tmp/pbix_v3/source.pbix'
OUT = '/home/user/newm/SalesAnalytics_Final_v2.pbix'

def vn(): return uuid.uuid4().hex[:20]

def vc(x, y, w, h, tab, sv_obj):
    p = {"x":x,"y":y,"z":tab,"width":w,"height":h,"tabOrder":tab}
    return {**p, "filters":"[]",
            "config": json.dumps({"name":vn(),"layouts":[{"id":0,"position":p}],"singleVisual":sv_obj}),
            "query":"{}","dataTransforms":"{}"}

def card(x,y,w,h,entity,alias,col_,agg_fn,label,tab):
    qn = ("Sum" if agg_fn==0 else "Avg" if agg_fn==1 else "Count") + f"({entity}.{col_})"
    return vc(x,y,w,h,tab,{
        "visualType":"card","drillFilterOtherVisuals":True,
        "projections":{"Values":[{"queryRef":qn}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_}},"Function":agg_fn},"Name":qn,"NativeReferenceName":label}]}
    })

def bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,vtype="clusteredBarChart",leg_e=None,leg_a=None,leg_c=None):
    cqn=f"{cat_e}.{cat_c}"; vqn=f"{'Sum' if agg==0 else 'Count'}({val_e}.{val_c})"
    froms=[{"Name":cat_a,"Entity":cat_e,"Type":0}]
    if val_a!=cat_a: froms.append({"Name":val_a,"Entity":val_e,"Type":0})
    selects=[
        {"Column":{"Expression":{"SourceRef":{"Source":cat_a}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
        {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":val_a}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
    ]
    projs={"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]}
    if leg_c:
        lqn=f"{leg_e}.{leg_c}"
        if leg_a not in [f["Name"] for f in froms]: froms.append({"Name":leg_a,"Entity":leg_e,"Type":0})
        selects.insert(1,{"Column":{"Expression":{"SourceRef":{"Source":leg_a}},"Property":leg_c},"Name":lqn,"NativeReferenceName":leg_c})
        projs["Legend"]=[{"queryRef":lqn}]
    return vc(x,y,w,h,tab,{"visualType":vtype,"drillFilterOtherVisuals":True,"projections":projs,
        "prototypeQuery":{"Version":2,"From":froms,"Select":selects}})

def donut(x,y,w,h,entity,alias,cat_c,val_c,agg,label,tab):
    cqn=f"{entity}.{cat_c}"; vqn=f"Sum({entity}.{val_c})"
    return vc(x,y,w,h,tab,{"visualType":"donutChart","drillFilterOtherVisuals":True,
        "projections":{"Category":[{"queryRef":cqn,"active":True}],"Y":[{"queryRef":vqn}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[
                {"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":cat_c},"Name":cqn,"NativeReferenceName":cat_c},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":val_c}},"Function":agg},"Name":vqn,"NativeReferenceName":label}
            ]}})

def line(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab):
    return bar(x,y,w,h,cat_e,cat_a,cat_c,val_e,val_a,val_c,agg,label,tab,"lineChart")

def matrix(x,y,w,h,tab):
    return vc(x,y,w,h,tab,{"visualType":"pivotTable","drillFilterOtherVisuals":True,
        "projections":{"Rows":[{"queryRef":"Year(Orders.Order Date)","active":True}],
                       "Columns":[{"queryRef":"MonthName(Orders.Order Date)","active":True}],
                       "Values":[{"queryRef":"CountNonNull(Orders.Order ID)"}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":"o","Entity":"Orders","Type":0}],
            "Select":[
                {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order Date"}},"TimeUnit":6},"Name":"Year(Orders.Order Date)","NativeReferenceName":"Year"},
                {"DateSpan":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order Date"}},"TimeUnit":3},"Name":"MonthName(Orders.Order Date)","NativeReferenceName":"Month"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"o"}},"Property":"Order ID"}},"Function":5},"Name":"CountNonNull(Orders.Order ID)","NativeReferenceName":"Count of Orders"}
            ]},
        "vcObjects":{"subTotals":[{"properties":{"rowSubtotals":{"expr":{"Literal":{"Value":"false"}}},"columnSubtotals":{"expr":{"Literal":{"Value":"false"}}}}}]}
    })

def slicer(x,y,w,h,entity,alias,col_,tab):
    qn=f"{entity}.{col_}"
    return vc(x,y,w,h,tab,{"visualType":"slicer","drillFilterOtherVisuals":True,
        "objects":{"data":[{"properties":{"mode":{"expr":{"Literal":{"Value":"'Dropdown'"}}}}}]},
        "projections":{"Values":[{"queryRef":qn,"active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":alias,"Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":alias}},"Property":col_},"Name":qn,"NativeReferenceName":col_}]}
    })

def header(tab=0):
    """Dark header bar + 4 slicers (Year/Quarter via Order Date, Category, Ship Mode)"""
    hdr = vc(0,0,1280,44,tab,{"visualType":"textbox","objects":{"general":[{"properties":{"paragraphs":[{
        "textRuns":[{"value":"  Sales Analytics Dashboard","textStyle":{"fontWeight":"bold","fontSize":"14pt","color":"#FFFFFF"}}],
        "horizontalTextAlignment":"left"}]}}]}})
    yr  = slicer(80,  50,130,28,"Orders","o","Order Date",tab+1)
    cat = slicer(225, 50,160,28,"Orders","o","Category",  tab+2)
    seg = slicer(400, 50,160,28,"Orders","o","Segment",   tab+3)
    shp = slicer(575, 50,165,28,"Orders","o","Ship Mode", tab+4)
    return [hdr, yr, cat, seg, shp]

CW,CH=193,105
def kpis(y, t):
    return [
        card(10+0*(CW+8), y, CW,CH, "Orders","o","Sales",    0,"Total Revenue",  t+0),
        card(10+1*(CW+8), y, CW,CH, "Orders","o","Profit",   0,"Total Profit",   t+10),
        card(10+2*(CW+8), y, CW,CH, "Orders","o","Order ID", 5,"Total Orders",   t+20),
        card(10+3*(CW+8), y, CW,CH, "Orders","o","Customer ID",5,"Customers",    t+30),
        card(10+4*(CW+8), y, CW,CH, "Returns","r","Order ID",5,"Total Returns",  t+40),
        card(10+5*(CW+8), y, CW,CH, "Orders","o","Sales",    1,"Avg Order Value",t+50),
    ]

# ── Page 1: Executive Summary ────────────────────────────────────────────────
p1 = header(0) + kpis(88,100) + [
    line(10, 210,1260,190, "Orders","o","Order Date","Orders","o","Sales",0,"Sales",600),
    bar( 10, 415, 400,370, "Orders","o","Category",  "Orders","o","Sales",0,"Sales",700,"clusteredBarChart"),
    donut(420,415,415,370, "Orders","o","Segment","Sales",0,"Sales",800),
    donut(845,415,425,370, "Orders","o","Ship Mode","Order ID",5,"Count",900),
]

# ── Page 2: Sales Performance ────────────────────────────────────────────────
p2 = header(0) + kpis(88,100) + [
    matrix(10, 205,1260,195,600),
    bar(10, 407, 620,275, "Orders","o","Region",   "Orders","o","Sales",0,"Sales",700,"clusteredBarChart"),
    bar(645,407, 625,275, "Orders","o","Ship Mode","Orders","o","Order ID",5,"Orders",800,"clusteredColumnChart"),
    bar(10, 690,1260,100, "Orders","o","Order Date","Orders","o","Sales",0,"Revenue",900,"clusteredColumnChart",
        "Orders","o","Order Date"),
]

# ── Page 3: Product Analysis ─────────────────────────────────────────────────
p3 = header(0) + kpis(88,100) + [
    bar(10, 205, 620,280, "Orders","o","Sub-Category","Orders","o","Sales",0,"Sales",600,"clusteredBarChart"),
    bar(645,205, 625,280, "Orders","o","Category",    "Orders","o","Sales",1,"Avg Sales",700,"clusteredColumnChart"),
    bar(10, 495,1260,290, "Orders","o","Category",    "Orders","o","Sales",0,"Sales",800,"clusteredColumnChart",
        "Orders","o","Profit"),
]

# ── Page 4: Customer Insights ────────────────────────────────────────────────
p4 = header(0) + kpis(88,100) + [
    bar(10, 205, 620,280, "Customers","c","Segment",      "Orders","o","Sales",0,"Sales",600,"clusteredBarChart"),
    bar(645,205, 625,280, "Orders","o","Region",          "Orders","o","Customer ID",5,"Customers",700,"clusteredColumnChart"),
    bar(10, 495, 620,290, "Customers","c","Segment",      "Orders","o","Order ID",5,"Orders",800,"clusteredColumnChart",
        "Orders","o","Segment"),
    bar(645,495, 625,290, "Customers","c","Customer Name","Orders","o","Sales",0,"Sales",900,"clusteredBarChart"),
]

# ── Page 5: Team Performance ─────────────────────────────────────────────────
p5 = header(0) + kpis(88,100) + [
    bar(10, 205,1260,280, "Users","u","Region",   "Orders","o","Sales",0,"Sales",600,"clusteredColumnChart"),
    bar(10, 495, 620,290, "Users","u","Region",   "Orders","o","Sales",0,"Sales",700,"clusteredBarChart"),
    bar(645,495, 625,290, "Orders","o","Segment", "Orders","o","Profit",0,"Profit",800,"clusteredBarChart"),
]

def section(sid,name,display,ordinal,visuals):
    return {"id":sid,"name":name,"displayName":display,"ordinal":ordinal,
            "visualContainers":visuals,"filters":"[]","config":"{}",
            "displayOption":1,"width":1280,"height":800}

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
    "config": json.dumps({
        "version":"5.49",
        "themeCollection":{"baseTheme":{"name":"CY23SU11","version":"5.49","type":2}},
        "activeSectionIndex":0,"defaultDrillFilterOtherVisuals":True,
        "settings":{"useNewFilterPaneExperience":True,"allowChangeFilterTypes":True,"useStylableVisualContainerHeader":True}
    }),
    "layoutOptimization":0
}

layout_bytes = json.dumps(report_layout, ensure_ascii=False).encode('utf-16-le')

# Read ALL original files from source PBIX
with zipfile.ZipFile(SRC) as z:
    orig = {n: z.read(n) for n in z.namelist()}

# Build new PBIX: keep EVERYTHING from source except Report/Layout
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for name, data in orig.items():
        if name == 'Report/Layout':
            z.writestr(name, layout_bytes)
        else:
            z.writestr(name, data)

size = os.path.getsize(OUT)
print(f"Written: {OUT}  ({size:,} bytes)")

with zipfile.ZipFile(OUT) as z:
    print("Files:")
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")
    layout = json.loads(z.read('Report/Layout').decode('utf-16-le'))
    for s in layout['sections']:
        print(f"  Page {s['ordinal']}: {s['displayName']} ({len(s['visualContainers'])} visuals)")
print("Done.")

"""
Build SalesAnalytics_Final_v2.pbix
- Keeps source PBIX DataModel 100% intact (no corruption)
- Rebuilds Report/Layout with 5 pages matching HTML design
- Full color theme: teal/dark/red palette from HTML
- Card formatting: white bg, teal border, bold value, colored label
- Chart colors: teal, red, yellow, blue, purple, green
"""
import json, zipfile, uuid, os

SRC = '/tmp/pbix_v3/source.pbix'
OUT = '/home/user/newm/SalesAnalytics_Final_v2.pbix'

# ── Color palette from HTML ───────────────────────────────────────────────────
TEAL    = "#01B8AA"
DARK    = "#252423"
RED     = "#FD625E"
YELLOW  = "#F2C80F"
BLUE    = "#118DFF"
PURPLE  = "#8B00FF"
GREEN   = "#00B050"
DGRAY   = "#374649"
ORANGE  = "#FF6B35"
PINK    = "#E91E63"
WHITE   = "#FFFFFF"
LTGRAY  = "#F5F5F5"

CHART_COLORS = [TEAL, RED, YELLOW, BLUE, PURPLE, GREEN, ORANGE, PINK, DGRAY]

# Card accent colors per position (6 cards)
CARD_ACCENTS = [TEAL, GREEN, BLUE, ORANGE, RED, PURPLE]

def vn(): return uuid.uuid4().hex[:20]

def lit(v):   return {"expr": {"Literal": {"Value": v}}}
def color(c): return {"solid": {"color": lit(f"'{c}'")}}

def vc(x, y, w, h, tab, sv_obj):
    p = {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}
    return {**p, "filters": "[]",
            "config": json.dumps({"name": vn(), "layouts": [{"id": 0, "position": p}], "singleVisual": sv_obj}),
            "query": "{}", "dataTransforms": "{}"}

def card(x, y, w, h, entity, alias, col_, agg_fn, label, tab, accent=TEAL):
    fn_name = "Sum" if agg_fn == 0 else "Avg" if agg_fn == 1 else "Count"
    qn = f"{fn_name}({entity}.{col_})"
    sv = {
        "visualType": "card",
        "drillFilterOtherVisuals": True,
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col_}}, "Function": agg_fn}, "Name": qn, "NativeReferenceName": label}]
        },
        "vcObjects": {
            # White background
            "background": [{"properties": {
                "show": lit("true"),
                "color": color(WHITE),
                "transparency": lit("0D")
            }}],
            # Teal/accent left border via visual border
            "border": [{"properties": {
                "show": lit("true"),
                "color": color(accent),
                "radius": lit("4D")
            }}],
            # Value (data label): large, bold, dark
            "labels": [{"properties": {
                "color": color(DARK),
                "fontSize": lit("22D"),
                "fontFamily": lit("'Segoe UI'"),
                "bold": lit("true")
            }}],
            # Category label: smaller, gray
            "categoryLabels": [{"properties": {
                "show": lit("true"),
                "color": color(DGRAY),
                "fontSize": lit("10D"),
                "fontFamily": lit("'Segoe UI'")
            }}],
            # Drop shadow for depth
            "dropShadow": [{"properties": {
                "show": lit("true"),
                "color": color("#DDDDDD"),
                "position": lit("'Outer'"),
                "preset": lit("'BottomRight'")
            }}]
        }
    }
    return vc(x, y, w, h, tab, sv)

def _chart_vcobjects(vtype):
    """Common vcObjects for all chart types: colored background, data colors."""
    objs = {
        "background": [{"properties": {
            "show": lit("true"),
            "color": color(WHITE),
            "transparency": lit("0D")
        }}],
        "border": [{"properties": {
            "show": lit("true"),
            "color": color("#E0E0E0"),
            "radius": lit("4D")
        }}],
        "valueAxis": [{"properties": {
            "gridlineColor": color("#F0F0F0")
        }}],
    }
    # Apply chart color palette via dataPoint
    data_points = []
    for i, c in enumerate(CHART_COLORS):
        data_points.append({
            "selector": {"id": str(i)},
            "properties": {"fill": color(c)}
        })
    objs["dataPoint"] = data_points
    return objs

def bar(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab,
        vtype="clusteredBarChart", leg_e=None, leg_a=None, leg_c=None):
    cqn = f"{cat_e}.{cat_c}"
    vqn = f"{'Sum' if agg == 0 else 'Count'}({val_e}.{val_c})"
    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if val_a != cat_a:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})
    selects = [
        {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c}, "Name": cqn, "NativeReferenceName": cat_c},
        {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}}, "Property": val_c}}, "Function": agg}, "Name": vqn, "NativeReferenceName": label}
    ]
    projs = {"Category": [{"queryRef": cqn, "active": True}], "Y": [{"queryRef": vqn}]}
    if leg_c:
        lqn = f"{leg_e}.{leg_c}"
        if leg_a not in [f["Name"] for f in froms]:
            froms.append({"Name": leg_a, "Entity": leg_e, "Type": 0})
        selects.insert(1, {"Column": {"Expression": {"SourceRef": {"Source": leg_a}}, "Property": leg_c}, "Name": lqn, "NativeReferenceName": leg_c})
        projs["Legend"] = [{"queryRef": lqn}]
    sv = {
        "visualType": vtype,
        "drillFilterOtherVisuals": True,
        "projections": projs,
        "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
        "vcObjects": _chart_vcobjects(vtype)
    }
    return vc(x, y, w, h, tab, sv)

def donut(x, y, w, h, entity, alias, cat_c, val_c, agg, label, tab):
    cqn = f"{entity}.{cat_c}"
    vqn = f"Sum({entity}.{val_c})"
    sv = {
        "visualType": "donutChart",
        "drillFilterOtherVisuals": True,
        "projections": {"Category": [{"queryRef": cqn, "active": True}], "Y": [{"queryRef": vqn}]},
        "prototypeQuery": {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [
                {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": cat_c}, "Name": cqn, "NativeReferenceName": cat_c},
                {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": val_c}}, "Function": agg}, "Name": vqn, "NativeReferenceName": label}
            ]},
        "vcObjects": _chart_vcobjects("donutChart")
    }
    return vc(x, y, w, h, tab, sv)

def line(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab):
    return bar(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab, "lineChart")

def matrix(x, y, w, h, tab):
    sv = {
        "visualType": "pivotTable",
        "drillFilterOtherVisuals": True,
        "projections": {
            "Rows": [{"queryRef": "Year(Orders.Order Date)", "active": True}],
            "Columns": [{"queryRef": "MonthName(Orders.Order Date)", "active": True}],
            "Values": [{"queryRef": "CountNonNull(Orders.Order ID)"}]
        },
        "prototypeQuery": {"Version": 2, "From": [{"Name": "o", "Entity": "Orders", "Type": 0}],
            "Select": [
                {"DateSpan": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "Order Date"}}, "TimeUnit": 6}, "Name": "Year(Orders.Order Date)", "NativeReferenceName": "Year"},
                {"DateSpan": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "Order Date"}}, "TimeUnit": 3}, "Name": "MonthName(Orders.Order Date)", "NativeReferenceName": "Month"},
                {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "Order ID"}}, "Function": 5}, "Name": "CountNonNull(Orders.Order ID)", "NativeReferenceName": "Count of Orders"}
            ]},
        "vcObjects": {
            "background": [{"properties": {"show": lit("true"), "color": color(WHITE), "transparency": lit("0D")}}],
            "border": [{"properties": {"show": lit("true"), "color": color(TEAL), "radius": lit("2D")}}],
            "subTotals": [{"properties": {
                "rowSubtotals": lit("false"),
                "columnSubtotals": lit("false")
            }}],
            "columnHeaders": [{"properties": {
                "backColor": color(TEAL),
                "fontColor": color(WHITE),
                "bold": lit("true"),
                "fontSize": lit("11D")
            }}],
            "rowHeaders": [{"properties": {
                "fontColor": color(DARK),
                "bold": lit("true"),
                "fontSize": lit("11D")
            }}],
            "values": [{"properties": {
                "backColor": color(LTGRAY),
                "fontColor": color(DARK),
                "fontSize": lit("11D")
            }}]
        }
    }
    return vc(x, y, w, h, tab, sv)

def slicer(x, y, w, h, entity, alias, col_, tab):
    qn = f"{entity}.{col_}"
    sv = {
        "visualType": "slicer",
        "drillFilterOtherVisuals": True,
        "objects": {"data": [{"properties": {"mode": lit("'Dropdown'")}}]},
        "projections": {"Values": [{"queryRef": qn, "active": True}]},
        "prototypeQuery": {"Version": 2, "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col_}, "Name": qn, "NativeReferenceName": col_}]},
        "vcObjects": {
            "background": [{"properties": {"show": lit("true"), "color": color(WHITE), "transparency": lit("0D")}}],
            "border": [{"properties": {"show": lit("true"), "color": color(TEAL)}}],
            "header": [{"properties": {
                "show": lit("true"),
                "fontColor": color(DARK),
                "background": color(LTGRAY),
                "outline": lit("'None'")
            }}],
            "items": [{"properties": {
                "fontColor": color(DARK),
                "background": color(WHITE)
            }}]
        }
    }
    return vc(x, y, w, h, tab, sv)

def header(tab=0):
    """Dark header bar with teal accent line + 4 slicers."""
    hdr = vc(0, 0, 1280, 44, tab, {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{
            "textRuns": [{"value": "  ■  Sales Analytics Dashboard",
                          "textStyle": {"fontWeight": "bold", "fontSize": "14pt", "color": WHITE}}],
            "horizontalTextAlignment": "left"
        }]}}]},
        "vcObjects": {
            "background": [{"properties": {"show": lit("true"), "color": color(DARK), "transparency": lit("0D")}}]
        }
    })
    # Slicer label strip (light gray, sits below header)
    lbl = vc(0, 44, 1280, 16, tab, {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{
            "textRuns": [{"value": "   Filter by:  Order Date        Category                Segment                  Ship Mode",
                          "textStyle": {"fontSize": "8pt", "color": DGRAY}}],
            "horizontalTextAlignment": "left"
        }]}}]},
        "vcObjects": {
            "background": [{"properties": {"show": lit("true"), "color": color(LTGRAY), "transparency": lit("0D")}}]
        }
    })
    yr  = slicer(10,  62, 155, 28, "Orders", "o", "Order Date", tab + 1)
    cat = slicer(175, 62, 155, 28, "Orders", "o", "Category",   tab + 2)
    seg = slicer(340, 62, 155, 28, "Orders", "o", "Segment",    tab + 3)
    shp = slicer(505, 62, 155, 28, "Orders", "o", "Ship Mode",  tab + 4)
    return [hdr, lbl, yr, cat, seg, shp]

CW, CH = 193, 100

def kpis(y, t):
    cards = []
    configs = [
        ("Orders",  "o", "Sales",       0, "Total Revenue"),
        ("Orders",  "o", "Profit",      0, "Total Profit"),
        ("Orders",  "o", "Order ID",    5, "Total Orders"),
        ("Orders",  "o", "Customer ID", 5, "Customers"),
        ("Returns", "r", "Order ID",    5, "Total Returns"),
        ("Orders",  "o", "Sales",       1, "Avg Order Value"),
    ]
    for i, (ent, ali, col, agg, lbl) in enumerate(configs):
        cards.append(card(10 + i * (CW + 8), y, CW, CH, ent, ali, col, agg, lbl, t + i * 10, CARD_ACCENTS[i]))
    return cards

# ── Page 1: Executive Summary ─────────────────────────────────────────────────
p1 = header(0) + kpis(96, 100) + [
    line(10,  205, 1260, 195, "Orders", "o", "Order Date", "Orders", "o", "Sales",    0, "Sales",  600),
    bar( 10,  410,  400, 370, "Orders", "o", "Category",   "Orders", "o", "Sales",    0, "Sales",  700, "clusteredBarChart"),
    donut(420, 410, 415, 370, "Orders", "o", "Segment",    "Sales",  0,   "Sales",    800),
    donut(845, 410, 425, 370, "Orders", "o", "Ship Mode",  "Order ID", 5, "Count",    900),
]

# ── Page 2: Sales Performance ─────────────────────────────────────────────────
p2 = header(0) + kpis(96, 100) + [
    matrix(10,  205, 1260, 190, 600),
    bar(10,  405,  620, 280, "Orders", "o", "Region",    "Orders", "o", "Sales",    0, "Sales",  700, "clusteredBarChart"),
    bar(645, 405,  625, 280, "Orders", "o", "Ship Mode", "Orders", "o", "Order ID", 5, "Orders", 800, "clusteredColumnChart"),
    bar(10,  695, 1260,  95, "Orders", "o", "Order Date","Orders", "o", "Sales",    0, "Revenue",900, "clusteredColumnChart"),
]

# ── Page 3: Product Analysis ──────────────────────────────────────────────────
p3 = header(0) + kpis(96, 100) + [
    bar(10,  205,  620, 285, "Orders", "o", "Sub-Category", "Orders", "o", "Sales",  0, "Sales",    600, "clusteredBarChart"),
    bar(645, 205,  625, 285, "Orders", "o", "Category",     "Orders", "o", "Sales",  1, "Avg Sales",700, "clusteredColumnChart"),
    bar(10,  500, 1260, 285, "Orders", "o", "Category",     "Orders", "o", "Sales",  0, "Sales",    800, "clusteredColumnChart",
        "Orders", "o", "Profit"),
]

# ── Page 4: Customer Insights ─────────────────────────────────────────────────
p4 = header(0) + kpis(96, 100) + [
    bar(10,  205,  620, 285, "Customers", "c", "Segment",       "Orders", "o", "Sales",      0, "Sales",    600, "clusteredBarChart"),
    bar(645, 205,  625, 285, "Orders",    "o", "Region",        "Orders", "o", "Customer ID",5, "Customers",700, "clusteredColumnChart"),
    bar(10,  500,  620, 285, "Customers", "c", "Segment",       "Orders", "o", "Order ID",   5, "Orders",   800, "clusteredColumnChart",
        "Orders", "o", "Segment"),
    bar(645, 500,  625, 285, "Customers", "c", "Customer Name", "Orders", "o", "Sales",      0, "Sales",    900, "clusteredBarChart"),
]

# ── Page 5: Team Performance ──────────────────────────────────────────────────
p5 = header(0) + kpis(96, 100) + [
    bar(10,  205, 1260, 285, "Users", "u", "Region",  "Orders", "o", "Sales",  0, "Sales", 600, "clusteredColumnChart"),
    bar(10,  500,  620, 285, "Users", "u", "Region",  "Orders", "o", "Sales",  0, "Sales", 700, "clusteredBarChart"),
    bar(645, 500,  625, 285, "Orders","o", "Segment", "Orders", "o", "Profit", 0, "Profit",800, "clusteredBarChart"),
]

# ── Custom theme JSON ─────────────────────────────────────────────────────────
CUSTOM_THEME = {
    "name": "SalesAnalyticsTheme",
    "dataColors": CHART_COLORS,
    "background": WHITE,
    "foreground": DARK,
    "tableAccent": TEAL,
    "visualStyles": {
        "*": {"*": {
            "background": [{"color": {"solid": {"color": WHITE}}}],
            "border": [{"show": True}]
        }},
        "card": {"*": {
            "labels": [{"color": {"solid": {"color": DARK}}, "fontSize": 22, "bold": True}],
            "categoryLabels": [{"show": True, "color": {"solid": {"color": DGRAY}}, "fontSize": 10}]
        }}
    }
}

theme_bytes = json.dumps(CUSTOM_THEME, ensure_ascii=False).encode("utf-8")
THEME_PATH = "Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json"

def section(sid, name, display, ordinal, visuals):
    # Page-level light gray background
    cfg = {"page": {"background": {"color": {"solid": {"color": LTGRAY}}, "transparency": 0}}}
    return {"id": sid, "name": name, "displayName": display, "ordinal": ordinal,
            "visualContainers": visuals, "filters": "[]",
            "config": json.dumps(cfg),
            "displayOption": 1, "width": 1280, "height": 800}

report_layout = {
    "id": 0,
    "resourcePackages": [
        {"resourcePackage": {"name": "SharedResources", "type": 2,
            "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json", "name": "CY23SU11"}],
            "disabled": False}},
        {"resourcePackage": {"name": "RegisteredResources", "type": 1,
            "items": [{"type": 202, "path": "SalesAnalyticsTheme.json", "name": "SalesAnalyticsTheme"}],
            "disabled": False}}
    ],
    "sections": [
        section(0, "S1", "Executive Summary", 0, p1),
        section(1, "S2", "Sales Performance",  1, p2),
        section(2, "S3", "Product Analysis",   2, p3),
        section(3, "S4", "Customer Insights",  3, p4),
        section(4, "S5", "Team Performance",   4, p5),
    ],
    "config": json.dumps({
        "version": "5.49",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU11", "version": "5.49", "type": 2},
            "customTheme": {"name": "SalesAnalyticsTheme", "type": 1, "resourcePackage": "RegisteredResources"}
        },
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

layout_bytes = json.dumps(report_layout, ensure_ascii=False).encode("utf-16-le")

# ── Update Content_Types to include new theme ─────────────────────────────────
def patch_content_types(xml_bytes):
    xml = xml_bytes.decode("utf-8")
    if "SalesAnalyticsTheme" not in xml:
        xml = xml.replace(
            "</Types>",
            '<Override PartName="/Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json" ContentType="application/json" /></Types>'
        )
    return xml.encode("utf-8")

# Read ALL original files from source PBIX
with zipfile.ZipFile(SRC) as z:
    orig = {n: z.read(n) for n in z.namelist()}

# Build new PBIX
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in orig.items():
        if name == "Report/Layout":
            z.writestr(name, layout_bytes)
        elif name == "[Content_Types].xml":
            z.writestr(name, patch_content_types(data))
        else:
            z.writestr(name, data)
    # Add custom theme file
    z.writestr(THEME_PATH, theme_bytes)

size = os.path.getsize(OUT)
print(f"Written: {OUT}  ({size:,} bytes)")

with zipfile.ZipFile(OUT) as z:
    print("Files:")
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")
    layout = json.loads(z.read("Report/Layout").decode("utf-16-le"))
    for s in layout["sections"]:
        print(f"  Page {s['ordinal']}: {s['displayName']} ({len(s['visualContainers'])} visuals)")
print("Done.")

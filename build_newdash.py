"""
Build SalesAnalytics_NewDash.pbix
- Copies DataModel from uploaded PBIX exactly
- 4 pages: Executive Summary, Sales Analysis, Customer Insights, Product Performance
- Professional dark theme: bg #0F1923, accent cyan #00D4FF, orange #FF6B35, purple #7C3AED
- Canvas 1280x720
"""
import json, zipfile, uuid, os, shutil

SRC_PBIX = '/root/.claude/uploads/b8c05b51-af18-50bc-8604-873964cd092e/7a94861f-newdash.pbix'
OUT = '/home/user/newm/SalesAnalytics_NewDash.pbix'

# ── Theme colors ──────────────────────────────────────────────────────────────
BG      = "#0F1923"   # dark navy background
CARD_BG = "#162433"   # slightly lighter card background
PANEL   = "#1A2E40"   # panel/section background
CYAN    = "#00D4FF"   # primary accent
ORANGE  = "#FF6B35"   # secondary accent
PURPLE  = "#7C3AED"   # tertiary accent
GREEN   = "#00C896"   # positive/success
RED     = "#FF4757"   # negative/alert
YELLOW  = "#FFD700"   # highlight
WHITE   = "#FFFFFF"
LGRAY   = "#8899AA"   # light gray text
DGRAY   = "#334455"   # dividers

PALETTE = [CYAN, ORANGE, PURPLE, GREEN, RED, YELLOW, "#FF69B4", "#20B2AA", "#FFA07A", "#9370DB"]

# ── Helpers ───────────────────────────────────────────────────────────────────
def vn(): return uuid.uuid4().hex[:20]
def Ls(s): return {"expr":{"Literal":{"Value":f"'{s}'"}}}
def Ln(n): return {"expr":{"Literal":{"Value":str(n)}}}
def Lb(b): return {"expr":{"Literal":{"Value":"true" if b else "false"}}}
def clr(c): return {"solid":{"color":Ls(c)}}

def vc(x, y, w, h, tab, sv):
    p = {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}
    return {
        **p,
        "filters": "[]",
        "config": json.dumps({
            "name": vn(),
            "layouts": [{"id": 0, "position": p}],
            "singleVisual": sv
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }

def dark_vco(title_text, accent=CYAN):
    return {
        "title": [{"properties": {
            "show": Lb(True),
            "text": Ls(title_text),
            "fontColor": clr(WHITE),
            "fontSize": Ln("11D"),
            "bold": Lb(True),
            "background": clr(PANEL)
        }}],
        "background": [{"properties": {"show": Lb(True), "color": clr(CARD_BG), "transparency": Ln(0)}}],
        "border": [{"properties": {"show": Lb(True), "color": clr(accent)}}],
    }

# ── KPI Card (dark theme) ────────────────────────────────────────────────────
def card(x, y, w, h, entity, alias, col, agg, title, tab, accent=CYAN):
    fn = "Sum" if agg == 0 else "Avg" if agg == 1 else "CountNonNull"
    qn = f"{fn}({entity}.{col})"
    sv = {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Aggregation": {
                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}},
                "Function": agg
            }, "Name": qn, "NativeReferenceName": title}]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": Lb(True), "text": Ls(title),
                "fontColor": clr(LGRAY), "fontSize": Ln("9D")
            }}],
            "background": [{"properties": {"show": Lb(True), "color": clr(CARD_BG), "transparency": Ln(0)}}],
            "border": [{"properties": {"show": Lb(True), "color": clr(accent)}}],
            "labels": [{"properties": {"color": clr(accent), "fontSize": Ln("20D"), "bold": Lb(True)}}],
            "categoryLabels": [{"properties": {"show": Lb(False)}}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ── Bar / Column chart ────────────────────────────────────────────────────────
def bar(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab,
        vtype="clusteredBarChart", title="", accent=CYAN):
    fn = "Sum" if agg == 0 else "CountNonNull" if agg == 5 else "Avg"
    cqn = f"{cat_e}.{cat_c}"
    vqn = f"{fn}({val_e}.{val_c})"
    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if val_a != cat_a:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})
    sels = [
        {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c}, "Name": cqn, "NativeReferenceName": cat_c},
        {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}}, "Property": val_c}}, "Function": agg}, "Name": vqn, "NativeReferenceName": label}
    ]
    projs = {"Category": [{"queryRef": cqn, "active": True}], "Y": [{"queryRef": vqn}]}
    vco = dark_vco(title, accent)
    vco["dataPoint"] = [{"properties": {"fill": clr(accent)}}]
    sv = {
        "visualType": vtype,
        "projections": projs,
        "prototypeQuery": {"Version": 2, "From": froms, "Select": sels},
        "drillFilterOtherVisuals": True,
        "vcObjects": vco
    }
    return vc(x, y, w, h, tab, sv)

# ── Line chart ────────────────────────────────────────────────────────────────
def line(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab, title="", accent=CYAN):
    return bar(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab,
               "lineChart", title, accent)

# ── Donut chart ───────────────────────────────────────────────────────────────
def donut(x, y, w, h, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg, label, tab, title=""):
    fn = "Sum" if agg == 0 else "CountNonNull"
    cqn = f"{cat_e}.{cat_c}"
    vqn = f"{fn}({val_e}.{val_c})"
    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if val_a != cat_a:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})
    vco = dark_vco(title, PURPLE)
    vco["legend"] = [{"properties": {"show": Lb(True), "position": Ls("Bottom"), "fontColor": clr(WHITE)}}]
    sv = {
        "visualType": "donutChart",
        "projections": {
            "Category": [{"queryRef": cqn, "active": True}],
            "Y": [{"queryRef": vqn}]
        },
        "prototypeQuery": {"Version": 2, "From": froms, "Select": [
            {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c}, "Name": cqn, "NativeReferenceName": cat_c},
            {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}}, "Property": val_c}}, "Function": agg}, "Name": vqn, "NativeReferenceName": label}
        ]},
        "drillFilterOtherVisuals": True,
        "vcObjects": vco
    }
    return vc(x, y, w, h, tab, sv)

# ── Table visual ──────────────────────────────────────────────────────────────
def table(x, y, w, h, entity, alias, cols_with_agg, tab, title=""):
    """cols_with_agg: list of (col, agg_fn or None) — None = dimension, 0=Sum, 5=Count"""
    froms = [{"Name": alias, "Entity": entity, "Type": 0}]
    sels = []
    projs_vals = []
    for col, agg in cols_with_agg:
        if agg is None:
            qn = f"{entity}.{col}"
            sels.append({"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}, "Name": qn, "NativeReferenceName": col})
        else:
            fn = "Sum" if agg == 0 else "CountNonNull"
            qn = f"{fn}({entity}.{col})"
            sels.append({"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}}, "Function": agg}, "Name": qn, "NativeReferenceName": col})
        projs_vals.append({"queryRef": qn})
    vco = dark_vco(title, CYAN)
    vco["columnHeaders"] = [{"properties": {"backColor": clr(DGRAY), "fontColor": clr(CYAN), "bold": Lb(True), "fontSize": Ln("10D")}}]
    vco["values"] = [{"properties": {"fontColor": clr(WHITE), "fontSize": Ln("9D")}}]
    sv = {
        "visualType": "tableEx",
        "projections": {"Values": projs_vals},
        "prototypeQuery": {"Version": 2, "From": froms, "Select": sels},
        "drillFilterOtherVisuals": True,
        "vcObjects": vco
    }
    return vc(x, y, w, h, tab, sv)

# ── Text box (header/label) ───────────────────────────────────────────────────
def textbox(x, y, w, h, text, font_size=14, tab=0, color=WHITE, bg=PANEL):
    sv = {
        "visualType": "textbox",
        "vcObjects": {
            "background": [{"properties": {"show": Lb(True), "color": clr(bg), "transparency": Ln(0)}}],
            "border": [{"properties": {"show": Lb(False)}}],
        },
        "howToBindData": {"paragraphs": [{"textRuns": [{"value": text, "textStyle": {"fontSize": f"{font_size}pt", "bold": True, "color": color}}], "horizontalTextAlignment": "left"}]}
    }
    return vc(x, y, w, h, tab, sv)

# ── Scatter plot ─────────────────────────────────────────────────────────────
def scatter(x, y, w, h, det_e, det_a, det_c, xval_e, xval_a, xval_c, yval_e, yval_a, yval_c, tab, title=""):
    det_qn = f"{det_e}.{det_c}"
    x_qn = f"Sum({xval_e}.{xval_c})"
    y_qn = f"Sum({yval_e}.{yval_c})"
    froms = [{"Name": det_a, "Entity": det_e, "Type": 0}]
    for a, e in [(xval_a, xval_e), (yval_a, yval_e)]:
        if a not in [f["Name"] for f in froms]:
            froms.append({"Name": a, "Entity": e, "Type": 0})
    vco = dark_vco(title, ORANGE)
    sv = {
        "visualType": "scatterChart",
        "projections": {
            "Details": [{"queryRef": det_qn, "active": True}],
            "X": [{"queryRef": x_qn}],
            "Y": [{"queryRef": y_qn}]
        },
        "prototypeQuery": {"Version": 2, "From": froms, "Select": [
            {"Column": {"Expression": {"SourceRef": {"Source": det_a}}, "Property": det_c}, "Name": det_qn, "NativeReferenceName": det_c},
            {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": xval_a}}, "Property": xval_c}}, "Function": 0}, "Name": x_qn, "NativeReferenceName": xval_c},
            {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": yval_a}}, "Property": yval_c}}, "Function": 0}, "Name": y_qn, "NativeReferenceName": yval_c}
        ]},
        "drillFilterOtherVisuals": True,
        "vcObjects": vco
    }
    return vc(x, y, w, h, tab, sv)

# ── Page background rectangle helper ─────────────────────────────────────────
def page_config(display_name):
    return json.dumps({
        "displayArea": {"color": clr(BG)},
        "outspacePane": {"backgroundColor": clr(BG)}
    })

# ── Page section builder ──────────────────────────────────────────────────────
def section(sid, name, display_name, containers, ordinal):
    return {
        "id": sid,
        "name": name,
        "displayName": display_name,
        "filters": "[]",
        "ordinal": ordinal,
        "visualContainers": containers,
        "config": json.dumps({
            "layouts": [{"id": 0, "position": {"x": 0, "y": 0, "z": 0, "width": 1280, "height": 720}}],
            "objects": {
                "background": [{"properties": {"color": clr(BG), "transparency": Ln(0)}}]
            }
        }),
        "displayOption": 1,
        "width": 1280,
        "height": 720
    }

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: Executive Summary
# Layout: header bar, 4 KPI cards (top), trend line (mid-left), regional bar (mid-right)
# ═══════════════════════════════════════════════════════════════════════════════
# Using Sales table columns. Since DataModel is from a minimal PBIX, we use generic
# placeholder entity names that match typical Sales Analytics models.

p1_containers = []

# Header bar (textbox)
p1_containers.append(textbox(0, 0, 1280, 60, "  Executive Summary", 18, 1, WHITE, BG))

# 4 KPI cards: Revenue, Profit, Margin%, Units — row at y=70, each 300px wide, 110px tall
kpi_defs = [
    ("Net Sales",   "Sales", "s", "Net Sales",       0, CYAN),
    ("Profit",      "Sales", "s", "Profit",           0, GREEN),
    ("Profit Margin %", "Sales", "s", "Profit Margin %", 1, ORANGE),
    ("Total Orders","Sales", "s", "Order ID",         5, PURPLE),
]
card_w, card_h = 298, 110
card_y = 70
for i, (title, entity, alias, col, agg, accent) in enumerate(kpi_defs):
    cx = 10 + i * (card_w + 8)
    p1_containers.append(card(cx, card_y, card_w, card_h, entity, alias, col, agg, title, 10+i, accent))

# Trend line chart: Revenue by Month — large, left side
# y=195, x=10, w=760, h=280
p1_containers.append(
    line(10, 195, 760, 280,
         "Sales", "s", "Order Date",
         "Sales", "s", "Net Sales",
         0, "Revenue", 20,
         "Revenue Trend Over Time", CYAN)
)

# Regional bar chart: Sales by Category — right side
# y=195, x=780, w=490, h=280
p1_containers.append(
    bar(780, 195, 490, 280,
        "Sales", "s", "Category",
        "Sales", "s", "Net Sales",
        0, "Revenue", 21,
        "clusteredBarChart", "Revenue by Category", ORANGE)
)

# Bottom: Profit by Sales Channel (line) left, Donut by Segment right
p1_containers.append(
    bar(10, 490, 500, 220,
        "Sales", "s", "Sales Channel",
        "Sales", "s", "Profit",
        0, "Profit", 22,
        "clusteredColumnChart", "Profit by Sales Channel", GREEN)
)
p1_containers.append(
    donut(520, 490, 750, 220,
          "Sales", "s", "Order Status",
          "Sales", "s", "Net Sales",
          0, "Revenue", 23,
          "Revenue by Order Status")
)

pg1 = section(0, "ExecSummary", "Executive Summary", p1_containers, 0)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: Sales Analysis
# ═══════════════════════════════════════════════════════════════════════════════
p2_containers = []
p2_containers.append(textbox(0, 0, 1280, 60, "  Sales Analysis", 18, 1, WHITE, BG))

# Time series chart (full width)
p2_containers.append(
    line(10, 70, 1260, 200,
         "Sales", "s", "Order Date",
         "Sales", "s", "Net Sales",
         0, "Net Sales", 10,
         "Monthly Sales Trend", CYAN)
)

# Category donut (left)
p2_containers.append(
    donut(10, 285, 380, 260,
          "Sales", "s", "Category",
          "Sales", "s", "Net Sales",
          0, "Revenue", 11,
          "Sales by Category")
)

# Payment method bar (center)
p2_containers.append(
    bar(400, 285, 430, 260,
        "Sales", "s", "Payment Method",
        "Sales", "s", "Net Sales",
        0, "Revenue", 12,
        "clusteredBarChart", "Sales by Payment Method", PURPLE)
)

# Quarter column chart (right)
p2_containers.append(
    bar(840, 285, 430, 260,
        "Sales", "s", "Quarter",
        "Sales", "s", "Net Sales",
        0, "Revenue", 13,
        "clusteredColumnChart", "Sales by Quarter", ORANGE)
)

# Top products table
p2_containers.append(
    table(10, 560, 1260, 150,
          "Sales", "s",
          [("Category", None), ("Net Sales", 0), ("Profit", 0), ("Quantity", 0)],
          14, "Sales Summary by Category")
)

pg2 = section(1, "SalesAnalysis", "Sales Analysis", p2_containers, 1)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: Customer Insights
# ═══════════════════════════════════════════════════════════════════════════════
p3_containers = []
p3_containers.append(textbox(0, 0, 1280, 60, "  Customer Insights", 18, 1, WHITE, BG))

# Customer count card
p3_containers.append(card(10, 70, 290, 110, "Sales", "s", "Customer ID", 5, "Total Customers", 10, CYAN))
# Avg order value card
p3_containers.append(card(308, 70, 290, 110, "Sales", "s", "Net Sales", 1, "Avg Order Value", 11, GREEN))
# Total orders card
p3_containers.append(card(606, 70, 290, 110, "Sales", "s", "Order ID", 5, "Total Orders", 12, ORANGE))
# Avg profit card
p3_containers.append(card(904, 70, 366, 110, "Sales", "s", "Profit", 1, "Avg Profit per Order", 13, PURPLE))

# Customer segment donut (left)
p3_containers.append(
    donut(10, 195, 400, 270,
          "Customers", "c", "Segment",
          "Sales", "s", "Net Sales",
          0, "Revenue", 20,
          "Revenue by Customer Segment")
)

# Sales channel bar (center-right)
p3_containers.append(
    bar(420, 195, 430, 270,
        "Sales", "s", "Sales Channel",
        "Sales", "s", "Net Sales",
        0, "Revenue", 21,
        "clusteredBarChart", "Revenue by Sales Channel", ORANGE)
)

# Country bar (far right)
p3_containers.append(
    bar(860, 195, 410, 270,
        "Customers", "c", "Country",
        "Sales", "s", "Net Sales",
        0, "Revenue", 22,
        "clusteredBarChart", "Revenue by Country", CYAN)
)

# Customer table
p3_containers.append(
    table(10, 480, 1260, 230,
          "Customers", "c",
          [("Segment", None), ("Country", None), ("Credit Limit", 0)],
          23, "Customer Summary")
)

pg3 = section(2, "CustomerInsights", "Customer Insights", p3_containers, 2)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Product Performance
# ═══════════════════════════════════════════════════════════════════════════════
p4_containers = []
p4_containers.append(textbox(0, 0, 1280, 60, "  Product Performance", 18, 1, WHITE, BG))

# KPI cards for products
p4_containers.append(card(10,   70, 290, 110, "Products", "p", "Unit Price", 1, "Avg Unit Price", 10, CYAN))
p4_containers.append(card(308,  70, 290, 110, "Products", "p", "Profit Margin %", 1, "Avg Margin %", 11, GREEN))
p4_containers.append(card(606,  70, 290, 110, "Products", "p", "Stock Quantity", 0, "Total Stock", 12, ORANGE))
p4_containers.append(card(904,  70, 366, 110, "Sales", "s", "Net Sales", 0, "Total Revenue", 13, PURPLE))

# Product category bar (left)
p4_containers.append(
    bar(10, 195, 490, 270,
        "Products", "p", "Category",
        "Sales", "s", "Net Sales",
        0, "Revenue", 20,
        "clusteredColumnChart", "Revenue by Product Category", CYAN)
)

# Sub-category bar (center)
p4_containers.append(
    bar(510, 195, 490, 270,
        "Products", "p", "Sub Category",
        "Sales", "s", "Net Sales",
        0, "Revenue", 21,
        "clusteredBarChart", "Revenue by Sub-Category", ORANGE)
)

# Brand donut (right)
p4_containers.append(
    donut(1010, 195, 260, 270,
          "Products", "p", "Brand",
          "Sales", "s", "Net Sales",
          0, "Revenue", 22,
          "Revenue by Brand")
)

# Scatter: Unit Price vs Profit Margin
p4_containers.append(
    scatter(10, 480, 600, 230,
            "Products", "p", "Product Name",
            "Products", "p", "Unit Price",
            "Products", "p", "Profit Margin %",
            23, "Price vs Profit Margin")
)

# Product table
p4_containers.append(
    table(620, 480, 650, 230,
          "Products", "p",
          [("Product Name", None), ("Category", None), ("Unit Price", 1), ("Profit Margin %", 1)],
          24, "Product Details")
)

pg4 = section(3, "ProductPerformance", "Product Performance", p4_containers, 3)

# ═══════════════════════════════════════════════════════════════════════════════
# Assemble Report/Layout JSON
# ═══════════════════════════════════════════════════════════════════════════════

# Read the original layout to get resourcePackages and config
with zipfile.ZipFile(SRC_PBIX, 'r') as z:
    raw_layout = z.read('Report/Layout')

# The layout is UTF-16 LE encoded (Power BI standard)
try:
    orig_layout = json.loads(raw_layout.decode('utf-16-le'))
except Exception:
    orig_layout = json.loads(raw_layout.decode('utf-8', errors='replace'))

resource_packages = orig_layout.get("resourcePackages", [])

report_config = json.dumps({
    "version": "5.72",
    "themeCollection": {
        "baseTheme": {
            "name": "CY26SU04",
            "version": {"visual": "2.8.0", "report": "3.2.0", "page": "2.3.1"},
            "type": 2
        }
    },
    "activeSectionIndex": 0,
    "defaultDrillFilterOtherVisuals": True,
    "settings": {
        "useNewFilterPaneExperience": True,
        "allowChangeFilterTypes": True,
        "useStylableVisualContainerHeader": True,
        "queryLimitOption": 6,
        "useEnhancedTooltips": True,
        "exportDataMode": 1,
        "useDefaultAggregateDisplayName": True
    },
    "objects": {
        "section": [{"properties": {"verticalAlignment": {"expr": {"Literal": {"Value": "'Top'"}}}}}]
    }
})

layout = {
    "id": 0,
    "resourcePackages": resource_packages,
    "sections": [pg1, pg2, pg3, pg4],
    "config": report_config,
    "layoutOptimization": 0
}

layout_bytes = json.dumps(layout, ensure_ascii=False).encode('utf-16-le')

# ═══════════════════════════════════════════════════════════════════════════════
# Write PBIX (copy everything from source, replace Report/Layout)
# ═══════════════════════════════════════════════════════════════════════════════
with zipfile.ZipFile(SRC_PBIX, 'r') as src_zip:
    with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED) as out_zip:
        for item in src_zip.infolist():
            if item.filename == 'Report/Layout':
                out_zip.writestr(item, layout_bytes)
            else:
                out_zip.writestr(item, src_zip.read(item.filename))

size = os.path.getsize(OUT)
print(f"Done! Output: {OUT}")
print(f"Size: {size:,} bytes ({size/1024:.1f} KB)")
print(f"Pages: Executive Summary, Sales Analysis, Customer Insights, Product Performance")

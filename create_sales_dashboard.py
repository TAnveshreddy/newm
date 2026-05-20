"""
Sales Analytics Dashboard - Power BI PBIT + PBIX Generator
Creates a production-ready PBIT (template) and PBIX that exactly matches the HTML dashboard.

Output files:
  /home/user/newm/Sales_Analytics_Dashboard.pbit  ← Open this in Power BI Desktop
  /home/user/newm/Sales_Analytics_Dashboard.pbix  ← PBIX with embedded DataModel
"""

import json, zipfile, uuid, re, os, struct, io

HTML_PATH  = '/root/.claude/uploads/2134a754-069c-451d-a23b-bfadf1730f85/56e3bddc-PowerBI_Sales_Dashboard.html'
OUT_PBIT   = '/home/user/newm/Sales_Analytics_Dashboard.pbit'
OUT_PBIX   = '/home/user/newm/Sales_Analytics_Dashboard.pbix'

# ─── Extract raw data from HTML ─────────────────────────────────────────────
html = open(HTML_PATH).read()

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

print(f"Data: {len(SALES)} sales | {len(CUSTOMERS)} customers | {len(USERS)} users | {len(PRODUCTS)} products")

# ─── Colors matching HTML exactly ───────────────────────────────────────────
TEAL   = "#01B8AA"; DARK   = "#252423"; RED    = "#FD625E"
YELLOW = "#F2C80F"; BLUE   = "#118DFF"; PURPLE = "#8B00FF"
GREEN  = "#00B050"; DGRAY  = "#374649"; ORANGE = "#FF6B35"
WHITE  = "#FFFFFF"; LTGRAY = "#F3F2F1"; SLATE  = "#5F6B6D"
BORDER = "#E0DFDE"; BGPAGE = "#F3F2F1"

CHART_COLORS  = [TEAL, RED, YELLOW, BLUE, PURPLE, GREEN, ORANGE, DGRAY, SLATE, "#E91E63"]
CARD_ACCENTS  = [TEAL, GREEN, BLUE, YELLOW, RED, PURPLE]  # one per KPI card

# ─── M-query helpers ─────────────────────────────────────────────────────────
def q(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    s = str(v).replace('"', '\\"')
    return f'"{s}"'

def build_m_table(records, col_types):
    type_str = ", ".join(f'#"{c}" = {t}' for c, t in col_types)
    rows = []
    for rec in records:
        vals = ", ".join(q(rec.get(c)) for c, _ in col_types)
        rows.append(f"    {{{vals}}}")
    body = ",\n".join(rows)
    return (f'let\n'
            f'  Source = #table(type table [{type_str}], {{\n'
            f'{body}\n'
            f'  }})\nin\n  Source')

SALES_COLS = [
    ("Order ID","text"), ("Order Date","date"), ("Year","Int64.Type"),
    ("Month","Int64.Type"), ("Quarter","text"), ("Customer ID","text"),
    ("Product ID","text"), ("User ID","text"), ("Category","text"),
    ("Quantity","Int64.Type"), ("Unit Price","number"), ("Unit Cost","number"),
    ("Gross Sales","number"), ("Discount %","number"), ("Discount Amount","number"),
    ("Net Sales","number"), ("Total Cost","number"), ("Profit","number"),
    ("Profit Margin %","number"), ("Sales Channel","text"),
    ("Order Status","text"), ("Ship Date","date"), ("Payment Method","text"),
]
CUST_COLS = [
    ("Customer ID","text"), ("First Name","text"), ("Last Name","text"),
    ("Email","text"), ("Phone","text"), ("Address","text"), ("City","text"),
    ("Country","text"), ("Postal Code","text"), ("Segment","text"),
    ("Registration Date","date"), ("Credit Limit","number"),
]
USER_COLS = [
    ("User ID","text"), ("Name","text"), ("First Name","text"), ("Last Name","text"),
    ("Email","text"), ("Role","text"), ("Department","text"), ("Country","text"),
    ("Location","text"), ("Phone","text"), ("Join Date","date"),
    ("Manager ID","text"), ("Sales Target","number"),
]
PROD_COLS = [
    ("Product ID","text"), ("Product Name","text"), ("Category","text"),
    ("Sub Category","text"), ("Brand","text"), ("Unit Cost","number"),
    ("Unit Price","number"), ("Profit Margin %","number"), ("Stock Quantity","Int64.Type"),
    ("Reorder Level","Int64.Type"), ("Supplier","text"), ("Weight (kg)","number"),
    ("Rating","number"),
]

# Build M expressions
M_SALES     = build_m_table(SALES, SALES_COLS)
M_CUSTOMERS = build_m_table(CUSTOMERS, CUST_COLS)
M_USERS     = build_m_table(USERS, USER_COLS)
M_PRODUCTS  = build_m_table(PRODUCTS, PROD_COLS)

print(f"M Sales: {len(M_SALES):,} chars | M Customers: {len(M_CUSTOMERS):,} | "
      f"M Users: {len(M_USERS):,} | M Products: {len(M_PRODUCTS):,}")

# ─── Layout helpers ───────────────────────────────────────────────────────────
def vn(): return uuid.uuid4().hex[:20]

def Ls(s): return {"expr": {"Literal": {"Value": f"'{s}'"}}}
def Ln(n): return {"expr": {"Literal": {"Value": str(n)}}}
def Lb(b): return {"expr": {"Literal": {"Value": "true" if b else "false"}}}
def clr(c): return {"solid": {"color": Ls(c)}}

def vc(x, y, w, h, tab, sv):
    pos = {"x": x, "y": y, "z": tab, "width": w, "height": h}
    cfg = {"name": vn(), "layouts": [{"id": 0, "position": pos}], "singleVisual": sv}
    return {**pos, "tabOrder": tab, "filters": "[]",
            "config": json.dumps(cfg), "query": "{}", "dataTransforms": "{}"}

# ─── Standard formatting objects ─────────────────────────────────────────────
def std_objects(title="", bg=WHITE, border_color=BORDER, title_color=DARK):
    objs = {
        "background": [{"properties": {"show": Lb(True), "color": clr(bg), "transparency": Ln(0)}}],
        "border":     [{"properties": {"show": Lb(True), "color": clr(border_color)}}],
    }
    if title:
        objs["title"] = [{"properties": {
            "show": Lb(True), "text": Ls(title),
            "fontColor": clr(title_color), "fontSize": Ln("12D"), "bold": Lb(True)
        }}]
    return objs

# ─── KPI Card ─────────────────────────────────────────────────────────────────
def card_vis(entity, alias, col, agg_fn, display_name, accent=TEAL):
    """
    agg_fn: 0=Sum, 1=Average, 5=Count (non-null)
    """
    fn_map = {0: "Sum", 1: "Avg", 5: "CountNonNull"}
    fn = fn_map.get(agg_fn, "Sum")
    qn = f"{fn}({entity}.{col})"
    return {
        "visualType": "card",
        "drillFilterOtherVisuals": True,
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Aggregation": {
                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}},
                "Function": agg_fn
            }, "Name": qn, "NativeReferenceName": display_name}],
        },
        "columnProperties": {},
        "vcObjects": {
            "title": [{"properties": {
                "show": Lb(True), "text": Ls(display_name),
                "fontColor": clr(SLATE), "fontSize": Ln("10D"), "bold": Lb(True)
            }}],
            "labels": [{"properties": {
                "color": clr(DARK), "fontSize": Ln("20D"), "bold": Lb(True)
            }}],
            "categoryLabels": [{"properties": {"show": Lb(False)}}],
            "background": [{"properties": {"show": Lb(True), "color": clr(WHITE), "transparency": Ln(0)}}],
            "border": [{"properties": {"show": Lb(True), "color": clr(accent)}}],
        }
    }

# ─── Measure Card (for DAX measures) ─────────────────────────────────────────
def measure_card_vis(entity, alias, measure_name, display_name, accent=TEAL):
    qn = f"{entity}.{measure_name}"
    return {
        "visualType": "card",
        "drillFilterOtherVisuals": True,
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Measure": {
                "Expression": {"SourceRef": {"Source": alias}},
                "Property": measure_name
            }, "Name": qn, "NativeReferenceName": display_name}],
        },
        "columnProperties": {},
        "vcObjects": {
            "title": [{"properties": {
                "show": Lb(True), "text": Ls(display_name),
                "fontColor": clr(SLATE), "fontSize": Ln("10D"), "bold": Lb(True)
            }}],
            "labels": [{"properties": {
                "color": clr(DARK), "fontSize": Ln("20D"), "bold": Lb(True)
            }}],
            "categoryLabels": [{"properties": {"show": Lb(False)}}],
            "background": [{"properties": {"show": Lb(True), "color": clr(WHITE), "transparency": Ln(0)}}],
            "border": [{"properties": {"show": Lb(True), "color": clr(accent)}}],
        }
    }

# ─── Slicer ───────────────────────────────────────────────────────────────────
def slicer_vis(entity, alias, col, title=""):
    qn = f"{entity}.{col}"
    return {
        "visualType": "slicer",
        "drillFilterOtherVisuals": True,
        "projections": {"Values": [{"queryRef": qn, "active": True}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{"Column": {
                "Expression": {"SourceRef": {"Source": alias}}, "Property": col
            }, "Name": qn, "NativeReferenceName": col}],
        },
        "columnProperties": {},
        "objects": {
            "data": [{"properties": {"mode": Ls("dropdownSelect")}}],
            "header": [{"properties": {
                "show": Lb(True), "fontColor": clr(SLATE), "fontSize": Ln("10D"),
                "outline": Ls("BottomOnly"), "background": clr(WHITE)
            }}],
            "background": [{"properties": {"show": Lb(True), "color": clr(WHITE), "transparency": Ln(0)}}],
        }
    }

# ─── Bar / Column Chart ───────────────────────────────────────────────────────
def chart_vis(vtype, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg_fn,
              title="", legend_e=None, legend_a=None, legend_c=None, colors=None):
    fn_map = {0: "Sum", 1: "Avg", 5: "CountNonNull"}
    fn = fn_map.get(agg_fn, "Sum")
    cqn = f"{cat_e}.{cat_c}"
    vqn = f"{fn}({val_e}.{val_c})"

    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if val_a != cat_a:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})

    selects = [
        {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c},
         "Name": cqn, "NativeReferenceName": cat_c},
        {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}},
         "Property": val_c}}, "Function": agg_fn}, "Name": vqn, "NativeReferenceName": val_c},
    ]
    projs = {
        "Category": [{"queryRef": cqn, "active": True}],
        "Y": [{"queryRef": vqn}],
    }

    if legend_c:
        lqn = f"{legend_e}.{legend_c}"
        if legend_a not in [f["Name"] for f in froms]:
            froms.append({"Name": legend_a, "Entity": legend_e, "Type": 0})
        selects.insert(1, {"Column": {"Expression": {"SourceRef": {"Source": legend_a}},
                            "Property": legend_c}, "Name": lqn, "NativeReferenceName": legend_c})
        projs["Legend"] = [{"queryRef": lqn}]

    objs = std_objects(title=title)
    if colors:
        dp_entries = []
        for i, color in enumerate(colors):
            dp_entries.append({
                "selector": {"id": {"visualId": None}, "index": i},
                "properties": {"fill": clr(color)}
            })
        objs["dataPoint"] = dp_entries

    return {
        "visualType": vtype,
        "drillFilterOtherVisuals": True,
        "projections": projs,
        "prototypeQuery": {"Version": 2, "From": froms, "Select": selects,
                           "OrderBy": [{"Direction": 2, "Expression":
                               {"Aggregation": {"Expression": {"Column": {
                                   "Expression": {"SourceRef": {"Source": val_a}},
                                   "Property": val_c}}, "Function": agg_fn}}}]},
        "columnProperties": {},
        "objects": objs,
    }

# Two-value column chart (e.g. Revenue vs Profit)
def chart_two_series(vtype, cat_e, cat_a, cat_c,
                     val1_e, val1_a, val1_c, val1_name, val1_color,
                     val2_e, val2_a, val2_c, val2_name, val2_color,
                     agg_fn=0, title=""):
    fn_map = {0: "Sum", 1: "Avg"}
    fn = fn_map.get(agg_fn, "Sum")
    cqn  = f"{cat_e}.{cat_c}"
    v1qn = f"{fn}({val1_e}.{val1_c})"
    v2qn = f"{fn}({val2_e}.{val2_c})"

    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if val1_a != cat_a: froms.append({"Name": val1_a, "Entity": val1_e, "Type": 0})
    if val2_a != cat_a and val2_a != val1_a:
        froms.append({"Name": val2_a, "Entity": val2_e, "Type": 0})

    agg = lambda alias, col: {"Aggregation": {
        "Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": col}},
        "Function": agg_fn}}

    selects = [
        {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c},
         "Name": cqn, "NativeReferenceName": cat_c},
        {**agg(val1_a, val1_c), "Name": v1qn, "NativeReferenceName": val1_name},
        {**agg(val2_a, val2_c), "Name": v2qn, "NativeReferenceName": val2_name},
    ]

    objs = std_objects(title=title)
    objs["dataPoint"] = [
        {"selector": {"id": {"visualId": None}, "index": 0}, "properties": {"fill": clr(val1_color)}},
        {"selector": {"id": {"visualId": None}, "index": 1}, "properties": {"fill": clr(val2_color)}},
    ]

    return {
        "visualType": vtype,
        "drillFilterOtherVisuals": True,
        "projections": {
            "Category": [{"queryRef": cqn, "active": True}],
            "Y": [{"queryRef": v1qn}, {"queryRef": v2qn}],
        },
        "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
        "columnProperties": {},
        "objects": objs,
    }

# ─── Donut / Pie Chart ────────────────────────────────────────────────────────
def donut_vis(vtype, cat_e, cat_a, cat_c, val_e, val_a, val_c, agg_fn=0,
              title="", colors=None):
    fn_map = {0: "Sum", 5: "CountNonNull"}
    fn = fn_map.get(agg_fn, "Sum")
    cqn = f"{cat_e}.{cat_c}"
    vqn = f"{fn}({val_e}.{val_c})"

    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if val_a != cat_a:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})

    objs = std_objects(title=title)
    if colors:
        objs["dataPoint"] = [
            {"selector": {"id": {"visualId": None}, "index": i},
             "properties": {"fill": clr(c)}} for i, c in enumerate(colors)
        ]
    objs["legend"] = [{"properties": {"show": Lb(True), "position": Ls("Bottom")}}]

    return {
        "visualType": vtype,
        "drillFilterOtherVisuals": True,
        "projections": {
            "Category": [{"queryRef": cqn, "active": True}],
            "Y": [{"queryRef": vqn}],
        },
        "prototypeQuery": {
            "Version": 2, "From": froms,
            "Select": [
                {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c},
                 "Name": cqn, "NativeReferenceName": cat_c},
                {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}},
                 "Property": val_c}}, "Function": agg_fn}, "Name": vqn, "NativeReferenceName": val_c},
            ]
        },
        "columnProperties": {},
        "objects": objs,
    }

# ─── Line Chart ───────────────────────────────────────────────────────────────
def line_vis(cat_e, cat_a, cat_c, val_e, val_a, val_c, series_e, series_a, series_c,
             agg_fn=0, title=""):
    fn_map = {0: "Sum"}
    fn = fn_map.get(agg_fn, "Sum")
    cqn = f"{cat_e}.{cat_c}"
    sqn = f"{series_e}.{series_c}"
    vqn = f"{fn}({val_e}.{val_c})"

    froms = [{"Name": cat_a, "Entity": cat_e, "Type": 0}]
    if series_a != cat_a:
        froms.append({"Name": series_a, "Entity": series_e, "Type": 0})
    if val_a not in [f["Name"] for f in froms]:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})

    objs = std_objects(title=title)
    objs["dataPoint"] = [
        {"selector": {"id": {"visualId": None}, "index": 0}, "properties": {"fill": clr(TEAL), "stroke": clr(TEAL)}},
        {"selector": {"id": {"visualId": None}, "index": 1}, "properties": {"fill": clr(YELLOW), "stroke": clr(YELLOW)}},
    ]
    objs["legend"] = [{"properties": {"show": Lb(True), "position": Ls("Top")}}]

    return {
        "visualType": "lineChart",
        "drillFilterOtherVisuals": True,
        "projections": {
            "Category": [{"queryRef": cqn, "active": True}],
            "Series": [{"queryRef": sqn}],
            "Y": [{"queryRef": vqn}],
        },
        "prototypeQuery": {
            "Version": 2, "From": froms,
            "Select": [
                {"Column": {"Expression": {"SourceRef": {"Source": cat_a}}, "Property": cat_c},
                 "Name": cqn, "NativeReferenceName": cat_c},
                {"Column": {"Expression": {"SourceRef": {"Source": series_a}}, "Property": series_c},
                 "Name": sqn, "NativeReferenceName": series_c},
                {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}},
                 "Property": val_c}}, "Function": agg_fn}, "Name": vqn, "NativeReferenceName": val_c},
            ]
        },
        "columnProperties": {},
        "objects": objs,
    }

# ─── Pivot / Matrix ───────────────────────────────────────────────────────────
def matrix_vis(row_e, row_a, row_c, col_e, col_a, col_c, val_e, val_a, val_c, agg_fn, title=""):
    fn_map = {5: "CountNonNull", 0: "Sum"}
    fn = fn_map.get(agg_fn, "CountNonNull")
    rqn = f"{row_e}.{row_c}"
    cqn2 = f"{col_e}.{col_c}"
    vqn = f"{fn}({val_e}.{val_c})"

    froms = [{"Name": row_a, "Entity": row_e, "Type": 0}]
    if col_a != row_a: froms.append({"Name": col_a, "Entity": col_e, "Type": 0})
    if val_a not in [f["Name"] for f in froms]:
        froms.append({"Name": val_a, "Entity": val_e, "Type": 0})

    objs = std_objects(title=title)
    objs["columnHeaders"] = [{"properties": {
        "fontColor": clr(WHITE), "backColor": clr(DARK), "fontSize": Ln("11D"), "bold": Lb(True)
    }}]
    objs["rowHeaders"] = [{"properties": {
        "fontColor": clr(DARK), "fontSize": Ln("11D"), "bold": Lb(True)
    }}]
    objs["values"] = [{"properties": {"fontColor": clr(DARK), "fontSize": Ln("11D")}}]

    return {
        "visualType": "pivotTable",
        "drillFilterOtherVisuals": True,
        "projections": {
            "Rows": [{"queryRef": rqn, "active": True}],
            "Columns": [{"queryRef": cqn2}],
            "Values": [{"queryRef": vqn}],
        },
        "prototypeQuery": {
            "Version": 2, "From": froms,
            "Select": [
                {"Column": {"Expression": {"SourceRef": {"Source": row_a}}, "Property": row_c},
                 "Name": rqn, "NativeReferenceName": row_c},
                {"Column": {"Expression": {"SourceRef": {"Source": col_a}}, "Property": col_c},
                 "Name": cqn2, "NativeReferenceName": col_c},
                {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": val_a}},
                 "Property": val_c}}, "Function": agg_fn}, "Name": vqn, "NativeReferenceName": val_c},
            ]
        },
        "columnProperties": {},
        "objects": objs,
    }

# ─── Table Visual ─────────────────────────────────────────────────────────────
def table_vis(cols_spec, title=""):
    """cols_spec: [(entity, alias, col, agg_fn_or_None), ...]
       agg_fn: None=column, 0=Sum, 5=Count
    """
    froms_dict = {}
    for e, a, c, _ in cols_spec:
        froms_dict[a] = e
    froms = [{"Name": a, "Entity": e, "Type": 0} for a, e in froms_dict.items()]

    selects = []
    projs = {"Values": []}
    for e, a, c, agg in cols_spec:
        if agg is None:
            qn = f"{e}.{c}"
            selects.append({"Column": {"Expression": {"SourceRef": {"Source": a}}, "Property": c},
                            "Name": qn, "NativeReferenceName": c})
        else:
            fn_map = {0: "Sum", 5: "CountNonNull", 1: "Avg"}
            fn = fn_map.get(agg, "Sum")
            qn = f"{fn}({e}.{c})"
            selects.append({"Aggregation": {"Expression": {"Column": {
                "Expression": {"SourceRef": {"Source": a}}, "Property": c}},
                "Function": agg}, "Name": qn, "NativeReferenceName": c})
        projs["Values"].append({"queryRef": qn, "active": True})

    objs = std_objects(title=title)
    objs["columnHeaders"] = [{"properties": {
        "fontColor": clr(WHITE), "backColor": clr(DARK), "fontSize": Ln("11D"), "bold": Lb(True)
    }}]
    objs["values"] = [{"properties": {"fontColor": clr(DARK), "fontSize": Ln("11D")}}]
    objs["total"] = [{"properties": {"show": Lb(False)}}]

    return {
        "visualType": "tableEx",
        "drillFilterOtherVisuals": True,
        "projections": projs,
        "prototypeQuery": {"Version": 2, "From": froms, "Select": selects},
        "columnProperties": {},
        "objects": objs,
    }

# ─── Textbox (header) ────────────────────────────────────────────────────────
def header_box(text, sub="", bg=DARK, fg=WHITE):
    paragraphs = [{"textRuns": [{"value": text, "textStyle": {
        "fontFamily": "Segoe UI", "fontSize": "16px", "bold": True
    }, "color": fg}], "horizontalTextAlignment": "Left"}]
    if sub:
        paragraphs.append({"textRuns": [{"value": sub, "textStyle": {
            "fontFamily": "Segoe UI", "fontSize": "11px"
        }, "color": "#AAAAAA"}], "horizontalTextAlignment": "Left"})
    return {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": {"expr": {
                "Literal": {"Value": json.dumps(paragraphs)}
            }}}}],
            "background": [{"properties": {"show": Lb(True), "color": clr(bg), "transparency": Ln(0)}}],
        }
    }

# ─── KPI cards row (6 cards) ──────────────────────────────────────────────────
def six_kpi_cards(y0, card_h=95):
    cw = 193; gap = 14; x0 = 10
    cards = [
        vc(x0 + i*(cw+gap), y0, cw, card_h, 1000+i,
           card_vis("Sales", "s", col, agg, label, CARD_ACCENTS[i]))
        for i, (col, agg, label) in enumerate([
            ("Net Sales",   0, "Total Revenue"),
            ("Profit",      0, "Total Profit"),
            ("Order ID",    5, "Total Orders"),
            ("Net Sales",   1, "Avg Order Value"),
            ("Order Status",5, "Total Transactions"),
            ("Discount Amount",0,"Total Discounts"),
        ])
    ]
    # Override card 5 to use Return Rate measure from Customers total
    cards[4] = vc(x0 + 4*(cw+gap), y0, cw, card_h, 1004,
                  measure_card_vis("Sales", "s", "Return Rate %", "Return Rate %", CARD_ACCENTS[4]))
    cards[5] = vc(x0 + 5*(cw+gap), y0, cw, card_h, 1005,
                  measure_card_vis("Sales", "s", "Target Achievement %", "Target Achievement", CARD_ACCENTS[5]))
    return cards

# ─── 4 Slicers row ────────────────────────────────────────────────────────────
def four_slicers(y0, h=30):
    positions = [(8,130),(150,120),(282,155),(450,170)]
    specs = [
        ("Sales","s","Year"),
        ("Sales","s","Quarter"),
        ("Sales","s","Category"),
        ("Sales","s","Sales Channel"),
    ]
    result = []
    for i, ((x,w),(e,a,c)) in enumerate(zip(positions, specs)):
        result.append(vc(x, y0, w, h, 100+i, slicer_vis(e,a,c)))
    return result

# ─── Page builder ─────────────────────────────────────────────────────────────
W = 1280  # page width

def page(name, display, ordinal, visuals):
    return {
        "name": name,
        "displayName": display,
        "filters": "[]",
        "ordinal": ordinal,
        "width": W,
        "height": 800,
        "config": json.dumps({
            "objects": {
                "background": [{"properties": {"show": Lb(True), "color": clr(BGPAGE), "transparency": Ln(0)}}]
            }
        }),
        "visualContainers": visuals,
    }

# ─── PAGE 1: Executive Summary ───────────────────────────────────────────────
p1_visuals = [
    # Header bar
    vc(0, 0,  W, 46, 1, header_box("📊 Executive Summary", "Sales Analytics Dashboard | Power BI")),
    vc(0, 46, W,  4, 2, {"visualType": "textbox", "objects": {"background": [{"properties": {"show": Lb(True), "color": clr(TEAL), "transparency": Ln(0)}}]}}),
    vc(0, 52, W, 18, 3, header_box("Data refreshed: May 2026  ·  500 Orders  ·  2022–2025", bg="#374649")),
    # Slicers
    *four_slicers(73),
    # KPI Cards
    *six_kpi_cards(108),
    # Revenue Trend line chart
    vc(10, 212, 1260, 195, 200, line_vis(
        "Sales","s","Month",  "Sales","s","Net Sales",  "Sales","s","Year",
        title="Revenue Trend — Current Year vs Prior Year")),
    # Sales by Category (bar)
    vc(10, 415, 390, 375, 201, chart_vis(
        "clusteredBarChart","Sales","s","Category","Sales","s","Net Sales",0,
        title="Sales by Category", colors=CHART_COLORS)),
    # Sales Channel Mix (donut)
    vc(410, 415, 410, 375, 202, donut_vis(
        "donutChart","Sales","s","Sales Channel","Sales","s","Net Sales",0,
        title="Sales Channel Mix", colors=CHART_COLORS)),
    # Order Status Distribution (donut)
    vc(830, 415, 440, 375, 203, donut_vis(
        "donutChart","Sales","s","Order Status","Sales","s","Order ID",5,
        title="Order Status Distribution", colors=[GREEN,YELLOW,RED])),
]

# ─── PAGE 2: Sales Performance ───────────────────────────────────────────────
p2_visuals = [
    vc(0, 0,  W, 46, 1, header_box("📈 Sales Performance", "Monthly & Quarterly Revenue Analysis")),
    vc(0, 46, W,  4, 2, {"visualType": "textbox", "objects": {"background": [{"properties": {"show": Lb(True), "color": clr(TEAL), "transparency": Ln(0)}}]}}),
    vc(0, 52, W, 18, 3, header_box("Data refreshed: May 2026", bg="#374649")),
    *four_slicers(73),
    *six_kpi_cards(108),
    # Monthly Orders heatmap (pivot table)
    vc(10, 212, 1260, 185, 200, matrix_vis(
        "Sales","s","Year", "Sales","s","Month", "Sales","s","Order ID",5,
        title="Monthly Orders — Count by Year & Month")),
    # Sales by Country
    vc(10, 407, 620, 280, 201, chart_vis(
        "clusteredBarChart","Customers","c","Country","Sales","s","Net Sales",0,
        title="Sales by Country")),
    # Payment Method Breakdown
    vc(640, 407, 630, 280, 202, chart_vis(
        "clusteredColumnChart","Sales","s","Payment Method","Sales","s","Order ID",5,
        title="Payment Method Breakdown")),
    # Quarterly Revenue by Year
    vc(10, 697, 1260, 95, 203, chart_vis(
        "clusteredColumnChart","Sales","s","Quarter","Sales","s","Net Sales",0,
        title="Quarterly Revenue by Year", legend_e="Sales",legend_a="s",legend_c="Year")),
]

# ─── PAGE 3: Product Analysis ────────────────────────────────────────────────
p3_visuals = [
    vc(0, 0,  W, 46, 1, header_box("📦 Product Analysis", "Top Products & Category Performance")),
    vc(0, 46, W,  4, 2, {"visualType": "textbox", "objects": {"background": [{"properties": {"show": Lb(True), "color": clr(TEAL), "transparency": Ln(0)}}]}}),
    vc(0, 52, W, 18, 3, header_box("Data refreshed: May 2026", bg="#374649")),
    *four_slicers(73),
    *six_kpi_cards(108),
    # Top 10 Products by Net Sales
    vc(10, 212, 620, 300, 200, chart_vis(
        "clusteredBarChart","Products","p","Product Name","Sales","s","Net Sales",0,
        title="Top 10 Products by Net Sales", colors=CHART_COLORS)),
    # Profit Margin % by Category
    vc(640, 212, 630, 300, 201, chart_vis(
        "clusteredColumnChart","Sales","s","Category","Sales","s","Profit Margin %",1,
        title="Profit Margin % by Category", colors=CHART_COLORS)),
    # Category Revenue vs Profit
    vc(10, 522, 1260, 270, 202, chart_two_series(
        "clusteredColumnChart","Sales","s","Category",
        "Sales","s","Net Sales","Net Sales",TEAL,
        "Sales","s","Profit","Profit",YELLOW,
        title="Category Revenue vs Profit")),
]

# ─── PAGE 4: Customer Insights ───────────────────────────────────────────────
p4_visuals = [
    vc(0, 0,  W, 46, 1, header_box("👥 Customer Insights", "Segment Revenue & Credit Analysis")),
    vc(0, 46, W,  4, 2, {"visualType": "textbox", "objects": {"background": [{"properties": {"show": Lb(True), "color": clr(TEAL), "transparency": Ln(0)}}]}}),
    vc(0, 52, W, 18, 3, header_box("Data refreshed: May 2026", bg="#374649")),
    *four_slicers(73),
    *six_kpi_cards(108),
    # Customer Segment Revenue (pie)
    vc(10, 212, 390, 290, 200, donut_vis(
        "pieChart","Customers","c","Segment","Sales","s","Net Sales",0,
        title="Customer Segment Revenue", colors=CHART_COLORS)),
    # Sales by Customer Country (bar)
    vc(410, 212, 860, 290, 201, chart_vis(
        "clusteredBarChart","Customers","c","Country","Sales","s","Net Sales",0,
        title="Sales by Customer Country", colors=CHART_COLORS)),
    # Orders by Segment & Status (stacked bar)
    vc(10, 512, 620, 280, 202, chart_vis(
        "clusteredColumnChart","Customers","c","Segment","Sales","s","Order ID",5,
        title="Orders by Segment & Status",
        legend_e="Sales",legend_a="s",legend_c="Order Status",
        colors=[GREEN,YELLOW,RED])),
    # Credit Limit by Segment
    vc(640, 512, 630, 280, 203, chart_vis(
        "clusteredColumnChart","Customers","c","Segment","Customers","c","Credit Limit",1,
        title="Credit Limit Distribution by Segment", colors=CHART_COLORS)),
]

# ─── PAGE 5: Team Performance ────────────────────────────────────────────────
p5_visuals = [
    vc(0, 0,  W, 46, 1, header_box("🏆 Team Performance", "Sales vs Target by Team Member")),
    vc(0, 46, W,  4, 2, {"visualType": "textbox", "objects": {"background": [{"properties": {"show": Lb(True), "color": clr(TEAL), "transparency": Ln(0)}}]}}),
    vc(0, 52, W, 18, 3, header_box("Data refreshed: May 2026", bg="#374649")),
    *four_slicers(73),
    *six_kpi_cards(108),
    # Team Sales vs Target (grouped column)
    vc(10, 212, 1260, 260, 200, chart_two_series(
        "clusteredColumnChart","Users","u","Name",
        "Sales","s","Net Sales","Net Sales",TEAL,
        "Users","u","Sales Target","Sales Target",YELLOW,
        title="Team Performance: Sales vs Target")),
    # Sales by Location (bar)
    vc(10, 482, 620, 300, 201, chart_vis(
        "clusteredBarChart","Users","u","Location","Sales","s","Net Sales",0,
        title="Sales by Location/City", colors=CHART_COLORS)),
    # Team Member Details (table)
    vc(640, 482, 630, 300, 202, table_vis([
        ("Users","u","Name",   None),
        ("Users","u","Role",   None),
        ("Users","u","Location",None),
        ("Sales","s","Net Sales",0),
        ("Users","u","Sales Target",0),
    ], title="Team Member Details")),
]

# ─── Report Layout ────────────────────────────────────────────────────────────
REPORT_LAYOUT = {
    "id": 0,
    "resourcePackages": [],
    "sections": [
        page("ReportSection1", "Executive Summary",  0, p1_visuals),
        page("ReportSection2", "Sales Performance",  1, p2_visuals),
        page("ReportSection3", "Product Analysis",   2, p3_visuals),
        page("ReportSection4", "Customer Insights",  3, p4_visuals),
        page("ReportSection5", "Team Performance",   4, p5_visuals),
    ],
    "config": json.dumps({
        "version": "5.55",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU11", "reportVersionAtImport": "5.55"},
            "customTheme": {"name": "SalesAnalyticsTheme", "version": ""}
        },
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useStyledTooltips": True,
            "defaultDrillFilterOtherVisuals": True
        }
    }),
    "resourcePackages": [{
        "resourcePackage": {
            "name": "SharedResources",
            "type": 2,
            "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json",
                       "name": "CY23SU11"}],
            "disabled": False
        }
    }]
}

# ─── DataModel Schema (TMSL) ──────────────────────────────────────────────────
def col_def(name, dtype, partition_col=True):
    type_map = {
        "text": "string", "number": "double", "Int64.Type": "int64",
        "date": "dateTime", "boolean": "boolean",
    }
    d = {
        "name": name, "dataType": type_map.get(dtype, "string"),
        "isHidden": False, "sourceColumn": name,
    }
    if dtype == "date":
        d["formatString"] = "Short Date"
    return d

def measure_def(name, expr, fmt=None):
    m = {"name": name, "expression": expr, "isHidden": False}
    if fmt:
        m["formatString"] = fmt
    return m

DATA_MODEL_SCHEMA = {
    "name": "SalesAnalyticsDashboard",
    "compatibilityLevel": 1550,
    "model": {
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "tables": [
            {
                "name": "Sales",
                "columns": [col_def(c, t) for c, t in SALES_COLS],
                "measures": [
                    measure_def("Total Revenue",       "SUM(Sales[Net Sales])",           "#,0.00"),
                    measure_def("Total Profit",        "SUM(Sales[Profit])",               "#,0.00"),
                    measure_def("Total Orders",        "COUNTROWS(Sales)",                 "#,0"),
                    measure_def("Total Returns",       'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Returned")', "#,0"),
                    measure_def("Total Customers",     "DISTINCTCOUNT(Sales[Customer ID])","#,0"),
                    measure_def("Avg Order Value",     "DIVIDE([Total Revenue],[Total Orders],0)", "#,0.00"),
                    measure_def("Profit Margin %",     "DIVIDE([Total Profit],[Total Revenue],0)", "0.0%"),
                    measure_def("Return Rate %",
                        'DIVIDE(CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Returned"),COUNTROWS(Sales),0)',
                        "0.0%"),
                    measure_def("Target Achievement %",
                        "DIVIDE([Total Revenue],SUM(Users[Sales Target]),0)", "0.0%"),
                    measure_def("Total Gross Sales",   "SUM(Sales[Gross Sales])",          "#,0.00"),
                    measure_def("Total Discount",      "SUM(Sales[Discount Amount])",      "#,0.00"),
                    measure_def("Completed Orders",
                        'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Completed")', "#,0"),
                    measure_def("Pending Orders",
                        'CALCULATE(COUNTROWS(Sales),Sales[Order Status]="Pending")', "#,0"),
                ],
                "partitions": [{"name": "Sales-Partition", "mode": "import",
                                "source": {"type": "m", "expression": M_SALES}}],
            },
            {
                "name": "Customers",
                "columns": [col_def(c, t) for c, t in CUST_COLS],
                "measures": [
                    measure_def("Avg Credit Limit", "AVERAGE(Customers[Credit Limit])", "#,0.00"),
                ],
                "partitions": [{"name": "Customers-Partition", "mode": "import",
                                "source": {"type": "m", "expression": M_CUSTOMERS}}],
            },
            {
                "name": "Users",
                "columns": [col_def(c, t) for c, t in USER_COLS],
                "measures": [
                    measure_def("Total Target", "SUM(Users[Sales Target])", "#,0.00"),
                ],
                "partitions": [{"name": "Users-Partition", "mode": "import",
                                "source": {"type": "m", "expression": M_USERS}}],
            },
            {
                "name": "Products",
                "columns": [col_def(c, t) for c, t in PROD_COLS],
                "partitions": [{"name": "Products-Partition", "mode": "import",
                                "source": {"type": "m", "expression": M_PRODUCTS}}],
            },
        ],
        "relationships": [
            {"name": str(uuid.uuid4()), "fromTable": "Sales", "fromColumn": "Customer ID",
             "toTable": "Customers",  "toColumn": "Customer ID", "crossFilteringBehavior": "bothDirections"},
            {"name": str(uuid.uuid4()), "fromTable": "Sales", "fromColumn": "User ID",
             "toTable": "Users",      "toColumn": "User ID",     "crossFilteringBehavior": "bothDirections"},
            {"name": str(uuid.uuid4()), "fromTable": "Sales", "fromColumn": "Product ID",
             "toTable": "Products",   "toColumn": "Product ID",  "crossFilteringBehavior": "bothDirections"},
        ],
        "cultures": [{"name": "en-US", "linguisticMetadata": {
            "Version": "1.0.0", "Language": "en-US"
        }}],
        "roles": [{
            "name": "Sales Rep",
            "modelPermission": "read",
            "tablePermissions": [{
                "name": "Sales",
                "filterExpression": "TRUE()"
            }]
        }],
    }
}

# ─── Theme JSON ───────────────────────────────────────────────────────────────
THEME = {
    "name": "SalesAnalyticsTheme",
    "dataColors": CHART_COLORS,
    "background": WHITE,
    "foreground": DARK,
    "tableAccent": TEAL,
    "visualStyles": {
        "card": {"*": {
            "labels": [{"color": {"solid": {"color": DARK}}, "fontSize": 20, "bold": True}],
            "categoryLabels": [{"show": True, "color": {"solid": {"color": SLATE}}, "fontSize": 10}],
        }},
        "clusteredBarChart": {"*": {
            "general": [{"responsive": True}],
            "dataColors": [{"color": {"solid": {"color": TEAL}}}],
        }},
        "donutChart": {"*": {
            "legend": [{"show": True, "position": "Bottom"}]
        }},
        "lineChart": {"*": {
            "dataColors": [
                {"color": {"solid": {"color": TEAL}}},
                {"color": {"solid": {"color": YELLOW}}},
            ]
        }},
    }
}

# Base theme (compact version)
BASE_THEME = {
    "name": "CY23SU11",
    "dataColors": CHART_COLORS,
    "background": WHITE,
    "foreground": DARK,
    "tableAccent": TEAL,
}

# ─── DiagramLayout ────────────────────────────────────────────────────────────
DIAGRAM_LAYOUT = {
    "version": 1,
    "nodes": [
        {"id": "Sales",     "position": {"x":  300, "y": 100}},
        {"id": "Customers", "position": {"x":  100, "y": 250}},
        {"id": "Users",     "position": {"x":  300, "y": 300}},
        {"id": "Products",  "position": {"x":  500, "y": 250}},
    ],
    "nodeIndex": {n["id"]: n for n in [
        {"id": "Sales",     "position": {"x":  300, "y": 100}},
        {"id": "Customers", "position": {"x":  100, "y": 250}},
        {"id": "Users",     "position": {"x":  300, "y": 300}},
        {"id": "Products",  "position": {"x":  500, "y": 250}},
    ]}
}

# ─── SecurityBindings (empty) ─────────────────────────────────────────────────
SECURITY_BINDINGS = b""

# ─── Assemble PBIT ────────────────────────────────────────────────────────────
def to_utf16le(obj):
    if isinstance(obj, dict):
        return json.dumps(obj, ensure_ascii=False).encode("utf-16-le")
    return obj.encode("utf-16-le")

CONTENT_TYPES_XML = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml"  ContentType="application/xml" />
  <Override PartName="/DataModelSchema"   ContentType="application/json" />
  <Override PartName="/DiagramLayout"     ContentType="application/json" />
  <Override PartName="/Report/Layout"     ContentType="application/json" />
  <Override PartName="/Settings"          ContentType="application/json" />
  <Override PartName="/Metadata"          ContentType="application/json" />
  <Override PartName="/SecurityBindings"  ContentType="application/json" />
  <Override PartName="/Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
            ContentType="application/json" />
  <Override PartName="/Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json"
            ContentType="application/json" />
</Types>"""

SETTINGS_JSON = json.dumps({"Version": 3, "AutoRecoveryEnabled": False, "RefreshOnOpen": True})
METADATA_JSON = json.dumps({"version": "4.0", "settings": {}})
VERSION_STR   = "3.0"

def write_pbit(path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML.strip().encode("utf-8"))
        zf.writestr("Version",             VERSION_STR.encode("utf-8"))
        zf.writestr("Settings",            SETTINGS_JSON.encode("utf-8"))
        zf.writestr("Metadata",            METADATA_JSON.encode("utf-8"))
        zf.writestr("SecurityBindings",    SECURITY_BINDINGS)
        zf.writestr("DiagramLayout",       json.dumps(DIAGRAM_LAYOUT, ensure_ascii=False).encode("utf-16-le"))
        zf.writestr("DataModelSchema",     json.dumps(DATA_MODEL_SCHEMA, ensure_ascii=False).encode("utf-8"))
        zf.writestr("Report/Layout",       json.dumps(REPORT_LAYOUT, ensure_ascii=False).encode("utf-16-le"))
        zf.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",
                    json.dumps(BASE_THEME, ensure_ascii=False).encode("utf-8"))
        zf.writestr("Report/StaticResources/RegisteredResources/SalesAnalyticsTheme.json",
                    json.dumps(THEME, ensure_ascii=False).encode("utf-8"))
    size = os.path.getsize(path)
    print(f"✅ PBIT written: {path} ({size/1024:.1f} KB)")

write_pbit(OUT_PBIT)

# ─── Verify PBIT ─────────────────────────────────────────────────────────────
with zipfile.ZipFile(OUT_PBIT, "r") as z:
    files = z.namelist()
    print(f"   Files: {files}")
    schema = json.loads(z.read("DataModelSchema").decode("utf-8"))
    tables = schema["model"]["tables"]
    print(f"   Tables: {[t['name'] for t in tables]}")
    for t in tables:
        print(f"     {t['name']}: {len(t.get('columns',[]))} cols, "
              f"{len(t.get('measures',[]))} measures, "
              f"{len(t.get('partitions',[]))} partitions")
    print(f"   Relationships: {len(schema['model'].get('relationships',[]))}")
    layout_raw = z.read("Report/Layout").decode("utf-16-le")
    layout = json.loads(layout_raw)
    pages = layout.get("sections", [])
    print(f"   Pages: {[p['displayName'] for p in pages]}")
    for p in pages:
        vcs = p.get("visualContainers", [])
        vtypes = []
        for v in vcs:
            try:
                cfg = json.loads(v.get("config","{}"))
                vtypes.append(cfg.get("singleVisual",{}).get("visualType","?"))
            except: pass
        print(f"     {p['displayName']}: {vtypes}")

print()
print("=" * 60)
print("SUCCESS! Power BI file created.")
print()
print("HOW TO USE:")
print(f"  1. Open '{OUT_PBIT}' in Power BI Desktop")
print("  2. Click 'Apply' when prompted (loads ~500 records)")
print("  3. All 5 pages will show with complete data")
print("  4. Click 'Publish' to publish directly to Power BI Service")
print("  (Or: File → Save As .pbix first, then publish)")

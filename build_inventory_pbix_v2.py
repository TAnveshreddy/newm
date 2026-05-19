#!/usr/bin/env python3
"""
Build Inventory_Position_vs_Target_Range.pbix (v2).
Single Deneb visual containing table columns + range bar chart via hconcat.
"""
import zipfile
import json
import os

SRC = "/root/.claude/uploads/1bd7e774-dea6-4fb5-b942-eeaa2c6a7dc4/132cd7d7-Denab_1.pbix"
DST = "/home/user/newm/Inventory_Position_vs_Target_Range.pbix"

# ── Read source ──────────────────────────────────────────────────────────────
with zipfile.ZipFile(SRC, "r") as z:
    raw = {m: z.read(m) for m in z.namelist()}

# ── Decode Layout ────────────────────────────────────────────────────────────
layout_bytes = raw["Report/Layout"]
try:
    layout_text = layout_bytes.decode("utf-16-le")
    enc = "utf-16-le"
except Exception:
    layout_text = layout_bytes.decode("utf-8")
    enc = "utf-8"

layout = json.loads(layout_text)
pages = layout.get("sections", [])

# Use first page (Inventory Fluctuation Process)
target_page = pages[0]
visuals = target_page.get("visualContainers", [])

# Find existing Deneb visual to preserve its data bindings / visual type id
deneb_visual = None
for v in visuals:
    try:
        cfg = json.loads(v.get("config", "{}"))
    except Exception:
        cfg = {}
    vtype = cfg.get("singleVisual", {}).get("visualType", "")
    if "deneb" in vtype.lower():
        deneb_visual = v
        break

assert deneb_visual, "Deneb visual not found in source file!"

# ── Build single Deneb Vega-Lite spec (table + chart) ────────────────────────
#
# Column definitions:  display title  →  Dummy field name
COLUMNS = [
    ("Region",               "Scheduling Region"),
    ("Location Name",        "Location Name"),
    ("Commodity",            "Scheduling Zone"),
    ("Working Min Capacity", "Draw To Low"),
    ("Target Min",           "Historical Low"),
    ("Actual Inventory",     "Current Inventory"),
    ("Target Max",           "Historical High"),
    ("Working Max Capacity", "Build To High 2"),
    ("Sub Group",            "LIFO Position"),
]

# Shared y encoding (used in every sub-view)
Y_ENC = {
    "field": "__index__",
    "type": "ordinal",
    "sort": None,
    "axis": None,
    "scale": {"paddingInner": 0.25}
}

# ── Text-column sub-views ─────────────────────────────────────────────────────
def text_col(title, field, width=90):
    return {
        "width": width,
        "layer": [
            # Header row (use a transform / filter trick — just put title as mark title)
            {
                "mark": {
                    "type": "text",
                    "align": "left",
                    "fontSize": 11,
                    "fontWeight": "normal",
                    "color": "#323130",
                    "dx": 4
                },
                "encoding": {
                    "y": Y_ENC,
                    "text": {"field": field, "type": "nominal"}
                }
            }
        ],
        "title": {
            "text": title,
            "align": "left",
            "anchor": "start",
            "fontSize": 11,
            "fontWeight": "bold",
            "color": "#323130",
            "offset": 4
        }
    }

# Numeric columns (right-align, narrower)
def num_col(title, field, width=80):
    col = text_col(title, field, width)
    col["layer"][0]["mark"]["align"] = "right"
    col["layer"][0]["mark"]["dx"] = -4
    col["layer"][0]["encoding"]["text"] = {
        "field": field,
        "type": "quantitative",
        "format": ",.0f"
    }
    col["title"]["align"] = "right"
    return col

text_cols = [
    text_col("Region",               "Scheduling Region",  width=70),
    text_col("Location Name",        "Location Name",      width=120),
    text_col("Commodity",            "Scheduling Zone",    width=80),
    num_col ("Working Min Capacity", "Draw To Low",        width=95),
    num_col ("Target Min",           "Historical Low",     width=75),
    num_col ("Actual Inventory",     "Current Inventory",  width=85),
    num_col ("Target Max",           "Historical High",    width=75),
    num_col ("Working Max Capacity", "Build To High 2",    width=95),
    text_col("Sub Group",            "LIFO Position",      width=70),
]

# ── Range-bar chart sub-view ──────────────────────────────────────────────────
chart_view = {
    "width": 320,
    "title": {
        "text": "Inventory vs Target Range",
        "fontSize": 11,
        "fontWeight": "bold",
        "color": "#323130",
        "anchor": "start",
        "offset": 4
    },
    "layer": [
        {
            "mark": {
                "type": "bar",
                "height": {"band": 0.28},
                "color": "#d3d3d3",
                "stroke": "#aaaaaa",
                "strokeWidth": 0.8
            },
            "encoding": {
                "y": Y_ENC,
                "x": {
                    "field": "Historical Low",
                    "type": "quantitative",
                    "scale": {"domain": [0, 500000]},
                    "axis": {
                        "title": "Inventory (Barrels)",
                        "titleFontSize": 10,
                        "labelExpr": "datum.value === 0 ? '0K' : format(datum.value/1000, '.0f') + 'K'",
                        "tickCount": 6,
                        "grid": True,
                        "gridColor": "#eeeeee"
                    }
                },
                "x2": {"field": "Historical High"}
            }
        },
        {
            "mark": {
                "type": "point",
                "filled": True,
                "size": 80,
                "color": "black",
                "opacity": 1
            },
            "encoding": {
                "y": {
                    "field": "__index__",
                    "type": "ordinal",
                    "sort": None,
                    "axis": None
                },
                "x": {
                    "field": "Current Inventory",
                    "type": "quantitative"
                }
            }
        }
    ]
}

# ── Compose full hconcat spec ─────────────────────────────────────────────────
# Add shared y-axis (row labels) only on the first text column
text_cols[0]["layer"][0]["encoding"]["y"] = {
    "field": "__index__",
    "type": "ordinal",
    "sort": None,
    "axis": {
        "title": None,
        "labels": False,
        "ticks": False,
        "grid": False,
        "domain": False
    },
    "scale": {"paddingInner": 0.25}
}

DENEB_SPEC = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"name": "dataset"},
    "width": "container",
    "height": "container",
    "spacing": 0,
    "hconcat": text_cols + [chart_view],
    "config": {
        "view": {"stroke": None},
        "background": "white",
        "concat": {"spacing": 2},
        "axis": {
            "domain": False,
            "ticks": False,
            "labelFontSize": 10,
            "titleFontSize": 10
        }
    }
}

DENEB_SPEC_STR = json.dumps(DENEB_SPEC, separators=(",", ":"))

# ── Update Deneb visual config ────────────────────────────────────────────────
try:
    cfg = json.loads(deneb_visual.get("config", "{}"))
except Exception:
    cfg = {}

sv = cfg.setdefault("singleVisual", {})
vc = sv.setdefault("vcObjects", {})

deneb_objs = vc.get("deneb", [{}])
if not deneb_objs:
    deneb_objs = [{}]

props = deneb_objs[0].setdefault("properties", {})
# Double-encode: Power BI stores the JSON spec as a JSON string literal
spec_escaped = json.dumps(DENEB_SPEC_STR)
props["jsonSpec"] = {
    "expr": {
        "Literal": {
            "Value": spec_escaped
        }
    }
}
deneb_objs[0]["properties"] = props
vc["deneb"] = deneb_objs

# Full-width single visual: fill the content area
deneb_visual["x"] = 20
deneb_visual["y"] = 58
deneb_visual["width"] = 1450
deneb_visual["height"] = 730
deneb_visual["config"] = json.dumps(cfg, separators=(",", ":"))

# ── Helper: make a textbox visual ────────────────────────────────────────────
def make_textbox(x, y, w, h, text, font_size=14, bold=False, color="#323130"):
    paragraphs = [{
        "horizontalTextAlignment": "Left",
        "textRuns": [{
            "value": text,
            "textStyle": {
                "fontWeight": "bold" if bold else "normal",
                "fontSize": f"{font_size}pt",
                "color": color
            }
        }]
    }]
    cfg = {
        "singleVisual": {
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "paragraphs": {
                            "expr": {"Literal": {"Value": json.dumps(paragraphs)}}
                        }
                    }
                }]
            }
        }
    }
    return {
        "x": x, "y": y, "width": w, "height": h,
        "config": json.dumps(cfg, separators=(",", ":")),
        "filters": "[]", "tabOrder": 0,
        "singleVisualGroup": None, "z": 0
    }

def make_shape(x, y, w, h, fill_color="#cccccc"):
    cfg = {
        "singleVisual": {
            "visualType": "shape",
            "objects": {
                "line": [{
                    "properties": {
                        "lineColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{fill_color}'"}}}}},
                        "weight": {"expr": {"Literal": {"Value": "2D"}}}
                    }
                }]
            }
        }
    }
    return {
        "x": x, "y": y, "width": w, "height": h,
        "config": json.dumps(cfg, separators=(",", ":")),
        "filters": "[]", "tabOrder": 0,
        "singleVisualGroup": None, "z": 0
    }

# ── Assemble page ─────────────────────────────────────────────────────────────
target_page["displayName"] = "Inventory Position vs Target Range"
target_page["width"] = 1500
target_page["height"] = 800

target_page["visualContainers"] = [
    make_textbox(20, 6, 800, 46,
                 "Inventory Position vs Target Range",
                 font_size=18, bold=True, color="#1e3a5f"),
    make_textbox(860, 6, 620, 46,
                 "● Actual Inventory    ▬ Target Min – Target Max Range",
                 font_size=10, bold=False, color="#555555"),
    make_shape(10, 53, 1470, 2, fill_color="#cccccc"),
    deneb_visual,   # single combined visual
]

layout["sections"] = [target_page]

# ── Serialise ─────────────────────────────────────────────────────────────────
updated_text = json.dumps(layout, ensure_ascii=False, separators=(",", ":"))
raw["Report/Layout"] = updated_text.encode(enc)

# ── Write pbix ────────────────────────────────────────────────────────────────
with zipfile.ZipFile(DST, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for name, data in raw.items():
        if name == "DataModel":
            zout.writestr(
                zipfile.ZipInfo(name), data,
                compress_type=zipfile.ZIP_STORED
            )
        else:
            zout.writestr(name, data)

size = os.path.getsize(DST)
print(f"Written: {DST}  ({size:,} bytes)")

# Quick verify
with zipfile.ZipFile(DST) as z:
    layout2 = json.loads(z.read("Report/Layout").decode(enc))
    page2 = layout2["sections"][0]
    print(f"Page: '{page2['displayName']}'  {page2['width']}x{page2['height']}")
    for v in page2["visualContainers"]:
        vtype = json.loads(v["config"]).get("singleVisual", {}).get("visualType", "?")
        print(f"  {vtype}: {v['width']}x{v['height']} @ ({v['x']},{v['y']})")

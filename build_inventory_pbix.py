#!/usr/bin/env python3
"""
Build Inventory_Position_vs_Target_Range.pbix from Denab_1.pbix source.
Modifies the report page to match the Inventory Position vs Target Range screenshot.
"""
import zipfile
import json
import shutil
import os
import re

SRC = "/root/.claude/uploads/1bd7e774-dea6-4fb5-b942-eeaa2c6a7dc4/132cd7d7-Denab_1.pbix"
DST = "/home/user/newm/Inventory_Position_vs_Target_Range.pbix"

# ── Read source ──────────────────────────────────────────────────────────────
with zipfile.ZipFile(SRC, "r") as z:
    members = z.namelist()
    print("Source members:", members)

    raw = {}
    for m in members:
        raw[m] = z.read(m)

# ── Decode Layout ────────────────────────────────────────────────────────────
layout_bytes = raw.get("Report/Layout", b"")
# Try UTF-16 LE (standard for pbix), fall back to UTF-8
try:
    layout_text = layout_bytes.decode("utf-16-le")
    layout_encoding = "utf-16-le"
    print("Layout encoding: UTF-16 LE")
except Exception:
    layout_text = layout_bytes.decode("utf-8")
    layout_encoding = "utf-8"
    print("Layout encoding: UTF-8")

layout = json.loads(layout_text)

# ── Inspect existing pages / visuals ─────────────────────────────────────────
pages = layout.get("sections", [])
print(f"Pages ({len(pages)}):", [p.get("displayName") for p in pages])

for pi, page in enumerate(pages):
    visuals = page.get("visualContainers", [])
    print(f"  Page {pi} '{page.get('displayName')}': {len(visuals)} visuals")
    for vi, v in enumerate(visuals):
        cfg_str = v.get("config", "{}")
        try:
            cfg = json.loads(cfg_str)
        except Exception:
            cfg = {}
        vtype = (cfg.get("singleVisual", {})
                    .get("visualType", "?"))
        print(f"    Visual {vi}: type={vtype}, x={v.get('x')}, y={v.get('y')}, w={v.get('width')}, h={v.get('height')}")

# ── Extract Deneb spec from existing visual ──────────────────────────────────
target_page = pages[0]  # assume first (only) page
visuals = target_page.get("visualContainers", [])

deneb_visual = None
table_visual = None
for v in visuals:
    try:
        cfg = json.loads(v.get("config", "{}"))
    except Exception:
        cfg = {}
    vtype = cfg.get("singleVisual", {}).get("visualType", "")
    if "deneb" in vtype.lower():
        deneb_visual = v
    elif vtype in ("tableEx", "table"):
        table_visual = v

print(f"\nFound deneb_visual: {deneb_visual is not None}")
print(f"Found table_visual: {table_visual is not None}")

# ── Build updated Deneb Vega-Lite spec ───────────────────────────────────────
DENEB_SPEC = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "data": {"name": "dataset"},
    "width": "container",
    "height": "container",
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
                "y": {
                    "field": "__index__",
                    "type": "ordinal",
                    "sort": None,
                    "axis": None,
                    "scale": {"padding": 0.35}
                },
                "x": {
                    "field": "Historical Low",
                    "type": "quantitative",
                    "scale": {"domain": [0, 500000]},
                    "axis": {
                        "title": "Inventory (Barrels)",
                        "titleFontSize": 11,
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
                "size": 90,
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
    ],
    "config": {
        "view": {"stroke": None},
        "background": "white"
    }
}

DENEB_SPEC_STR = json.dumps(DENEB_SPEC, separators=(",", ":"))

# ── Column mapping for tableEx ────────────────────────────────────────────────
# screenshot col name → Dummy table field name
COL_MAP = {
    "Region": "Scheduling Region",
    "Location Name": "Location Name",
    "Commodity": "Scheduling Zone",
    "Working Min Capacity": "Draw To Low",
    "Target Min": "Historical Low",
    "Actual Inventory": "Current Inventory",
    "Target Max": "Historical High",
    "Working Max Capacity": "Build To High 2",
    "Sub Group": "LIFO Position",
}

# ── Update Deneb visual config ────────────────────────────────────────────────
def update_deneb_visual(v):
    try:
        cfg = json.loads(v.get("config", "{}"))
    except Exception:
        cfg = {}

    sv = cfg.setdefault("singleVisual", {})
    vc = sv.setdefault("vcObjects", {})

    # Update the deneb spec stored in vcObjects.deneb[0].properties.jsonSpec.expr.Literal.Value
    deneb_objs = vc.get("deneb", [{}])
    if not deneb_objs:
        deneb_objs = [{}]
    props = deneb_objs[0].setdefault("properties", {})

    # Escape the spec as a JSON string literal (Power BI stores it double-encoded)
    spec_escaped = json.dumps(DENEB_SPEC_STR)  # double-encode
    props["jsonSpec"] = {
        "expr": {
            "Literal": {
                "Value": spec_escaped
            }
        }
    }
    deneb_objs[0]["properties"] = props
    vc["deneb"] = deneb_objs

    # Reposition / resize Deneb visual to right panel
    v["x"] = 1090
    v["y"] = 58
    v["width"] = 390
    v["height"] = 730
    v["config"] = json.dumps(cfg, separators=(",", ":"))
    return v


def update_table_visual(v):
    try:
        cfg = json.loads(v.get("config", "{}"))
    except Exception:
        cfg = {}

    sv = cfg.setdefault("singleVisual", {})

    # Build projections (column order) for tableEx
    projections = []
    for display_name, field_name in COL_MAP.items():
        projections.append({
            "queryRef": f"Dummy.{field_name}",
            "active": True
        })
    sv["projections"] = {"Values": projections}

    # Reposition table to left panel
    v["x"] = 20
    v["y"] = 58
    v["width"] = 1060
    v["height"] = 730
    v["config"] = json.dumps(cfg, separators=(",", ":"))
    return v


# ── Build title textbox ───────────────────────────────────────────────────────
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
        "x": x, "y": y,
        "width": w, "height": h,
        "config": json.dumps(cfg, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": 0,
        "singleVisualGroup": None,
        "z": 0
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
        "x": x, "y": y,
        "width": w, "height": h,
        "config": json.dumps(cfg, separators=(",", ":")),
        "filters": "[]",
        "tabOrder": 0,
        "singleVisualGroup": None,
        "z": 0
    }


# ── Modify the page ───────────────────────────────────────────────────────────
target_page["displayName"] = "Inventory Position vs Target Range"
target_page["width"] = 1500
target_page["height"] = 800

new_visuals = []

# Title
new_visuals.append(make_textbox(
    x=20, y=6, w=740, h=46,
    text="Inventory Position vs Target Range",
    font_size=18, bold=True, color="#1e3a5f"
))

# Legend
legend_text = "● Actual Inventory    ▬ Target Min – Target Max Range"
new_visuals.append(make_textbox(
    x=1100, y=6, w=380, h=46,
    text=legend_text,
    font_size=10, bold=False, color="#555555"
))

# Separator line (use a thin shape)
new_visuals.append(make_shape(x=10, y=53, w=1460, h=2, fill_color="#cccccc"))

# Update and add Deneb visual
if deneb_visual:
    new_visuals.append(update_deneb_visual(deneb_visual))
else:
    print("WARNING: No Deneb visual found in source file!")

# Update and add table visual
if table_visual:
    new_visuals.append(update_table_visual(table_visual))
else:
    print("WARNING: No table visual found — skipping table.")

target_page["visualContainers"] = new_visuals

# Only keep this one page
layout["sections"] = [target_page]

# ── Serialise updated Layout ──────────────────────────────────────────────────
updated_layout_text = json.dumps(layout, ensure_ascii=False, separators=(",", ":"))
if layout_encoding == "utf-16-le":
    updated_layout_bytes = updated_layout_text.encode("utf-16-le")
else:
    updated_layout_bytes = updated_layout_text.encode("utf-8")

raw["Report/Layout"] = updated_layout_bytes

# ── Write new pbix ────────────────────────────────────────────────────────────
with zipfile.ZipFile(DST, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for name, data in raw.items():
        if name == "DataModel":
            # DataModel MUST be stored uncompressed
            zout.writestr(
                zipfile.ZipInfo(name),
                data,
                compress_type=zipfile.ZIP_STORED
            )
        else:
            zout.writestr(name, data)

print(f"\nWrote {DST} ({os.path.getsize(DST):,} bytes)")

# ── Verify ────────────────────────────────────────────────────────────────────
with zipfile.ZipFile(DST, "r") as z:
    members_out = z.namelist()
    print("Output members:", members_out)
    info_list = z.infolist()
    for info in info_list:
        print(f"  {info.filename}: compress={info.compress_type}, size={info.file_size:,}")

print("\nDone!")

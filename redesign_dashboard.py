#!/usr/bin/env python3
"""
Redesign Power BI dashboard - Sales Performance page redesign
"""
import json
import uuid
import zipfile
import shutil
import os

# ─── Helpers ───────────────────────────────────────────────────────────────────

def vname():
    return uuid.uuid4().hex[:20]

def make_card(x, y, w, h, entity, alias, col, agg_fn, label, tab):
    """agg_fn: 0=Sum, 1=Avg, 5=CountNonNull"""
    if agg_fn == 0:
        qn = f"Sum({entity}.{col})"
    elif agg_fn == 1:
        qn = f"Avg({entity}.{col})"
    else:
        qn = f"CountNonNull({entity}.{col})"

    select_item = {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": alias}},
                    "Property": col
                }
            },
            "Function": agg_fn
        },
        "Name": qn,
        "NativeReferenceName": label
    }

    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname(),
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "card",
                "projections": {"Values": [{"queryRef": qn}]},
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                    "Select": [select_item]
                },
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "title": [{"properties": {
                        "text": {"expr": {"Literal": {"Value": f"'{label}'"}}},
                        "show": {"expr": {"Literal": {"Value": "true"}}}
                    }}]
                }
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


def make_bar(x, y, w, h, ce, ca, cc, ve, va, vc_, agg_fn, label, tab, vtype="clusteredBarChart"):
    cqn = f"{ce}.{cc}"
    if agg_fn == 0:
        vqn = f"Sum({ve}.{vc_})"
    elif agg_fn == 5:
        vqn = f"CountNonNull({ve}.{vc_})"
    else:
        vqn = f"Count({ve}.{vc_})"

    froms = [{"Name": ca, "Entity": ce, "Type": 0}]
    if va != ca:
        froms.append({"Name": va, "Entity": ve, "Type": 0})

    if agg_fn == 0:
        agg_select = {
            "Aggregation": {
                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": va}}, "Property": vc_}},
                "Function": 0
            },
            "Name": vqn,
            "NativeReferenceName": label
        }
    else:
        agg_select = {
            "Aggregation": {
                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": va}}, "Property": vc_}},
                "Function": 5
            },
            "Name": vqn,
            "NativeReferenceName": label
        }

    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname(),
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": vtype,
                "projections": {
                    "Category": [{"queryRef": cqn, "active": True}],
                    "Y": [{"queryRef": vqn}]
                },
                "prototypeQuery": {
                    "Version": 2,
                    "From": froms,
                    "Select": [
                        {
                            "Column": {
                                "Expression": {"SourceRef": {"Source": ca}},
                                "Property": cc
                            },
                            "Name": cqn,
                            "NativeReferenceName": cc
                        },
                        agg_select
                    ],
                    "OrderBy": [{
                        "Direction": 2,
                        "Expression": {
                            "Aggregation": {
                                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": va}}, "Property": vc_}},
                                "Function": agg_fn if agg_fn != 5 else 5
                            }
                        }
                    }]
                },
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "title": [{"properties": {
                        "text": {"expr": {"Literal": {"Value": f"'{label}'"}}},
                        "show": {"expr": {"Literal": {"Value": "true"}}}
                    }}]
                }
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


def make_line_chart(x, y, w, h, entity, alias, date_col, val_col, label, tab):
    cqn = f"{entity}.{date_col}"
    vqn = f"Sum({entity}.{val_col})"
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname(),
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "lineChart",
                "projections": {
                    "Category": [{"queryRef": cqn, "active": True}],
                    "Y": [{"queryRef": vqn}]
                },
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                    "Select": [
                        {
                            "Column": {
                                "Expression": {"SourceRef": {"Source": alias}},
                                "Property": date_col
                            },
                            "Name": cqn,
                            "NativeReferenceName": date_col
                        },
                        {
                            "Aggregation": {
                                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": val_col}},
                                "Function": 0
                            },
                            "Name": vqn,
                            "NativeReferenceName": label
                        }
                    ]
                },
                "drillFilterOtherVisuals": True,
                "vcObjects": {
                    "title": [{"properties": {
                        "text": {"expr": {"Literal": {"Value": f"'{label}'"}}},
                        "show": {"expr": {"Literal": {"Value": "true"}}}
                    }}]
                }
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


def make_slicer(x, y, w, h, entity, alias, col, tab):
    qn = f"{entity}.{col}"
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname(),
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "slicer",
                "projections": {"Values": [{"queryRef": qn, "active": True}]},
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": alias, "Entity": entity, "Type": 0}],
                    "Select": [{
                        "Column": {
                            "Expression": {"SourceRef": {"Source": alias}},
                            "Property": col
                        },
                        "Name": qn,
                        "NativeReferenceName": col
                    }]
                },
                "objects": {
                    "data": [{"properties": {"mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}}}]
                },
                "drillFilterOtherVisuals": True
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


def make_matrix(x, y, w, h, tab):
    """Monthly Orders Heatmap - Year rows x Month columns, count of orders"""
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname(),
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "pivotTable",
                "projections": {
                    "Rows": [{"queryRef": "Year(Orders.Order Date)", "active": True}],
                    "Columns": [{"queryRef": "MonthName(Orders.Order Date)", "active": True}],
                    "Values": [{"queryRef": "CountNonNull(Orders.Order ID)"}]
                },
                "prototypeQuery": {
                    "Version": 2,
                    "From": [{"Name": "o", "Entity": "Orders", "Type": 0}],
                    "Select": [
                        {
                            "DateSpan": {
                                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "Order Date"}},
                                "TimeUnit": 6
                            },
                            "Name": "Year(Orders.Order Date)",
                            "NativeReferenceName": "Year"
                        },
                        {
                            "DateSpan": {
                                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "Order Date"}},
                                "TimeUnit": 3
                            },
                            "Name": "MonthName(Orders.Order Date)",
                            "NativeReferenceName": "Month"
                        },
                        {
                            "Aggregation": {
                                "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "o"}}, "Property": "Order ID"}},
                                "Function": 5
                            },
                            "Name": "CountNonNull(Orders.Order ID)",
                            "NativeReferenceName": "Count of Orders"
                        }
                    ]
                },
                "drillFilterOtherVisuals": True,
                "objects": {
                    "subTotals": [{"properties": {
                        "rowSubtotals": {"expr": {"Literal": {"Value": "false"}}},
                        "columnSubtotals": {"expr": {"Literal": {"Value": "false"}}}
                    }}],
                    "general": [{"properties": {
                        "outspacePane": {"expr": {"Literal": {"Value": "false"}}}
                    }}]
                },
                "vcObjects": {
                    "title": [{"properties": {
                        "text": {"expr": {"Literal": {"Value": "'Monthly Orders Heatmap'"}}},
                        "show": {"expr": {"Literal": {"Value": "true"}}}
                    }}]
                }
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


def make_header_textbox(x, y, w, h, tab):
    return {
        "x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab,
        "filters": "[]",
        "config": json.dumps({
            "name": vname(),
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}}],
            "singleVisual": {
                "visualType": "textbox",
                "objects": {
                    "general": [{"properties": {"paragraphs": [
                        {
                            "textRuns": [{
                                "value": "Sales Analytics Dashboard",
                                "textStyle": {
                                    "fontWeight": "bold",
                                    "fontSize": "16pt",
                                    "color": "#FFFFFF"
                                }
                            }],
                            "horizontalTextAlignment": "left"
                        }
                    ]}}],
                    "background": [{"properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1A1A2E'"}}}}}
                    }}]
                }
            }
        }),
        "query": "{}",
        "dataTransforms": "{}"
    }


# ─── Build Sales Performance page visuals ──────────────────────────────────────

def build_sales_performance_visuals():
    sp_visuals = []

    # Row 1: Dark header bar
    sp_visuals.append(make_header_textbox(0, 0, 1280, 44, 0))

    # Row 2: 4 Slicers in filter row (y=50)
    sp_visuals.append(make_slicer(80, 50, 130, 30, "Orders", "o", "Order Date", 100))   # Year proxy
    sp_visuals.append(make_slicer(230, 50, 150, 30, "Orders", "o", "Category", 200))    # Category
    sp_visuals.append(make_slicer(400, 50, 160, 30, "Orders", "o", "Segment", 300))     # Segment (channel proxy)
    sp_visuals.append(make_slicer(580, 50, 160, 30, "Orders", "o", "Ship Mode", 400))   # Ship Mode

    # Row 3: 6 KPI Cards (y=90, height=108)
    CW, CH = 193, 108
    card_specs = [
        ("Orders", "o", "Sales",    0, "Total Revenue"),
        ("Orders", "o", "Profit",   0, "Total Profit"),
        ("Orders", "o", "Order ID", 5, "Total Orders"),
        ("Orders", "o", "Sales",    0, "Avg Order Value"),
        ("Returns","r", "Order ID", 5, "Total Returns"),
        ("Orders", "o", "Sales",    0, "Target Achievement"),
    ]
    for i, (e, a, c, f, lbl) in enumerate(card_specs):
        sp_visuals.append(make_card(10 + i * (CW + 8), 90, CW, CH, e, a, c, f, lbl, 500 + i * 10))

    # Row 4: Monthly Orders Heatmap matrix (y=210, h=220)
    sp_visuals.append(make_matrix(10, 210, 1260, 215, 1100))

    # Row 5: Three charts (y=440, h=345)
    # Sales by Region (clusteredBarChart)
    sp_visuals.append(make_bar(10, 440, 600, 345, "Orders", "o", "Region", "Orders", "o", "Sales", 0, "Sales by Region", 1200, "clusteredBarChart"))

    # Ship Mode Breakdown (clusteredColumnChart, count of order IDs)
    sp_visuals.append(make_bar(625, 440, 310, 345, "Orders", "o", "Ship Mode", "Orders", "o", "Order ID", 5, "Orders by Ship Mode", 1300, "clusteredColumnChart"))

    # Quarterly Revenue / Sales trend line chart
    sp_visuals.append(make_line_chart(950, 440, 320, 345, "Orders", "o", "Order Date", "Sales", "Quarterly Revenue", 1400))

    return sp_visuals


# ─── Build updated Executive Summary KPI cards ────────────────────────────────

def update_exec_summary_kpi_cards(existing_visuals):
    """
    Replace the 6 KPI cards in Executive Summary with the new 6-card layout,
    keeping header textbox and all other visuals intact.
    """
    # Identify non-card visuals to keep
    keep_visuals = []
    for v in existing_visuals:
        try:
            cfg = json.loads(v.get("config", "{}"))
            sv = cfg.get("singleVisual", {})
            vtype = sv.get("visualType", "")
        except Exception:
            vtype = ""
        # Keep everything that isn't a card
        if vtype != "card":
            keep_visuals.append(v)

    # Build 6 new KPI cards at y=60
    CW, CH = 193, 108
    card_specs = [
        ("Orders", "o", "Sales",    0, "Total Revenue"),
        ("Orders", "o", "Profit",   0, "Total Profit"),
        ("Orders", "o", "Order ID", 5, "Total Orders"),
        ("Orders", "o", "Sales",    0, "Avg Order Value"),
        ("Returns","r", "Order ID", 5, "Total Returns"),
        ("Orders", "o", "Sales",    0, "Target Achievement"),
    ]
    new_cards = []
    for i, (e, a, c, f, lbl) in enumerate(card_specs):
        new_cards.append(make_card(10 + i * (CW + 8), 60, CW, CH, e, a, c, f, lbl, 10 + i * 10))

    return keep_visuals + new_cards


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    layout_path = "/tmp/pbix_v2/extracted/Report/Layout"
    source_pbix = "/tmp/pbix_v2/dashboard_v2.pbix"
    output_pbix = "/home/user/newm/SalesAnalytics_Dashboard_v3.pbix"

    # Read Layout (UTF-16 LE, no BOM based on hex check showing 7b00 = '{' in UTF-16 LE)
    raw = open(layout_path, "rb").read()
    # Check for BOM
    if raw[:2] == b'\xff\xfe':
        text = raw[2:].decode("utf-16-le")
    else:
        text = raw.decode("utf-16-le")

    layout = json.loads(text)

    print(f"Loaded layout with {len(layout['sections'])} pages")
    for i, s in enumerate(layout["sections"]):
        print(f"  [{i}] {s['displayName']} — {len(s['visualContainers'])} visuals")

    # ── Update Sales Performance page (ordinal 1) ──
    sp_page = layout["sections"][1]
    assert sp_page["displayName"] == "Sales Performance", f"Expected 'Sales Performance', got '{sp_page['displayName']}'"

    new_sp_visuals = build_sales_performance_visuals()
    sp_page["visualContainers"] = new_sp_visuals
    print(f"\nSales Performance page: replaced with {len(new_sp_visuals)} new visuals")

    # ── Update Executive Summary KPI cards (page 0) ──
    es_page = layout["sections"][0]
    assert es_page["displayName"] == "Executive Summary", f"Expected 'Executive Summary', got '{es_page['displayName']}'"
    es_page["visualContainers"] = update_exec_summary_kpi_cards(es_page["visualContainers"])
    print(f"Executive Summary page: now {len(es_page['visualContainers'])} visuals (KPI cards updated)")

    # ── Verify all pages ──
    print("\nFinal page visual counts:")
    for i, s in enumerate(layout["sections"]):
        print(f"  [{i}] {s['displayName']} — {len(s['visualContainers'])} visuals")

    # ── Serialize back to UTF-16 LE ──
    new_text = json.dumps(layout, ensure_ascii=False, separators=(",", ":"))
    new_bytes = new_text.encode("utf-16-le")  # no BOM, matching original

    # Write to a temp file
    temp_layout = "/tmp/pbix_v2/new_Layout"
    with open(temp_layout, "wb") as f:
        f.write(new_bytes)
    print(f"\nNew Layout written: {len(new_bytes)} bytes (was {len(raw)} bytes)")

    # ── Package new PBIX ──
    with zipfile.ZipFile(source_pbix, "r") as zin:
        names = zin.namelist()
        print(f"\nSource PBIX files: {names}")
        with zipfile.ZipFile(output_pbix, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for name in names:
                if name == "Report/Layout":
                    zout.writestr(name, new_bytes)
                    print(f"  + Report/Layout (new, {len(new_bytes)} bytes)")
                else:
                    data = zin.read(name)
                    zout.writestr(name, data)
                    print(f"  + {name} ({len(data)} bytes, copied)")

    # ── Verify output ──
    print(f"\nVerifying output PBIX: {output_pbix}")
    with zipfile.ZipFile(output_pbix, "r") as z:
        members = z.namelist()
        print(f"  Files in output PBIX: {members}")
        layout_data = z.read("Report/Layout")
        layout_text = layout_data.decode("utf-16-le")
        layout_check = json.loads(layout_text)
        print(f"  Pages: {len(layout_check['sections'])}")
        for i, s in enumerate(layout_check["sections"]):
            print(f"    [{i}] {s['displayName']} — {len(s['visualContainers'])} visuals")

    print(f"\nDone! Output: {output_pbix}")
    print(f"File size: {os.path.getsize(output_pbix):,} bytes")


if __name__ == "__main__":
    main()

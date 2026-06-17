"""
Build FinancialDashboard.pbix
Strategy: use SalesAnalytics_Final.pbix as structural base (provides valid DataModel binary),
replace DataModelSchema with AgingAnalysis + CollectionPerformance tables,
replace Report/Layout with 2 pages matching the dark-theme screenshot.
User clicks "Refresh All" once to load the inline M-query data.
"""

import json, zipfile, uuid, os

BASE_PBIX = '/home/user/newm/SalesAnalytics_Final.pbix'
OUT_PATH  = '/home/user/newm/FinancialDashboard.pbix'

# ─── Data (matches screenshot values) ─────────────────────────────────────────
AGING_DATA = [
    {"Days Bucket": "Current",    "Amount": 4150000, "Sort": 1},
    {"Days Bucket": "1-30 Days",  "Amount": 2140000, "Sort": 2},
    {"Days Bucket": "31-60 Days", "Amount": 3150000, "Sort": 3},
    {"Days Bucket": "61-90 Days", "Amount": 2880000, "Sort": 4},
    {"Days Bucket": "90+ Days",   "Amount":  640000, "Sort": 5},
]

COLLECTION_DATA = [
    {"Month": "Jan", "MonthNum": 1, "Collected": 8800000, "PaymentRecovery": 2000000},
    {"Month": "Feb", "MonthNum": 2, "Collected": 8300000, "PaymentRecovery": 1900000},
    {"Month": "Mar", "MonthNum": 3, "Collected": 9100000, "PaymentRecovery": 2400000},
    {"Month": "Apr", "MonthNum": 4, "Collected": 8900000, "PaymentRecovery": 2300000},
    {"Month": "May", "MonthNum": 5, "Collected": 9400000, "PaymentRecovery": 2200000},
    {"Month": "Jun", "MonthNum": 6, "Collected": 5200000, "PaymentRecovery": 1500000},
]

def uid(): return uuid.uuid4().hex

# ─── M Query builder (one string per row, matching working PBIT format) ────────
def q(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'

def build_m_table(records, col_types):
    type_decls = ", ".join(f'#"{c}" = {t}' for c, t in col_types)
    header = f'  Source = #table(type table [{type_decls}], {{'
    lines = ["let", header]
    for i, rec in enumerate(records):
        vals = ", ".join(q(rec.get(c)) for c, _ in col_types)
        comma = "," if i < len(records) - 1 else ""
        lines.append(f"  {{{vals}}}{comma}")
    lines += ["  })", "in", "  Source"]
    return lines

AGING_COLS = [("Days Bucket", "text"), ("Amount", "number"), ("Sort", "Int64.Type")]
COLLECTION_COLS = [
    ("Month", "text"), ("MonthNum", "Int64.Type"),
    ("Collected", "number"), ("PaymentRecovery", "number"),
]

# ─── TMSL helpers ──────────────────────────────────────────────────────────────
def col(name, dtype, summarize="none"):
    return {
        "name": name, "dataType": dtype, "lineageTag": uid(),
        "summarizeBy": summarize,
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    }

def measure(name, expr, fmt=None):
    m = {"name": name, "expression": expr, "lineageTag": uid()}
    if fmt: m["formatString"] = fmt
    return m

def tmsl_table(name, columns, measures, expr_lines):
    return {
        "name": name, "lineageTag": uid(),
        "columns": columns,
        "measures": measures,
        "partitions": [{
            "name": name, "mode": "import",
            "source": {"type": "m", "expression": expr_lines}
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
    }

aging_table = tmsl_table("AgingAnalysis", [
    col("Days Bucket", "string"),
    col("Amount",      "double", "sum"),
    col("Sort",        "int64"),
], [
    measure("Total Receivables", "SUM(AgingAnalysis[Amount])", '"$"#,##0.00'),
], build_m_table(AGING_DATA, AGING_COLS))

collection_table = tmsl_table("CollectionPerformance", [
    col("Month",           "string"),
    col("MonthNum",        "int64"),
    col("Collected",       "double", "sum"),
    col("PaymentRecovery", "double", "sum"),
], [
    measure("Total Collected",        "SUM(CollectionPerformance[Collected])",       '"$"#,##0.00'),
    measure("Total Payment Recovery", "SUM(CollectionPerformance[PaymentRecovery])", '"$"#,##0.00'),
], build_m_table(COLLECTION_DATA, COLLECTION_COLS))

model_schema = {
    "model": {
        "compatibilityLevel": 1567,
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "tables": [aging_table, collection_table],
        "relationships": [],
        "annotations": [
            {"name": "PBI_QueryOrder", "value": '["AgingAnalysis","CollectionPerformance"]'},
            {"name": "__PBI_TimeIntelligenceEnabled", "value": "1"},
        ],
        "cultures": [{
            "name": "en-US",
            "linguisticMetadata": {
                "content": {"Version": "1.0.0", "Language": "en-US"},
                "contentType": "json"
            }
        }]
    }
}

# ─── Layout helpers ───────────────────────────────────────────────────────────
def vn(): return uuid.uuid4().hex[:20]

def Ls(s): return {"expr": {"Literal": {"Value": f"'{s}'"}}}
def Ln(n): return {"expr": {"Literal": {"Value": str(n)}}}
def Lb(b): return {"expr": {"Literal": {"Value": "true" if b else "false"}}}
def clr(c): return {"solid": {"color": Ls(c)}}

BG    = "#1a1b23"   # dark card background
PAGE  = "#12131a"   # page background
WHITE = "#FFFFFF"
GRAY  = "#9ca3af"
GREEN = "#22c55e"
AMBER = "#f59e0b"
ORANGE= "#f97316"
RED   = "#ef4444"
DRED  = "#dc2626"
GOLD  = "#d4d000"

def vc(x, y, w, h, tab, sv):
    p = {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}
    return {
        **p, "filters": "[]",
        "config": json.dumps({
            "name": vn(),
            "layouts": [{"id": 0, "position": p}],
            "singleVisual": sv
        }),
        "query": "{}", "dataTransforms": "{}"
    }

# ─── Textbox ──────────────────────────────────────────────────────────────────
def textbox(x, y, w, h, text, size="14", bold=True, color=WHITE, bg=PAGE, tab=0):
    fw = "bold" if bold else "normal"
    sv = {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {
                    "fontWeight": fw, "fontSize": f"{size}pt", "color": color
                }}],
                "horizontalTextAlignment": "left"
            }]}}],
            "background": [{"properties": {
                "show": Lb(True),
                "color": clr(bg),
                "transparency": Ln("0D")
            }}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ─── Slicer ───────────────────────────────────────────────────────────────────
def slicer(x, y, w, h, entity, alias, col_, tab, style="List"):
    qn = f"{entity}.{col_}"
    sv = {
        "visualType": "slicer",
        "projections": {"Values": [{"queryRef": qn, "active": True}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{
                "Column": {
                    "Expression": {"SourceRef": {"Source": alias}},
                    "Property": col_
                },
                "Name": qn,
                "NativeReferenceName": col_
            }]
        },
        "objects": {
            "data":   [{"properties": {"mode": Ls(style)}}],
            "selection": [{"properties": {
                "selectAllCheckboxEnabled": Lb(True),
                "singleSelect": Lb(False)
            }}],
            "header": [{"properties": {
                "show": Lb(True),
                "fontColor": clr(WHITE),
                "background": clr(BG),
                "fontSize": Ln("11D")
            }}],
            "items": [{"properties": {
                "fontColor": clr(GRAY),
                "background": clr(BG),
                "fontSize": Ln("10D")
            }}],
            "background": [{"properties": {
                "show": Lb(True),
                "color": clr(BG),
                "transparency": Ln("0D")
            }}],
        },
        "drillFilterOtherVisuals": True,
    }
    return vc(x, y, w, h, tab, sv)

# ─── KPI card ─────────────────────────────────────────────────────────────────
def kpi_card(x, y, w, h, entity, alias, prop_, tab, label, fmt="$"):
    qn = f"Sum({entity}.{prop_})"
    sv = {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": qn}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": alias, "Entity": entity, "Type": 0}],
            "Select": [{
                "Aggregation": {
                    "Expression": {"Column": {
                        "Expression": {"SourceRef": {"Source": alias}},
                        "Property": prop_
                    }},
                    "Function": 0
                },
                "Name": qn,
                "NativeReferenceName": label
            }]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "background":    [{"properties": {"show": Lb(True), "color": clr(BG), "transparency": Ln("0D")}}],
            "border":        [{"properties": {"show": Lb(False)}}],
            "labels":        [{"properties": {"color": clr(WHITE), "fontSize": Ln("20D"), "bold": Lb(True)}}],
            "categoryLabels":[{"properties": {"show": Lb(True), "color": clr(GRAY)}}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ─── Aging Analysis bar chart with per-bucket colors ──────────────────────────
def aging_bar(x, y, w, h, tab):
    BUCKET_COLORS = {
        "Current":    GREEN,
        "1-30 Days":  AMBER,
        "31-60 Days": ORANGE,
        "61-90 Days": RED,
        "90+ Days":   DRED,
    }
    data_points = []
    for val, hex_color in BUCKET_COLORS.items():
        data_points.append({
            "selector": {"data": {"expr": {"In": {
                "Expressions": [{"Column": {
                    "Expression": {"SourceRef": {"Source": "a"}},
                    "Property": "Days Bucket"
                }}],
                "Values": [[{"Literal": {"Value": f"'{val}'"}}]]
            }}}},
            "properties": {"fill": clr(hex_color)}
        })

    sv = {
        "visualType": "clusteredColumnChart",
        "projections": {
            "Category": [{"queryRef": "AgingAnalysis.Days Bucket", "active": True}],
            "Y":        [{"queryRef": "Sum(AgingAnalysis.Amount)"}],
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "a", "Entity": "AgingAnalysis", "Type": 0}],
            "Select": [
                {
                    "Column": {
                        "Expression": {"SourceRef": {"Source": "a"}},
                        "Property": "Days Bucket"
                    },
                    "Name": "AgingAnalysis.Days Bucket",
                    "NativeReferenceName": "Days Bucket"
                },
                {
                    "Aggregation": {
                        "Expression": {"Column": {
                            "Expression": {"SourceRef": {"Source": "a"}},
                            "Property": "Amount"
                        }},
                        "Function": 0
                    },
                    "Name": "Sum(AgingAnalysis.Amount)",
                    "NativeReferenceName": "Amount ($)"
                }
            ],
            "OrderBy": [{
                "Direction": 1,
                "Expression": {"Column": {
                    "Expression": {"SourceRef": {"Source": "a"}},
                    "Property": "Sort"
                }}
            }]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": Lb(True),
                "text": Ls("Aging Analysis"),
                "fontColor": clr(WHITE),
                "fontSize": Ln("16D"),
                "bold": Lb(True)
            }}],
            "subTitle": [{"properties": {
                "show": Lb(True),
                "text": Ls("Outstanding receivables by age bucket"),
                "fontColor": clr(GRAY),
                "fontSize": Ln("10D")
            }}],
            "background":  [{"properties": {"show": Lb(True), "color": clr(BG), "transparency": Ln("0D")}}],
            "border":      [{"properties": {"show": Lb(False)}}],
            "dataPoint":   data_points,
            "categoryAxis":[{"properties": {"labelColor": clr(GRAY), "fontSize": Ln("10D")}}],
            "valueAxis":   [{"properties": {
                "labelColor": clr(GRAY),
                "fontSize": Ln("10D"),
                "displayUnits": Ln("1000000D")
            }}],
            "dataLabels":  [{"properties": {"show": Lb(False)}}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ─── Legend badge (Total / On Track) ─────────────────────────────────────────
def badge(x, y, w, h, text, bg_color, tab):
    sv = {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {
                    "fontWeight": "bold", "fontSize": "10pt", "color": WHITE
                }}],
                "horizontalTextAlignment": "center"
            }]}}],
            "background": [{"properties": {
                "show": Lb(True),
                "color": clr(bg_color),
                "transparency": Ln("0D")
            }}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ─── Collection Performance dual-line chart ────────────────────────────────────
def collection_line(x, y, w, h, tab):
    sv = {
        "visualType": "lineChart",
        "projections": {
            "Category": [{"queryRef": "CollectionPerformance.Month", "active": True}],
            "Y": [
                {"queryRef": "Sum(CollectionPerformance.Collected)"},
                {"queryRef": "Sum(CollectionPerformance.PaymentRecovery)"},
            ],
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "c", "Entity": "CollectionPerformance", "Type": 0}],
            "Select": [
                {
                    "Column": {
                        "Expression": {"SourceRef": {"Source": "c"}},
                        "Property": "Month"
                    },
                    "Name": "CollectionPerformance.Month",
                    "NativeReferenceName": "Month"
                },
                {
                    "Aggregation": {
                        "Expression": {"Column": {
                            "Expression": {"SourceRef": {"Source": "c"}},
                            "Property": "Collected"
                        }},
                        "Function": 0
                    },
                    "Name": "Sum(CollectionPerformance.Collected)",
                    "NativeReferenceName": "Collected"
                },
                {
                    "Aggregation": {
                        "Expression": {"Column": {
                            "Expression": {"SourceRef": {"Source": "c"}},
                            "Property": "PaymentRecovery"
                        }},
                        "Function": 0
                    },
                    "Name": "Sum(CollectionPerformance.PaymentRecovery)",
                    "NativeReferenceName": "Payment Recovery"
                }
            ],
            "OrderBy": [{
                "Direction": 1,
                "Expression": {"Column": {
                    "Expression": {"SourceRef": {"Source": "c"}},
                    "Property": "MonthNum"
                }}
            }]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": Lb(True),
                "text": Ls("Collection Performance"),
                "fontColor": clr(WHITE),
                "fontSize": Ln("16D"),
                "bold": Lb(True)
            }}],
            "subTitle": [{"properties": {
                "show": Lb(True),
                "text": Ls("Monthly collected + payment recovery trend"),
                "fontColor": clr(GRAY),
                "fontSize": Ln("10D")
            }}],
            "background": [{"properties": {"show": Lb(True), "color": clr(BG), "transparency": Ln("0D")}}],
            "border":     [{"properties": {"show": Lb(False)}}],
            "dataPoint": [
                {
                    "selector": {"metadata": "Sum(CollectionPerformance.Collected)"},
                    "properties": {"fill": clr(GOLD)}
                },
                {
                    "selector": {"metadata": "Sum(CollectionPerformance.PaymentRecovery)"},
                    "properties": {"fill": clr(GREEN)}
                },
            ],
            "categoryAxis": [{"properties": {"labelColor": clr(GRAY), "fontSize": Ln("10D")}}],
            "valueAxis":    [{"properties": {
                "labelColor": clr(GRAY),
                "fontSize": Ln("10D"),
                "displayUnits": Ln("1000000D")
            }}],
            "legend": [{"properties": {
                "show": Lb(True),
                "labelColor": clr(WHITE),
                "fontSize": Ln("10D"),
                "position": Ls("Bottom")
            }}],
            "lineStyles": [{"properties": {"strokeWidth": Ln("2D")}}],
            "markers":    [{"properties": {"show": Lb(True)}}],
        }
    }
    return vc(x, y, w, h, tab, sv)

# ─── Page backgrounds ─────────────────────────────────────────────────────────
PAGE_CFG = json.dumps({
    "objects": {"background": [{"properties": {
        "color": {"solid": {"color": PAGE}},
        "transparency": 0
    }}]}
})

# ─── Page 1: Aging Analysis ───────────────────────────────────────────────────
p1_visuals = [
    # Header strip
    textbox(0, 0, 1280, 48, "   Aging Analysis", "15", True, WHITE, "#0d0e14", tab=0),

    # Total badge top-right
    badge(1070, 8, 190, 32, "💰  $12.96M Total", "#6b21a8", tab=5),

    # Slicer panel (right)
    textbox(1070, 65, 190, 28, "  Filter by Days", "10", True, GRAY, BG, tab=8),
    slicer(1070, 95, 190, 300, "AgingAnalysis", "a", "Days Bucket", tab=10),

    # KPI cards (right, below slicer)
    kpi_card(1070, 410, 190, 80, "AgingAnalysis", "a", "Amount", tab=20, label="Total Receivables"),

    # Main bar chart (left)
    aging_bar(20, 55, 1030, 725, tab=30),
]

# ─── Page 2: Collection Performance ──────────────────────────────────────────
p2_visuals = [
    # Header strip
    textbox(0, 0, 1280, 48, "   Collection Performance", "15", True, WHITE, "#0d0e14", tab=0),

    # On Track badge
    badge(1070, 8, 190, 32, "↑ On track", "#16a34a", tab=5),

    # Slicer panel (right)
    textbox(1070, 65, 190, 28, "  Filter by Month", "10", True, GRAY, BG, tab=8),
    slicer(1070, 95, 190, 260, "CollectionPerformance", "c", "Month", tab=10),

    # KPI cards (right)
    kpi_card(1070, 375, 190, 80, "CollectionPerformance", "c", "Collected",       tab=20, label="Total Collected"),
    kpi_card(1070, 470, 190, 80, "CollectionPerformance", "c", "PaymentRecovery", tab=25, label="Payment Recovery"),

    # Main line chart (left)
    collection_line(20, 55, 1030, 725, tab=30),
]

# ─── Report Layout ─────────────────────────────────────────────────────────────
def section(sid, name, display, ordinal, visuals, cfg=PAGE_CFG):
    return {
        "id": sid, "name": name, "displayName": display, "ordinal": ordinal,
        "visualContainers": visuals, "filters": "[]", "config": cfg,
        "displayOption": 1, "width": 1280, "height": 800
    }

theme_cfg = json.dumps({
    "version": "5.49",
    "themeCollection": {"baseTheme": {"name": "CY23SU11", "version": "5.49", "type": 2}},
    "activeSectionIndex": 0,
    "defaultDrillFilterOtherVisuals": True,
    "settings": {
        "useNewFilterPaneExperience": True,
        "allowChangeFilterTypes": True,
        "useStylableVisualContainerHeader": True,
    },
})

report_layout = {
    "id": 0,
    "resourcePackages": [{"resourcePackage": {
        "name": "SharedResources", "type": 2,
        "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json", "name": "CY23SU11"}],
        "disabled": False
    }}],
    "sections": [
        section(0, "P1", "Aging Analysis",        0, p1_visuals),
        section(1, "P2", "Collection Performance", 1, p2_visuals),
    ],
    "config": theme_cfg,
    "layoutOptimization": 0,
}

# ─── Diagram layout ────────────────────────────────────────────────────────────
diagram = {
    "version": "1.1.0",
    "selectedDiagram": "All tables",
    "defaultDiagram": "All tables",
    "diagrams": [{
        "ordinal": 0,
        "scrollPosition": {"x": 0, "y": 0},
        "nodes": [
            {"location": {"x": 10,  "y": 10}, "nodeIndex": "AgingAnalysis",
             "nodeLineageTag": uid(), "size": {"height": 180, "width": 234}, "zIndex": 0},
            {"location": {"x": 270, "y": 10}, "nodeIndex": "CollectionPerformance",
             "nodeLineageTag": uid(), "size": {"height": 200, "width": 234}, "zIndex": 0},
        ],
        "name": "All tables", "zoomValue": 100,
        "pinKeyFieldsToTop": False, "showExtraHeaderInfo": False,
        "hideKeyFieldsWhenCollapsed": False, "tablesLocked": False
    }]
}

# ─── Write PBIX (copy base file, replace DataModelSchema + Report/Layout) ──────
def u16(s): return s.encode("utf-16-le")

layout_bytes  = u16(json.dumps(report_layout, ensure_ascii=False))
schema_bytes  = json.dumps(model_schema, ensure_ascii=False, indent=2).encode("utf-8")
diagram_bytes = u16(json.dumps(diagram, ensure_ascii=False))

metadata = json.dumps({
    "Version": 5,
    "AutoCreatedRelationships": [],
    "CreatedFrom": "Cloud",
    "CreatedFromRelease": "2023.11"
})
settings = json.dumps({
    "Version": 4,
    "ReportSettings": {},
    "QueriesSettings": {
        "TypeDetectionEnabled": True,
        "RelationshipImportEnabled": True,
        "Version": "2.123.424.0"
    }
})

# Read all original files from base PBIX
with zipfile.ZipFile(BASE_PBIX) as z:
    base_files = {n: z.read(n) for n in z.namelist()}

# Write new PBIX: keep DataModel binary intact, replace everything else
with zipfile.ZipFile(OUT_PATH, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in base_files.items():
        if name == "DataModelSchema":
            z.writestr(name, schema_bytes)
        elif name == "DiagramLayout":
            z.writestr(name, diagram_bytes)
        elif name == "Report/Layout":
            z.writestr(name, layout_bytes)
        elif name == "Settings":
            z.writestr(name, u16(settings))
        elif name == "Metadata":
            z.writestr(name, u16(metadata))
        elif name == "SecurityBindings":
            z.writestr(name, b"")  # clear security bindings (no encryption)
        else:
            z.writestr(name, data)  # Version, Content_Types, DataModel, theme

size = os.path.getsize(OUT_PATH)
print(f"Written: {OUT_PATH}  ({size:,} bytes)")

with zipfile.ZipFile(OUT_PATH) as z:
    for n in z.namelist():
        print(f"  {n:60s} {z.getinfo(n).file_size:>10,} bytes")

# Verify layout is readable
with zipfile.ZipFile(OUT_PATH) as z:
    layout2 = json.loads(z.read("Report/Layout").decode("utf-16-le"))
    print("\nPages:")
    for s in layout2["sections"]:
        print(f"  [{s['displayName']}] {len(s['visualContainers'])} visuals")
        for vc_ in s["visualContainers"]:
            cfg_ = json.loads(vc_["config"])
            vtype = cfg_.get("singleVisual", {}).get("visualType", "?")
            print(f"    - {vtype} at ({vc_['x']},{vc_['y']}) {vc_['width']}x{vc_['height']}")

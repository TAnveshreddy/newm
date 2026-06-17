"""
Build FinancialDashboard.pbit
- Two pages: Aging Analysis & Collection Performance
- Aging Analysis: clustered bar chart + Days Bucket slicer
- Collection Performance: dual-line chart + Month slicer
- Dark theme matching the screenshot (#1e1e1e background, colored bars/lines)
"""

import json, zipfile, uuid, os

EXCEL_PATH = '/root/.claude/uploads/643f3b26-48e6-5d19-bf2a-cd58aff0e699/5881b57f-Financial_Dashboard_Data_2_1.xlsx'
SOURCE_PBIX = '/home/user/newm/SalesAnalytics_Final.pbix'
OUT_PATH = '/home/user/newm/FinancialDashboard.pbit'

# ─── Data ────────────────────────────────────────────────────────────────────
AGING_DATA = [
    {"Days Bucket": "Current",    "Amount": 4150000, "Sort": 1},
    {"Days Bucket": "1-30 Days",  "Amount": 2140000, "Sort": 2},
    {"Days Bucket": "31-60 Days", "Amount": 3150000, "Sort": 3},
    {"Days Bucket": "61-90 Days", "Amount": 2880000, "Sort": 4},
    {"Days Bucket": "90+ Days",   "Amount":  640000, "Sort": 5},
]

COLLECTION_DATA = [
    {"Month": "Jan", "MonthNum": 1,  "Collected": 8800000, "PaymentRecovery": 2000000},
    {"Month": "Feb", "MonthNum": 2,  "Collected": 8300000, "PaymentRecovery": 1900000},
    {"Month": "Mar", "MonthNum": 3,  "Collected": 9100000, "PaymentRecovery": 2400000},
    {"Month": "Apr", "MonthNum": 4,  "Collected": 8900000, "PaymentRecovery": 2300000},
    {"Month": "May", "MonthNum": 5,  "Collected": 9400000, "PaymentRecovery": 2200000},
    {"Month": "Jun", "MonthNum": 6,  "Collected": 5200000, "PaymentRecovery": 1500000},
]

def uid(): return uuid.uuid4().hex

# ─── M Query builder ─────────────────────────────────────────────────────────
def q(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'

def build_m_table(records, col_types):
    type_decls = ", ".join(f'#"{c}" = {t}' for c, t in col_types)
    header = f'#table(type table [{type_decls}], {{'
    rows = [f"  {{{', '.join(q(rec.get(c)) for c, _ in col_types)}}}" for rec in records]
    return ["let", f"  Source = {header}", ",\n".join(rows), "  })", "in", "  Source"]

AGING_COLS = [("Days Bucket", "text"), ("Amount", "number"), ("Sort", "Int64.Type")]
COLLECTION_COLS = [
    ("Month", "text"), ("MonthNum", "Int64.Type"),
    ("Collected", "number"), ("PaymentRecovery", "number"),
]

AGING_EXPR = build_m_table(AGING_DATA, AGING_COLS)
COLLECTION_EXPR = build_m_table(COLLECTION_DATA, COLLECTION_COLS)

# ─── TMSL helpers ─────────────────────────────────────────────────────────────
def col(name, dtype, summarize="none"):
    return {
        "name": name, "dataType": dtype, "lineageTag": uid(),
        "summarizeBy": summarize,
        "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
    }

def tmsl_table(name, columns, measures, expr_lines):
    return {
        "name": name, "lineageTag": uid(),
        "columns": columns,
        "measures": measures if measures else [],
        "partitions": [{
            "name": name, "mode": "import",
            "source": {"type": "m", "expression": expr_lines}
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
    }

aging_table = tmsl_table("AgingAnalysis", [
    col("Days Bucket", "string"),
    col("Amount",      "double", "sum"),
    col("Sort",        "int64",  "none"),
], [
    {"name": "Total Receivables", "expression": "SUM(AgingAnalysis[Amount])",
     "lineageTag": uid(), "formatString": '"$"#,##0.00'}
], AGING_EXPR)

collection_table = tmsl_table("CollectionPerformance", [
    col("Month",           "string"),
    col("MonthNum",        "int64"),
    col("Collected",       "double", "sum"),
    col("PaymentRecovery", "double", "sum"),
], [
    {"name": "Total Collected",       "expression": "SUM(CollectionPerformance[Collected])",
     "lineageTag": uid(), "formatString": '"$"#,##0.00'},
    {"name": "Total Payment Recovery","expression": "SUM(CollectionPerformance[PaymentRecovery])",
     "lineageTag": uid(), "formatString": '"$"#,##0.00'},
], COLLECTION_EXPR)

model_schema = {
    "model": {
        "compatibilityLevel": 1567,
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "tables": [aging_table, collection_table],
        "relationships": [],
        "annotations": [
            {"name": "PBI_QueryOrder", "value": '["AgingAnalysis","CollectionPerformance"]'},
        ],
        "cultures": [{"name": "en-US", "linguisticMetadata": {
            "content": {"Version": "1.0.0", "Language": "en-US"}, "contentType": "json"}}]
    }
}

# ─── Layout helpers ──────────────────────────────────────────────────────────
def vn(): return uuid.uuid4().hex[:20]

def vc(x, y, w, h, tab, config_obj):
    p = {"x": x, "y": y, "z": tab, "width": w, "height": h, "tabOrder": tab}
    return {
        **p, "filters": "[]",
        "config": json.dumps({
            "name": vn(),
            "layouts": [{"id": 0, "position": p}],
            **config_obj
        }),
        "query": "{}", "dataTransforms": "{}"
    }

# ─── Aging Analysis bar chart (5 bars, custom colors per bar) ─────────────────
def make_aging_bar(x, y, w, h, tab):
    """Clustered column chart: Days Bucket on X, Amount on Y, colored per bucket."""
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
                        "Expression": {
                            "Column": {
                                "Expression": {"SourceRef": {"Source": "a"}},
                                "Property": "Amount"
                            }
                        },
                        "Function": 0
                    },
                    "Name": "Sum(AgingAnalysis.Amount)",
                    "NativeReferenceName": "Amount"
                }
            ],
            "OrderBy": [
                {
                    "Direction": 1,
                    "Expression": {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "a"}},
                            "Property": "Sort"
                        }
                    }
                }
            ]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": "'Aging Analysis'"}}},
                "fontColor": {"solid": {"color": "#FFFFFF"}},
                "fontSize": {"expr": {"Literal": {"Value": "14D"}}}
            }}],
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": "#1e2028"}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }}],
            "border": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "false"}}}
            }}],
            "dataPoint": [
                {
                    "selector": {"data": {"expr": {"In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": "Days Bucket"}}],
                        "Values": [[{"Literal": {"Value": "'Current'"}}]]
                    }}}},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#22c55e'"}}}}}}
                },
                {
                    "selector": {"data": {"expr": {"In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": "Days Bucket"}}],
                        "Values": [[{"Literal": {"Value": "'1-30 Days'"}}]]
                    }}}},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#f59e0b'"}}}}}}
                },
                {
                    "selector": {"data": {"expr": {"In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": "Days Bucket"}}],
                        "Values": [[{"Literal": {"Value": "'31-60 Days'"}}]]
                    }}}},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#f97316'"}}}}}}
                },
                {
                    "selector": {"data": {"expr": {"In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": "Days Bucket"}}],
                        "Values": [[{"Literal": {"Value": "'61-90 Days'"}}]]
                    }}}},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#ef4444'"}}}}}}
                },
                {
                    "selector": {"data": {"expr": {"In": {
                        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": "Days Bucket"}}],
                        "Values": [[{"Literal": {"Value": "'90+ Days'"}}]]
                    }}}},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#dc2626'"}}}}}}
                },
            ],
            "categoryAxis": [{"properties": {
                "labelColor": {"solid": {"color": "#AAAAAA"}},
                "fontSize": {"expr": {"Literal": {"Value": "10D"}}}
            }}],
            "valueAxis": [{"properties": {
                "labelColor": {"solid": {"color": "#AAAAAA"}},
                "displayUnits": {"expr": {"Literal": {"Value": "1000000D"}}}
            }}],
        }
    }
    return vc(x, y, w, h, tab, {"singleVisual": sv})

# ─── Collection Performance dual-line chart ───────────────────────────────────
def make_collection_line(x, y, w, h, tab):
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
                        "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "Collected"}},
                        "Function": 0
                    },
                    "Name": "Sum(CollectionPerformance.Collected)",
                    "NativeReferenceName": "Collected"
                },
                {
                    "Aggregation": {
                        "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "c"}}, "Property": "PaymentRecovery"}},
                        "Function": 0
                    },
                    "Name": "Sum(CollectionPerformance.PaymentRecovery)",
                    "NativeReferenceName": "Payment Recovery"
                }
            ],
            "OrderBy": [
                {
                    "Direction": 1,
                    "Expression": {
                        "Column": {
                            "Expression": {"SourceRef": {"Source": "c"}},
                            "Property": "MonthNum"
                        }
                    }
                }
            ]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": "'Collection Performance'"}}},
                "fontColor": {"solid": {"color": "#FFFFFF"}},
                "fontSize": {"expr": {"Literal": {"Value": "14D"}}}
            }}],
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": "#1e2028"}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }}],
            "border": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "false"}}}
            }}],
            "dataPoint": [
                {
                    "selector": {"metadata": "Sum(CollectionPerformance.Collected)"},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#d4d000'"}}}}}},
                },
                {
                    "selector": {"metadata": "Sum(CollectionPerformance.PaymentRecovery)"},
                    "properties": {"fill": {"solid": {"color": {"expr": {"Literal": {"Value": "'#22c55e'"}}}}}},
                },
            ],
            "categoryAxis": [{"properties": {
                "labelColor": {"solid": {"color": "#AAAAAA"}},
                "fontSize": {"expr": {"Literal": {"Value": "10D"}}}
            }}],
            "valueAxis": [{"properties": {
                "labelColor": {"solid": {"color": "#AAAAAA"}},
                "displayUnits": {"expr": {"Literal": {"Value": "1000000D"}}}
            }}],
            "legend": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "labelColor": {"solid": {"color": "#FFFFFF"}},
                "fontSize": {"expr": {"Literal": {"Value": "10D"}}}
            }}],
        }
    }
    return vc(x, y, w, h, tab, {"singleVisual": sv})

# ─── Slicer helper ─────────────────────────────────────────────────────────────
def make_slicer(x, y, w, h, entity, alias, col_, tab, title="", style="List"):
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
            "data": [{"properties": {
                "mode": {"expr": {"Literal": {"Value": f"'{style}'"}}}
            }}],
            "selection": [{"properties": {
                "selectAllCheckboxEnabled": {"expr": {"Literal": {"Value": "true"}}},
                "singleSelect": {"expr": {"Literal": {"Value": "false"}}}
            }}],
            "header": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "fontColor": {"solid": {"color": "#FFFFFF"}},
                "background": {"solid": {"color": "#1e2028"}},
                "fontSize": {"expr": {"Literal": {"Value": "11D"}}}
            }}],
            "items": [{"properties": {
                "fontColor": {"solid": {"color": "#CCCCCC"}},
                "background": {"solid": {"color": "#1e2028"}},
                "fontSize": {"expr": {"Literal": {"Value": "10D"}}}
            }}],
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": "#1e2028"}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }}],
        },
        "drillFilterOtherVisuals": True,
    }
    if title:
        sv["vcObjects"] = {"title": [{"properties": {
            "show": {"expr": {"Literal": {"Value": "true"}}},
            "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
            "fontColor": {"solid": {"color": "#FFFFFF"}},
        }}]}
    return vc(x, y, w, h, tab, {"singleVisual": sv})

# ─── KPI Card ─────────────────────────────────────────────────────────────────
def make_kpi_card(x, y, w, h, entity, alias, measure_name, tab, label):
    qn = f"Sum({entity}.{measure_name})"
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
                        "Property": measure_name
                    }},
                    "Function": 0
                },
                "Name": qn,
                "NativeReferenceName": label
            }]
        },
        "drillFilterOtherVisuals": True,
        "vcObjects": {
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": "#1e2028"}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }}],
            "labels": [{"properties": {
                "color": {"solid": {"color": "#FFFFFF"}},
                "fontSize": {"expr": {"Literal": {"Value": "22D"}}}
            }}],
            "categoryLabels": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": "#AAAAAA"}}
            }}],
        }
    }
    return vc(x, y, w, h, tab, {"singleVisual": sv})

# ─── Textbox ──────────────────────────────────────────────────────────────────
def make_textbox(x, y, w, h, text, font_size="14", color="#FFFFFF", bg="#12131a", tab=0):
    sv = {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {
                    "fontWeight": "bold", "fontSize": f"{font_size}pt", "color": color
                }}],
                "horizontalTextAlignment": "left"
            }]}}],
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": bg}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }}],
        }
    }
    return vc(x, y, w, h, tab, {"singleVisual": sv})

# ─── Badge visual (On Track / Total) ─────────────────────────────────────────
def make_badge(x, y, w, h, text, bg_color, tab):
    sv = {
        "visualType": "textbox",
        "objects": {
            "general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": text, "textStyle": {
                    "fontWeight": "bold", "fontSize": "11pt", "color": "#FFFFFF"
                }}],
                "horizontalTextAlignment": "center"
            }]}}],
            "background": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "color": {"solid": {"color": bg_color}},
                "transparency": {"expr": {"Literal": {"Value": "0D"}}}
            }}],
        }
    }
    return vc(x, y, w, h, tab, {"singleVisual": sv})

# ─── PAGE 1: Aging Analysis ───────────────────────────────────────────────────
# Layout: 1280 x 800
# Header: full-width dark strip
# Slicer (Days Bucket): right side vertical list
# Main chart: large bar chart on left/center

CANVAS_W = 1280
CANVAS_H = 800

aging_page = [
    # Dark background header
    make_textbox(0, 0, CANVAS_W, 50, "  Financial Dashboard  |  Aging Analysis", "16", "#FFFFFF", "#12131a", 0),

    # Slicer: Days Bucket (right panel)
    make_slicer(1050, 70, 210, 240, "AgingAnalysis", "a", "Days Bucket", 10, "Filter by Days Bucket", "List"),

    # Total receivables KPI badge area (top-right of chart)
    make_kpi_card(1050, 330, 210, 80, "AgingAnalysis", "a", "Amount", 20, "$12.96M Total"),

    # Main bar chart
    make_aging_bar(20, 70, 1010, 710, 30),
]

# ─── PAGE 2: Collection Performance ──────────────────────────────────────────
collection_page = [
    # Dark background header
    make_textbox(0, 0, CANVAS_W, 50, "  Financial Dashboard  |  Collection Performance", "16", "#FFFFFF", "#12131a", 0),

    # Slicer: Month (right panel)
    make_slicer(1050, 70, 210, 300, "CollectionPerformance", "c", "Month", 10, "Filter by Month", "List"),

    # On Track badge
    make_badge(1050, 390, 210, 40, "↑ On track", "#16a34a", 20),

    # Total Collected KPI
    make_kpi_card(1050, 450, 210, 80, "CollectionPerformance", "c", "Collected", 25, "Total Collected"),

    # Total Payment Recovery KPI
    make_kpi_card(1050, 550, 210, 80, "CollectionPerformance", "c", "PaymentRecovery", 30, "Payment Recovery"),

    # Main line chart
    make_collection_line(20, 70, 1010, 710, 40),
]

# ─── Report Layout ────────────────────────────────────────────────────────────
def section(sid, name, display, ordinal, visuals):
    return {
        "id": sid, "name": name, "displayName": display, "ordinal": ordinal,
        "visualContainers": visuals, "filters": "[]", "config": "{}",
        "displayOption": 1, "width": CANVAS_W, "height": CANVAS_H
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
        section(0, "P1", "Aging Analysis", 0, aging_page),
        section(1, "P2", "Collection Performance", 1, collection_page),
    ],
    "config": theme_cfg,
    "layoutOptimization": 0,
}

# ─── Diagram Layout ───────────────────────────────────────────────────────────
diagram = {
    "version": "1.1.0",
    "selectedDiagram": "All tables",
    "defaultDiagram": "All tables",
    "diagrams": [{
        "ordinal": 0,
        "scrollPosition": {"x": 0, "y": 0},
        "nodes": [
            {"location": {"x": 10, "y": 10}, "nodeIndex": "AgingAnalysis",
             "nodeLineageTag": uid(), "size": {"height": 200, "width": 234}, "zIndex": 0},
            {"location": {"x": 270, "y": 10}, "nodeIndex": "CollectionPerformance",
             "nodeLineageTag": uid(), "size": {"height": 200, "width": 234}, "zIndex": 0},
        ],
        "name": "All tables", "zoomValue": 100, "pinKeyFieldsToTop": False,
        "showExtraHeaderInfo": False, "hideKeyFieldsWhenCollapsed": False, "tablesLocked": False
    }]
}

# ─── Write PBIT ───────────────────────────────────────────────────────────────
content_types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/DataModelSchema"  ContentType="application/json"/>
  <Override PartName="/DiagramLayout"    ContentType="application/json"/>
  <Override PartName="/Report/Layout"    ContentType="application/json"/>
  <Override PartName="/Settings"         ContentType="application/json"/>
  <Override PartName="/Metadata"         ContentType="application/json"/>
</Types>"""

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

def u16(s): return s.encode('utf-16-le')

# Extract CY23SU11 theme from existing pbix
with zipfile.ZipFile(SOURCE_PBIX) as z:
    orig_theme = z.read('Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json')

layout_str  = json.dumps(report_layout, ensure_ascii=False)
schema_str  = json.dumps(model_schema,  ensure_ascii=False, indent=2)
diagram_str = json.dumps(diagram,       ensure_ascii=False)

with zipfile.ZipFile(OUT_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('Version',              '3.0')
    z.writestr('[Content_Types].xml',  content_types.encode('utf-8'))
    z.writestr('DataModelSchema',      schema_str.encode('utf-8'))
    z.writestr('DiagramLayout',        u16(diagram_str))
    z.writestr('Report/Layout',        u16(layout_str))
    z.writestr('Settings',             u16(settings))
    z.writestr('Metadata',             u16(metadata))
    z.writestr('SecurityBindings',     b'')
    z.writestr('Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json', orig_theme)

size = os.path.getsize(OUT_PATH)
print(f"Written: {OUT_PATH}  ({size:,} bytes)")

with zipfile.ZipFile(OUT_PATH) as z:
    for name in z.namelist():
        info = z.getinfo(name)
        print(f"  {name:60s} {info.file_size:>10,} bytes")

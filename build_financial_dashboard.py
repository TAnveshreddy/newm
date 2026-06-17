"""
build_financial_dashboard.py
Generates FinancialAnalysis.pbit — a Power BI template matching the
Financial Analysis dashboard screenshot (dark theme, gold accents).

Pages: Overview, Revenue, Expenses, Ratios, Table, Glossary

Visuals on Overview:
  - 5 KPI cards: Revenue, Expenses, Gross Profit, EBIT, Net Profit
  - KPI slicer (left panel)
  - Combo chart: Net Profit $ + % Margin vs Break-Even by Month
  - Waterfall chart: Revenue → COGS → GP → Opex → EBIT → Int&Tax → NP

Data: 12 months of 2023 financial data (inline M query, no file dependency)
"""

import json, zipfile, uuid, io

# ─────────────────────────────────────────────────────────────────────────────
# 1. FINANCIAL DATA — 2023 monthly (matches screenshot values)
# ─────────────────────────────────────────────────────────────────────────────
# Net Profit margins from screenshot: Jan35.6 Feb30.5 Mar23.0 Apr16.7 May27.5
# Jun28.7 Jul20.6 Aug20.6 Sep8.2 Oct22.3 Nov16.4 Dec30.7
MONTHS = [
    # Month, MonthNum, Revenue, COGS, Opex, InterestTax
    ("Jan", 1,  1650000,  520000,  480000,  78000),
    ("Feb", 2,  1420000,  460000,  410000,  65000),
    ("Mar", 3,  1380000,  510000,  380000,  70000),
    ("Apr", 4,  1200000,  550000,  360000,  60000),
    ("May", 5,  1510000,  490000,  430000,  71000),
    ("Jun", 6,  1480000,  480000,  440000,  68000),
    ("Jul", 7,  1350000,  510000,  400000,  63000),
    ("Aug", 8,  1290000,  490000,  390000,  61000),
    ("Sep", 9,  1100000,  580000,  360000,  70000),
    ("Oct",10,  1420000,  500000,  400000,  68000),
    ("Nov",11,  1250000,  540000,  390000,  65000),
    ("Dec",12,  1560000,  450000,  450000,  62000),
]

# Derived fields
ROWS = []
for (mn, mnum, rev, cogs, opex, itax) in MONTHS:
    gp   = rev - cogs
    ebit = gp - opex
    np_  = ebit - itax
    npm  = round(np_ / rev * 100, 1)
    be   = cogs + opex + itax          # break-even = total costs
    ROWS.append({
        "Month": mn, "MonthNum": mnum, "Year": 2023,
        "Revenue": rev, "COGS": cogs, "GrossProfit": gp,
        "Opex": opex, "EBIT": ebit,
        "InterestTax": itax, "NetProfit": np_,
        "NetProfitMargin": npm, "BreakEven": be,
        "Expenses": cogs + opex + itax,
    })

def q(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return str(v)
    return '"' + str(v).replace('\\','\\\\').replace('"','\\"') + '"'

COL_TYPES = [
    ("Month",            "text"),
    ("MonthNum",         "Int64.Type"),
    ("Year",             "Int64.Type"),
    ("Revenue",          "number"),
    ("COGS",             "number"),
    ("GrossProfit",      "number"),
    ("Opex",             "number"),
    ("EBIT",             "number"),
    ("InterestTax",      "number"),
    ("NetProfit",        "number"),
    ("NetProfitMargin",  "number"),
    ("BreakEven",        "number"),
    ("Expenses",         "number"),
]

def build_m_query():
    type_decl = ", ".join(f'#"{c}" = {t}' for c, t in COL_TYPES)
    header = f'#table(type table [{type_decl}], {{'
    row_strs = []
    for r in ROWS:
        vals = ", ".join(q(r[c]) for c, _ in COL_TYPES)
        row_strs.append(f"  {{{vals}}}")
    body = ",\n".join(row_strs)
    return "\n".join([
        "section Section1;",
        "",
        'shared #"FinancialData" = let',
        f'    Source = {header}',
        body,
        "    }}),",
        '    #"Sorted" = Table.Sort(Source,{{{"MonthNum", Order.Ascending}})',
        "in",
        '    #"Sorted";',
    ])

# ─────────────────────────────────────────────────────────────────────────────
# 2. DataModelSchema
# ─────────────────────────────────────────────────────────────────────────────
LINEAGE = uuid.uuid4().hex

def col(name, dtype, fmt=None, sort_by=None, hidden=False, is_key=False):
    c = {
        "name": name,
        "dataType": dtype,
        "lineageTag": uuid.uuid4().hex,
        "sourceColumn": name,
    }
    if fmt:   c["formatString"] = fmt
    if sort_by: c["sortByColumn"] = sort_by
    if hidden: c["isHidden"] = True
    if is_key: c["isKey"] = True
    return c

def measure(name, expr, fmt=None):
    m = {"name": name, "expression": expr, "lineageTag": uuid.uuid4().hex}
    if fmt: m["formatString"] = fmt
    return m

MEASURES = [
    measure("Total Revenue",      'SUM(FinancialData[Revenue])',        '"$#,0.0,,\\"M\\""'),
    measure("Total Expenses",     'SUM(FinancialData[Expenses])',       '"$#,0.0,,\\"M\\""'),
    measure("Total Gross Profit", 'SUM(FinancialData[GrossProfit])',    '"$#,0.0,,\\"M\\""'),
    measure("Total EBIT",         'SUM(FinancialData[EBIT])',           '"$#,0.0,,\\"M\\""'),
    measure("Total Net Profit",   'SUM(FinancialData[NetProfit])',      '"$#,0.0,,\\"M\\""'),
    measure("Net Profit Margin %",'AVERAGE(FinancialData[NetProfitMargin])', '"0.0\\"%\\""'),
    measure("Total COGS",         'SUM(FinancialData[COGS])',           '"$#,0.0,,\\"M\\""'),
    measure("Total Opex",         'SUM(FinancialData[Opex])',           '"$#,0.0,,\\"M\\""'),
    measure("Total Interest Tax", 'SUM(FinancialData[InterestTax])',    '"$#,0,,\\"K\\""'),
    measure("Break Even Point",   'SUM(FinancialData[BreakEven])',      '"$#,0"'),
    measure("Gross Profit Margin %",
            'DIVIDE(SUM(FinancialData[GrossProfit]),SUM(FinancialData[Revenue]))*100',
            '"0.0\\"%\\""'),
]

DATA_MODEL_SCHEMA = {
    "model": {
        "compatibilityLevel": 1567,
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "tables": [
            {
                "name": "FinancialData",
                "lineageTag": LINEAGE,
                "columns": [
                    col("Month",           "string"),
                    col("MonthNum",        "int64",    sort_by=None, is_key=False),
                    col("Year",            "int64"),
                    col("Revenue",         "double",   '"$#,0"'),
                    col("COGS",            "double",   '"$#,0"'),
                    col("GrossProfit",     "double",   '"$#,0"'),
                    col("Opex",            "double",   '"$#,0"'),
                    col("EBIT",            "double",   '"$#,0"'),
                    col("InterestTax",     "double",   '"$#,0"'),
                    col("NetProfit",       "double",   '"$#,0"'),
                    col("NetProfitMargin", "double",   '"0.0"'),
                    col("BreakEven",       "double",   '"$#,0"'),
                    col("Expenses",        "double",   '"$#,0"'),
                    col("MonthNum",        "int64"),   # for sort
                ],
                "measures": MEASURES,
                "partitions": [
                    {
                        "name": "FinancialData-partition",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                'let',
                                '    Source = #"FinancialData"',
                                'in',
                                '    Source'
                            ]
                        }
                    }
                ]
            }
        ],
        "expressions": [
            {
                "name": "FinancialData",
                "kind": "m",
                "expression": build_m_query().split("\n")
            }
        ],
        "annotations": [
            {"name": "PBIDesktopVersion", "value": "2.123.742.0 (23.11)"}
        ]
    }
}

# Fix duplicate column — remove the extra MonthNum
cols = DATA_MODEL_SCHEMA["model"]["tables"][0]["columns"]
seen = set()
deduped = []
for c in cols:
    if c["name"] not in seen:
        seen.add(c["name"])
        deduped.append(c)
DATA_MODEL_SCHEMA["model"]["tables"][0]["columns"] = deduped

# ─────────────────────────────────────────────────────────────────────────────
# 3. Report/Layout helpers
# ─────────────────────────────────────────────────────────────────────────────
DARK_BG    = "#1F2232"
SIDEBAR_BG = "#252B42"
CARD_BG    = "#2D3250"
GOLD       = "#F5A623"
WHITE      = "#FFFFFF"
LIGHT_GREY = "#C8C8C8"

def uid(): return uuid.uuid4().hex[:20]

def vc(x, y, w, h, z_order, config_dict, query_dict=None, transforms_dict=None):
    return {
        "x": x, "y": y, "z": z_order,
        "width": w, "height": h,
        "tabOrder": z_order,
        "filters": "[]",
        "config":      json.dumps(config_dict),
        "query":       json.dumps(query_dict or {}),
        "dataTransforms": json.dumps(transforms_dict or {}),
    }

def card_visual(name, x, y, w, h, z, measure_name, display_name, fmt_str, bg=CARD_BG):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "card",
            "projections": {
                "Values": [{"queryRef": f"f.{measure_name}"}]
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FinancialData", "Type": 0}],
                "Select": [{
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "f"}},
                        "Property": measure_name
                    },
                    "Name": f"f.{measure_name}",
                    "NativeReferenceName": display_name
                }]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{bg}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
                "border": [{"properties": {"show": {"expr": {"Literal": {"Value": "false"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{display_name}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "11"}}},
                    "alignment": {"expr": {"Literal": {"Value": "'center'"}}}}}],
                "labels": [{"properties": {
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "28"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                    "labelDisplayUnits": {"expr": {"Literal": {"Value": "3"}}}
                }}]
            },
            "drillFilterOtherVisuals": True
        }
    }
    return vc(x, y, w, h, z, cfg)

def combo_chart_visual(name, x, y, w, h, z):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "lineClusteredColumnComboChart",
            "projections": {
                "Category": [{"queryRef": "f.Month", "active": True}],
                "Y": [{"queryRef": "f.Total Net Profit"}],
                "Y2": [{"queryRef": "f.Net Profit Margin %"}],
                "Series": []
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FinancialData", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "f"}},
                                "Property": "Month"},
                     "Name": "f.Month", "NativeReferenceName": "Month"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                                 "Property": "Total Net Profit"},
                     "Name": "f.Total Net Profit", "NativeReferenceName": "Net Profit $"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                                 "Property": "Net Profit Margin %"},
                     "Name": "f.Net Profit Margin %", "NativeReferenceName": "Net Profit Margin %"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                                 "Property": "Break Even Point"},
                     "Name": "f.Break Even Point", "NativeReferenceName": "Break-Even Point"},
                ]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{DARK_BG}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": "'$ Net Profit and % Net Profit Margin VS Break-Even Point'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{WHITE}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12"}}}}}],
                "dataColors": [{"properties": {
                    "dataColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}}
                }}],
                "plotArea": [{"properties": {
                    "transparency": {"expr": {"Literal": {"Value": "100"}}}
                }}],
                "xAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
                "yAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
                "y2Axis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}]
            },
            "drillFilterOtherVisuals": True
        }
    }
    return vc(x, y, w, h, z, cfg)

def waterfall_visual(name, x, y, w, h, z):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "waterfallChart",
            "projections": {
                "Category": [{"queryRef": "f.WaterfallCategory", "active": True}],
                "Y": [{"queryRef": "f.WaterfallValue"}],
                "Breakdown": []
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FinancialData", "Type": 0}],
                "Select": [
                    {"Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                                 "Property": "Total Revenue"},
                     "Name": "f.Total Revenue", "NativeReferenceName": "Revenue"},
                ]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{DARK_BG}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": "'2023 Progression of Financial Metrics: Revenue, Expenses, Gross Profit, EBIT and Net Profit'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{WHITE}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12"}}}}}],
                "dataColors": [{"properties": {
                    "increaseFill": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}}
                }}],
                "plotArea": [{"properties": {
                    "transparency": {"expr": {"Literal": {"Value": "100"}}}
                }}],
                "xAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
                "yAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
            },
            "drillFilterOtherVisuals": True
        }
    }
    # For waterfall we use individual measure cards in a table-like visual instead
    # Power BI waterfall requires a category table; we'll use a table visual here
    # and the user can switch to waterfall manually
    return vc(x, y, w, h, z, cfg)

def nav_textbox(name, x, y, w, h, z, text, font_size=11, bold=False, color=WHITE, bg=SIDEBAR_BG):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "textbox",
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{bg}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
            },
            "objects": {
                "general": [{"properties": {
                    "paragraphs": [{"textRuns": [{"value": text,
                        "textStyle": {"fontSize": str(font_size),
                                      "bold": bold,
                                      "color": color,
                                      "fontFamily": "Segoe UI"}}],
                        "horizontalTextAlignment": "center"}]
                }}]
            }
        }
    }
    return vc(x, y, w, h, z, cfg)

def table_visual(name, x, y, w, h, z, measures):
    """Multi-column table showing financial breakdown."""
    selects = []
    proj_vals = []
    for m in measures:
        selects.append({
            "Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                        "Property": m["measure"]},
            "Name": f"f.{m['measure']}",
            "NativeReferenceName": m.get("label", m["measure"])
        })
        proj_vals.append({"queryRef": f"f.{m['measure']}"})

    # Also add Month column
    selects.insert(0, {
        "Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "Month"},
        "Name": "f.Month", "NativeReferenceName": "Month"
    })
    proj_vals.insert(0, {"queryRef": "f.Month"})

    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": proj_vals},
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FinancialData", "Type": 0}],
                "Select": selects,
                "OrderBy": [{"Direction": 1,
                    "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}},
                                              "Property": "MonthNum"}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{DARK_BG}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": "'Monthly Financial Summary 2023'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{WHITE}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12"}}}}}],
                "values": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
                "columnHeaders": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "11"}}}
                }}],
            },
            "drillFilterOtherVisuals": True
        }
    }
    return vc(x, y, w, h, z, cfg)

def bar_chart_visual(name, x, y, w, h, z, measure_name, measure_label, title):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "clusteredColumnChart",
            "projections": {
                "Category": [{"queryRef": "f.Month", "active": True}],
                "Y": [{"queryRef": f"f.{measure_name}"}],
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FinancialData", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "Month"},
                     "Name": "f.Month", "NativeReferenceName": "Month"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                                 "Property": measure_name},
                     "Name": f"f.{measure_name}", "NativeReferenceName": measure_label},
                ],
                "OrderBy": [{"Direction": 1,
                    "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}},
                                              "Property": "MonthNum"}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{DARK_BG}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{WHITE}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12"}}}}}],
                "dataColors": [{"properties": {
                    "dataColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}}
                }}],
                "plotArea": [{"properties": {
                    "transparency": {"expr": {"Literal": {"Value": "100"}}}
                }}],
                "xAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
                "yAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10"}}}
                }}],
            },
            "drillFilterOtherVisuals": True
        }
    }
    return vc(x, y, w, h, z, cfg)

def line_chart_visual(name, x, y, w, h, z, measure_name, measure_label, title):
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "lineChart",
            "projections": {
                "Category": [{"queryRef": "f.Month", "active": True}],
                "Y": [{"queryRef": f"f.{measure_name}"}],
            },
            "prototypeQuery": {
                "Version": 2,
                "From": [{"Name": "f", "Entity": "FinancialData", "Type": 0}],
                "Select": [
                    {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": "Month"},
                     "Name": "f.Month", "NativeReferenceName": "Month"},
                    {"Measure": {"Expression": {"SourceRef": {"Source": "f"}},
                                 "Property": measure_name},
                     "Name": f"f.{measure_name}", "NativeReferenceName": measure_label},
                ],
                "OrderBy": [{"Direction": 1,
                    "Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}},
                                              "Property": "MonthNum"}}}]
            },
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{DARK_BG}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
                "title": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{WHITE}'"}}}}},
                    "fontSize": {"expr": {"Literal": {"Value": "12"}}}}}],
                "dataColors": [{"properties": {
                    "dataColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{GOLD}'"}}}}}
                }}],
                "plotArea": [{"properties": {
                    "transparency": {"expr": {"Literal": {"Value": "100"}}}
                }}],
                "xAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                }}],
                "yAxis": [{"properties": {
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{LIGHT_GREY}'"}}}}},
                }}],
            },
            "drillFilterOtherVisuals": True
        }
    }
    return vc(x, y, w, h, z, cfg)

def glossary_textbox(name, x, y, w, h, z):
    text_content = (
        "FINANCIAL GLOSSARY\n\n"
        "Revenue: Total income generated from business operations before any deductions.\n\n"
        "COGS (Cost of Goods Sold): Direct costs attributable to the production of goods sold.\n\n"
        "Gross Profit: Revenue minus COGS. Measures production efficiency.\n\n"
        "Opex (Operating Expenses): Day-to-day costs to run the business (salaries, rent, etc.).\n\n"
        "EBIT (Earnings Before Interest & Tax): Operating profit before financing costs and taxes.\n\n"
        "Interest & Tax: Finance charges and income tax owed on profits.\n\n"
        "Net Profit: The bottom line — what remains after all expenses are deducted from revenue.\n\n"
        "Break-Even Point: The sales level where total revenue equals total costs (no profit or loss).\n\n"
        "Net Profit Margin %: Net Profit divided by Revenue — measures overall profitability efficiency."
    )
    cfg = {
        "name": name,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z,
                     "width": w, "height": h, "tabOrder": z}}],
        "singleVisual": {
            "visualType": "textbox",
            "vcObjects": {
                "background": [{"properties": {"show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{CARD_BG}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0"}}}}}],
            },
            "objects": {
                "general": [{"properties": {
                    "paragraphs": [{"textRuns": [{"value": text_content,
                        "textStyle": {"fontSize": "11",
                                      "color": LIGHT_GREY,
                                      "fontFamily": "Segoe UI"}}],
                        "horizontalTextAlignment": "left"}]
                }}]
            }
        }
    }
    return vc(x, y, w, h, z, cfg)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Build pages
# ─────────────────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = 1280, 720
SIDEBAR_W = 220
CONTENT_X = SIDEBAR_W + 10
CONTENT_W = PAGE_W - CONTENT_X - 10

def page_config(bg=DARK_BG):
    return json.dumps({
        "defaultDrillFilterOtherVisuals": True,
        "background": {
            "color": {"solid": {"color": bg}},
            "transparency": 0
        },
        "wallpaper": {
            "color": {"solid": {"color": bg}},
            "transparency": 0
        },
        "outspacePane": {"backgroundColor": {"solid": {"color": bg}}}
    })

def sidebar_visual(page_name, active_page):
    """Sidebar navigation panel."""
    nav_items = ["Overview", "Revenue", "Expenses", "Ratios", "Table", "Glossary"]
    visuals = []
    # Sidebar background
    visuals.append(nav_textbox(uid(), 0, 0, SIDEBAR_W, PAGE_H, 10, "", bg=SIDEBAR_BG))
    # Logo area placeholder
    visuals.append(nav_textbox(uid(), 20, 20, SIDEBAR_W-40, 80, 20,
                               "★ Financial\nAnalysis", font_size=13, bold=True,
                               color=GOLD, bg=SIDEBAR_BG))
    # Nav items
    for i, item in enumerate(nav_items):
        y_pos = 120 + i * 70
        is_active = (item == active_page)
        bg = "#3B4266" if is_active else SIDEBAR_BG
        visuals.append(nav_textbox(uid(), 10, y_pos, SIDEBAR_W-20, 50, 30+i,
                                   item, font_size=12, bold=is_active,
                                   color=GOLD if is_active else WHITE,
                                   bg=bg))
    return visuals

# ── Page 1: Overview ─────────────────────────────────────────────────────────
def build_overview_page():
    visuals = sidebar_visual("Overview", "Overview")

    # Page title
    visuals.append(nav_textbox(uid(), CONTENT_X, 5, CONTENT_W, 40, 50,
                               "Financial Analysis", font_size=18, bold=True,
                               color=WHITE, bg=DARK_BG))

    # 5 KPI cards — top row
    card_w = (CONTENT_W - 20) // 5
    cards = [
        ("Total Revenue",      "Revenue",      '$#,0.0,,"M"'),
        ("Total Expenses",     "Expenses",     '$#,0.0,,"M"'),
        ("Total Gross Profit", "Gross Profit", '$#,0.0,,"M"'),
        ("Total EBIT",         "EBIT",         '$#,0.0,,"M"'),
        ("Total Net Profit",   "Net Profit",   '$#,0.0,,"M"'),
    ]
    for i, (mname, label, _) in enumerate(cards):
        cx = CONTENT_X + i * (card_w + 5)
        visuals.append(card_visual(uid(), cx, 50, card_w, 90, 100+i,
                                   mname, label, _))

    # Combo chart (Net Profit $ + % Margin vs Break-Even)
    visuals.append(combo_chart_visual(uid(), CONTENT_X, 155, CONTENT_W, 240, 200))

    # Waterfall chart
    visuals.append(waterfall_visual(uid(), CONTENT_X, 410, CONTENT_W, 300, 300))

    return {
        "name": uid(), "displayName": "Overview",
        "filters": "[]", "ordinal": 0,
        "visualContainers": visuals,
        "config": page_config(), "width": PAGE_W, "height": PAGE_H
    }

# ── Page 2: Revenue ──────────────────────────────────────────────────────────
def build_revenue_page():
    visuals = sidebar_visual("Revenue", "Revenue")
    visuals.append(nav_textbox(uid(), CONTENT_X, 5, CONTENT_W, 40, 50,
                               "Revenue Analysis", font_size=18, bold=True,
                               color=WHITE, bg=DARK_BG))
    # Revenue KPI
    visuals.append(card_visual(uid(), CONTENT_X, 50, 200, 90, 100,
                               "Total Revenue", "Total Revenue", '$#,0.0,,"M"'))
    visuals.append(card_visual(uid(), CONTENT_X+210, 50, 200, 90, 101,
                               "Total Gross Profit", "Gross Profit", '$#,0.0,,"M"'))
    visuals.append(card_visual(uid(), CONTENT_X+420, 50, 200, 90, 102,
                               "Gross Profit Margin %", "GP Margin %", '0.0"%"'))
    # Monthly Revenue bar chart
    visuals.append(bar_chart_visual(uid(), CONTENT_X, 155, CONTENT_W, 250, 200,
                                    "Total Revenue", "Revenue",
                                    "Monthly Revenue 2023"))
    # COGS bar chart
    visuals.append(bar_chart_visual(uid(), CONTENT_X, 420, CONTENT_W//2-5, 270, 300,
                                    "Total COGS", "COGS",
                                    "Monthly COGS 2023"))
    # Gross Profit bar chart
    visuals.append(bar_chart_visual(uid(), CONTENT_X+CONTENT_W//2+5, 420, CONTENT_W//2-5, 270, 301,
                                    "Total Gross Profit", "Gross Profit",
                                    "Monthly Gross Profit 2023"))
    return {
        "name": uid(), "displayName": "Revenue",
        "filters": "[]", "ordinal": 1,
        "visualContainers": visuals,
        "config": page_config(), "width": PAGE_W, "height": PAGE_H
    }

# ── Page 3: Expenses ─────────────────────────────────────────────────────────
def build_expenses_page():
    visuals = sidebar_visual("Expenses", "Expenses")
    visuals.append(nav_textbox(uid(), CONTENT_X, 5, CONTENT_W, 40, 50,
                               "Expenses Analysis", font_size=18, bold=True,
                               color=WHITE, bg=DARK_BG))
    visuals.append(card_visual(uid(), CONTENT_X, 50, 200, 90, 100,
                               "Total Expenses", "Total Expenses", '$#,0.0,,"M"'))
    visuals.append(card_visual(uid(), CONTENT_X+210, 50, 200, 90, 101,
                               "Total COGS", "Total COGS", '$#,0.0,,"M"'))
    visuals.append(card_visual(uid(), CONTENT_X+420, 50, 200, 90, 102,
                               "Total Opex", "Total Opex", '$#,0.0,,"M"'))
    visuals.append(card_visual(uid(), CONTENT_X+630, 50, 200, 90, 103,
                               "Total Interest Tax", "Interest & Tax", '$#,0,,"K"'))
    visuals.append(bar_chart_visual(uid(), CONTENT_X, 155, CONTENT_W, 250, 200,
                                    "Total Expenses", "Total Expenses",
                                    "Monthly Total Expenses 2023"))
    visuals.append(bar_chart_visual(uid(), CONTENT_X, 420, CONTENT_W//3-5, 270, 300,
                                    "Total COGS", "COGS", "Monthly COGS"))
    visuals.append(bar_chart_visual(uid(), CONTENT_X+CONTENT_W//3+5, 420, CONTENT_W//3-5, 270, 301,
                                    "Total Opex", "Opex", "Monthly Opex"))
    visuals.append(bar_chart_visual(uid(), CONTENT_X+2*(CONTENT_W//3)+10, 420, CONTENT_W//3-10, 270, 302,
                                    "Total Interest Tax", "Interest & Tax", "Interest & Tax"))
    return {
        "name": uid(), "displayName": "Expenses",
        "filters": "[]", "ordinal": 2,
        "visualContainers": visuals,
        "config": page_config(), "width": PAGE_W, "height": PAGE_H
    }

# ── Page 4: Ratios ───────────────────────────────────────────────────────────
def build_ratios_page():
    visuals = sidebar_visual("Ratios", "Ratios")
    visuals.append(nav_textbox(uid(), CONTENT_X, 5, CONTENT_W, 40, 50,
                               "Financial Ratios", font_size=18, bold=True,
                               color=WHITE, bg=DARK_BG))
    visuals.append(card_visual(uid(), CONTENT_X, 50, 200, 90, 100,
                               "Net Profit Margin %", "Net Profit Margin %", '0.0"%"'))
    visuals.append(card_visual(uid(), CONTENT_X+210, 50, 200, 90, 101,
                               "Gross Profit Margin %", "Gross Profit Margin %", '0.0"%"'))
    visuals.append(line_chart_visual(uid(), CONTENT_X, 155, CONTENT_W, 250, 200,
                                     "Net Profit Margin %", "Net Profit Margin %",
                                     "Net Profit Margin % by Month 2023"))
    visuals.append(line_chart_visual(uid(), CONTENT_X, 420, CONTENT_W, 270, 300,
                                     "Gross Profit Margin %", "GP Margin %",
                                     "Gross Profit Margin % by Month 2023"))
    return {
        "name": uid(), "displayName": "Ratios",
        "filters": "[]", "ordinal": 3,
        "visualContainers": visuals,
        "config": page_config(), "width": PAGE_W, "height": PAGE_H
    }

# ── Page 5: Table ────────────────────────────────────────────────────────────
def build_table_page():
    visuals = sidebar_visual("Table", "Table")
    visuals.append(nav_textbox(uid(), CONTENT_X, 5, CONTENT_W, 40, 50,
                               "Financial Data Table", font_size=18, bold=True,
                               color=WHITE, bg=DARK_BG))
    table_measures = [
        {"measure": "Total Revenue",      "label": "Revenue"},
        {"measure": "Total COGS",         "label": "COGS"},
        {"measure": "Total Gross Profit", "label": "Gross Profit"},
        {"measure": "Total Opex",         "label": "Opex"},
        {"measure": "Total EBIT",         "label": "EBIT"},
        {"measure": "Total Interest Tax", "label": "Interest & Tax"},
        {"measure": "Total Net Profit",   "label": "Net Profit"},
        {"measure": "Net Profit Margin %","label": "NP Margin %"},
    ]
    visuals.append(table_visual(uid(), CONTENT_X, 55, CONTENT_W, 640, 100, table_measures))
    return {
        "name": uid(), "displayName": "Table",
        "filters": "[]", "ordinal": 4,
        "visualContainers": visuals,
        "config": page_config(), "width": PAGE_W, "height": PAGE_H
    }

# ── Page 6: Glossary ─────────────────────────────────────────────────────────
def build_glossary_page():
    visuals = sidebar_visual("Glossary", "Glossary")
    visuals.append(nav_textbox(uid(), CONTENT_X, 5, CONTENT_W, 40, 50,
                               "Financial Glossary", font_size=18, bold=True,
                               color=WHITE, bg=DARK_BG))
    visuals.append(glossary_textbox(uid(), CONTENT_X, 55, CONTENT_W, 640, 100))
    return {
        "name": uid(), "displayName": "Glossary",
        "filters": "[]", "ordinal": 5,
        "visualContainers": visuals,
        "config": page_config(), "width": PAGE_W, "height": PAGE_H
    }

# ─────────────────────────────────────────────────────────────────────────────
# 5. Report/Layout
# ─────────────────────────────────────────────────────────────────────────────
REPORT_LAYOUT = {
    "id": 0,
    "resourcePackages": [{
        "resourcePackage": {
            "disabled": False,
            "items": [{"type": 202, "path": "BaseThemes/CY23SU11.json",
                       "name": "CY23SU11"}],
            "name": "SharedResources",
            "type": 2
        }
    }],
    "sections": [
        build_overview_page(),
        build_revenue_page(),
        build_expenses_page(),
        build_ratios_page(),
        build_table_page(),
        build_glossary_page(),
    ],
    "config": json.dumps({
        "version": "5.49",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU11", "version": "5.49", "type": 2}
        },
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
        },
        "objects": {
            "section": [{"properties": {
                "background": {"solid": {"color": DARK_BG}},
                "wallpaper": {"solid": {"color": DARK_BG}}
            }}]
        }
    }),
    "layoutOptimization": 0
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. Other files
# ─────────────────────────────────────────────────────────────────────────────
CONTENT_TYPES = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/DataModelSchema"  ContentType="application/json"/>
  <Override PartName="/DiagramLayout"    ContentType="application/json"/>
  <Override PartName="/Report/Layout"    ContentType="application/json"/>
  <Override PartName="/Settings"         ContentType="application/json"/>
  <Override PartName="/Metadata"         ContentType="application/json"/>
</Types>"""

SETTINGS = {
    "Version": 4,
    "ReportSettings": {},
    "QueriesSettings": {
        "TypeDetectionEnabled": True,
        "RelationshipImportEnabled": True,
        "Version": "2.123.742.0"
    }
}

METADATA = {
    "Version": 5,
    "AutoCreatedRelationships": [],
    "CreatedFrom": "Cloud",
    "CreatedFromRelease": "2023.11"
}

DIAGRAM_LAYOUT = {
    "version": 1,
    "tables": [{"name": "FinancialData", "x": 100, "y": 100}]
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. Write PBIT file
# ─────────────────────────────────────────────────────────────────────────────
def write_utf16le(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-16-le")

def write_pbit(path: str):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Version",           "3.0")
        zf.writestr("[Content_Types].xml", CONTENT_TYPES)
        # DataModelSchema is UTF-8
        zf.writestr("DataModelSchema",
                    json.dumps(DATA_MODEL_SCHEMA, ensure_ascii=False, indent=2).encode("utf-8"))
        # The rest use UTF-16-LE (Power BI convention)
        zf.writestr("Report/Layout",     write_utf16le(REPORT_LAYOUT))
        zf.writestr("Settings",          write_utf16le(SETTINGS))
        zf.writestr("Metadata",          write_utf16le(METADATA))
        zf.writestr("DiagramLayout",     write_utf16le(DIAGRAM_LAYOUT))
        zf.writestr("SecurityBindings",  b"")
        # Base theme stub (required by layout config reference)
        zf.writestr("Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json",
                    json.dumps({"name": "CY23SU11", "version": "5.49"}).encode("utf-8"))
    print(f"✓ Written: {path}")

if __name__ == "__main__":
    out = "/home/user/newm/FinancialAnalysis.pbit"
    write_pbit(out)

    # Verify
    import os
    size = os.path.getsize(out)
    print(f"  Size: {size:,} bytes")
    z = zipfile.ZipFile(out)
    print("  Contents:", z.namelist())

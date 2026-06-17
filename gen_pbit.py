import zipfile
import json
import uuid

def guid():
    return str(uuid.uuid4()).upper()

# ── Financial Data ──────────────────────────────────────────────
months   = ["January","February","March","April","May","June",
            "July","August","September","October","November","December"]
revenue  = [850000,780000,920000,880000,950000,1020000,
            990000,1050000,980000,1100000,1080000,1200000]
expenses = [650000,610000,720000,690000,740000,790000,
            770000,820000,760000,850000,840000,920000]
profit   = [r-e for r,e in zip(revenue,expenses)]

# ── M expression as a SINGLE STRING (not a list) ────────────────
rows = ",\r\n        ".join(
    [f'{{"{m}", {r}, {e}, {p}}}' for m,r,e,p in zip(months,revenue,expenses,profit)]
)
m_expr = (
    "let\r\n"
    "    Source = #table(\r\n"
    "        type table [Month = text, Revenue = number, Expenses = number, Profit = number],\r\n"
    "        {\r\n"
    f"        {rows}\r\n"
    "        }\r\n"
    "    )\r\n"
    "in\r\n"
    "    Source"
)

# ── DataModelSchema ─────────────────────────────────────────────
dms = {
    "name": "Model",
    "defaultPowerBIDataSourceVersion": "powerBI_V3",
    "tables": [
        {
            "name": "FinancialData",
            "lineageTag": guid(),
            "partitions": [{
                "name": "FinancialData",
                "mode": "import",
                "lineageTag": guid(),
                "source": {
                    "type": "m",
                    "expression": m_expr
                }
            }],
            "columns": [
                {
                    "name": "Month",
                    "dataType": "string",
                    "lineageTag": guid(),
                    "summarizeBy": "none",
                    "sourceColumn": "Month",
                    "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
                },
                {
                    "name": "Revenue",
                    "dataType": "int64",
                    "lineageTag": guid(),
                    "summarizeBy": "sum",
                    "sourceColumn": "Revenue",
                    "formatString": "$#,##0",
                    "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
                },
                {
                    "name": "Expenses",
                    "dataType": "int64",
                    "lineageTag": guid(),
                    "summarizeBy": "sum",
                    "sourceColumn": "Expenses",
                    "formatString": "$#,##0",
                    "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
                },
                {
                    "name": "Profit",
                    "dataType": "int64",
                    "lineageTag": guid(),
                    "summarizeBy": "sum",
                    "sourceColumn": "Profit",
                    "formatString": "$#,##0",
                    "annotations": [{"name": "SummarizationSetBy", "value": "Automatic"}]
                }
            ],
            "measures": [
                {
                    "name": "Total Revenue",
                    "expression": "SUM(FinancialData[Revenue])",
                    "formatString": "$#,##0",
                    "lineageTag": guid()
                },
                {
                    "name": "Total Expenses",
                    "expression": "SUM(FinancialData[Expenses])",
                    "formatString": "$#,##0",
                    "lineageTag": guid()
                },
                {
                    "name": "Total Profit",
                    "expression": "SUM(FinancialData[Profit])",
                    "formatString": "$#,##0",
                    "lineageTag": guid()
                },
                {
                    "name": "Profit Margin",
                    "expression": "DIVIDE(SUM(FinancialData[Profit]),SUM(FinancialData[Revenue]),0)",
                    "formatString": "0.00%",
                    "lineageTag": guid()
                }
            ]
        }
    ],
    "annotations": [
        {"name": "PBI_QueryOrder",               "value": "[\"FinancialData\"]"},
        {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
        {"name": "PBIDesktopVersion",             "value": "2.128.702.0"}
    ]
}

# ── Visual builder ───────────────────────────────────────────────
def vc(x, y, w, h, config_dict, query_dict=None, transforms_dict=None):
    item = {
        "x": x, "y": y, "z": 0,
        "width": w, "height": h,
        "config": json.dumps(config_dict, separators=(',', ':')),
        "filters": "[]"
    }
    if query_dict:
        item["query"] = json.dumps(query_dict, separators=(',', ':'))
    if transforms_dict:
        item["dataTransforms"] = json.dumps(transforms_dict, separators=(',', ':'))
    return item

def from_clause():
    return [{"Name": "f", "Entity": "FinancialData", "Type": 0}]

def col_expr(prop):
    return {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": prop}}

def agg_expr(prop):
    return {"Aggregation": {"Expression": {"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": prop}}, "Function": 0}}

def meas_expr(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": prop}}

# Card visual
def card_visual(x, y, w, h, vis_id, col, display, is_measure=False):
    qname = f"FinancialData.{col}" if is_measure else f"Sum(FinancialData.{col})"
    sel   = {**(meas_expr(col) if is_measure else agg_expr(col)), "Name": qname}
    query = {"Version": 2, "From": from_clause(), "Select": [sel]}
    config = {
        "name": vis_id,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": qname, "active": True}]},
            "prototypeQuery": query,
            "columnProperties": {},
            "vcObjects": {}
        }
    }
    transforms = {"selects": [{"displayName": display, "queryName": qname, "roles": {"Values": 0}, "type": 1}]}
    return vc(x, y, w, h, config, query, transforms)

# Clustered column chart
def column_chart(x, y, w, h, vis_id):
    s_month = {**col_expr("Month"),    "Name": "FinancialData.Month"}
    s_rev   = {**agg_expr("Revenue"),  "Name": "Sum(FinancialData.Revenue)"}
    s_exp   = {**agg_expr("Expenses"), "Name": "Sum(FinancialData.Expenses)"}
    query = {"Version": 2, "From": from_clause(), "Select": [s_month, s_rev, s_exp]}
    config = {
        "name": vis_id,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "clusteredColumnChart",
            "projections": {
                "Category": [{"queryRef": "FinancialData.Month"}],
                "Y": [
                    {"queryRef": "Sum(FinancialData.Revenue)",  "active": True},
                    {"queryRef": "Sum(FinancialData.Expenses)"}
                ]
            },
            "prototypeQuery": query,
            "columnProperties": {},
            "vcObjects": {}
        }
    }
    transforms = {"selects": [
        {"displayName": "Month",    "queryName": "FinancialData.Month",         "roles": {"Category": 0}, "type": 2},
        {"displayName": "Revenue",  "queryName": "Sum(FinancialData.Revenue)",  "roles": {"Y": 0},        "type": 1},
        {"displayName": "Expenses", "queryName": "Sum(FinancialData.Expenses)","roles": {"Y": 1},        "type": 1}
    ]}
    return vc(x, y, w, h, config, query, transforms)

# Line chart
def line_chart(x, y, w, h, vis_id):
    s_month  = {**col_expr("Month"),  "Name": "FinancialData.Month"}
    s_profit = {**agg_expr("Profit"), "Name": "Sum(FinancialData.Profit)"}
    query = {"Version": 2, "From": from_clause(), "Select": [s_month, s_profit]}
    config = {
        "name": vis_id,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "lineChart",
            "projections": {
                "Category": [{"queryRef": "FinancialData.Month"}],
                "Y":        [{"queryRef": "Sum(FinancialData.Profit)", "active": True}]
            },
            "prototypeQuery": query,
            "columnProperties": {},
            "vcObjects": {}
        }
    }
    transforms = {"selects": [
        {"displayName": "Month",  "queryName": "FinancialData.Month",        "roles": {"Category": 0}, "type": 2},
        {"displayName": "Profit", "queryName": "Sum(FinancialData.Profit)",  "roles": {"Y": 0},        "type": 1}
    ]}
    return vc(x, y, w, h, config, query, transforms)

# Table visual
def table_visual(x, y, w, h, vis_id):
    s_month  = {**col_expr("Month"),    "Name": "FinancialData.Month"}
    s_rev    = {**agg_expr("Revenue"),  "Name": "Sum(FinancialData.Revenue)"}
    s_exp    = {**agg_expr("Expenses"), "Name": "Sum(FinancialData.Expenses)"}
    s_profit = {**agg_expr("Profit"),   "Name": "Sum(FinancialData.Profit)"}
    query = {"Version": 2, "From": from_clause(), "Select": [s_month, s_rev, s_exp, s_profit]}
    config = {
        "name": vis_id,
        "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": 0, "width": w, "height": h}}],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": [
                {"queryRef": "FinancialData.Month"},
                {"queryRef": "Sum(FinancialData.Revenue)"},
                {"queryRef": "Sum(FinancialData.Expenses)"},
                {"queryRef": "Sum(FinancialData.Profit)"}
            ]},
            "prototypeQuery": query,
            "columnProperties": {},
            "vcObjects": {}
        }
    }
    transforms = {"selects": [
        {"displayName": "Month",    "queryName": "FinancialData.Month",         "roles": {"Values": 0}, "type": 2},
        {"displayName": "Revenue",  "queryName": "Sum(FinancialData.Revenue)",  "roles": {"Values": 1}, "type": 1},
        {"displayName": "Expenses", "queryName": "Sum(FinancialData.Expenses)","roles": {"Values": 2}, "type": 1},
        {"displayName": "Profit",   "queryName": "Sum(FinancialData.Profit)",  "roles": {"Values": 3}, "type": 1}
    ]}
    return vc(x, y, w, h, config, query, transforms)

# ── Assemble visuals ────────────────────────────────────────────
visuals = [
    card_visual(  20,  20, 270, 110, "card_rev",    "Revenue",       "Total Revenue"),
    card_visual( 310,  20, 270, 110, "card_exp",    "Expenses",      "Total Expenses"),
    card_visual( 600,  20, 270, 110, "card_profit", "Profit",        "Total Profit"),
    card_visual( 890,  20, 270, 110, "card_margin", "Profit Margin", "Profit Margin", is_measure=True),
    column_chart( 20, 150, 770, 300, "col_chart"),
    line_chart(  810, 150, 450, 300, "line_chart"),
    table_visual( 20, 470, 1240, 230, "tbl_visual"),
]

# ── Report Layout ───────────────────────────────────────────────
layout = {
    "id": 0,
    "resourcePackages": [],
    "sections": [{
        "id": 0,
        "name": "ReportSection",
        "displayName": "Financial Dashboard",
        "filters": "[]",
        "ordinal": 0,
        "visualContainers": visuals,
        "width": 1280,
        "height": 720,
        "config": json.dumps({"relationships": [], "queryCanCrossFilterVisual": True}, separators=(',', ':')),
        "displayOption": 0
    }],
    "config": json.dumps({
        "version": "5.47",
        "themeCollection": {
            "baseTheme": {"name": "CY24SU08", "reportVersionAtImport": "5.47", "type": 2}
        }
    }, separators=(',', ':')),
    "layoutOptimization": 0
}

# ── Supporting files ────────────────────────────────────────────
content_types = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="json" ContentType="application/json" />'
    '<Default Extension="xml"  ContentType="application/xml" />'
    '</Types>'
)

metadata       = {"version": 4, "upgradedFrom": 3, "createdFromTemplate": False}
settings       = {"QnaAutoSuggestions": True, "AutoRecoverSaves": False, "Version": 4}
diagram_layout = {
    "version": 1,
    "diagrams": [{"ordinal": 0, "scrollPosition": {"x": 0, "y": 0}, "zoom": 1, "nodes": []}]
}

# ── Write PBIT using ZIP_STORED (no compression) ────────────────
out_path = "/home/user/newm/financial_dashboard.pbit"

def write_utf8(zf, name, content):
    data = content.encode("utf-8-sig")   # UTF-8 with BOM — Power BI expects this
    zf.writestr(
        zipfile.ZipInfo(name),
        data
    )

with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    # Version must be plain ASCII, no BOM
    zf.writestr(zipfile.ZipInfo("Version"), b"2.0")
    write_utf8(zf, "[Content_Types].xml", content_types)
    write_utf8(zf, "DataModelSchema",     json.dumps(dms,            ensure_ascii=False, indent=2))
    write_utf8(zf, "Report/Layout",       json.dumps(layout,         ensure_ascii=False))
    write_utf8(zf, "Metadata",            json.dumps(metadata,       ensure_ascii=False))
    write_utf8(zf, "Settings",            json.dumps(settings,       ensure_ascii=False))
    write_utf8(zf, "DiagramLayout",       json.dumps(diagram_layout, ensure_ascii=False))

import os
print(f"Created: {out_path}  ({os.path.getsize(out_path):,} bytes)")

with zipfile.ZipFile(out_path, "r") as zf:
    for info in zf.infolist():
        print(f"  {info.filename:30s}  {info.file_size:6d} bytes")

print("Done!")

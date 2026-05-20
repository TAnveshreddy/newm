#!/usr/bin/env python3
"""
Fix SalesAnalytics_Dashboard_4.pbix:
  1. Rebuild DiagramLayout with star-schema table positions
  2. Produce a companion .pbit (Power BI Template) whose DataModelSchema
     includes all table relationships in TMSL JSON so Power BI Desktop
     creates them automatically on data refresh.
"""
import zipfile, json, os, shutil

SRC = "/root/.claude/uploads/bca2e082-c5c3-477b-a9e1-cb5c255f50cf/2fe318b8-SalesAnalytics_Dashboard_4.pbix"
DST_PBIX = "/home/user/newm/SalesAnalytics_Dashboard_v2.pbix"
DST_PBIT = "/home/user/newm/SalesAnalytics_Dashboard.pbit"

# ── Read source ──────────────────────────────────────────────────────────────
with zipfile.ZipFile(SRC, "r") as z:
    raw = {m: z.read(m) for m in z.namelist()}

# ── 1. Rebuild DiagramLayout (star schema) ───────────────────────────────────
# Layout: Orders (fact) at centre, dims around it
# Positions chosen for a clear star schema view in Power BI Model View

STAR_LAYOUT = {
    "version": "1.1.0",
    "diagrams": [
        {
            "ordinal": 0,
            "scrollPosition": {"x": 0, "y": 0},
            "zoomValue": 70,
            "nodes": [
                # ── Fact table (centre) ──────────────────────────────────────
                {
                    "nodeIndex": "Orders",
                    "nodeLineageTag": "3d220f15-fcd7-4892-b853-cd66b8d38f4e",
                    "location": {"x": 480, "y": 320},
                    "size": {"width": 240, "height": 340},
                    "zIndex": 2
                },
                # ── Dimension tables (around fact) ───────────────────────────
                {
                    "nodeIndex": "Customers",
                    "nodeLineageTag": "1538a4d8-a39e-49d1-8d4e-f2b9af2f1bda",
                    "location": {"x": 80, "y": 80},
                    "size": {"width": 240, "height": 200},
                    "zIndex": 1
                },
                {
                    "nodeIndex": "Products",
                    "nodeLineageTag": "ca3f3930-5ca3-4365-8a7c-b8987b332a58",
                    "location": {"x": 880, "y": 80},
                    "size": {"width": 240, "height": 220},
                    "zIndex": 1
                },
                {
                    "nodeIndex": "Users",
                    "nodeLineageTag": "452791df-4c5a-44b0-b59f-42c1b362f9a9",
                    "location": {"x": 80, "y": 580},
                    "size": {"width": 240, "height": 160},
                    "zIndex": 1
                },
                {
                    "nodeIndex": "Returns",
                    "nodeLineageTag": "07d5e658-5a32-4bd3-a214-b3e9e65831aa",
                    "location": {"x": 880, "y": 580},
                    "size": {"width": 240, "height": 140},
                    "zIndex": 1
                },
                {
                    "nodeIndex": "Monthly KPIs",
                    "nodeLineageTag": "00debda1-7a60-41b5-b33d-2a11d2641014",
                    "location": {"x": 480, "y": 780},
                    "size": {"width": 240, "height": 280},
                    "zIndex": 1
                },
                {
                    "nodeIndex": "Sales",
                    "nodeLineageTag": "af7c4660-b9d4-444d-b9b4-19b481576d75",
                    "location": {"x": 480, "y": 20},
                    "size": {"width": 240, "height": 220},
                    "zIndex": 1
                },
            ]
        }
    ]
}

raw["DiagramLayout"] = json.dumps(STAR_LAYOUT, separators=(",", ":")).encode("utf-16-le")

# ── Write updated PBIX ───────────────────────────────────────────────────────
with zipfile.ZipFile(DST_PBIX, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for name, data in raw.items():
        if name == "DataModel":
            zout.writestr(zipfile.ZipInfo(name), data, compress_type=zipfile.ZIP_STORED)
        else:
            zout.writestr(name, data)

print(f"PBIX written: {DST_PBIX} ({os.path.getsize(DST_PBIX):,} bytes)")

# ── 2. Build .pbit with TMSL DataModelSchema ─────────────────────────────────
# TMSL includes full table schema + relationships so Power BI Desktop
# creates them when the user refreshes from the Excel source.

# Read Report/Layout (will be reused)
layout_bytes = raw["Report/Layout"]
layout_text  = layout_bytes.decode("utf-16-le")
settings     = raw["Settings"].decode("utf-16-le")
metadata_raw = raw["Metadata"]

EXCEL_PARAM = "ExcelFilePath"

TMSL = {
    "name": "SalesAnalytics",
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "collation": "Latin1_General_100_BIN2_UTF8",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",
        "expressions": [
            {
                "name": EXCEL_PARAM,
                "description": "Path to the Excel data file",
                "kind": "m",
                "expression": "\"C:\\\\Users\\\\YourName\\\\Downloads\\\\PowerBI_Data_Model.xlsx\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]",
                "annotations": [{"name": "PBI_NavigationStepName", "value": "Navigation"}]
            }
        ],
        "tables": [
            # ── Orders (main fact) ───────────────────────────────────────────
            {
                "name": "Orders",
                "lineageTag": "3d220f15-fcd7-4892-b853-cd66b8d38f4e",
                "columns": [
                    {"name": "Order ID",     "dataType": "string",   "lineageTag": "col-ord-01", "sourceColumn": "Order ID"},
                    {"name": "Customer ID",  "dataType": "string",   "lineageTag": "col-ord-02", "sourceColumn": "Customer ID"},
                    {"name": "Order Date",   "dataType": "dateTime", "lineageTag": "col-ord-03", "sourceColumn": "Order Date",
                     "formatString": "Short Date", "annotations": [{"name": "UnderlyingDateTimeDataType", "value": "Date"}]},
                    {"name": "Category",     "dataType": "string",   "lineageTag": "col-ord-04", "sourceColumn": "Category"},
                    {"name": "Sub-Category", "dataType": "string",   "lineageTag": "col-ord-05", "sourceColumn": "Sub-Category"},
                    {"name": "Region",       "dataType": "string",   "lineageTag": "col-ord-06", "sourceColumn": "Region"},
                    {"name": "City",         "dataType": "string",   "lineageTag": "col-ord-07", "sourceColumn": "City"},
                    {"name": "Segment",      "dataType": "string",   "lineageTag": "col-ord-08", "sourceColumn": "Segment"},
                    {"name": "Sales",        "dataType": "double",   "lineageTag": "col-ord-09", "sourceColumn": "Sales",    "formatString": "#,0.00"},
                    {"name": "Profit",       "dataType": "double",   "lineageTag": "col-ord-10", "sourceColumn": "Profit",   "formatString": "#,0.00"},
                    {"name": "Quantity",     "dataType": "int64",    "lineageTag": "col-ord-11", "sourceColumn": "Quantity"},
                    {"name": "Discount",     "dataType": "double",   "lineageTag": "col-ord-12", "sourceColumn": "Discount", "formatString": "0.0%"},
                    {"name": "Channel",      "dataType": "string",   "lineageTag": "col-ord-13", "sourceColumn": "Channel"},
                    {"name": "Status",       "dataType": "string",   "lineageTag": "col-ord-14", "sourceColumn": "Status"},
                    {"name": "Product ID",   "dataType": "string",   "lineageTag": "col-ord-15", "sourceColumn": "Product ID"},
                    {"name": "User ID",      "dataType": "string",   "lineageTag": "col-ord-16", "sourceColumn": "User ID"},
                ],
                "measures": [
                    {
                        "name": "Total Revenue",
                        "expression": "SUM(Orders[Sales])",
                        "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00",
                        "lineageTag": "meas-rev"
                    },
                    {
                        "name": "Total Profit",
                        "expression": "SUM(Orders[Profit])",
                        "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00",
                        "lineageTag": "meas-prof"
                    },
                    {
                        "name": "Total Orders",
                        "expression": "COUNTROWS(Orders)",
                        "formatString": "#,0",
                        "lineageTag": "meas-cnt"
                    },
                    {
                        "name": "Profit Margin %",
                        "expression": "DIVIDE(SUM(Orders[Profit]), SUM(Orders[Sales]), 0)",
                        "formatString": "0.0%",
                        "lineageTag": "meas-margin"
                    },
                    {
                        "name": "Avg Order Value",
                        "expression": "DIVIDE(SUM(Orders[Sales]), COUNTROWS(Orders), 0)",
                        "formatString": "\\$#,0.00",
                        "lineageTag": "meas-aov"
                    },
                    {
                        "name": "Revenue YTD",
                        "expression": "TOTALYTD(SUM(Orders[Sales]), Orders[Order Date])",
                        "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00",
                        "lineageTag": "meas-ytd"
                    },
                    {
                        "name": "Revenue PY",
                        "expression": "CALCULATE(SUM(Orders[Sales]), SAMEPERIODLASTYEAR(Orders[Order Date]))",
                        "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00",
                        "lineageTag": "meas-py"
                    },
                    {
                        "name": "YoY Growth %",
                        "expression": "DIVIDE([Revenue YTD] - [Revenue PY], [Revenue PY], 0)",
                        "formatString": "0.0%",
                        "lineageTag": "meas-yoy"
                    },
                    {
                        "name": "Return Rate %",
                        "expression": "DIVIDE(CALCULATE(COUNTROWS(Returns)), COUNTROWS(Orders), 0)",
                        "formatString": "0.0%",
                        "lineageTag": "meas-rr"
                    },
                ],
                "partitions": [
                    {
                        "name": "Orders",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                "    Source = Excel.Workbook(File.Contents(" + EXCEL_PARAM + "), null, true),",
                                "    Sales_Sheet = Source{[Item=\"Sales\",Kind=\"Sheet\"]}[Data],",
                                "    #\"Promoted Headers\" = Table.PromoteHeaders(Sales_Sheet, [PromoteAllScalars=true]),",
                                "    #\"Changed Types\" = Table.TransformColumnTypes(#\"Promoted Headers\",{",
                                "        {\"Order ID\", type text}, {\"Customer ID\", type text},",
                                "        {\"Product ID\", type text}, {\"User ID\", type text},",
                                "        {\"Order Date\", type date}, {\"Sales\", type number},",
                                "        {\"Profit\", type number}, {\"Quantity\", Int64.Type},",
                                "        {\"Discount\", type number}, {\"Channel\", type text},",
                                "        {\"Status\", type text}})",
                                "in",
                                "    #\"Changed Types\""
                            ]
                        }
                    }
                ],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },
            # ── Customers ────────────────────────────────────────────────────
            {
                "name": "Customers",
                "lineageTag": "1538a4d8-a39e-49d1-8d4e-f2b9af2f1bda",
                "columns": [
                    {"name": "Customer ID",    "dataType": "string", "lineageTag": "col-cust-01", "sourceColumn": "Customer ID"},
                    {"name": "Customer Name",  "dataType": "string", "lineageTag": "col-cust-02", "sourceColumn": "Customer Name"},
                    {"name": "Email",          "dataType": "string", "lineageTag": "col-cust-03", "sourceColumn": "Email"},
                    {"name": "Location",       "dataType": "string", "lineageTag": "col-cust-04", "sourceColumn": "Location"},
                    {"name": "Segment",        "dataType": "string", "lineageTag": "col-cust-05", "sourceColumn": "Segment"},
                    {"name": "Join Date",      "dataType": "dateTime","lineageTag": "col-cust-06", "sourceColumn": "Join Date",
                     "formatString": "Short Date"},
                ],
                "partitions": [
                    {
                        "name": "Customers",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                "    Source = Excel.Workbook(File.Contents(" + EXCEL_PARAM + "), null, true),",
                                "    Sheet = Source{[Item=\"Customers\",Kind=\"Sheet\"]}[Data],",
                                "    #\"Promoted Headers\" = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                                "    #\"Changed Types\" = Table.TransformColumnTypes(#\"Promoted Headers\",{",
                                "        {\"Customer ID\", type text}, {\"Customer Name\", type text},",
                                "        {\"Email\", type text}, {\"Location\", type text},",
                                "        {\"Segment\", type text}, {\"Join Date\", type date}})",
                                "in",
                                "    #\"Changed Types\""
                            ]
                        }
                    }
                ],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },
            # ── Products ─────────────────────────────────────────────────────
            {
                "name": "Products",
                "lineageTag": "ca3f3930-5ca3-4365-8a7c-b8987b332a58",
                "columns": [
                    {"name": "Product ID",    "dataType": "string", "lineageTag": "col-prod-01", "sourceColumn": "Product ID"},
                    {"name": "Product Name",  "dataType": "string", "lineageTag": "col-prod-02", "sourceColumn": "Product Name"},
                    {"name": "Category",      "dataType": "string", "lineageTag": "col-prod-03", "sourceColumn": "Category"},
                    {"name": "Sub-Category",  "dataType": "string", "lineageTag": "col-prod-04", "sourceColumn": "Sub-Category"},
                    {"name": "Unit Price",    "dataType": "double", "lineageTag": "col-prod-05", "sourceColumn": "Unit Price", "formatString": "\\$#,0.00"},
                    {"name": "Cost",          "dataType": "double", "lineageTag": "col-prod-06", "sourceColumn": "Cost",       "formatString": "\\$#,0.00"},
                ],
                "partitions": [
                    {
                        "name": "Products",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                "    Source = Excel.Workbook(File.Contents(" + EXCEL_PARAM + "), null, true),",
                                "    Sheet = Source{[Item=\"Products\",Kind=\"Sheet\"]}[Data],",
                                "    #\"Promoted Headers\" = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                                "    #\"Changed Types\" = Table.TransformColumnTypes(#\"Promoted Headers\",{",
                                "        {\"Product ID\", type text}, {\"Product Name\", type text},",
                                "        {\"Category\", type text}, {\"Sub-Category\", type text},",
                                "        {\"Unit Price\", type number}, {\"Cost\", type number}})",
                                "in",
                                "    #\"Changed Types\""
                            ]
                        }
                    }
                ],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },
            # ── Users ────────────────────────────────────────────────────────
            {
                "name": "Users",
                "lineageTag": "452791df-4c5a-44b0-b59f-42c1b362f9a9",
                "columns": [
                    {"name": "User ID",   "dataType": "string", "lineageTag": "col-usr-01", "sourceColumn": "User ID"},
                    {"name": "Username",  "dataType": "string", "lineageTag": "col-usr-02", "sourceColumn": "Username"},
                    {"name": "Email",     "dataType": "string", "lineageTag": "col-usr-03", "sourceColumn": "Email"},
                    {"name": "Role",      "dataType": "string", "lineageTag": "col-usr-04", "sourceColumn": "Role"},
                    {"name": "Location",  "dataType": "string", "lineageTag": "col-usr-05", "sourceColumn": "Location"},
                    {"name": "Region",    "dataType": "string", "lineageTag": "col-usr-06", "sourceColumn": "Region"},
                ],
                "partitions": [
                    {
                        "name": "Users",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                "    Source = Excel.Workbook(File.Contents(" + EXCEL_PARAM + "), null, true),",
                                "    Sheet = Source{[Item=\"Users\",Kind=\"Sheet\"]}[Data],",
                                "    #\"Promoted Headers\" = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                                "    #\"Changed Types\" = Table.TransformColumnTypes(#\"Promoted Headers\",{",
                                "        {\"User ID\", type text}, {\"Username\", type text},",
                                "        {\"Email\", type text}, {\"Role\", type text},",
                                "        {\"Location\", type text}, {\"Region\", type text}})",
                                "in",
                                "    #\"Changed Types\""
                            ]
                        }
                    }
                ],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },
            # ── Returns ──────────────────────────────────────────────────────
            {
                "name": "Returns",
                "lineageTag": "07d5e658-5a32-4bd3-a214-b3e9e65831aa",
                "columns": [
                    {"name": "Order ID",  "dataType": "string", "lineageTag": "col-ret-01", "sourceColumn": "Order ID"},
                    {"name": "Region",    "dataType": "string", "lineageTag": "col-ret-02", "sourceColumn": "Region"},
                    {"name": "Returned",  "dataType": "string", "lineageTag": "col-ret-03", "sourceColumn": "Returned"},
                ],
                "partitions": [
                    {
                        "name": "Returns",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                "    Source = Excel.Workbook(File.Contents(" + EXCEL_PARAM + "), null, true),",
                                "    Sheet = Source{[Item=\"Returns\",Kind=\"Sheet\"]}[Data],",
                                "    #\"Promoted Headers\" = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                                "    #\"Changed Types\" = Table.TransformColumnTypes(#\"Promoted Headers\",{",
                                "        {\"Order ID\", type text}, {\"Region\", type text},",
                                "        {\"Returned\", type text}})",
                                "in",
                                "    #\"Changed Types\""
                            ]
                        }
                    }
                ],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },
            # ── DateTable ────────────────────────────────────────────────────
            {
                "name": "DateTable",
                "lineageTag": "date-table-001",
                "isHidden": False,
                "columns": [
                    {"name": "Date",       "dataType": "dateTime", "lineageTag": "col-dt-01", "sourceColumn": "Date",
                     "formatString": "Short Date", "isKey": True,
                     "annotations": [{"name": "UnderlyingDateTimeDataType", "value": "Date"}]},
                    {"name": "Year",       "dataType": "int64",    "lineageTag": "col-dt-02", "sourceColumn": "Year"},
                    {"name": "Quarter",    "dataType": "string",   "lineageTag": "col-dt-03", "sourceColumn": "Quarter"},
                    {"name": "Month",      "dataType": "int64",    "lineageTag": "col-dt-04", "sourceColumn": "Month"},
                    {"name": "Month Name", "dataType": "string",   "lineageTag": "col-dt-05", "sourceColumn": "Month Name"},
                    {"name": "Week",       "dataType": "int64",    "lineageTag": "col-dt-06", "sourceColumn": "Week"},
                    {"name": "Day",        "dataType": "int64",    "lineageTag": "col-dt-07", "sourceColumn": "Day"},
                    {"name": "Day Name",   "dataType": "string",   "lineageTag": "col-dt-08", "sourceColumn": "Day Name"},
                ],
                "partitions": [
                    {
                        "name": "DateTable",
                        "mode": "import",
                        "source": {
                            "type": "m",
                            "expression": [
                                "let",
                                "    Source = Excel.Workbook(File.Contents(" + EXCEL_PARAM + "), null, true),",
                                "    Sheet = Source{[Item=\"DateTable\",Kind=\"Sheet\"]}[Data],",
                                "    #\"Promoted Headers\" = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                                "    #\"Changed Types\" = Table.TransformColumnTypes(#\"Promoted Headers\",{",
                                "        {\"Date\", type date}, {\"Year\", Int64.Type},",
                                "        {\"Quarter\", type text}, {\"Month\", Int64.Type},",
                                "        {\"Month Name\", type text}, {\"Week\", Int64.Type},",
                                "        {\"Day\", Int64.Type}, {\"Day Name\", type text}})",
                                "in",
                                "    #\"Changed Types\""
                            ]
                        }
                    }
                ],
                "annotations": [
                    {"name": "PBI_ResultType", "value": "Table"},
                    {"name": "PBI_IsDateTable", "value": "true"}
                ]
            },
        ],
        # ── Relationships (star schema) ───────────────────────────────────────
        "relationships": [
            {
                "name": "Orders_Customers",
                "fromTable": "Orders",
                "fromColumn": "Customer ID",
                "toTable": "Customers",
                "toColumn": "Customer ID",
                "fromCardinality": "many",
                "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection",
                "isActive": True
            },
            {
                "name": "Orders_Products",
                "fromTable": "Orders",
                "fromColumn": "Product ID",
                "toTable": "Products",
                "toColumn": "Product ID",
                "fromCardinality": "many",
                "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection",
                "isActive": True
            },
            {
                "name": "Orders_Users",
                "fromTable": "Orders",
                "fromColumn": "User ID",
                "toTable": "Users",
                "toColumn": "User ID",
                "fromCardinality": "many",
                "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection",
                "isActive": True
            },
            {
                "name": "Returns_Orders",
                "fromTable": "Returns",
                "fromColumn": "Order ID",
                "toTable": "Orders",
                "toColumn": "Order ID",
                "fromCardinality": "many",
                "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection",
                "isActive": True
            },
            {
                "name": "Orders_DateTable",
                "fromTable": "Orders",
                "fromColumn": "Order Date",
                "toTable": "DateTable",
                "toColumn": "Date",
                "fromCardinality": "many",
                "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection",
                "isActive": True
            },
        ],
        # ── Row-Level Security ────────────────────────────────────────────────
        "roles": [
            {
                "name": "LocationRLS",
                "modelPermission": "read",
                "tablePermissions": [
                    {
                        "name": "Customers",
                        "filterExpression": "[Location] = LOOKUPVALUE(Users[Location], Users[Email], LOWER(USERPRINCIPALNAME()))"
                    }
                ]
            },
            {
                "name": "London",
                "modelPermission": "read",
                "tablePermissions": [
                    {
                        "name": "Customers",
                        "filterExpression": "[Location] = \"London\""
                    }
                ]
            },
            {
                "name": "New York",
                "modelPermission": "read",
                "tablePermissions": [
                    {
                        "name": "Customers",
                        "filterExpression": "[Location] = \"New York\""
                    }
                ]
            },
            {
                "name": "Paris",
                "modelPermission": "read",
                "tablePermissions": [
                    {
                        "name": "Customers",
                        "filterExpression": "[Location] = \"Paris\""
                    }
                ]
            },
        ],
        "annotations": [
            {"name": "PBI_QueryOrder", "value": "[\"Orders\",\"Customers\",\"Products\",\"Users\",\"Returns\",\"DateTable\"]"},
            {"name": "__PBI_TimeIntelligenceEnabled", "value": "1"},
            {"name": "PBIDesktopVersion", "value": "2.136.1202.0 (24.12)"}
        ]
    }
}

# ── Content-Types for PBIT ────────────────────────────────────────────────────
CONTENT_TYPES_PBIT = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/DataModelSchema" ContentType="application/octet-stream"/>
  <Override PartName="/DiagramLayout" ContentType="application/json"/>
  <Override PartName="/Report/Layout" ContentType="application/json"/>
  <Override PartName="/Settings" ContentType="application/json"/>
  <Override PartName="/Metadata" ContentType="application/json"/>
  <Override PartName="/Version" ContentType="application/octet-stream"/>
  <Override PartName="/SecurityBindings" ContentType="application/octet-stream"/>
</Types>"""

tmsl_str  = json.dumps(TMSL, ensure_ascii=False, separators=(",", ":"))
tmsl_bytes = tmsl_str.encode("utf-16-le")  # UTF-16 LE, no BOM

# ── Write PBIT ────────────────────────────────────────────────────────────────
with zipfile.ZipFile(DST_PBIT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("Version",            raw["Version"])
    zout.writestr("[Content_Types].xml", CONTENT_TYPES_PBIT.encode("utf-8"))
    zout.writestr("DataModelSchema",    tmsl_bytes)
    zout.writestr("DiagramLayout",      json.dumps(STAR_LAYOUT, separators=(",",":")).encode("utf-16-le"))
    zout.writestr("Report/Layout",      layout_bytes)
    zout.writestr("Settings",           raw["Settings"])
    zout.writestr("Metadata",           raw["Metadata"])
    zout.writestr("SecurityBindings",   raw["SecurityBindings"])
    # Include base theme
    theme_key = "Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
    if theme_key in raw:
        zout.writestr(theme_key, raw[theme_key])

print(f"PBIT written: {DST_PBIT} ({os.path.getsize(DST_PBIT):,} bytes)")

# ── Verify ────────────────────────────────────────────────────────────────────
print("\n=== PBIX members ===")
with zipfile.ZipFile(DST_PBIX) as z:
    for i in z.infolist():
        print(f"  {i.filename}: compress={i.compress_type}, size={i.file_size:,}")

print("\n=== PBIT members ===")
with zipfile.ZipFile(DST_PBIT) as z:
    for i in z.infolist():
        print(f"  {i.filename}: compress={i.compress_type}, size={i.file_size:,}")

print("\nRelationships in TMSL:")
for r in TMSL["model"]["relationships"]:
    print(f"  {r['fromTable']}[{r['fromColumn']}] → {r['toTable']}[{r['toColumn']}]  ({r['fromCardinality']}:{r['toCardinality']})")

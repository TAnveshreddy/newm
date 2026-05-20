#!/usr/bin/env python3
"""
Build SalesAnalytics_Dashboard.pbit with:
- Correct column names matching the actual Excel file
- M queries that join sheets to derive Sub-Category, Region, City, Segment for Orders
- Returns table derived from Sales[Is Returned = 1]
- 5 relationships (star schema)
- RLS roles (city-based, matching Users[Location] = Customers[City])
"""
import zipfile, json, os

SRC      = "/root/.claude/uploads/bca2e082-c5c3-477b-a9e1-cb5c255f50cf/2fe318b8-SalesAnalytics_Dashboard_4.pbix"
DST_PBIX = "/home/user/newm/SalesAnalytics_Dashboard_v2.pbix"
DST_PBIT = "/home/user/newm/SalesAnalytics_Dashboard.pbit"
EP       = "ExcelFilePath"  # parameter name shorthand

with zipfile.ZipFile(SRC) as z:
    raw = {m: z.read(m) for m in z.namelist()}

# ── Star-schema DiagramLayout ────────────────────────────────────────────────
STAR_LAYOUT = {
    "version": "1.1.0",
    "diagrams": [{
        "ordinal": 0,
        "scrollPosition": {"x": 0, "y": 0},
        "zoomValue": 70,
        "nodes": [
            {"nodeIndex": "Orders",      "nodeLineageTag": "3d220f15-fcd7-4892-b853-cd66b8d38f4e",
             "location": {"x": 460, "y": 300}, "size": {"width": 250, "height": 380}, "zIndex": 2},
            {"nodeIndex": "Customers",   "nodeLineageTag": "1538a4d8-a39e-49d1-8d4e-f2b9af2f1bda",
             "location": {"x": 80,  "y": 60},  "size": {"width": 230, "height": 220}, "zIndex": 1},
            {"nodeIndex": "Products",    "nodeLineageTag": "ca3f3930-5ca3-4365-8a7c-b8987b332a58",
             "location": {"x": 860, "y": 60},  "size": {"width": 230, "height": 220}, "zIndex": 1},
            {"nodeIndex": "Users",       "nodeLineageTag": "452791df-4c5a-44b0-b59f-42c1b362f9a9",
             "location": {"x": 80,  "y": 560}, "size": {"width": 230, "height": 200}, "zIndex": 1},
            {"nodeIndex": "Returns",     "nodeLineageTag": "07d5e658-5a32-4bd3-a214-b3e9e65831aa",
             "location": {"x": 860, "y": 560}, "size": {"width": 230, "height": 140}, "zIndex": 1},
            {"nodeIndex": "DateTable",   "nodeLineageTag": "date-table-001",
             "location": {"x": 460, "y": 30},  "size": {"width": 230, "height": 260}, "zIndex": 1},
        ]
    }]
}

raw["DiagramLayout"] = json.dumps(STAR_LAYOUT, separators=(",", ":")).encode("utf-16-le")

# Write updated PBIX (DiagramLayout only change)
with zipfile.ZipFile(DST_PBIX, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for name, data in raw.items():
        if name == "DataModel":
            zout.writestr(zipfile.ZipInfo(name), data, compress_type=zipfile.ZIP_STORED)
        else:
            zout.writestr(name, data)
print(f"PBIX written: {DST_PBIX} ({os.path.getsize(DST_PBIX):,} bytes)")

# ── M query helpers ──────────────────────────────────────────────────────────
def mlines(*lines):
    """Return list of M query lines (each a string)."""
    return list(lines)

# ── TMSL DataModelSchema ─────────────────────────────────────────────────────
TMSL = {
    "name": "SalesAnalytics",
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-US",
        "collation": "Latin1_General_100_BIN2_UTF8",
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-US",

        # ── Parameter ────────────────────────────────────────────────────────
        "expressions": [{
            "name": EP,
            "description": "Full path to PowerBI_Data_Model.xlsx",
            "kind": "m",
            "expression": '"C:\\\\Users\\\\anvesh.t\\\\Downloads\\\\PowerBI_Data_Model.xlsx" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
            "annotations": [{"name": "PBI_NavigationStepName", "value": "Navigation"}]
        }],

        "tables": [

            # ── Orders (fact) ────────────────────────────────────────────────
            # Sources: Sales sheet + join Customers (City/Country→Region/Segment)
            #          + join Products (Sub Category → Sub-Category)
            # Renames: Net Sales→Sales, Sales Channel→Channel,
            #          Order Status→Status, Discount Pct→Discount
            {
                "name": "Orders",
                "lineageTag": "3d220f15-fcd7-4892-b853-cd66b8d38f4e",
                "columns": [
                    {"name": "Order ID",     "dataType": "string",   "sourceColumn": "Order ID",     "lineageTag": "col-o-01"},
                    {"name": "Customer ID",  "dataType": "string",   "sourceColumn": "Customer ID",  "lineageTag": "col-o-02"},
                    {"name": "Product ID",   "dataType": "string",   "sourceColumn": "Product ID",   "lineageTag": "col-o-03"},
                    {"name": "User ID",      "dataType": "string",   "sourceColumn": "User ID",      "lineageTag": "col-o-04"},
                    {"name": "Order Date",   "dataType": "dateTime", "sourceColumn": "Order Date",   "lineageTag": "col-o-05",
                     "formatString": "Short Date",
                     "annotations": [{"name": "UnderlyingDateTimeDataType", "value": "Date"}]},
                    {"name": "Category",     "dataType": "string",   "sourceColumn": "Category",     "lineageTag": "col-o-06"},
                    {"name": "Sub-Category", "dataType": "string",   "sourceColumn": "Sub-Category", "lineageTag": "col-o-07"},
                    {"name": "City",         "dataType": "string",   "sourceColumn": "City",         "lineageTag": "col-o-08"},
                    {"name": "Region",       "dataType": "string",   "sourceColumn": "Region",       "lineageTag": "col-o-09"},
                    {"name": "Segment",      "dataType": "string",   "sourceColumn": "Segment",      "lineageTag": "col-o-10"},
                    {"name": "Sales",        "dataType": "double",   "sourceColumn": "Sales",        "lineageTag": "col-o-11", "formatString": "#,0.00"},
                    {"name": "Profit",       "dataType": "double",   "sourceColumn": "Profit",       "lineageTag": "col-o-12", "formatString": "#,0.00"},
                    {"name": "Quantity",     "dataType": "int64",    "sourceColumn": "Quantity",     "lineageTag": "col-o-13"},
                    {"name": "Discount",     "dataType": "double",   "sourceColumn": "Discount",     "lineageTag": "col-o-14", "formatString": "0.0%"},
                    {"name": "Channel",      "dataType": "string",   "sourceColumn": "Channel",      "lineageTag": "col-o-15"},
                    {"name": "Status",       "dataType": "string",   "sourceColumn": "Status",       "lineageTag": "col-o-16"},
                ],
                "measures": [
                    {"name": "Total Revenue",   "lineageTag": "m-01",
                     "expression": "SUM(Orders[Sales])",
                     "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00"},
                    {"name": "Total Profit",    "lineageTag": "m-02",
                     "expression": "SUM(Orders[Profit])",
                     "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00"},
                    {"name": "Total Orders",    "lineageTag": "m-03",
                     "expression": "COUNTROWS(Orders)",
                     "formatString": "#,0"},
                    {"name": "Profit Margin %", "lineageTag": "m-04",
                     "expression": "DIVIDE(SUM(Orders[Profit]), SUM(Orders[Sales]), 0)",
                     "formatString": "0.0%"},
                    {"name": "Avg Order Value", "lineageTag": "m-05",
                     "expression": "DIVIDE(SUM(Orders[Sales]), COUNTROWS(Orders), 0)",
                     "formatString": "\\$#,0.00"},
                    {"name": "Total Quantity",  "lineageTag": "m-06",
                     "expression": "SUM(Orders[Quantity])",
                     "formatString": "#,0"},
                    {"name": "Revenue YTD",     "lineageTag": "m-07",
                     "expression": "TOTALYTD(SUM(Orders[Sales]), Orders[Order Date])",
                     "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00"},
                    {"name": "Revenue PY",      "lineageTag": "m-08",
                     "expression": "CALCULATE(SUM(Orders[Sales]), SAMEPERIODLASTYEAR(Orders[Order Date]))",
                     "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00"},
                    {"name": "YoY Growth %",    "lineageTag": "m-09",
                     "expression": "DIVIDE([Revenue YTD] - [Revenue PY], [Revenue PY], 0)",
                     "formatString": "0.0%"},
                    {"name": "Return Rate %",   "lineageTag": "m-10",
                     "expression": "DIVIDE(COUNTROWS(Returns), COUNTROWS(Orders), 0)",
                     "formatString": "0.0%"},
                    {"name": "Revenue MTD",     "lineageTag": "m-11",
                     "expression": "TOTALMTD(SUM(Orders[Sales]), Orders[Order Date])",
                     "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00"},
                    {"name": "Revenue QTD",     "lineageTag": "m-12",
                     "expression": "TOTALQTD(SUM(Orders[Sales]), Orders[Order Date])",
                     "formatString": "\\$#,0.00;(\\$#,0.00);\\$#,0.00"},
                ],
                "partitions": [{
                    "name": "Orders",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": mlines(
                            "let",
                            f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
                            "    // Load Sales sheet",
                            '    SalesRaw  = Source{[Item="Sales",Kind="Sheet"]}[Data],',
                            "    Sales     = Table.PromoteHeaders(SalesRaw,  [PromoteAllScalars=true]),",
                            "    // Load Customers sheet (for City, Country→Region, Segment)",
                            '    CustRaw   = Source{[Item="Customers",Kind="Sheet"]}[Data],',
                            "    Cust      = Table.PromoteHeaders(CustRaw,   [PromoteAllScalars=true]),",
                            '    CustCols  = Table.SelectColumns(Cust, {"Customer ID","City","Country","Segment"}),',
                            "    // Load Products sheet (for Sub Category)",
                            '    ProdRaw   = Source{[Item="Products",Kind="Sheet"]}[Data],',
                            "    Prod      = Table.PromoteHeaders(ProdRaw,   [PromoteAllScalars=true]),",
                            '    ProdCols  = Table.SelectColumns(Prod, {"Product ID","Sub Category"}),',
                            "    // Join Sales ← Customers",
                            '    J1 = Table.NestedJoin(Sales, {"Customer ID"}, CustCols, {"Customer ID"}, "_c", JoinKind.LeftOuter),',
                            '    E1 = Table.ExpandTableColumn(J1, "_c", {"City","Country","Segment"}, {"City","Region","Segment"}),',
                            "    // Join Sales ← Products",
                            '    J2 = Table.NestedJoin(E1, {"Product ID"}, ProdCols, {"Product ID"}, "_p", JoinKind.LeftOuter),',
                            '    E2 = Table.ExpandTableColumn(J2, "_p", {"Sub Category"}, {"Sub-Category"}),',
                            "    // Rename to match model column names",
                            "    Renamed = Table.RenameColumns(E2, {",
                            '        {"Net Sales",    "Sales"},',
                            '        {"Sales Channel","Channel"},',
                            '        {"Order Status", "Status"},',
                            '        {"Discount Pct", "Discount"}',
                            "    }),",
                            "    // Keep only needed columns",
                            "    Selected = Table.SelectColumns(Renamed, {",
                            '        "Order ID","Customer ID","Product ID","User ID","Order Date",',
                            '        "Category","Sub-Category","City","Region","Segment",',
                            '        "Sales","Profit","Quantity","Discount","Channel","Status"',
                            "    }),",
                            "    Typed = Table.TransformColumnTypes(Selected, {",
                            '        {"Order ID", type text},    {"Customer ID", type text},',
                            '        {"Product ID", type text},  {"User ID", type text},',
                            '        {"Order Date", type date},  {"Category", type text},',
                            '        {"Sub-Category", type text},{"City", type text},',
                            '        {"Region", type text},      {"Segment", type text},',
                            '        {"Sales", type number},     {"Profit", type number},',
                            '        {"Quantity", Int64.Type},   {"Discount", type number},',
                            '        {"Channel", type text},     {"Status", type text}',
                            "    })",
                            "in",
                            "    Typed"
                        )
                    }
                }],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },

            # ── Customers ────────────────────────────────────────────────────
            # Full Name → Customer Name
            # City     → Location  (matches Users[Location] for RLS)
            # Country  → Country
            # Registration Date → Join Date
            {
                "name": "Customers",
                "lineageTag": "1538a4d8-a39e-49d1-8d4e-f2b9af2f1bda",
                "columns": [
                    {"name": "Customer ID",   "dataType": "string",   "sourceColumn": "Customer ID",   "lineageTag": "col-c-01"},
                    {"name": "Customer Name", "dataType": "string",   "sourceColumn": "Customer Name", "lineageTag": "col-c-02"},
                    {"name": "Email",         "dataType": "string",   "sourceColumn": "Email",         "lineageTag": "col-c-03"},
                    {"name": "City",          "dataType": "string",   "sourceColumn": "City",          "lineageTag": "col-c-04"},
                    {"name": "Country",       "dataType": "string",   "sourceColumn": "Country",       "lineageTag": "col-c-05"},
                    {"name": "Segment",       "dataType": "string",   "sourceColumn": "Segment",       "lineageTag": "col-c-06"},
                    {"name": "Join Date",     "dataType": "dateTime", "sourceColumn": "Join Date",     "lineageTag": "col-c-07",
                     "formatString": "Short Date"},
                    {"name": "Credit Limit",  "dataType": "double",   "sourceColumn": "Credit Limit",  "lineageTag": "col-c-08",
                     "formatString": "#,0.00"},
                ],
                "partitions": [{
                    "name": "Customers",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": mlines(
                            "let",
                            f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
                            '    Sheet    = Source{[Item="Customers",Kind="Sheet"]}[Data],',
                            "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                            "    Renamed  = Table.RenameColumns(Promoted, {",
                            '        {"Full Name",         "Customer Name"},',
                            '        {"Registration Date", "Join Date"}',
                            "    }),",
                            "    Selected = Table.SelectColumns(Renamed, {",
                            '        "Customer ID","Customer Name","Email",',
                            '        "City","Country","Segment","Join Date","Credit Limit"',
                            "    }),",
                            "    Typed = Table.TransformColumnTypes(Selected, {",
                            '        {"Customer ID", type text},   {"Customer Name", type text},',
                            '        {"Email", type text},         {"City", type text},',
                            '        {"Country", type text},       {"Segment", type text},',
                            '        {"Join Date", type date},     {"Credit Limit", type number}',
                            "    })",
                            "in",
                            "    Typed"
                        )
                    }
                }],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },

            # ── Products ─────────────────────────────────────────────────────
            # Sub Category → Sub-Category (hyphen added to match report)
            # Unit Cost    → Cost
            {
                "name": "Products",
                "lineageTag": "ca3f3930-5ca3-4365-8a7c-b8987b332a58",
                "columns": [
                    {"name": "Product ID",   "dataType": "string", "sourceColumn": "Product ID",   "lineageTag": "col-p-01"},
                    {"name": "Product Name", "dataType": "string", "sourceColumn": "Product Name", "lineageTag": "col-p-02"},
                    {"name": "Category",     "dataType": "string", "sourceColumn": "Category",     "lineageTag": "col-p-03"},
                    {"name": "Sub-Category", "dataType": "string", "sourceColumn": "Sub-Category", "lineageTag": "col-p-04"},
                    {"name": "Unit Price",   "dataType": "double", "sourceColumn": "Unit Price",   "lineageTag": "col-p-05", "formatString": "#,0.00"},
                    {"name": "Cost",         "dataType": "double", "sourceColumn": "Cost",         "lineageTag": "col-p-06", "formatString": "#,0.00"},
                    {"name": "Brand",        "dataType": "string", "sourceColumn": "Brand",        "lineageTag": "col-p-07"},
                    {"name": "Stock Status", "dataType": "string", "sourceColumn": "Stock Status", "lineageTag": "col-p-08"},
                    {"name": "Price Range",  "dataType": "string", "sourceColumn": "Price Range",  "lineageTag": "col-p-09"},
                ],
                "partitions": [{
                    "name": "Products",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": mlines(
                            "let",
                            f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
                            '    Sheet    = Source{[Item="Products",Kind="Sheet"]}[Data],',
                            "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                            "    Renamed  = Table.RenameColumns(Promoted, {",
                            '        {"Sub Category", "Sub-Category"},',
                            '        {"Unit Cost",    "Cost"}',
                            "    }),",
                            "    Selected = Table.SelectColumns(Renamed, {",
                            '        "Product ID","Product Name","Category","Sub-Category",',
                            '        "Unit Price","Cost","Brand","Stock Status","Price Range"',
                            "    }),",
                            "    Typed = Table.TransformColumnTypes(Selected, {",
                            '        {"Product ID", type text},   {"Product Name", type text},',
                            '        {"Category", type text},     {"Sub-Category", type text},',
                            '        {"Unit Price", type number}, {"Cost", type number},',
                            '        {"Brand", type text},        {"Stock Status", type text},',
                            '        {"Price Range", type text}',
                            "    })",
                            "in",
                            "    Typed"
                        )
                    }
                }],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },

            # ── Users ────────────────────────────────────────────────────────
            # Name → Username
            # Country → Region
            # Login Email kept for RLS USERPRINCIPALNAME() matching
            {
                "name": "Users",
                "lineageTag": "452791df-4c5a-44b0-b59f-42c1b362f9a9",
                "columns": [
                    {"name": "User ID",     "dataType": "string",   "sourceColumn": "User ID",     "lineageTag": "col-u-01"},
                    {"name": "Username",    "dataType": "string",   "sourceColumn": "Username",    "lineageTag": "col-u-02"},
                    {"name": "Email",       "dataType": "string",   "sourceColumn": "Email",       "lineageTag": "col-u-03"},
                    {"name": "Login Email", "dataType": "string",   "sourceColumn": "Login Email", "lineageTag": "col-u-04"},
                    {"name": "Role",        "dataType": "string",   "sourceColumn": "Role",        "lineageTag": "col-u-05"},
                    {"name": "Department",  "dataType": "string",   "sourceColumn": "Department",  "lineageTag": "col-u-06"},
                    {"name": "Location",    "dataType": "string",   "sourceColumn": "Location",    "lineageTag": "col-u-07"},
                    {"name": "Region",      "dataType": "string",   "sourceColumn": "Region",      "lineageTag": "col-u-08"},
                    {"name": "Sales Target","dataType": "double",   "sourceColumn": "Sales Target","lineageTag": "col-u-09",
                     "formatString": "#,0.00"},
                ],
                "partitions": [{
                    "name": "Users",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": mlines(
                            "let",
                            f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
                            '    Sheet    = Source{[Item="Users",Kind="Sheet"]}[Data],',
                            "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                            "    Renamed  = Table.RenameColumns(Promoted, {",
                            '        {"Name",    "Username"},',
                            '        {"Country", "Region"}',
                            "    }),",
                            "    Selected = Table.SelectColumns(Renamed, {",
                            '        "User ID","Username","Email","Login Email",',
                            '        "Role","Department","Location","Region","Sales Target"',
                            "    }),",
                            "    Typed = Table.TransformColumnTypes(Selected, {",
                            '        {"User ID", type text},      {"Username", type text},',
                            '        {"Email", type text},        {"Login Email", type text},',
                            '        {"Role", type text},         {"Department", type text},',
                            '        {"Location", type text},     {"Region", type text},',
                            '        {"Sales Target", type number}',
                            "    })",
                            "in",
                            "    Typed"
                        )
                    }
                }],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },

            # ── Returns ──────────────────────────────────────────────────────
            # Derived from Sales sheet where Is Returned = 1
            # Region comes from joining Customers[Country]
            {
                "name": "Returns",
                "lineageTag": "07d5e658-5a32-4bd3-a214-b3e9e65831aa",
                "columns": [
                    {"name": "Order ID", "dataType": "string", "sourceColumn": "Order ID", "lineageTag": "col-r-01"},
                    {"name": "Region",   "dataType": "string", "sourceColumn": "Region",   "lineageTag": "col-r-02"},
                ],
                "partitions": [{
                    "name": "Returns",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": mlines(
                            "let",
                            f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
                            "    // Load Sales and filter returned orders",
                            '    SalesRaw  = Source{[Item="Sales",Kind="Sheet"]}[Data],',
                            "    Sales     = Table.PromoteHeaders(SalesRaw, [PromoteAllScalars=true]),",
                            "    Returned  = Table.SelectRows(Sales, each [Is Returned] = 1),",
                            "    // Load Customers to get Country as Region",
                            '    CustRaw   = Source{[Item="Customers",Kind="Sheet"]}[Data],',
                            "    Cust      = Table.PromoteHeaders(CustRaw, [PromoteAllScalars=true]),",
                            '    CustCols  = Table.SelectColumns(Cust, {"Customer ID","Country"}),',
                            "    // Join to get Region",
                            '    Joined    = Table.NestedJoin(Returned, {"Customer ID"}, CustCols, {"Customer ID"}, "_c", JoinKind.LeftOuter),',
                            '    Expanded  = Table.ExpandTableColumn(Joined, "_c", {"Country"}, {"Region"}),',
                            '    Selected  = Table.SelectColumns(Expanded, {"Order ID","Region"}),',
                            "    Typed     = Table.TransformColumnTypes(Selected, {",
                            '        {"Order ID", type text}, {"Region", type text}',
                            "    })",
                            "in",
                            "    Typed"
                        )
                    }
                }],
                "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
            },

            # ── DateTable ────────────────────────────────────────────────────
            # Actual columns: Date, Year, Month, Day, Quarter, Quarter Num,
            #   Week Num, Month Name, Month Short, Day Name, Year-Month,
            #   Year-Qtr, Is Weekend, Fiscal Year
            {
                "name": "DateTable",
                "lineageTag": "date-table-001",
                "columns": [
                    {"name": "Date",        "dataType": "dateTime", "sourceColumn": "Date",        "lineageTag": "col-d-01",
                     "formatString": "Short Date", "isKey": True,
                     "annotations": [{"name": "UnderlyingDateTimeDataType", "value": "Date"}]},
                    {"name": "Year",        "dataType": "int64",    "sourceColumn": "Year",        "lineageTag": "col-d-02"},
                    {"name": "Month",       "dataType": "int64",    "sourceColumn": "Month",       "lineageTag": "col-d-03"},
                    {"name": "Day",         "dataType": "int64",    "sourceColumn": "Day",         "lineageTag": "col-d-04"},
                    {"name": "Quarter",     "dataType": "string",   "sourceColumn": "Quarter",     "lineageTag": "col-d-05"},
                    {"name": "Quarter Num", "dataType": "int64",    "sourceColumn": "Quarter Num", "lineageTag": "col-d-06"},
                    {"name": "Week Num",    "dataType": "int64",    "sourceColumn": "Week Num",    "lineageTag": "col-d-07"},
                    {"name": "Month Name",  "dataType": "string",   "sourceColumn": "Month Name",  "lineageTag": "col-d-08"},
                    {"name": "Month Short", "dataType": "string",   "sourceColumn": "Month Short", "lineageTag": "col-d-09"},
                    {"name": "Day Name",    "dataType": "string",   "sourceColumn": "Day Name",    "lineageTag": "col-d-10"},
                    {"name": "Year-Month",  "dataType": "string",   "sourceColumn": "Year-Month",  "lineageTag": "col-d-11"},
                    {"name": "Year-Qtr",    "dataType": "string",   "sourceColumn": "Year-Qtr",    "lineageTag": "col-d-12"},
                    {"name": "Is Weekend",  "dataType": "int64",    "sourceColumn": "Is Weekend",  "lineageTag": "col-d-13"},
                    {"name": "Fiscal Year", "dataType": "string",   "sourceColumn": "Fiscal Year", "lineageTag": "col-d-14"},
                ],
                "partitions": [{
                    "name": "DateTable",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": mlines(
                            "let",
                            f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
                            '    Sheet    = Source{[Item="DateTable",Kind="Sheet"]}[Data],',
                            "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
                            "    Typed = Table.TransformColumnTypes(Promoted, {",
                            '        {"Date", type date},        {"Year", Int64.Type},',
                            '        {"Month", Int64.Type},      {"Day", Int64.Type},',
                            '        {"Quarter", type text},     {"Quarter Num", Int64.Type},',
                            '        {"Week Num", Int64.Type},   {"Month Name", type text},',
                            '        {"Month Short", type text}, {"Day Name", type text},',
                            '        {"Year-Month", type text},  {"Year-Qtr", type text},',
                            '        {"Is Weekend", Int64.Type}, {"Fiscal Year", type text}',
                            "    })",
                            "in",
                            "    Typed"
                        )
                    }
                }],
                "annotations": [
                    {"name": "PBI_ResultType",  "value": "Table"},
                    {"name": "PBI_IsDateTable", "value": "true"}
                ]
            },
        ],

        # ── Relationships ─────────────────────────────────────────────────────
        "relationships": [
            {
                "name": "Orders_Customers",
                "fromTable": "Orders", "fromColumn": "Customer ID",
                "toTable": "Customers", "toColumn": "Customer ID",
                "fromCardinality": "many", "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection", "isActive": True
            },
            {
                "name": "Orders_Products",
                "fromTable": "Orders", "fromColumn": "Product ID",
                "toTable": "Products", "toColumn": "Product ID",
                "fromCardinality": "many", "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection", "isActive": True
            },
            {
                "name": "Orders_Users",
                "fromTable": "Orders", "fromColumn": "User ID",
                "toTable": "Users", "toColumn": "User ID",
                "fromCardinality": "many", "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection", "isActive": True
            },
            {
                "name": "Returns_Orders",
                "fromTable": "Returns", "fromColumn": "Order ID",
                "toTable": "Orders", "toColumn": "Order ID",
                "fromCardinality": "many", "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection", "isActive": True
            },
            {
                "name": "Orders_DateTable",
                "fromTable": "Orders", "fromColumn": "Order Date",
                "toTable": "DateTable", "toColumn": "Date",
                "fromCardinality": "many", "toCardinality": "one",
                "crossFilteringBehavior": "oneDirection", "isActive": True
            },
        ],

        # ── Row-Level Security ────────────────────────────────────────────────
        # Users[Location] = city names (Hamburg, Lyon, Vancouver …)
        # Customers[City] = same city names
        # Orders is filtered via Orders→Customers relationship
        "roles": [
            {
                "name": "Dynamic Location RLS",
                "modelPermission": "read",
                "tablePermissions": [{
                    "name": "Customers",
                    "filterExpression": '[City] = LOOKUPVALUE(Users[Location], Users[Login Email], LOWER(USERPRINCIPALNAME()))'
                }]
            },
            {
                "name": "Hamburg",
                "modelPermission": "read",
                "tablePermissions": [{"name": "Customers", "filterExpression": '[City] = "Hamburg"'}]
            },
            {
                "name": "London",
                "modelPermission": "read",
                "tablePermissions": [{"name": "Customers", "filterExpression": '[City] = "London"'}]
            },
            {
                "name": "Lyon",
                "modelPermission": "read",
                "tablePermissions": [{"name": "Customers", "filterExpression": '[City] = "Lyon"'}]
            },
            {
                "name": "Vancouver",
                "modelPermission": "read",
                "tablePermissions": [{"name": "Customers", "filterExpression": '[City] = "Vancouver"'}]
            },
        ],

        "annotations": [
            {"name": "PBI_QueryOrder",
             "value": '["Orders","Customers","Products","Users","Returns","DateTable"]'},
            {"name": "__PBI_TimeIntelligenceEnabled", "value": "1"},
            {"name": "PBIDesktopVersion",             "value": "2.136.1202.0 (24.12)"}
        ]
    }
}

# ── Content-Types for PBIT ───────────────────────────────────────────────────
CT_PBIT = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="png"  ContentType="image/png"/>
  <Override PartName="/DataModelSchema"  ContentType="application/octet-stream"/>
  <Override PartName="/DiagramLayout"    ContentType="application/json"/>
  <Override PartName="/Report/Layout"    ContentType="application/json"/>
  <Override PartName="/Settings"         ContentType="application/json"/>
  <Override PartName="/Metadata"         ContentType="application/json"/>
  <Override PartName="/Version"          ContentType="application/octet-stream"/>
  <Override PartName="/SecurityBindings" ContentType="application/octet-stream"/>
</Types>"""

tmsl_bytes = json.dumps(TMSL, ensure_ascii=False, separators=(",", ":")).encode("utf-16-le")

layout_bytes = raw["Report/Layout"]

with zipfile.ZipFile(DST_PBIT, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("Version",            raw["Version"])
    zout.writestr("[Content_Types].xml", CT_PBIT.strip().encode("utf-8"))
    zout.writestr("DataModelSchema",    tmsl_bytes)
    zout.writestr("DiagramLayout",      json.dumps(STAR_LAYOUT, separators=(",",":")).encode("utf-16-le"))
    zout.writestr("Report/Layout",      layout_bytes)
    zout.writestr("Settings",           raw["Settings"])
    zout.writestr("Metadata",           raw["Metadata"])
    zout.writestr("SecurityBindings",   raw["SecurityBindings"])
    theme = "Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
    if theme in raw:
        zout.writestr(theme, raw[theme])

print(f"PBIT written: {DST_PBIT} ({os.path.getsize(DST_PBIT):,} bytes)")

print("\nColumn fixes applied:")
print("  Orders   : Net Sales→Sales, Sales Channel→Channel, Order Status→Status,")
print("             Discount Pct→Discount, City+Region+Segment joined from Customers,")
print("             Sub-Category joined from Products")
print("  Customers: Full Name→Customer Name, Registration Date→Join Date")
print("  Products : Sub Category→Sub-Category (hyphen), Unit Cost→Cost")
print("  Users    : Name→Username, Country→Region")
print("  Returns  : derived from Sales[Is Returned=1], Region from Customers[Country]")
print("  DateTable: all 14 columns mapped (Quarter Num, Week Num, Year-Month, etc.)")

print("\nRelationships:")
for r in TMSL["model"]["relationships"]:
    print(f"  {r['fromTable']}[{r['fromColumn']}] → {r['toTable']}[{r['toColumn']}]")

print("\nRLS roles:", [r["name"] for r in TMSL["model"]["roles"]])

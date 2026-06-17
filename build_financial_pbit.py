#!/usr/bin/env python3
"""
Build Financial_Dashboard.pbit
Strategy: use Report/Layout from the working SalesAnalytics PBIX (guarantees
Power BI Desktop compatibility), replace only DataModelSchema with Financial data.
"""
import zipfile, json, os

# Working source — provides valid Layout, Version, Settings, Metadata, theme
SRC  = "/root/.claude/uploads/bca2e082-c5c3-477b-a9e1-cb5c255f50cf/2fe318b8-SalesAnalytics_Dashboard_4.pbix"
DST  = "/home/user/newm/Financial_Dashboard.pbit"
EP   = "ExcelFilePath"

with zipfile.ZipFile(SRC) as z:
    raw = {m: z.read(m) for m in z.namelist()}

# ── DiagramLayout ─────────────────────────────────────────────────────────────
DIAGRAM = {
  "version": "1.1.0",
  "diagrams": [{
    "ordinal": 0, "scrollPosition": {"x":0,"y":0}, "zoomValue": 75,
    "nodes": [
      {"nodeIndex":"KPIs",                  "nodeLineageTag":"kpi-table-001",
       "location":{"x":60, "y":60},  "size":{"width":230,"height":260},"zIndex":1},
      {"nodeIndex":"AgingAnalysis",         "nodeLineageTag":"aging-table-001",
       "location":{"x":360,"y":60},  "size":{"width":230,"height":150},"zIndex":1},
      {"nodeIndex":"CollectionPerformance", "nodeLineageTag":"col-table-001",
       "location":{"x":660,"y":60},  "size":{"width":230,"height":200},"zIndex":1},
    ]
  }]
}

# ── TMSL DataModelSchema (compatibilityLevel 1500 = works with all PBI versions) ──
TMSL = {
  "name": "FinancialDashboard",
  "compatibilityLevel": 1500,
  "model": {
    "culture": "en-US",
    "defaultPowerBIDataSourceVersion": "powerBI_V3",

    "expressions": [{
      "name": EP,
      "description": "Full path to Financial_Dashboard_Data_2.xlsx",
      "kind": "m",
      "expression": '"C:\\\\Users\\\\anvesh.t\\\\Downloads\\\\Financial_Dashboard_Data_2.xlsx" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
      "annotations": [{"name":"PBI_NavigationStepName","value":"Navigation"}]
    }],

    "tables": [

      # ── KPIs (from Thumbnail sheet) ────────────────────────────────────────
      {
        "name": "KPIs",
        "lineageTag": "kpi-table-001",
        "columns": [
          {"name":"KPI Name", "dataType":"string","sourceColumn":"KPI Name","lineageTag":"kpi-c-01"},
          {"name":"Value",    "dataType":"double","sourceColumn":"Value",   "lineageTag":"kpi-c-02","formatString":"#,0.00"},
          {"name":"UoM",      "dataType":"string","sourceColumn":"UoM",    "lineageTag":"kpi-c-03"},
          {"name":"Min",      "dataType":"double","sourceColumn":"Min",    "lineageTag":"kpi-c-04"},
          {"name":"Max",      "dataType":"double","sourceColumn":"Max",    "lineageTag":"kpi-c-05"},
          {"name":"Accepted", "dataType":"double","sourceColumn":"Accepted","lineageTag":"kpi-c-06"},
          {"name":"Comments", "dataType":"string","sourceColumn":"Comments","lineageTag":"kpi-c-07"},
          {
            "name":"Status","dataType":"string","lineageTag":"kpi-c-08","type":"calculated",
            "expression": (
              'VAR v = KPIs[Value] VAR a = KPIs[Accepted] '
              'VAR hib = NOT (KPIs[KPI Name] IN {"Lost Shipment Rate","Revenue Leakage","Delivery Exceptions"}) '
              'RETURN IF(hib, IF(v>=a,"On Track",IF(v>=a*0.9,"Watch","Off Track")), '
              'IF(v<=a,"On Track",IF(v<=a*1.5,"Watch","Off Track")))'
            )
          },
          {
            "name":"Status Icon","dataType":"string","lineageTag":"kpi-c-09","type":"calculated",
            "expression":'IF(KPIs[Status]="On Track","✓ On Track",IF(KPIs[Status]="Watch","⚠ Watch","✕ Off Track"))'
          },
          {
            "name":"vs Target %","dataType":"double","lineageTag":"kpi-c-10",
            "type":"calculated","formatString":"0.0%",
            "expression":"DIVIDE(KPIs[Value]-KPIs[Accepted],KPIs[Accepted],0)"
          },
          {
            "name":"Progress %","dataType":"double","lineageTag":"kpi-c-11",
            "type":"calculated","formatString":"0.0%",
            "expression":"DIVIDE(KPIs[Value]-KPIs[Min],KPIs[Max]-KPIs[Min],0)"
          },
          {
            "name":"Formatted Value","dataType":"string","lineageTag":"kpi-c-12","type":"calculated",
            "expression":'IF(KPIs[UoM]="$","$"&TEXT(KPIs[Value],"#,0.0"),TEXT(KPIs[Value],"#,0.0")&KPIs[UoM])'
          },
        ],
        "measures": [
          {"name":"# KPIs On Track",  "lineageTag":"kpi-m-01","formatString":"#,0",
           "expression":'COUNTROWS(FILTER(KPIs,KPIs[Status]="On Track"))'},
          {"name":"# KPIs Watch",     "lineageTag":"kpi-m-02","formatString":"#,0",
           "expression":'COUNTROWS(FILTER(KPIs,KPIs[Status]="Watch"))'},
          {"name":"# KPIs Off Track", "lineageTag":"kpi-m-03","formatString":"#,0",
           "expression":'COUNTROWS(FILTER(KPIs,KPIs[Status]="Off Track"))'},
          {"name":"Overall Health %", "lineageTag":"kpi-m-04","formatString":"0.0%",
           "expression":'DIVIDE(COUNTROWS(FILTER(KPIs,KPIs[Status]="On Track")),COUNTROWS(KPIs),0)'},
        ],
        "partitions": [{
          "name": "KPIs", "mode": "import",
          "source": {
            "type": "m",
            "expression": [
              "let",
              f"    Source   = Excel.Workbook(File.Contents({EP}), null, true),",
              '    Sheet    = Source{[Item="Thumbnail",Kind="Sheet"]}[Data],',
              "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
              "    Filtered = Table.SelectRows(Promoted, each [KPI Name] <> null),",
              '    Selected = Table.SelectColumns(Filtered,{"KPI Name","Value","UoM","Min","Max","Accepted","Comments"}),',
              "    Typed    = Table.TransformColumnTypes(Selected,{",
              '        {"KPI Name",type text},{"Value",type number},{"UoM",type text},',
              '        {"Min",type number},{"Max",type number},{"Accepted",type number},{"Comments",type text}})',
              "in Typed"
            ]
          }
        }],
        "annotations":[{"name":"PBI_ResultType","value":"Table"}]
      },

      # ── AgingAnalysis ──────────────────────────────────────────────────────
      {
        "name": "AgingAnalysis",
        "lineageTag": "aging-table-001",
        "columns": [
          {"name":"Days Bucket","dataType":"string","sourceColumn":"Days Bucket","lineageTag":"ag-c-01"},
          {"name":"Amount",     "dataType":"double","sourceColumn":"Amount",     "lineageTag":"ag-c-02","formatString":"\\$#,0"},
          {
            "name":"Bucket Order","dataType":"int64","lineageTag":"ag-c-03","type":"calculated",
            "expression":'SWITCH(AgingAnalysis[Days Bucket],"Current",1,"1-30 Days",2,"31-60 Days",3,"61-90 Days",4,5)'
          },
        ],
        "measures": [
          {"name":"Total AR Outstanding","lineageTag":"ag-m-01","formatString":"\\$#,0",
           "expression":"SUM(AgingAnalysis[Amount])"},
          {"name":"Current Amount",      "lineageTag":"ag-m-02","formatString":"\\$#,0",
           "expression":'CALCULATE(SUM(AgingAnalysis[Amount]),AgingAnalysis[Days Bucket]="Current")'},
          {"name":"Overdue Amount",      "lineageTag":"ag-m-03","formatString":"\\$#,0",
           "expression":'CALCULATE(SUM(AgingAnalysis[Amount]),AgingAnalysis[Days Bucket]<>"Current")'},
          {"name":"Current %",           "lineageTag":"ag-m-04","formatString":"0.0%",
           "expression":"DIVIDE([Current Amount],[Total AR Outstanding],0)"},
          {"name":"61-90 Days Amount",   "lineageTag":"ag-m-05","formatString":"\\$#,0",
           "expression":'CALCULATE(SUM(AgingAnalysis[Amount]),AgingAnalysis[Days Bucket]="61-90 Days")'},
        ],
        "partitions": [{
          "name": "AgingAnalysis", "mode": "import",
          "source": {
            "type": "m",
            "expression": [
              "let",
              f"    Source   = Excel.Workbook(File.Contents({EP}), null, true),",
              '    Sheet    = Source{[Item="Aging Analysis",Kind="Sheet"]}[Data],',
              "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
              "    Filtered = Table.SelectRows(Promoted, each [Days Bucket] <> null),",
              '    Renamed  = Table.RenameColumns(Filtered,{{"Amount ($)","Amount"}}),',
              '    Selected = Table.SelectColumns(Renamed,{"Days Bucket","Amount"}),',
              "    Typed    = Table.TransformColumnTypes(Selected,{",
              '        {"Days Bucket",type text},{"Amount",type number}})',
              "in Typed"
            ]
          }
        }],
        "annotations":[{"name":"PBI_ResultType","value":"Table"}]
      },

      # ── CollectionPerformance ──────────────────────────────────────────────
      {
        "name": "CollectionPerformance",
        "lineageTag": "col-table-001",
        "columns": [
          {"name":"Month",      "dataType":"string","sourceColumn":"Month",      "lineageTag":"col-c-01"},
          {"name":"Collected",  "dataType":"double","sourceColumn":"Collected",  "lineageTag":"col-c-02","formatString":"\\$#,0"},
          {"name":"Outstanding","dataType":"double","sourceColumn":"Outstanding","lineageTag":"col-c-03","formatString":"\\$#,0"},
          {
            "name":"Year","dataType":"int64","lineageTag":"col-c-04","type":"calculated",
            "expression":"2000 + VALUE(RIGHT(CollectionPerformance[Month],2))"
          },
          {
            "name":"Month Order","dataType":"int64","lineageTag":"col-c-05","type":"calculated",
            "expression":(
              'VAR mo=LEFT(CollectionPerformance[Month],3) '
              'VAR yr=VALUE(RIGHT(CollectionPerformance[Month],2)) '
              'VAR mn=SWITCH(mo,"Jan",1,"Feb",2,"Mar",3,"Apr",4,"May",5,"Jun",6,'
              '"Jul",7,"Aug",8,"Sep",9,"Oct",10,"Nov",11,"Dec",12,0) '
              'RETURN yr*100+mn'
            )
          },
          {
            "name":"Collection Rate %","dataType":"double","lineageTag":"col-c-06",
            "type":"calculated","formatString":"0.0%",
            "expression":"DIVIDE(CollectionPerformance[Collected],CollectionPerformance[Collected]+CollectionPerformance[Outstanding],0)"
          },
        ],
        "measures": [
          {"name":"Total Collected",    "lineageTag":"col-m-01","formatString":"\\$#,0",
           "expression":"SUM(CollectionPerformance[Collected])"},
          {"name":"Total Outstanding",  "lineageTag":"col-m-02","formatString":"\\$#,0",
           "expression":"SUM(CollectionPerformance[Outstanding])"},
          {"name":"Avg Collection Rate","lineageTag":"col-m-03","formatString":"0.0%",
           "expression":"AVERAGEX(CollectionPerformance,CollectionPerformance[Collection Rate %])"},
          {"name":"Latest Collected",   "lineageTag":"col-m-04","formatString":"\\$#,0",
           "expression":"CALCULATE(SUM(CollectionPerformance[Collected]),TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],DESC))"},
          {"name":"Latest Outstanding", "lineageTag":"col-m-05","formatString":"\\$#,0",
           "expression":"CALCULATE(SUM(CollectionPerformance[Outstanding]),TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],DESC))"},
          {"name":"Collection Growth %","lineageTag":"col-m-06","formatString":"0.0%",
           "expression":(
             'VAR first=CALCULATE(SUM(CollectionPerformance[Collected]),'
             'TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],ASC)) '
             'VAR last=CALCULATE(SUM(CollectionPerformance[Collected]),'
             'TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],DESC)) '
             'RETURN DIVIDE(last-first,first,0)'
           )},
        ],
        "partitions": [{
          "name": "CollectionPerformance", "mode": "import",
          "source": {
            "type": "m",
            "expression": [
              "let",
              f"    Source   = Excel.Workbook(File.Contents({EP}), null, true),",
              '    Sheet    = Source{[Item="Collection Performance",Kind="Sheet"]}[Data],',
              "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
              "    Filtered = Table.SelectRows(Promoted, each [Month] <> null),",
              "    Renamed  = Table.RenameColumns(Filtered,{",
              '        {"Collected ($)","Collected"},{"Outstanding ($)","Outstanding"}}),',
              '    Selected = Table.SelectColumns(Renamed,{"Month","Collected","Outstanding"}),',
              "    Typed    = Table.TransformColumnTypes(Selected,{",
              '        {"Month",type text},{"Collected",type number},{"Outstanding",type number}})',
              "in Typed"
            ]
          }
        }],
        "annotations":[{"name":"PBI_ResultType","value":"Table"}]
      },
    ],

    "relationships": [],

    "annotations": [
      {"name":"PBI_QueryOrder","value":'["KPIs","AgingAnalysis","CollectionPerformance"]'},
      {"name":"PBIDesktopVersion","value":"2.112.1161.0 (22.11)"}
    ]
  }
}

# ── Content-Types (PBIT — no DataModel, uses DataModelSchema) ─────────────────
CT = '<?xml version="1.0" encoding="utf-8"?>\n' \
     '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n' \
     '  <Default Extension="json" ContentType="application/json"/>\n' \
     '  <Default Extension="png"  ContentType="image/png"/>\n' \
     '  <Override PartName="/DataModelSchema"  ContentType="application/octet-stream"/>\n' \
     '  <Override PartName="/DiagramLayout"    ContentType="application/json"/>\n' \
     '  <Override PartName="/Report/Layout"    ContentType="application/json"/>\n' \
     '  <Override PartName="/Settings"         ContentType="application/json"/>\n' \
     '  <Override PartName="/Metadata"         ContentType="application/json"/>\n' \
     '  <Override PartName="/Version"          ContentType="application/octet-stream"/>\n' \
     '  <Override PartName="/SecurityBindings" ContentType="application/octet-stream"/>\n' \
     '</Types>'

# ── Strip fields unsupported by older Power BI Desktop versions ───────────────
UNSUPPORTED_KEYS = {"lineageTag", "isKey", "sourceLineageTag"}

def strip_unsupported(obj):
    """Recursively remove keys that older PBI Desktop versions reject."""
    if isinstance(obj, dict):
        return {k: strip_unsupported(v) for k, v in obj.items() if k not in UNSUPPORTED_KEYS}
    if isinstance(obj, list):
        return [strip_unsupported(i) for i in obj]
    return obj

TMSL_CLEAN = strip_unsupported(TMSL)

# ── Write PBIT ────────────────────────────────────────────────────────────────
# KEY: reuse Report/Layout, Settings, Metadata, Version, SecurityBindings
# from the working source PBIX — only DataModelSchema and DiagramLayout are new.
tmsl_bytes = json.dumps(TMSL_CLEAN, ensure_ascii=False, separators=(",",":")).encode("utf-16-le")
diag_bytes = json.dumps(DIAGRAM,    ensure_ascii=False, separators=(",",":")).encode("utf-16-le")

with zipfile.ZipFile(DST, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("Version",             raw["Version"])          # original version file
    zout.writestr("[Content_Types].xml", CT.encode("utf-8"))
    zout.writestr("DataModelSchema",     tmsl_bytes)
    zout.writestr("DiagramLayout",       diag_bytes)
    zout.writestr("Report/Layout",       raw["Report/Layout"])    # reuse working layout
    zout.writestr("Settings",            raw["Settings"])         # reuse working settings
    zout.writestr("Metadata",            raw["Metadata"])         # reuse working metadata
    zout.writestr("SecurityBindings",    raw["SecurityBindings"])
    theme = "Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
    if theme in raw:
        zout.writestr(theme, raw[theme])

size = os.path.getsize(DST)
print(f"Written: {DST}  ({size:,} bytes)")

with zipfile.ZipFile(DST) as z:
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes (compress={i.compress_type})")

print(f"\nDataModelSchema: compatibilityLevel=1500")
print(f"Report/Layout:   reused from working PBIX (version 5.55) — guarantees compatibility")
print(f"\nTables:")
for t in TMSL["model"]["tables"]:
    cols = len(t.get("columns",[]))
    meas = len(t.get("measures",[]))
    print(f"  {t['name']}: {cols} columns, {meas} measures")

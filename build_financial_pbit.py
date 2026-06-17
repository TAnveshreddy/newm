#!/usr/bin/env python3
"""
Build Financial_Dashboard.pbit from Financial_Dashboard_Data_2.xlsx
Tables: KPIs (Thumbnail), AgingAnalysis, CollectionPerformance
"""
import zipfile, json, os

SRC_PBIX = "/root/.claude/uploads/bca2e082-c5c3-477b-a9e1-cb5c255f50cf/2fe318b8-SalesAnalytics_Dashboard_4.pbix"
DST      = "/home/user/newm/Financial_Dashboard.pbit"
EP       = "ExcelFilePath"

# Borrow Version / Settings / Metadata / SecurityBindings from an existing pbix
with zipfile.ZipFile(SRC_PBIX) as z:
    raw = {m: z.read(m) for m in z.namelist()}

# ── DiagramLayout (model view) ───────────────────────────────────────────────
DIAGRAM = {
  "version": "1.1.0",
  "diagrams": [{
    "ordinal": 0,
    "scrollPosition": {"x": 0, "y": 0},
    "zoomValue": 75,
    "nodes": [
      {"nodeIndex": "KPIs",                  "nodeLineageTag": "kpi-table-001",
       "location": {"x": 60,  "y": 60},  "size": {"width": 230, "height": 250}, "zIndex": 1},
      {"nodeIndex": "AgingAnalysis",         "nodeLineageTag": "aging-table-001",
       "location": {"x": 360, "y": 60},  "size": {"width": 230, "height": 150}, "zIndex": 1},
      {"nodeIndex": "CollectionPerformance", "nodeLineageTag": "col-table-001",
       "location": {"x": 660, "y": 60},  "size": {"width": 230, "height": 200}, "zIndex": 1},
    ]
  }]
}

# ── TMSL ─────────────────────────────────────────────────────────────────────
TMSL = {
  "name": "FinancialDashboard",
  "compatibilityLevel": 1567,
  "model": {
    "culture": "en-US",
    "collation": "Latin1_General_100_BIN2_UTF8",
    "defaultPowerBIDataSourceVersion": "powerBI_V3",
    "sourceQueryCulture": "en-US",

    "expressions": [{
      "name": EP,
      "description": "Full path to Financial_Dashboard_Data_2.xlsx",
      "kind": "m",
      "expression": '"C:\\\\Users\\\\anvesh.t\\\\Downloads\\\\Financial_Dashboard_Data_2.xlsx" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
      "annotations": [{"name": "PBI_NavigationStepName", "value": "Navigation"}]
    }],

    "tables": [

      # ── KPIs (Thumbnail sheet) ──────────────────────────────────────────
      {
        "name": "KPIs",
        "lineageTag": "kpi-table-001",
        "columns": [
          {"name": "KPI Name",  "dataType": "string", "sourceColumn": "KPI Name",  "lineageTag": "kpi-c-01", "isKey": True},
          {"name": "Value",     "dataType": "double", "sourceColumn": "Value",     "lineageTag": "kpi-c-02", "formatString": "#,0.00"},
          {"name": "UoM",       "dataType": "string", "sourceColumn": "UoM",       "lineageTag": "kpi-c-03"},
          {"name": "Min",       "dataType": "double", "sourceColumn": "Min",       "lineageTag": "kpi-c-04"},
          {"name": "Max",       "dataType": "double", "sourceColumn": "Max",       "lineageTag": "kpi-c-05"},
          {"name": "Accepted",  "dataType": "double", "sourceColumn": "Accepted",  "lineageTag": "kpi-c-06"},
          {"name": "Comments",  "dataType": "string", "sourceColumn": "Comments",  "lineageTag": "kpi-c-07"},
          # Computed columns
          {
            "name": "Status",
            "dataType": "string",
            "lineageTag": "kpi-c-08",
            "type": "calculated",
            "expression": """
VAR v = KPIs[Value]
VAR a = KPIs[Accepted]
VAR hib = NOT (KPIs[KPI Name] IN {"Lost Shipment Rate","Revenue Leakage","Delivery Exceptions"})
RETURN
IF(hib,
   IF(v >= a, "On Track", IF(v >= a * 0.9, "Watch", "Off Track")),
   IF(v <= a, "On Track", IF(v <= a * 1.5, "Watch", "Off Track"))
)"""
          },
          {
            "name": "Status Icon",
            "dataType": "string",
            "lineageTag": "kpi-c-09",
            "type": "calculated",
            "expression": 'IF(KPIs[Status]="On Track","✓ On Track", IF(KPIs[Status]="Watch","⚠ Watch","✕ Off Track"))'
          },
          {
            "name": "vs Target %",
            "dataType": "double",
            "lineageTag": "kpi-c-10",
            "type": "calculated",
            "formatString": "0.0%",
            "expression": "DIVIDE(KPIs[Value] - KPIs[Accepted], KPIs[Accepted], 0)"
          },
          {
            "name": "Progress %",
            "dataType": "double",
            "lineageTag": "kpi-c-11",
            "type": "calculated",
            "formatString": "0.0%",
            "expression": "DIVIDE(KPIs[Value] - KPIs[Min], KPIs[Max] - KPIs[Min], 0)"
          },
          {
            "name": "Formatted Value",
            "dataType": "string",
            "lineageTag": "kpi-c-12",
            "type": "calculated",
            "expression": 'IF(KPIs[UoM]="$", "$" & TEXT(KPIs[Value],"#,0.0"), TEXT(KPIs[Value],"#,0.0") & KPIs[UoM])'
          },
          {
            "name": "Higher Is Better",
            "dataType": "boolean",
            "lineageTag": "kpi-c-13",
            "type": "calculated",
            "expression": 'NOT (KPIs[KPI Name] IN {"Lost Shipment Rate","Revenue Leakage","Delivery Exceptions"})'
          },
        ],
        "measures": [
          {"name": "# KPIs On Track",  "lineageTag": "kpi-m-01",
           "expression": 'COUNTROWS(FILTER(KPIs, KPIs[Status]="On Track"))', "formatString": "#,0"},
          {"name": "# KPIs Watch",     "lineageTag": "kpi-m-02",
           "expression": 'COUNTROWS(FILTER(KPIs, KPIs[Status]="Watch"))',    "formatString": "#,0"},
          {"name": "# KPIs Off Track", "lineageTag": "kpi-m-03",
           "expression": 'COUNTROWS(FILTER(KPIs, KPIs[Status]="Off Track"))',"formatString": "#,0"},
          {"name": "Overall Health %", "lineageTag": "kpi-m-04",
           "expression": 'DIVIDE(COUNTROWS(FILTER(KPIs, KPIs[Status]="On Track")), COUNTROWS(KPIs), 0)',
           "formatString": "0.0%"},
          {"name": "Selected KPI Value", "lineageTag": "kpi-m-05",
           "expression": "SELECTEDVALUE(KPIs[Value])", "formatString": "#,0.00"},
          {"name": "Selected KPI Accepted", "lineageTag": "kpi-m-06",
           "expression": "SELECTEDVALUE(KPIs[Accepted])", "formatString": "#,0.00"},
        ],
        "partitions": [{
          "name": "KPIs",
          "mode": "import",
          "source": {
            "type": "m",
            "expression": [
              "let",
              f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
              '    Sheet    = Source{[Item="Thumbnail",Kind="Sheet"]}[Data],',
              "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
              "    // Remove rows where KPI Name is null",
              "    Filtered = Table.SelectRows(Promoted, each [KPI Name] <> null),",
              "    // Select only the 7 data columns",
              '    Selected = Table.SelectColumns(Filtered,{"KPI Name","Value","UoM","Min","Max","Accepted","Comments"}),',
              "    Typed = Table.TransformColumnTypes(Selected, {",
              '        {"KPI Name", type text},  {"Value", type number},',
              '        {"UoM", type text},       {"Min", type number},',
              '        {"Max", type number},     {"Accepted", type number},',
              '        {"Comments", type text}',
              "    })",
              "in",
              "    Typed"
            ]
          }
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
      },

      # ── AgingAnalysis ────────────────────────────────────────────────────
      {
        "name": "AgingAnalysis",
        "lineageTag": "aging-table-001",
        "columns": [
          {"name": "Days Bucket", "dataType": "string", "sourceColumn": "Days Bucket", "lineageTag": "ag-c-01", "isKey": True},
          {"name": "Amount",      "dataType": "double", "sourceColumn": "Amount",      "lineageTag": "ag-c-02",
           "formatString": '\\$#,0'},
          # Sort order column
          {
            "name": "Bucket Order",
            "dataType": "int64",
            "lineageTag": "ag-c-03",
            "type": "calculated",
            "expression": 'SWITCH(AgingAnalysis[Days Bucket],"Current",1,"1-30 Days",2,"31-60 Days",3,"61-90 Days",4,5)'
          },
        ],
        "measures": [
          {"name": "Total Outstanding",  "lineageTag": "ag-m-01",
           "expression": "SUM(AgingAnalysis[Amount])", "formatString": '\\$#,0'},
          {"name": "Current Amount",     "lineageTag": "ag-m-02",
           "expression": 'CALCULATE(SUM(AgingAnalysis[Amount]), AgingAnalysis[Days Bucket]="Current")',
           "formatString": '\\$#,0'},
          {"name": "Overdue Amount",     "lineageTag": "ag-m-03",
           "expression": 'CALCULATE(SUM(AgingAnalysis[Amount]), AgingAnalysis[Days Bucket]<>"Current")',
           "formatString": '\\$#,0'},
          {"name": "Current %",          "lineageTag": "ag-m-04",
           "expression": 'DIVIDE([Current Amount],[Total Outstanding],0)', "formatString": "0.0%"},
          {"name": "Overdue %",          "lineageTag": "ag-m-05",
           "expression": 'DIVIDE([Overdue Amount],[Total Outstanding],0)', "formatString": "0.0%"},
          {"name": "Highest Risk Amount","lineageTag": "ag-m-06",
           "expression": 'CALCULATE(SUM(AgingAnalysis[Amount]), AgingAnalysis[Days Bucket]="61-90 Days")',
           "formatString": '\\$#,0'},
        ],
        "partitions": [{
          "name": "AgingAnalysis",
          "mode": "import",
          "source": {
            "type": "m",
            "expression": [
              "let",
              f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
              '    Sheet    = Source{[Item="Aging Analysis",Kind="Sheet"]}[Data],',
              "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
              "    Filtered = Table.SelectRows(Promoted, each [Days Bucket] <> null),",
              "    Renamed  = Table.RenameColumns(Filtered, {{\"Amount ($)\", \"Amount\"}}),",
              '    Selected = Table.SelectColumns(Renamed, {"Days Bucket","Amount"}),',
              "    Typed    = Table.TransformColumnTypes(Selected, {",
              '        {"Days Bucket", type text}, {"Amount", type number}',
              "    })",
              "in",
              "    Typed"
            ]
          }
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
      },

      # ── CollectionPerformance ────────────────────────────────────────────
      {
        "name": "CollectionPerformance",
        "lineageTag": "col-table-001",
        "columns": [
          {"name": "Month",       "dataType": "string", "sourceColumn": "Month",       "lineageTag": "col-c-01", "isKey": True},
          {"name": "Collected",   "dataType": "double", "sourceColumn": "Collected",   "lineageTag": "col-c-02", "formatString": '\\$#,0'},
          {"name": "Outstanding", "dataType": "double", "sourceColumn": "Outstanding", "lineageTag": "col-c-03", "formatString": '\\$#,0'},
          # Computed columns
          {
            "name": "Year",
            "dataType": "int64",
            "lineageTag": "col-c-04",
            "type": "calculated",
            "expression": "2000 + VALUE(RIGHT(CollectionPerformance[Month], 2))"
          },
          {
            "name": "Month Order",
            "dataType": "int64",
            "lineageTag": "col-c-05",
            "type": "calculated",
            "expression": """
VAR mo = LEFT(CollectionPerformance[Month], 3)
VAR yr = VALUE(RIGHT(CollectionPerformance[Month], 2))
VAR mnum = SWITCH(mo,"Jan",1,"Feb",2,"Mar",3,"Apr",4,"May",5,"Jun",6,
                     "Jul",7,"Aug",8,"Sep",9,"Oct",10,"Nov",11,"Dec",12,0)
RETURN yr * 100 + mnum"""
          },
          {
            "name": "Collection Rate %",
            "dataType": "double",
            "lineageTag": "col-c-06",
            "type": "calculated",
            "formatString": "0.0%",
            "expression": "DIVIDE(CollectionPerformance[Collected], CollectionPerformance[Collected] + CollectionPerformance[Outstanding], 0)"
          },
          {
            "name": "Total",
            "dataType": "double",
            "lineageTag": "col-c-07",
            "type": "calculated",
            "formatString": '\\$#,0',
            "expression": "CollectionPerformance[Collected] + CollectionPerformance[Outstanding]"
          },
        ],
        "measures": [
          {"name": "Total Collected",    "lineageTag": "col-m-01",
           "expression": "SUM(CollectionPerformance[Collected])",   "formatString": '\\$#,0'},
          {"name": "Total Outstanding",  "lineageTag": "col-m-02",
           "expression": "SUM(CollectionPerformance[Outstanding])", "formatString": '\\$#,0'},
          {"name": "Avg Collection Rate","lineageTag": "col-m-03",
           "expression": "AVERAGEX(CollectionPerformance, CollectionPerformance[Collection Rate %])",
           "formatString": "0.0%"},
          {"name": "Latest Collected",   "lineageTag": "col-m-04",
           "expression": "CALCULATE(SUM(CollectionPerformance[Collected]),   TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],DESC))",
           "formatString": '\\$#,0'},
          {"name": "Latest Outstanding", "lineageTag": "col-m-05",
           "expression": "CALCULATE(SUM(CollectionPerformance[Outstanding]), TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],DESC))",
           "formatString": '\\$#,0'},
          {"name": "First Collected",    "lineageTag": "col-m-06",
           "expression": "CALCULATE(SUM(CollectionPerformance[Collected]),   TOPN(1,CollectionPerformance,CollectionPerformance[Month Order],ASC))",
           "formatString": '\\$#,0'},
          {"name": "Collection Growth %","lineageTag": "col-m-07",
           "expression": "DIVIDE([Latest Collected] - [First Collected], [First Collected], 0)",
           "formatString": "0.0%"},
          {"name": "MoM Growth %",       "lineageTag": "col-m-08",
           "expression": """
VAR curMonth  = MAX(CollectionPerformance[Month Order])
VAR curVal    = CALCULATE(SUM(CollectionPerformance[Collected]), CollectionPerformance[Month Order]=curMonth)
VAR prevMonth = curMonth - 1
VAR prevVal   = CALCULATE(SUM(CollectionPerformance[Collected]), CollectionPerformance[Month Order]=prevMonth)
RETURN DIVIDE(curVal - prevVal, prevVal, 0)""",
           "formatString": "0.0%"},
        ],
        "partitions": [{
          "name": "CollectionPerformance",
          "mode": "import",
          "source": {
            "type": "m",
            "expression": [
              "let",
              f"    Source = Excel.Workbook(File.Contents({EP}), null, true),",
              '    Sheet    = Source{[Item="Collection Performance",Kind="Sheet"]}[Data],',
              "    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars=true]),",
              "    Filtered = Table.SelectRows(Promoted, each [Month] <> null),",
              "    Renamed  = Table.RenameColumns(Filtered, {",
              '        {"Collected ($)", "Collected"}, {"Outstanding ($)", "Outstanding"}',
              "    }),",
              '    Selected = Table.SelectColumns(Renamed, {"Month","Collected","Outstanding"}),',
              "    Typed    = Table.TransformColumnTypes(Selected, {",
              '        {"Month", type text}, {"Collected", type number}, {"Outstanding", type number}',
              "    })",
              "in",
              "    Typed"
            ]
          }
        }],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}]
      },

    ],   # end tables

    # No cross-table relationships needed (3 independent fact tables)
    "relationships": [],

    "annotations": [
      {"name": "PBI_QueryOrder", "value": '["KPIs","AgingAnalysis","CollectionPerformance"]'},
      {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
      {"name": "PBIDesktopVersion",             "value": "2.136.1202.0 (24.12)"}
    ]
  }
}

# ── Report/Layout: minimal 3-page report ─────────────────────────────────────
def v(x,y,w,h,tab=0):
    return {"x":x,"y":y,"width":w,"height":h,"tabOrder":tab,"singleVisualGroup":None,"z":0,"filters":"[]"}

def textbox(x,y,w,h,text,size=14,bold=False,color="#1a2f4e",tab=0):
    paras=[{"horizontalTextAlignment":"Left","textRuns":[{"value":text,"textStyle":{
        "fontWeight":"bold" if bold else "normal","fontSize":f"{size}pt","color":color}}]}]
    cfg={"singleVisual":{"visualType":"textbox","objects":{"general":[{"properties":{"paragraphs":{"expr":{"Literal":{"Value":json.dumps(paras)}}}}}]}}}
    vc=v(x,y,w,h,tab); vc["config"]=json.dumps(cfg,separators=(",",":")); return vc

def card_visual(x,y,w,h,entity,prop,is_measure=False,title="",tab=0):
    if is_measure:
        sel=[{"Measure":{"Expression":{"SourceRef":{"Source":"t"}},"Property":prop},"Name":f"t.{prop}","NativeReferenceName":prop}]
        frm=[{"Name":"t","Entity":entity,"Type":0}]
        qref=f"t.{prop}"
    else:
        sel=[{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"t"}},"Property":prop}},"Function":0},"Name":f"Sum({entity}.{prop})","NativeReferenceName":f"Sum({entity}.{prop})"}]
        frm=[{"Name":"t","Entity":entity,"Type":0}]
        qref=f"Sum({entity}.{prop})"
    cfg={"singleVisual":{"visualType":"card","projections":{"Values":[{"queryRef":qref,"active":True}]},
        "prototypeQuery":{"Version":2,"From":frm,"Select":sel},
        "vcObjects":{
            "title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}},
                "fontSize":{"expr":{"Literal":{"Value":"10D"}}}}}],
            "labels":[{"properties":{"fontSize":{"expr":{"Literal":{"Value":"22D"}}},
                "color":{"solid":{"color":{"expr":{"Literal":{"Value":"'#0078d4'"}}}}}}}]}}}
    vc=v(x,y,w,h,tab); vc["config"]=json.dumps(cfg,separators=(",",":")); return vc

def bar_chart(x,y,w,h,entity,cat_col,val_col,title="",tab=0):
    cfg={"singleVisual":{"visualType":"columnChart",
        "projections":{"Category":[{"queryRef":f"{entity}.{cat_col}","active":True}],
                       "Y":[{"queryRef":f"Sum({entity}.{val_col})","active":True}]},
        "prototypeQuery":{"Version":2,
            "From":[{"Name":"a","Entity":entity,"Type":0}],
            "Select":[
                {"Column":{"Expression":{"SourceRef":{"Source":"a"}},"Property":cat_col},"Name":f"{entity}.{cat_col}"},
                {"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"a"}},"Property":val_col}},"Function":0},
                 "Name":f"Sum({entity}.{val_col})"}
            ],
            "OrderBy":[{"Direction":2,"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"a"}},"Property":"Bucket Order"}}}]
        },
        "vcObjects":{"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    }}
    vc=v(x,y,w,h,tab); vc["config"]=json.dumps(cfg,separators=(",",":")); return vc

def line_chart(x,y,w,h,entity,cat_col,val_cols,title="",tab=0):
    sel=[{"Column":{"Expression":{"SourceRef":{"Source":"c"}},"Property":cat_col},"Name":f"{entity}.{cat_col}"}]
    proj_y=[]
    for vc_col in val_cols:
        sel.append({"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"c"}},"Property":vc_col}},"Function":0},
                    "Name":f"Sum({entity}.{vc_col})"})
        proj_y.append({"queryRef":f"Sum({entity}.{vc_col})","active":True})
    cfg={"singleVisual":{"visualType":"lineChart",
        "projections":{"Category":[{"queryRef":f"{entity}.{cat_col}","active":True}],"Y":proj_y},
        "prototypeQuery":{"Version":2,"From":[{"Name":"c","Entity":entity,"Type":0}],"Select":sel,
            "OrderBy":[{"Direction":1,"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"c"}},"Property":"Month Order"}}}]},
        "vcObjects":{"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    }}
    vc=v(x,y,w,h,tab); vc["config"]=json.dumps(cfg,separators=(",",":")); return vc

def matrix_visual(x,y,w,h,entity,row_col,val_cols,title="",tab=0):
    sel=[{"Column":{"Expression":{"SourceRef":{"Source":"t"}},"Property":row_col},"Name":f"{entity}.{row_col}"}]
    proj_v=[]
    for c in val_cols:
        sel.append({"Column":{"Expression":{"SourceRef":{"Source":"t"}},"Property":c},"Name":f"{entity}.{c}"})
        proj_v.append({"queryRef":f"{entity}.{c}","active":True})
    cfg={"singleVisual":{"visualType":"tableEx",
        "projections":{"Values":[{"queryRef":f"{entity}.{row_col}","active":True}]+proj_v},
        "prototypeQuery":{"Version":2,"From":[{"Name":"t","Entity":entity,"Type":0}],"Select":sel},
        "vcObjects":{"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    }}
    vc=v(x,y,w,h,tab); vc["config"]=json.dumps(cfg,separators=(",",":")); return vc

def slicer(x,y,w,h,entity,col,title="",tab=0):
    cfg={"singleVisual":{"visualType":"slicer",
        "projections":{"Values":[{"queryRef":f"{entity}.{col}","active":True}]},
        "prototypeQuery":{"Version":2,"From":[{"Name":"s","Entity":entity,"Type":0}],
            "Select":[{"Column":{"Expression":{"SourceRef":{"Source":"s"}},"Property":col},"Name":f"{entity}.{col}"}]},
        "objects":{"data":[{"properties":{"mode":{"expr":{"Literal":{"Value":"'Basic'"}}}}}]},
        "vcObjects":{"title":[{"properties":{"show":{"expr":{"Literal":{"Value":"true"}}},"text":{"expr":{"Literal":{"Value":f"'{title}'"}}}}}]}
    }}
    vc=v(x,y,w,h,tab); vc["config"]=json.dumps(cfg,separators=(",",":")); return vc

# ── Pages ────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = 1280, 720

pages = [
  # Page 1: KPI Overview
  {
    "name": "Page1", "displayName": "KPI Overview",
    "width": PAGE_W, "height": PAGE_H, "visualContainers": [
      textbox(0,0,PAGE_W,46,"Financial Operations Dashboard — KPI Overview",16,True,"#1a2f4e",0),
      # KPI status slicer
      slicer(10,56,160,200,"KPIs","Status","KPI Status",10),
      slicer(10,264,160,160,"KPIs","KPI Name","KPI Name",20),
      # Summary cards
      card_visual(180,56,210,90,"KPIs","Overall Health %",True,"Overall Health",30),
      card_visual(400,56,210,90,"KPIs","# KPIs On Track",True,"On Track",40),
      card_visual(620,56,210,90,"KPIs","# KPIs Watch",True,"Watch",50),
      card_visual(840,56,210,90,"KPIs","# KPIs Off Track",True,"Off Track",60),
      # KPI table
      matrix_visual(180,156,880,390,"KPIs","KPI Name",
        ["Formatted Value","UoM","Accepted","Status Icon","vs Target %","Progress %","Comments"],
        "KPI Details",70),
      # Gauge chart (bar)
      bar_chart(180,556,880,150,"KPIs","KPI Name","Progress %","KPI Progress vs Target",80),
    ]
  },
  # Page 2: Aging Analysis
  {
    "name": "Page2", "displayName": "Aging Analysis",
    "width": PAGE_W, "height": PAGE_H, "visualContainers": [
      textbox(0,0,PAGE_W,46,"Accounts Receivable Aging Analysis",16,True,"#1a2f4e",0),
      # Slicer
      slicer(10,56,160,220,"AgingAnalysis","Days Bucket","Aging Bucket",10),
      # Summary cards
      card_visual(180,56,220,90,"AgingAnalysis","Total Outstanding",True,"Total Outstanding",20),
      card_visual(410,56,220,90,"AgingAnalysis","Current Amount",True,"Current (0 Days)",30),
      card_visual(640,56,220,90,"AgingAnalysis","Overdue Amount",True,"Total Overdue",40),
      card_visual(870,56,200,90,"AgingAnalysis","Current %",True,"Current %",50),
      # Bar chart
      bar_chart(180,156,620,300,"AgingAnalysis","Days Bucket","Amount","Aging by Bucket ($)",60),
      # Table
      matrix_visual(180,466,620,240,"AgingAnalysis","Days Bucket",["Amount","Bucket Order"],"Aging Detail",70),
      # Donut (use pie)
      bar_chart(810,156,450,550,"AgingAnalysis","Days Bucket","Amount","Distribution",80),
    ]
  },
  # Page 3: Collection Performance
  {
    "name": "Page3", "displayName": "Collection Performance",
    "width": PAGE_W, "height": PAGE_H, "visualContainers": [
      textbox(0,0,PAGE_W,46,"Collection Performance — Monthly Trends",16,True,"#1a2f4e",0),
      # Slicers
      slicer(10,56,160,160,"CollectionPerformance","Year","Year",10),
      slicer(10,226,160,120,"CollectionPerformance","Month","Month",20),
      # Summary cards
      card_visual(180,56,215,90,"CollectionPerformance","Latest Collected",True,"Latest Collected",30),
      card_visual(405,56,215,90,"CollectionPerformance","Latest Outstanding",True,"Latest Outstanding",40),
      card_visual(630,56,215,90,"CollectionPerformance","Collection Growth %",True,"Overall Growth",50),
      card_visual(855,56,215,90,"CollectionPerformance","Avg Collection Rate",True,"Avg Collection Rate",60),
      # Line chart: collected + outstanding
      line_chart(180,156,890,310,"CollectionPerformance","Month",
        ["Collected","Outstanding"],"Monthly Collected vs Outstanding",70),
      # Bar chart: collected only (trend)
      bar_chart(180,476,890,230,"CollectionPerformance","Month","Collected","Collected Amount by Month",80),
    ]
  },
]

LAYOUT = {
  "id": 0,
  "resourcePackages": [],
  "sections": [
    {
      "id": i,
      "name": p["name"],
      "displayName": p["displayName"],
      "filters": "[]",
      "ordinal": i,
      "width": p["width"],
      "height": p["height"],
      "displayOption": 1,
      "visualContainers": p["visualContainers"],
      "config": json.dumps({"relationships":[]}, separators=(",",":"))
    }
    for i, p in enumerate(pages)
  ],
  "config": json.dumps({
    "version": "5.51",
    "themeCollection": {"baseTheme": {"name": "CY23SU11", "version": "5.51",
      "type": 2, "resourceKey": "BaseThemes/CY23SU11.json"}},
    "activeSectionIndex": 0,
    "filterConfig": {"filters": []},
    "defaultDrillFilterOtherVisuals": True
  }, separators=(",",":")),
  "layoutOptimization": 0
}

# ── Content-Types ─────────────────────────────────────────────────────────────
CT = """<?xml version="1.0" encoding="utf-8"?>
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

SETTINGS = json.dumps({"Version":3,"AutoRecovery":{"Enabled":False}}, separators=(",",":"))
METADATA  = json.dumps({"version":"4.0","createdFrom":"unknown"}, separators=(",",":"))

# ── Write PBIT ────────────────────────────────────────────────────────────────
layout_bytes = json.dumps(LAYOUT, ensure_ascii=False, separators=(",",":")).encode("utf-16-le")
tmsl_bytes   = json.dumps(TMSL,   ensure_ascii=False, separators=(",",":")).encode("utf-16-le")
diag_bytes   = json.dumps(DIAGRAM,ensure_ascii=False, separators=(",",":")).encode("utf-16-le")

with zipfile.ZipFile(DST, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    zout.writestr("Version",             raw["Version"])
    zout.writestr("[Content_Types].xml", CT.strip().encode("utf-8"))
    zout.writestr("DataModelSchema",     tmsl_bytes)
    zout.writestr("DiagramLayout",       diag_bytes)
    zout.writestr("Report/Layout",       layout_bytes)
    zout.writestr("Settings",            SETTINGS.encode("utf-16-le"))
    zout.writestr("Metadata",            METADATA.encode("utf-16-le"))
    zout.writestr("SecurityBindings",    raw["SecurityBindings"])
    theme = "Report/StaticResources/SharedResources/BaseThemes/CY23SU11.json"
    if theme in raw:
        zout.writestr(theme, raw[theme])

size = os.path.getsize(DST)
print(f"Written: {DST}  ({size:,} bytes)")

with zipfile.ZipFile(DST) as z:
    for i in z.infolist():
        print(f"  {i.filename}: {i.file_size:,} bytes")

print("\nTables & measures:")
for t in TMSL["model"]["tables"]:
    cols = [c["name"] for c in t.get("columns",[])]
    meas = [m["name"] for m in t.get("measures",[])]
    print(f"  {t['name']}: {len(cols)} cols, {len(meas)} measures")
    print(f"    Cols: {cols}")
    print(f"    Measures: {meas}")

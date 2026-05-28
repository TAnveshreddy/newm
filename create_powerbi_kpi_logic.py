import openpyxl
from openpyxl.styles import (PatternFill, Font, Alignment, Border, Side,
                              numbers)
from openpyxl.utils import get_column_letter

# ── colours ────────────────────────────────────────────────────────────────
DARK_BLUE  = "1F3864"
MID_BLUE   = "2E75B6"
LIGHT_BLUE = "BDD7EE"
DARK_GREEN = "1E5631"
MID_GREEN  = "375623"
LIGHT_GREEN= "E2EFDA"
DARK_ORANGE= "843C0C"
LIGHT_ORANGE="FCE4D6"
DARK_GRAY  = "404040"
MID_GRAY   = "808080"
LIGHT_GRAY = "F2F2F2"
YELLOW     = "FFF2CC"
WHITE      = "FFFFFF"
PURPLE     = "7030A0"
LIGHT_PURPLE="EAD1DC"

def fill(hex_):  return PatternFill("solid", fgColor=hex_)
def font(hex_="000000", bold=False, size=10, italic=False, name="Calibri"):
    return Font(color=hex_, bold=bold, size=size, italic=italic, name=name)
def align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)
def thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)
def thick_bottom():
    b = Side(style="medium", color=DARK_BLUE)
    s = Side(style="thin",   color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=b)

def set_cell(ws, row, col, value, fill_=None, font_=None, align_=None,
             border_=None, number_format=None):
    c = ws.cell(row=row, column=col, value=value)
    if fill_:          c.fill          = fill_
    if font_:          c.font          = font_
    if align_:         c.alignment     = align_
    if border_:        c.border        = border_
    if number_format:  c.number_format = number_format
    return c

def merge_title(ws, row, start_col, end_col, text, fill_hex, font_hex="FFFFFF",
                sz=12, bold=True):
    ws.merge_cells(start_row=row, start_column=start_col,
                   end_row=row,   end_column=end_col)
    c = ws.cell(row=row, column=start_col, value=text)
    c.fill      = fill(fill_hex)
    c.font      = font(font_hex, bold=bold, size=sz)
    c.alignment = align("center", "center")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
wb = openpyxl.Workbook()
wb.remove(wb.active)

# ══════════════════════════════════════════════════════════════════════════
#  SHEET 1 – Daily Inventory KPIs  (Power BI DAX)
# ══════════════════════════════════════════════════════════════════════════
ws1 = wb.create_sheet("Daily Inventory — Power BI DAX")
ws1.sheet_view.showGridLines = False
ws1.freeze_panes = "A5"

# col widths
for col, w in [(1,5),(2,32),(3,18),(4,18),(5,65),(6,28),(7,22)]:
    ws1.column_dimensions[get_column_letter(col)].width = w

# ── Banner ──────────────────────────────────────────────────────────────
ws1.row_dimensions[1].height = 38
ws1.merge_cells("A1:G1")
c = ws1.cell(1,1,"DAILY INVENTORY REPORT  —  Power BI KPI Logic (DAX Measures)")
c.fill = fill(DARK_BLUE); c.font = font("FFFFFF", True, 15)
c.alignment = align("center","center")

ws1.row_dimensions[2].height = 22
ws1.merge_cells("A2:G2")
c = ws1.cell(2,1,"Source table: DailyInventory   |   Paste each DAX formula in Power BI → New Measure")
c.fill = fill(MID_BLUE); c.font = font("FFFFFF", False, 10)
c.alignment = align("center","center")

ws1.row_dimensions[3].height = 26
for col, lbl in enumerate(
        ["#","KPI Name","Source Column","Aggregation","DAX Measure Formula","What It Calculates","Power BI Visual Tips"],1):
    c = ws1.cell(3, col, lbl)
    c.fill = fill(MID_BLUE); c.font = font("FFFFFF", True, 10)
    c.alignment = align("center","center")
    c.border = thin_border()

# ── Data rows ──────────────────────────────────────────────────────────
daily_kpis = [
    (1,  "Opening Net Volume (BBLs)",        "Opening_Net_Volume",     "SUM",
     "Opening Net Volume (BBLs) =\nSUM(DailyInventory[Opening_Net_Volume])",
     "Total opening BBLs across all tanks",
     "Card, Bar Chart, Matrix by Product"),

    (2,  "Opening Gravity",                  "Opening_Gravity",        "AVERAGE",
     "Opening Gravity =\nAVERAGE(DailyInventory[Opening_Gravity])",
     "Average opening gravity across tanks",
     "Card, Table — filter by Tank for individual reading"),

    (3,  "Closing Net Volume (BBLs)",         "Closing_Net_Volume",     "SUM",
     "Closing Net Volume (BBLs) =\nSUM(DailyInventory[Closing_Net_Volume])",
     "Total closing BBLs across all tanks",
     "Card, Trend line over Date"),

    (4,  "Closing Gross Volume (BBLs)",       "Closing_Gross_Volume",   "SUM",
     "Closing Gross Volume (BBLs) =\nSUM(DailyInventory[Closing_Gross_Volume])",
     "Total gross closing BBLs (includes BS&W)",
     "Compare with Closing Net in clustered bar"),

    (5,  "Level Feet",                        "Level_Feet",             "Raw (per tank)",
     'Level Feet =\nIF(\n    HASONEVALUE(DailyInventory[Tank]),\n    MAX(DailyInventory[Level_Feet]),\n    BLANK()\n)',
     "Physical level reading — meaningful only per tank",
     "Table or Matrix — must filter to single tank"),

    (6,  "Gravity (Closing)",                "Gravity_Closing",        "AVERAGE",
     "Closing Gravity =\nAVERAGE(DailyInventory[Gravity_Closing])",
     "Average closing gravity across tanks",
     "Card, Gauge visual"),

    (7,  "Temperature",                      "Temperature",            "Raw (per tank)",
     'Temperature =\nIF(\n    HASONEVALUE(DailyInventory[Tank]),\n    MAX(DailyInventory[Temperature]),\n    BLANK()\n)',
     "Temperature reading — meaningful only per tank",
     "Table — do not aggregate across tanks"),

    (8,  "Total Water (BBLs)",               "Total_Water",            "SUM",
     "Total Water (BBLs) =\nSUM(DailyInventory[Total_Water])",
     "Total BS&W across all tanks",
     "Stacked bar with Net Volume"),

    (9,  "BSW Feet",                         "BSW_Feet",               "Raw (per tank)",
     'BSW Feet =\nIF(\n    HASONEVALUE(DailyInventory[Tank]),\n    MAX(DailyInventory[BSW_Feet]),\n    BLANK()\n)',
     "Bottom sediment & water level — per tank only",
     "Table — filter to single tank"),

    (10, "Volume of Available Product (BBLs)","Volume_Available_Product","SUM",
     "Volume Available Product (BBLs) =\nSUM(DailyInventory[Volume_Available_Product])",
     "Saleable product volume (Net – Water)",
     "KPI Card, Gauge vs max capacity"),

    (11, "Remaining Capacity (BBLs)",         "Remaining_Capacity",     "SUM",
     "Remaining Capacity (BBLs) =\nSUM(DailyInventory[Remaining_Capacity])",
     "Unused tank capacity available for filling",
     "Gauge visual, capacity utilisation %"),

    (12, "Inventory Change Net Vol (BBLs)",   "Inventory_Change_Net_Vol","SUM / Derived",
     "Inventory Change Net Vol (BBLs) =\n[Closing Net Volume (BBLs)]\n    - [Opening Net Volume (BBLs)]",
     "Daily movement: positive = fill, negative = draw",
     "Waterfall chart, conditional colour (red/green)"),
]

SUM_FILL   = fill(LIGHT_GREEN)
AVG_FILL   = fill(YELLOW)
RAW_FILL   = fill(LIGHT_GRAY)
CALC_FILL  = fill(LIGHT_ORANGE)

row = 4
for kpi in daily_kpis:
    num, name, src_col, agg, dax, what, tip = kpi
    ws1.row_dimensions[row].height = 72

    agg_fill = (SUM_FILL if "SUM" in agg else
                AVG_FILL if "AVERAGE" in agg else
                CALC_FILL if "Derived" in agg else RAW_FILL)

    set_cell(ws1, row, 1, num,     fill_=agg_fill,   font_=font(DARK_GRAY, True),
             align_=align("center","center"),       border_=thin_border())
    set_cell(ws1, row, 2, name,    fill_=agg_fill,   font_=font(DARK_BLUE, True, 10),
             align_=align("left","center",True),    border_=thin_border())
    set_cell(ws1, row, 3, src_col, fill_=agg_fill,   font_=font(DARK_GRAY),
             align_=align("center","center",True),  border_=thin_border())
    set_cell(ws1, row, 4, agg,     fill_=agg_fill,   font_=font(DARK_GREEN, True),
             align_=align("center","center"),       border_=thin_border())

    # DAX formula cell — Courier New, dark bg
    c = ws1.cell(row=row, column=5, value=dax)
    c.fill = fill("1C1C2E"); c.font = Font(name="Courier New", size=9,
                                           color="00FF9C", bold=False)
    c.alignment = Alignment(horizontal="left", vertical="center",
                            wrap_text=True)
    c.border = thin_border()

    set_cell(ws1, row, 6, what, fill_=fill(LIGHT_BLUE), font_=font(DARK_BLUE),
             align_=align("left","center",True),    border_=thin_border())
    set_cell(ws1, row, 7, tip,  fill_=fill(LIGHT_PURPLE), font_=font(PURPLE, False, 9),
             align_=align("left","center",True),    border_=thin_border())
    row += 1

# Legend row
ws1.row_dimensions[row].height = 18
ws1.merge_cells(f"A{row}:G{row}")
c = ws1.cell(row, 1,
    "LEGEND:  ■ Green = SUM   ■ Yellow = AVERAGE   ■ Grey = Raw/Per-Tank   ■ Orange = Derived/Calculated")
c.fill = fill(LIGHT_GRAY); c.font = font(DARK_GRAY, False, 9, True)
c.alignment = align("center","center")

# ══════════════════════════════════════════════════════════════════════════
#  SHEET 2 – Crude Inventory KPIs  (Power BI DAX)
# ══════════════════════════════════════════════════════════════════════════
ws2 = wb.create_sheet("Crude Inventory — Power BI DAX")
ws2.sheet_view.showGridLines = False
ws2.freeze_panes = "A5"

for col, w in [(1,5),(2,26),(3,20),(4,18),(5,65),(6,32),(7,24)]:
    ws2.column_dimensions[get_column_letter(col)].width = w

ws2.row_dimensions[1].height = 38
ws2.merge_cells("A1:G1")
c = ws2.cell(1,1,"CRUDE INVENTORY BY TANK REPORT  —  Power BI KPI Logic (DAX Measures)")
c.fill = fill(DARK_GREEN); c.font = font("FFFFFF", True, 15)
c.alignment = align("center","center")

ws2.row_dimensions[2].height = 22
ws2.merge_cells("A2:G2")
c = ws2.cell(2,1,"Source table: CrudeInventory   |   Columns: Tank, CrudeCode, CrudeDescription, Opening_Volume, Closing_Volume")
c.fill = fill(MID_GREEN); c.font = font("FFFFFF", False, 10)
c.alignment = align("center","center")

ws2.row_dimensions[3].height = 26
for col, lbl in enumerate(
        ["#","KPI Name","Applies To","Aggregation","DAX Measure Formula","What It Calculates","Power BI Visual Tips"],1):
    c = ws2.cell(3, col, lbl)
    c.fill = fill(MID_GREEN); c.font = font("FFFFFF", True, 10)
    c.alignment = align("center","center"); c.border = thin_border()

crude_kpis = [
    (1,  "Opening Volume (MB)",      "Crude-level rows",   "SUM",
     "Opening Volume (MB) =\nSUM(CrudeInventory[Opening_Volume])",
     "Total opening volume for selected crude(s)/tank(s)",
     "Matrix rows=Tank, cols=CrudeCode; Card by Tank"),

    (2,  "Opening % Share",          "Crude-level rows",   "IF / DIVIDE",
     "Opening % Share =\nVAR TankTotal =\n    CALCULATE(\n        SUM(CrudeInventory[Opening_Volume]),\n        ALLEXCEPT(CrudeInventory, CrudeInventory[Tank])\n    )\nRETURN\n    IF(TankTotal = 0, 0,\n        DIVIDE(\n            SUM(CrudeInventory[Opening_Volume]),\n            TankTotal\n        )\n    )",
     "Each crude's % share of its tank's opening volume.\nGuards against divide-by-zero.",
     "100% stacked bar per tank; format as %"),

    (3,  "Closing Volume (MB)",      "Crude-level rows",   "SUM",
     "Closing Volume (MB) =\nSUM(CrudeInventory[Closing_Volume])",
     "Total closing volume for selected crude(s)/tank(s)",
     "Compare Opening vs Closing in clustered bar"),

    (4,  "Closing % Share",          "Crude-level rows",   "IF / DIVIDE",
     "Closing % Share =\nVAR TankTotal =\n    CALCULATE(\n        SUM(CrudeInventory[Closing_Volume]),\n        ALLEXCEPT(CrudeInventory, CrudeInventory[Tank])\n    )\nRETURN\n    IF(TankTotal = 0, 0,\n        DIVIDE(\n            SUM(CrudeInventory[Closing_Volume]),\n            TankTotal\n        )\n    )",
     "Each crude's % share of its tank's closing volume.\nGuards against divide-by-zero.",
     "100% stacked bar per tank; format as %"),

    (5,  "Opening Vol — Tank Total", "Tank Total row",     "SUM (scoped to tank)",
     "Opening Vol Tank Total =\nCALCULATE(\n    SUM(CrudeInventory[Opening_Volume]),\n    ALLEXCEPT(CrudeInventory, CrudeInventory[Tank])\n)",
     "Sum of all crude opening volumes within each tank",
     "Matrix footer row; Tank-level Card"),

    (6,  "Closing Vol — Tank Total", "Tank Total row",     "SUM (scoped to tank)",
     "Closing Vol Tank Total =\nCALCULATE(\n    SUM(CrudeInventory[Closing_Volume]),\n    ALLEXCEPT(CrudeInventory, CrudeInventory[Tank])\n)",
     "Sum of all crude closing volumes within each tank",
     "Matrix footer row; Tank-level Card"),

    (7,  "Volume Change (MB)",       "Crude-level rows",   "Derived",
     "Volume Change (MB) =\n[Closing Volume (MB)] - [Opening Volume (MB)]",
     "Inventory movement per crude per tank.\nPositive = received, Negative = consumed/shipped.",
     "Waterfall chart by Tank+Crude; conditional colour"),

    (8,  "Grand Total — Opening Vol","Grand Total (all tanks)","SUM (ALL)",
     "Grand Total Opening Vol =\nCALCULATE(\n    SUM(CrudeInventory[Opening_Volume]),\n    ALL(CrudeInventory)\n)",
     "Facility-wide total opening volume across ALL tanks and crudes",
     "Single KPI Card at top of dashboard"),

    (9,  "Grand Total — Closing Vol","Grand Total (all tanks)","SUM (ALL)",
     "Grand Total Closing Vol =\nCALCULATE(\n    SUM(CrudeInventory[Closing_Volume]),\n    ALL(CrudeInventory)\n)",
     "Facility-wide total closing volume across ALL tanks and crudes",
     "Single KPI Card at top of dashboard"),

    (10, "Utilisation % by Tank",    "Tank-level KPI",     "Derived / DIVIDE",
     "Utilisation % by Tank =\nDIVIDE(\n    [Closing Vol — Tank Total],\n    [Tank Capacity],\n    0\n)",
     "How full each tank is at close (requires TankCapacity lookup table)",
     "Gauge visual per tank; conditional formatting"),
]

IF_FILL   = fill(YELLOW)
SCOPE_FILL= fill(LIGHT_BLUE)
GRAND_FILL= fill(LIGHT_ORANGE)

row = 4
for kpi in crude_kpis:
    num, name, applies, agg, dax, what, tip = kpi
    ws2.row_dimensions[row].height = 90

    a_fill = (fill(LIGHT_GREEN) if "SUM" == agg else
              IF_FILL           if "IF"   in agg  else
              SCOPE_FILL        if "scoped" in agg else
              GRAND_FILL        if "ALL"  in agg  else
              fill(LIGHT_ORANGE))

    set_cell(ws2, row, 1, num,     fill_=a_fill, font_=font(DARK_GRAY, True),
             align_=align("center","center"),    border_=thin_border())
    set_cell(ws2, row, 2, name,    fill_=a_fill, font_=font(DARK_GREEN, True,10),
             align_=align("left","center",True), border_=thin_border())
    set_cell(ws2, row, 3, applies, fill_=a_fill, font_=font(DARK_GRAY,False,9),
             align_=align("center","center",True),border_=thin_border())
    set_cell(ws2, row, 4, agg,     fill_=a_fill, font_=font(DARK_GREEN, True),
             align_=align("center","center"),    border_=thin_border())

    c = ws2.cell(row=row, column=5, value=dax)
    c.fill = fill("1C1C2E"); c.font = Font(name="Courier New", size=9,
                                           color="00FF9C", bold=False)
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    c.border = thin_border()

    set_cell(ws2, row, 6, what, fill_=fill(LIGHT_BLUE),   font_=font(DARK_BLUE,False,9),
             align_=align("left","center",True), border_=thin_border())
    set_cell(ws2, row, 7, tip,  fill_=fill(LIGHT_PURPLE), font_=font(PURPLE,False,9),
             align_=align("left","center",True), border_=thin_border())
    row += 1

ws2.row_dimensions[row].height = 18
ws2.merge_cells(f"A{row}:G{row}")
c = ws2.cell(row, 1,
    "LEGEND:  ■ Green = SUM   ■ Yellow = IF/DIVIDE %   ■ Blue = Tank-Scoped SUM   ■ Orange = Grand Total / Derived")
c.fill = fill(LIGHT_GRAY); c.font = font(DARK_GRAY, False, 9, True)
c.alignment = align("center","center")

# ══════════════════════════════════════════════════════════════════════════
#  SHEET 3 – Data Model & Setup Guide
# ══════════════════════════════════════════════════════════════════════════
ws3 = wb.create_sheet("Power BI Data Model Guide")
ws3.sheet_view.showGridLines = False

for col, w in [(1,30),(2,50),(3,45),(4,35)]:
    ws3.column_dimensions[get_column_letter(col)].width = w

ws3.row_dimensions[1].height = 38
ws3.merge_cells("A1:D1")
c = ws3.cell(1,1,"POWER BI DATA MODEL SETUP GUIDE")
c.fill = fill(DARK_BLUE); c.font = font("FFFFFF", True, 15)
c.alignment = align("center","center")

def section_hdr(ws, row, text, fill_hex):
    ws.row_dimensions[row].height = 22
    ws.merge_cells(f"A{row}:D{row}")
    c = ws.cell(row, 1, text)
    c.fill = fill(fill_hex); c.font = font("FFFFFF", True, 11)
    c.alignment = align("left","center")

def col_hdr_row(ws, row, headers, fill_hex):
    ws.row_dimensions[row].height = 20
    for i, h in enumerate(headers, 1):
        c = ws.cell(row, i, h)
        c.fill = fill(fill_hex); c.font = font("FFFFFF", True, 10)
        c.alignment = align("center","center"); c.border = thin_border()

def data_row(ws, row, vals, alt=False):
    ws.row_dimensions[row].height = 20
    bg = LIGHT_GRAY if alt else WHITE
    for i, v in enumerate(vals, 1):
        c = ws.cell(row, i, v)
        c.fill = fill(bg); c.font = font(DARK_GRAY, False, 9)
        c.alignment = align("left","center",True); c.border = thin_border()

# ── Table 1: Daily Inventory columns ─────────────────────────────────
r = 3
section_hdr(ws3, r, "TABLE 1 — DailyInventory  (Daily Inventory Report)", MID_BLUE); r+=1
col_hdr_row(ws3, r, ["Column Name (DAX)", "Data Type", "Description", "Source in Excel"], MID_BLUE); r+=1
daily_cols = [
    ("Date",                    "Date",    "Report date",                         "Column A"),
    ("Product_SAP_Code",        "Text",    "SAP product / grade code",            "Column B"),
    ("Product_Name",            "Text",    "Full product name",                   "Column C"),
    ("Tank",                    "Text",    "Tank identifier",                     "Column D"),
    ("Opening_Net_Volume",      "Decimal", "Opening net BBLs",                    "Column E"),
    ("Opening_Gravity",         "Decimal", "Opening gravity",                     "Column F"),
    ("Closing_Net_Volume",      "Decimal", "Closing net BBLs",                    "Column G"),
    ("Closing_Gross_Volume",    "Decimal", "Closing gross BBLs",                  "Column H"),
    ("Level_Feet",              "Decimal", "Physical tank level in feet",         "Column I"),
    ("Gravity_Closing",         "Decimal", "Closing gravity",                     "Column J"),
    ("Temperature",             "Decimal", "Temperature reading",                 "Column K"),
    ("Total_Water",             "Decimal", "BS&W volume BBLs",                    "Column L"),
    ("BSW_Feet",                "Decimal", "Bottom sediment & water feet",        "Column M"),
    ("Volume_Available_Product","Decimal", "Saleable product volume BBLs",        "Column N"),
    ("Remaining_Capacity",      "Decimal", "Unused tank capacity BBLs",           "Column O"),
    ("Inventory_Change_Net_Vol","Decimal", "Daily change in net vol BBLs",        "Column P"),
]
for i, row_data in enumerate(daily_cols):
    data_row(ws3, r, row_data, i%2==0); r+=1

r += 1
section_hdr(ws3, r, "TABLE 2 — CrudeInventory  (Crude Inventory By Tank Report)", MID_GREEN); r+=1
col_hdr_row(ws3, r, ["Column Name (DAX)", "Data Type", "Description", "Source in Excel"], MID_GREEN); r+=1
crude_cols = [
    ("Date",             "Date",    "Report date",                              "From filename / header"),
    ("Tank",             "Text",    "Tank identifier  e.g. TK13, TK16",        "Column A"),
    ("CrudeCode",        "Text",    "Crude short code  e.g. ANS, MED",         "Column B"),
    ("CrudeDescription", "Text",    "Full crude name  e.g. Alaskan North Slope","Column C"),
    ("Opening_Volume",   "Decimal", "Opening volume in MB (thousand barrels)",  "Column D / E"),
    ("Opening_Pct",      "Decimal", "Opening % share of tank (0–1)",           "Column F — calculate in DAX"),
    ("Closing_Volume",   "Decimal", "Closing volume in MB",                     "Column G"),
    ("Closing_Pct",      "Decimal", "Closing % share of tank (0–1)",           "Column H — calculate in DAX"),
]
for i, row_data in enumerate(crude_cols):
    data_row(ws3, r, row_data, i%2==0); r+=1

r += 1
section_hdr(ws3, r, "RECOMMENDED POWER BI VISUALS PER KPI GROUP", DARK_ORANGE); r+=1
col_hdr_row(ws3, r, ["KPI Group", "Recommended Visual", "Drill-through / Slicer", "Notes"], DARK_ORANGE); r+=1
visuals = [
    ("Volume KPIs (Opening/Closing Net/Gross)", "Clustered Bar / Line+Column",
     "Slicer: Date, Product, Tank", "Show trend over date on secondary axis"),
    ("Gravity KPIs",                            "Card + Table detail",
     "Slicer: Tank",               "Gravity varies by product — filter to single tank"),
    ("Water & BSW KPIs",                        "Stacked Bar (Net + Water)",
     "Slicer: Product/Tank",       "Helps identify tanks with high water cut"),
    ("Inventory Change (Daily P&L)",            "Waterfall Chart",
     "Slicer: Date range",         "Colour: green=positive(fill), red=negative(draw)"),
    ("Remaining Capacity",                      "Gauge Visual",
     "Slicer: Tank",               "Set max value = tank capacity from ref table"),
    ("Crude % Share per Tank",                  "100% Stacked Bar by CrudeCode",
     "Slicer: Tank, Date",         "Compare crude mix shift opening → closing"),
    ("Grand Total Volumes",                     "KPI Card (large font)",
     "Page-level slicer: Date",    "Place at top of dashboard for exec summary"),
    ("Utilisation % by Tank",                   "Treemap or Matrix + Conditional Format",
     "Slicer: Date",               "Red = >90%, Green = <70%, Yellow = 70–90%"),
]
for i, v in enumerate(visuals):
    data_row(ws3, r, v, i%2==0); r+=1

r += 1
section_hdr(ws3, r, "KEY DAX PATTERNS EXPLAINED", DARK_GRAY); r+=1
patterns = [
    ("SUM(Table[Column])",
     "Simple aggregation — sums all visible rows after slicers/filters",
     "Use for Volume KPIs"),
    ("AVERAGE(Table[Column])",
     "Simple mean — use carefully; gravity should ideally be volume-weighted",
     "Use for Gravity, Temperature"),
    ("IF(HASONEVALUE(T[Col]), MAX(T[Col]), BLANK())",
     "Returns value only when a single row is visible — prevents meaningless cross-tank aggregation",
     "Use for Level Feet, BSW Feet, Temperature"),
    ("CALCULATE(SUM(), ALLEXCEPT(T, T[Tank]))",
     "Removes all filters EXCEPT Tank — gives the tank-total regardless of crude slicer",
     "Required for % share denominator"),
    ("DIVIDE(numerator, denominator, 0)",
     "Safe division — returns 0 (not error) if denominator = 0",
     "Use for all % / ratio KPIs"),
    ("CALCULATE(SUM(), ALL(Table))",
     "Removes ALL filters — gives facility-wide grand total ignoring slicers",
     "Use for Grand Total KPI Cards"),
    ("[Closing Vol] - [Opening Vol]",
     "Measure referencing other measures — Power BI resolves filter context automatically",
     "Use for Inventory Change, Volume Delta"),
]
ws3.row_dimensions[r].height = 20
for col, h in enumerate(["DAX Pattern","What It Does","When to Use"],1):
    c = ws3.cell(r, col, h)
    c.fill = fill(DARK_GRAY); c.font = font("FFFFFF", True, 10)
    c.alignment = align("center","center"); c.border = thin_border()
r += 1
for i, (pat, what, when) in enumerate(patterns):
    ws3.row_dimensions[r].height = 28
    c = ws3.cell(r, 1, pat)
    c.fill = fill("1C1C2E"); c.font = Font(name="Courier New",size=9,color="00FF9C")
    c.alignment = Alignment(horizontal="left",vertical="center",wrap_text=True)
    c.border = thin_border()
    bg = LIGHT_GRAY if i%2==0 else WHITE
    set_cell(ws3, r, 2, what, fill_=fill(bg), font_=font(DARK_GRAY,False,9),
             align_=align("left","center",True), border_=thin_border())
    set_cell(ws3, r, 3, when, fill_=fill(LIGHT_BLUE), font_=font(DARK_BLUE,False,9),
             align_=align("left","center",True), border_=thin_border())
    r += 1

out = "/home/user/newm/PowerBI_KPI_Logic.xlsx"
wb.save(out)
print(f"Saved: {out}")
print(f"Sheets: {[s.title for s in wb.worksheets]}")

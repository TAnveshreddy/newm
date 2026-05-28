"""
Script to generate KPI_Formula_Summary.xlsx for Carson Daily Inventory Report.
"""

from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter

# ── Color palette ────────────────────────────────────────────────────────────
DARK_BLUE   = "003366"
MED_BLUE    = "1F5C99"
LIGHT_BLUE  = "E8F0FE"
ACCENT_BLUE = "2E75B6"
WHITE       = "FFFFFF"
LIGHT_GRAY  = "F2F2F2"
BORDER_CLR  = "BFBFBF"

# ── Fill helpers ─────────────────────────────────────────────────────────────
def fill(hex_color):
    return PatternFill(fill_type="solid", fgColor=hex_color)

def thin_border(top=True, bottom=True, left=True, right=True):
    s = Side(style="thin", color=BORDER_CLR)
    return Border(
        top    = s if top    else Side(),
        bottom = s if bottom else Side(),
        left   = s if left   else Side(),
        right  = s if right  else Side(),
    )

def medium_border():
    s = Side(style="medium", color="003366")
    return Border(top=s, bottom=s, left=s, right=s)

# ── Cell helpers ─────────────────────────────────────────────────────────────
def write_cell(ws, row, col, value,
               bg=None, fg=WHITE, bold=False, italic=False,
               size=10, wrap=False, halign="left", valign="center",
               border=None, number_format=None):
    cell = ws.cell(row=row, column=col, value=value)
    if bg:
        cell.fill = fill(bg)
    cell.font = Font(color=fg, bold=bold, italic=italic, size=size,
                     name="Calibri")
    cell.alignment = Alignment(horizontal=halign, vertical=valign,
                                wrap_text=wrap)
    if border is not None:
        cell.border = border
    if number_format:
        cell.number_format = number_format
    return cell


# ── DATA ──────────────────────────────────────────────────────────────────────

REPORT_NAME = "CARSON DAILY INVENTORY REPORT"
SYSTEM_INFO = "MPC Carson Refinery | AORA Mass Balance System"
UNIT        = "Barrels"
RECON_DATE  = "2026-01-01"
RECON_STATUS = "Intermediate"
SOURCE_SHEET = "Daily Inventory"
COL_RANGE   = "Columns B–P, Rows 8–246"

KPI_LIST = [
    # (No, Name, Column-letter, FormulaType, FormulaPattern, Notes)
    (1,  "Opening Net Volume (BBLs)",        "E", "SUM",
     "=E[tank1]+E[tank2]+…",
     "Sum of all tanks' opening volumes"),
    (2,  "Opening Gravity",                  "F", "AVERAGE",
     "=AVERAGE(F[tank1],F[tank2],…)",
     "Average gravity across all tanks"),
    (3,  "Closing Net Volume (BBLs)",         "G", "SUM",
     "=G[tank1]+G[tank2]+…",
     "Sum of all tanks' closing volumes"),
    (4,  "Closing Gross Volume (BBLs)",       "H", "SUM",
     "=H[tank1]+H[tank2]+…",
     "Sum of all tanks' gross volumes"),
    (5,  "Level Feet",                        "I", "Raw Data",
     "N/A – No aggregation",
     "Individual tank gauge reading"),
    (6,  "Gravity (Closing)",                 "J", "AVERAGE",
     "=AVERAGE(J[tank1],J[tank2],…)",
     "Average closing gravity"),
    (7,  "Temperature",                       "K", "Raw Data",
     "N/A – No aggregation",
     "Individual tank temperature"),
    (8,  "Total Water",                       "L", "SUM",
     "=L[tank1]+L[tank2]+…",
     "Sum of water volume across tanks"),
    (9,  "BSW Feet",                          "M", "Raw Data",
     "N/A – No aggregation",
     "Individual tank BSW reading"),
    (10, "Volume of Available Product",       "N", "SUM",
     "=N[tank1]+N[tank2]+…",
     "Sum of usable product"),
    (11, "Remaining Capacity",                "O", "SUM",
     "=O[tank1]+O[tank2]+…",
     "Sum of available tank space"),
    (12, "Inventory Change Net Volume (BBLs)","P", "SUM",
     "=P[tank1]+P[tank2]+…",
     "Net change per group"),
]

# overview summary (name, formula-type, purpose)
KPI_OVERVIEW = [
    ("Opening Net Volume (BBLs)",         "SUM",      "Total opening inventory per product group"),
    ("Opening Gravity",                   "AVERAGE",  "Average API gravity at opening"),
    ("Closing Net Volume (BBLs)",          "SUM",      "Total closing inventory per product group"),
    ("Closing Gross Volume (BBLs)",        "SUM",      "Gross closing volume (before water deduction)"),
    ("Level Feet",                         "Raw Data", "Actual gauge level; not aggregated"),
    ("Gravity (Closing)",                  "AVERAGE",  "Average API gravity at close"),
    ("Temperature",                        "Raw Data", "Actual tank temperature; not aggregated"),
    ("Total Water",                        "SUM",      "Aggregate water volume across tanks"),
    ("BSW Feet",                           "Raw Data", "Bottom sediment & water gauge level; not aggregated"),
    ("Volume of Available Product",        "SUM",      "Net product available for movement / sale"),
    ("Remaining Capacity",                 "SUM",      "Unused shell capacity per product group"),
    ("Inventory Change Net Volume (BBLs)", "SUM",      "Opening minus closing (net movement)"),
]

PRODUCT_GROUPS = [
    (1,  "Acc_84Blendgrade",      "84 Blendgrade",
     ["LF_001", "TK51"]),
    (2,  "Acc_84RegSuboctane",    "84 Regular Suboctane CBG AZ",
     ["TK53"]),
    (3,  "Acc_84RegularCARBOB",   "84 Regular CARBOB",
     ["TK41", "TK50", "TK54", "TK55", "TK65"]),
    (4,  "Acc_89PremiumCARB",     "89 Premium CARBOB",
     ["TK45", "TK52"]),
    (5,  "Acc_AlkyFeed",          "Alky Feed",
     ["TK682", "TK76", "TK78"]),
    (6,  "Acc_Alkylate",          "Alkylate",
     ["LF_005", "TK31", "TK43", "TK64"]),
    (7,  "Acc_ChemPropylene",     "Chemical Grade Propylene",
     ["TK398", "TK399"]),
    (8,  "Acc_Crude",             "Crude Mix",
     ["LF_004", "TK13", "TK16", "TK17", "TK18", "TK2", "TK3", "TK5", "TK6", "TK8"]),
    (9,  "Acc_DistillateStock",   "Distillate Stock",
     ["TK957", "TK958"]),
    (10, "Acc_ExportDiesel",      "Export Diesel",
     ["TK56", "TK57", "TK58", "TK59", "TK60"]),
    (11, "Acc_FuelOilBlndStck",   "Fuel Oil Blend Stock",
     ["TK152", "TK84"]),
    (12, "Acc_HighSulSlurry",     "High Sulfur Slurry",
     ["TK22"]),
    (13, "Acc_HSFO",              "High Sulfur Fuel Oil",
     ["TK23"]),
    (14, "Acc_HSVGO",             "High Sulfur Vacuum Gas Oil",
     ["TK24", "TK25", "TK26", "TK61"]),
    (15, "Acc_HvyCatGasoline",    "Heavy Cat Gasoline",
     ["TK71"]),
    (16, "Acc_Isobutane",         "Isobutane",
     ["TK88", "TK89"]),
    (17, "Acc_Isomerate",         "Isomerate",
     ["TK69", "TK70"]),
    (18, "Acc_JetBlendstock",     "Jet Fuel Blendstock",
     ["TK4"]),
    (19, "Acc_JetFuel",           "Jet Fuel",
     ["TK32", "TK33", "TK34", "TK40", "TK44", "TK49"]),
    (20, "Acc_KeroBlndStck",      "Unfinished Kerosene Blendstock",
     ["TK35", "TK773", "TK96", "TK97"]),
    (21, "Acc_LCO",               "Light Cycle Oil",
     ["TK968"]),
    (22, "Acc_LNaphtha",          "Light Naphtha",
     ["TK93"]),
    (23, "Acc_LowSulSlurry",      "Low Sulfur Slurry",
     ["TK11"]),
    (24, "Acc_LSVGO",             "Low Sulfur Vacuum Gas Oil",
     ["TK14", "TK502", "TK956", "TK959"]),
    (25, "Acc_LtCatGasoline",     "Light Cat Gasoline",
     ["TK68"]),
    (26, "Acc_MedCatGasoline",    "Medium Cat Gasoline",
     ["TK66"]),
    (27, "Acc_MixedButane",       "Mixed Butane",
     ["TK683", "TK73"]),
    (28, "Acc_MixedPentane",      "Mixed Pentanes",
     ["TK138", "TK139", "TK684"]),
    (29, "Acc_MoltenSulfur",      "Molten Sulfur",
     ["TK619"]),
    (30, "Acc_NormalButane",      "Normal Butane",
     ["LF_002", "TK79", "TK86", "TK87"]),
    (31, "Acc_OOS",               "Out of Service (group 1)",
     ["TK155", "TK157", "TK187", "TK289", "TK355", "TK42", "TK620", "TK776", "TK905"]),
    (32, "Acc_PetCoke",           "Petroleum Coke",
     ["TK_Coke"]),
    (33, "Acc_Reformate",         "Reformate",
     ["TK62", "TK63"]),
    (34, "Acc_RefPropylene",      "Refinery Grade Propylene",
     ["TK350", "TK351", "TK352", "TK353"]),
    (35, "Acc_RenewDiesel",       "Renewable Diesel Consumption",
     ["TK36", "TK37", "TK39"]),
    (36, "Acc_RenewNaph",         "Renewable Naphtha Consumption",
     ["TK27", "TK28"]),
    (37, "Acc_SlopOil",           "Slop Oil",
     ["TK1", "TK101", "TK102", "TK103", "TK12", "TK154", "TK164",
      "TK188", "TK189", "TK190", "TK194", "TK284", "TK426",
      "TK614", "TK700", "TK777", "TK778"]),
    (38, "Acc_SourNaph",          "Sour Naphtha",
     ["TK681", "TK90", "TK91", "TK969"]),
    (39, "Acc_SRNaphtha",         "Straight Run Naphtha",
     ["TK74", "TK75", "TK955"]),
    (40, "Acc_SweetNaph",         "Sweet Naphtha",
     ["TK67"]),
    (41, "Acc_Transmix",          "Transmix",
     ["TK191", "TK192", "TK29", "TK30"]),
    (42, "Acc_ULSD2",             "ULSD No 2",
     ["LF_003"]),
    (43, "Acc_UnstnchdPropane",   "Unstenched Propane",
     ["TK274", "TK275", "TK276", "TK301", "TK302", "TK303",
      "TK325", "TK326", "TK327", "TK340", "TK341", "TK342",
      "TK343", "TK354"]),
    (44, "H20",                   "Water",
     ["TK83"]),
    (45, "OOS",                   "Out of Service (group 2)",
     ["TK153", "TK774", "TK775"]),
]


# ── Sheet 1: Report Overview ──────────────────────────────────────────────────

def build_overview(wb):
    ws = wb.create_sheet("Report Overview")
    ws.sheet_view.showGridLines = False

    # --- Column widths ---
    col_widths = {1: 4, 2: 36, 3: 18, 4: 52}
    for c, w in col_widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w

    row = 1
    # ── Big title banner (spans B:D = cols 2-4) ──
    ws.row_dimensions[row].height = 40
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    c = write_cell(ws, row, 2,
                   "✦  CARSON DAILY INVENTORY REPORT  ✦",
                   bg=DARK_BLUE, fg=WHITE, bold=True, size=16,
                   halign="center", valign="center")
    c.border = medium_border()
    row += 1

    # ── Subtitle ──
    ws.row_dimensions[row].height = 22
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    c = write_cell(ws, row, 2,
                   "KPI & Formula Reference  ·  AORA Mass Balance System",
                   bg=ACCENT_BLUE, fg=WHITE, bold=False, size=11,
                   halign="center", valign="center", italic=True)
    c.border = thin_border()
    row += 2   # blank row

    # ── Report Info section header ──
    ws.row_dimensions[row].height = 20
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    write_cell(ws, row, 2, "  REPORT INFORMATION",
               bg=MED_BLUE, fg=WHITE, bold=True, size=10,
               halign="left", valign="center",
               border=thin_border())
    row += 1

    info_rows = [
        ("System",        SYSTEM_INFO),
        ("Unit of Measure", UNIT),
        ("Recon Date",    RECON_DATE),
        ("Recon Status",  RECON_STATUS),
        ("Source Sheet",  SOURCE_SHEET),
        ("Data Range",    COL_RANGE),
        ("Product Groups", f"{len(PRODUCT_GROUPS)} groups"),
    ]

    for i, (label, value) in enumerate(info_rows):
        ws.row_dimensions[row].height = 18
        bg = WHITE if i % 2 == 0 else LIGHT_BLUE
        write_cell(ws, row, 2, f"  {label}",
                   bg=bg, fg="1F1F1F", bold=True, size=10,
                   halign="left", valign="center", border=thin_border())
        ws.merge_cells(start_row=row, start_column=3, end_row=row, end_column=4)
        write_cell(ws, row, 3, value,
                   bg=bg, fg="1F1F1F", bold=False, size=10,
                   halign="left", valign="center", border=thin_border())
        row += 1

    row += 1  # spacer

    # ── KPI Summary table header ──
    ws.row_dimensions[row].height = 20
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    write_cell(ws, row, 2, "  KPI SUMMARY  —  All 12 Key Performance Indicators",
               bg=MED_BLUE, fg=WHITE, bold=True, size=10,
               halign="left", valign="center", border=thin_border())
    row += 1

    # sub-header
    ws.row_dimensions[row].height = 18
    for col_idx, hdr in enumerate(["KPI Name", "Formula Type", "Purpose / Description"], start=2):
        write_cell(ws, row, col_idx, hdr,
                   bg=DARK_BLUE, fg=WHITE, bold=True, size=10,
                   halign="center", valign="center", border=thin_border())
    row += 1

    for i, (name, ftype, purpose) in enumerate(KPI_OVERVIEW):
        ws.row_dimensions[row].height = 18
        bg = WHITE if i % 2 == 0 else LIGHT_BLUE
        # badge color for formula type
        badge_bg = "D6E4FF" if ftype == "SUM" else ("FFF0D6" if ftype == "AVERAGE" else "F0F0F0")
        badge_fg = "003399" if ftype == "SUM" else ("7F4F00" if ftype == "AVERAGE" else "555555")

        write_cell(ws, row, 2, f"  {name}",
                   bg=bg, fg="1F1F1F", bold=False, size=10,
                   halign="left", valign="center", border=thin_border())
        write_cell(ws, row, 3, ftype,
                   bg=badge_bg, fg=badge_fg, bold=True, size=10,
                   halign="center", valign="center", border=thin_border())
        write_cell(ws, row, 4, purpose,
                   bg=bg, fg="1F1F1F", bold=False, size=10,
                   halign="left", valign="center", border=thin_border(), wrap=True)
        row += 1

    row += 1
    ws.row_dimensions[row].height = 14
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
    write_cell(ws, row, 2,
               "Generated by create_kpi_summary.py  ·  Data Source: Carson Daily Inventory Report (.xlsm)",
               bg=LIGHT_GRAY, fg="888888", italic=True, size=8,
               halign="center", valign="center")

    ws.freeze_panes = "B4"
    return ws


# ── Sheet 2: KPI Formula Details ─────────────────────────────────────────────

def build_kpi_details(wb):
    ws = wb.create_sheet("KPI Formula Details")
    ws.sheet_view.showGridLines = False

    col_widths = {1: 4, 2: 6, 3: 34, 4: 10, 5: 14, 6: 42, 7: 44}
    for c, w in col_widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w

    row = 1
    ws.row_dimensions[row].height = 36
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    c = write_cell(ws, row, 2,
                   "KPI FORMULA DETAILS  —  Carson Daily Inventory Report",
                   bg=DARK_BLUE, fg=WHITE, bold=True, size=14,
                   halign="center", valign="center")
    c.border = medium_border()
    row += 1

    ws.row_dimensions[row].height = 18
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    write_cell(ws, row, 2,
               f"Source: {SOURCE_SHEET}  |  Columns B–P  |  Unit: {UNIT}  |  Recon Date: {RECON_DATE}",
               bg=ACCENT_BLUE, fg=WHITE, italic=True, size=10,
               halign="center", valign="center", border=thin_border())
    row += 1

    headers = ["No.", "KPI Name", "Column", "Formula Type", "Formula Pattern", "Notes"]
    ws.row_dimensions[row].height = 20
    for col_idx, hdr in enumerate(headers, start=2):
        write_cell(ws, row, col_idx, hdr,
                   bg=DARK_BLUE, fg=WHITE, bold=True, size=10,
                   halign="center", valign="center", border=thin_border())
    ws.freeze_panes = f"B{row+1}"
    row += 1

    for i, (no, name, col_ltr, ftype, pattern, notes) in enumerate(KPI_LIST):
        ws.row_dimensions[row].height = 18
        bg = WHITE if i % 2 == 0 else LIGHT_BLUE
        badge_bg = "D6E4FF" if ftype == "SUM" else ("FFF0D6" if ftype == "AVERAGE" else "F0F0F0")
        badge_fg = "003399" if ftype == "SUM" else ("7F4F00" if ftype == "AVERAGE" else "555555")

        write_cell(ws, row, 2, no,
                   bg=bg, bold=True, fg="1F1F1F", size=10,
                   halign="center", valign="center", border=thin_border())
        write_cell(ws, row, 3, name,
                   bg=bg, fg="1F1F1F", size=10,
                   halign="left", valign="center", border=thin_border())
        write_cell(ws, row, 4, col_ltr,
                   bg=bg, bold=True, fg=DARK_BLUE, size=10,
                   halign="center", valign="center", border=thin_border())
        write_cell(ws, row, 5, ftype,
                   bg=badge_bg, fg=badge_fg, bold=True, size=10,
                   halign="center", valign="center", border=thin_border())
        write_cell(ws, row, 6, pattern,
                   bg=bg, fg="1F1F1F", size=9,
                   halign="left", valign="center", border=thin_border())
        write_cell(ws, row, 7, notes,
                   bg=bg, fg="444444", size=10, italic=True,
                   halign="left", valign="center", border=thin_border())
        row += 1

    return ws


# ── Sheet 3: Table-KPI-Formula Mapping ───────────────────────────────────────

def build_mapping(wb):
    ws = wb.create_sheet("Table-KPI-Formula Mapping")
    ws.sheet_view.showGridLines = False

    # column widths: 1=spacer, 2=No, 3=SAP Code, 4=Full Name, 5=Tanks, 6=#Tanks,
    # 7..14 = 8 KPI columns
    kpi_col_widths = {
        1: 2,
        2: 6,
        3: 28,
        4: 36,
        5: 68,
        6: 10,
        7: 20,
        8: 20,
        9: 20,
        10: 22,
        11: 18,
        12: 18,
        13: 24,
        14: 22,
        15: 26,
    }
    for c, w in kpi_col_widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w

    row = 1
    ws.row_dimensions[row].height = 38
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=15)
    c = write_cell(ws, row, 2,
                   "TABLE  ·  KPI  ·  FORMULA MAPPING  —  Carson Daily Inventory Report",
                   bg=DARK_BLUE, fg=WHITE, bold=True, size=14,
                   halign="center", valign="center")
    c.border = medium_border()
    row += 1

    ws.row_dimensions[row].height = 18
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=15)
    write_cell(ws, row, 2,
               f"45 Product Groups  |  Unit: {UNIT}  |  Recon Date: {RECON_DATE}  |  Status: {RECON_STATUS}",
               bg=ACCENT_BLUE, fg=WHITE, italic=True, size=10,
               halign="center", valign="center", border=thin_border())
    row += 1

    # ── Legend row ──
    ws.row_dimensions[row].height = 16
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    write_cell(ws, row, 2, "  Legend:",
               bg=LIGHT_GRAY, fg="555555", bold=True, size=9,
               halign="left", valign="center", border=thin_border())
    legend_items = [
        (6,  "D6E4FF", "003399", "SUM = total across tanks"),
        (8,  "FFF0D6", "7F4F00", "AVG = average across tanks"),
        (10, "F0F0F0", "555555", "– = Raw Data only"),
    ]
    for col_idx, bg_hex, fg_hex, label in legend_items:
        write_cell(ws, row, col_idx, label,
                   bg=bg_hex, fg=fg_hex, bold=True, size=9,
                   halign="center", valign="center", border=thin_border())
        # leave gap
    for gap_col in [7, 9, 11, 12, 13, 14, 15]:
        write_cell(ws, row, gap_col, "",
                   bg=LIGHT_GRAY, size=9, border=thin_border())
    row += 1

    # ── Column headers (split into 2 header rows for KPI columns) ──
    hdr1 = [
        (2,  "No."),
        (3,  "SAP Code\n(Table Name)"),
        (4,  "Full Product Name"),
        (5,  "Tanks Included"),
        (6,  "No. of\nTanks"),
        (7,  "Opening\nNet Vol"),
        (8,  "Opening\nGravity"),
        (9,  "Closing\nNet Vol"),
        (10, "Closing\nGross Vol"),
        (11, "Gravity\n(Closing)"),
        (12, "Total\nWater"),
        (13, "Vol of Available\nProduct"),
        (14, "Remaining\nCapacity"),
        (15, "Inv Change\nNet Vol"),
    ]
    ws.row_dimensions[row].height = 30
    for col_idx, hdr_text in hdr1:
        write_cell(ws, row, col_idx, hdr_text,
                   bg=DARK_BLUE, fg=WHITE, bold=True, size=9,
                   halign="center", valign="center",
                   border=thin_border(), wrap=True)
    ws.freeze_panes = f"B{row+1}"
    row += 1

    # KPI column index to formula type
    # col 7  = Opening Net Vol   → SUM
    # col 8  = Opening Gravity   → AVERAGE
    # col 9  = Closing Net Vol   → SUM
    # col 10 = Closing Gross Vol → SUM
    # col 11 = Gravity (Closing) → AVERAGE
    # col 12 = Total Water       → SUM
    # col 13 = Vol Avail Product → SUM
    # col 14 = Remaining Cap     → SUM
    # col 15 = Inv Change Net    → SUM
    KPI_COL_TYPE = {
        7:  ("SUM",     "D6E4FF", "003399"),
        8:  ("AVG",     "FFF0D6", "7F4F00"),
        9:  ("SUM",     "D6E4FF", "003399"),
        10: ("SUM",     "D6E4FF", "003399"),
        11: ("AVG",     "FFF0D6", "7F4F00"),
        12: ("SUM",     "D6E4FF", "003399"),
        13: ("SUM",     "D6E4FF", "003399"),
        14: ("SUM",     "D6E4FF", "003399"),
        15: ("SUM",     "D6E4FF", "003399"),
    }

    for i, (no, sap_code, full_name, tanks) in enumerate(PRODUCT_GROUPS):
        ws.row_dimensions[row].height = 32
        bg = WHITE if i % 2 == 0 else LIGHT_BLUE

        tank_str = ",  ".join(tanks)
        n_tanks  = len(tanks)

        write_cell(ws, row, 2,  no,        bg=bg, bold=True, fg="1F1F1F", size=9,
                   halign="center", valign="center", border=thin_border())
        write_cell(ws, row, 3,  sap_code,  bg=bg, bold=True, fg=DARK_BLUE, size=9,
                   halign="left",   valign="center", border=thin_border())
        write_cell(ws, row, 4,  full_name, bg=bg, fg="1F1F1F", size=9,
                   halign="left",   valign="center", border=thin_border(), wrap=True)
        write_cell(ws, row, 5,  tank_str,  bg=bg, fg="333333", size=8,
                   halign="left",   valign="center", border=thin_border(), wrap=True)
        write_cell(ws, row, 6,  n_tanks,   bg=bg, bold=True, fg="1F1F1F", size=9,
                   halign="center", valign="center", border=thin_border())

        for col_idx, (label, b_bg, b_fg) in KPI_COL_TYPE.items():
            write_cell(ws, row, col_idx, label,
                       bg=b_bg, fg=b_fg, bold=True, size=9,
                       halign="center", valign="center", border=thin_border())
        row += 1

    # ── Totals / stats row ──
    ws.row_dimensions[row].height = 18
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    write_cell(ws, row, 2, f"  TOTAL:  {len(PRODUCT_GROUPS)} Product Groups",
               bg=DARK_BLUE, fg=WHITE, bold=True, size=10,
               halign="left", valign="center", border=thin_border())
    total_tanks = sum(len(t) for _, _, _, t in PRODUCT_GROUPS)
    write_cell(ws, row, 6, total_tanks,
               bg=DARK_BLUE, fg=WHITE, bold=True, size=10,
               halign="center", valign="center", border=thin_border())
    for col_idx in range(7, 16):
        write_cell(ws, row, col_idx, "",
                   bg=DARK_BLUE, border=thin_border())

    return ws


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    print("Building Sheet 1: Report Overview …")
    build_overview(wb)

    print("Building Sheet 2: KPI Formula Details …")
    build_kpi_details(wb)

    print("Building Sheet 3: Table-KPI-Formula Mapping …")
    build_mapping(wb)

    out_path = "/home/user/newm/KPI_Formula_Summary.xlsx"
    wb.save(out_path)
    print(f"\nDone!  Saved to: {out_path}")
    print(f"  Sheets: {[s.title for s in wb.worksheets]}")
    print(f"  Product groups: {len(PRODUCT_GROUPS)}")
    print(f"  Total tanks:    {sum(len(t) for _,_,_,t in PRODUCT_GROUPS)}")


if __name__ == "__main__":
    main()

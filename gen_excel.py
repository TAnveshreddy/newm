import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# ── helpers ──────────────────────────────────────────────────────────────────
def thin_border():
    s = Side(style='thin', color='CCCCCC')
    return Border(left=s, right=s, top=s, bottom=s)

def apply_header(ws, row, cols, bg='1F3A5F', fg='FFFFFF'):
    fill = PatternFill('solid', fgColor=bg)
    font = Font(bold=True, color=fg, size=11)
    for c, val in enumerate(cols, 1):
        cell = ws.cell(row=row, column=c, value=val)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border()

def money(ws, row, col, val):
    c = ws.cell(row=row, column=col, value=val)
    c.number_format = '#,##0.00'
    c.alignment = Alignment(horizontal='right')
    c.border = thin_border()
    return c

def pct(ws, row, col, val):
    c = ws.cell(row=row, column=col, value=val / 100)
    c.number_format = '0.00%'
    c.alignment = Alignment(horizontal='right')
    c.border = thin_border()
    return c

def text_cell(ws, row, col, val, bold=False, center=False):
    c = ws.cell(row=row, column=col, value=val)
    c.font = Font(bold=bold, size=11)
    c.border = thin_border()
    if center:
        c.alignment = Alignment(horizontal='center')
    return c

# ── Monthly data ─────────────────────────────────────────────────────────────
months = ['January','February','March','April','May','June',
          'July','August','September','October','November','December']

revenue = [720000, 755000, 810000, 865000, 890000, 920000,
           880000, 905000, 950000, 980000, 1050000, 1075000]
expenses= [610000, 625000, 660000, 695000, 710000, 730000,
           700000, 715000, 740000, 760000, 820000, 840000]
profits = [r - e for r, e in zip(revenue, expenses)]
margins = [p / r * 100 for p, r in zip(profits, revenue)]

# ── Sheet 1: Summary ─────────────────────────────────────────────────────────
ws1 = wb.active
ws1.title = 'Summary'

# Title rows
ws1.merge_cells('A1:E1')
title = ws1['A1']
title.value = 'Financial Dashboard 2024'
title.font = Font(bold=True, size=16, color='FFFFFF')
title.fill = PatternFill('solid', fgColor='0D2137')
title.alignment = Alignment(horizontal='center', vertical='center')
ws1.row_dimensions[1].height = 36

ws1.merge_cells('A2:E2')
sub = ws1['A2']
sub.value = 'Company: Acme Corp  |  Period: Jan–Dec 2024  |  Currency: USD'
sub.font = Font(italic=True, size=11, color='FFFFFF')
sub.fill = PatternFill('solid', fgColor='1F3A5F')
sub.alignment = Alignment(horizontal='center', vertical='center')
ws1.row_dimensions[2].height = 22

ws1.row_dimensions[3].height = 6  # spacer

apply_header(ws1, 4, ['Month', 'Revenue (USD)', 'Expenses (USD)', 'Profit (USD)', 'Profit Margin %'])
ws1.row_dimensions[4].height = 22

alt1 = PatternFill('solid', fgColor='EBF2FA')
alt2 = PatternFill('solid', fgColor='FFFFFF')

for i, (m, r, e, p, mg) in enumerate(zip(months, revenue, expenses, profits, margins)):
    row = 5 + i
    fill = alt1 if i % 2 == 0 else alt2
    c = text_cell(ws1, row, 1, m, center=True)
    c.fill = fill
    for col, val in ((2, r), (3, e), (4, p)):
        cell = money(ws1, row, col, val)
        cell.fill = fill
    pc = pct(ws1, row, 5, mg)
    pc.fill = fill
    # colour profit cell
    profit_cell = ws1.cell(row=row, column=4)
    profit_cell.font = Font(color='1A7A4A' if p > 0 else 'C0392B', bold=True)

# Totals row
tr = 17
ws1.cell(row=tr, column=1, value='TOTAL').font = Font(bold=True, size=11)
ws1.cell(row=tr, column=1).fill = PatternFill('solid', fgColor='1F3A5F')
ws1.cell(row=tr, column=1).font = Font(bold=True, color='FFFFFF')
ws1.cell(row=tr, column=1).alignment = Alignment(horizontal='center')
ws1.cell(row=tr, column=1).border = thin_border()
for col, vals in ((2, revenue), (3, expenses), (4, profits)):
    c = money(ws1, tr, col, sum(vals))
    c.font = Font(bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='1F3A5F')
avg_margin = sum(profits) / sum(revenue) * 100
pc = pct(ws1, tr, 5, avg_margin)
pc.font = Font(bold=True, color='FFFFFF')
pc.fill = PatternFill('solid', fgColor='1F3A5F')

ws1.column_dimensions['A'].width = 16
ws1.column_dimensions['B'].width = 18
ws1.column_dimensions['C'].width = 18
ws1.column_dimensions['D'].width = 16
ws1.column_dimensions['E'].width = 16

# ── Sheet 2: Quarterly ───────────────────────────────────────────────────────
ws2 = wb.create_sheet('Quarterly')

ws2.merge_cells('A1:E1')
t2 = ws2['A1']
t2.value = 'Quarterly Performance – Acme Corp 2024'
t2.font = Font(bold=True, size=14, color='FFFFFF')
t2.fill = PatternFill('solid', fgColor='0D2137')
t2.alignment = Alignment(horizontal='center', vertical='center')
ws2.row_dimensions[1].height = 32

apply_header(ws2, 2, ['Quarter', 'Revenue (USD)', 'Expenses (USD)', 'EBITDA (USD)', 'Net Income (USD)'])

q_rev   = [sum(revenue[0:3]),  sum(revenue[3:6]),  sum(revenue[6:9]),  sum(revenue[9:12])]
q_exp   = [sum(expenses[0:3]), sum(expenses[3:6]), sum(expenses[6:9]), sum(expenses[9:12])]
q_ebitda= [r * 0.28 for r in q_rev]
q_net   = [r - e for r, e in zip(q_rev, q_exp)]

q_colors = ['2E86AB', '3BB273', 'E84855', 'F18F01']
for i, (q, r, e, eb, n) in enumerate(zip(['Q1','Q2','Q3','Q4'], q_rev, q_exp, q_ebitda, q_net)):
    row = 3 + i
    fill = PatternFill('solid', fgColor='F0F7FF' if i % 2 == 0 else 'FFFFFF')
    c = ws2.cell(row=row, column=1, value=q)
    c.font = Font(bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor=q_colors[i])
    c.alignment = Alignment(horizontal='center')
    c.border = thin_border()
    for col, val in ((2, r), (3, e), (4, eb), (5, n)):
        cell = money(ws2, row, col, val)
        cell.fill = fill

for col, w in zip('ABCDE', [12, 18, 18, 18, 18]):
    ws2.column_dimensions[col].width = w

# ── Sheet 3: KPIs ────────────────────────────────────────────────────────────
ws3 = wb.create_sheet('KPIs')

ws3.merge_cells('A1:E1')
t3 = ws3['A1']
t3.value = 'Key Performance Indicators – Acme Corp 2024'
t3.font = Font(bold=True, size=14, color='FFFFFF')
t3.fill = PatternFill('solid', fgColor='0D2137')
t3.alignment = Alignment(horizontal='center', vertical='center')
ws3.row_dimensions[1].height = 32

apply_header(ws3, 2, ['Metric', 'Q1', 'Q2', 'Q3', 'Q4'])

kpis = [
    ('Gross Margin %',       42.5, 43.1, 44.0, 44.8),
    ('Operating Margin %',   18.2, 19.0, 19.5, 20.3),
    ('ROE %',                12.4, 13.1, 13.8, 14.5),
    ('Current Ratio',         2.1,  2.3,  2.4,  2.6),
    ('Debt-to-Equity',        0.45, 0.42, 0.40, 0.38),
]

green = Font(color='1A7A4A', bold=True)
red   = Font(color='C0392B', bold=True)

for i, (metric, *vals) in enumerate(kpis):
    row = 3 + i
    fill = PatternFill('solid', fgColor='F0F7FF' if i % 2 == 0 else 'FFFFFF')
    c = ws3.cell(row=row, column=1, value=metric)
    c.font = Font(bold=True, size=11)
    c.fill = fill
    c.border = thin_border()
    for j, v in enumerate(vals, 2):
        cell = ws3.cell(row=row, column=j, value=v)
        cell.fill = fill
        cell.border = thin_border()
        cell.alignment = Alignment(horizontal='center')
        # colour-code trends: last Q better than first Q = green
        if j == 5:  # Q4 column
            cell.font = green if vals[-1] >= vals[0] else red
        else:
            cell.font = Font(size=11)
        if metric.endswith('%'):
            cell.number_format = '0.00"%"'
        else:
            cell.number_format = '0.00'

ws3.column_dimensions['A'].width = 22
for col in 'BCDE':
    ws3.column_dimensions[col].width = 14

# ── Save ─────────────────────────────────────────────────────────────────────
path = '/home/user/newm/financial_data.xlsx'
wb.save(path)
print(f'Saved: {path}')

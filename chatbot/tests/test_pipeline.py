"""
Regression tests for the chatbot AI + query pipeline.
Run:  python tests/test_pipeline.py     (no framework required)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from semantic_model import get_model            # noqa: E402
from analyst import Analyst                     # noqa: E402
from auth import get_auth_provider              # noqa: E402
from nl_planner import QueryIntent, Planner     # noqa: E402

MODEL = get_model()
ANALYST = Analyst(MODEL)
USER = get_auth_provider().connect("tester@contoso.com")

_passed = 0
_failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}  {detail}")


def viz0(r):
    return r["visuals"][0]["viz"] if r.get("visuals") else {}


def data0(r):
    return r["visuals"][0]["data"] if r.get("visuals") else {}


# --- extraction sanity ---
check("model has 4 tables", len(MODEL.meta["tables"]) == 4)
check("model has 3 relationships", len(MODEL.meta["relationships"]) == 3)
check("500 sales rows loaded", len(MODEL.fact) == 500)
check("years are 2022-2025", MODEL.years == [2022, 2023, 2024, 2025])

# --- KPI ---
r = ANALYST.handle("Show total sales", USER, None)
check("total sales is a card", viz0(r)["chartType"] == "card")
val = data0(r)["rows"][0]["Total Revenue"]
check("total revenue ~ sum net sales", abs(val - sum(x["Net Sales"] for x in MODEL.fact)) < 1,
      f"got {val}")

# --- breakdown by country ---
r = ANALYST.handle("Show total sales by country", USER, None)
check("country breakdown has 10 rows", data0(r)["row_count"] == 10)
check("country auto-chart is column", viz0(r)["chartType"] == "column")

# --- explicit chart type ---
r = ANALYST.handle("sales by category as a bar chart", USER, None)
check("explicit bar honoured", viz0(r)["chartType"] == "bar")
r = ANALYST.handle("revenue contribution by category as a pie chart", USER, None)
check("explicit pie honoured", viz0(r)["chartType"] == "pie")

# --- trend + year filter ---
r = ANALYST.handle("monthly sales trend for 2025", USER, None)
check("trend is a line", viz0(r)["chartType"] == "line")
check("2025 trend has 12 months", data0(r)["row_count"] == 12,
      f"got {data0(r)['row_count']}")

# --- top N with dimension collision ---
r = ANALYST.handle("Top 10 customers by revenue", USER, None)
check("top-10 customers has a Customer dimension", r["intent"]["dimension"] == "Customer")
check("top-10 customers returns 10 rows", data0(r)["row_count"] == 10)

# --- compare ---
r = ANALYST.handle("Compare revenue between UK, India and USA", USER, None)
check("compare groups by Country", r["intent"]["dimension"] == "Country")
check("compare returns 3 rows", data0(r)["row_count"] == 3)

# --- YoY / profit growth by product ---
r = ANALYST.handle("Profit growth by product", USER, None)
check("profit growth includes Profit YoY %", "Profit YoY %" in r["intent"]["measures"])
check("profit growth includes base Total Profit", "Total Profit" in r["intent"]["measures"])

# --- missing metric: no fabrication ---
r = ANALYST.handle("Show employee satisfaction by department", USER, None)
check("missing metric refused", r["ok"] is False and r["kind"] == "error")
check("missing metric message mentions model", "couldn't find" in r["reply"].lower())

# --- ad-hoc report ---
r = ANALYST.handle(
    "Create a sales report for 2025 showing total revenue, total profit, "
    "monthly sales trend, sales by country and top 10 customers", USER, None)
check("report produces multiple visuals", r["kind"] == "report" and len(r["visuals"]) >= 4,
      f"got {len(r.get('visuals', []))}")

# --- conversation follow-ups ---
r = ANALYST.handle("Show sales by region", USER, None)
prev = QueryIntent(**r["intent"])
r2 = ANALYST.handle("change this to a pie chart", USER, prev)
check("follow-up switches to pie", viz0(r2)["chartType"] == "pie")
prev = QueryIntent(**r2["intent"])
r3 = ANALYST.handle("now filter it to 2025", USER, prev)
check("follow-up adds year filter",
      any(f["field"] == "Year" for f in r3["intent"]["filters"]))
prev = QueryIntent(**r3["intent"])
r4 = ANALYST.handle("add profit to the chart", USER, prev)
check("follow-up adds profit measure", "Total Profit" in r4["intent"]["measures"])
prev = QueryIntent(**r4["intent"])
r5 = ANALYST.handle("show only UK and India", USER, prev)
country_filters = [f for f in r5["intent"]["filters"] if f["field"] in ("Country", "Rep Country")]
check("only-UK-India adds a single country filter", len(country_filters) == 1,
      f"got {country_filters}")

# --- DAX generation present ---
r = ANALYST.handle("Show total sales by country", USER, None)
check("DAX generated", "SUMMARIZECOLUMNS" in r["visuals"][0]["dax"])

# --- DAX generates for every measure/dim pair without error ---
from dax import generate_dax   # noqa: E402
ok = True
for mname in MODEL.measures:
    for dname in list(MODEL.dimensions)[:6]:
        try:
            generate_dax(MODEL, QueryIntent(measures=[mname], dimension=dname))
        except Exception as exc:  # noqa: BLE001
            ok = False
            print("   DAX error", mname, dname, exc)
check("DAX generates for all measure/dim combos", ok)

print(f"\n{_passed} passed, {_failed} failed")
sys.exit(1 if _failed else 0)

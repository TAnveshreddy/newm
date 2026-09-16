"""
Tests for the multi-dataset registry, the generic (model-agnostic) profile, and
report switching.  Run:  python tests/test_datasets.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from semantic_model import get_registry, SemanticModel     # noqa: E402
from analyst import Analyst                                 # noqa: E402
from auth import get_auth_provider                          # noqa: E402
from dax import generate_dax                                # noqa: E402
from nl_planner import QueryIntent                          # noqa: E402

USER = get_auth_provider().connect("tester@hospital.com")
_passed = _failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1; print(f"  PASS  {name}")
    else:
        _failed += 1; print(f"  FAIL  {name}  {detail}")


reg = get_registry()

# --- registry ---
check("registry discovers sales + healthcare", set(reg.ids()) >= {"sales", "healthcare"},
      f"got {reg.ids()}")
check("default dataset is sales", reg.default_id() == "sales")
cat = {d["id"]: d for d in reg.catalog()}
check("catalog lists healthcare with measures", cat.get("healthcare", {}).get("measures", 0) >= 8)

# --- sales model unchanged by the refactor ---
sales = reg.get("sales")
check("sales still profile=sales", sales.profile == "sales")
check("sales fact still 500 rows", len(sales.fact) == 500)
check("sales still has Total Revenue", "Total Revenue" in sales.measures)

# --- healthcare generic model ---
hc = reg.get("healthcare")
check("healthcare profile=generic", hc.profile == "generic")
check("healthcare fact table = Encounters", hc.fact_table == "Encounters")
check("healthcare loaded encounters", len(hc.fact) == 650)
check("healthcare years 2022-2025", hc.years == [2022, 2023, 2024, 2025])
for m in ("Total Charges", "Total Encounters", "Avg Length of Stay", "Readmission Rate %",
          "Charges YoY %"):
    check(f"healthcare has measure '{m}'", m in hc.measures)
for d in ("Department", "Diagnosis", "Provider", "Gender", "Insurance", "Year", "Month"):
    check(f"healthcare has dimension '{d}'", d in hc.dimensions)

# --- healthcare queries run end to end ---
ha = Analyst(hc)


def viz0(r):
    return r["visuals"][0]["viz"] if r.get("visuals") else {}


def data0(r):
    return r["visuals"][0]["data"] if r.get("visuals") else {}


r = ha.handle("total charges by department", USER, None)
check("charges by department -> 8 rows", data0(r)["row_count"] == 8, f"got {data0(r).get('row_count')}")
check("charges is currency-formatted", any(c.get("format") == "currency" for c in viz0(r).get("measures", [])))

r = ha.handle("average length of stay by department as a bar chart", USER, None)
check("LOS explicit bar honoured", viz0(r)["chartType"] == "bar")

r = ha.handle("readmission rate by department", USER, None)
vals = [row.get("Readmission Rate %") for row in data0(r)["rows"] if row.get("Readmission Rate %") is not None]
check("readmission rate is a fraction 0..1", vals and all(0 <= v <= 1 for v in vals), f"got {vals[:3]}")

r = ha.handle("charges growth year over year", USER, None)
check("charges YoY runs", r["ok"] and data0(r)["row_count"] >= 1)

r = ha.handle("create a dashboard showing charges, encounters and length of stay", USER, None)
check("healthcare ad-hoc report has multiple visuals", r["kind"] == "report" and len(r["visuals"]) >= 4,
      f"got {len(r.get('visuals', []))}")

# missing metric on healthcare -> honest refusal
r = ha.handle("show employee satisfaction by department", USER, None)
check("healthcare refuses unknown metric", r["ok"] is False and r["kind"] == "error")

# --- DAX generation for the generic model ---
ok = True
for mname in hc.measures:
    try:
        generate_dax(hc, QueryIntent(measures=[mname], dimension="Department"))
    except Exception as exc:  # noqa: BLE001
        ok = False; print("   DAX error", mname, exc)
check("DAX generates for all healthcare measures", ok)

# --- switching datasets keeps models independent ---
check("sales and healthcare are distinct models", reg.get("sales") is not reg.get("healthcare"))
check("sales measures untouched after loading healthcare", "Total Revenue" in reg.get("sales").measures)

print(f"\n{_passed} passed, {_failed} failed")
sys.exit(1 if _failed else 0)

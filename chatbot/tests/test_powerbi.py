"""
Offline tests for the live Power BI integration.  No tenant required — a mock
client returns recorded-shape JSON so the metadata parsing, catalog building,
result mapping and OAuth URL construction can all be verified.

Run:  python tests/test_powerbi.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import powerbi as pb                                   # noqa: E402
from powerbi import (LiveModel, LiveExecutor, EntraConfig, parse_execute_results,  # noqa: E402
                     strip_col_key, discover_dashboards, map_rows_to_result)
from query_engine import QueryResult                   # noqa: E402
from nl_planner import QueryIntent                     # noqa: E402

_passed = _failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1; print(f"  PASS  {name}")
    else:
        _failed += 1; print(f"  FAIL  {name}  {detail}")


# --- a mock Power BI client -------------------------------------------------
INFO_MEASURES = [
    {"[Name]": "Total Revenue", "[Expression]": "SUM(Sales[Net Sales])",
     "[FormatString]": "\\$#,0", "[Table]": "Sales", "[Description]": "Revenue"},
    {"[Name]": "Profit Margin %", "[Expression]": "DIVIDE([Total Profit],[Total Revenue])",
     "[FormatString]": "0.0%", "[Table]": "Sales", "[Description]": ""},
]
INFO_COLUMNS = [
    {"[Name]": "Country", "[Table]": "Customers", "[DataType]": "String", "[IsHidden]": "False"},
    {"[Name]": "Category", "[Table]": "Sales", "[DataType]": "String", "[IsHidden]": "False"},
    {"[Name]": "Year", "[Table]": "Date", "[DataType]": "Int64", "[IsHidden]": "False"},
    {"[Name]": "Month", "[Table]": "Date", "[DataType]": "String", "[IsHidden]": "False"},
    {"[Name]": "Key", "[Table]": "Sales", "[DataType]": "String", "[IsHidden]": "True"},
]
INFO_RELATIONSHIPS = [
    {"[FromTable]": "Sales", "[FromColumn]": "Customer ID", "[ToTable]": "Customers", "[ToColumn]": "Customer ID"},
    {"[FromTable]": "Sales", "[FromColumn]": "Date", "[ToTable]": "Date", "[ToColumn]": "Date"},
]
INFO_TABLES = [{"[Name]": "Sales"}, {"[Name]": "Customers"}, {"[Name]": "Date"}]


class MockClient:
    def __init__(self):
        self.executed = []

    def execute_dax(self, dataset_id, dax, group_id=None):
        if "INFO.VIEW.MEASURES" in dax:
            return list(INFO_MEASURES)
        if "INFO.VIEW.COLUMNS" in dax:
            return list(INFO_COLUMNS)
        if "INFO.VIEW.RELATIONSHIPS" in dax:
            return list(INFO_RELATIONSHIPS)
        if "INFO.VIEW.TABLES" in dax:
            return list(INFO_TABLES)
        if "VALUES(" in dax and "Country" in dax:
            return [{"Customers[Country]": c} for c in ["UK", "India", "USA"]]
        if "VALUES(" in dax and "Year" in dax:
            return [{"Date[Year]": y} for y in [2024, 2025]]
        # a real grouped query
        self.executed.append(dax)
        return [
            {"Customers[Country]": "USA", "[Total Revenue]": 461917.0},
            {"Customers[Country]": "UK", "[Total Revenue]": 120000.0},
        ]

    def list_workspaces(self):
        return [{"id": "ws1", "name": "Finance"}]

    def list_reports(self, group_id=None):
        if group_id == "ws1":
            return [{"name": "Sales Dashboard", "datasetId": "ds1"},
                    {"name": "Finance Dashboard", "datasetId": "ds2"}]
        return []

    def list_datasets(self, group_id=None):
        if group_id == "ws1":
            return [{"id": "ds1", "name": "SalesModel"}, {"id": "ds3", "name": "ExtraModel"}]
        return []


# --- parser units -----------------------------------------------------------
check("strip_col_key with table", strip_col_key("Customers[Country]") == ("Customers", "Country"))
check("strip_col_key measure", strip_col_key("[Total Revenue]") == (None, "Total Revenue"))
check("parse_execute_results reads rows",
      parse_execute_results({"results": [{"tables": [{"rows": [{"a": 1}]}]}]}) == [{"a": 1}])
check("parse_execute_results empty-safe", parse_execute_results({}) == [])

# --- OAuth URL --------------------------------------------------------------
os.environ["ENTRA_TENANT_ID"] = "tenant-123"
os.environ["ENTRA_CLIENT_ID"] = "client-abc"
os.environ["ENTRA_CLIENT_SECRET"] = "secret-xyz"
cfg = EntraConfig()
url = cfg.authorize_url("state42")
check("authorize URL points at tenant", "tenant-123/oauth2/v2.0/authorize" in url)
check("authorize URL requests code", "response_type=code" in url)
check("authorize URL carries state", "state=state42" in url)
check("authorize URL requests powerbi scope", "powerbi" in url and "Dataset.Read.All" in url)
check("client secret never in authorize URL", "secret-xyz" not in url)

# --- LiveModel from mocked metadata ----------------------------------------
mc = MockClient()
lm = LiveModel(mc, "ds1", "ws1", "Sales Dashboard")
check("live model name", lm.meta["name"] == "Sales Dashboard")
check("live profile", lm.profile == "live")
check("live fact table = Sales", lm.fact_table == "Sales")
check("live measures parsed", "Total Revenue" in lm.measures and "Profit Margin %" in lm.measures)
check("live measure currency format", lm.measures["Total Revenue"].fmt == "currency")
check("live measure percent format", lm.measures["Profit Margin %"].fmt == "percent")
check("live dimension Country present", "Country" in lm.dimensions)
check("live dimension table is Customers", lm.dimensions["Country"].table == "Customers")
check("live hidden column excluded", "Key" not in lm.dimensions)
check("live time dims Year & Month", "Year" in lm.dimensions and "Month" in lm.dimensions)
check("live years discovered", lm.years == [2024, 2025])
check("live distinct values via VALUES", lm.distinct_values("Country") == ["India", "UK", "USA"])

# resolve_terms reuse (semantic awareness) works on the live catalog
res = lm.resolve_terms("show revenue by country")
check("live resolve maps revenue->Total Revenue", "Total Revenue" in res["measures"])
check("live resolve finds Country", "Country" in res["dimensions"])

# --- executor maps executeQueries rows into a QueryResult -------------------
ex = LiveExecutor(lm, mc)
intent = QueryIntent(measures=["Total Revenue"], dimension="Country", intent_kind="breakdown")
result = ex.run(intent).to_dict()
check("executor returns 2 rows", result["row_count"] == 2, f"got {result['row_count']}")
cols = [c["name"] for c in result["columns"]]
check("executor columns are Country + Total Revenue", cols == ["Country", "Total Revenue"], f"got {cols}")
check("executor mapped a value", result["rows"][0]["Total Revenue"] == 461917.0)
check("executor emitted DAX to Power BI", any("SUMMARIZECOLUMNS" in q for q in mc.executed))

# --- discovery for the dropdown --------------------------------------------
dash = discover_dashboards(mc)
names = [d["name"] for d in dash]
check("discovery lists reports as dashboards", "Sales Dashboard" in names and "Finance Dashboard" in names)
check("discovery maps report to dataset", any(d["name"] == "Sales Dashboard" and d["datasetId"] == "ds1" for d in dash))
check("discovery includes report-less dataset", any(d.get("datasetId") == "ds3" for d in dash))
check("discovery nothing hardcoded (all from client)", all(d["groupName"] == "Finance" for d in dash))

# --- full live chat path: planner -> DAX -> LiveExecutor -> viz -------------
from analyst import Analyst                          # noqa: E402
from auth import get_auth_provider                   # noqa: E402

live_analyst = Analyst(lm, executor=LiveExecutor(lm, mc))
user = get_auth_provider().connect("x@y.com")
r = live_analyst.handle("show revenue by country as a bar chart", user, None)
check("live chat ok", r["ok"], f"got {r}")
check("live chat produced a visual", bool(r.get("visuals")))
if r.get("visuals"):
    check("live chat chart honours explicit bar", r["visuals"][0]["viz"]["chartType"] == "bar")
    check("live chat rows mapped", r["visuals"][0]["data"]["row_count"] == 2)
    check("live chat shows the DAX it ran", "SUMMARIZECOLUMNS" in r["visuals"][0]["dax"])

print(f"\n{_passed} passed, {_failed} failed")
sys.exit(1 if _failed else 0)

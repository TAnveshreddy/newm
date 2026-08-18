"""Automated tests for every engine capability (requirement #16)."""
import pandas as pd
import pytest

from ai_report import (
    generate_report,
    load_data,
    profile_dataset,
    to_powerbi_spec,
)
from ai_report import planner, validation
from ai_report.aggregations import evaluate_expression, extract_expression_columns
from ai_report.cleaning import clean_dataframe
from ai_report.dates import parse_dates, parse_or_raise
from ai_report.errors import DateParseError, SchemaError, SemanticError
from ai_report.profiler import profile_all
from ai_report.query_engine import build_result
from ai_report.schema import Filter, ReportPlan, Sort, VisualPlan


# 1 -------------------------------------------------------------------------
def test_column_detection(clean_sales):
    p = profile_dataset(clean_sales, "sales")
    assert p.column("Region").semantic_type == "dimension"
    assert p.column("Revenue").semantic_type == "measure"
    assert p.column("Date").semantic_type == "date"
    assert p.column("CustomerID").semantic_type == "identifier"
    assert "Revenue" in p.measures()
    assert "Region" in p.dimensions()
    assert "Date" in p.date_columns()


# 2 -------------------------------------------------------------------------
def test_data_type_detection(clean_sales):
    p = profile_dataset(clean_sales, "sales")
    assert p.column("Revenue").data_type in ("integer", "float")
    assert p.column("Region").data_type == "categorical"
    assert p.column("Date").data_type in ("date", "datetime")
    assert p.column("CustomerID").data_type == "identifier"


# 3 -------------------------------------------------------------------------
def test_date_parsing():
    s = pd.Series(["2025-01-01", "01/02/2025", "Jan 04 2025", "not-a-date"])
    parsed, invalid = parse_dates(s)
    assert invalid == 1
    assert parsed.notna().sum() == 3
    # a clearly non-date column raises
    with pytest.raises(DateParseError):
        parse_or_raise(pd.Series(["apple", "banana", "cherry"]))


# 4 -------------------------------------------------------------------------
def test_null_handling(messy_sales):
    clean, report = clean_dataframe(messy_sales)
    assert report.rows_received == 6
    assert report.duplicates_removed == 1          # one exact duplicate removed
    assert report.rows_processed == 5
    assert report.null_values >= 2                 # empty Region + null Revenue


# 5 -------------------------------------------------------------------------
def test_multiple_visuals(datasets):
    prompt = ("Create a sales dashboard showing revenue by region, monthly revenue trend, "
              "revenue by category and total revenue")
    result = generate_report(datasets, prompt, render=False)
    assert len(result.plan["visuals"]) >= 3
    assert result.failed == 0
    types = {v["type"] for v in result.plan["visuals"]}
    assert "line" in types and ("bar" in types or "pie" in types)


# 6 -------------------------------------------------------------------------
def test_filters(clean_sales):
    p = profile_dataset(clean_sales, "sales")
    visual = VisualPlan(type="bar", dataset="sales", x="Region", y="Revenue",
                        aggregation="sum",
                        filters=[Filter("Year", "=", 2025), Filter("Region", "=", "North")])
    res = build_result(clean_sales, p, visual)
    assert list(res.df["Region"].unique()) == ["North"]
    # planner also extracts filters from language
    rp = planner.plan_report("Show revenue for 2025", {"sales": p})
    assert any(f.column == "Year" for v in rp.visuals for f in v.filters)


# 7 -------------------------------------------------------------------------
def test_sorting(clean_sales):
    p = profile_dataset(clean_sales, "sales")
    v = VisualPlan(type="bar", dataset="sales", x="Region", y="Revenue",
                   aggregation="sum", sort=Sort("Revenue", "asc"))
    res = build_result(clean_sales, p, v)
    vals = list(res.df["Revenue"])
    assert vals == sorted(vals)


# 8 -------------------------------------------------------------------------
def test_top_n(clean_sales):
    p = profile_dataset(clean_sales, "sales")
    v = VisualPlan(type="bar", dataset="sales", x="Product", y="Revenue",
                   aggregation="sum", limit=2, order="desc", order_by="Revenue")
    res = build_result(clean_sales, p, v)
    assert len(res.df) == 2
    # the two shown are the two largest totals
    full = build_result(clean_sales, p, VisualPlan(type="bar", dataset="sales",
                        x="Product", y="Revenue", aggregation="sum"))
    top2 = set(full.df.nlargest(2, "Revenue")["Product"])
    assert set(res.df["Product"]) == top2


# 9 -------------------------------------------------------------------------
def test_kpi(clean_sales):
    p = profile_dataset(clean_sales, "sales")
    # simple KPI
    v = VisualPlan(type="kpi", dataset="sales", y="Revenue", aggregation="sum")
    res = build_result(clean_sales, p, v)
    from ai_report.kpi import compute_kpi
    assert compute_kpi(res.df, v) == pytest.approx(clean_sales["Revenue"].sum())
    # calculated measure: profit margin
    vm = VisualPlan(type="kpi", dataset="sales", expression="(Revenue - Cost) / Revenue",
                    measure_name="Profit Margin")
    margin = compute_kpi(clean_sales, vm)
    expected = (clean_sales["Revenue"].sum() - clean_sales["Cost"].sum()) / clean_sales["Revenue"].sum()
    assert margin == pytest.approx(expected)


# 10 ------------------------------------------------------------------------
def test_visual_json_validation():
    good = {"title": "t", "visuals": [{"type": "bar", "dataset": "sales",
            "x": "Region", "y": "Revenue", "aggregation": "sum"}]}
    plan = ReportPlan.from_dict(good)
    assert plan.visuals[0].type == "bar"
    with pytest.raises(SchemaError):
        VisualPlan.from_dict({"type": "banana", "dataset": "sales"})
    with pytest.raises(SchemaError):
        ReportPlan.from_dict({"title": "t", "visuals": []})


# 11 ------------------------------------------------------------------------
def test_invalid_column(datasets):
    profiles = profile_all(datasets)
    bad = VisualPlan(type="bar", dataset="sales", x="Region", y="Profit", aggregation="sum")
    with pytest.raises(SemanticError):
        validation.validate_visual(bad, profiles)


# 12 ------------------------------------------------------------------------
def test_invalid_date(messy_sales):
    # A line chart on a column with an unparseable value should still run
    # (invalid rows coerced to NaT), not crash the whole request.
    datasets = {"sales": messy_sales}
    result = generate_report(datasets, "Show monthly revenue trend", render=False)
    assert result.successful + result.failed == len(result.plan["visuals"])
    assert isinstance(result.to_dict(), dict)


# 13 ------------------------------------------------------------------------
def test_visual_error_recovery(datasets):
    # One valid + one invalid visual: valid must succeed, invalid must be reported.
    profiles = profile_all(datasets)
    plan = {"title": "mixed", "visuals": [
        {"type": "bar", "dataset": "sales", "x": "Region", "y": "Revenue", "aggregation": "sum",
         "title": "Good"},
        {"type": "bar", "dataset": "sales", "x": "Region", "y": "DoesNotExist", "aggregation": "sum",
         "title": "Bad"},
    ]}
    from ai_report.report import _run_visual
    from ai_report.schema import ReportPlan as RP
    rp = RP.from_dict(plan)
    results = [_run_visual(i, v, datasets, profiles, None, False) for i, v in enumerate(rp.visuals, 1)]
    ok = [r for r in results if r.ok]
    bad = [r for r in results if not r.ok]
    assert len(ok) == 1 and ok[0].title == "Good"
    assert len(bad) == 1 and "DoesNotExist" in bad[0].error


# extra: powerbi adapter + backward-compat load_data --------------------------
def test_powerbi_spec_and_loading(tmp_path, clean_sales):
    v = VisualPlan(type="bar", dataset="sales", x="Region", y="Revenue", aggregation="sum",
                   title="Revenue by Region")
    spec = to_powerbi_spec(v)
    assert spec["visualType"] == "clusteredBarChart"
    assert spec["category"] == "Region" and spec["aggregation"] == "Sum"

    csv = tmp_path / "sales.csv"
    clean_sales.to_csv(csv, index=False)
    ds = load_data(str(csv))
    assert "sales" in ds and len(ds["sales"]) == len(clean_sales)

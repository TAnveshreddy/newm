# AI Visual / Report Generation Engine (v2)

An upgraded, modular, production-oriented engine that turns a **natural-language
request** into **validated visuals and reports** from CSV/Excel data — following
a safe pipeline:

```
Natural Language → LLM (or offline planner) → Structured JSON
   → Schema Validation → Semantic-Metadata Validation
   → Query / Transformation → Visualization Engine → Visual / Report
```

The LLM only ever produces **validated JSON**, never Python code. Every column
and measure is checked against the dataset's semantic metadata before anything
runs, so the model can never invent fields or execute arbitrary code.

> This is the enhanced version of the original `ai_report.py` prototype. The old
> `load_data(...)` and `execute_visuals(...)` calls still work (backward
> compatible), while everything below is new.

---

## 1. Quick start (runs offline, no API key)

```bash
cd ai-visual-engine
python3 -m pip install -r requirements.txt

# Single visual
python3 ai_report.py --data ./data/sales.csv \
  --prompt "Show revenue by region for 2025 sorted highest to lowest"

# A whole dashboard from one prompt
python3 ai_report.py --data ./data/sales.csv \
  --prompt "Create a sales dashboard showing total revenue, revenue by region, monthly revenue trend and revenue by category"
```

PNGs are written to `./generated_reports/`. Add `--no-render` to get only JSON.

**Using a real LLM (optional):** set environment variables and the planner
switches from the built-in rule parser to the model automatically:

```bash
export LLM_API_KEY=sk-...            # your key (OpenAI, Azure OpenAI, or compatible)
export LLM_MODEL=gpt-4.1             # optional
export LLM_BASE_URL=https://...      # optional, for Azure/compatible endpoints
```

## 1b. Web application (browser chat box)

Prefer a UI over the terminal? A small web app is included: type a question in a
chat box and the charts render on the page.

```bash
cd ai-visual-engine
python3 -m pip install -r requirements.txt
python3 webapp/app.py
# then open http://localhost:8000
```

- Starts on the **sample dataset**; use **Upload CSV / Excel** to switch to your own file.
- One prompt can produce a whole dashboard (KPI + charts) inline.
- Endpoints: `GET /` (page), `POST /api/chat` `{prompt}`, `POST /api/upload` (file),
  `GET /api/info`. The same `ai_report` engine does the work — this only adds the UI.

## 2. Run the tests

```bash
python3 -m pytest ai_report/tests/ -q
# 14 passed
```

---

## 3. Architecture — modules and what each does

```
ai_report/
├── __init__.py          Public API (load_data, generate_report, profile_dataset, …)
├── data_loader.py       Load CSV / Excel / folder into DataFrames (#17 backward compat)
├── profiler.py          Column + data-type + semantic detection; semantic metadata (#1,#2,#12)
├── dates.py             Robust multi-format date parsing + date hierarchy (#3)
├── cleaning.py          Null/empty/duplicate handling with a cleaning report (#4)
├── schema.py            Visual/Report dataclasses + structural JSON validation (#11,#13)
├── validation.py        Semantic validation against metadata (#11,#12,#20)
├── filters.py           Filter operators, applied before aggregation (#6)
├── aggregations.py      Aggregations + safe calculated-measure expressions (#10,#20)
├── kpi.py               KPI + calculated-metric values (#10)
├── hierarchy.py         Drill-down / hierarchy helpers (#9)
├── query_engine.py      filter → date-grain → aggregate → sort → top-N (#6,#7,#8,#9)
├── visuals.py           Matplotlib renderers (PNG preview) (#13)
├── powerbi_adapter.py   VisualPlan → Power BI-compatible spec (#13)
├── report.py            Orchestrator with per-visual error recovery (#14,#15,#20)
├── planner.py           NL → Visual JSON (LLM backend + offline rule backend) (#11,#14)
├── logging_util.py      Structured JSON logging, redacts secrets (#18)
├── errors.py            Typed exceptions used for recovery (#15)
└── tests/               Automated tests for every capability (#16)
```

### What changed vs. the prototype
- **Fixed the line-chart crash** (`errors="ignore"` → robust multi-format parser in `dates.py`).
- **Implemented `filters`, `sort`, `top_n`, `group_by`/hierarchy** (previously defined but ignored).
- **Added automatic column/type/semantic detection** and a **semantic metadata layer**.
- **Added schema + semantic validation** before execution.
- **Added calculated measures** (e.g. Profit Margin) via a **safe expression evaluator** (no `eval`).
- **Added per-visual error recovery** — one failure never aborts the report.
- **Added a Power BI-compatible spec** output alongside PNGs.
- **Split the monolith into modules**; kept `load_data`/`execute_visuals` working.

---

## 4. Example prompts

- `Show revenue by region`
- `Show monthly revenue trend`
- `Compare revenue by product category and show the top 10`
- `Top 5 products by revenue`
- `Show revenue for Electronics category in 2025`
- `Give me total revenue` · `Show profit margin`
- `Create a sales dashboard showing revenue by region, monthly revenue trend, revenue by category and total revenue`

## 5. Example generated **Visual JSON**

Prompt: *"Give me a bar chart showing revenue by region for 2025, sorted highest to lowest."*

```json
{
  "type": "bar",
  "dataset": "sales",
  "x": "Region",
  "y": "Revenue",
  "aggregation": "sum",
  "filters": [{ "column": "Year", "operator": "=", "value": 2025 }],
  "sort": { "column": "Revenue", "direction": "desc" },
  "title": "Revenue by Region - 2025"
}
```

## 6. Example generated **Report JSON** (with Power BI spec + summary)

```json
{
  "request_id": "fb0fe76fa703",
  "title": "2025 Sales Dashboard",
  "successful": 4,
  "failed": 0,
  "errors": [],
  "cleaning": { "sales": { "rows_received": 288, "rows_processed": 288, "null_values": 0, "duplicates_removed": 0 } },
  "plan": {
    "title": "…",
    "visuals": [
      { "type": "kpi",  "dataset": "sales", "y": "Revenue", "aggregation": "sum", "title": "Total Revenue" },
      { "type": "bar",  "dataset": "sales", "x": "Region",  "y": "Revenue", "aggregation": "sum", "title": "Revenue by Region" },
      { "type": "line", "dataset": "sales", "x": "Date", "date_part": "Month", "y": "Revenue", "aggregation": "sum", "title": "Revenue by Date" },
      { "type": "bar",  "dataset": "sales", "x": "Category", "y": "Revenue", "aggregation": "sum", "title": "Revenue by Category" }
    ]
  },
  "visuals": [
    {
      "title": "Revenue by Region", "type": "bar", "ok": true,
      "file": "generated_reports/visual_2_bar.png",
      "powerbi_spec": {
        "visualType": "clusteredBarChart", "category": "Region",
        "measure": "Revenue", "aggregation": "Sum", "filters": []
      }
    }
  ]
}
```

## 7. Programmatic (API) usage

```python
from ai_report import load_data, generate_report

datasets = load_data("data/sales.csv")
result = generate_report(datasets, "Top 5 products by revenue in 2025", output_folder="out")

print(result.summary())          # {successful, failed, errors, ...}
for v in result.visuals:
    print(v.type, v.ok, v.file, v.powerbi_spec)
```

---

## 8. Supported visual types
`bar`, `column`, `line`, `area`, `pie`, `donut`, `scatter`, `histogram`, `kpi`, `table`

## 9. Supported filter operators
`=`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `not in`, `between`, `contains`
(applied **before** aggregation; a `Year` filter works automatically via the date hierarchy)

## 10. Supported aggregations
`sum`, `avg`/`mean`, `min`, `max`, `count`, `distinct_count`
Plus **calculated measures** via safe expressions, e.g. `(Revenue - Cost) / Revenue`.

## 11. Date hierarchy
`Year`, `Quarter`, `Month`, `Week`, `Day` — derived automatically; "monthly"/"yearly"
phrasing picks the grain. Robust parsing of `2025-01-01`, `01/02/2025`, `Jan 04 2025`, etc.

---

## 12. Known limitations
- The **offline rule planner** covers common business phrasing; nuanced or highly
  compound requests are better served by setting `LLM_API_KEY`.
- One visual maps to **one dimension + one measure** (plus filters/sort/top-N).
  Multi-series/stacked grouping is represented in metadata but rendered as a
  single series in the PNG preview.
- Calculated measures support **arithmetic only** (`+ - * /`) over existing
  measures — no arbitrary functions (by design, for safety).
- Renders are **matplotlib PNGs** (preview/prototype). Interactive rendering is a
  frontend concern (see next section).
- Data source is **flat files (CSV/Excel)** — not yet a live Power BI semantic model.

## 13. Recommended next steps for Power BI integration
1. **Swap the data layer:** replace `data_loader` + `query_engine` execution with
   a Power BI connector that runs the validated plan as **DAX** against your
   **semantic model** (via the `executeQueries` REST API or XMLA), so measures
   and **RLS** are honored. The plan/validation/visual layers stay unchanged.
2. **Build metadata from the model:** populate the semantic layer (`profiler`
   output) from the Power BI dataset schema instead of profiling a DataFrame.
3. **Use the Power BI spec:** `powerbi_adapter.to_powerbi_spec()` already emits a
   Power BI-shaped visual spec — feed it to a Power BI embedding / web frontend
   instead of (or alongside) the PNG renderer.
4. **Auth:** acquire tokens server-side (managed identity / service principal or
   delegated user) — never in the browser.

---

## 14. Deliverables checklist (from the enhancement spec)
Updated source ✓ · module explanations ✓ (§3) · example prompts ✓ (§4) · example
Visual JSON ✓ (§5) · example Report JSON ✓ (§6) · unit tests ✓ (`ai_report/tests`)
· sample CSV ✓ (`data/sales.csv`) · run instructions ✓ (§1) · CLI/API usage ✓
(§1, §7) · visual types ✓ (§8) · filters ✓ (§9) · aggregations ✓ (§10) · known
limitations ✓ (§12) · Power BI next steps ✓ (§13).

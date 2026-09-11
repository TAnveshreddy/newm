# Power BI AI Analyst — Natural-Language Reporting Chatbot

An AI chatbot that lets business users generate ad-hoc Power BI-style reports and
visualizations in plain English — no Power BI, DAX or SQL knowledge required.

> **Ask → Understand → Query Power BI → Analyze → Visualize → Explain → Modify**

You type *“Create a dashboard showing sales, profit, quantity and YoY growth”* and
the assistant interprets the intent, maps your words to the semantic model,
generates the DAX, runs it, picks the right charts, renders them, and explains the
result — then lets you refine everything conversationally.

---

## What this build contains

This is a **runnable, self-contained implementation** of the chatbot. Because a
sandbox has no live Microsoft Entra tenant or Power BI dataset, it runs against
the **real semantic model extracted from `SalesAnalytics_Complete.pbit`** (the
`.pbit` in the repo root) — the same tables, columns, measures and relationships.
The live-tenant path (Entra ID sign-in + Power BI REST/XMLA) is implemented as a
**documented, swappable adapter**, so going to production is a configuration
change, not a rewrite.

| Requirement (from the brief) | Where it lives |
|---|---|
| Connect to a Power BI semantic model / dataset | `backend/semantic_model.py`, `scripts/extract_from_pbit.py` |
| NL understanding & business intent | `backend/nl_planner.py` (rule-based **+ optional Claude**) |
| Map user terms → model fields (synonyms) | `data/semantic_model.json`, `SemanticModel.resolve_terms` |
| Identify tables/columns/measures/filters/dates/aggregations | `backend/nl_planner.py` → `QueryIntent` |
| Generate DAX / query | `backend/dax.py` (SUMMARIZECOLUMNS / TOPN / EVALUATE) |
| Execute the query, analyze data | `backend/query_engine.py` |
| Auto-select the visualization | `backend/viz.py` |
| Dynamic visualizations (bar, line, pie, KPI, table, …) | `frontend/app.js` (Chart.js) |
| Conversational report modification | `backend/nl_planner.py` `modify()`, session context in `backend/app.py` |
| Ad-hoc multi-visual reports from one prompt | `backend/analyst.py` `_handle_report` |
| Business KPIs incl. **YoY sales & profit growth by product** | `SemanticModel._build_measures`, `query_engine` YoY logic |
| Error handling / no fabrication | `backend/analyst.py`, missing-metric guard in planner |
| Microsoft Entra ID auth, RLS, secure token handling | `backend/auth.py` (see **Going live**) |
| Modern responsive chat UI | `frontend/` |

---

## Quick start

```bash
cd chatbot
python3 backend/app.py            # no dependencies to install
# open http://127.0.0.1:8000
```

Sign in with any work-style email (e.g. `you@company.com`) — this simulates the
post-Entra state. Then try:

- `Show total sales by country`
- `Create a monthly sales trend for 2025`
- `Top 10 customers by revenue`
- `Profit growth by product` → then `change this to a bar chart`, `filter to 2025`
- `Compare revenue between UK, India and USA`
- `Create a dashboard showing sales, profit, quantity and YoY growth`

Run the tests:

```bash
python3 tests/test_pipeline.py     # 27 checks, no framework needed
```

Regenerate the data/metadata from the `.pbit` at any time:

```bash
python3 scripts/extract_from_pbit.py ../SalesAnalytics_Complete.pbit
```

---

## Architecture

```
                 Browser (frontend/)                         Backend (backend/)
  ┌───────────────────────────────────┐        ┌────────────────────────────────────────┐
  │ Connect to Power BI (Entra sign-in)│        │ app.py         HTTP API + sessions       │
  │ Chat UI · Chart.js · KPI/table     │  HTTPS │ auth.py        Entra/RLS + PBI executor  │
  │ Per-visual actions · DAX viewer    │◀──────▶│ analyst.py     orchestrator (the analyst)│
  └───────────────────────────────────┘        │ nl_planner.py  NL → QueryIntent (AI)     │
                                                │ dax.py         QueryIntent → DAX         │
                                                │ query_engine.py execute → rows           │
                                                │ viz.py         choose visualization      │
                                                │ semantic_model.py  model + data          │
                                                └────────────────────────────────────────┘
                                                                │
                                        demo: extracted model   │  live: Power BI dataset
                                        (data/*.csv)            ▼  (XMLA / REST executeQueries)
```

**The AI layer** (`nl_planner.py`) has two interchangeable planners that emit the
identical `QueryIntent`:

- **Rule planner** — a deterministic semantic parser over the model's field
  catalog and synonym dictionary. Always on, no key, no network.
- **Claude planner** — engaged automatically when `ANTHROPIC_API_KEY` is set. The
  model catalog is passed in the prompt so Claude can only reference real fields;
  its JSON is validated and the rule planner backfills anything missing. Falls
  back to the rule planner on any error.

Because both produce the same structured intent, DAX generation, execution and
visualization never care which planner ran.

---

## Semantic-model awareness (no column guessing)

The backend hands the AI real metadata — tables, columns, measures,
relationships, plus **synonyms** and **business definitions** — so everyday
language maps to the model:

- *“revenue”, “sales”, “turnover”* → `Total Revenue` (`SUM(Sales[Net Sales])`)
- *“profit growth”, “profit YoY”* → `Profit YoY %`
- *“country”, “region”, “geography”* → `Customers[Country]` (joined via the model relationship)

If you ask for something the model doesn’t contain, the assistant refuses instead
of inventing data:

> *“Show employee satisfaction by department”* →
> “I couldn’t find an **employee/customer satisfaction** field or measure in the
> connected Power BI model. … Please try another metric.”

### Business KPIs (built in)

Core: Total Revenue, Total Profit, Profit Margin %, Total Orders, Total Quantity,
Total Customers, Avg Order Value, Return Rate %, Discount Rate %, Avg Selling
Price, Target Achievement %.
Time-intelligence: **Revenue YoY %**, **Profit YoY %**, Quantity YoY % — computed
against the prior year (the engine looks past a Year filter so the comparison is
available). Sliced by `Product` these give **profit growth by product**; by
`Country`/`Category`/month they give YoY trends.

---

## Conversational modification

The session keeps the current visual so follow-ups refine it:

| You say | Effect |
|---|---|
| “Show sales by region” | column chart of revenue by country |
| “Change this to a pie chart” | same data, pie |
| “Now filter it to 2025” | adds a Year = 2025 filter |
| “Add profit to the chart” | adds the Total Profit measure |
| “Show only UK and India” | filters the country dimension |
| “Make it a table” | switches to a supporting table |

Each visual also has UI actions: change chart type, view the generated DAX,
export to CSV, and expand.

---

## Visualizations

Rendered with Chart.js (bundled locally in `frontend/vendor/`, so the app works
offline): **column, bar, stacked bar/column, line, area, pie, donut, combo,
scatter, KPI cards, table, matrix**. If no chart type is specified the assistant
auto-selects one from the data shape and question (time → line, few categories →
column, part-of-whole → donut, many rows → table, ranking → bar). Chart types not
natively drawn by Chart.js (gauge/funnel/waterfall/treemap/map) fall back to the
closest supported visual or a table, clearly noted.

---

## Security & going live

The demo never asks the user for a Power BI username/password, API key, access
token, client secret, dataset id or workspace id — and never sends any secret to
the browser. The session token is an opaque server-issued id.

**To connect a real tenant** (`backend/auth.py`):

1. Register an app in **Microsoft Entra ID**; grant Power BI **delegated**
   permissions (`Dataset.Read.All`, `Report.Read.All`).
2. `pip install -r requirements.txt` (uncomment `msal`, `requests`).
3. Set env: `POWERBI_MODE=live`, `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`,
   `ENTRA_CLIENT_SECRET` (or use device-code / auth-code flow).
4. The frontend redirects the user to the Microsoft authorize endpoint; the
   backend exchanges the code for a **Power BI access token for that user** and
   discovers the workspaces/datasets they may see.
5. `PowerBIExecutor` runs the generated DAX via
   `POST /v1.0/myorg/datasets/{id}/executeQueries` **as the user**, so
   **Row-Level Security defined in the model is enforced by Power BI**.

Other production notes: serve over HTTPS behind your gateway; store the session
server-side (Redis) instead of in-memory; add audit logging of prompt → DAX →
dataset per user; the `RLS_RULES` hook in `auth.py` shows how to emulate RLS in
the demo.

---

## Project layout

```
chatbot/
  backend/
    app.py            HTTP API + static server + session store
    semantic_model.py model metadata + data + synonym resolution
    nl_planner.py     NL → QueryIntent  (rule-based + optional Claude)
    dax.py            QueryIntent → DAX
    query_engine.py   execute intent → rows (incl. YoY time-intelligence)
    viz.py            choose + configure the visualization
    analyst.py        orchestrator (single visual + ad-hoc reports)
    auth.py           Entra/demo auth, RLS, Power BI executor adapter
  frontend/
    index.html, styles.css, app.js, vendor/chart.umd.min.js
  data/               extracted from the .pbit (CSV + semantic_model.json)
  scripts/extract_from_pbit.py
  tests/test_pipeline.py
```

## Environment variables

| Var | Default | Meaning |
|---|---|---|
| `PORT` / `HOST` | `8000` / `127.0.0.1` | where the server listens |
| `ANTHROPIC_API_KEY` | *(unset)* | enables the Claude planner |
| `CHATBOT_LLM_MODEL` | `claude-sonnet-5` | model id for the Claude planner |
| `POWERBI_MODE` | `demo` | `live` switches to Entra + Power BI REST |

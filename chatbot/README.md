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
| Microsoft Entra ID auth, list live workspaces/datasets, live DAX execution, RLS | `backend/powerbi.py` (see **Live Power BI Service mode**) |
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

## Live Power BI Service mode (connect to your real dashboards)

Set `POWERBI_MODE=live` to connect the chatbot to the **live Power BI Service**
instead of the bundled demo data. This satisfies the "connect to existing
production dashboards" requirement:

**Flow**
1. The user clicks **Sign in with Microsoft** → Entra ID OAuth2 authorization-code
   flow (`/api/auth/login` → Microsoft → `/api/auth/callback`). No API key, token,
   client secret, dataset id or Power BI credential is ever requested from or shown
   to the user; the access/refresh tokens live only server-side.
2. The chatbot calls the Power BI REST API **as the user** to list the workspaces,
   reports and datasets they're authorized to see, and shows them in a
   **Select Power BI Dashboard** dropdown — nothing hardcoded (`/api/workspaces`).
3. On selection (`/api/select-live`) it reads that dataset's **own** tables,
   columns, measures and relationships via the `INFO.VIEW.*` DAX functions and
   builds the catalog from them — so the NL→DAX layer uses the real semantic model.
4. Every question generates DAX and runs it against the **live dataset** via the
   REST `executeQueries` endpoint **as the signed-in user**, so the model's
   **Row-Level Security is enforced by Power BI**. No local copy of the data is used.
5. Switching dashboards (the sidebar picker) disconnects the previous one, loads
   the new dataset's model, and resets the conversation.

**Two live sign-in styles**

- `POWERBI_MODE=live` — each user signs in with Microsoft (one click, no keys
  typed); queries run as that user (per-user permissions/RLS).
- `POWERBI_MODE=service` — a **Service Principal**: the chatbot uses one registered
  app identity, so users just click **Connect** with no login at all. Best when a
  single service account should reach the dashboards. Extra prerequisites: in the
  Power BI admin portal enable **"Allow service principals to use Power BI APIs"**,
  and **add the service principal as a member** of each workspace whose dashboards
  it should see. (Per-user RLS is not automatic in this mode.)

**One-time setup (your side)**
1. Register an app in **Microsoft Entra ID**. Add a **Web** redirect URI matching
   `ENTRA_REDIRECT_URI` (default `http://localhost:8000/api/auth/callback`).
2. Grant **delegated** Power BI permissions: `Dataset.Read.All`, `Report.Read.All`,
   `Workspace.Read.All` (grant admin consent). In the Power BI admin/tenant
   settings, allow service principals / REST APIs as your org requires.
3. Run with:
   ```bash
   export POWERBI_MODE=live
   export ENTRA_TENANT_ID=<tenant-guid>
   export ENTRA_CLIENT_ID=<app-client-id>
   export ENTRA_CLIENT_SECRET=<app-secret>
   export ENTRA_REDIRECT_URI=https://your-host/api/auth/callback
   python3 backend/app.py
   ```
   Serve over HTTPS in production and store sessions in a shared store (e.g. Redis)
   instead of memory.

> Note: `executeQueries` requires the dataset to allow it (XMLA read / "Dataset
> Execute Queries REST API" tenant setting; Premium/PPU or a supported capacity).
> The live path is implemented and unit-tested against recorded API shapes, but a
> live tenant is required to validate end-to-end — it cannot be exercised from a
> sandbox.

## Multiple reports — the report picker (demo / file mode)

The chatbot can hold several reports and switch between them from the UI
(sidebar → **Switch report**). Two ship out of the box:

| Report | Profile | What it is |
|---|---|---|
| **SalesAnalytics** (default) | `sales` | the original hand-tuned sales model |
| **HospitalAnalytics** | `generic` | a synthetic healthcare model (encounters, charges, length of stay, readmissions) — demonstrates loading a *different* schema |

Switching reloads that report's measures, dimensions, suggested prompts and
tables, and starts a fresh conversation. Each report is independent.

**How a report is discovered:** any folder with a `semantic_model.json` (+ its
CSVs) is a report — the built-in `data/` folder (id `sales`) plus every subfolder
of `datasets/`. See `backend/semantic_model.py` → `DatasetRegistry`.

**Add your own report** from any `.pbit` — no code changes:

```bash
python scripts/extract_from_pbit.py C:\path\to\your.pbit --dataset myreport
```

That writes `datasets/myreport/` with `profile: "generic"`, so the chatbot builds
the catalog from *that model's own metadata*: measures are parsed from the model's
DAX (`SUM`/`AVERAGE`/`COUNTROWS`/`DISTINCTCOUNT`), dimensions from the relationship
graph, and time-intelligence from the fact's date column. Restart the server and it
appears in the picker. (Measures whose DAX is too complex to parse are simply not
offered rather than guessed.)

To regenerate the healthcare sample: `python scripts/make_healthcare_dataset.py`.

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

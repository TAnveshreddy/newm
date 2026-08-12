# VCB Power BI — Requirements Analysis & Data-Availability Mapping

Analysis of the **VCB Blending Potential and KPI Dashboards Functional Design Document (v1.0)**
against the four supplied Excel data files, to determine what can be built and where data is missing.

## Deliverable
`VCB_PowerBI_Requirements_Analysis.xlsx` — 6 sheets:

| Sheet | Contents |
|-------|----------|
| 1. Overview | Scope, method, legend, and the Kittyhawk truncation note |
| 2. Report Inventory | The 7 dashboards (4 Visibility + 2 KPI + 1 placeholder) — group, cadence, purpose, KPIs, slicers, sources |
| 3. Data Source Availability | Every FDD source system vs. what was supplied in the four Excel files |
| 4. Report-Data Mapping | **Main deliverable** — report-wise field mapping (Report / KPIs / Required Columns / Slicers / Data Available / Source Excel Sheet / Missing Data & Remarks) |
| 5. KPI Data Availability | Each KPI/metric flagged as computable (Yes) / partial / **NOT computable (No)** from supplied data |
| 6. Data Gaps & Remarks | Consolidated gaps, missing sources and data-quality issues with severity + recommended action |

## Number of Power BI reports
**7 planned** — Refinery-Wide, Blending Potential, Distillate, Supply (Visibility, daily);
Gasoline KPI, Distillate KPI (KPI, weekly/monthly); + 1 reserved placeholder. 6 are fully specified in the FDD.

## Supplied data files
- **APS_Data.xlsm** — `_EVENT` schedule (Event Type 15) for Canton, Catlettsburg, Detroit. *Robinson APS missing.*
- **Lims_data.xlsx** — refinery certified quality (all 4 refineries), stored by ASTM method code.
- **PI_Data.xlsm** — PIAF blend-component tag mapping (Butane/Transmix/Ethanol) + tank service + terminal master.
- **Kittyhawk_data.xlsm** — **received truncated**; table names/column counts recovered, cell text not readable.

## Key findings
- **21 of 30 dashboard KPIs cannot be computed** from the supplied data — chiefly the value-loss / QGA /
  give-away KPIs, which require **MPR pricing** and **PQ spec limits**, neither of which was supplied.
- Missing sources: **PQ Core** (terminal/post-blend quality), **MPR** (pricing), **PQ Spec Shop** (spec/targets),
  **Towworks** (barge movements).
- **LIMS** quality is present but needs the sample-point → tag mapping file to attach properties to batches.
- **Kittyhawk** should be re-supplied intact to confirm columns and load transfer/movement/inventory data.

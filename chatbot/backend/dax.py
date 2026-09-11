"""
dax.py
------
Generate the Power BI / DAX query that corresponds to a ``QueryIntent``.

In the demo the query is executed by the in-memory ``query_engine`` against the
extracted data, but the DAX is generated for two real reasons:

  * Transparency – the chatbot shows the user exactly what query would run
    against the Power BI semantic model (a real "AI BI analyst" shows its work).
  * Portability – when the ``PowerBIExecutor`` adapter is pointed at a live XMLA
    endpoint, this same DAX is the string that gets executed.

The generated DAX targets ``SUMMARIZECOLUMNS`` / ``EVALUATE`` which is what the
Power BI engine uses for visual queries.
"""
from __future__ import annotations

from semantic_model import SemanticModel
from nl_planner import QueryIntent


def _q(table: str, col: str) -> str:
    return f"'{table}'[{col}]"


def _filter_clause(model: SemanticModel, f: dict) -> str:
    field = f["field"]
    values = f.get("values", [])
    if field == "Year":
        col = _q("Sales", "Year")
        vals = ", ".join(str(int(v)) for v in values)
        return f"FILTER(ALL({col}), {col} IN {{{vals}}})"
    dim = model.dimensions.get(field)
    if not dim:
        return ""
    col = _q(dim.table, dim.source_column)
    vals = ", ".join(f'"{v}"' for v in values)
    return f"FILTER(ALL({col}), {col} IN {{{vals}}})"


def generate_dax(model: SemanticModel, intent: QueryIntent) -> str:
    if intent.is_report:
        blocks = []
        for i, spec in enumerate(intent.report_specs, 1):
            sub = _spec_to_intent(spec)
            blocks.append(f"-- Visual {i}: {spec.get('title', spec.get('kind'))}\n"
                          + generate_dax(model, sub))
        return "\n\n".join(blocks)

    measures = intent.measures or ["Total Revenue"]
    measure_defs = []
    for mname in measures:
        meas = model.measures.get(mname)
        if not meas:
            continue
        expr = meas.dax if meas.kind != "derived" else meas.dax
        measure_defs.append(f'    "{mname}", [{mname}]')

    filters = [c for c in (_filter_clause(model, f) for f in intent.filters) if c]

    # KPI: no grouping
    if not intent.dimension:
        inner = ",\n".join(measure_defs)
        base = f"EVALUATE\nROW(\n{inner}\n)"
        if filters:
            base = "EVALUATE\nCALCULATETABLE(\n    ROW(\n" + inner + "\n    ),\n    " + \
                   ",\n    ".join(filters) + "\n)"
        return base

    # Grouped
    group_cols = []
    for d in (intent.dimension, intent.secondary_dimension):
        if not d:
            continue
        dim = model.dimensions[d]
        group_cols.append(_q(dim.table, dim.source_column))
    group_txt = ",\n    ".join(group_cols)
    measure_txt = ",\n    ".join(f'"{m}", [{m}]' for m in measures)

    if filters:
        filt_txt = ",\n    ".join(filters)
        dax = (f"EVALUATE\nTOPN_PLACEHOLDER"
               f"SUMMARIZECOLUMNS(\n    {group_txt},\n    {filt_txt},\n    {measure_txt}\n)")
    else:
        dax = f"EVALUATE\nTOPN_PLACEHOLDER" \
              f"SUMMARIZECOLUMNS(\n    {group_txt},\n    {measure_txt}\n)"

    order_measure = measures[0]
    order = f'\nORDER BY [{order_measure}] {"DESC" if intent.sort_desc else "ASC"}'

    if intent.top_n:
        n = abs(intent.top_n)
        desc = "DESC" if intent.top_n > 0 else "ASC"
        summarize = dax.replace("EVALUATE\nTOPN_PLACEHOLDER", "")
        dax = (f"EVALUATE\nTOPN(\n    {n},\n    " +
               summarize.replace("\n", "\n    ") +
               f",\n    [{order_measure}], {desc}\n)")
        return dax + order
    else:
        dax = dax.replace("TOPN_PLACEHOLDER", "")
        return dax + order


def _spec_to_intent(spec: dict) -> QueryIntent:
    return QueryIntent(
        measures=spec.get("measures", ["Total Revenue"]),
        dimension=spec.get("dimension"),
        time_grain=spec.get("time_grain"),
        top_n=spec.get("top_n"),
        filters=spec.get("filters", []),
        chart_type=spec.get("chart"),
        intent_kind=spec.get("kind", "breakdown"),
    )

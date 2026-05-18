#!/usr/bin/env python3
"""
generate_enhanced_pbix.py
Generates an enhanced Power BI PBIX file with 4 business KPI report pages.
Uses only Python stdlib.
"""

import zipfile
import json
import uuid
import os
import shutil

# ── paths ──────────────────────────────────────────────────────────────────────
SOURCE_PBIX  = "/root/.claude/uploads/981e5159-96ae-47ea-aa63-e6ef6347afef/2e8e1704-make1.pbix"
OUTPUT_PBIX  = "/home/user/newm/make1_enhanced.pbix"
DAX_FILE     = "/home/user/newm/kpi_measures.dax"
REL_FILE     = "/home/user/newm/relationships.json"

# ── helpers ────────────────────────────────────────────────────────────────────

def new_name() -> str:
    """Return a 20-character hex visual name derived from a UUID."""
    return uuid.uuid4().hex[:20]


def js(obj) -> str:
    """Compact JSON string (no extra spaces)."""
    return json.dumps(obj, separators=(',', ':'))


# ── query helpers ──────────────────────────────────────────────────────────────

def col_ref(source_alias: str, prop: str, table: str) -> dict:
    """Build a Column select item for a prototypeQuery / query."""
    return {
        "Column": {
            "Expression": {"SourceRef": {"Source": source_alias}},
            "Property": prop
        },
        "Name": f"{table}.{prop}",
        "NativeReferenceName": prop
    }


def agg_ref(source_alias: str, prop: str, table: str,
            func: int = 0, label: str = None) -> dict:
    """Build an Aggregation select item.  func: 0=Sum,1=Avg,2=Min,3=Max,5=CountNonNull."""
    func_names = {0: "Sum", 1: "Avg", 2: "Min", 3: "Max", 5: "CountNonNull"}
    fn = func_names.get(func, "Sum")
    native = label or f"{fn} of {prop}"
    return {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": source_alias}},
                    "Property": prop
                }
            },
            "Function": func
        },
        "Name": f"{fn}({table}.{prop})",
        "NativeReferenceName": native
    }


def make_from(alias: str, entity: str) -> dict:
    return {"Name": alias, "Entity": entity, "Type": 0}


def make_prototype_query(frm: list, selects: list, order_by: list = None) -> dict:
    q = {"Version": 2, "From": frm, "Select": selects}
    if order_by:
        q["OrderBy"] = order_by
    return q


def make_query_cmd(proto_query: dict, projections_count: int) -> str:
    """Wrap a prototypeQuery into the Commands JSON string used in VC.query."""
    binding = {
        "Primary": {"Groupings": [{"Projections": list(range(projections_count))}]},
        "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
        "Version": 1
    }
    cmd = {
        "Commands": [{
            "SemanticQueryDataShapeCommand": {
                "Query": proto_query,
                "Binding": binding,
                "ExecutionMetricsKind": 1
            }
        }]
    }
    return js(cmd)


def make_data_transforms(category_refs: list, y_refs: list, selects_meta: list) -> str:
    """Build dataTransforms JSON string."""
    cat_proj   = list(range(len(category_refs)))
    y_proj     = list(range(len(category_refs), len(category_refs) + len(y_refs)))
    proj_order = {}
    if category_refs:
        proj_order["Category"] = cat_proj
    if y_refs:
        proj_order["Y"] = y_proj

    proj_active = {}
    if category_refs:
        proj_active["Category"] = [{"queryRef": r, "suppressConcat": False}
                                   for r in category_refs]

    data_roles = []
    for r in category_refs:
        data_roles.append({"Name": "Category", "Projection": category_refs.index(r),
                            "isActive": True})
    for r in y_refs:
        data_roles.append({"Name": "Y",
                            "Projection": len(category_refs) + y_refs.index(r),
                            "isActive": False})

    dt = {
        "projectionOrdering": proj_order,
        "projectionActiveItems": proj_active,
        "queryMetadata": {"Select": selects_meta},
        "visualElements": [{"DataRoles": data_roles}],
        "selects": selects_meta  # simplified; full form would include type info
    }
    return js(dt)


def make_data_transforms_full(category_col_info: list, y_agg_info: list) -> str:
    """
    category_col_info: list of (queryRef, displayName, entity, prop)
    y_agg_info:        list of (queryRef, displayName, entity, prop, func)
    """
    proj_order = {}
    proj_active = {}
    query_meta_selects = []
    visual_data_roles = []
    selects = []

    idx = 0
    cat_indices = []
    for (qref, disp, entity, prop) in category_col_info:
        proj_order.setdefault("Category", []).append(idx)
        proj_active.setdefault("Category", []).append({
            "queryRef": qref, "suppressConcat": False})
        query_meta_selects.append({"Restatement": disp, "Name": qref, "Type": 2048})
        visual_data_roles.append({"Name": "Category", "Projection": idx, "isActive": True})
        selects.append({
            "displayName": disp, "queryName": qref,
            "roles": {"Category": True},
            "type": {"category": None, "underlyingType": 1},
            "expr": {"Column": {
                "Expression": {"SourceRef": {"Entity": entity}},
                "Property": prop}}
        })
        cat_indices.append(idx)
        idx += 1

    for (qref, disp, entity, prop, func) in y_agg_info:
        proj_order.setdefault("Y", []).append(idx)
        query_meta_selects.append({"Restatement": disp, "Name": qref, "Type": 3})
        visual_data_roles.append({"Name": "Y", "Projection": idx, "isActive": False})
        selects.append({
            "displayName": disp, "queryName": qref,
            "roles": {"Y": True},
            "sort": 2, "sortOrder": 0,
            "type": {"category": None, "underlyingType": 260},
            "expr": {"Aggregation": {
                "Expression": {"Column": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": prop}},
                "Function": func}}
        })
        idx += 1

    dt = {
        "projectionOrdering": proj_order,
        "projectionActiveItems": proj_active,
        "queryMetadata": {"Select": query_meta_selects},
        "visualElements": [{"DataRoles": visual_data_roles}],
        "selects": selects
    }
    return js(dt)


# ── visual container builders ──────────────────────────────────────────────────

def make_card_vc(x, y, z, w, h, tab_order,
                 table: str, agg_col: str, agg_func: int,
                 display_name: str = None) -> dict:
    """Build a KPI card visual container."""
    alias = table[0].lower()
    func_names = {0: "Sum", 1: "Avg", 2: "Min", 3: "Max", 5: "CountNonNull"}
    fn = func_names.get(agg_func, "Sum")
    disp = display_name or f"{fn} of {agg_col}"
    qref = f"{fn}({table}.{agg_col})"

    frm = [make_from(alias, table)]
    sel = [agg_ref(alias, agg_col, table, agg_func, disp)]
    proto = make_prototype_query(frm, sel)

    config = {
        "name": new_name(),
        "layouts": [{"id": 0, "position": {
            "x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab_order}}],
        "singleVisual": {
            "visualType": "card",
            "projections": {"Values": [{"queryRef": qref}]},
            "prototypeQuery": proto,
            "drillFilterOtherVisuals": True
        }
    }

    query_binding = {
        "Commands": [{
            "SemanticQueryDataShapeCommand": {
                "Query": proto,
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": [0]}]},
                    "DataReduction": {"DataVolume": 3, "Primary": {"Top": {"Count": 1}}},
                    "Version": 1
                },
                "ExecutionMetricsKind": 1
            }
        }]
    }

    dt = {
        "projectionOrdering": {"Values": [0]},
        "queryMetadata": {"Select": [{"Restatement": disp, "Name": qref, "Type": 3}]},
        "visualElements": [{"DataRoles": [{"Name": "Values", "Projection": 0, "isActive": False}]}],
        "selects": [{
            "displayName": disp, "queryName": qref,
            "roles": {"Values": True},
            "type": {"category": None, "underlyingType": 260},
            "expr": {"Aggregation": {
                "Expression": {"Column": {
                    "Expression": {"SourceRef": {"Entity": table}},
                    "Property": agg_col}},
                "Function": agg_func}}
        }]
    }

    return {
        "x": x, "y": y, "z": z, "width": w, "height": h,
        "config": js(config),
        "filters": "[]",
        "query": js(query_binding),
        "dataTransforms": js(dt),
        "tabOrder": tab_order
    }


def make_bar_chart_vc(x, y, z, w, h, tab_order,
                      cat_table: str, cat_col: str,
                      val_table: str, val_col: str,
                      agg_func: int = 0,
                      visual_type: str = "clusteredBarChart") -> dict:
    """Build a bar/column chart visual container."""
    cat_alias = cat_table[0].lower()
    val_alias = val_table[0].lower()
    if cat_alias == val_alias and cat_table != val_table:
        val_alias = val_table[:2].lower()

    func_names = {0: "Sum", 1: "Avg", 2: "Min", 3: "Max", 5: "CountNonNull"}
    fn = func_names.get(agg_func, "Sum")
    cat_qref = f"{cat_table}.{cat_col}"
    val_qref = f"{fn}({val_table}.{val_col})"
    val_disp = f"{fn} of {val_col}"

    frm = [make_from(cat_alias, cat_table)]
    if val_table != cat_table:
        frm.append(make_from(val_alias, val_table))

    v_alias = val_alias if val_table != cat_table else cat_alias
    sel = [
        col_ref(cat_alias, cat_col, cat_table),
        agg_ref(v_alias, val_col, val_table, agg_func, val_disp)
    ]
    proto = make_prototype_query(frm, sel,
        order_by=[{"Direction": 2, "Expression": sel[1]["Aggregation"]
                   if "Aggregation" in sel[1] else sel[1]}])

    # fix: build OrderBy using just the agg expression
    order_expr = {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": v_alias}},
                    "Property": val_col
                }
            },
            "Function": agg_func
        }
    }
    proto["OrderBy"] = [{"Direction": 2, "Expression": order_expr}]

    config = {
        "name": new_name(),
        "layouts": [{"id": 0, "position": {
            "x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab_order}}],
        "singleVisual": {
            "visualType": visual_type,
            "projections": {
                "Category": [{"queryRef": cat_qref, "active": True}],
                "Y": [{"queryRef": val_qref}]
            },
            "prototypeQuery": proto,
            "drillFilterOtherVisuals": True,
            "hasDefaultSort": True
        }
    }

    query_binding = {
        "Commands": [{
            "SemanticQueryDataShapeCommand": {
                "Query": proto,
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": [0, 1]}]},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                    "Version": 1
                },
                "ExecutionMetricsKind": 1
            }
        }]
    }

    cat_info = [(cat_qref, cat_col, cat_table, cat_col)]
    y_info   = [(val_qref, val_disp, val_table, val_col, agg_func)]
    dt_str   = make_data_transforms_full(cat_info, y_info)

    return {
        "x": x, "y": y, "z": z, "width": w, "height": h,
        "config": js(config),
        "filters": "[]",
        "query": js(query_binding),
        "dataTransforms": dt_str,
        "tabOrder": tab_order
    }


def make_line_chart_vc(x, y, z, w, h, tab_order,
                       cat_table: str, cat_col: str,
                       val_table: str, val_col: str,
                       agg_func: int = 0) -> dict:
    """Build a line chart visual container."""
    return make_bar_chart_vc(x, y, z, w, h, tab_order,
                             cat_table, cat_col, val_table, val_col,
                             agg_func, visual_type="lineChart")


def make_table_vc(x, y, z, w, h, tab_order,
                  columns: list) -> dict:
    """
    Build a table (tableEx) visual container.
    columns: list of dicts with keys: table, col, agg (None=column, 0/5/etc=aggregation)
    """
    frm_map = {}
    for c in columns:
        t = c["table"]
        if t not in frm_map:
            alias = t[0].lower()
            # ensure unique alias
            used = set(frm_map.values())
            if alias in used:
                alias = t[:2].lower()
            while alias in used:
                alias = alias + "_"
            frm_map[t] = alias

    frm = [make_from(alias, t) for t, alias in frm_map.items()]
    sel = []
    projections_values = []

    for c in columns:
        alias = frm_map[c["table"]]
        prop = c["col"]
        table = c["table"]
        agg = c.get("agg")
        if agg is None:
            item = col_ref(alias, prop, table)
        else:
            func_names = {0: "Sum", 1: "Avg", 5: "CountNonNull"}
            fn = func_names.get(agg, "Sum")
            item = agg_ref(alias, prop, table, agg, f"{fn} of {prop}")
        sel.append(item)
        qref = item.get("Name", "")
        projections_values.append({"queryRef": qref})

    proto = make_prototype_query(frm, sel)

    config = {
        "name": new_name(),
        "layouts": [{"id": 0, "position": {
            "x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab_order}}],
        "singleVisual": {
            "visualType": "tableEx",
            "projections": {"Values": projections_values},
            "prototypeQuery": proto,
            "drillFilterOtherVisuals": True
        }
    }

    query_binding = {
        "Commands": [{
            "SemanticQueryDataShapeCommand": {
                "Query": proto,
                "Binding": {
                    "Primary": {"Groupings": [{"Projections": list(range(len(sel)))}]},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 1000}}},
                    "Version": 1
                },
                "ExecutionMetricsKind": 1
            }
        }]
    }

    # dataTransforms for table
    qm_selects = []
    vdr = []
    selects_dt = []
    for i, (c, s) in enumerate(zip(columns, sel)):
        qref = s.get("Name", "")
        disp = c.get("displayName", c["col"])
        agg = c.get("agg")
        type_val = 3 if agg is not None else 2048
        qm_selects.append({"Restatement": disp, "Name": qref, "Type": type_val})
        vdr.append({"Name": "Values", "Projection": i, "isActive": True if agg is None else False})
        if agg is None:
            selects_dt.append({
                "displayName": disp, "queryName": qref,
                "roles": {"Values": True},
                "type": {"category": None, "underlyingType": 1},
                "expr": {"Column": {
                    "Expression": {"SourceRef": {"Entity": c["table"]}},
                    "Property": c["col"]}}
            })
        else:
            func_names = {0: "Sum", 1: "Avg", 5: "CountNonNull"}
            fn = func_names.get(agg, "Sum")
            selects_dt.append({
                "displayName": disp, "queryName": qref,
                "roles": {"Values": True},
                "type": {"category": None, "underlyingType": 260},
                "expr": {"Aggregation": {
                    "Expression": {"Column": {
                        "Expression": {"SourceRef": {"Entity": c["table"]}},
                        "Property": c["col"]}},
                    "Function": agg}}
            })

    dt = {
        "projectionOrdering": {"Values": list(range(len(sel)))},
        "queryMetadata": {"Select": qm_selects},
        "visualElements": [{"DataRoles": vdr}],
        "selects": selects_dt
    }

    return {
        "x": x, "y": y, "z": z, "width": w, "height": h,
        "config": js(config),
        "filters": "[]",
        "query": js(query_binding),
        "dataTransforms": js(dt),
        "tabOrder": tab_order
    }


# ── page builders ──────────────────────────────────────────────────────────────

def build_page1() -> dict:
    """Page 1: Sales KPI Dashboard"""
    containers = []
    tab = 0

    # ── 6 KPI cards in a row (y=20, each ~195px wide, 110px tall) ──────────────
    card_defs = [
        ("Orders", "Sales",       0,  "Sum of Sales"),       # Total Sales
        ("Orders", "Profit",      0,  "Sum of Profit"),      # Total Profit
        ("Orders", "Profit",      0,  "Sum of Profit"),      # Profit Margin % (approx)
        ("Orders", "Order ID",    5,  "Count of Order ID"),  # Total Orders
        ("Orders", "Customer ID", 5,  "Count of Customer ID"), # Total Customers
        ("Orders", "Sales",       0,  "Sum of Sales"),       # Avg Order Value (approx)
    ]
    card_w, card_h = 195, 110
    card_y = 20
    card_gap = 10
    card_start_x = 10

    for i, (tbl, col, func, disp) in enumerate(card_defs):
        cx = card_start_x + i * (card_w + card_gap)
        containers.append(
            make_card_vc(cx, card_y, tab, card_w, card_h, tab, tbl, col, func, disp)
        )
        tab += 1

    # ── Bar chart: Sales by Region ──────────────────────────────────────────────
    containers.append(
        make_bar_chart_vc(10, 160, tab, 600, 530, tab,
                          "Orders", "Region",
                          "Orders", "Sales", 0,
                          visual_type="clusteredBarChart")
    )
    tab += 1

    # ── Line chart: Sales Trend (by Order Date) ─────────────────────────────────
    containers.append(
        make_line_chart_vc(640, 160, tab, 630, 530, tab,
                           "Orders", "Order Date",
                           "Orders", "Sales", 0)
    )
    tab += 1

    return {
        "id": 0,
        "name": "ReportSection",
        "displayName": "Sales KPI Dashboard",
        "filters": "[]",
        "ordinal": 0,
        "visualContainers": containers,
        "config": "{}",
        "displayOption": 1,
        "width": 1280,
        "height": 720
    }


def build_page2() -> dict:
    """Page 2: Product Analysis"""
    containers = []
    tab = 0

    # KPI card: Total Products
    containers.append(
        make_card_vc(10, 10, tab, 200, 100, tab,
                     "Products", "Product ID", 5, "Count of Product ID")
    )
    tab += 1

    # Bar chart: Sales by Category
    containers.append(
        make_bar_chart_vc(10, 130, tab, 600, 280, tab,
                          "Orders", "Category",
                          "Orders", "Sales", 0,
                          visual_type="clusteredBarChart")
    )
    tab += 1

    # Bar chart: Sales by Sub-Category
    containers.append(
        make_bar_chart_vc(640, 130, tab, 630, 280, tab,
                          "Orders", "Sub-Category",
                          "Orders", "Sales", 0,
                          visual_type="clusteredBarChart")
    )
    tab += 1

    # Table: Product details
    cols = [
        {"table": "Products", "col": "Category",     "agg": None, "displayName": "Category"},
        {"table": "Products", "col": "Sub-Category",  "agg": None, "displayName": "Sub-Category"},
        {"table": "Products", "col": "Product Name", "agg": None, "displayName": "Product Name"},
        {"table": "Orders",   "col": "Sales",        "agg": 0,    "displayName": "Sum of Sales"},
    ]
    containers.append(
        make_table_vc(10, 430, tab, 1260, 270, tab, cols)
    )
    tab += 1

    return {
        "id": 1,
        "name": "ReportSection2",
        "displayName": "Product Analysis",
        "filters": "[]",
        "ordinal": 1,
        "visualContainers": containers,
        "config": "{}",
        "displayOption": 1,
        "width": 1280,
        "height": 720
    }


def build_page3() -> dict:
    """Page 3: Customer Analysis"""
    containers = []
    tab = 0

    # KPI card: Total Customers
    containers.append(
        make_card_vc(10, 10, tab, 200, 100, tab,
                     "Orders", "Customer ID", 5, "Count of Customer ID")
    )
    tab += 1

    # KPI card: Avg Order Value (Sum of Sales as proxy)
    containers.append(
        make_card_vc(230, 10, tab, 200, 100, tab,
                     "Orders", "Sales", 0, "Sum of Sales")
    )
    tab += 1

    # Bar chart: Sales by Segment
    containers.append(
        make_bar_chart_vc(10, 130, tab, 600, 280, tab,
                          "Orders", "Segment",
                          "Orders", "Sales", 0,
                          visual_type="clusteredBarChart")
    )
    tab += 1

    # Bar chart: Orders by City (existing visual reproduced)
    containers.append(
        make_bar_chart_vc(640, 130, tab, 630, 280, tab,
                          "Orders", "City",
                          "Orders", "Customer ID", 5,
                          visual_type="clusteredColumnChart")
    )
    tab += 1

    # Table: Customer details
    cols = [
        {"table": "Customers", "col": "Customer Name", "agg": None, "displayName": "Customer Name"},
        {"table": "Customers", "col": "Segment",       "agg": None, "displayName": "Segment"},
        {"table": "Orders",    "col": "Sales",         "agg": 0,    "displayName": "Sum of Sales"},
    ]
    containers.append(
        make_table_vc(10, 430, tab, 1260, 270, tab, cols)
    )
    tab += 1

    return {
        "id": 2,
        "name": "ReportSection3",
        "displayName": "Customer Analysis",
        "filters": "[]",
        "ordinal": 2,
        "visualContainers": containers,
        "config": "{}",
        "displayOption": 1,
        "width": 1280,
        "height": 720
    }


def build_page4() -> dict:
    """Page 4: Returns & Performance"""
    containers = []
    tab = 0

    # KPI card: Total Returns
    containers.append(
        make_card_vc(10, 10, tab, 200, 100, tab,
                     "Returns", "Order ID", 5, "Count of Order ID")
    )
    tab += 1

    # KPI card: Return Rate (approx – CountNonNull of Returns Order ID)
    containers.append(
        make_card_vc(230, 10, tab, 200, 100, tab,
                     "Returns", "Order ID", 5, "Return Count")
    )
    tab += 1

    # Bar chart: Returns by Category
    containers.append(
        make_bar_chart_vc(10, 130, tab, 600, 560, tab,
                          "Returns", "Region",
                          "Returns", "Order ID", 5,
                          visual_type="clusteredBarChart")
    )
    tab += 1

    # Bar chart: Profit by Segment
    containers.append(
        make_bar_chart_vc(640, 130, tab, 630, 280, tab,
                          "Orders", "Segment",
                          "Orders", "Profit", 0,
                          visual_type="clusteredBarChart")
    )
    tab += 1

    # Line chart: Monthly Profit Trend
    containers.append(
        make_line_chart_vc(640, 430, tab, 630, 260, tab,
                           "Orders", "Order Date",
                           "Orders", "Profit", 0)
    )
    tab += 1

    return {
        "id": 3,
        "name": "ReportSection4",
        "displayName": "Returns & Performance",
        "filters": "[]",
        "ordinal": 3,
        "visualContainers": containers,
        "config": "{}",
        "displayOption": 1,
        "width": 1280,
        "height": 720
    }


# ── report layout assembler ────────────────────────────────────────────────────

def build_report_layout() -> str:
    """Return the full Report/Layout JSON as a Python string (UTF-16 LE to be encoded by caller)."""

    report_config = {
        "version": "5.49",
        "themeCollection": {
            "baseTheme": {"name": "CY23SU11", "version": "5.49", "type": 2}
        },
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True,
        "slowDataSourceSettings": {
            "isCrossHighlightingDisabled": False,
            "isSlicerSelectionsButtonEnabled": False,
            "isFilterSelectionsButtonEnabled": False,
            "isFieldWellButtonEnabled": False,
            "isApplyAllButtonEnabled": False
        },
        "linguisticSchemaSyncVersion": 2,
        "settings": {
            "useNewFilterPaneExperience": True,
            "allowChangeFilterTypes": True,
            "useStylableVisualContainerHeader": True,
            "queryLimitOption": 6,
            "exportDataMode": 1,
            "useDefaultAggregateDisplayName": True
        },
        "objects": {
            "section": [{
                "properties": {
                    "verticalAlignment": {
                        "expr": {"Literal": {"Value": "'Top'"}}
                    }
                }
            }]
        }
    }

    layout = {
        "id": 0,
        "resourcePackages": [{
            "resourcePackage": {
                "name": "SharedResources",
                "type": 2,
                "items": [{"type": 202,
                           "path": "BaseThemes/CY23SU11.json",
                           "name": "CY23SU11"}],
                "disabled": False
            }
        }],
        "sections": [
            build_page1(),
            build_page2(),
            build_page3(),
            build_page4()
        ],
        "config": js(report_config),
        "layoutOptimization": 0
    }

    return json.dumps(layout, ensure_ascii=False)


# ── PBIX generator ─────────────────────────────────────────────────────────────

def generate_pbix():
    print(f"Reading source PBIX: {SOURCE_PBIX}")
    if not os.path.exists(SOURCE_PBIX):
        raise FileNotFoundError(f"Source PBIX not found: {SOURCE_PBIX}")

    layout_json_str = build_report_layout()
    # Validate JSON
    _ = json.loads(layout_json_str)
    print("Report/Layout JSON is valid.")

    layout_bytes = layout_json_str.encode("utf-16-le")

    print(f"Writing enhanced PBIX to: {OUTPUT_PBIX}")
    with zipfile.ZipFile(SOURCE_PBIX, 'r') as src_zip:
        with zipfile.ZipFile(OUTPUT_PBIX, 'w', compression=zipfile.ZIP_DEFLATED) as dst_zip:
            for item in src_zip.infolist():
                if item.filename == "Report/Layout":
                    # Replace with our enhanced layout
                    dst_zip.writestr(item.filename, layout_bytes)
                    print(f"  Replaced: {item.filename}  ({len(layout_bytes):,} bytes)")
                else:
                    # Copy everything else verbatim
                    data = src_zip.read(item.filename)
                    dst_zip.writestr(item, data)
                    print(f"  Copied:   {item.filename}  ({len(data):,} bytes)")

    print(f"\nEnhanced PBIX saved: {OUTPUT_PBIX}")
    size = os.path.getsize(OUTPUT_PBIX)
    print(f"  File size: {size:,} bytes")


# ── DAX measures ───────────────────────────────────────────────────────────────

DAX_CONTENT = """\
-- ============================================================
-- KPI Measures for Business Dashboard
-- Create these measures in the Orders table (or a dedicated
-- Measures table) using Power BI Desktop > Data view >
-- New measure.
-- ============================================================

-- ── Core Sales KPIs ────────────────────────────────────────

Total Sales = SUM(Orders[Sales])

Total Profit = SUM(Orders[Profit])

Profit Margin % = DIVIDE([Total Profit], [Total Sales], 0)

Total Orders = DISTINCTCOUNT(Orders[Order ID])

Total Customers = DISTINCTCOUNT(Orders[Customer ID])

Avg Order Value = DIVIDE([Total Sales], [Total Orders], 0)

Total Quantity = SUM(Orders[Quantity])

Avg Discount = AVERAGE(Orders[Discount])

-- ── Returns KPIs ───────────────────────────────────────────

Total Returns = COUNTROWS(Returns)

Return Rate % = DIVIDE([Total Returns], [Total Orders], 0)

-- ── Sales Growth ───────────────────────────────────────────

Sales YoY % =
VAR CurrentYear = CALCULATE([Total Sales], YEAR(Orders[Order Date]) = YEAR(TODAY()))
VAR PriorYear   = CALCULATE([Total Sales], YEAR(Orders[Order Date]) = YEAR(TODAY()) - 1)
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, 0)

-- ── Monthly Targets (uses Monthly KPIs table) ──────────────

Target Achievement % = DIVIDE([Total Sales], SUM('Monthly KPIs'[Target Sales]), 0)

-- ── Customer Metrics ───────────────────────────────────────

New Customers =
CALCULATE(
    DISTINCTCOUNT(Orders[Customer ID]),
    FILTER(
        VALUES(Orders[Customer ID]),
        CALCULATE(MIN(Orders[Order Date])) = MIN(Orders[Order Date])
    )
)

-- ── Product Metrics ────────────────────────────────────────

Top Category =
CALCULATE(
    FIRSTNONBLANK(Orders[Category], 1),
    TOPN(1, VALUES(Orders[Category]), [Total Sales])
)
"""


def write_dax():
    with open(DAX_FILE, "w", encoding="utf-8") as f:
        f.write(DAX_CONTENT)
    print(f"DAX measures written: {DAX_FILE}")


# ── Relationships JSON ─────────────────────────────────────────────────────────

RELATIONSHIPS = {
    "relationships": [
        {
            "from_table": "Orders",
            "from_column": "Customer ID",
            "to_table": "Customers",
            "to_column": "Customer ID",
            "cardinality": "Many-to-One",
            "cross_filter": "Single"
        },
        {
            "from_table": "Orders",
            "from_column": "Product ID",
            "to_table": "Products",
            "to_column": "Product ID",
            "cardinality": "Many-to-One",
            "cross_filter": "Single"
        },
        {
            "from_table": "Returns",
            "from_column": "Order ID",
            "to_table": "Orders",
            "to_column": "Order ID",
            "cardinality": "Many-to-One",
            "cross_filter": "Single"
        },
        {
            "from_table": "Orders",
            "from_column": "Region",
            "to_table": "Users",
            "to_column": "Region",
            "cardinality": "Many-to-One",
            "cross_filter": "Single"
        },
        {
            "from_table": "Orders",
            "from_column": "Order Date",
            "to_table": "Monthly KPIs",
            "to_column": "Month",
            "cardinality": "Many-to-One",
            "cross_filter": "Single",
            "note": "May need date table bridge"
        },
        {
            "from_table": "Orders",
            "from_column": "Sales",
            "to_table": "Sales",
            "to_column": "Sales",
            "cardinality": "Many-to-One",
            "cross_filter": "Single",
            "note": "Review Sales table structure - may be a duplicate or summary table"
        }
    ],
    "notes": [
        "These relationships need to be created manually in Power BI Desktop > Model view",
        "The Orders table is the main fact table",
        "Customers, Products, Users are dimension tables",
        "Returns is a related fact table",
        "Monthly KPIs is a target/budget table"
    ]
}


def write_relationships():
    with open(REL_FILE, "w", encoding="utf-8") as f:
        json.dump(RELATIONSHIPS, f, indent=2)
    print(f"Relationships JSON written: {REL_FILE}")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Enhanced PBIX Generator")
    print("=" * 60)

    write_dax()
    write_relationships()
    generate_pbix()

    # ── verify outputs ──────────────────────────────────────────
    print("\n── Verification ──────────────────────────────────────────")
    for path in (OUTPUT_PBIX, DAX_FILE, REL_FILE):
        exists = os.path.exists(path)
        size   = os.path.getsize(path) if exists else 0
        print(f"  {'OK' if exists else 'MISSING':7s}  {path}  ({size:,} bytes)")

    # Verify PBIX contains 4 pages
    print("\n── Report pages in enhanced PBIX ─────────────────────────")
    with zipfile.ZipFile(OUTPUT_PBIX, 'r') as z:
        raw = z.read("Report/Layout")
    layout = json.loads(raw.decode("utf-16-le"))
    for sec in layout["sections"]:
        vc_count = len(sec["visualContainers"])
        print(f"  Page {sec['ordinal']+1}: \"{sec['displayName']}\"  "
              f"({vc_count} visual container{'s' if vc_count != 1 else ''})")

    print("\nDone.")


if __name__ == "__main__":
    main()

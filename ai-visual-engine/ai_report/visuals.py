"""Matplotlib renderers (requirement #13: PNG remains available for preview).

Renderers consume a QueryResult (already filtered/aggregated by query_engine)
plus the VisualPlan, and return a matplotlib Figure. They never re-query.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt

from . import kpi as kpimod
from .errors import VisualError
from .query_engine import QueryResult
from .schema import VisualPlan


def render(visual: VisualPlan, result: QueryResult):
    vt = visual.type
    if vt in ("bar", "column"):
        return _bar(visual, result)
    if vt in ("line", "area"):
        return _line(visual, result, area=vt == "area")
    if vt in ("pie", "donut"):
        return _pie(visual, result, donut=vt == "donut")
    if vt == "scatter":
        return _scatter(visual, result)
    if vt == "histogram":
        return _histogram(visual, result)
    if vt == "kpi":
        return _kpi(visual, result)
    if vt == "table":
        return _table(visual, result)
    raise VisualError(f"Unsupported visual type: {vt}")


def _title(visual: VisualPlan, default: str) -> str:
    return visual.title or default


def _bar(visual, result):
    df, x, y = result.df, result.x, result.y
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(df[x].astype(str), df[y])
    ax.set_title(_title(visual, f"{y} by {x}"))
    ax.set_xlabel(x)
    ax.set_ylabel(f"{visual.aggregation.upper()} of {y}")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig


def _line(visual, result, area=False):
    df, x, y = result.df, result.x, result.y
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df[x].astype(str), df[y], marker="o")
    if area:
        ax.fill_between(df[x].astype(str), df[y], alpha=0.2)
    ax.set_title(_title(visual, f"{y} over {x}"))
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig


def _pie(visual, result, donut=False):
    df, x, y = result.df, result.x, result.y
    fig, ax = plt.subplots(figsize=(8, 8))
    wedgeprops = {"width": 0.4} if donut else None
    ax.pie(df[y], labels=df[x].astype(str), autopct="%1.1f%%", wedgeprops=wedgeprops)
    ax.set_title(_title(visual, f"{y} by {x}"))
    fig.tight_layout()
    return fig


def _scatter(visual, result):
    df, x, y = result.df, result.x, result.y
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df[x], df[y], alpha=0.6)
    ax.set_title(_title(visual, f"{y} vs {x}"))
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    fig.tight_layout()
    return fig


def _histogram(visual, result):
    df, x = result.df, result.x
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df[x].dropna(), bins=30)
    ax.set_title(_title(visual, f"Distribution of {x}"))
    ax.set_xlabel(x)
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    return fig


def _kpi(visual, result):
    value = kpimod.compute_kpi(result.df, visual)
    label = kpimod.kpi_label(visual)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis("off")
    text = f"{value:,.2f}" if isinstance(value, (int, float)) else str(value)
    ax.text(0.5, 0.55, text, ha="center", va="center", fontsize=32)
    ax.text(0.5, 0.25, label, ha="center", va="center", fontsize=16)
    return fig


def _table(visual, result):
    df = result.df.head(20)
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis("off")
    table = ax.table(cellText=df.values, colLabels=list(df.columns), loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.5)
    ax.set_title(_title(visual, "Table"), fontsize=16)
    return fig

"""Drill-down / hierarchy helpers (requirement #9).

Hierarchies are detected during profiling (Geography, Date). This module keeps
the notion of "which level to display" so a drill-down request preserves the
full hierarchy metadata instead of treating each column independently.
"""
from __future__ import annotations

from typing import List, Optional

from .profiler import DatasetProfile


def resolve_hierarchy(profile: DatasetProfile, levels: List[str]) -> List[str]:
    """Return the valid subset of a requested hierarchy, in order."""
    valid = {c.name for c in profile.columns}
    return [lvl for lvl in levels if lvl in valid]


def top_level(hierarchy: List[str]) -> Optional[str]:
    return hierarchy[0] if hierarchy else None


def next_level(hierarchy: List[str], current: str) -> Optional[str]:
    if current in hierarchy:
        idx = hierarchy.index(current)
        if idx + 1 < len(hierarchy):
            return hierarchy[idx + 1]
    return None

"""AI Visual / Report Generation Engine.

Public API (backward compatible with the prototype):

    from ai_report import load_data, execute_visuals, generate_report, profile_dataset
"""
from .data_loader import load_data
from .profiler import profile_dataset, profile_all, profiles_to_dict
from .planner import plan_report
from .report import generate_report, execute_visuals, ReportResult, VisualResult
from .schema import ReportPlan, VisualPlan, Filter, Sort
from .powerbi_adapter import to_powerbi_spec

__all__ = [
    "load_data",
    "execute_visuals",
    "generate_report",
    "profile_dataset",
    "profile_all",
    "profiles_to_dict",
    "plan_report",
    "to_powerbi_spec",
    "ReportResult",
    "VisualResult",
    "ReportPlan",
    "VisualPlan",
    "Filter",
    "Sort",
]

__version__ = "2.0.0"

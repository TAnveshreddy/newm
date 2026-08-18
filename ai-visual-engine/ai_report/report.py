"""Report orchestrator (requirements #14, #15, #20).

Ties the pipeline together:

    clean -> profile (semantic metadata) -> plan (NL->JSON) -> schema validate
    -> semantic validate -> query/transform -> render -> structured result

Error recovery is central: a single failing visual never crashes the request.
Each visual is executed in isolation and failures are collected.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from . import cleaning, planner, profiler, validation, visuals as vismod
from .errors import AiReportError
from .logging_util import log_event, new_request_id
from .powerbi_adapter import to_powerbi_spec
from .query_engine import build_result
from .schema import ReportPlan, VisualPlan


@dataclass
class VisualResult:
    title: str
    type: str
    ok: bool
    file: Optional[str] = None
    visual_json: Optional[Dict[str, Any]] = None
    powerbi_spec: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ReportResult:
    request_id: str
    title: str
    successful: int
    failed: int
    visuals: List[VisualResult] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    cleaning: Dict[str, Any] = field(default_factory=dict)
    plan: Dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    def summary(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "title": self.title,
            "successful": self.successful,
            "failed": self.failed,
            "errors": self.errors,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.summary(),
            "cleaning": self.cleaning,
            "plan": self.plan,
            "duration_ms": self.duration_ms,
            "visuals": [
                {"title": v.title, "type": v.type, "ok": v.ok, "file": v.file,
                 "visual_json": v.visual_json, "powerbi_spec": v.powerbi_spec, "error": v.error}
                for v in self.visuals
            ],
        }


def generate_report(
    datasets: Dict[str, pd.DataFrame],
    prompt: str,
    output_folder: Optional[str] = None,
    render: bool = True,
) -> ReportResult:
    request_id = new_request_id()
    start = time.time()

    # 1. Clean + profile.
    cleaned: Dict[str, pd.DataFrame] = {}
    cleaning_reports: Dict[str, Any] = {}
    for name, df in datasets.items():
        cdf, rep = cleaning.clean_dataframe(df)
        cleaned[name] = cdf
        cleaning_reports[name] = rep.to_dict()
    profiles = profiler.profile_all(cleaned)

    # 2. Plan (NL -> JSON), then structurally validated by schema.
    plan: ReportPlan = planner.plan_report(prompt, profiles)

    log_event("plan_generated", request_id=request_id, prompt=prompt,
              datasets=list(datasets), visuals=len(plan.visuals))

    if output_folder and render:
        os.makedirs(output_folder, exist_ok=True)

    results: List[VisualResult] = []
    errors: List[Dict[str, str]] = []

    for index, visual in enumerate(plan.visuals, 1):
        vr = _run_visual(index, visual, cleaned, profiles, output_folder, render)
        results.append(vr)
        if not vr.ok:
            errors.append({"visual": vr.title, "reason": vr.error or "unknown error"})

    successful = sum(1 for r in results if r.ok)
    failed = len(results) - successful
    duration_ms = int((time.time() - start) * 1000)

    log_event("report_complete", request_id=request_id,
              successful=successful, failed=failed, duration_ms=duration_ms)

    return ReportResult(
        request_id=request_id, title=plan.title, successful=successful, failed=failed,
        visuals=results, errors=errors, cleaning=cleaning_reports,
        plan=plan.to_dict(), duration_ms=duration_ms,
    )


def _run_visual(index, visual: VisualPlan, datasets, profiles, output_folder, render) -> VisualResult:
    title = visual.title or f"Visual {index}"
    try:
        # Semantic validation (raises SemanticError on invalid references).
        validation.validate_visual(visual, profiles)

        df = datasets[visual.dataset]
        profile = profiles[visual.dataset]
        result = build_result(df, profile, visual)

        file_path = None
        if render and output_folder:
            fig = vismod.render(visual, result)
            file_path = os.path.join(output_folder, f"visual_{index}_{visual.type}.png")
            fig.savefig(file_path, dpi=150, bbox_inches="tight")
            import matplotlib.pyplot as plt
            plt.close(fig)

        return VisualResult(
            title=title, type=visual.type, ok=True, file=file_path,
            visual_json=visual.to_dict(), powerbi_spec=to_powerbi_spec(visual),
        )
    except (AiReportError, KeyError, ValueError, TypeError) as e:
        reason = str(e) or e.__class__.__name__
        log_event("visual_failed", visual=title, reason=reason)
        return VisualResult(title=title, type=visual.type, ok=False, error=reason,
                            visual_json=visual.to_dict())


# ---------------------------------------------------------------------------
# Backward-compatible helper (requirement #17)
# ---------------------------------------------------------------------------

def execute_visuals(datasets: Dict[str, pd.DataFrame], report_plan: Dict[str, Any],
                    output_folder: str) -> List[str]:
    """Execute an explicit plan dict and return generated PNG paths.

    Mirrors the prototype's ``execute_visuals`` signature so existing callers
    keep working. Invalid visuals are skipped (not fatal).
    """
    profiles = profiler.profile_all(datasets)
    plan = ReportPlan.from_dict(report_plan) if "title" in report_plan else ReportPlan(
        title="Report", visuals=[VisualPlan.from_dict(v) for v in report_plan["visuals"]])
    os.makedirs(output_folder, exist_ok=True)
    files: List[str] = []
    for index, visual in enumerate(plan.visuals, 1):
        vr = _run_visual(index, visual, datasets, profiles, output_folder, render=True)
        if vr.ok and vr.file:
            files.append(vr.file)
    return files

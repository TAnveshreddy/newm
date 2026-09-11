"""
analyst.py
----------
The "AI BI Analyst" orchestrator: Ask -> Understand -> Query -> Analyze ->
Visualize -> Explain -> Modify.

Ties together the planner (nl_planner), DAX generation (dax), execution
(query_engine via the executor) and visualization selection (viz), and keeps the
conversational context so follow-up prompts modify the current report.
"""
from __future__ import annotations

from typing import Optional

from semantic_model import SemanticModel
from nl_planner import Planner, QueryIntent
from dax import generate_dax
from viz import select_visualization
from auth import UserContext, get_executor


class Analyst:
    def __init__(self, model: SemanticModel):
        self.model = model
        self.planner = Planner(model)
        self.executor = get_executor(model)

    # ------------------------------------------------------------------ #
    def handle(self, message: str, user: UserContext,
               prev_intent: Optional[QueryIntent]) -> dict:
        intent = self.planner.interpret(message, prev_intent)

        # Nothing we can map + a clearly-missing metric -> honest error, no fabrication.
        if intent.unresolved and not intent.measures and not intent.is_report:
            missing = ", ".join(intent.unresolved)
            return {
                "ok": False,
                "reply": (f"I couldn't find a **{missing}** field or measure in the connected "
                          f"Power BI model. Available measures include: "
                          f"{', '.join(list(self.model.measures)[:8])}… "
                          f"Please try another metric."),
                "intent": intent.to_dict(),
                "visuals": [],
                "kind": "error",
            }

        if intent.is_report:
            return self._handle_report(message, intent, user)

        return self._handle_single(message, intent, user)

    # ------------------------------------------------------------------ #
    def _handle_single(self, message: str, intent: QueryIntent, user: UserContext) -> dict:
        dax = generate_dax(self.model, intent)
        result = self.executor.run(intent, user)
        if result.error:
            return {
                "ok": False,
                "reply": f"I hit a problem running that query: {result.error}",
                "intent": intent.to_dict(), "dax": dax, "visuals": [], "kind": "error",
            }
        viz = select_visualization(self.model, intent, result)
        reply = self._compose_reply(intent, result, viz)
        return {
            "ok": True,
            "reply": reply,
            "intent": intent.to_dict(),
            "dax": dax,
            "kind": "report" if False else intent.intent_kind,
            "using_llm": self.planner.using_llm,
            "visuals": [{
                "id": "v1",
                "viz": viz,
                "dax": dax,
                "data": result.to_dict(),
            }],
        }

    def _handle_report(self, message: str, intent: QueryIntent, user: UserContext) -> dict:
        visuals = []
        for i, spec in enumerate(intent.report_specs, 1):
            sub = QueryIntent(
                measures=spec.get("measures", ["Total Revenue"]),
                dimension=spec.get("dimension"),
                secondary_dimension=spec.get("secondary_dimension"),
                time_grain=spec.get("time_grain"),
                top_n=spec.get("top_n"),
                filters=spec.get("filters", []),
                chart_type=spec.get("chart"),
                intent_kind=spec.get("kind", "breakdown"),
                raw=spec.get("title", message),
            )
            dax = generate_dax(self.model, sub)
            result = self.executor.run(sub, user)
            viz = select_visualization(self.model, sub, result)
            if spec.get("title"):
                viz["title"] = spec["title"]
            visuals.append({
                "id": f"v{i}",
                "viz": viz,
                "dax": dax,
                "data": result.to_dict(),
            })
        n = len(visuals)
        reply = (f"Here's your **{intent.report_title}** — {n} visuals generated from the "
                 f"Power BI semantic model. You can refine any of them, e.g. "
                 f"*“change the country chart to a pie”* or *“filter to 2025”*.")
        return {
            "ok": True,
            "reply": reply,
            "intent": intent.to_dict(),
            "kind": "report",
            "title": intent.report_title,
            "using_llm": self.planner.using_llm,
            "visuals": visuals,
        }

    # ------------------------------------------------------------------ #
    def _compose_reply(self, intent: QueryIntent, result, viz: dict) -> str:
        if not result.rows or (len(result.rows) == 1 and result.dimension and
                               all(v is None for k, v in result.rows[0].items())):
            yrs = next((f["values"] for f in intent.filters if f["field"] == "Year"), None)
            hint = ""
            if yrs and not any(y in self.model.years for y in yrs):
                hint = (f" The model covers {min(self.model.years)}–{max(self.model.years)}; "
                        f"there's no data for {', '.join(str(y) for y in yrs)}.")
            return "I ran the query but no rows matched those filters." + hint
        return viz.get("explanation", "Here's the result.")

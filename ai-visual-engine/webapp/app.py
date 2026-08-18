"""Web application wrapper for the AI Visual / Report engine.

Serves a single chat page and a JSON API. You type a question in the browser and
the generated charts render on the page. The heavy lifting is done by the
`ai_report` engine — this file only adds the HTTP + UI layer.

Run:
    cd ai-visual-engine
    python webapp/app.py
    # then open http://localhost:8000
"""
from __future__ import annotations

import base64
import io
import os
import pathlib
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request, send_from_directory

# Make the parent folder importable so `import ai_report` works when run directly.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ai_report import cleaning, planner, profiler, validation  # noqa: E402
from ai_report import visuals as vismod  # noqa: E402
from ai_report.data_loader import load_data  # noqa: E402
from ai_report.errors import AiReportError  # noqa: E402
from ai_report.powerbi_adapter import to_powerbi_spec  # noqa: E402
from ai_report.query_engine import build_result  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
SAMPLE = HERE.parents[0] / "data" / "sales.csv"

app = Flask(__name__, static_folder=str(HERE), static_url_path="")

# In-memory current dataset (single-user local app).
STATE = {"datasets": None, "name": None}


def ensure_dataset() -> None:
    if STATE["datasets"] is None:
        STATE["datasets"] = load_data(str(SAMPLE))
        STATE["name"] = "sales.csv (sample)"


def _fig_to_data_uri(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def run_prompt(prompt: str) -> dict:
    ensure_dataset()

    # Clean + profile (semantic metadata drives validation).
    cleaned = {}
    for name, df in STATE["datasets"].items():
        cdf, _ = cleaning.clean_dataframe(df)
        cleaned[name] = cdf
    profiles = profiler.profile_all(cleaned)

    plan = planner.plan_report(prompt, profiles)

    visuals = []
    ok = 0
    for index, visual in enumerate(plan.visuals, 1):
        title = visual.title or f"Visual {index}"
        try:
            validation.validate_visual(visual, profiles)
            result = build_result(cleaned[visual.dataset], profiles[visual.dataset], visual)
            fig = vismod.render(visual, result)
            visuals.append({
                "title": title,
                "type": visual.type,
                "ok": True,
                "image": _fig_to_data_uri(fig),
                "visual_json": visual.to_dict(),
                "powerbi_spec": to_powerbi_spec(visual),
            })
            ok += 1
        except (AiReportError, KeyError, ValueError, TypeError) as e:
            visuals.append({
                "title": title,
                "type": visual.type,
                "ok": False,
                "error": str(e) or e.__class__.__name__,
            })

    failed = len(visuals) - ok
    message = _assistant_message(plan.title, ok, failed)
    return {"title": plan.title, "message": message, "successful": ok,
            "failed": failed, "visuals": visuals}


def _assistant_message(title: str, ok: int, failed: int) -> str:
    if ok == 0 and failed == 0:
        return "I couldn't find anything to chart for that. Try naming a measure like revenue."
    parts = [f"Here {'is' if ok == 1 else 'are'} {ok} visual{'' if ok == 1 else 's'}."]
    if failed:
        parts.append(f"{failed} could not be generated (see notes below).")
    return " ".join(parts)


# --- routes ---------------------------------------------------------------

@app.get("/")
def index():
    return send_from_directory(str(HERE), "index.html")


@app.get("/api/info")
def info():
    ensure_dataset()
    profiles = profiler.profile_all(STATE["datasets"])
    return jsonify({
        "name": STATE["name"],
        "datasets": {n: p.semantic_metadata() for n, p in profiles.items()},
    })


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    if not prompt:
        return jsonify({"error": "Please enter a question."}), 400
    try:
        return jsonify(run_prompt(prompt))
    except Exception as e:  # noqa: BLE001 - surface a safe message to the UI
        return jsonify({"error": str(e) or "Something went wrong."}), 500


@app.post("/api/upload")
def upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No file selected."}), 400
    suffix = pathlib.Path(f.filename).suffix.lower() or ".csv"
    if suffix not in (".csv", ".xlsx", ".xls"):
        return jsonify({"error": "Please upload a CSV or Excel file."}), 400
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    f.save(tmp.name)
    tmp.close()
    try:
        datasets = load_data(tmp.name)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Could not read the file: {e}"}), 400
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    STATE["datasets"] = datasets
    STATE["name"] = f.filename
    profiles = profiler.profile_all(datasets)
    return jsonify({
        "name": f.filename,
        "datasets": {n: p.semantic_metadata() for n, p in profiles.items()},
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"\n  AI Visual Chatbot running →  http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=False)

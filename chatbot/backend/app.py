"""
app.py
------
Self-contained backend API + static file server for the Power BI AI chatbot.
Standard library only (http.server) so it runs anywhere with just Python 3.

Routes
------
  GET  /                       -> frontend (index.html)
  GET  /api/health             -> {status}
  POST /api/connect            -> {email} -> session token + workspaces (Entra-style)
  GET  /api/model              -> semantic model summary + suggested prompts
  POST /api/chat               -> {session, message} -> analyst response (visuals, dax, data)

Security notes
--------------
  * No Power BI secrets, tokens, keys, dataset/workspace ids are ever sent to the
    browser. The session token is an opaque server-issued id.
  * In live mode the browser only ever holds the Entra session; queries run
    server-side as the user so RLS is enforced by Power BI.
"""
from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FRONTEND = os.path.join(ROOT, "frontend")
sys.path.insert(0, HERE)

from semantic_model import get_registry, SemanticModel  # noqa: E402
from nl_planner import QueryIntent                  # noqa: E402
from analyst import Analyst                         # noqa: E402
from auth import get_auth_provider, UserContext     # noqa: E402

REGISTRY = get_registry()
AUTH = get_auth_provider()

# Lazily-built Analyst per dataset id (each has its own model + planner).
_ANALYSTS: dict[str, Analyst] = {}


def get_analyst(ds_id: str) -> Analyst:
    if ds_id not in _ANALYSTS:
        _ANALYSTS[ds_id] = Analyst(REGISTRY.get(ds_id))
    return _ANALYSTS[ds_id]


# In-memory session store: token -> {"user", "dataset": id, "last_intent"}
SESSIONS: dict[str, dict] = {}

SALES_PROMPTS = [
    "Show total sales by country",
    "Create a monthly sales trend for 2025",
    "Top 10 customers by revenue",
    "Profit growth by product (YoY)",
    "Sales by product category as a bar chart",
    "Compare revenue between UK, India and USA",
    "Profit margin by category using a line chart",
    "Create a dashboard showing sales, profit, quantity and YoY growth",
]


def suggested_prompts(model: SemanticModel) -> list[str]:
    """Per-dataset starter prompts (curated for sales, generated otherwise)."""
    if model.profile == "sales":
        return SALES_PROMPTS
    ms = list(model.measures)
    prim = ms[0] if ms else "value"
    dims = model.categorical_dimensions()
    yr = model.years[-1] if model.years else ""
    yoy = next((m for m in ms if model.measures[m].kind == "derived"), None)
    out = []
    if dims:
        out.append(f"Show {prim} by {dims[0]}")
    if any(d.is_time for d in model.dimensions.values()):
        out.append(f"Monthly {prim} trend for {yr}".strip())
    if len(dims) > 1:
        out.append(f"Top 10 {dims[1].lower()} by {prim.lower()}")
    if len(dims) > 2:
        out.append(f"{prim} by {dims[2].lower()} as a bar chart")
    if yoy and dims:
        out.append(f"{yoy} by {dims[0].lower()}")
    out.append(f"Create a dashboard for {model.meta.get('name', 'this model')}")
    return out[:8]

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml", ".ico": "image/x-icon",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "PBIChatbot/1.0"

    # ---- helpers ----
    def _json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _session(self) -> dict | None:
        token = self.headers.get("X-Session", "")
        return SESSIONS.get(token)

    def log_message(self, *args):  # quieter logs
        if os.environ.get("CHATBOT_VERBOSE"):
            super().log_message(*args)

    # ---- static ----
    def _serve_static(self, path: str):
        if path in ("/", ""):
            path = "/index.html"
        full = os.path.normpath(os.path.join(FRONTEND, path.lstrip("/")))
        if not full.startswith(FRONTEND) or not os.path.isfile(full):
            self.send_error(404, "Not found")
            return
        ext = os.path.splitext(full)[1]
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")
        with open(full, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---- routing ----
    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/api/health":
            return self._json({"status": "ok", "datasets": REGISTRY.ids()})
        if route == "/api/datasets":
            return self._json({"datasets": REGISTRY.catalog(), "default": REGISTRY.default_id()})
        if route == "/api/model":
            return self._model_summary()
        return self._serve_static(route)

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/api/connect":
            return self._connect()
        if route == "/api/select":
            return self._select()
        if route == "/api/chat":
            return self._chat()
        self.send_error(404, "Not found")

    # ---- helpers ----
    def _current_dataset(self, sess: dict | None) -> str:
        # query override (?dataset=), else the session's, else default
        qs = parse_qs(urlparse(self.path).query)
        if qs.get("dataset"):
            ds = qs["dataset"][0]
            if REGISTRY.has(ds):
                return ds
        if sess and REGISTRY.has(sess.get("dataset", "")):
            return sess["dataset"]
        return REGISTRY.default_id()

    def _model_summary(self, ds_id: str | None = None):
        sess = self._session()
        ds_id = ds_id or self._current_dataset(sess)
        analyst = get_analyst(ds_id)
        model = analyst.model
        summary = model.summary()
        summary["dataset"] = ds_id
        summary["suggestedPrompts"] = suggested_prompts(model)
        summary["authMode"] = AUTH.mode
        summary["llm"] = analyst.planner.using_llm
        summary["description"] = model.meta.get("description", "")
        return self._json(summary)

    # ---- endpoints ----
    def _connect(self):
        data = self._body()
        try:
            user = AUTH.connect(data.get("email", ""))
        except ValueError as exc:
            return self._json({"ok": False, "error": str(exc)}, status=400)
        except NotImplementedError as exc:
            return self._json({"ok": False, "error": str(exc)}, status=501)
        default_ds = REGISTRY.default_id()
        SESSIONS[user.token] = {"user": user, "dataset": default_ds, "last_intent": None}
        return self._json({
            "ok": True,
            "session": user.token,
            "user": {"name": user.name, "email": user.email},
            "workspaces": user.workspaces,
            "rls": bool(user.rls_filters),
            "authMode": AUTH.mode,
            "datasets": REGISTRY.catalog(),
            "dataset": default_ds,
        })

    def _select(self):
        sess = self._session()
        if not sess:
            return self._json({"ok": False, "error": "Not connected."}, status=401)
        data = self._body()
        ds_id = data.get("dataset", "")
        if not REGISTRY.has(ds_id):
            return self._json({"ok": False, "error": f"Unknown report '{ds_id}'."}, status=400)
        sess["dataset"] = ds_id
        sess["last_intent"] = None      # a new report starts a fresh conversation context
        return self._model_summary(ds_id)

    def _chat(self):
        sess = self._session()
        if not sess:
            return self._json({"ok": False, "error": "Not connected. Please sign in to Power BI."},
                              status=401)
        data = self._body()
        message = (data.get("message") or "").strip()
        if not message:
            return self._json({"ok": False, "error": "Empty message."}, status=400)

        ds_id = self._current_dataset(sess)
        analyst = get_analyst(ds_id)
        prev = sess.get("last_intent")
        prev_intent = QueryIntent(**prev) if prev else None
        t0 = time.time()
        result = analyst.handle(message, sess["user"], prev_intent)
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        result["dataset"] = ds_id
        # remember intent for follow-ups (single-visual intents only)
        if result.get("ok") and result.get("kind") != "report" and result.get("intent"):
            sess["last_intent"] = result["intent"]
        return self._json(result)


def main():
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    httpd = ThreadingHTTPServer((host, port), Handler)
    default = get_analyst(REGISTRY.default_id())
    print(f"Power BI AI Chatbot running at http://{host}:{port}")
    print(f"  Reports available: {', '.join(REGISTRY.ids())}")
    print(f"  Default model: {default.model.meta.get('name')} | "
          f"LLM planner={'on' if default.planner.using_llm else 'off (rule-based)'}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.shutdown()


if __name__ == "__main__":
    main()

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
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FRONTEND = os.path.join(ROOT, "frontend")
sys.path.insert(0, HERE)

from semantic_model import get_model               # noqa: E402
from nl_planner import QueryIntent                  # noqa: E402
from analyst import Analyst                         # noqa: E402
from auth import get_auth_provider, UserContext     # noqa: E402

MODEL = get_model()
ANALYST = Analyst(MODEL)
AUTH = get_auth_provider()

# In-memory session store: token -> {"user": UserContext, "last_intent": QueryIntent}
SESSIONS: dict[str, dict] = {}

SUGGESTED_PROMPTS = [
    "Show total sales by country",
    "Create a monthly sales trend for 2025",
    "Top 10 customers by revenue",
    "Profit growth by product (YoY)",
    "Sales by product category as a bar chart",
    "Compare revenue between UK, India and USA",
    "Profit margin by category using a line chart",
    "Create a dashboard showing sales, profit, quantity and YoY growth",
]

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
            return self._json({"status": "ok", "model": MODEL.meta.get("name"),
                               "llm": ANALYST.planner.using_llm})
        if route == "/api/model":
            summary = MODEL.summary()
            summary["suggestedPrompts"] = SUGGESTED_PROMPTS
            summary["authMode"] = AUTH.mode
            return self._json(summary)
        return self._serve_static(route)

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/api/connect":
            return self._connect()
        if route == "/api/chat":
            return self._chat()
        self.send_error(404, "Not found")

    # ---- endpoints ----
    def _connect(self):
        data = self._body()
        try:
            user = AUTH.connect(data.get("email", ""))
        except ValueError as exc:
            return self._json({"ok": False, "error": str(exc)}, status=400)
        except NotImplementedError as exc:
            return self._json({"ok": False, "error": str(exc)}, status=501)
        SESSIONS[user.token] = {"user": user, "last_intent": None}
        return self._json({
            "ok": True,
            "session": user.token,
            "user": {"name": user.name, "email": user.email},
            "workspaces": user.workspaces,
            "rls": bool(user.rls_filters),
            "authMode": AUTH.mode,
        })

    def _chat(self):
        sess = self._session()
        if not sess:
            return self._json({"ok": False, "error": "Not connected. Please sign in to Power BI."},
                              status=401)
        data = self._body()
        message = (data.get("message") or "").strip()
        if not message:
            return self._json({"ok": False, "error": "Empty message."}, status=400)

        prev = sess.get("last_intent")
        prev_intent = QueryIntent(**prev) if prev else None
        t0 = time.time()
        result = ANALYST.handle(message, sess["user"], prev_intent)
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        # remember intent for follow-ups (single-visual intents only)
        if result.get("ok") and result.get("kind") != "report" and result.get("intent"):
            sess["last_intent"] = result["intent"]
        return self._json(result)


def main():
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Power BI AI Chatbot running at http://{host}:{port}")
    print(f"  Semantic model: {MODEL.meta.get('name')} | "
          f"tables={len(MODEL.meta['tables'])} measures={len(MODEL.measures)} "
          f"| LLM planner={'on' if ANALYST.planner.using_llm else 'off (rule-based)'}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        httpd.shutdown()


if __name__ == "__main__":
    main()

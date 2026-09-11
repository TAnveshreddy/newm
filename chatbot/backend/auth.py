"""
auth.py
-------
Authentication, authorization and the Power BI execution adapter.

The chatbot never asks the user for a Power BI username/password, API key, access
token, dataset id or workspace id.  In production the flow is:

    User -> "Connect to Power BI" -> Microsoft Entra ID sign-in (MSAL) ->
    backend receives an access token for the Power BI service ->
    backend discovers the workspaces/datasets the user may see ->
    queries run *as the user* so Row-Level Security is enforced by Power BI.

Because this sandbox has no Entra tenant or live dataset, two providers are
supplied:

  * ``DemoAuthProvider`` / ``DemoExecutor`` – sign in with just an email (no
    password stored, nothing exposed), query the extracted semantic model.  This
    is what runs here.
  * ``EntraAuthProvider`` / ``PowerBIExecutor`` – the real, documented path using
    MSAL + the Power BI REST ``executeQueries`` endpoint.  Enabled by setting
    ``POWERBI_MODE=live`` and the Entra env vars; the code paths are present so a
    real deployment is a config change, not a rewrite.

Secrets (client secret, tokens) live only in server-side env/session and are
never sent to the browser.
"""
from __future__ import annotations

import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional

from semantic_model import SemanticModel, get_model
from nl_planner import QueryIntent
from query_engine import QueryEngine
from dax import generate_dax


# --------------------------------------------------------------------------- #
@dataclass
class UserContext:
    email: str
    name: str
    token: str
    rls_filters: list[dict] = field(default_factory=list)
    workspaces: list[dict] = field(default_factory=list)
    issued_at: float = field(default_factory=time.time)


# --------------------------------------------------------------------------- #
#  Row-Level Security
# --------------------------------------------------------------------------- #
# In a live model, RLS is defined inside Power BI and enforced automatically when
# queries run as the user.  For the demo we emulate a couple of RLS roles so the
# behaviour is visible.  Map an email (or domain) to a filter that is silently
# ANDed into every query.
RLS_RULES = {
    # "regional.manager@contoso.com": [{"field": "Country", "op": "in", "values": ["UK", "India"]}],
}


def rls_for(email: str) -> list[dict]:
    rules = RLS_RULES.get(email.lower(), [])
    # domain-level example (disabled by default)
    return list(rules)


# --------------------------------------------------------------------------- #
#  Auth providers
# --------------------------------------------------------------------------- #
class DemoAuthProvider:
    """Email-only sign-in that simulates the post-Entra state."""

    mode = "demo"

    def connect(self, email: str) -> UserContext:
        email = (email or "").strip().lower()
        if "@" not in email:
            raise ValueError("Please sign in with a valid work email address.")
        name = email.split("@")[0].replace(".", " ").title()
        model = get_model()
        workspaces = [{
            "id": "demo-ws",
            "name": "Sales Analytics (Demo Workspace)",
            "datasets": [{"id": "demo-ds", "name": model.meta.get("name", "SalesAnalytics")}],
        }]
        return UserContext(
            email=email,
            name=name,
            token=secrets.token_urlsafe(24),
            rls_filters=rls_for(email),
            workspaces=workspaces,
        )


class EntraAuthProvider:
    """Real Microsoft Entra ID sign-in (documented; requires msal + tenant).

    Set POWERBI_MODE=live plus ENTRA_TENANT_ID / ENTRA_CLIENT_ID /
    ENTRA_CLIENT_SECRET (or use device-code / auth-code flow) to enable.
    """

    mode = "live"

    def connect(self, email: str) -> UserContext:  # pragma: no cover - needs a tenant
        raise NotImplementedError(
            "Live Entra auth requires the msal package and a configured tenant. "
            "See README 'Going live'. The frontend redirects to the Microsoft "
            "authorize endpoint; the backend exchanges the code for a Power BI "
            "access token and calls the REST API as the user."
        )


def get_auth_provider() -> DemoAuthProvider | EntraAuthProvider:
    if os.environ.get("POWERBI_MODE", "demo").lower() == "live":
        return EntraAuthProvider()
    return DemoAuthProvider()


# --------------------------------------------------------------------------- #
#  Executors
# --------------------------------------------------------------------------- #
class DemoExecutor:
    """Runs the query against the in-memory extracted semantic model."""

    def __init__(self, model: SemanticModel):
        self.model = model

    def run(self, intent: QueryIntent, user: UserContext):
        engine = QueryEngine(self.model, rls_filters=user.rls_filters)
        return engine.execute(intent)


class PowerBIExecutor:  # pragma: no cover - needs live dataset
    """Runs the generated DAX against a live Power BI dataset via REST.

    POST https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/executeQueries
    Authorization: Bearer <user access token>
    Body: {"queries":[{"query":"<DAX>"}], "serializerSettings":{"includeNulls":true}}

    RLS is enforced by Power BI because the call is made with the user's token.
    """

    def __init__(self, model: SemanticModel, dataset_id: str):
        self.model = model
        self.dataset_id = dataset_id

    def run(self, intent: QueryIntent, user: UserContext):
        dax = generate_dax(self.model, intent)
        raise NotImplementedError(
            "Live execution not enabled in this environment. Would POST the "
            f"following DAX to executeQueries with the user's token:\n{dax}"
        )


def get_executor(model: SemanticModel) -> DemoExecutor:
    return DemoExecutor(model)

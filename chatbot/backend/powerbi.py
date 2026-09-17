"""
powerbi.py
----------
Live Power BI Service integration.

This is the ``POWERBI_MODE=live`` path.  It:
  * signs the user in with Microsoft Entra ID (OAuth2 authorization-code flow) —
    no API key / token / client secret / Power BI credentials are ever requested
    from or shown to the end user;
  * lists the workspaces, reports and datasets the *signed-in user* is allowed to
    see (dynamically, nothing hardcoded);
  * builds a live semantic-model catalog from the selected dataset's own metadata
    (tables, columns, measures, relationships) read via the INFO.VIEW.* DAX
    functions;
  * executes the DAX generated from the user's natural-language question against
    the live dataset via the REST ``executeQueries`` endpoint — as the user, so
    the dataset's Row-Level Security is enforced by Power BI.

Only the Python standard library is used (urllib), so there is no extra
dependency to install.  Every network call is isolated in small methods so the
parsing/mapping logic can be unit-tested offline with recorded JSON.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from semantic_model import SemanticModel, Measure, Dimension, _guess_format
from query_engine import QueryResult

AUTHORITY = "https://login.microsoftonline.com"
# Power BI delegated scopes (offline_access gives a refresh token).
SCOPES = [
    "https://analysis.windows.net/powerbi/api/Dataset.Read.All",
    "https://analysis.windows.net/powerbi/api/Report.Read.All",
    "https://analysis.windows.net/powerbi/api/Workspace.Read.All",
    "offline_access",
    "openid",
    "profile",
]
API_BASE = "https://api.powerbi.com/v1.0/myorg"


class PowerBIError(Exception):
    pass


# --------------------------------------------------------------------------- #
#  Configuration (all from server-side env — never from the browser)
# --------------------------------------------------------------------------- #
class EntraConfig:
    def __init__(self, tenant=None, client_id=None, client_secret=None, redirect_uri=None):
        # Explicit args (e.g. from the in-app connect form) win over env vars.
        self.tenant = tenant or os.environ.get("ENTRA_TENANT_ID", "")
        self.client_id = client_id or os.environ.get("ENTRA_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("ENTRA_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri or os.environ.get(
            "ENTRA_REDIRECT_URI", "http://localhost:8000/api/auth/callback")

    @property
    def configured(self) -> bool:
        return bool(self.tenant and self.client_id and self.client_secret)

    def authorize_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": " ".join(SCOPES),
            "state": state,
        }
        return f"{AUTHORITY}/{self.tenant}/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)

    def token_url(self) -> str:
        return f"{AUTHORITY}/{self.tenant}/oauth2/v2.0/token"


# --------------------------------------------------------------------------- #
#  OAuth token exchange (stdlib)
# --------------------------------------------------------------------------- #
def _post_form(url: str, form: dict) -> dict:
    data = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:  # surface Entra's error description
        body = exc.read().decode(errors="replace")
        raise PowerBIError(f"Token endpoint error {exc.code}: {body}") from exc


def exchange_code(cfg: EntraConfig, code: str) -> dict:
    """Authorization code -> token set ({access_token, refresh_token, expires_in})."""
    return _post_form(cfg.token_url(), {
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": cfg.redirect_uri,
        "scope": " ".join(SCOPES),
    })


def refresh_access_token(cfg: EntraConfig, refresh_token: str) -> dict:
    return _post_form(cfg.token_url(), {
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": " ".join(SCOPES),
    })


def acquire_app_token(cfg: EntraConfig) -> dict:
    """Client-credentials flow: the app's OWN token (Service Principal, no user)."""
    return _post_form(cfg.token_url(), {
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "grant_type": "client_credentials",
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    })


class AppTokenSet:
    """Service-principal token: re-acquired via client-credentials when it expires."""

    def __init__(self, cfg: EntraConfig):
        self.cfg = cfg
        self.access_token = ""
        self.expires_at = 0.0

    def valid_token(self) -> str:
        if time.time() >= self.expires_at:
            t = acquire_app_token(self.cfg)
            self.access_token = t.get("access_token", "")
            self.expires_at = time.time() + int(t.get("expires_in", 3600)) - 60
        return self.access_token


class TokenSet:
    """Holds a user's tokens server-side and refreshes transparently."""

    def __init__(self, cfg: EntraConfig, tokens: dict):
        self.cfg = cfg
        self.access_token = tokens.get("access_token", "")
        self.refresh_token = tokens.get("refresh_token", "")
        self.expires_at = time.time() + int(tokens.get("expires_in", 3600)) - 60

    def valid_token(self) -> str:
        if time.time() >= self.expires_at and self.refresh_token:
            fresh = refresh_access_token(self.cfg, self.refresh_token)
            self.access_token = fresh.get("access_token", self.access_token)
            if fresh.get("refresh_token"):
                self.refresh_token = fresh["refresh_token"]
            self.expires_at = time.time() + int(fresh.get("expires_in", 3600)) - 60
        return self.access_token


# --------------------------------------------------------------------------- #
#  REST client
# --------------------------------------------------------------------------- #
class PowerBIClient:
    def __init__(self, token_provider):
        # token_provider: callable returning a valid bearer token string
        self._token = token_provider

    def _get(self, path: str) -> dict:
        req = urllib.request.Request(API_BASE + path,
                                     headers={"Authorization": f"Bearer {self._token()}"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raise PowerBIError(f"GET {path} -> {exc.code}: {exc.read().decode(errors='replace')}") from exc

    def _post(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            API_BASE + path, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self._token()}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raise PowerBIError(f"POST {path} -> {exc.code}: {exc.read().decode(errors='replace')}") from exc

    # ---- discovery ----
    def list_workspaces(self) -> list[dict]:
        return self._get("/groups").get("value", [])

    def list_datasets(self, group_id: Optional[str] = None) -> list[dict]:
        path = f"/groups/{group_id}/datasets" if group_id else "/datasets"
        return self._get(path).get("value", [])

    def list_reports(self, group_id: Optional[str] = None) -> list[dict]:
        path = f"/groups/{group_id}/reports" if group_id else "/reports"
        return self._get(path).get("value", [])

    # ---- query ----
    def execute_dax(self, dataset_id: str, dax: str, group_id: Optional[str] = None) -> list[dict]:
        path = (f"/groups/{group_id}/datasets/{dataset_id}/executeQueries"
                if group_id else f"/datasets/{dataset_id}/executeQueries")
        payload = {"queries": [{"query": dax}],
                   "serializerSettings": {"includeNulls": True}}
        raw = self._post(path, payload)
        return parse_execute_results(raw)


# --------------------------------------------------------------------------- #
#  Parsers (pure functions — unit-tested offline)
# --------------------------------------------------------------------------- #
def parse_execute_results(raw: dict) -> list[dict]:
    """Return the first result table's rows: [{ 'Table[Col]'|'[Measure]': value }]."""
    try:
        return raw["results"][0]["tables"][0]["rows"]
    except (KeyError, IndexError, TypeError):
        return []


def strip_col_key(key: str) -> tuple[Optional[str], str]:
    """'Customers[Country]' -> ('Customers','Country'); '[Total Revenue]' -> (None,'Total Revenue')."""
    if "[" in key and key.endswith("]"):
        table, col = key.split("[", 1)
        return (table or None), col[:-1]
    return None, key


# --------------------------------------------------------------------------- #
#  Discover reports/datasets the user can see (for the dropdown)
# --------------------------------------------------------------------------- #
def discover_dashboards(client: PowerBIClient) -> list[dict]:
    """Return a flat, de-duplicated list of selectable dashboards:
       [{id(dataset), name, datasetId, groupId, groupName, reportName}].
    Reports are preferred as the user-facing 'dashboard' name; each maps to its
    dataset.  Datasets without a report are still listed so nothing is hidden."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    workspaces = client.list_workspaces()
    # include "My workspace" (group_id None)
    scopes = [(None, "My workspace")] + [(w["id"], w.get("name", "Workspace")) for w in workspaces]
    for group_id, group_name in scopes:
        try:
            reports = client.list_reports(group_id)
        except PowerBIError:
            reports = []
        for r in reports:
            ds_id = r.get("datasetId")
            if not ds_id:
                continue
            key = (group_id or "", ds_id)
            out.append({
                "id": f"{group_id or 'me'}::{ds_id}",
                "name": r.get("name", "Report"),
                "datasetId": ds_id,
                "groupId": group_id,
                "groupName": group_name,
                "reportName": r.get("name"),
            })
            seen.add(key)
        try:
            datasets = client.list_datasets(group_id)
        except PowerBIError:
            datasets = []
        for d in datasets:
            key = (group_id or "", d["id"])
            if key in seen:
                continue
            out.append({
                "id": f"{group_id or 'me'}::{d['id']}",
                "name": d.get("name", "Dataset"),
                "datasetId": d["id"],
                "groupId": group_id,
                "groupName": group_name,
                "reportName": None,
            })
            seen.add(key)
    return out


# --------------------------------------------------------------------------- #
#  Live semantic model (duck-types SemanticModel so the planner/dax/viz reuse it)
# --------------------------------------------------------------------------- #
# DAX to read the model's own metadata (INFO.VIEW.* returns friendly names).
DAX_MEASURES = "EVALUATE INFO.VIEW.MEASURES()"
DAX_COLUMNS = "EVALUATE INFO.VIEW.COLUMNS()"
DAX_RELATIONSHIPS = "EVALUATE INFO.VIEW.RELATIONSHIPS()"
DAX_TABLES = "EVALUATE INFO.VIEW.TABLES()"


class LiveModel(SemanticModel):
    """A SemanticModel whose catalog comes from a live Power BI dataset."""

    def __init__(self, client: PowerBIClient, dataset_id: str, group_id: Optional[str],
                 display_name: str):
        self.client = client
        self.dataset_id = dataset_id
        self.group_id = group_id
        self.profile = "live"
        self.data_dir = ""
        self._distinct_cache: dict[str, list] = {}

        measures_rows = self._safe(DAX_MEASURES)
        columns_rows = self._safe(DAX_COLUMNS)
        rel_rows = self._safe(DAX_RELATIONSHIPS)
        table_rows = self._safe(DAX_TABLES)

        self.meta = self._build_meta(display_name, table_rows, columns_rows, rel_rows)
        self.fact_table = self._pick_fact(rel_rows, table_rows)
        self.measures = self._build_measures_live(measures_rows)
        self.dimensions = self._build_dimensions_live(columns_rows, rel_rows)
        self.synonyms = {}
        self.definitions = {}
        self._synonym_index = self._build_synonym_index()
        self.years = self._discover_years()

    # ---- helpers ----
    def _safe(self, dax: str) -> list[dict]:
        try:
            return self.client.execute_dax(self.dataset_id, dax, self.group_id)
        except PowerBIError:
            return []

    @staticmethod
    def _clean(rows: list[dict]) -> list[dict]:
        """INFO.VIEW.* returns keys like '[Name]' — strip the brackets."""
        out = []
        for r in rows:
            out.append({strip_col_key(k)[1]: v for k, v in r.items()})
        return out

    def _build_meta(self, name, table_rows, column_rows, rel_rows) -> dict:
        tables = self._clean(table_rows)
        cols = self._clean(column_rows)
        by_table: dict[str, list] = {}
        for c in cols:
            by_table.setdefault(c.get("Table"), []).append(
                {"name": c.get("Name"), "dataType": self._map_type(c.get("DataType"))})
        tmeta = []
        for t in tables:
            tn = t.get("Name")
            tmeta.append({"name": tn, "rowCount": None, "columns": by_table.get(tn, [])})
        if not tmeta:  # fall back to whatever tables columns referenced
            for tn, cc in by_table.items():
                tmeta.append({"name": tn, "rowCount": None, "columns": cc})
        rels = []
        for r in self._clean(rel_rows):
            rels.append({
                "fromTable": r.get("FromTable") or r.get("FromTableName"),
                "fromColumn": r.get("FromColumn") or r.get("FromColumnName"),
                "toTable": r.get("ToTable") or r.get("ToTableName"),
                "toColumn": r.get("ToColumn") or r.get("ToColumnName"),
                "crossFilteringBehavior": "oneDirection",
            })
        return {"name": name, "profile": "live", "tables": tmeta, "relationships": rels,
                "description": "Live Power BI dataset"}

    @staticmethod
    def _map_type(dt: Optional[str]) -> str:
        d = (dt or "").lower()
        if d in ("int64", "integer", "whole number"):
            return "int64"
        if d in ("double", "decimal", "currency", "fixed decimal number"):
            return "double"
        if d in ("datetime", "date", "datetimezone"):
            return "dateTime"
        return "string"

    def _pick_fact(self, rel_rows, table_rows) -> str:
        from collections import Counter
        rels = self._clean(rel_rows)
        counts = Counter((r.get("FromTable") or r.get("FromTableName")) for r in rels)
        if counts:
            return counts.most_common(1)[0][0]
        tables = self._clean(table_rows)
        return tables[0].get("Name") if tables else ""

    def _build_measures_live(self, measure_rows) -> dict[str, Measure]:
        out: dict[str, Measure] = {}
        for m in self._clean(measure_rows):
            name = m.get("Name")
            if not name:
                continue
            expr = m.get("Expression", "")
            fs = m.get("FormatString", "")
            # Kind is only used for classification; execution is 100% via DAX by name.
            out[name] = Measure(name=name, kind="sum", dax=(expr or f"[{name}]"),
                                fmt=_guess_format(name, fs),
                                definition=m.get("Description", "") or "")
        return out

    def _build_dimensions_live(self, column_rows, rel_rows) -> dict[str, Dimension]:
        d: dict[str, Dimension] = {}
        cols = self._clean(column_rows)
        used = set()

        def add(name, table, col, is_time=False, grain=None):
            label = name if name not in used else f"{table} {name}"
            used.add(label)
            d[label] = Dimension(label, col, table, col, is_time=is_time, time_grain=grain)

        for c in cols:
            name = c.get("Name")
            table = c.get("Table")
            dt = self._map_type(c.get("DataType"))
            if not name or not table:
                continue
            if str(c.get("IsHidden", False)).lower() == "true":
                continue
            low = name.lower()
            if dt == "string":
                add(name, table, name)
            elif dt == "int64" and low in ("year",):
                add("Year", table, name, is_time=True, grain="year")
            elif low in ("month", "month name", "monthname"):
                add("Month", table, name, is_time=True, grain="month")
            elif low in ("quarter",):
                add("Quarter", table, name, is_time=True, grain="quarter")
        return d

    # ---- live overrides ----
    def distinct_values(self, dim_name: str) -> list:
        if dim_name in self._distinct_cache:
            return self._distinct_cache[dim_name]
        dim = self.dimensions[dim_name]
        dax = f"EVALUATE VALUES('{dim.table}'[{dim.source_column}])"
        vals = []
        for row in self._safe(dax):
            for v in row.values():
                if v is not None:
                    vals.append(v)
        try:
            vals = sorted(set(vals), key=lambda x: (str(type(x)), x))
        except TypeError:
            vals = list(dict.fromkeys(vals))
        self._distinct_cache[dim_name] = vals
        return vals

    def _discover_years(self) -> list[int]:
        for name, dim in self.dimensions.items():
            if dim.is_time and dim.time_grain == "year":
                try:
                    return sorted(int(v) for v in self.distinct_values(name) if v is not None)
                except (ValueError, TypeError):
                    return []
        return []


# --------------------------------------------------------------------------- #
#  Live executor: run the generated DAX and map results into a QueryResult
# --------------------------------------------------------------------------- #
class LiveExecutor:
    def __init__(self, model: LiveModel, client: PowerBIClient):
        self.model = model
        self.client = client

    def run(self, intent, user=None) -> QueryResult:
        from dax import generate_dax
        res = QueryResult()
        res.measures = intent.measures or [next(iter(self.model.measures), "")]
        res.dimension = intent.dimension
        try:
            dax = generate_dax(self.model, intent)
            rows = self.client.execute_dax(self.model.dataset_id, dax, self.model.group_id)
        except PowerBIError as exc:
            res.error = f"Power BI query failed: {exc}"
            return res
        return map_rows_to_result(self.model, intent, rows, res)


def map_rows_to_result(model, intent, rows: list[dict], res: QueryResult) -> QueryResult:
    """Translate executeQueries rows (keys like 'Customers[Country]', '[Measure]')
    into the QueryResult shape the viz layer expects."""
    # Build the key -> output-column map from the intent.
    dim_field = None
    key_map: dict[str, str] = {}
    columns = []
    if intent.dimension:
        dim = model.dimensions[intent.dimension]
        dim_field = _period_label(intent) or dim.name
        key_map[f"{dim.table}[{dim.source_column}]"] = dim_field
        key_map[dim.source_column] = dim_field
        columns.append({"name": dim_field, "role": "dimension", "format": "text"})
    if intent.secondary_dimension:
        sd = model.dimensions[intent.secondary_dimension]
        key_map[f"{sd.table}[{sd.source_column}]"] = sd.name
        columns.append({"name": sd.name, "role": "dimension", "format": "text"})
    for m in res.measures:
        key_map[f"[{m}]"] = m
        key_map[m] = m
        fmt = model.measures[m].fmt if m in model.measures else "number"
        columns.append({"name": m, "role": "measure", "format": fmt})

    out_rows = []
    for r in rows:
        nr = {}
        for k, v in r.items():
            name = key_map.get(k)
            if name is None:
                _, bare = strip_col_key(k)
                name = key_map.get(bare, bare)
            nr[name] = v
        out_rows.append(nr)

    res.rows = out_rows
    res.columns = columns
    res.dimension = intent.dimension
    if intent.time_grain and dim_field:
        res.period_field = dim_field
    if intent.secondary_dimension:
        res.series_field = model.dimensions[intent.secondary_dimension].name
    return res


def _period_label(intent) -> Optional[str]:
    return {"month": "Month", "quarter": "Quarter", "year": "Year"}.get(intent.time_grain)

# Architecture

This document maps the implementation to the target architecture in the guide.

## High-level flow

```
User
  │
  ▼
Web Chatbot (React + TypeScript)  ── Static Web Apps / Front Door (TLS, WAF)
  │  (Entra ID access token, audience = backend API)
  ▼
Secure Backend API (Azure App Service, Node + Express)
  ├──► Azure OpenAI      (intent + structured plan; never executes queries)
  ├──► Azure Key Vault   (secrets via managed identity)
  └──► Power BI Semantic Model (validated query execution, RLS respected)
  │
  ▼
Validated Query Result  ──►  Ad-hoc Visualization Engine (ECharts)  ──►  User
```

The browser **never** calls Azure OpenAI or Power BI directly and never holds a
Power BI token or any server secret (NFR §3). Every data path goes through the
backend, which authenticates the user and authorizes the request first.

## Controlled AI orchestration pipeline (Phase 7)

The LLM proposes; the backend disposes. The model can only emit a structured
`AiPlan`; it never runs a query.

```
prompt
  → intent classification            (AiClient.plan)
  → candidate fields from metadata   (semantic model metadata, whitelisted)
  → structured QueryPlan             (declarative, no DAX/SQL text)
  → VALIDATE against metadata        (QueryValidator — rejects invented fields)
  → execute only the validated plan  (PowerBiClient, server-side auth)
  → normalized QueryResult
  → VisualSpec                       (VisualSpecService)
  → typed ChatResponse               (to the frontend)
```

Key guarantee: **no field, measure, or model that isn't in the authorized
metadata can ever be queried**, because validation happens between the AI's
proposal and execution (`aiOrchestrator.ts` → `queryValidator.ts`).

## Backend components (`backend/src`)

| Path | Responsibility |
| --- | --- |
| `controllers/` | HTTP endpoints (Phase 4) — health, me, models, chat, query, visuals, conversations |
| `middleware/authMiddleware.ts` | Entra ID token validation on every protected route (Phase 5) |
| `middleware/rateLimiter.ts` | Per-user rate limiting for chat/query (Phase 11) |
| `middleware/errorHandler.ts` | Sanitized error → status mapping (§25) |
| `auth/entraId.ts` | JWKS signature + issuer/audience/expiry validation |
| `services/semanticmodel/` | Model registry (authorization) + metadata discovery/cache (Phase 6) |
| `services/ai/` | System prompt (§15), OpenAI client, orchestrator (Phase 7) |
| `validators/queryValidator.ts` | Plan validation + normalization (Phase 8) |
| `services/powerbi/` | Metadata discovery + query execution (Phase 6/8) |
| `services/visualization/` | VisualSpec generation (Phase 9) |
| `services/conversation/` | Server-side conversation state (Phase 10) |

## Frontend components (`frontend/src`)

`ChatWindow` → `MessageList` → `Visualization` (ECharts), with `PromptInput`,
`LoadingState`, `ErrorState`. `auth/` wraps MSAL; `services/api.ts` is the only
place that talks to the backend, always with a bearer token.

## Mock mode

`MOCK_MODE=true` (and `VITE_MOCK_AUTH=true`) swap in in-process adapters:

- `MockTokenValidator` — accepts `mock:{…}` bearer tokens.
- `MockAiClient` — deterministic rules-based planner reproducing the §26
  scenarios.
- `MockPowerBiClient` — synthesizes deterministic sample rows for the
  `sales-analytics` model.

This makes the **entire pipeline runnable and testable with no Azure/Power BI
resources**. The security-critical logic (validation, authorization,
conversation ownership, visual reconciliation) is identical in mock and live
mode — only the external I/O adapters change.

## Endpoints (Phase 4)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Liveness (public) |
| GET | `/api/me` | Authenticated identity/claims |
| GET | `/api/models` | Models the user is authorized to use |
| GET | `/api/models/:id/metadata` | Approved, cached, sanitized metadata |
| POST | `/api/chat` | Main NL request (full pipeline) |
| POST | `/api/query/validate` | Validate a plan before execution |
| POST | `/api/query/execute` | Execute a validated plan |
| POST | `/api/visuals/generate` | Build a visual spec from a result |
| GET | `/api/conversations/:id` | Conversation context (owner only) |

# Security

How this implementation satisfies the guide's non-functional and security
requirements (NFR §3, Phase 5, Phase 11).

## Secrets never reach the browser

- The frontend bundle contains only **public** values: tenant ID, client ID,
  API scope, API base URL (`frontend/.env.example`, all `VITE_` prefixed).
- There is **no client secret** in the SPA; MSAL uses the public authorization
  code flow with PKCE.
- Tokens are cached in `sessionStorage`, never `localStorage`
  (`auth/authConfig.ts`).
- End users are never asked for an API key or Power BI token. The backend
  explicitly refuses to accept a Power BI token from a prompt (see below).

## Authentication & authorization (Phase 5)

- Every protected route runs `requireAuth`, which validates the Entra ID bearer
  token: signature against the tenant JWKS, plus issuer, audience and expiry
  (`auth/entraId.ts`). Raw tokens are never logged.
- `/api/models` returns only models the user is authorized to use; model access
  is gated by role/group rules in the model registry
  (`services/semanticmodel/modelRegistry.ts`).
- Metadata requests throw `ModelUnauthorizedError` → **403** and
  `ModelNotFoundError` → **404** (§25).
- Conversation state is owner-scoped: a user can never read another user's
  conversation (`services/conversation/conversationStore.ts`).

## The AI cannot invent or bypass

- The system prompt (§15) constrains the model to supplied metadata only.
- The model returns a **declarative plan**, never executable DAX/SQL.
- `QueryValidator` re-checks every table/column/measure/model against the
  cached metadata **before** execution and rejects unknown fields, unknown
  measures and unauthorized model IDs (`validators/queryValidator.ts`).
- `/api/query/execute` always re-validates — it never trusts a client-supplied
  "already validated" flag.
- Row limits are clamped server-side to prevent huge result sets.

## No token passthrough / injection

- The backend never accepts a Power BI token from user input; Power BI access
  uses a **server-side** flow (managed identity / delegated token) only.
- User input is never concatenated into query text — the plan is translated
  field-by-field from validated metadata references (`services/powerbi`).
- Backend tokens are never returned to the frontend.

## Transport & platform hardening (Phase 11)

- `helmet` sets secure response headers; `x-powered-by` disabled.
- CORS is restricted to approved origins (`ALLOWED_ORIGINS`).
- Request body size is capped (`MAX_REQUEST_BODY_BYTES`).
- Per-user rate limiting on chat/query endpoints.
- App Service enforces HTTPS-only and TLS 1.2 (`infra/bicep/main.bicep`).
- Secrets come from Key Vault via managed identity; the backend has no keys in
  app settings for OpenAI/Key Vault access.

## Auditing & error hygiene (§25)

- The request logger records method, path, user object ID, status and duration
  — **never** prompt text, results, or tokens (`middleware/requestLogger.ts`).
- The error handler returns sanitized, user-safe messages and logs internal
  detail server-side only.

## RLS / least privilege

- Power BI Row-Level Security is respected because queries execute under the
  appropriate identity server-side; the app never elevates beyond the user's
  authorization.
- Test with at least two users having different Power BI permissions
  (Phase 5 / Phase 13). The mock mode supports distinct users and role-gated
  models to exercise these paths in tests.

## Pre-production checklist

- [ ] `MOCK_MODE=false` and `VITE_MOCK_AUTH=false` in every deployed environment.
- [ ] Entra app registrations created; redirect URIs match deployed origins.
- [ ] Backend managed identity granted least-privilege Power BI + OpenAI access.
- [ ] Secrets stored in Key Vault; none in source control or app settings.
- [ ] CORS origins locked to the real frontend domain(s).
- [ ] Front Door + WAF + custom domain + TLS configured for production.
- [ ] Application Insights alerts configured (auth failures, errors, latency).

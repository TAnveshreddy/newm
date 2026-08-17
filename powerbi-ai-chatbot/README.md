# Web-Based Power BI AI Chatbot

A secure, web-based AI chatbot that connects to an authorized Power BI semantic
model. Users authenticate with their company account, ask natural-language
questions, receive analytical answers, and create or modify ad-hoc visuals —
**without ever entering an API key, Power BI token, or database credential.**

This repository implements the *Power BI Web AI Chatbot Implementation &
Deployment Guide* end to end: React + TypeScript frontend, a secure Node +
TypeScript backend, a controlled AI-orchestration pipeline, Power BI
semantic-model integration, Entra ID authentication, infrastructure-as-code, and
CI/CD.

> **Runs with zero cloud credentials.** In **mock mode** the whole pipeline —
> auth, AI planning, Power BI queries — runs against in-process adapters, so you
> can try it locally immediately. Swapping in real Azure/Power BI/Entra
> resources is configuration only; the security-critical logic is identical.

## Repository layout

```
powerbi-ai-chatbot/
├── frontend/          React + TypeScript SPA (MSAL, ECharts)
├── backend/           Node + TypeScript API (Express)
│   ├── src/
│   │   ├── controllers/   HTTP endpoints (Phase 4)
│   │   ├── middleware/    auth, rate limit, error handling, audit log
│   │   ├── auth/          Entra ID token validation (Phase 5)
│   │   ├── services/
│   │   │   ├── ai/            system prompt, OpenAI client, orchestrator (Phase 7)
│   │   │   ├── powerbi/       metadata + query execution (Phase 6/8)
│   │   │   ├── semanticmodel/ model registry + metadata cache (Phase 6)
│   │   │   ├── visualization/ visual spec builder (Phase 9)
│   │   │   └── conversation/  server-side state (Phase 10)
│   │   └── validators/    query-plan validation (Phase 8)
│   └── tests/         unit + integration tests (Phase 13)
├── infra/bicep/       Azure resources (Phase 1)
├── docs/              ARCHITECTURE.md, SECURITY.md
└── .github/workflows/ CI + deploy (Phase 14)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how each part maps to the
guide, and [`docs/SECURITY.md`](docs/SECURITY.md) for the security model.

## Quick start (mock mode, no secrets)

Requires Node.js 20+.

**1. Backend**

```bash
cd backend
cp .env.example .env          # MOCK_MODE=true by default
npm install
npm run dev                   # http://localhost:8080
```

**2. Frontend** (in a second terminal)

```bash
cd frontend
cp .env.example .env          # VITE_MOCK_AUTH=true by default
npm install
npm run dev                   # http://localhost:5173
```

Open http://localhost:5173 and try:

- *"What are total sales for 2026?"* → KPI answer
- *"Create a bar chart of sales by region for 2026."* → bar chart
- *"Change it to a line chart."* → re-renders without re-querying
- *"Only show APAC."* → re-queries with the filter
- *"Show inventory turnover by region."* → reports it's unavailable (no hallucination)

## Testing

```bash
cd backend
npm test            # unit + integration (46 tests)
npm run lint
npm run typecheck
```

The suite covers the Phase 13 cases: unknown-field rejection, unauthorized /
not-found models, RLS-style per-user authorization, clarification, ad-hoc
visuals, follow-up filter/visual changes, and large-result protection.

## Going live

1. Provision Azure resources: `infra/bicep/main.bicep` (see `infra/README.md`).
2. Register the frontend SPA and backend API in Entra ID (`docs/SECURITY.md`).
3. Set backend app settings (`backend/appsettings.example.json`) with
   `MOCK_MODE=false`; source secrets from Key Vault.
4. Set frontend build vars (`VITE_ENTRA_*`, `VITE_MOCK_AUTH=false`).
5. Deploy via `.github/workflows/deploy.yml` (DEV → TEST → PROD with approvals).

## Configuration

- **Backend:** `backend/.env.example` (non-secret) + Key Vault for secrets.
- **Frontend:** `frontend/.env.example` — public values only; nothing secret
  ever enters the browser bundle.

## Design decision: rendering vs native Power BI visuals

Per §29 of the guide, first-release ad-hoc visuals are rendered in the web app
with ECharts while Power BI remains the governed semantic/data layer. Deeper
Power BI embedding is a later phase.

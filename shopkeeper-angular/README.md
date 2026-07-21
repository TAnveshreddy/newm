# Shopkeeper — Angular (Desktop Web App)

An enterprise-architected **Angular 18** rebuild of the Shopkeeper business
manager (Billing · Inventory · Khata), running against the **same Firebase /
Firestore backend and schema** as the original single-file app — no data
migration, no schema changes. Both apps can run side-by-side on the same data.

## Tech stack

| Concern | Choice |
|---|---|
| Framework | Angular 18 (standalone APIs, no NgModules) |
| Reactivity | Signals + a thin RxJS layer at the Firebase boundary |
| Backend | Firebase Auth (Google + Phone OTP) + Cloud Firestore (`@angular/fire`) |
| Offline | Firestore persistent local cache (multi-tab) — works offline, auto-syncs |
| Styling | SCSS design system, theme-aware (light/dark) |
| Build | Angular application builder, esbuild, per-route code-splitting |

## Architecture

```
src/
├── environments/                 # public Firebase config (dev + prod)
└── app/
    ├── app.config.ts             # providers: router, firebase, http interceptors, animations
    ├── app.routes.ts             # top-level routes — all features lazy-loaded
    ├── core/                     # singletons, no UI (imported once)
    │   ├── models/               # domain types — mirror the Firestore schema 1:1
    │   ├── domain/               # transaction metadata (stock/ledger rules)
    │   ├── services/
    │   │   ├── auth.service.ts            # Google + OTP, profile provisioning
    │   │   ├── firestore-data.service.ts  # typed, uid-scoped Firestore gateway
    │   │   ├── business-store.service.ts  # reactive store + all domain math
    │   │   ├── admin.service.ts           # users/* administration
    │   │   ├── theme.service.ts, toast.service.ts
    │   ├── guards/                # authGuard, adminGuard (functional)
    │   ├── interceptors/          # errorInterceptor (functional)
    │   └── util/                  # pure helpers (num, dates, ids)
    ├── shared/                    # reusable, presentational
    │   ├── components/            # kpi-card, bar-chart, toast
    │   ├── layout/                # authenticated app shell (sidebar + topbar)
    │   └── pipes/                 # inr currency pipe
    └── features/                  # lazy-loaded route components
        ├── auth/ (login)
        ├── dashboard/            # KPIs, chart, business summary, low-stock, recent txns
        ├── inventory/           # products, stock, barcode + generate
        ├── billing/             # sale invoice, barcode scan, live totals
        ├── parties/             # khata (customers/suppliers) with live balances
        ├── reports/             # ranged P&L + transactions
        ├── settings/            # business profile, preferences, account
        └── admin/               # user management (roles, plans, activate, delete)
```

### Design principles
- **Clean layering** — `core` (singletons/logic) → `shared` (reusable UI) →
  `features` (routed screens). Features never import each other.
- **Lazy loading & code-splitting** — every feature is its own bundle,
  fetched on first navigation (see the per-route chunks in a prod build).
- **Signals-first state** — `BusinessStore` streams Firestore collections into
  signals; components read them synchronously and stay in sync across devices.
- **Same schema, reused** — `core/models` map exactly onto `users/{uid}` and
  `userData/{uid}/…`; the domain math (stock, balances, profit) is ported
  verbatim from the original app.

## Security
- **Authentication** — Firebase (Google + SMS OTP); session handled by the SDK.
- **Authorization** — `authGuard` (route + child) and `adminGuard` gate the
  shell and the admin module. Defence-in-depth — the **Firestore security
  rules** remain the real server-side boundary.
- **HTTP** — functional `errorInterceptor` centralises REST error handling;
  `provideHttpClient(withFetch())`.
- **XSS** — Angular's built-in contextual output encoding + template
  sanitisation; no `bypassSecurityTrust*` used.
- **Secrets** — only the *public* Firebase web config ships to the client (safe
  by design); no admin/service-account credentials anywhere.

## Getting started

```bash
cd shopkeeper-angular
npm install
npm start                 # dev server at http://localhost:4200
npm run build             # production build -> dist/shopkeeper-angular/browser
```

Firebase console prerequisites (same project, `shopkeeper-poc`): enable
Google + Phone sign-in, publish the Firestore rules, and add your serving
domain to **Authentication → Authorized domains**.

## Feature parity status

| Area | Status |
|---|---|
| Auth (Google + Mobile OTP) | ✅ |
| Multi-device Firestore sync + offline | ✅ |
| Dashboard (KPIs, chart, summary, low-stock, recent txns) | ✅ |
| Inventory + barcode (scan / generate) | ✅ |
| Billing (scan, picker, live GST totals, save) | ✅ |
| Khata (parties, live balances) | ✅ |
| Reports (ranged P&L + transactions) | ✅ |
| Settings (profile, preferences, account) | ✅ |
| Admin console (users, roles, plans, activate/delete) | ✅ |
| Estimates / Purchases / Returns / Payments / Expenses forms | ⏳ next (schema + store already support them) |
| Invoice PDF/print, barcode label sheet | ⏳ next |

These remaining items reuse the same `BusinessStore` + models and slot into the
existing `features/` structure without architectural changes.

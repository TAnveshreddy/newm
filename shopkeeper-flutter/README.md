# Shopkeeper — Flutter (Mobile App)

A **Flutter** (Android + iOS) build of the Shopkeeper business manager
(Billing · Inventory · Khata), running against the **same Firebase / Firestore
backend and schema** as the web + Angular apps — no data migration. All three
clients share one dataset and sync in real time.

## Tech stack

| Concern | Choice |
|---|---|
| Framework | Flutter 3.44 / Dart 3.12, Material 3 |
| State | Riverpod (reactive providers over Firestore streams) |
| Routing / guards | go_router with an auth-state redirect |
| Backend | firebase_auth (Google + Phone OTP) + cloud_firestore |
| Offline | Firestore local persistence (works offline, syncs on reconnect) |

## Architecture

```
lib/
├── main.dart                 # Firebase init + offline persistence + runApp(ProviderScope)
├── app.dart                  # MaterialApp.router + go_router auth guard
├── firebase_options.dart     # project config (same shopkeeper-poc project)
├── core/
│   ├── models/               # domain models — mirror the Firestore schema 1:1
│   ├── domain/               # transaction metadata (stock/ledger rules)
│   ├── util/                 # pure helpers (num, dates, ids, money)
│   ├── theme/                # Material 3 light/dark theme
│   ├── services/             # AuthService, FirestoreService, AdminService
│   └── state/                # Riverpod providers + Calc (derived business logic)
├── shared/widgets/           # reusable UI (KpiCard)
└── features/
    ├── auth/                 # login (Google + Mobile OTP)
    ├── shell/                # bottom-nav shell + More/account
    ├── dashboard/            # KPIs, low-stock, recent transactions
    ├── inventory/            # products, stock, add/edit
    ├── billing/              # sale invoice (search-add, live GST totals)
    ├── parties/              # khata (customers/suppliers, live balances)
    └── admin/                # user management (roles, plans, activate/delete)
```

### Design principles
- **Clean layering:** `core` (models/services/logic) → `shared` → `features`.
- **Reactive & efficient:** Firestore snapshot streams → Riverpod providers →
  `const` widgets and `ListView.builder`; screens rebuild only on real changes.
- **Same schema, reused:** models map onto `users/{uid}` and `userData/{uid}/…`;
  stock/balance/profit math (`core/state/calc.dart`) ported verbatim.

## Security
- **Auth:** Firebase (native Google Sign-In + SMS OTP); session by the SDK.
- **Authorization:** go_router redirect guard blocks unauthenticated access and
  gates `/admin` to admin profiles — plus the **Firestore rules** enforce the
  real boundary server-side (defence-in-depth).
- **No secrets:** only the public Firebase config is shipped; no service-account
  keys anywhere.
- **Input validation** on phone/OTP and forms; least-privilege writes.

## Performance
- Firestore **offline cache** with unlimited size → instant repeat loads, no
  network on cold open.
- Riverpod scoped providers + `IndexedStack` tabs (kept alive) + `const`
  widgets minimise rebuilds.
- Release builds use Dart AOT (Android/iOS) with icon tree-shaking.

## Run / build

```bash
cd shopkeeper-flutter
flutter pub get
flutter run                       # on a connected device / emulator

flutter build apk --release       # Android APK  -> build/app/outputs/flutter-apk/
flutter build appbundle --release # Play Store AAB
flutter build ios --release       # iOS (on macOS)
```

### Firebase device setup (one-time)
For real devices, generate proper platform config:
```bash
dart pub global activate flutterfire_cli
flutterfire configure --project=shopkeeper-poc
```
This writes `android/app/google-services.json` (and iOS plist) and refreshes
`firebase_options.dart`. Then, in the Firebase console:
- **Authentication → Sign-in method:** enable **Google** and **Phone**.
- **Phone auth on Android** needs your app's **SHA-1/SHA-256** fingerprints
  added to the Firebase Android app (Play Integrity / SafetyNet).
- Publish the Firestore **rules** (shared with the web app).

## Feature parity status

| Area | Status |
|---|---|
| Auth (Google + Mobile OTP) | ✅ |
| Multi-device Firestore sync + offline | ✅ |
| Dashboard (KPIs, low-stock, recent txns) | ✅ |
| Inventory (products, stock, add/edit, barcode field) | ✅ |
| Billing (search-add, live GST totals, save) | ✅ |
| Khata (parties, live balances) | ✅ |
| Admin console (users, roles, plans, activate/delete) | ✅ |
| Camera barcode scanning, invoice PDF, remaining txn forms | ⏳ next |

Verified: `flutter analyze` is clean and `flutter build web` compiles the full
app (all Dart + Firebase plugins).

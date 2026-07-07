# Vyapar Lite 🧾

A **Vyapar-style billing, inventory & party-ledger app** built with Flutter.
Works fully **offline** — all data is saved locally on your device as JSON
(no server or internet needed).

## Features

- 📊 **Dashboard** — To Collect, To Pay, Sales this month, Stock value, low-stock alerts
- 👥 **Parties** — customers & suppliers with running balance (you'll get / you'll pay)
- 📦 **Items** — inventory with sale/purchase price, GST rate, stock quantity, low-stock alert
- 🧾 **Sale invoices & Purchase bills** — multi-line items, automatic GST calculation,
  full/partial payment, auto stock & balance updates
- 💰 **Payment In / Payment Out** — settle party balances
- 💸 **Expenses** — record business expenses
- 📜 **Transactions list** — filter by type, tap for details, long-press to delete
  (deletion safely reverses stock & balance effects)

## How to run on your laptop

1. **Install Flutter** (one time): <https://docs.flutter.dev/get-started/install>
   — verify with `flutter doctor`.

2. **Get this folder** (clone the repo or download it), then in a terminal:

   ```bash
   cd vyapar_app

   # One time: generate the platform runner for your OS
   flutter create . --platforms=windows,macos,linux,android

   # Fetch dependencies
   flutter pub get

   # Run it (pick your platform)
   flutter run -d windows    # Windows laptop
   flutter run -d macos      # Mac
   flutter run -d linux      # Linux
   flutter run               # Android phone/emulator if connected
   ```

3. **Build an installable app** (optional):

   ```bash
   flutter build windows     # .exe in build/windows/x64/runner/Release/
   flutter build apk         # Android APK in build/app/outputs/
   ```

## Tech stack

| Layer         | Choice                                      |
|---------------|---------------------------------------------|
| UI            | Flutter (Material 3 widgets)                 |
| State         | `provider` (ChangeNotifier)                  |
| Storage       | Local JSON file via `path_provider` (offline-first) |
| Language      | Dart                                         |

## Where is my data stored?

A single file `vyapar_lite_data.json` inside your OS's app-documents folder
(e.g. `Documents` on Windows). Back it up to keep your records safe.

## Roadmap (not yet implemented)

- PDF invoice generation & sharing
- Cloud sync/backup (Firebase or Node.js + PostgreSQL backend)
- Reports (GST reports, party statements export)
- Barcode scanning, multi-user, payments via Razorpay

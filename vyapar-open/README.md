# VyaparOpen 🧾

**A free, open-source alternative to Vyapar** — GST billing, inventory, parties, payments, expenses and reports for small businesses. Runs **100% offline in your browser**: no installation, no account, no server, no tracking. Your data never leaves your device.

## 📥 Download & use (30 seconds)

**Option A — single file (easiest):**

1. Download [`dist/VyaparOpen.html`](dist/VyaparOpen.html) (click → "Download raw file").
2. Double-click the downloaded file. It opens in your browser — that's it, start billing.

**Option B — full source:**

1. Download this repository as a ZIP (green **Code** button → *Download ZIP*) and extract it.
2. Open `vyapar-open/index.html` in any modern browser (Chrome, Edge, Firefox, Safari).

Works on desktop, laptop and mobile browsers. No internet needed after download.

## ✨ Features (Vyapar-style)

| Area | What you get |
|---|---|
| **Sale invoices** | GST invoices with multi-line items, per-line & overall discount, round-off, received amount, balance due, payment modes (Cash/UPI/Card/Bank/Cheque/Credit) |
| **Invoice printing** | Print / save-as-PDF tax invoice with CGST+SGST or IGST split (auto-detected from GSTINs), HSN codes, amount in words, UPI ID, terms & signature |
| **Estimates / Quotations** | Create estimates and convert them to sale invoices in one click |
| **Purchases** | Purchase bills with stock-in and supplier payables |
| **Credit / Debit notes** | Sale returns and purchase returns with stock & ledger reversal |
| **Parties** | Customers & suppliers, GSTIN, opening balances, full ledger/statement, "to collect / to pay" tracking |
| **Inventory** | Products & services, units, HSN/SAC, sale & purchase prices, GST rates, opening stock, stock adjustments, low-stock alerts, stock movement history |
| **Payments** | Payment In / Payment Out with live party balance |
| **Expenses** | Categorised expense tracking (rent, salary, transport…) |
| **Reports (12)** | Sale, Purchase, Day Book, Cash Flow, Profit & Loss, Party Statement, All Party Balances, Stock Summary, Item Sale Summary, Low Stock, Expense, **GST Summary** (output vs input tax by rate) — all exportable to CSV/Excel |
| **Dashboard** | To-collect / to-pay, stock value, monthly sales & expenses, 30-day sales chart, recent transactions, low-stock alerts |
| **Excel import** | Bulk-import **Items and Parties from Excel (.xlsx) or CSV** — downloadable templates, automatic column matching, preview before import, duplicate skip/update |
| **Backup & restore** | One-click JSON backup, restore on any device |
| **Extras** | Dark theme, mobile-friendly layout, keyboard shortcuts (Alt+N new sale, Alt+P purchase), demo data to explore |

## 📊 Importing your existing data from Excel

Open **Items → ⬆ Import** (or **Parties → ⬆ Import**):

1. Click **Download Template** to get the expected columns (or use your own file — columns are matched by header name, e.g. "Item Name", "Sale Price", "GST %").
2. Fill it in Excel and upload it back — both **.xlsx** and **.csv** work directly.
3. Review the preview, tick *Update existing* if you want matching names overwritten, then **Import**.

Rows without a name are skipped; re-importing the same file won't create duplicates.

## 🔒 Where is my data?

Everything is stored in your browser's `localStorage` on your own device. Nothing is uploaded anywhere.

- **Take backups regularly** (Settings → *Download Backup*, or the ⬇ Backup button). Clearing browser data erases the app's data.
- To move to another computer: download a backup, open the app there, Settings → *Restore from Backup*.

## 🛠 Tech

Plain HTML + CSS + vanilla JavaScript — zero dependencies, zero build step. `dist/VyaparOpen.html` is the same app with all CSS/JS inlined into one file (generated from the sources in `js/` and `css/`).

To rebuild the single file after editing sources:

```bash
node build.js
```

## ⚠️ Disclaimer

VyaparOpen is an independent open-source project and is **not affiliated with or endorsed by Vyapar / Simply Vyapar Apps Pvt Ltd**. GST figures are working summaries — verify with your accountant before filing.

## 📄 License

MIT — free for personal and commercial use.

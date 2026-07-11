# Shop Billing App

Open-source daily billing app (like Vyapar) for shops selling
**sanitary, paints, plumbing, electrical and hardware** items.

Built with **Python (Flask) + SQLite + HTML/CSS/JS** — no paid software, no
internet needed, all data stays on your computer in one file (`shop.db`).

## Features

- **User login** — multiple users; Admin (everything) and Staff roles.
  Default login: `admin` / `admin123` — change it from the Users page.
- **Dashboard** — today / week / month / year sales tiles, last-7-days sales
  chart, low-stock alerts, top products, recent bills (Vyapar-style).
- **Billing** — customer name, mobile, address (optional); per item:
  category → product → description → unit → quantity → price →
  **discount → GST** → total. Auto bill numbers (`INV-YYYYMMDD-001`),
  extra whole-bill discount, payment mode (Cash / UPI / Card / Credit).
- **Invoice printing** — GST tax invoice; Print or Save as PDF from the
  browser's print dialog.
- **Customers** — add / edit / search customers; auto-created from bills;
  shows each customer's bill count and total business.
- **Products** — selling price, purchase price (for profit), GST rate,
  unit, opening stock, low-stock alert level. Edit inline.
- **Inventory** — stock in / stock out with notes, automatic stock-out on
  every sale, movement history, **low stock alerts**.
- **Reports** — **daily, weekly, monthly, quarterly, yearly** sales;
  **category-wise, product-wise, customer-wise**; **profit report**
  (revenue − cost with margin %). Any report exports to **Excel (.xlsx)**,
  CSV, or PDF (via Print).
- **Backup & Restore** — one-click backup file download; restore by upload
  (a safety copy of current data is kept automatically).

## How to run (desktop)

1. Install Python 3 from https://python.org (tick "Add to PATH" on Windows).
2. In this folder run:

   ```
   pip install -r requirements.txt
   python app.py
   ```

3. Open **http://localhost:5000** and log in with `admin` / `admin123`.

## How to use on a tablet

Run the app on the shop computer, then on the tablet's browser open
`http://<computer-ip>:5000` (e.g. `http://192.168.1.5:5000`) — both devices
must be on the same Wi-Fi. Find the computer's IP with `ipconfig` (Windows)
or `ip addr` (Linux).

## Customising

- Shop name / address / GSTIN on the invoice: edit `templates/bill_view.html`.
- Categories and GST rates: edit `CATEGORIES` / `GST_RATES` at the top of `app.py`.
- Set a secret key in production: `SHOP_SECRET=<random text> python app.py`.
- Backup: use the Backup page, or just copy the `shop.db` file.

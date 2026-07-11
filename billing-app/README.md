# Shop Billing App

Simple, open-source daily billing app (like Vyapar) for shops selling
**sanitary, paints, plumbing, electrical and hardware** items.

Built with **Python (Flask) + SQLite + HTML/CSS/JS** — no paid software, no
internet needed, all data stays on your computer in one file (`shop.db`).

## Features

- **New Bill** — customer name, contact number, then per line item:
  category → product (auto-filled description, unit, price) → quantity.
  Discount, payment mode (Cash / UPI / Card / Credit), auto bill numbers
  (`INV-YYYYMMDD-001`), save & print invoice.
- **Bills** — search past bills by customer name, phone or bill number;
  filter by date; reprint any invoice.
- **Products** — add / remove products with category, description, unit, price.
  Comes pre-loaded with sample items in every category.
- **Reports** — **daily, monthly, quarterly and yearly** sales reports with
  date-range filter, sales-by-category, top-10 products, today / this-month /
  this-year summary cards, and CSV export (opens in Excel).

## How to run (desktop)

1. Install Python 3 from https://python.org (tick "Add to PATH" on Windows).
2. In this folder run:

   ```
   pip install -r requirements.txt
   python app.py
   ```

3. Open **http://localhost:5000** in any browser (Chrome, Edge, Firefox).

## How to use on a tablet

Run the app on the shop computer, then on the tablet's browser open
`http://<computer-ip>:5000` (e.g. `http://192.168.1.5:5000`) — both devices
must be on the same Wi-Fi. Find the computer's IP with `ipconfig` (Windows)
or `ip addr` (Linux).

## Customising

- Shop name / address on the invoice: edit `templates/bill_view.html`.
- Categories: edit the `CATEGORIES` list at the top of `app.py`.
- Backup: just copy the `shop.db` file.

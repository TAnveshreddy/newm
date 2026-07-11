"""Shop Billing App — daily billing for sanitary, paints, plumbing, electrical shops.

Run:  python app.py   then open http://localhost:5000
Works on desktop and tablet (open the same URL from the tablet browser on the
same Wi-Fi, using this computer's IP address, e.g. http://192.168.1.5:5000).
"""

import csv
import io
import os
import sqlite3
from datetime import date, datetime

from flask import (Flask, Response, g, jsonify, redirect, render_template,
                   request, url_for)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "shop.db")

app = Flask(__name__)

CATEGORIES = ["Sanitary", "Paints", "Plumbing", "Electrical", "Hardware", "Other"]

SEED_PRODUCTS = [
    # (category, name, description, unit, price)
    ("Sanitary", "Wash Basin", "Ceramic wash basin, white", "pcs", 1450),
    ("Sanitary", "Western Toilet Seat", "Floor-mounted EWC with flush tank", "pcs", 5200),
    ("Sanitary", "Health Faucet", "ABS body health faucet with hose", "pcs", 350),
    ("Sanitary", "Bathroom Mirror", "18x24 inch frameless mirror", "pcs", 650),
    ("Paints", "Emulsion Paint 20L", "Interior emulsion, white base", "bucket", 3800),
    ("Paints", "Enamel Paint 1L", "Oil-based enamel, gloss finish", "tin", 320),
    ("Paints", "Primer 10L", "Wall primer, water-based", "bucket", 1600),
    ("Paints", "Paint Brush 4 inch", "Bristle brush for oil/water paints", "pcs", 90),
    ("Plumbing", "PVC Pipe 1 inch", "3-metre length, ISI mark", "pcs", 210),
    ("Plumbing", "CPVC Pipe 3/4 inch", "3-metre length, hot/cold water", "pcs", 260),
    ("Plumbing", "Ball Valve 1/2 inch", "Brass ball valve", "pcs", 180),
    ("Plumbing", "Teflon Tape", "Thread seal tape roll", "pcs", 15),
    ("Electrical", "Wire 1.5 sqmm 90m", "FR copper wire coil", "coil", 1750),
    ("Electrical", "Switch 6A", "Modular switch, white", "pcs", 45),
    ("Electrical", "LED Bulb 9W", "B22 cool white LED bulb", "pcs", 110),
    ("Electrical", "MCB 16A", "Single-pole miniature circuit breaker", "pcs", 240),
    ("Hardware", "Door Hinge 4 inch", "Stainless steel butt hinge", "pcs", 60),
    ("Hardware", "Screws Box 1 inch", "100-piece box, zinc plated", "box", 120),
]


# ---------------------------------------------------------------- database

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL,
            name        TEXT NOT NULL,
            description TEXT DEFAULT '',
            unit        TEXT DEFAULT 'pcs',
            price       REAL NOT NULL DEFAULT 0,
            active      INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS bills (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_no       TEXT NOT NULL UNIQUE,
            customer_name TEXT NOT NULL,
            phone         TEXT DEFAULT '',
            bill_date     TEXT NOT NULL,           -- YYYY-MM-DD
            created_at    TEXT NOT NULL,
            subtotal      REAL NOT NULL DEFAULT 0,
            discount      REAL NOT NULL DEFAULT 0,
            total         REAL NOT NULL DEFAULT 0,
            payment_mode  TEXT NOT NULL DEFAULT 'Cash'
        );
        CREATE TABLE IF NOT EXISTS bill_items (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id      INTEGER NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
            category     TEXT NOT NULL,
            product_name TEXT NOT NULL,
            description  TEXT DEFAULT '',
            unit         TEXT DEFAULT 'pcs',
            qty          REAL NOT NULL,
            price        REAL NOT NULL,
            amount       REAL NOT NULL
        );
        """
    )
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO products (category, name, description, unit, price) "
            "VALUES (?, ?, ?, ?, ?)",
            SEED_PRODUCTS,
        )
    db.commit()
    db.close()


def next_bill_no(db):
    today = date.today().strftime("%Y%m%d")
    prefix = f"INV-{today}-"
    row = db.execute(
        "SELECT bill_no FROM bills WHERE bill_no LIKE ? ORDER BY id DESC LIMIT 1",
        (prefix + "%",),
    ).fetchone()
    seq = int(row["bill_no"].rsplit("-", 1)[1]) + 1 if row else 1
    return f"{prefix}{seq:03d}"


# ---------------------------------------------------------------- billing

@app.route("/")
def new_bill():
    db = get_db()
    products = db.execute(
        "SELECT * FROM products WHERE active = 1 ORDER BY category, name"
    ).fetchall()
    customers = db.execute(
        "SELECT customer_name, phone, MAX(id) FROM bills "
        "GROUP BY customer_name, phone ORDER BY MAX(id) DESC LIMIT 50"
    ).fetchall()
    return render_template(
        "billing.html",
        categories=CATEGORIES,
        products=[dict(p) for p in products],
        customers=customers,
        today=date.today().isoformat(),
    )


@app.route("/api/bills", methods=["POST"])
def save_bill():
    data = request.get_json(force=True)
    name = (data.get("customer_name") or "").strip()
    items = data.get("items") or []
    if not name:
        return jsonify(error="Customer name is required"), 400
    if not items:
        return jsonify(error="Add at least one item"), 400

    clean_items, subtotal = [], 0.0
    for it in items:
        try:
            qty = float(it.get("qty") or 0)
            price = float(it.get("price") or 0)
        except (TypeError, ValueError):
            return jsonify(error="Quantity and price must be numbers"), 400
        pname = (it.get("product_name") or "").strip()
        if not pname or qty <= 0:
            return jsonify(error="Each item needs a product and a quantity above 0"), 400
        amount = round(qty * price, 2)
        subtotal += amount
        clean_items.append((
            it.get("category") or "Other", pname,
            (it.get("description") or "").strip(),
            it.get("unit") or "pcs", qty, price, amount,
        ))

    try:
        discount = max(0.0, float(data.get("discount") or 0))
    except (TypeError, ValueError):
        discount = 0.0
    total = round(subtotal - discount, 2)

    db = get_db()
    bill_no = next_bill_no(db)
    cur = db.execute(
        "INSERT INTO bills (bill_no, customer_name, phone, bill_date, created_at,"
        " subtotal, discount, total, payment_mode) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            bill_no, name, (data.get("phone") or "").strip(),
            data.get("bill_date") or date.today().isoformat(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(subtotal, 2), round(discount, 2), total,
            data.get("payment_mode") or "Cash",
        ),
    )
    bill_id = cur.lastrowid
    db.executemany(
        "INSERT INTO bill_items (bill_id, category, product_name, description,"
        " unit, qty, price, amount) VALUES (?,?,?,?,?,?,?,?)",
        [(bill_id,) + item for item in clean_items],
    )
    db.commit()
    return jsonify(ok=True, bill_id=bill_id, bill_no=bill_no)


@app.route("/bills")
def bills():
    db = get_db()
    q = (request.args.get("q") or "").strip()
    day = request.args.get("date") or ""
    sql = "SELECT * FROM bills WHERE 1=1"
    args = []
    if q:
        sql += " AND (customer_name LIKE ? OR phone LIKE ? OR bill_no LIKE ?)"
        args += [f"%{q}%"] * 3
    if day:
        sql += " AND bill_date = ?"
        args.append(day)
    rows = db.execute(sql + " ORDER BY id DESC LIMIT 300", args).fetchall()
    total = sum(r["total"] for r in rows)
    return render_template("bills.html", bills=rows, q=q, day=day, total=total)


@app.route("/bills/<int:bill_id>")
def bill_view(bill_id):
    db = get_db()
    bill = db.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
    if not bill:
        return "Bill not found", 404
    items = db.execute(
        "SELECT * FROM bill_items WHERE bill_id = ? ORDER BY id", (bill_id,)
    ).fetchall()
    return render_template("bill_view.html", bill=bill, items=items)


# ---------------------------------------------------------------- products

@app.route("/products")
def products():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM products WHERE active = 1 ORDER BY category, name"
    ).fetchall()
    return render_template("products.html", products=rows, categories=CATEGORIES)


@app.route("/products/add", methods=["POST"])
def add_product():
    f = request.form
    name = (f.get("name") or "").strip()
    if name:
        try:
            price = float(f.get("price") or 0)
        except ValueError:
            price = 0.0
        get_db().execute(
            "INSERT INTO products (category, name, description, unit, price)"
            " VALUES (?,?,?,?,?)",
            (f.get("category") or "Other", name,
             (f.get("description") or "").strip(),
             (f.get("unit") or "pcs").strip(), price),
        )
        get_db().commit()
    return redirect(url_for("products"))


@app.route("/products/<int:pid>/delete", methods=["POST"])
def delete_product(pid):
    db = get_db()
    db.execute("UPDATE products SET active = 0 WHERE id = ?", (pid,))
    db.commit()
    return redirect(url_for("products"))


# ---------------------------------------------------------------- reports

PERIOD_SQL = {
    "daily": "bill_date",
    "monthly": "strftime('%Y-%m', bill_date)",
    "quarterly": "strftime('%Y', bill_date) || '-Q' || ((strftime('%m', bill_date) + 2) / 3)",
    "yearly": "strftime('%Y', bill_date)",
}


def report_rows(db, period, start, end):
    bucket = PERIOD_SQL[period]
    return db.execute(
        f"SELECT {bucket} AS period, COUNT(*) AS bills,"
        f" SUM(total) AS sales, SUM(discount) AS discount"
        f" FROM bills WHERE bill_date BETWEEN ? AND ?"
        f" GROUP BY period ORDER BY period DESC",
        (start, end),
    ).fetchall()


def default_range(period):
    today = date.today()
    if period == "daily":
        start = today.replace(day=1)
    elif period == "monthly":
        start = today.replace(month=1, day=1)
    else:  # quarterly / yearly
        start = today.replace(year=today.year - 4, month=1, day=1)
    return start.isoformat(), today.isoformat()


@app.route("/reports")
def reports():
    db = get_db()
    period = request.args.get("period", "daily")
    if period not in PERIOD_SQL:
        period = "daily"
    d_start, d_end = default_range(period)
    start = request.args.get("start") or d_start
    end = request.args.get("end") or d_end

    rows = report_rows(db, period, start, end)
    by_category = db.execute(
        "SELECT i.category, SUM(i.amount) AS sales, SUM(i.qty) AS qty"
        " FROM bill_items i JOIN bills b ON b.id = i.bill_id"
        " WHERE b.bill_date BETWEEN ? AND ?"
        " GROUP BY i.category ORDER BY sales DESC",
        (start, end),
    ).fetchall()
    top_products = db.execute(
        "SELECT i.product_name, i.category, SUM(i.qty) AS qty, SUM(i.amount) AS sales"
        " FROM bill_items i JOIN bills b ON b.id = i.bill_id"
        " WHERE b.bill_date BETWEEN ? AND ?"
        " GROUP BY i.product_name, i.category ORDER BY sales DESC LIMIT 10",
        (start, end),
    ).fetchall()

    today = date.today()
    summary = {}
    for label, s in (
        ("Today", today.isoformat()),
        ("This Month", today.replace(day=1).isoformat()),
        ("This Year", today.replace(month=1, day=1).isoformat()),
    ):
        r = db.execute(
            "SELECT COUNT(*) AS bills, COALESCE(SUM(total), 0) AS sales"
            " FROM bills WHERE bill_date BETWEEN ? AND ?",
            (s, today.isoformat()),
        ).fetchone()
        summary[label] = r

    return render_template(
        "reports.html", period=period, start=start, end=end, rows=rows,
        by_category=by_category, top_products=top_products, summary=summary,
        grand_sales=sum(r["sales"] or 0 for r in rows),
        grand_bills=sum(r["bills"] for r in rows),
    )


@app.route("/reports/export.csv")
def export_csv():
    db = get_db()
    period = request.args.get("period", "daily")
    if period not in PERIOD_SQL:
        period = "daily"
    d_start, d_end = default_range(period)
    start = request.args.get("start") or d_start
    end = request.args.get("end") or d_end
    rows = report_rows(db, period, start, end)

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Period", "Bills", "Discount", "Sales"])
    for r in rows:
        w.writerow([r["period"], r["bills"], r["discount"] or 0, r["sales"] or 0])
    return Response(
        buf.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition":
                 f"attachment; filename={period}_report_{start}_to_{end}.csv"},
    )


if __name__ == "__main__":
    init_db()
    # host 0.0.0.0 lets tablets/phones on the same Wi-Fi open the app
    app.run(host="0.0.0.0", port=5000, debug=False)

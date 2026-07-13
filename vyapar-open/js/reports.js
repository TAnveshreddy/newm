/* VyaparOpen — reports.js */
'use strict';

const REPORTS = [
  ['daily', 'Daily Sales'],
  ['weekly', 'Weekly Sales'],
  ['monthly', 'Monthly Sales'],
  ['quarterly', 'Quarterly Sales'],
  ['yearly', 'Yearly Sales'],
  ['productwise', 'Product-wise Sales'],
  ['categorywise', 'Category-wise Sales'],
  ['customerwise', 'Customer-wise Sales'],
  ['profit', 'Profit Report'],
  ['stock', 'Stock Availability'],
  ['sale', 'Bill Register'],
  ['purchase', 'Purchase Report'],
  ['daybook', 'Day Book'],
  ['cashflow', 'Cash Flow'],
  ['party', 'Party Statement'],
  ['allparties', 'Party Balances'],
  ['expense', 'Expense Report'],
  ['gst', 'GST Summary']
];

let repState = { key: 'daily', from: addDays(todayStr(), -29), to: todayStr(), partyId: '' };

/* switching report picks a sensible default range for its granularity */
function repSetKey(key) {
  repState.key = key;
  const d = new Date();
  const fyStart = (d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1) + '-04-01';
  if (key === 'daily') { repState.from = addDays(todayStr(), -29); repState.to = todayStr(); }
  else if (key === 'weekly') { repState.from = addDays(todayStr(), -83); repState.to = todayStr(); }
  else if (key === 'monthly' || key === 'quarterly' || key === 'profit') { repState.from = fyStart; repState.to = todayStr(); }
  else if (key === 'yearly') { repState.from = addDays(fyStart, -730); repState.to = todayStr(); }
  renderReports();
}

function renderReports() {
  const tabs = REPORTS.map(r =>
    '<button class="rtab' + (repState.key === r[0] ? ' active' : '') + '" onclick="repSetKey(\'' + r[0] + '\')">' + r[1] + '</button>'
  ).join('');
  const needsRange = !['stock', 'lowstock', 'allparties'].includes(repState.key);
  const needsParty = repState.key === 'party';

  el('view').innerHTML =
    '<div class="page-head"><h2>Reports</h2></div>' +
    '<div class="rtabs">' + tabs + '</div>' +
    '<div class="card"><div class="rfilters">' +
    (needsRange ?
      '<label>From <input type="date" value="' + repState.from + '" onchange="repState.from=this.value;renderReports()"></label>' +
      '<label>To <input type="date" value="' + repState.to + '" onchange="repState.to=this.value;renderReports()"></label>' +
      '<span class="presets">' +
      '<button class="btn tiny ghost" onclick="setRange(0)">Today</button>' +
      '<button class="btn tiny ghost" onclick="setRange(6)">7 days</button>' +
      '<button class="btn tiny ghost" onclick="setRange(29)">30 days</button>' +
      '<button class="btn tiny ghost" onclick="setRangeMonth()">This month</button>' +
      '<button class="btn tiny ghost" onclick="setRangeFY()">This FY</button></span>' : '') +
    (needsParty ? '<label>Party <select onchange="repState.partyId=this.value;renderReports()">' +
      '<option value="">— select —</option>' +
      state.parties.slice().sort((a, b) => a.name.localeCompare(b.name)).map(p => '<option value="' + p.id + '"' + (repState.partyId === p.id ? ' selected' : '') + '>' + esc(p.name) + '</option>').join('') +
      '</select></label>' : '') +
    '<span style="margin-left:auto;display:flex;gap:8px">' +
    '<button class="btn ghost" onclick="exportDetailedSales()" title="Every bill item in the date range: customer, item, brand, received, due, profit">⬇ Detailed CSV</button>' +
    '<button class="btn ghost" onclick="exportCurrentReport()">⬇ Export CSV</button>' +
    '</span></div><div id="repBody"></div></div>';

  el('repBody').innerHTML = buildReport().html;
}

function setRange(daysBack) { repState.to = todayStr(); repState.from = addDays(todayStr(), -daysBack); renderReports(); }
function setRangeMonth() {
  const d = new Date();
  repState.from = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-01';
  repState.to = todayStr();
  renderReports();
}
function setRangeFY() {
  const d = new Date();
  const fyStartYear = d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1;
  repState.from = fyStartYear + '-04-01';
  repState.to = todayStr();
  renderReports();
}

function txnsIn(types, from, to) {
  return state.txns
    .filter(t => types.includes(t.type) && inRange(t.date, from, to))
    .sort((a, b) => a.date === b.date ? a.createdAt - b.createdAt : (a.date < b.date ? -1 : 1));
}

function tbl(headers, rows, footRow) {
  let html = '<div class="table-wrap"><table><thead><tr>' +
    headers.map(hd => '<th class="' + (hd[1] || '') + '">' + hd[0] + '</th>').join('') + '</tr></thead><tbody>';
  html += rows.length ? rows.map(r => '<tr>' + r.map((c, i) => '<td class="' + (headers[i][1] || '') + '">' + c + '</td>').join('') + '</tr>').join('')
    : '<tr><td colspan="' + headers.length + '" class="empty">No data for this period.</td></tr>';
  html += '</tbody>';
  if (footRow) html += '<tfoot><tr>' + footRow.map((c, i) => '<td class="' + (headers[i] ? headers[i][1] || '' : '') + '"><strong>' + c + '</strong></td>').join('') + '</tr></tfoot>';
  return html + '</table></div>';
}

/* group a date into a period bucket for the sales-by-period reports */
function periodKey(dateStr, granularity) {
  const [y, m, dd] = dateStr.split('-').map(Number);
  if (granularity === 'daily') return { key: dateStr, label: fmtDate(dateStr) };
  if (granularity === 'weekly') {
    const dt = new Date(dateStr + 'T00:00:00');
    const monday = new Date(dt);
    monday.setDate(dt.getDate() - ((dt.getDay() + 6) % 7));
    const iso = monday.getFullYear() + '-' + String(monday.getMonth() + 1).padStart(2, '0') + '-' + String(monday.getDate()).padStart(2, '0');
    return { key: iso, label: 'Week of ' + fmtDate(iso) };
  }
  if (granularity === 'monthly') return { key: y + '-' + String(m).padStart(2, '0'), label: monthName(m - 1) + ' ' + y };
  const fy = m >= 4 ? y : y - 1;
  if (granularity === 'quarterly') {
    const q = Math.floor(((m - 4 + 12) % 12) / 3) + 1;
    return { key: fy + '-Q' + q, label: 'Q' + q + ' FY ' + fy + '-' + String((fy + 1) % 100).padStart(2, '0') };
  }
  return { key: String(fy), label: 'FY ' + fy + '-' + String((fy + 1) % 100).padStart(2, '0') }; // yearly
}

function buildReport() {
  const k = repState.key, from = repState.from, to = repState.to;
  let html = '', csv = { name: k + '-report.csv', headers: [], rows: [] };

  if (['daily', 'weekly', 'monthly', 'quarterly', 'yearly'].includes(k)) {
    const buckets = {};
    for (const t of txnsIn(['SALE'], from, to)) {
      const p = periodKey(t.date, k);
      if (!buckets[p.key]) buckets[p.key] = { label: p.label, bills: 0, sales: 0, received: 0, profit: 0 };
      const b = buckets[p.key];
      b.bills++; b.sales += num(t.total); b.received += num(t.paid); b.profit += txnProfit(t);
    }
    for (const t of txnsIn(['SALE_RETURN'], from, to)) {
      const p = periodKey(t.date, k);
      if (!buckets[p.key]) buckets[p.key] = { label: p.label, bills: 0, sales: 0, received: 0, profit: 0 };
      buckets[p.key].sales -= num(t.total);
      buckets[p.key].profit += txnProfit(t);
    }
    const keys = Object.keys(buckets).sort();
    let tb = 0, ts = 0, tr = 0, tp = 0;
    const rows = keys.map(key => {
      const b = buckets[key];
      tb += b.bills; ts += b.sales; tr += b.received; tp += b.profit;
      return [esc(b.label), String(b.bills), fmtMoney(b.sales), fmtMoney(b.received),
        '<span class="' + (b.profit >= 0 ? 'pos' : 'neg') + '">' + fmtMoney(b.profit) + '</span>'];
    });
    html = tbl([['Period'], ['Bills', 'r'], ['Sales', 'r'], ['Received', 'r'], ['Profit', 'r']], rows,
      ['Total', String(tb), fmtMoney(ts), fmtMoney(tr), fmtMoney(tp)]);
    csv.headers = ['Period', 'Bills', 'Sales', 'Received', 'Profit'];
    csv.rows = keys.map(key => { const b = buckets[key]; return [b.label, b.bills, round2(b.sales), round2(b.received), round2(b.profit)]; });
  }

  else if (k === 'sale' || k === 'purchase') {
    const type = k === 'sale' ? 'SALE' : 'PURCHASE';
    const list = txnsIn([type], from, to);
    let tot = 0, paid = 0;
    const rows = list.map(t => {
      tot += num(t.total); paid += num(t.paid);
      return [fmtDate(t.date), esc(t.number), esc(partyName(t.partyId)), fmtMoney(t.total), fmtMoney(t.paid), fmtMoney(Math.max(0, num(t.total) - num(t.paid))), txnStatus(t)];
    });
    html = tbl([['Date'], ['Number'], ['Party'], ['Total', 'r'], ['Paid', 'r'], ['Balance', 'r'], ['Status']], rows,
      ['', '', 'Total', fmtMoney(tot), fmtMoney(paid), fmtMoney(tot - paid), '']);
    csv.headers = ['Date', 'Number', 'Party', 'Total', 'Paid', 'Balance', 'Status'];
    csv.rows = list.map(t => [t.date, t.number, partyName(t.partyId), num(t.total), num(t.paid), num(t.total) - num(t.paid), txnStatus(t)]);
  }

  else if (k === 'daybook') {
    const list = txnsIn(Object.keys(TXN_TYPES).filter(t => t !== 'ESTIMATE'), from, to);
    let mIn = 0, mOut = 0;
    const rows = list.map(t => {
      const io = moneyInOut(t);
      mIn += io.in; mOut += io.out;
      return [fmtDate(t.date), TXN_TYPES[t.type].label, esc(t.number), esc(t.type === 'EXPENSE' ? (t.category || '') : partyName(t.partyId)), fmtMoney(t.total),
        io.in ? fmtMoney(io.in) : '—', io.out ? fmtMoney(io.out) : '—'];
    });
    html = tbl([['Date'], ['Type'], ['Number'], ['Party'], ['Total', 'r'], ['Money In', 'r'], ['Money Out', 'r']], rows,
      ['', '', '', 'Total', '', fmtMoney(mIn), fmtMoney(mOut)]);
    csv.headers = ['Date', 'Type', 'Number', 'Party', 'Total', 'MoneyIn', 'MoneyOut'];
    csv.rows = list.map(t => { const io = moneyInOut(t); return [t.date, TXN_TYPES[t.type].label, t.number, partyName(t.partyId), num(t.total), io.in, io.out]; });
  }

  else if (k === 'cashflow') {
    const list = txnsIn(Object.keys(TXN_TYPES).filter(t => t !== 'ESTIMATE'), from, to);
    let mIn = 0, mOut = 0;
    for (const t of list) { const io = moneyInOut(t); mIn += io.in; mOut += io.out; }
    html = '<div class="cards">' +
      '<div class="card stat"><div class="stat-label">Money In</div><div class="stat-value pos">' + fmtMoney(mIn) + '</div></div>' +
      '<div class="card stat"><div class="stat-label">Money Out</div><div class="stat-value neg">' + fmtMoney(mOut) + '</div></div>' +
      '<div class="card stat"><div class="stat-label">Net Cash Flow</div><div class="stat-value ' + (mIn - mOut >= 0 ? 'pos' : 'neg') + '">' + fmtMoney(mIn - mOut) + '</div></div></div>' +
      '<p class="sub">Money In counts amounts actually received (sales receipts + payments in). Money Out counts amounts actually paid (purchases, payments out, expenses, refunds).</p>';
    csv.headers = ['Metric', 'Amount'];
    csv.rows = [['Money In', mIn], ['Money Out', mOut], ['Net', mIn - mOut]];
  }

  else if (k === 'profit') {
    const sum = (types, field) => txnsIn(types, from, to).reduce((s, t) => s + num(t[field || 'total']), 0);
    const sales = sum(['SALE']), saleRet = sum(['SALE_RETURN']);
    const purch = sum(['PURCHASE']), purchRet = sum(['PURCHASE_RETURN']);
    const expenses = sum(['EXPENSE']);
    const taxOut = txnsIn(['SALE'], from, to).reduce((s, t) => s + num(t.taxAmount), 0) - txnsIn(['SALE_RETURN'], from, to).reduce((s, t) => s + num(t.taxAmount), 0);
    const taxIn = txnsIn(['PURCHASE'], from, to).reduce((s, t) => s + num(t.taxAmount), 0) - txnsIn(['PURCHASE_RETURN'], from, to).reduce((s, t) => s + num(t.taxAmount), 0);
    const netSales = sales - saleRet - taxOut;
    const netPurch = purch - purchRet - taxIn;
    const gross = netSales - netPurch;
    const net = gross - expenses;
    const costProfit = txnsIn(['SALE', 'SALE_RETURN'], from, to).reduce((s, t) => s + txnProfit(t), 0);
    const row = (l, v, strong, cls) => '<div class="totals-row' + (strong ? ' grand' : '') + '"><span>' + l + '</span><span class="' + (cls || '') + '">' + fmtMoney(v) + '</span></div>';
    html = '<div class="totals-panel pnl">' +
      row('Gross Margin on items sold (sale price − item cost)', costProfit, false, costProfit >= 0 ? 'pos' : 'neg') +
      row('Margin after expenses', costProfit - expenses, true, costProfit - expenses >= 0 ? 'pos' : 'neg') +
      '<div class="totals-row"><span style="font-weight:700;margin-top:8px">Purchase-based P&amp;L</span><span></span></div>' +
      row('Sales (excl. GST)', sales - taxOut) +
      row('Less: Sale Returns', -(saleRet ? saleRet - (saleRet ? txnsIn(['SALE_RETURN'], from, to).reduce((s, t) => s + num(t.taxAmount), 0) : 0) : 0)) +
      row('Net Sales', netSales, true) +
      row('Purchases (excl. GST)', netPurch) +
      row('Gross Profit', gross, true, gross >= 0 ? 'pos' : 'neg') +
      row('Less: Expenses', -expenses) +
      row('Net Profit', net, true, net >= 0 ? 'pos' : 'neg') +
      '</div><p class="sub">Simplified P&amp;L: purchases in the period are treated as cost of goods (no opening/closing stock valuation).</p>';
    csv.headers = ['Line', 'Amount'];
    csv.rows = [['Net Sales', netSales], ['Purchases', netPurch], ['Gross Profit', gross], ['Expenses', expenses], ['Net Profit', net]];
  }

  else if (k === 'party') {
    if (!repState.partyId) { html = '<p class="empty">Select a party above to view their statement.</p>'; }
    else {
      const p = getParty(repState.partyId);
      const list = txnsIn(Object.keys(TXN_TYPES), null, null).filter(t => t.partyId === p.id);
      let bal = partyOpening(p);
      const pre = list.filter(t => from && t.date < from);
      for (const t of pre) bal += txnDue(t);
      const rows = [['', 'Opening Balance (' + fmtDate(from) + ')', '', '', fmtMoney(Math.abs(bal)) + (bal >= 0 ? ' Dr' : ' Cr')]];
      const inList = list.filter(t => inRange(t.date, from, to));
      for (const t of inList) {
        bal += txnDue(t);
        rows.push([fmtDate(t.date), TXN_TYPES[t.type].label, esc(t.number), fmtMoney(t.total), fmtMoney(Math.abs(bal)) + (bal >= 0 ? ' Dr' : ' Cr')]);
      }
      html = '<h3 class="card-title">' + esc(p.name) + ' — closing balance ' + fmtMoney(Math.abs(bal)) + (bal >= 0 ? ' (to receive)' : ' (to pay)') + '</h3>' +
        tbl([['Date'], ['Type'], ['Number'], ['Amount', 'r'], ['Balance', 'r']], rows);
      csv.headers = ['Date', 'Type', 'Number', 'Amount', 'Balance'];
      csv.rows = rows.map(r => r.map(c => String(c).replace(/<[^>]+>/g, '')));
    }
  }

  else if (k === 'allparties') {
    let recv = 0, pay = 0;
    const rows = state.parties.slice().sort((a, b) => a.name.localeCompare(b.name)).map(p => {
      const b = partyBalance(p.id);
      if (b > 0) recv += b; else pay -= b;
      return [esc(p.name), esc(p.phone || ''), esc(p.type), fmtMoney(Math.abs(b)), b > 0 ? 'To Receive' : b < 0 ? 'To Pay' : '—'];
    });
    html = tbl([['Party'], ['Phone'], ['Type'], ['Balance', 'r'], ['Direction']], rows,
      ['Total', '', '', fmtMoney(recv) + ' Dr / ' + fmtMoney(pay) + ' Cr', '']);
    csv.headers = ['Party', 'Phone', 'Type', 'Balance', 'Direction'];
    csv.rows = state.parties.map(p => { const b = partyBalance(p.id); return [p.name, p.phone, p.type, Math.abs(b), b >= 0 ? 'Receive' : 'Pay']; });
  }

  else if (k === 'stock') {
    // one combined stock-availability report: No Stock first, then Low, then In Stock
    const severity = (it, stock) => stock <= 0 ? 0 : isLowStock(it) ? 1 : 2;
    const items = state.items.filter(i => i.type !== 'service')
      .map(it => ({ it: it, stock: itemStock(it.id) }))
      .sort((a, b) => severity(a.it, a.stock) - severity(b.it, b.stock) || a.it.name.localeCompare(b.it.name));
    let totVal = 0;
    const rows = items.map(({ it, stock }) => {
      const val = Math.max(0, stock) * num(it.purchasePrice || it.salePrice);
      totVal += val;
      const avail = stock <= 0 ? '<span class="badge bad">No Stock</span>'
        : isLowStock(it) ? '<span class="badge warn">▲ ' + fmtQty(stock) + ' ' + esc(it.unit) + '</span>'
          : fmtQty(stock) + ' ' + esc(it.unit);
      return [esc(it.name), esc(it.category || ''), esc(it.brand || ''), avail, fmtMoney(val)];
    });
    html = tbl([['Product'], ['Category'], ['Brand'], ['Available Stock', 'r'], ['Stock Value', 'r']], rows,
      ['Total', '', '', '', fmtMoney(totVal)]);
    csv.headers = ['Product', 'Category', 'Brand', 'AvailableStock', 'Status', 'StockValue'];
    csv.rows = items.map(({ it, stock }) => [it.name, it.category, it.brand || '',
      Math.max(0, stock), stock <= 0 ? 'No Stock' : isLowStock(it) ? 'Low Stock' : 'In Stock',
      round2(Math.max(0, stock) * num(it.purchasePrice || it.salePrice))]);
  }

  else if (k === 'productwise' || k === 'categorywise') {
    const map = {};
    for (const t of txnsIn(['SALE'], from, to)) {
      for (const l of (t.lines || [])) {
        let key, name;
        if (k === 'productwise') { key = l.itemId || l.name; name = l.name; }
        else {
          const it = getItem(l.itemId);
          name = (it && it.category) ? it.category : 'Uncategorised';
          key = name;
        }
        if (!map[key]) map[key] = { name: name, qty: 0, amount: 0, profit: 0 };
        map[key].qty += num(l.qty);
        map[key].amount += num(l.amount) + num(l.tax);
        map[key].profit += num(l.amount) - lineCost(l) * num(l.qty);
      }
    }
    const arr = Object.values(map).sort((a, b) => b.amount - a.amount);
    let tq = 0, ta = 0, tp = 0;
    const rows = arr.map(x => {
      tq += x.qty; ta += x.amount; tp += x.profit;
      return [esc(x.name), fmtQty(x.qty), fmtMoney(x.amount),
        '<span class="' + (x.profit >= 0 ? 'pos' : 'neg') + '">' + fmtMoney(x.profit) + '</span>'];
    });
    const first = k === 'productwise' ? 'Product' : 'Category';
    html = tbl([[first], ['Qty Sold', 'r'], ['Sales (incl. GST)', 'r'], ['Profit', 'r']], rows,
      ['Total', fmtQty(tq), fmtMoney(ta), fmtMoney(tp)]);
    csv.headers = [first, 'QtySold', 'Sales', 'Profit'];
    csv.rows = arr.map(x => [x.name, x.qty, round2(x.amount), round2(x.profit)]);
  }

  else if (k === 'customerwise') {
    const map = {};
    for (const t of txnsIn(['SALE'], from, to)) {
      const key = t.partyId || '_cash';
      if (!map[key]) map[key] = { name: partyName(t.partyId), bills: 0, sales: 0, received: 0, profit: 0 };
      const c = map[key];
      c.bills++; c.sales += num(t.total); c.received += num(t.paid); c.profit += txnProfit(t);
    }
    const arr = Object.entries(map).sort((a, b) => b[1].sales - a[1].sales);
    let tb2 = 0, ts = 0, tr = 0, tp = 0;
    const rows = arr.map(([key, c]) => {
      tb2 += c.bills; ts += c.sales; tr += c.received; tp += c.profit;
      const due = key !== '_cash' ? partyBalance(key) : 0;
      return [esc(c.name), String(c.bills), fmtMoney(c.sales), fmtMoney(c.received),
        '<span class="' + (c.profit >= 0 ? 'pos' : 'neg') + '">' + fmtMoney(c.profit) + '</span>',
        key !== '_cash' ? fmtMoney(Math.max(0, due)) : '—'];
    });
    html = tbl([['Customer'], ['Bills', 'r'], ['Sales', 'r'], ['Received', 'r'], ['Profit', 'r'], ['Outstanding', 'r']], rows,
      ['Total', String(tb2), fmtMoney(ts), fmtMoney(tr), fmtMoney(tp), '']);
    csv.headers = ['Customer', 'Bills', 'Sales', 'Received', 'Profit'];
    csv.rows = arr.map(([, c]) => [c.name, c.bills, round2(c.sales), round2(c.received), round2(c.profit)]);
  }

  else if (k === 'expense') {
    const list = txnsIn(['EXPENSE'], from, to);
    const byCat = {};
    let tot = 0;
    for (const t of list) { byCat[t.category || 'Other'] = (byCat[t.category || 'Other'] || 0) + num(t.total); tot += num(t.total); }
    const rows = list.map(t => [fmtDate(t.date), esc(t.number), esc(t.category || ''), esc(t.notes || ''), fmtMoney(t.total)]);
    html = '<div class="cards">' +
      Object.entries(byCat).sort((a, b) => b[1] - a[1]).slice(0, 4).map(c =>
        '<div class="card stat"><div class="stat-label">' + esc(c[0]) + '</div><div class="stat-mid">' + fmtMoney(c[1]) + '</div></div>').join('') +
      '</div>' + tbl([['Date'], ['Number'], ['Category'], ['Notes'], ['Amount', 'r']], rows, ['', '', '', 'Total', fmtMoney(tot)]);
    csv.headers = ['Date', 'Number', 'Category', 'Notes', 'Amount'];
    csv.rows = list.map(t => [t.date, t.number, t.category, t.notes, num(t.total)]);
  }

  else if (k === 'gst') {
    function taxByRate(types) {
      const m = {};
      for (const t of txnsIn(types, from, to)) {
        for (const l of (t.lines || [])) {
          const r = num(l.taxRate);
          if (!m[r]) m[r] = { taxable: 0, tax: 0 };
          m[r].taxable += num(l.amount);
          m[r].tax += num(l.tax);
        }
      }
      return m;
    }
    const out = taxByRate(['SALE']), outRet = taxByRate(['SALE_RETURN']);
    const inn = taxByRate(['PURCHASE']), innRet = taxByRate(['PURCHASE_RETURN']);
    const rates = [...new Set([].concat(Object.keys(out), Object.keys(inn), Object.keys(outRet), Object.keys(innRet)))].map(Number).sort((a, b) => a - b);
    let outputTax = 0, inputTax = 0;
    const rows = rates.map(r => {
      const o = (out[r] ? out[r].tax : 0) - (outRet[r] ? outRet[r].tax : 0);
      const i = (inn[r] ? inn[r].tax : 0) - (innRet[r] ? innRet[r].tax : 0);
      outputTax += o; inputTax += i;
      return [r + '%',
        fmtMoney((out[r] ? out[r].taxable : 0) - (outRet[r] ? outRet[r].taxable : 0)), fmtMoney(o),
        fmtMoney((inn[r] ? inn[r].taxable : 0) - (innRet[r] ? innRet[r].taxable : 0)), fmtMoney(i)];
    });
    html = '<div class="cards">' +
      '<div class="card stat"><div class="stat-label">Output GST (on sales)</div><div class="stat-mid">' + fmtMoney(outputTax) + '</div></div>' +
      '<div class="card stat"><div class="stat-label">Input GST (on purchases)</div><div class="stat-mid">' + fmtMoney(inputTax) + '</div></div>' +
      '<div class="card stat"><div class="stat-label">Net GST Payable</div><div class="stat-value ' + (outputTax - inputTax > 0 ? 'neg' : 'pos') + '">' + fmtMoney(outputTax - inputTax) + '</div></div></div>' +
      tbl([['GST Rate'], ['Sales Taxable', 'r'], ['Output Tax', 'r'], ['Purchase Taxable', 'r'], ['Input Tax', 'r']], rows,
        ['Total', '', fmtMoney(outputTax), '', fmtMoney(inputTax)]) +
      '<p class="sub">Net of credit/debit notes. Use this as a working summary for GSTR filing — verify with your CA.</p>';
    csv.headers = ['Rate', 'SalesTaxable', 'OutputTax', 'PurchaseTaxable', 'InputTax'];
    csv.rows = rows.map(r => r.map(c => String(c).replace('₹ ', '')));
  }

  window._lastReportCSV = csv;
  return { html: html };
}

function moneyInOut(t) {
  switch (t.type) {
    case 'SALE': return { in: num(t.paid), out: 0 };
    case 'PAYMENT_IN': return { in: num(t.total), out: 0 };
    case 'SALE_RETURN': return { in: 0, out: num(t.paid) };
    case 'PURCHASE': return { in: 0, out: num(t.paid) };
    case 'PURCHASE_RETURN': return { in: num(t.paid), out: 0 };
    case 'PAYMENT_OUT': return { in: 0, out: num(t.total) };
    case 'EXPENSE': return { in: 0, out: num(t.total) };
    default: return { in: 0, out: 0 };
  }
}

function exportCurrentReport() {
  const c = window._lastReportCSV;
  if (!c || !c.headers.length) { toast('Nothing to export', 'error'); return; }
  exportTableCSV(c.name, c.headers, c.rows);
}

/* Bill-item level export for the selected date range.
   Bill-level amounts (Bill Total / Received / Due) are written only on the
   first row of each bill so that summing those columns in Excel stays correct. */
function exportDetailedSales() {
  const from = repState.from, to = repState.to;
  const bills = txnsIn(['SALE'], from, to);
  if (!bills.length) { toast('No bills in the selected date range', 'error'); return; }
  const headers = ['Date', 'Bill No', 'Customer Name', 'Contact Number', 'Referred By',
    'Item', 'Brand', 'Description', 'Qty', 'Unit', 'Rate',
    'Line Sales (incl GST)', 'Line Profit/Loss',
    'Bill Total', 'Received', 'Due', 'Status'];
  const rows = [];
  for (const t of bills) {
    const p = t.partyId ? getParty(t.partyId) : null;
    const discFactor = 1 - num(t.discountPct || 0) / 100;
    const due = round2(Math.max(0, num(t.total) - num(t.paid)));
    (t.lines || []).forEach((l, i) => {
      const lineSales = round2((num(l.amount) + num(l.tax)) * discFactor);
      const lineProfit = round2(num(l.amount) * discFactor - lineCost(l) * num(l.qty));
      rows.push([
        fmtDate(t.date), t.number,
        p ? p.name : 'Cash Sale', p ? (p.phone || '') : '', t.referredBy || '',
        l.name, l.brand || '', l.description || '', num(l.qty), l.unit || '', num(l.rate),
        lineSales, lineProfit,
        i === 0 ? num(t.total) : '', i === 0 ? num(t.paid) : '', i === 0 ? due : '',
        i === 0 ? txnStatus(t) : ''
      ]);
    });
  }
  exportTableCSV('sales-detailed-' + from + '-to-' + to + '.csv', headers, rows);
}

/* VyaparOpen — dashboard.js */
'use strict';

function renderDashboard() {
  const totals = totalsReceivablePayable();
  const from30 = addDays(todayStr(), -29);

  // sales by day (last 30 days) for the chart
  const byDay = {};
  for (let i = 0; i < 30; i++) byDay[addDays(from30, i)] = 0;
  let sales30 = 0;
  for (const t of state.txns) {
    if (t.type === 'SALE' && inRange(t.date, from30, todayStr())) {
      byDay[t.date] = (byDay[t.date] || 0) + num(t.total);
      sales30 += num(t.total);
    }
  }
  const chartData = Object.keys(byDay).sort().map(d => ({ label: d.slice(8) + '/' + d.slice(5, 7), value: byDay[d] }));

  // this month figures
  const d = new Date();
  const mStart = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-01';
  const sum = (type) => state.txns.filter(t => t.type === type && inRange(t.date, mStart, todayStr())).reduce((s, t) => s + num(t.total), 0);
  const mSales = sum('SALE'), mPurch = sum('PURCHASE'), mExp = sum('EXPENSE');

  const low = lowStockItems();
  const recent = state.txns.slice().sort((a, b) => b.createdAt - a.createdAt).slice(0, 8);
  const recentRows = recent.map(t =>
    '<tr class="rowlink" onclick="viewTxn(\'' + t.id + '\')">' +
    '<td>' + fmtDate(t.date) + '</td><td>' + TXN_TYPES[t.type].label + '<div class="sub">' + esc(t.number) + '</div></td>' +
    '<td>' + esc(t.type === 'EXPENSE' ? (t.category || '') : partyName(t.partyId)) + '</td>' +
    '<td class="r">' + fmtMoney(t.total) + '</td>' +
    '<td><span class="badge ' + (txnStatus(t) === 'Paid' || txnStatus(t) === 'Converted' ? 'ok' : txnStatus(t) === 'Partial' ? 'warn' : 'bad') + '">' + txnStatus(t) + '</span></td></tr>'
  ).join('') || '<tr><td colspan="5" class="empty">No transactions yet — create your first sale!</td></tr>';

  const lowRows = low.slice(0, 6).map(it =>
    '<tr class="rowlink" onclick="openItemDetail(\'' + it.id + '\')"><td>' + esc(it.name) + '</td>' +
    '<td class="r neg">' + fmtQty(itemStock(it.id)) + ' ' + esc(it.unit) + '</td>' +
    '<td class="r">' + fmtQty(it.minStock) + '</td></tr>'
  ).join('');

  const empty = state.txns.length === 0 && state.parties.length === 0 && state.items.length === 0;

  el('view').innerHTML =
    '<div class="page-head"><h2>Dashboard</h2><div class="head-actions">' +
    '<button class="btn primary" onclick="openTxnForm(\'SALE\')">+ New Sale</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'PURCHASE\')">+ Purchase</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'PAYMENT_IN\')">+ Payment In</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'EXPENSE\')">+ Expense</button></div></div>' +
    (empty ?
      '<div class="card welcome"><h3>👋 Welcome to VyaparOpen!</h3>' +
      '<p>Your free, open-source business manager — invoicing, inventory, payments &amp; GST reports. All data stays on this device.</p>' +
      '<div class="head-actions" style="margin-top:12px">' +
      '<button class="btn primary" onclick="go(\'settings\')">1. Set up your business profile</button>' +
      '<button class="btn ghost" onclick="openItemForm()">2. Add items</button>' +
      '<button class="btn ghost" onclick="openPartyForm()">3. Add parties</button>' +
      '<button class="btn ghost" onclick="confirmDemo()">Or load demo data</button></div></div>' : '') +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">To Collect</div><div class="stat-value pos">' + fmtMoney(totals.receivable) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">To Pay</div><div class="stat-value neg">' + fmtMoney(totals.payable) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Stock Value</div><div class="stat-value">' + fmtMoney(stockValue()) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Sales This Month</div><div class="stat-value">' + fmtMoney(mSales) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Purchases This Month</div><div class="stat-mid">' + fmtMoney(mPurch) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Expenses This Month</div><div class="stat-mid">' + fmtMoney(mExp) + '</div></div>' +
    '</div>' +
    '<div class="card"><h3 class="card-title">Sales — last 30 days <span class="sub">(total ' + fmtMoney(sales30) + ')</span></h3>' +
    svgBarChart(chartData, { height: 220 }) + '</div>' +
    '<div class="grid-2">' +
    '<div class="card"><h3 class="card-title">Recent Transactions</h3><div class="table-wrap"><table><thead><tr><th>Date</th><th>Type</th><th>Party</th><th class="r">Amount</th><th>Status</th></tr></thead><tbody>' +
    recentRows + '</tbody></table></div></div>' +
    '<div class="card"><h3 class="card-title">Low Stock ' + (low.length ? '<span class="badge bad">' + low.length + '</span>' : '') + '</h3>' +
    (lowRows ? '<div class="table-wrap"><table><thead><tr><th>Item</th><th class="r">Stock</th><th class="r">Min</th></tr></thead><tbody>' + lowRows + '</tbody></table></div>'
      : '<p class="empty">All stocked up 🎉</p>') +
    '</div></div>';
}

function confirmDemo() {
  openModal(
    '<div class="modal-head"><h3>Load demo data?</h3></div>' +
    '<div class="modal-body"><p>This loads a sample business (parties, items and transactions) so you can explore the app. Existing data will be replaced.</p></div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="closeModal();loadDemoData();route();toast(\'Demo data loaded\')">Load Demo</button></div>'
  );
}

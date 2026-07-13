/* VyaparOpen — dashboard.js */
'use strict';

function renderDashboard() {
  const today = todayStr();
  const totals = totalsReceivablePayable();

  // today's figures
  let todaySales = 0, todayProfit = 0, todayBills = 0;
  for (const t of state.txns) {
    if (t.date !== today) continue;
    if (t.type === 'SALE') { todaySales += num(t.total); todayProfit += txnProfit(t); todayBills++; }
    if (t.type === 'SALE_RETURN') { todayProfit += txnProfit(t); }
  }

  // monthly sales (daily bars for the current month)
  const d = new Date();
  const mStart = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-01';
  const daysInMonth = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate();
  const byDay = {};
  for (let i = 0; i < daysInMonth; i++) byDay[addDays(mStart, i)] = 0;
  let monthSales = 0;
  for (const t of state.txns) {
    if (t.type === 'SALE' && inRange(t.date, mStart, null) && byDay[t.date] !== undefined) {
      byDay[t.date] += num(t.total);
      if (t.date <= today) monthSales += num(t.total);
    }
  }
  const chartData = Object.keys(byDay).sort().map(dt => ({ label: dt.slice(8), value: byDay[dt] }));

  const low = lowStockItems();
  const recentBills = state.txns.filter(t => t.type === 'SALE')
    .sort((a, b) => b.createdAt - a.createdAt).slice(0, 8);

  const billRows = recentBills.map(t => {
    const st = txnStatus(t);
    return '<tr class="rowlink" onclick="viewTxn(\'' + t.id + '\')">' +
      '<td>' + fmtDate(t.date) + '</td><td>' + esc(t.number) + '</td>' +
      '<td>' + esc(partyName(t.partyId)) + '</td>' +
      '<td class="r">' + fmtMoney(t.total) + '</td>' +
      '<td><span class="badge ' + (st === 'Paid' ? 'ok' : st === 'Partial' ? 'warn' : 'bad') + '">' + st + '</span></td></tr>';
  }).join('') || '<tr><td colspan="5" class="empty">No bills yet — create your first bill!</td></tr>';

  // stock availability (same as the report: No Stock first, then Low, then In Stock)
  const severity = (it, stock) => stock <= 0 ? 0 : isLowStock(it) ? 1 : 2;
  const availItems = state.items.filter(i => i.type !== 'service')
    .map(it => ({ it: it, stock: itemStock(it.id) }))
    .sort((a, b) => severity(a.it, a.stock) - severity(b.it, b.stock) || a.it.name.localeCompare(b.it.name));
  const availRows = availItems.slice(0, 10).map(({ it, stock }) =>
    '<tr class="rowlink" onclick="openItemDetail(\'' + it.id + '\')">' +
    '<td><strong>' + esc(it.name) + '</strong></td>' +
    '<td>' + esc(it.category || '') + '</td>' +
    '<td>' + esc(it.brand || '') + '</td>' +
    '<td class="r">' + (stock <= 0 ? '<span class="badge bad">No Stock</span>'
      : isLowStock(it) ? '<span class="badge warn">▲ ' + fmtQty(stock) + ' ' + esc(it.unit) + '</span>'
        : fmtQty(stock) + ' ' + esc(it.unit)) + '</td></tr>'
  ).join('');

  const empty = state.txns.length === 0 && state.parties.length === 0 && state.items.length === 0;

  el('view').innerHTML =
    '<div class="page-head"><h2>Dashboard</h2><div class="head-actions">' +
    '<button class="btn primary" onclick="go(\'billing\')">+ New Bill</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'PURCHASE\')">+ Purchase</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'PAYMENT_IN\')">+ Payment In</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'EXPENSE\')">+ Expense</button></div></div>' +
    (empty ?
      '<div class="card welcome"><h3>👋 Welcome to Shopkeeper!</h3>' +
      '<p>Your free, open-source business manager — billing, inventory, payments &amp; GST reports. All data stays on this device.</p>' +
      '<div class="head-actions" style="margin-top:12px">' +
      '<button class="btn primary" onclick="go(\'settings\')">1. Set up your business profile</button>' +
      '<button class="btn ghost" onclick="openItemForm()">2. Add products</button>' +
      '<button class="btn ghost" onclick="go(\'billing\')">3. Start billing</button>' +
      '<button class="btn ghost" onclick="confirmDemo()">Or load demo data</button></div></div>' : '') +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">Today\'s Sales</div><div class="stat-value">' + fmtMoney(todaySales) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Today\'s Profit</div><div class="stat-value ' + (todayProfit >= 0 ? 'pos' : 'neg') + '">' + fmtMoney(todayProfit) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Bills Created Today</div><div class="stat-value">' + todayBills + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Low Stock Items</div><div class="stat-value ' + (low.length ? 'neg' : '') + '">' + low.length + '</div></div>' +
    '<div class="card stat"><div class="stat-label">To Collect</div><div class="stat-mid pos">' + fmtMoney(totals.receivable) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">To Pay</div><div class="stat-mid neg">' + fmtMoney(totals.payable) + '</div></div>' +
    '</div>' +
    '<div class="card"><h3 class="card-title">Monthly Sales — ' + monthName(d.getMonth()) + ' ' + d.getFullYear() + ' <span class="sub">(total ' + fmtMoney(monthSales) + ')</span></h3>' +
    svgBarChart(chartData, { height: 220 }) + '</div>' +
    '<div class="card"><div class="page-head" style="margin-bottom:8px"><h3 class="card-title" style="margin:0">Stock Availability ' +
    (low.length ? '<span class="badge bad">' + low.length + ' need attention</span>' : '') + '</h3>' +
    '<button class="btn tiny ghost" onclick="repState.key=\'stock\';go(\'reports\')">Full report →</button></div>' +
    (availRows ? '<div class="table-wrap"><table><thead><tr><th>Product</th><th>Category</th><th>Brand</th><th class="r">Available Stock</th></tr></thead><tbody>' +
      availRows + '</tbody></table></div>' +
      (availItems.length > 10 ? '<p class="sub">Showing 10 of ' + availItems.length + ' products — open the full report for all.</p>' : '')
      : '<p class="empty">No products yet — add products in Inventory.</p>') +
    '</div>' +
    '<div class="card"><div class="page-head" style="margin-bottom:8px"><h3 class="card-title" style="margin:0">Recent Bills</h3>' +
    '<button class="btn tiny ghost" onclick="go(\'billing\')">View all →</button></div>' +
    '<div class="table-wrap"><table><thead><tr><th>Date</th><th>Bill No</th><th>Customer</th><th class="r">Amount</th><th>Status</th></tr></thead><tbody>' +
    billRows + '</tbody></table></div></div>';
}

function confirmDemo() {
  openModal(
    '<div class="modal-head"><h3>Load demo data?</h3></div>' +
    '<div class="modal-body"><p>This loads a sample business (parties, items and transactions) so you can explore the app. Existing data will be replaced.</p></div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="closeModal();loadDemoData();route();toast(\'Demo data loaded\')">Load Demo</button></div>'
  );
}

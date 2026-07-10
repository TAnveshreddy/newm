/* VyaparOpen — reports.js */
'use strict';

const REPORTS = [
  ['sale', 'Sale Report'],
  ['purchase', 'Purchase Report'],
  ['daybook', 'Day Book'],
  ['cashflow', 'Cash Flow'],
  ['pnl', 'Profit & Loss'],
  ['party', 'Party Statement'],
  ['allparties', 'All Parties Balance'],
  ['stock', 'Stock Summary'],
  ['itemsales', 'Item Sale Summary'],
  ['lowstock', 'Low Stock'],
  ['expense', 'Expense Report'],
  ['gst', 'GST Summary']
];

let repState = { key: 'sale', from: addDays(todayStr(), -29), to: todayStr(), partyId: '' };

function renderReports() {
  const tabs = REPORTS.map(r =>
    '<button class="rtab' + (repState.key === r[0] ? ' active' : '') + '" onclick="repState.key=\'' + r[0] + '\';renderReports()">' + r[1] + '</button>'
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
    '<button class="btn ghost" style="margin-left:auto" onclick="exportCurrentReport()">⬇ Export CSV</button>' +
    '</div><div id="repBody"></div></div>';

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

function buildReport() {
  const k = repState.key, from = repState.from, to = repState.to;
  let html = '', csv = { name: k + '-report.csv', headers: [], rows: [] };

  if (k === 'sale' || k === 'purchase') {
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

  else if (k === 'pnl') {
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
    const row = (l, v, strong, cls) => '<div class="totals-row' + (strong ? ' grand' : '') + '"><span>' + l + '</span><span class="' + (cls || '') + '">' + fmtMoney(v) + '</span></div>';
    html = '<div class="totals-panel pnl">' +
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

  else if (k === 'stock' || k === 'lowstock') {
    const items = k === 'lowstock' ? lowStockItems() : state.items.filter(i => i.type !== 'service');
    let totVal = 0;
    const rows = items.map(it => {
      const stq = itemStock(it.id);
      const val = Math.max(0, stq) * num(it.purchasePrice || it.salePrice);
      totVal += val;
      return [esc(it.name), esc(it.category || ''), fmtQty(stq) + ' ' + esc(it.unit), fmtQty(it.minStock), fmtMoney(it.purchasePrice), fmtMoney(val)];
    });
    html = tbl([['Item'], ['Category'], ['Stock', 'r'], ['Min Level', 'r'], ['Purchase Price', 'r'], ['Stock Value', 'r']], rows,
      ['Total', '', '', '', '', fmtMoney(totVal)]);
    csv.headers = ['Item', 'Category', 'Stock', 'MinLevel', 'PurchasePrice', 'StockValue'];
    csv.rows = items.map(it => [it.name, it.category, itemStock(it.id), it.minStock, it.purchasePrice, Math.max(0, itemStock(it.id)) * num(it.purchasePrice || it.salePrice)]);
  }

  else if (k === 'itemsales') {
    const map = {};
    for (const t of txnsIn(['SALE'], from, to)) {
      for (const l of (t.lines || [])) {
        const key = l.itemId || l.name;
        if (!map[key]) map[key] = { name: l.name, qty: 0, amount: 0 };
        map[key].qty += num(l.qty);
        map[key].amount += num(l.amount) + num(l.tax);
      }
    }
    const arr = Object.values(map).sort((a, b) => b.amount - a.amount);
    let tq = 0, ta = 0;
    const rows = arr.map(x => { tq += x.qty; ta += x.amount; return [esc(x.name), fmtQty(x.qty), fmtMoney(x.amount)]; });
    html = tbl([['Item'], ['Qty Sold', 'r'], ['Sale Amount', 'r']], rows, ['Total', fmtQty(tq), fmtMoney(ta)]);
    csv.headers = ['Item', 'QtySold', 'SaleAmount'];
    csv.rows = arr.map(x => [x.name, x.qty, round2(x.amount)]);
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

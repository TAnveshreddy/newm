/* VyaparOpen — txns.js : sales, purchases, returns, estimates, payments, expenses */
'use strict';

const LIST_DEFS = {
  sales:     { title: 'Sales',      types: ['SALE'],            add: [['SALE', '+ New Sale']] },
  estimates: { title: 'Estimates / Quotations', types: ['ESTIMATE'], add: [['ESTIMATE', '+ New Estimate']] },
  purchases: { title: 'Purchases',  types: ['PURCHASE'],        add: [['PURCHASE', '+ New Purchase']] },
  returns:   { title: 'Credit / Debit Notes', types: ['SALE_RETURN', 'PURCHASE_RETURN'], add: [['SALE_RETURN', '+ Credit Note (Sale Return)'], ['PURCHASE_RETURN', '+ Debit Note (Purchase Return)']] },
  payments:  { title: 'Payments',   types: ['PAYMENT_IN', 'PAYMENT_OUT'], add: [['PAYMENT_IN', '+ Payment In'], ['PAYMENT_OUT', '+ Payment Out']] },
  expenses:  { title: 'Expenses',   types: ['EXPENSE'],         add: [['EXPENSE', '+ New Expense']] }
};

function renderTxnList(defKey) {
  const def = LIST_DEFS[defKey];
  const q = (window._txnSearch || '').toLowerCase();
  const list = state.txns
    .filter(t => def.types.includes(t.type))
    .filter(t => !q || t.number.toLowerCase().includes(q) || partyName(t.partyId).toLowerCase().includes(q))
    .sort((a, b) => a.date === b.date ? b.createdAt - a.createdAt : (a.date < b.date ? 1 : -1));

  const totalAmt = list.reduce((s, t) => s + num(t.total), 0);
  const totalDue = list.reduce((s, t) => s + (TXN_TYPES[t.type].balance !== 0 && !t.type.startsWith('PAYMENT') ? Math.max(0, num(t.total) - num(t.paid)) : 0), 0);

  let rows = list.map(t => {
    const st = txnStatus(t);
    const badge = st === 'Paid' || st === 'Converted' ? 'ok' : st === 'Partial' ? 'warn' : st === 'Open' ? 'info' : 'bad';
    return '<tr class="rowlink" onclick="viewTxn(\'' + t.id + '\')">' +
      '<td>' + fmtDate(t.date) + '</td>' +
      '<td>' + esc(t.number) + '<div class="sub">' + TXN_TYPES[t.type].label + '</div></td>' +
      '<td>' + esc(t.type === 'EXPENSE' ? (t.category || 'Expense') : partyName(t.partyId)) + '</td>' +
      '<td class="r">' + fmtMoney(t.total) + '</td>' +
      '<td class="r">' + (TXN_TYPES[t.type].balance !== 0 && !t.type.startsWith('PAYMENT') ? fmtMoney(Math.max(0, num(t.total) - num(t.paid))) : '—') + '</td>' +
      '<td><span class="badge ' + badge + '">' + st + '</span></td>' +
      '<td class="r actions" onclick="event.stopPropagation()">' +
      (t.type === 'ESTIMATE' && !t.convertedTo ? '<button class="btn tiny primary" onclick="convertEstimate(\'' + t.id + '\')">To Sale</button> ' : '') +
      ((t.lines || []).length ? '<button class="btn tiny ghost" onclick="printTxn(\'' + t.id + '\')">Print</button> ' : '') +
      '<button class="btn tiny ghost" onclick="openTxnForm(\'' + t.type + '\',\'' + t.id + '\')">Edit</button> ' +
      '<button class="btn tiny danger-ghost" onclick="askDeleteTxn(\'' + t.id + '\')">Delete</button></td></tr>';
  }).join('');
  if (!rows) rows = '<tr><td colspan="7" class="empty">No transactions yet.</td></tr>';

  el('view').innerHTML =
    '<div class="page-head"><h2>' + def.title + '</h2><div class="head-actions">' +
    '<input class="search" placeholder="Search number or party…" value="' + esc(window._txnSearch || '') + '" oninput="_txnSearch=this.value;renderTxnList(\'' + defKey + '\')">' +
    def.add.map(a => '<button class="btn primary" onclick="openTxnForm(\'' + a[0] + '\')">' + a[1] + '</button>').join('') +
    '</div></div>' +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">Total Amount</div><div class="stat-value">' + fmtMoney(totalAmt) + '</div></div>' +
    (defKey === 'sales' || defKey === 'purchases' ? '<div class="card stat"><div class="stat-label">Balance Due</div><div class="stat-value ' + (totalDue ? 'neg' : '') + '">' + fmtMoney(totalDue) + '</div></div>' : '') +
    '</div>' +
    '<div class="card"><div class="table-wrap"><table><thead><tr><th>Date</th><th>Number</th><th>Party / Category</th><th class="r">Total</th><th class="r">Balance</th><th>Status</th><th class="r">Actions</th></tr></thead><tbody>' +
    rows + '</tbody></table></div></div>';
}

function askDeleteTxn(id) {
  confirmDialog('Delete this transaction? Stock and balances will be recalculated.', () => {
    deleteTxn(id);
    toast('Transaction deleted');
    route();
  });
}

/* =========================================================
   Transaction form
   ========================================================= */
let draft = null;

function isItemType(type) {
  return ['SALE', 'PURCHASE', 'SALE_RETURN', 'PURCHASE_RETURN', 'ESTIMATE'].includes(type);
}

function partyOptionsFor(type, selectedId) {
  const kind = TXN_TYPES[type].party;
  const list = state.parties.filter(p => p.type === kind || p.type === 'both')
    .sort((a, b) => a.name.localeCompare(b.name));
  let opts = '<option value="">— ' + (type === 'SALE' || type === 'ESTIMATE' ? 'Cash Sale (no party)' : 'Select party') + ' —</option>';
  for (const p of list) {
    opts += '<option value="' + p.id + '"' + (p.id === selectedId ? ' selected' : '') + '>' + esc(p.name) + '</option>';
  }
  return opts;
}

function openTxnForm(type, id, presetPartyId) {
  const existing = id ? getTxn(id) : null;
  draft = existing ? JSON.parse(JSON.stringify(existing)) : {
    id: null, type: type, number: nextNumber(type), date: todayStr(),
    partyId: presetPartyId || '', lines: [], discountPct: 0, paid: 0,
    mode: 'Cash', category: EXPENSE_CATEGORIES[0], notes: '', total: 0
  };
  if (isItemType(type) && draft.lines.length === 0) draft.lines.push(blankLine());

  const cfg = TXN_TYPES[type];
  let body;
  if (isItemType(type)) {
    body =
      '<div class="form-grid form-grid-4">' +
      '<label>Party<select id="tf_party" onchange="draft.partyId=this.value">' + partyOptionsFor(type, draft.partyId) + '</select></label>' +
      '<label>Number<input id="tf_number" value="' + esc(draft.number) + '"></label>' +
      '<label>Date<input id="tf_date" type="date" value="' + esc(draft.date) + '"></label>' +
      '<label>Payment Mode<select id="tf_mode">' + PAY_MODES.map(m => '<option' + (draft.mode === m ? ' selected' : '') + '>' + m + '</option>').join('') + '</select></label>' +
      '</div>' +
      '<div class="table-wrap"><table class="lines-table"><thead><tr>' +
      '<th style="width:30%">Item</th><th class="r">Qty</th><th>Unit</th><th class="r">Rate (₹)</th><th class="r">Disc %</th><th class="r">GST %</th><th class="r">Amount</th><th></th>' +
      '</tr></thead><tbody id="tf_lines"></tbody></table></div>' +
      '<button class="btn ghost" onclick="draft.lines.push(blankLine());renderLines()">+ Add Row</button>' +
      '<div class="totals-panel" id="tf_totals"></div>' +
      '<label class="notes">Notes<textarea id="tf_notes" rows="2" oninput="draft.notes=this.value">' + esc(draft.notes || '') + '</textarea></label>';
  } else if (type === 'EXPENSE') {
    body =
      '<div class="form-grid">' +
      '<label>Category<select id="tf_cat">' + EXPENSE_CATEGORIES.map(c => '<option' + (draft.category === c ? ' selected' : '') + '>' + c + '</option>').join('') + '</select></label>' +
      '<label>Amount (₹) *<input id="tf_amount" type="number" step="0.01" min="0" value="' + (num(draft.total) || '') + '"></label>' +
      '<label>Date<input id="tf_date" type="date" value="' + esc(draft.date) + '"></label>' +
      '<label>Payment Mode<select id="tf_mode">' + PAY_MODES.filter(m => m !== 'Credit').map(m => '<option' + (draft.mode === m ? ' selected' : '') + '>' + m + '</option>').join('') + '</select></label>' +
      '<label>Number<input id="tf_number" value="' + esc(draft.number) + '"></label>' +
      '<label class="span2">Notes<textarea id="tf_notes" rows="2">' + esc(draft.notes || '') + '</textarea></label></div>';
  } else { // PAYMENT_IN / PAYMENT_OUT
    body =
      '<div class="form-grid">' +
      '<label>Party *<select id="tf_party">' + partyOptionsFor(type, draft.partyId) + '</select></label>' +
      '<label>Amount (₹) *<input id="tf_amount" type="number" step="0.01" min="0" value="' + (num(draft.total) || '') + '"></label>' +
      '<label>Date<input id="tf_date" type="date" value="' + esc(draft.date) + '"></label>' +
      '<label>Payment Mode<select id="tf_mode">' + PAY_MODES.filter(m => m !== 'Credit').map(m => '<option' + (draft.mode === m ? ' selected' : '') + '>' + m + '</option>').join('') + '</select></label>' +
      '<label>Receipt Number<input id="tf_number" value="' + esc(draft.number) + '"></label>' +
      '<label class="span2">Notes<textarea id="tf_notes" rows="2">' + esc(draft.notes || '') + '</textarea></label></div>' +
      '<p class="sub" id="tf_partybal"></p>';
  }

  openModal(
    '<div class="modal-head"><h3>' + (existing ? 'Edit ' : 'New ') + cfg.label + '</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body">' + body + '</div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="saveTxn()">' + (existing ? 'Save Changes' : 'Save ' + cfg.label) + '</button></div>',
    isItemType(type)
  );

  if (isItemType(type)) { renderLines(); }
  if (type === 'PAYMENT_IN' || type === 'PAYMENT_OUT') {
    const sel = el('tf_party');
    const updBal = () => {
      const b = sel.value ? partyBalance(sel.value) : 0;
      el('tf_partybal').textContent = sel.value ? 'Current balance: ' + fmtMoney(Math.abs(b)) + (b >= 0 ? ' to receive' : ' to pay') : '';
    };
    sel.addEventListener('change', updBal);
    updBal();
  }
}

function blankLine() {
  return { itemId: '', name: '', hsn: '', unit: 'PCS', qty: 1, rate: 0, disc: 0, taxRate: 0 };
}

function itemOptions(selectedId) {
  let o = '<option value="">— select item —</option>';
  for (const it of state.items.slice().sort((a, b) => a.name.localeCompare(b.name))) {
    o += '<option value="' + it.id + '"' + (it.id === selectedId ? ' selected' : '') + '>' + esc(it.name) + '</option>';
  }
  return o;
}

function renderLines() {
  const tb = el('tf_lines');
  if (!tb) return;
  tb.innerHTML = draft.lines.map((l, i) => {
    const gross = num(l.qty) * num(l.rate);
    const amt = gross - gross * num(l.disc) / 100;
    return '<tr>' +
      '<td><select onchange="lineItemPick(' + i + ',this.value)">' + itemOptions(l.itemId) + '</select></td>' +
      '<td><input class="r" type="number" step="any" min="0" value="' + num(l.qty) + '" oninput="lineSet(' + i + ',\'qty\',this.value)"></td>' +
      '<td><input value="' + esc(l.unit) + '" oninput="lineSet(' + i + ',\'unit\',this.value)"></td>' +
      '<td><input class="r" type="number" step="0.01" min="0" value="' + num(l.rate) + '" oninput="lineSet(' + i + ',\'rate\',this.value)"></td>' +
      '<td><input class="r" type="number" step="0.01" min="0" max="100" value="' + num(l.disc) + '" oninput="lineSet(' + i + ',\'disc\',this.value)"></td>' +
      '<td><select onchange="lineSet(' + i + ',\'taxRate\',this.value)">' + GST_RATES.map(r => '<option value="' + r + '"' + (num(l.taxRate) === r ? ' selected' : '') + '>' + r + '%</option>').join('') + '</select></td>' +
      '<td class="r amt">' + fmtMoney(amt) + '</td>' +
      '<td><button class="btn tiny danger-ghost" onclick="draft.lines.splice(' + i + ',1);if(!draft.lines.length)draft.lines.push(blankLine());renderLines()">×</button></td></tr>';
  }).join('');
  renderTotals();
}

function lineItemPick(i, itemId) {
  const l = draft.lines[i];
  l.itemId = itemId;
  const it = getItem(itemId);
  if (it) {
    l.name = it.name; l.hsn = it.hsn; l.unit = it.unit;
    l.rate = ['PURCHASE', 'PURCHASE_RETURN'].includes(draft.type) ? num(it.purchasePrice) || num(it.salePrice) : num(it.salePrice);
    l.taxRate = state.settings.taxEnabled ? num(it.taxRate) : 0;
  }
  renderLines();
}

function lineSet(i, field, value) {
  draft.lines[i][field] = field === 'unit' ? value : num(value);
  // update only totals + this row's amount to preserve input focus
  const row = el('tf_lines').rows[i];
  if (row) {
    const l = draft.lines[i];
    const gross = num(l.qty) * num(l.rate);
    row.querySelector('.amt').textContent = fmtMoney(gross - gross * num(l.disc) / 100);
  }
  txnTotalsRecalc();
}

/* Panel is built once; typing only updates the number displays (see billing.js
   for why — rebuilding inputs on their own oninput steals focus mid-keystroke). */
function renderTotals() {
  const box = el('tf_totals');
  if (!box) return;
  const paidLabel = ['SALE', 'ESTIMATE'].includes(draft.type) ? 'Received' : draft.type === 'SALE_RETURN' ? 'Refunded' : 'Paid';
  box.innerHTML =
    '<div class="totals-row"><span>Subtotal (taxable)</span><span id="tf_sub"></span></div>' +
    '<div class="totals-row"><span>Discount <input id="tf_disc" type="number" min="0" max="100" step="0.01" style="width:70px" onfocus="this.select()" value="' + num(draft.discountPct) + '" oninput="draft.discountPct=num(this.value);txnTotalsRecalc()"> %</span><span id="tf_discamt"></span></div>' +
    (state.settings.taxEnabled ? '<div class="totals-row"><span>GST</span><span id="tf_gst"></span></div>' : '') +
    '<div class="totals-row"><span>Round Off</span><span id="tf_ro"></span></div>' +
    '<div class="totals-row grand"><span>Total</span><span id="tf_grand"></span></div>' +
    (draft.type !== 'ESTIMATE' ?
      '<div class="totals-row"><span>' + paidLabel + ' <button class="btn tiny ghost" onclick="draftPaidFull()">Full</button></span>' +
      '<span><input id="tf_paid" type="number" min="0" step="0.01" style="width:110px;text-align:right" onfocus="this.select()" value="' + num(draft.paid) + '" oninput="draft.paid=num(this.value);txnTotalsRecalc()"></span></div>' +
      '<div class="totals-row due"><span>Balance Due</span><span id="tf_due"></span></div>' : '');
  txnTotalsRecalc();
}

function txnTotalsRecalc() {
  const lines = draft.lines.filter(l => l.itemId || num(l.qty) * num(l.rate) > 0);
  const t = computeTotals(JSON.parse(JSON.stringify(lines)), draft.discountPct, state.settings.taxEnabled);
  draft._totals = t;
  el('tf_sub').textContent = fmtMoney(t.subtotal);
  el('tf_discamt').textContent = '− ' + fmtMoney(t.discount);
  if (el('tf_gst')) el('tf_gst').textContent = '+ ' + fmtMoney(t.taxAmount);
  el('tf_ro').textContent = fmtMoney(t.roundOff);
  el('tf_grand').textContent = fmtMoney(t.total);
  if (el('tf_due')) el('tf_due').textContent = fmtMoney(Math.max(0, t.total - num(draft.paid)));
}

function draftPaidFull() {
  draft.paid = draft._totals ? draft._totals.total : 0;
  const inp = el('tf_paid');
  if (inp) inp.value = draft.paid;
  txnTotalsRecalc();
}

function saveTxn() {
  const type = draft.type;
  draft.number = el('tf_number') ? el('tf_number').value.trim() || draft.number : draft.number;
  draft.date = el('tf_date') ? (el('tf_date').value || todayStr()) : draft.date;
  draft.mode = el('tf_mode') ? el('tf_mode').value : draft.mode;
  draft.notes = el('tf_notes') ? el('tf_notes').value.trim() : draft.notes;

  if (isItemType(type)) {
    draft.partyId = el('tf_party').value || null;
    draft.lines = draft.lines.filter(l => l.itemId && num(l.qty) > 0);
    if (draft.lines.length === 0) { toast('Add at least one item line', 'error'); return; }
    // fill denormalized names
    for (const l of draft.lines) {
      const it = getItem(l.itemId);
      if (it) {
        l.name = it.name; l.hsn = it.hsn;
        if (l.cost == null) l.cost = num(it.purchasePrice);
      }
    }
    const t = computeTotals(draft.lines, draft.discountPct, state.settings.taxEnabled);
    Object.assign(draft, t);
    if (type === 'ESTIMATE') draft.paid = 0;
    if (num(draft.paid) > t.total) draft.paid = t.total;
  } else {
    const amount = num(el('tf_amount').value);
    if (amount <= 0) { toast('Enter an amount', 'error'); return; }
    draft.total = amount;
    draft.paid = amount;
    draft.lines = [];
    draft.subtotal = amount; draft.discount = 0; draft.taxAmount = 0; draft.roundOff = 0;
    if (type === 'EXPENSE') {
      draft.category = el('tf_cat').value;
      draft.partyId = null;
    } else {
      draft.partyId = el('tf_party').value || null;
      if (!draft.partyId) { toast('Select a party for the payment', 'error'); return; }
    }
  }
  delete draft._totals;

  if (draft.id) {
    const idx = state.txns.findIndex(t => t.id === draft.id);
    if (idx >= 0) state.txns[idx] = draft;
  } else {
    draft.id = uid();
    draft.createdAt = Date.now();
    state.txns.push(draft);
    bumpCounter(type);
  }
  save();
  closeModal();
  toast(TXN_TYPES[type].label + ' saved');
  const savedId = draft.id;
  route();
  if (isItemType(type) && type !== 'ESTIMATE') {
    // offer print right away
    setTimeout(() => { if (getTxn(savedId)) viewTxn(savedId); }, 60);
  }
}

function convertEstimate(id) {
  const est = getTxn(id);
  if (!est || est.convertedTo) return;
  const sale = JSON.parse(JSON.stringify(est));
  sale.id = uid();
  sale.type = 'SALE';
  sale.number = nextNumber('SALE');
  sale.date = todayStr();
  sale.paid = 0;
  sale.createdAt = Date.now();
  delete sale.convertedTo;
  state.txns.push(sale);
  bumpCounter('SALE');
  est.convertedTo = sale.id;
  save();
  toast('Estimate converted to Sale ' + sale.number);
  route();
}

/* =========================================================
   Transaction detail + print
   ========================================================= */
function viewTxn(id) {
  const t = getTxn(id);
  if (!t) return;
  const cfg = TXN_TYPES[t.type];
  const st = txnStatus(t);
  let linesHtml = '';
  if ((t.lines || []).length) {
    linesHtml = '<div class="table-wrap"><table><thead><tr><th>#</th><th>Item</th><th class="r">Qty</th><th class="r">Rate</th><th class="r">GST</th><th class="r">Amount</th></tr></thead><tbody>' +
      t.lines.map((l, i) => '<tr><td>' + (i + 1) + '</td><td>' + esc(l.name) +
        ([l.brand, l.description].filter(Boolean).length ? '<div class="sub">' + [l.brand, l.description].filter(Boolean).map(esc).join(' — ') + '</div>' : '') +
        '</td><td class="r">' + fmtQty(l.qty) + ' ' + esc(l.unit) + '</td><td class="r">' + fmtMoney(l.rate) + '</td><td class="r">' + num(l.taxRate) + '%</td><td class="r">' + fmtMoney(num(l.amount) + num(l.tax)) + '</td></tr>').join('') +
      '</tbody></table></div>' +
      '<div class="totals-panel">' +
      '<div class="totals-row"><span>Subtotal</span><span>' + fmtMoney(t.subtotal) + '</span></div>' +
      (num(t.discount) ? '<div class="totals-row"><span>Discount</span><span>− ' + fmtMoney(t.discount) + '</span></div>' : '') +
      (num(t.taxAmount) ? '<div class="totals-row"><span>GST</span><span>+ ' + fmtMoney(t.taxAmount) + '</span></div>' : '') +
      '<div class="totals-row grand"><span>Total</span><span>' + fmtMoney(t.total) + '</span></div>' +
      '<div class="totals-row"><span>Paid / Received</span><span>' + fmtMoney(t.paid) + '</span></div>' +
      '<div class="totals-row due"><span>Balance</span><span>' + fmtMoney(Math.max(0, num(t.total) - num(t.paid))) + '</span></div></div>';
  } else {
    linesHtml = '<p class="stat-value">' + fmtMoney(t.total) + '</p><p class="sub">' + esc(t.mode || '') + (t.category ? ' · ' + esc(t.category) : '') + '</p>';
  }
  openModal(
    '<div class="modal-head"><h3>' + cfg.label + ' ' + esc(t.number) + ' <span class="badge ' + (st === 'Paid' || st === 'Converted' ? 'ok' : st === 'Partial' ? 'warn' : 'bad') + '">' + st + '</span></h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body">' +
    '<p><strong>' + esc(t.type === 'EXPENSE' ? (t.category || 'Expense') : partyName(t.partyId)) + '</strong> · ' + fmtDate(t.date) + (t.mode ? ' · ' + esc(t.mode) : '') +
    (t.referredBy ? ' · Referred by ' + esc(t.referredBy) : '') + '</p>' +
    linesHtml +
    (t.notes ? '<p class="sub">Note: ' + esc(t.notes) + '</p>' : '') +
    '</div>' +
    '<div class="modal-foot">' +
    ((t.lines || []).length ? '<button class="btn ghost" onclick="printTxn(\'' + t.id + '\')">🖨 Print / PDF</button>' : '') +
    '<button class="btn ghost" onclick="closeModal();openTxnForm(\'' + t.type + '\',\'' + t.id + '\')">Edit</button>' +
    '<button class="btn primary" onclick="closeModal()">Done</button></div>',
    true
  );
}

function printTxn(id) {
  const t = getTxn(id);
  if (!t) return;
  const s = state.settings;
  const p = t.partyId ? getParty(t.partyId) : null;
  const split = taxSplitFor(t);
  const docTitle = t.type === 'SALE' ? 'TAX INVOICE' : t.type === 'ESTIMATE' ? 'ESTIMATE / QUOTATION' : TXN_TYPES[t.type].label.toUpperCase();

  let rows = t.lines.map((l, i) => {
    const taxHalf = num(l.tax) / 2;
    const meta = [l.brand, l.description].filter(Boolean).join(' — ');
    return '<tr><td>' + (i + 1) + '</td><td>' + esc(l.name) +
      (meta ? '<br><span class="muted" style="font-size:11px">' + esc(meta) + '</span>' : '') +
      '</td><td>' + esc(l.hsn || '') + '</td>' +
      '<td class="r">' + fmtQty(l.qty) + ' ' + esc(l.unit) + '</td><td class="r">' + fmtMoney(l.rate, false) + '</td>' +
      '<td class="r">' + fmtMoney(l.amount, false) + '</td>' +
      (s.taxEnabled ?
        (split === 'IGST'
          ? '<td class="r">' + num(l.taxRate) + '%<br>' + fmtMoney(l.tax, false) + '</td>'
          : '<td class="r">' + (num(l.taxRate) / 2) + '%<br>' + fmtMoney(taxHalf, false) + '</td><td class="r">' + (num(l.taxRate) / 2) + '%<br>' + fmtMoney(taxHalf, false) + '</td>')
        : '') +
      '<td class="r">' + fmtMoney(num(l.amount) + num(l.tax), false) + '</td></tr>';
  }).join('');

  const taxCols = s.taxEnabled ? (split === 'IGST' ? '<th class="r">IGST</th>' : '<th class="r">CGST</th><th class="r">SGST</th>') : '';
  const nCols = 7 + (s.taxEnabled ? (split === 'IGST' ? 1 : 2) : 0);
  const due = Math.max(0, num(t.total) - num(t.paid));

  const html = '<!doctype html><html><head><meta charset="utf-8"><title>' + esc(t.number) + '</title><style>' +
    'body{font:13px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;color:#0b0b0b;margin:24px;max-width:860px}' +
    '.head{display:flex;justify-content:space-between;border-bottom:2px solid #0b0b0b;padding-bottom:12px;margin-bottom:12px}' +
    'h1{font-size:20px;margin:0 0 4px}h2{font-size:14px;letter-spacing:2px;margin:0;text-align:right}' +
    '.muted{color:#52514e}table{width:100%;border-collapse:collapse;margin:12px 0}' +
    'th,td{border:1px solid #c3c2b7;padding:6px 8px;text-align:left;vertical-align:top}' +
    'th{background:#f0efec;font-weight:600}.r{text-align:right}' +
    '.tot td{font-weight:700;background:#f0efec}.foot{display:flex;justify-content:space-between;margin-top:28px}' +
    '.sign{text-align:center;margin-top:40px}.words{font-style:italic}' +
    '@media print{body{margin:8mm}}' +
    '</style></head><body>' +
    '<div class="head"><div><h1>' + esc(s.businessName) + '</h1>' +
    '<div class="muted">' + esc(s.address || '') + (s.phone ? '<br>Phone: ' + esc(s.phone) : '') + (s.email ? ' · ' + esc(s.email) : '') +
    (s.gstin ? '<br><strong>GSTIN: ' + esc(s.gstin) + '</strong>' : '') + '</div></div>' +
    '<div><h2>' + docTitle + '</h2><div class="muted" style="text-align:right">No: <strong>' + esc(t.number) + '</strong><br>Date: ' + fmtDate(t.date) + '</div></div></div>' +
    '<table><tr><td style="width:50%"><strong>Bill To:</strong><br>' +
    (p ? esc(p.name) + (p.address ? '<br>' + esc(p.address) : '') + (p.phone ? '<br>Phone: ' + esc(p.phone) : '') + (p.gstin ? '<br>GSTIN: ' + esc(p.gstin) : '') : 'Cash Sale') +
    '</td><td><strong>Payment:</strong> ' + esc(t.mode || '—') + '<br><strong>Status:</strong> ' + txnStatus(t) +
    (t.referredBy ? '<br><strong>Referred by:</strong> ' + esc(t.referredBy) : '') + '</td></tr></table>' +
    '<table><thead><tr><th>#</th><th>Item</th><th>HSN</th><th class="r">Qty</th><th class="r">Rate</th><th class="r">Taxable</th>' + taxCols + '<th class="r">Amount</th></tr></thead>' +
    '<tbody>' + rows + '</tbody><tfoot>' +
    (num(t.discount) ? '<tr><td colspan="' + (nCols - 1) + '" class="r">Discount</td><td class="r">− ' + fmtMoney(t.discount, false) + '</td></tr>' : '') +
    (num(t.roundOff) ? '<tr><td colspan="' + (nCols - 1) + '" class="r">Round Off</td><td class="r">' + fmtMoney(t.roundOff, false) + '</td></tr>' : '') +
    '<tr class="tot"><td colspan="' + (nCols - 1) + '" class="r">TOTAL</td><td class="r">₹ ' + fmtMoney(t.total, false) + '</td></tr>' +
    (t.type !== 'ESTIMATE' ? '<tr><td colspan="' + (nCols - 1) + '" class="r">Received / Paid</td><td class="r">' + fmtMoney(t.paid, false) + '</td></tr>' +
      '<tr><td colspan="' + (nCols - 1) + '" class="r">Balance Due</td><td class="r">' + fmtMoney(due, false) + '</td></tr>' : '') +
    '</tfoot></table>' +
    '<p class="words"><strong>Amount in words:</strong> ' + amountInWords(t.total) + '</p>' +
    (s.upiId ? '<p class="muted">Pay via UPI: <strong>' + esc(s.upiId) + '</strong></p>' : '') +
    '<div class="foot"><div class="muted" style="max-width:55%"><strong>Terms:</strong><br>' + esc(s.terms || '') + '</div>' +
    '<div class="sign">___________________________<br>Authorised Signatory<br><strong>' + esc(s.signatureName || s.businessName) + '</strong></div></div>' +
    '<script>window.onload=function(){window.print()}<\/script></body></html>';

  const w = window.open('', '_blank');
  if (!w) { toast('Pop-up blocked — allow pop-ups to print', 'error'); return; }
  w.document.write(html);
  w.document.close();
}

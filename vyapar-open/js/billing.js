/* VyaparOpen — billing.js : fast POS-style billing screen */
'use strict';

let bill = null;

function newBill() {
  bill = {
    customerName: '', mobile: '', lines: [],
    discountVal: 0, discountType: 'pct',   // whole-bill discount: % or ₹
    paid: 0, mode: 'Cash', search: '', category: '', brand: '',
    referredBy: '', itemSel: '', desc: ''
  };
}

function renderBilling() {
  if (!bill) newBill();
  el('view').innerHTML =
    '<div class="page-head"><h2>Billing</h2><div class="head-actions">' +
    '<button class="btn ghost" onclick="newBill();renderBilling()">Clear Bill</button></div></div>' +

    '<div class="card">' +
    '<div class="form-grid form-grid-3">' +
    '<label>Customer Name<input id="bl_name" list="bl_names" placeholder="Cash sale (optional)" value="' + esc(bill.customerName) + '" oninput="bill.customerName=this.value" onchange="billCustomerPicked()"></label>' +
    '<datalist id="bl_names">' + state.parties.filter(p => p.type !== 'supplier').map(p => '<option value="' + esc(p.name) + '">').join('') + '</datalist>' +
    '<label>Contact Number<input id="bl_mobile" placeholder="10-digit mobile" maxlength="10" value="' + esc(bill.mobile) + '" oninput="bill.mobile=this.value" onchange="billMobilePicked()"></label>' +
    '<label>Referred By<input id="bl_ref" placeholder="Who referred this customer (optional)" value="' + esc(bill.referredBy) + '" oninput="bill.referredBy=this.value"></label>' +
    '</div>' +

    '<div class="add-item-row">' +
    '<label>Category<select id="bl_cat" onchange="bill.category=this.value;bill.itemSel=\'\';bill.brand=\'\';el(\'bl_brand\').value=\'\';renderItemSelect();renderProductPicker()">' +
    '<option value="">All Categories</option>' +
    [...new Set(state.items.map(i => i.category).filter(Boolean))].sort().map(c => '<option' + (bill.category === c ? ' selected' : '') + '>' + esc(c) + '</option>').join('') +
    '</select></label>' +
    '<label>Item<select id="bl_item" onchange="billItemSelected(this.value)"></select></label>' +
    '<label>Brand<input id="bl_brand" placeholder="Auto-fills from item" value="' + esc(bill.brand) + '" oninput="bill.brand=this.value"></label>' +
    '<label>Product Description<input id="bl_desc" placeholder="Prints on invoice" value="' + esc(bill.desc) + '" oninput="bill.desc=this.value"></label>' +
    '<button class="btn primary" onclick="billAddSelected()">+ Add to Bill</button>' +
    '</div>' +

    '<div class="form-grid" style="grid-template-columns:1fr;margin-top:10px">' +
    '<label>Search Product (quick add)<input id="bl_search" placeholder="Type to search, click a product to add…" value="' + esc(bill.search) + '" oninput="bill.search=this.value;renderProductPicker()"></label>' +
    '</div>' +
    '<div id="bl_products" class="product-picker"></div>' +
    '</div>' +

    '<div class="card">' +
    '<div class="table-wrap"><table class="lines-table"><thead><tr>' +
    '<th style="width:38%">Product</th><th class="r">Quantity</th><th class="r">Price (₹)</th><th class="r">GST %</th><th class="r">Total</th><th></th>' +
    '</tr></thead><tbody id="bl_lines"></tbody></table></div>' +
    '<div class="bill-foot"><div class="bill-pay">' +
    '<label>Payment Mode<select id="bl_mode" onchange="bill.mode=this.value">' + PAY_MODES.map(m => '<option' + (bill.mode === m ? ' selected' : '') + '>' + m + '</option>').join('') + '</select></label>' +
    '</div><div class="totals-panel" id="bl_totals"></div></div>' +
    '<div class="head-actions" style="justify-content:flex-end;margin-top:12px">' +
    '<button class="btn ghost" onclick="saveBill(false)">💾 Save Bill</button>' +
    '<button class="btn primary" onclick="saveBill(true)">🖨 Save &amp; Print Invoice</button></div>' +
    '</div>' +

    '<div class="card"><div class="page-head" style="margin-bottom:8px"><h3 class="card-title" style="margin:0">Recent Bills</h3>' +
    '<input class="search" placeholder="Search bill no / customer…" value="' + esc(window._billSearch || '') + '" oninput="_billSearch=this.value;renderBillList()"></div>' +
    '<div id="bl_list"></div></div>';

  renderItemSelect();
  renderProductPicker();
  renderBillLines();
  renderBillList();
}

function billCustomerPicked() {
  const p = state.parties.find(x => x.name.toLowerCase() === bill.customerName.trim().toLowerCase());
  if (p && p.phone && !bill.mobile) { bill.mobile = p.phone; el('bl_mobile').value = p.phone; }
}

function billMobilePicked() {
  const p = state.parties.find(x => x.phone && x.phone === bill.mobile.trim());
  if (p && !bill.customerName) { bill.customerName = p.name; el('bl_name').value = p.name; }
}

/* ---------- add-item row ---------- */
function renderItemSelect() {
  const sel = el('bl_item');
  if (!sel) return;
  const items = state.items
    .filter(i => !bill.category || i.category === bill.category)
    .sort((a, b) => a.name.localeCompare(b.name));
  sel.innerHTML = '<option value="">— select item —</option>' +
    items.map(i => '<option value="' + i.id + '"' + (bill.itemSel === i.id ? ' selected' : '') + '>' + esc(i.name) + (i.brand ? ' (' + esc(i.brand) + ')' : '') + '</option>').join('');
}

function billItemSelected(itemId) {
  bill.itemSel = itemId;
  const it = getItem(itemId);
  bill.brand = it ? (it.brand || '') : '';
  bill.desc = it ? (it.description || '') : '';
  el('bl_brand').value = bill.brand;
  el('bl_desc').value = bill.desc;
}

function billAddSelected() {
  const it = getItem(bill.itemSel);
  if (!it) { toast('Select an item first', 'error'); return; }
  const brand = (bill.brand || '').trim();
  const desc = (bill.desc || '').trim();
  const existing = bill.lines.find(l => l.itemId === it.id && (l.description || '') === desc && (l.brand || '') === brand);
  if (existing) existing.qty = num(existing.qty) + 1;
  else bill.lines.push({
    itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1,
    brand: brand, description: desc,
    rate: num(it.salePrice), disc: 0,
    taxRate: state.settings.taxEnabled ? num(it.taxRate) : 0,
    cost: num(it.purchasePrice)
  });
  bill.itemSel = ''; bill.brand = ''; bill.desc = '';
  renderItemSelect();
  el('bl_brand').value = ''; el('bl_desc').value = '';
  renderBillLines();
}

/* ---------- quick-add chips ---------- */
function renderProductPicker() {
  const box = el('bl_products');
  if (!box) return;
  const q = (bill.search || '').toLowerCase();
  const matches = state.items
    .filter(i => (!bill.category || i.category === bill.category) &&
      (!q || i.name.toLowerCase().includes(q) || (i.hsn || '').toLowerCase().includes(q)))
    .sort((a, b) => a.name.localeCompare(b.name))
    .slice(0, 12);
  box.innerHTML = matches.length ? matches.map(it => {
    const stock = it.type === 'service' ? null : itemStock(it.id);
    const low = stock !== null && isLowStock(it);
    return '<button class="product-chip' + (stock !== null && stock <= 0 ? ' out' : '') + '" onclick="billAddItem(\'' + it.id + '\')">' +
      '<span class="pc-name">' + esc(it.name) + '</span>' +
      '<span class="pc-meta">' + fmtMoney(it.salePrice) + (stock !== null ? ' · <span class="' + (low ? 'neg' : '') + '">' + fmtQty(stock) + ' ' + esc(it.unit) + '</span>' : '') + '</span></button>';
  }).join('') : '<p class="empty">No matching products. <a class="crumb" onclick="openItemForm()">Add a product</a></p>';
}

function billAddItem(itemId) {
  const it = getItem(itemId);
  if (!it) return;
  const existing = bill.lines.find(l => l.itemId === itemId);
  if (existing) existing.qty = num(existing.qty) + 1;
  else bill.lines.push({
    itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1,
    brand: it.brand || '', description: it.description || '',
    rate: num(it.salePrice), disc: 0,
    taxRate: state.settings.taxEnabled ? num(it.taxRate) : 0,
    cost: num(it.purchasePrice)
  });
  renderBillLines();
}

/* ---------- bill lines ---------- */
function renderBillLines() {
  const tb = el('bl_lines');
  if (!tb) return;
  tb.innerHTML = bill.lines.length ? bill.lines.map((l, i) => {
    const taxable = num(l.qty) * num(l.rate);
    const tot = taxable + (state.settings.taxEnabled ? taxable * num(l.taxRate) / 100 : 0);
    return '<tr>' +
      '<td><strong>' + esc(l.name) + '</strong><div class="sub">' + [l.brand, l.unit].filter(Boolean).map(esc).join(' · ') + '</div>' +
      '<input class="line-desc" placeholder="Product description (prints on invoice)" value="' + esc(l.description || '') + '" oninput="bill.lines[' + i + '].description=this.value"></td>' +
      '<td><div class="qty-ctl"><button class="btn tiny ghost" onclick="billQty(' + i + ',-1)">−</button>' +
      '<input class="r" type="number" step="any" min="0" onfocus="this.select()" value="' + num(l.qty) + '" oninput="billLineSet(' + i + ',\'qty\',this.value)">' +
      '<button class="btn tiny ghost" onclick="billQty(' + i + ',1)">+</button></div></td>' +
      '<td><input class="r" type="number" step="0.01" min="0" onfocus="this.select()" value="' + num(l.rate) + '" oninput="billLineSet(' + i + ',\'rate\',this.value)"></td>' +
      '<td><select onchange="billLineSet(' + i + ',\'taxRate\',this.value)">' + GST_RATES.map(r => '<option value="' + r + '"' + (num(l.taxRate) === r ? ' selected' : '') + '>' + r + '%</option>').join('') + '</select></td>' +
      '<td class="r amt">' + fmtMoney(tot) + '</td>' +
      '<td><button class="btn tiny danger-ghost" onclick="bill.lines.splice(' + i + ',1);renderBillLines()">×</button></td></tr>';
  }).join('') : '<tr><td colspan="6" class="empty">Select an item above (or click a product) to add it to the bill.</td></tr>';
  renderBillTotals();
}

function billQty(i, d) {
  bill.lines[i].qty = Math.max(0, num(bill.lines[i].qty) + d);
  if (bill.lines[i].qty === 0) bill.lines.splice(i, 1);
  renderBillLines();
}

function billLineSet(i, field, value) {
  bill.lines[i][field] = num(value);
  const row = el('bl_lines').rows[i];
  if (row) {
    const l = bill.lines[i];
    const taxable = num(l.qty) * num(l.rate);
    row.querySelector('.amt').textContent = fmtMoney(taxable + (state.settings.taxEnabled ? taxable * num(l.taxRate) / 100 : 0));
  }
  billTotalsRecalc();
}

/* whole-bill discount: convert a ₹ amount into the equivalent % of subtotal */
function billDiscountPct() {
  const sub = bill.lines.reduce((s, l) => s + num(l.qty) * num(l.rate), 0);
  if (bill.discountType === 'amt') {
    return sub > 0 ? Math.min(100, num(bill.discountVal) / sub * 100) : 0;
  }
  return Math.min(100, num(bill.discountVal));
}

/* The totals panel is built once; keystrokes in its inputs only update the
   displayed numbers (billTotalsRecalc). Rebuilding the panel on every input
   event would destroy the input mid-typing and steal focus — the page then
   feels frozen after the first keystroke. */
function renderBillTotals() {
  const box = el('bl_totals');
  if (!box) return;
  box.innerHTML =
    '<div class="totals-row"><span>Subtotal</span><span id="bl_sub"></span></div>' +
    '<div class="totals-row"><span>Discount on entire bill ' +
    '<input id="bl_discin" type="number" min="0" step="0.01" style="width:80px" onfocus="this.select()" value="' + num(bill.discountVal) + '" oninput="bill.discountVal=num(this.value);billTotalsRecalc()"> ' +
    '<select id="bl_disctype" style="width:56px" onchange="bill.discountType=this.value;billTotalsRecalc()">' +
    '<option value="pct"' + (bill.discountType === 'pct' ? ' selected' : '') + '>%</option>' +
    '<option value="amt"' + (bill.discountType === 'amt' ? ' selected' : '') + '>₹</option></select>' +
    '</span><span id="bl_discamt"></span></div>' +
    (state.settings.taxEnabled ? '<div class="totals-row"><span>GST</span><span id="bl_gst"></span></div>' : '') +
    '<div class="totals-row grand"><span>Total</span><span id="bl_grand"></span></div>' +
    '<div class="totals-row"><span>Received <button class="btn tiny ghost" onclick="billPaidFull()">Full</button></span>' +
    '<span><input id="bl_paid" type="number" min="0" step="0.01" style="width:110px;text-align:right" onfocus="this.select()" value="' + num(bill.paid) + '" oninput="bill.paid=num(this.value);billTotalsRecalc()"></span></div>' +
    '<div class="totals-row due"><span>Balance Due</span><span id="bl_due"></span></div>';
  billTotalsRecalc();
}

function billTotalsRecalc() {
  const t = computeTotals(JSON.parse(JSON.stringify(bill.lines)), billDiscountPct(), state.settings.taxEnabled);
  bill._totals = t;
  el('bl_sub').textContent = fmtMoney(t.subtotal);
  el('bl_discamt').textContent = '− ' + fmtMoney(t.discount);
  if (el('bl_gst')) el('bl_gst').textContent = '+ ' + fmtMoney(t.taxAmount);
  el('bl_grand').textContent = fmtMoney(t.total);
  el('bl_due').textContent = fmtMoney(Math.max(0, t.total - num(bill.paid)));
}

function billPaidFull() {
  bill.paid = bill._totals ? bill._totals.total : 0;
  const inp = el('bl_paid');
  if (inp) inp.value = bill.paid;
  billTotalsRecalc();
}

function saveBill(print) {
  bill.lines = bill.lines.filter(l => num(l.qty) > 0);
  if (bill.lines.length === 0) { toast('Add at least one product to the bill', 'error'); return; }

  // resolve / auto-create customer
  let partyId = null;
  const name = bill.customerName.trim();
  const mobile = bill.mobile.trim();
  if (name || mobile) {
    let p = state.parties.find(x =>
      (mobile && x.phone === mobile) || (name && x.name.toLowerCase() === name.toLowerCase()));
    if (!p) {
      p = { id: uid(), name: name || ('Customer ' + mobile), phone: mobile, email: '', gstin: '', address: '', type: 'customer', openingBalance: 0, openingType: 'receive', createdAt: Date.now() };
      state.parties.push(p);
    } else {
      if (mobile && !p.phone) p.phone = mobile;
    }
    partyId = p.id;
  }

  const discountPct = billDiscountPct();
  const totals = computeTotals(bill.lines, discountPct, state.settings.taxEnabled);
  const t = Object.assign({
    id: uid(), type: 'SALE', number: nextNumber('SALE'), date: todayStr(),
    partyId: partyId, lines: bill.lines, discountPct: round2(discountPct),
    referredBy: bill.referredBy.trim(),
    paid: Math.min(num(bill.paid), totals.total), mode: bill.mode, notes: '', createdAt: Date.now()
  }, totals);
  // cash sales are settled in full unless told otherwise
  if (!partyId && num(bill.paid) === 0) t.paid = t.total;
  state.txns.push(t);
  bumpCounter('SALE');
  save();
  toast('Bill ' + t.number + ' saved — ' + fmtMoney(t.total));
  if (print) printTxn(t.id);
  newBill();
  renderBilling();
}

function renderBillList() {
  const box = el('bl_list');
  if (!box) return;
  const q = (window._billSearch || '').toLowerCase();
  const list = state.txns.filter(t => t.type === 'SALE')
    .filter(t => !q || t.number.toLowerCase().includes(q) || partyName(t.partyId).toLowerCase().includes(q))
    .sort((a, b) => a.date === b.date ? b.createdAt - a.createdAt : (a.date < b.date ? 1 : -1))
    .slice(0, 25);
  let rows = list.map(t => {
    const st = txnStatus(t);
    return '<tr class="rowlink" onclick="viewTxn(\'' + t.id + '\')">' +
      '<td>' + fmtDate(t.date) + '</td><td>' + esc(t.number) + '</td>' +
      '<td>' + esc(partyName(t.partyId)) + '</td>' +
      '<td class="r">' + fmtMoney(t.total) + '</td>' +
      '<td><span class="badge ' + (st === 'Paid' ? 'ok' : st === 'Partial' ? 'warn' : 'bad') + '">' + st + '</span></td>' +
      '<td class="r actions" onclick="event.stopPropagation()">' +
      '<button class="btn tiny ghost" onclick="printTxn(\'' + t.id + '\')">Print</button> ' +
      '<button class="btn tiny ghost" onclick="openTxnForm(\'SALE\',\'' + t.id + '\')">Edit</button> ' +
      '<button class="btn tiny danger-ghost" onclick="askDeleteTxn(\'' + t.id + '\')">Delete</button></td></tr>';
  }).join('');
  if (!rows) rows = '<tr><td colspan="6" class="empty">No bills yet — create your first one above!</td></tr>';
  box.innerHTML = '<div class="table-wrap"><table><thead><tr><th>Date</th><th>Bill No</th><th>Customer</th><th class="r">Total</th><th>Status</th><th class="r">Actions</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
}

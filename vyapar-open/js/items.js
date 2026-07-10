/* VyaparOpen — items.js : inventory / products & services */
'use strict';

function renderItems() {
  const q = (window._itemSearch || '').toLowerCase();
  const list = state.items
    .filter(i => !q || i.name.toLowerCase().includes(q) || (i.category || '').toLowerCase().includes(q))
    .sort((a, b) => a.name.localeCompare(b.name));
  const low = lowStockItems();

  let rows = list.map(it => {
    const stock = itemStock(it.id);
    const isLow = it.type !== 'service' && num(it.minStock) > 0 && stock <= num(it.minStock);
    return '<tr class="rowlink" onclick="openItemDetail(\'' + it.id + '\')">' +
      '<td><strong>' + esc(it.name) + '</strong><div class="sub">' + esc(it.category || '') + (it.hsn ? ' · HSN ' + esc(it.hsn) : '') + '</div></td>' +
      '<td><span class="tag">' + (it.type === 'service' ? 'Service' : 'Product') + '</span></td>' +
      '<td class="r">' + fmtMoney(it.salePrice) + '</td>' +
      '<td class="r">' + fmtMoney(it.purchasePrice) + '</td>' +
      '<td class="r">' + num(it.taxRate) + '%</td>' +
      '<td class="r">' + (it.type === 'service' ? '—' :
        (isLow ? '<span class="badge warn" title="Low stock">▲ ' : '<span>') + fmtQty(stock) + ' ' + esc(it.unit) + '</span>') + '</td>' +
      '<td class="r actions" onclick="event.stopPropagation()">' +
      '<button class="btn tiny ghost" onclick="openItemForm(\'' + it.id + '\')">Edit</button> ' +
      '<button class="btn tiny ghost" onclick="openStockAdjust(\'' + it.id + '\')"' + (it.type === 'service' ? ' disabled' : '') + '>Adjust</button> ' +
      '<button class="btn tiny danger-ghost" onclick="deleteItem(\'' + it.id + '\')">Delete</button></td></tr>';
  }).join('');
  if (!rows) rows = '<tr><td colspan="7" class="empty">No items yet. Add products or services you sell.</td></tr>';

  el('view').innerHTML =
    '<div class="page-head"><h2>Items</h2>' +
    '<div class="head-actions">' +
    '<input class="search" placeholder="Search items…" value="' + esc(window._itemSearch || '') + '" oninput="_itemSearch=this.value;renderItems()">' +
    '<button class="btn ghost" onclick="openImportModal(\'items\')">⬆ Import</button>' +
    '<button class="btn primary" onclick="openItemForm()">+ Add Item</button></div></div>' +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">Stock Value (at purchase price)</div><div class="stat-value">' + fmtMoney(stockValue()) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Low Stock Items</div><div class="stat-value ' + (low.length ? 'neg' : '') + '">' + low.length + '</div></div>' +
    '</div>' +
    '<div class="card"><div class="table-wrap"><table><thead><tr><th>Item</th><th>Type</th><th class="r">Sale Price</th><th class="r">Purchase Price</th><th class="r">GST</th><th class="r">Stock</th><th class="r">Actions</th></tr></thead><tbody>' +
    rows + '</tbody></table></div></div>';
}

function openItemForm(id) {
  const it = id ? getItem(id) : null;
  openModal(
    '<div class="modal-head"><h3>' + (it ? 'Edit Item' : 'Add Item') + '</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body"><div class="form-grid">' +
    '<label class="span2">Item Name *<input id="if_name" value="' + esc(it ? it.name : '') + '"></label>' +
    '<label>Type<select id="if_type" onchange="el(\'if_stockwrap\').style.display=this.value===\'service\'?\'none\':\'\'">' +
    '<option value="product"' + (it && it.type === 'product' ? ' selected' : '') + '>Product</option>' +
    '<option value="service"' + (it && it.type === 'service' ? ' selected' : '') + '>Service</option></select></label>' +
    '<label>Category<input id="if_cat" value="' + esc(it ? it.category : '') + '"></label>' +
    '<label>Unit<select id="if_unit">' + UNITS.map(u => '<option' + (it && it.unit === u ? ' selected' : '') + '>' + u + '</option>').join('') + '</select></label>' +
    '<label>HSN / SAC Code<input id="if_hsn" value="' + esc(it ? it.hsn : '') + '"></label>' +
    '<label>Sale Price (₹) *<input id="if_sale" type="number" step="0.01" min="0" value="' + (it ? num(it.salePrice) : '') + '"></label>' +
    '<label>Purchase Price (₹)<input id="if_pur" type="number" step="0.01" min="0" value="' + (it ? num(it.purchasePrice) : '') + '"></label>' +
    '<label>GST Rate %<select id="if_tax">' + GST_RATES.map(r => '<option value="' + r + '"' + (it && num(it.taxRate) === r ? ' selected' : (!it && r === 18 ? ' selected' : '')) + '>' + r + '%</option>').join('') + '</select></label>' +
    '<div class="span2" id="if_stockwrap" style="display:' + (it && it.type === 'service' ? 'none' : 'grid') + ';grid-template-columns:1fr 1fr;gap:12px">' +
    '<label>Opening Stock<input id="if_open" type="number" step="any" min="0" value="' + (it ? num(it.openingStock) : 0) + '"></label>' +
    '<label>Low Stock Alert At<input id="if_min" type="number" step="any" min="0" value="' + (it ? num(it.minStock) : 0) + '"></label></div>' +
    '</div></div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="saveItem(\'' + (id || '') + '\')">Save</button></div>'
  );
}

function saveItem(id) {
  const name = el('if_name').value.trim();
  if (!name) { toast('Item name is required', 'error'); return; }
  const data = {
    name: name,
    type: el('if_type').value,
    category: el('if_cat').value.trim(),
    unit: el('if_unit').value,
    hsn: el('if_hsn').value.trim(),
    salePrice: num(el('if_sale').value),
    purchasePrice: num(el('if_pur').value),
    taxRate: num(el('if_tax').value),
    openingStock: num(el('if_open').value),
    minStock: num(el('if_min').value)
  };
  if (id) Object.assign(getItem(id), data);
  else state.items.push(Object.assign({ id: uid(), createdAt: Date.now() }, data));
  save();
  closeModal();
  toast('Item saved');
  route();
}

function deleteItem(id) {
  const used = state.txns.some(t => (t.lines || []).some(l => l.itemId === id));
  if (used) { toast('Cannot delete: item is used in transactions.', 'error'); return; }
  confirmDialog('Delete this item permanently?', () => {
    state.items = state.items.filter(i => i.id !== id);
    state.adjustments = state.adjustments.filter(a => a.itemId !== id);
    save();
    toast('Item deleted');
    renderItems();
  });
}

function openStockAdjust(id) {
  const it = getItem(id);
  openModal(
    '<div class="modal-head"><h3>Adjust Stock — ' + esc(it.name) + '</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body"><div class="form-grid">' +
    '<label>Adjustment<select id="sa_dir"><option value="1">Add stock (+)</option><option value="-1">Reduce stock (−)</option></select></label>' +
    '<label>Quantity<input id="sa_qty" type="number" step="any" min="0" value="1"></label>' +
    '<label>Date<input id="sa_date" type="date" value="' + todayStr() + '"></label>' +
    '<label>Reason<input id="sa_note" placeholder="e.g. damage, recount"></label>' +
    '</div><p class="sub">Current stock: ' + fmtQty(itemStock(id)) + ' ' + esc(it.unit) + '</p></div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="saveStockAdjust(\'' + id + '\')">Adjust</button></div>'
  );
}

function saveStockAdjust(id) {
  const qty = num(el('sa_qty').value);
  if (qty <= 0) { toast('Enter a quantity', 'error'); return; }
  state.adjustments.push({
    id: uid(), itemId: id, date: el('sa_date').value || todayStr(),
    delta: qty * num(el('sa_dir').value), note: el('sa_note').value.trim(), createdAt: Date.now()
  });
  save();
  closeModal();
  toast('Stock adjusted');
  route();
}

function openItemDetail(id) {
  const it = getItem(id);
  if (!it) return;
  const moves = [];
  for (const t of state.txns) {
    const dir = TXN_TYPES[t.type].stock;
    for (const l of (t.lines || [])) {
      if (l.itemId === id) moves.push({ date: t.date, label: TXN_TYPES[t.type].label + ' ' + t.number, qty: dir * num(l.qty), rate: num(l.rate), txnId: t.id, at: t.createdAt });
    }
  }
  for (const a of state.adjustments) {
    if (a.itemId === id) moves.push({ date: a.date, label: 'Stock Adjustment' + (a.note ? ' — ' + a.note : ''), qty: num(a.delta), rate: null, at: a.createdAt || 0 });
  }
  moves.sort((a, b) => a.date === b.date ? a.at - b.at : (a.date < b.date ? -1 : 1));

  let run = num(it.openingStock);
  let rows = it.type === 'service' ? '' :
    '<tr><td></td><td>Opening Stock</td><td class="r"></td><td class="r"></td><td class="r">' + fmtQty(run) + '</td></tr>';
  for (const m of moves) {
    run += m.qty;
    rows += '<tr' + (m.txnId ? ' class="rowlink" onclick="viewTxn(\'' + m.txnId + '\')"' : '') + '>' +
      '<td>' + fmtDate(m.date) + '</td><td>' + esc(m.label) + '</td>' +
      '<td class="r ' + (m.qty >= 0 ? 'pos' : 'neg') + '">' + (m.qty >= 0 ? '+' : '') + fmtQty(m.qty) + '</td>' +
      '<td class="r">' + (m.rate != null ? fmtMoney(m.rate) : '—') + '</td>' +
      '<td class="r">' + fmtQty(run) + '</td></tr>';
  }
  if (!rows) rows = '<tr><td colspan="5" class="empty">No movements yet.</td></tr>';

  el('view').innerHTML =
    '<div class="page-head"><h2><a class="crumb" onclick="go(\'items\')">Items</a> › ' + esc(it.name) + '</h2>' +
    '<div class="head-actions"><button class="btn ghost" onclick="openItemForm(\'' + id + '\')">Edit</button>' +
    (it.type !== 'service' ? '<button class="btn primary" onclick="openStockAdjust(\'' + id + '\')">Adjust Stock</button>' : '') +
    '</div></div>' +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">Sale Price</div><div class="stat-value">' + fmtMoney(it.salePrice) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Purchase Price</div><div class="stat-value">' + fmtMoney(it.purchasePrice) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">Current Stock</div><div class="stat-value">' + (it.type === 'service' ? '—' : fmtQty(itemStock(id)) + ' ' + esc(it.unit)) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">GST Rate</div><div class="stat-value">' + num(it.taxRate) + '%</div></div></div>' +
    '<div class="card"><h3 class="card-title">Stock Movement</h3><div class="table-wrap"><table><thead><tr>' +
    '<th>Date</th><th>Transaction</th><th class="r">Qty</th><th class="r">Rate</th><th class="r">Stock After</th></tr></thead><tbody>' +
    rows + '</tbody></table></div></div>';
}

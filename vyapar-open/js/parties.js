/* VyaparOpen — parties.js : customers & suppliers */
'use strict';

function renderParties() {
  const q = (window._partySearch || '').toLowerCase();
  const list = state.parties
    .filter(p => !q || p.name.toLowerCase().includes(q) || (p.phone || '').includes(q))
    .sort((a, b) => a.name.localeCompare(b.name));
  const totals = totalsReceivablePayable();

  let rows = list.map(p => {
    const bal = partyBalance(p.id);
    const cls = bal > 0 ? 'pos' : bal < 0 ? 'neg' : '';
    const dir = bal > 0 ? 'You will get' : bal < 0 ? 'You will pay' : '—';
    return '<tr class="rowlink" onclick="openPartyLedger(\'' + p.id + '\')">' +
      '<td><strong>' + esc(p.name) + '</strong><div class="sub">' + esc(p.phone || '') + '</div></td>' +
      '<td><span class="tag">' + esc(p.type) + '</span></td>' +
      '<td>' + esc(p.gstin || '—') + '</td>' +
      '<td class="r ' + cls + '">' + fmtMoney(Math.abs(bal)) + '<div class="sub">' + dir + '</div></td>' +
      '<td class="r actions" onclick="event.stopPropagation()">' +
      '<button class="btn tiny ghost" onclick="openPartyForm(\'' + p.id + '\')">Edit</button> ' +
      '<button class="btn tiny danger-ghost" onclick="deleteParty(\'' + p.id + '\')">Delete</button></td></tr>';
  }).join('');
  if (!rows) rows = '<tr><td colspan="5" class="empty">No parties yet. Add your first customer or supplier.</td></tr>';

  el('view').innerHTML =
    '<div class="page-head"><h2>Customers &amp; Suppliers</h2>' +
    '<div class="head-actions">' +
    '<input class="search" placeholder="Search name or phone…" value="' + esc(window._partySearch || '') + '" oninput="_partySearch=this.value;renderParties()">' +
    '<button class="btn ghost" onclick="openImportModal(\'parties\')">⬆ Import</button>' +
    '<button class="btn primary" onclick="openPartyForm()">+ Add Party</button></div></div>' +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">To Collect (Receivable)</div><div class="stat-value pos">' + fmtMoney(totals.receivable) + '</div></div>' +
    '<div class="card stat"><div class="stat-label">To Pay (Payable)</div><div class="stat-value neg">' + fmtMoney(totals.payable) + '</div></div>' +
    '</div>' +
    '<div class="card"><div class="table-wrap"><table><thead><tr><th>Name</th><th>Type</th><th>GSTIN</th><th class="r">Balance</th><th class="r">Actions</th></tr></thead><tbody>' + rows + '</tbody></table></div></div>';
}

function openPartyForm(id) {
  const p = id ? getParty(id) : null;
  openModal(
    '<div class="modal-head"><h3>' + (p ? 'Edit Party' : 'Add Party') + '</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body"><div class="form-grid">' +
    '<label>Party Name *<input id="pf_name" value="' + esc(p ? p.name : '') + '" required></label>' +
    '<label>Phone<input id="pf_phone" value="' + esc(p ? p.phone : '') + '"></label>' +
    '<label>Email<input id="pf_email" type="email" value="' + esc(p ? p.email : '') + '"></label>' +
    '<label>GSTIN<input id="pf_gstin" maxlength="15" style="text-transform:uppercase" value="' + esc(p ? p.gstin : '') + '"></label>' +
    '<label>Party Type<select id="pf_type">' +
    ['customer', 'supplier', 'both'].map(t => '<option value="' + t + '"' + (p && p.type === t ? ' selected' : '') + '>' + t[0].toUpperCase() + t.slice(1) + '</option>').join('') +
    '</select></label>' +
    '<label class="span2">Billing Address<textarea id="pf_addr" rows="2">' + esc(p ? p.address : '') + '</textarea></label>' +
    '<label>Opening Balance<input id="pf_open" type="number" step="0.01" min="0" value="' + (p ? num(p.openingBalance) : 0) + '"></label>' +
    '<label>Opening Type<select id="pf_opentype">' +
    '<option value="receive"' + (p && p.openingType === 'receive' ? ' selected' : '') + '>To Receive (they owe you)</option>' +
    '<option value="pay"' + (p && p.openingType === 'pay' ? ' selected' : '') + '>To Pay (you owe them)</option>' +
    '</select></label>' +
    '</div></div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="saveParty(\'' + (id || '') + '\')">Save</button></div>'
  );
}

function saveParty(id) {
  const name = el('pf_name').value.trim();
  if (!name) { toast('Party name is required', 'error'); return; }
  const gstin = el('pf_gstin').value.trim().toUpperCase();
  if (gstin && gstin.length !== 15) { toast('GSTIN must be 15 characters', 'error'); return; }
  const data = {
    name: name,
    phone: el('pf_phone').value.trim(),
    email: el('pf_email').value.trim(),
    gstin: gstin,
    type: el('pf_type').value,
    address: el('pf_addr').value.trim(),
    openingBalance: num(el('pf_open').value),
    openingType: el('pf_opentype').value
  };
  if (id) {
    Object.assign(getParty(id), data);
  } else {
    state.parties.push(Object.assign({ id: uid(), createdAt: Date.now() }, data));
  }
  save();
  closeModal();
  toast('Party saved');
  route();
}

function deleteParty(id) {
  const used = state.txns.some(t => t.partyId === id);
  if (used) { toast('Cannot delete: this party has transactions. Delete those first.', 'error'); return; }
  confirmDialog('Delete this party permanently?', () => {
    state.parties = state.parties.filter(p => p.id !== id);
    save();
    toast('Party deleted');
    renderParties();
  });
}

/* ---------- party ledger / statement ---------- */
function openPartyLedger(id) {
  const p = getParty(id);
  if (!p) return;
  const entries = state.txns
    .filter(t => t.partyId === id)
    .sort((a, b) => a.date === b.date ? a.createdAt - b.createdAt : (a.date < b.date ? -1 : 1));

  let bal = partyOpening(p);
  let rows = '<tr><td>' + fmtDate('') + '</td><td>Opening Balance</td><td></td><td class="r"></td><td class="r"></td>' +
    '<td class="r"><strong>' + fmtMoney(Math.abs(bal)) + ' ' + (bal >= 0 ? 'Dr' : 'Cr') + '</strong></td></tr>';
  for (const t of entries) {
    const eff = txnDue(t);
    bal += eff;
    const debit = eff > 0 ? eff : (TXN_TYPES[t.type].balance > 0 ? num(t.total) : 0);
    rows += '<tr class="rowlink" onclick="viewTxn(\'' + t.id + '\')">' +
      '<td>' + fmtDate(t.date) + '</td>' +
      '<td>' + TXN_TYPES[t.type].label + '</td>' +
      '<td>' + esc(t.number) + '</td>' +
      '<td class="r">' + fmtMoney(t.total) + '</td>' +
      '<td class="r">' + (num(t.paid) && TXN_TYPES[t.type].balance !== 0 && t.type.indexOf('PAYMENT') !== 0 ? fmtMoney(t.paid) : '—') + '</td>' +
      '<td class="r">' + fmtMoney(Math.abs(bal)) + ' ' + (bal >= 0 ? 'Dr' : 'Cr') + '</td></tr>';
  }
  const finalBal = partyBalance(id);
  el('view').innerHTML =
    '<div class="page-head"><h2><a class="crumb" onclick="go(\'parties\')">Customers &amp; Suppliers</a> › ' + esc(p.name) + '</h2>' +
    '<div class="head-actions">' +
    '<button class="btn ghost" onclick="openPartyForm(\'' + id + '\')">Edit Party</button>' +
    '<button class="btn primary" onclick="openTxnForm(\'PAYMENT_IN\',null,\'' + id + '\')">+ Payment In</button>' +
    '<button class="btn primary" onclick="openTxnForm(\'SALE\',null,\'' + id + '\')">+ Sale</button></div></div>' +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">Phone</div><div class="stat-mid">' + esc(p.phone || '—') + '</div></div>' +
    '<div class="card stat"><div class="stat-label">GSTIN</div><div class="stat-mid">' + esc(p.gstin || '—') + '</div></div>' +
    '<div class="card stat"><div class="stat-label">' + (finalBal >= 0 ? 'You will get' : 'You will pay') + '</div>' +
    '<div class="stat-value ' + (finalBal >= 0 ? 'pos' : 'neg') + '">' + fmtMoney(Math.abs(finalBal)) + '</div></div></div>' +
    '<div class="card"><h3 class="card-title">Statement (Ledger)</h3><div class="table-wrap"><table><thead><tr>' +
    '<th>Date</th><th>Type</th><th>Number</th><th class="r">Total</th><th class="r">Paid/Recd</th><th class="r">Balance</th></tr></thead><tbody>' +
    rows + '</tbody></table></div></div>';
}

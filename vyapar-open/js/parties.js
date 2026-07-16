/* VyaparOpen — parties.js : Khata (customers & suppliers ledger book) */
'use strict';

function partyLastActivity(id) {
  let last = null;
  for (const t of state.txns) {
    if (t.partyId === id && (!last || t.date > last)) last = t.date;
  }
  return last;
}

function renderParties() {
  const tab = window._khataTab || 'customer';
  const q = (window._partySearch || '').toLowerCase();

  const inTab = p => p.type === tab || p.type === 'both';
  const all = state.parties.filter(inTab);
  const list = all
    .filter(p => !q || p.name.toLowerCase().includes(q) || (p.phone || '').includes(q))
    .sort((a, b) => {
      const la = partyLastActivity(a.id) || '', lb = partyLastActivity(b.id) || '';
      return la === lb ? a.name.localeCompare(b.name) : (la < lb ? 1 : -1);
    });

  // khata totals for this tab: get = they owe us, give = we owe them
  let get = 0, give = 0;
  for (const p of all) {
    const b = partyBalance(p.id);
    if (b > 0) get += b; else give += -b;
  }

  const nCust = state.parties.filter(p => p.type === 'customer' || p.type === 'both').length;
  const nSupp = state.parties.filter(p => p.type === 'supplier' || p.type === 'both').length;
  const ktab = (key, label) =>
    '<button class="rtab' + (tab === key ? ' active' : '') + '" onclick="_khataTab=\'' + key + '\';renderParties()">' + label + '</button>';

  let rows = list.map(p => {
    const bal = partyBalance(p.id);
    const last = partyLastActivity(p.id);
    const dir = bal > 0 ? '<div class="sub" style="color:var(--bad)">YOU\'LL GET</div>'
      : bal < 0 ? '<div class="sub" style="color:var(--good)">YOU\'LL GIVE</div>' : '<div class="sub">Settled</div>';
    const amtCls = bal > 0 ? 'neg' : bal < 0 ? 'pos' : '';
    return '<tr class="rowlink" onclick="openPartyLedger(\'' + p.id + '\')">' +
      '<td><span class="avatar">' + esc((p.name || '?')[0].toUpperCase()) + '</span></td>' +
      '<td><strong>' + esc(p.name) + '</strong><div class="sub">' + esc(p.phone || '') +
      (last ? ' · last ' + fmtDate(last) : '') + '</div></td>' +
      '<td class="r"><span class="' + amtCls + '" style="font-weight:700">' + fmtMoney(Math.abs(bal)) + '</span>' + dir + '</td>' +
      '<td class="r actions" onclick="event.stopPropagation()">' +
      '<button class="btn tiny ghost" onclick="openPartyForm(\'' + p.id + '\')">Edit</button> ' +
      '<button class="btn tiny danger-ghost" onclick="deleteParty(\'' + p.id + '\')">Delete</button></td></tr>';
  }).join('');
  if (!rows) rows = '<tr><td colspan="4" class="empty">No ' + (tab === 'customer' ? 'customers' : 'suppliers') + ' yet — add one to start the khata.</td></tr>';

  el('view').innerHTML =
    '<div class="page-head"><h2>Khata</h2>' +
    '<div class="head-actions">' +
    '<button class="btn ghost" onclick="openImportModal(\'parties\')">⬆ Import</button>' +
    '<button class="btn primary" onclick="openPartyForm(null,\'' + tab + '\')">+ Add ' + (tab === 'customer' ? 'Customer' : 'Supplier') + '</button>' +
    '</div></div>' +
    '<div class="rtabs">' +
    ktab('customer', 'Customers <span class="badge info">' + nCust + '</span>') +
    ktab('supplier', 'Suppliers <span class="badge info">' + nSupp + '</span>') +
    '<button class="rtab" onclick="go(\'expenses\')">Expenses</button>' +
    '<button class="rtab" onclick="go(\'reports\')">Reports</button>' +
    '</div>' +
    '<div class="card"><div class="khata-head">' +
    '<div>You\'ll Give: <strong class="pos">' + fmtMoney(give) + '</strong> <span class="pos">↗</span></div>' +
    '<div>You\'ll Get: <strong class="neg">' + fmtMoney(get) + '</strong> <span class="neg">↙</span></div>' +
    '<input class="search" style="margin-left:auto" placeholder="Name or phone number…" value="' + esc(window._partySearch || '') + '" oninput="_partySearch=this.value;renderParties()">' +
    '</div>' +
    '<div class="table-wrap"><table><thead><tr><th style="width:44px"></th><th>Name</th><th class="r">Amount</th><th class="r">Actions</th></tr></thead><tbody>' +
    rows + '</tbody></table></div></div>';
}

function openPartyForm(id, presetType) {
  const p = id ? getParty(id) : null;
  const selType = p ? p.type : (presetType || 'customer');
  openModal(
    '<div class="modal-head"><h3>' + (p ? 'Edit Party' : 'Add ' + (selType === 'supplier' ? 'Supplier' : 'Customer')) + '</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body"><div class="form-grid">' +
    '<label>Name *<input id="pf_name" value="' + esc(p ? p.name : '') + '" required></label>' +
    '<label>Phone<input id="pf_phone" value="' + esc(p ? p.phone : '') + '"></label>' +
    '<label>Email<input id="pf_email" type="email" value="' + esc(p ? p.email : '') + '"></label>' +
    '<label>GSTIN<input id="pf_gstin" maxlength="15" style="text-transform:uppercase" value="' + esc(p ? p.gstin : '') + '"></label>' +
    '<label>Type<select id="pf_type">' +
    [['customer', 'Customer'], ['supplier', 'Supplier'], ['both', 'Both']].map(([v, lbl]) => '<option value="' + v + '"' + (selType === v ? ' selected' : '') + '>' + lbl + '</option>').join('') +
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
  if (!name) { toast('Name is required', 'error'); return; }
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
  toast('Saved');
  route();
}

function deleteParty(id) {
  const used = state.txns.some(t => t.partyId === id);
  if (used) { toast('Cannot delete: this party has transactions. Delete those first.', 'error'); return; }
  confirmDialog('Delete this party permanently?', () => {
    state.parties = state.parties.filter(p => p.id !== id);
    save();
    toast('Deleted');
    renderParties();
  });
}

/* ---------- party ledger / khata statement ---------- */
function openPartyLedger(id) {
  const p = getParty(id);
  if (!p) return;
  const entries = state.txns
    .filter(t => t.partyId === id)
    .sort((a, b) => a.date === b.date ? a.createdAt - b.createdAt : (a.date < b.date ? -1 : 1));

  let bal = partyOpening(p);
  let rows = '<tr><td></td><td>Opening Balance</td><td></td><td class="r"></td><td class="r"></td>' +
    '<td class="r"><strong>' + fmtMoney(Math.abs(bal)) + ' ' + (bal >= 0 ? 'Dr' : 'Cr') + '</strong></td></tr>';
  for (const t of entries) {
    const eff = txnDue(t);
    bal += eff;
    rows += '<tr class="rowlink" onclick="viewTxn(\'' + t.id + '\')">' +
      '<td>' + fmtDate(t.date) + '</td>' +
      '<td>' + TXN_TYPES[t.type].label + '</td>' +
      '<td>' + esc(t.number) + '</td>' +
      '<td class="r">' + fmtMoney(t.total) + '</td>' +
      '<td class="r">' + (num(t.paid) && TXN_TYPES[t.type].balance !== 0 && t.type.indexOf('PAYMENT') !== 0 ? fmtMoney(t.paid) : '—') + '</td>' +
      '<td class="r">' + fmtMoney(Math.abs(bal)) + ' ' + (bal >= 0 ? 'Dr' : 'Cr') + '</td></tr>';
  }
  const finalBal = partyBalance(id);
  const isSupp = p.type === 'supplier' || p.type === 'both';
  el('view').innerHTML =
    '<div class="page-head"><h2><a class="crumb" onclick="go(\'parties\')">Khata</a> › ' + esc(p.name) + '</h2>' +
    '<div class="head-actions">' +
    '<button class="btn ghost" onclick="openPartyForm(\'' + id + '\')">Edit</button>' +
    '<button class="btn ghost" onclick="openTxnForm(\'PAYMENT_OUT\',null,\'' + id + '\')">You Gave ₹ (Pay Out)</button>' +
    '<button class="btn primary" onclick="openTxnForm(\'PAYMENT_IN\',null,\'' + id + '\')">You Got ₹ (Pay In)</button>' +
    (isSupp ? '<button class="btn ghost" onclick="openTxnForm(\'PURCHASE\',null,\'' + id + '\')">+ Purchase</button>' : '') +
    '<button class="btn primary" onclick="openTxnForm(\'SALE\',null,\'' + id + '\')">+ Sale</button></div></div>' +
    '<div class="cards">' +
    '<div class="card stat"><div class="stat-label">Phone</div><div class="stat-mid">' + esc(p.phone || '—') + '</div></div>' +
    '<div class="card stat"><div class="stat-label">GSTIN</div><div class="stat-mid">' + esc(p.gstin || '—') + '</div></div>' +
    '<div class="card stat"><div class="stat-label">' + (finalBal >= 0 ? 'You\'ll Get' : 'You\'ll Give') + '</div>' +
    '<div class="stat-value ' + (finalBal >= 0 ? 'neg' : 'pos') + '">' + fmtMoney(Math.abs(finalBal)) + '</div></div></div>' +
    '<div class="card"><h3 class="card-title">Khata Statement</h3><div class="table-wrap"><table><thead><tr>' +
    '<th>Date</th><th>Type</th><th>Number</th><th class="r">Total</th><th class="r">Paid/Recd</th><th class="r">Balance</th></tr></thead><tbody>' +
    rows + '</tbody></table></div></div>';
}

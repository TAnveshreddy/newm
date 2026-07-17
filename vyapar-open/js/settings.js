/* VyaparOpen — settings.js : business profile, preferences, backup/restore */
'use strict';

function renderSettings() {
  const s = state.settings;
  el('view').innerHTML =
    '<div class="page-head"><h2>Settings</h2></div>' +
    '<div class="grid-2">' +
    '<div class="card"><h3 class="card-title">Business Profile (shown on invoices)</h3><div class="form-grid">' +
    '<label class="span2">Business Name<input id="st_name" value="' + esc(s.businessName) + '"></label>' +
    '<label class="span2">Address<textarea id="st_addr" rows="2">' + esc(s.address) + '</textarea></label>' +
    '<label>Phone<input id="st_phone" value="' + esc(s.phone) + '"></label>' +
    '<label>Email<input id="st_email" value="' + esc(s.email) + '"></label>' +
    '<label>GSTIN<input id="st_gstin" maxlength="15" style="text-transform:uppercase" value="' + esc(s.gstin) + '"></label>' +
    '<label>UPI ID (for invoice)<input id="st_upi" value="' + esc(s.upiId) + '"></label>' +
    '<label>Signatory Name<input id="st_sign" value="' + esc(s.signatureName) + '"></label>' +
    '<label class="span2">Invoice Terms<textarea id="st_terms" rows="2">' + esc(s.terms) + '</textarea></label>' +
    '</div><div style="margin-top:12px"><button class="btn primary" onclick="saveSettings()">Save Profile</button></div></div>' +

    '<div>' +
    '<div class="card"><h3 class="card-title">Preferences</h3>' +
    '<label class="switch-row"><input type="checkbox" id="st_tax"' + (s.taxEnabled ? ' checked' : '') + ' onchange="state.settings.taxEnabled=this.checked;save();toast(\'Saved\')"> Enable GST on transactions</label>' +
    '<label class="switch-row"><input type="checkbox" id="st_dark"' + (s.theme === 'dark' ? ' checked' : '') + ' onchange="state.settings.theme=this.checked?\'dark\':\'light\';save();applyTheme()"> Dark theme</label>' +
    '</div>' +

    '<div class="card"><h3 class="card-title">☁️ Google Drive Sync</h3>' +
    '<p class="sub">' + syncStatusText(s) + '</p>' +
    '<div class="head-actions" style="margin-top:10px;flex-wrap:wrap">' +
    '<button class="btn primary" onclick="openSyncSetup()">' + ((s.gClientId || s.syncUrl) ? 'Sync Settings' : 'Set Up Sync') + '</button>' +
    ((s.gClientId || s.syncUrl) ? '<button class="btn ghost" onclick="syncNow(\'push\')">⬆ Upload Now</button>' +
      '<button class="btn ghost" onclick="syncNow(\'pull\')">⬇ Download Now</button>' : '') +
    '</div></div>' +

    '<div class="card"><h3 class="card-title">Backup &amp; Restore</h3>' +
    '<p class="sub">All data is stored only in this browser (localStorage). Take regular backups — clearing browser data will erase everything.</p>' +
    '<div class="head-actions" style="margin-top:10px;flex-wrap:wrap">' +
    '<button class="btn primary" onclick="exportBackup()">⬇ Download Backup (JSON)</button>' +
    '<button class="btn ghost" onclick="el(\'st_file\').click()">⬆ Restore from Backup</button>' +
    '<input type="file" id="st_file" accept=".json,application/json" style="display:none" onchange="restoreFile(this)">' +
    '</div></div>' +

    '<div class="card"><h3 class="card-title">Danger Zone</h3>' +
    '<div class="head-actions" style="flex-wrap:wrap">' +
    '<button class="btn ghost" onclick="confirmDemo()">Load Demo Data</button>' +
    '<button class="btn danger" onclick="wipeAll()">Erase All Data</button></div></div>' +

    '<div class="card"><h3 class="card-title">About</h3>' +
    '<p class="sub"><strong>Shopkeeper</strong> — free &amp; open-source business management (billing · inventory · GST). ' +
    'Works fully offline; no account, no server, no tracking. MIT licensed.</p></div>' +
    '</div></div>';
}

function saveSettings() {
  const s = state.settings;
  s.businessName = el('st_name').value.trim() || 'My Business';
  s.address = el('st_addr').value.trim();
  s.phone = el('st_phone').value.trim();
  s.email = el('st_email').value.trim();
  s.gstin = el('st_gstin').value.trim().toUpperCase();
  s.upiId = el('st_upi').value.trim();
  s.signatureName = el('st_sign').value.trim();
  s.terms = el('st_terms').value.trim();
  save();
  el('bizName').textContent = s.businessName;
  toast('Settings saved');
}

function restoreFile(input) {
  const f = input.files && input.files[0];
  if (!f) return;
  importBackup(f, (ok, err) => {
    if (ok) { applyTheme(); route(); toast('Backup restored'); }
    else toast('Restore failed: ' + err, 'error');
    input.value = '';
  });
}

function wipeAll() {
  confirmDialog('Erase ALL data (parties, items, transactions, settings)? This cannot be undone. Download a backup first!', () => {
    state = defaultState();
    save();
    applyTheme();
    route();
    toast('All data erased');
  });
}

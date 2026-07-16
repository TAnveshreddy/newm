/* VyaparOpen — sync.js : sync data to the user's own Google Sheet
   via a personal Google Apps Script web app (no server, no API keys).
   One-click sync: newest side wins (compares meta.updatedAt). */
'use strict';

const LAST_SYNC_KEY = 'shopkeeper_last_sync'; // kept outside state so syncing doesn't dirty it

const APPS_SCRIPT_CODE =
`function sheet_() {
  var files = DriveApp.getFilesByName('Shopkeeper Sync Data');
  var ss = files.hasNext() ? SpreadsheetApp.open(files.next())
                           : SpreadsheetApp.create('Shopkeeper Sync Data');
  return ss.getSheets()[0];
}
function doGet() {
  var sh = sheet_();
  var last = sh.getLastRow();
  var json = '';
  if (last > 0) {
    var rows = sh.getRange(1, 1, last, 1).getValues();
    for (var i = 0; i < rows.length; i++) json += rows[i][0];
  }
  return ContentService.createTextOutput(json || '{}')
    .setMimeType(ContentService.MimeType.JSON);
}
function doPost(e) {
  var sh = sheet_();
  sh.clearContents();
  var data = e.postData.contents;
  var chunks = [];
  for (var i = 0; i < data.length; i += 45000) chunks.push([data.slice(i, i + 45000)]);
  sh.getRange(1, 1, chunks.length, 1).setValues(chunks);
  return ContentService.createTextOutput('OK');
}`;

function lastSyncText() {
  const t = num(localStorage.getItem(LAST_SYNC_KEY));
  if (!t) return state.settings.syncUrl ? 'Not synced yet' : '';
  const d = new Date(t);
  return 'Last sync: ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') +
    ' ' + fmtDate(d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'));
}

function updateSyncUI() {
  const info = el('syncInfo');
  if (info) info.textContent = lastSyncText();
  const btn = el('syncBtn');
  if (btn) btn.title = state.settings.syncEmail ? 'Sync (' + state.settings.syncEmail + ')' : 'Set up Google Sheet sync';
}

function setSyncBusy(busy) {
  const btn = el('syncBtn');
  if (!btn) return;
  btn.disabled = busy;
  btn.textContent = busy ? '⏳ Syncing…' : '🔄 Sync';
}

async function syncNow(force) {
  const s = state.settings;
  if (!s.syncUrl) { openSyncSetup(); return; }
  setSyncBusy(true);
  try {
    let remote = null;
    if (force !== 'push') {
      const res = await fetch(s.syncUrl, { method: 'GET' });
      if (!res.ok) throw new Error('server returned ' + res.status);
      try { remote = JSON.parse(await res.text()); } catch (e) { remote = null; }
    }
    const rAt = remote && remote.meta ? num(remote.meta.updatedAt) : 0;
    const lAt = state.meta ? num(state.meta.updatedAt) : 0;
    // safety: a device with no data must never overwrite a sheet that has data
    const localEmpty = !state.txns.length && !state.items.length && !state.parties.length;
    const remoteHasData = !!(remote && remote.settings);

    if (!force && remoteHasData && localEmpty) {
      applyRemoteState(remote);
      toast('Synced ⬇ — your data downloaded from the Google Sheet');
    } else if (force === 'pull') {
      if (remote && remote.settings) { applyRemoteState(remote); toast('Downloaded data from your Google Sheet'); }
      else toast('No data found in the Google Sheet yet', 'error');
    } else if (force === 'push') {
      await pushStateToSheet();
      toast('Uploaded data to your Google Sheet');
    } else if (remote && remote.settings && rAt > lAt) {
      applyRemoteState(remote);
      toast('Synced ⬇ — newer data downloaded from your Google Sheet');
    } else if (!remote || !remote.settings || lAt > rAt) {
      await pushStateToSheet();
      toast('Synced ⬆ — data uploaded to your Google Sheet');
    } else {
      toast('Already up to date ✓');
    }
    localStorage.setItem(LAST_SYNC_KEY, String(Date.now()));
  } catch (e) {
    toast('Sync failed: ' + e.message + ' (check internet & sync link)', 'error');
  }
  setSyncBusy(false);
  updateSyncUI();
}

async function pushStateToSheet() {
  const res = await fetch(state.settings.syncUrl, {
    method: 'POST',
    // text/plain avoids a CORS preflight, which Apps Script web apps don't answer
    headers: { 'Content-Type': 'text/plain;charset=utf-8' },
    body: JSON.stringify(state)
  });
  if (!res.ok) throw new Error('upload failed (' + res.status + ')');
}

function applyRemoteState(remote) {
  const keepUrl = state.settings.syncUrl, keepEmail = state.settings.syncEmail;
  state = remote;
  const d = defaultState();
  state.settings = Object.assign(d.settings, state.settings || {});
  state.counters = Object.assign(d.counters, state.counters || {});
  state.parties = state.parties || []; state.items = state.items || [];
  state.txns = state.txns || []; state.adjustments = state.adjustments || [];
  if (!state.settings.syncUrl) state.settings.syncUrl = keepUrl;
  if (!state.settings.syncEmail) state.settings.syncEmail = keepEmail;
  save();
  applyTheme();
  const bn = el('bizName');
  if (bn) bn.textContent = state.settings.businessName;
  route();
}

/* ---------- one-time setup wizard ---------- */
function openSyncSetup() {
  const s = state.settings;
  openModal(
    '<div class="modal-head"><h3>🔄 Google Sheet Sync — one-time setup</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body">' +
    '<p class="sub">Your data will be saved to a Google Sheet in <strong>your own Google account</strong>. Set this up once, then paste the same link on your mobile — one tap on Sync shows the same data everywhere.</p>' +
    '<ol style="padding-left:18px;line-height:1.9;font-size:13.5px">' +
    '<li>Open <strong>script.google.com/create</strong> (login with your Google email)</li>' +
    '<li>Delete the existing code, paste the code below, press <strong>Ctrl+S</strong></li>' +
    '<li>Click <strong>Deploy → New deployment → ⚙ → Web app</strong></li>' +
    '<li>Set <strong>Execute as: Me</strong> and <strong>Who has access: Anyone</strong> → Deploy → Authorise</li>' +
    '<li>Copy the <strong>Web app URL</strong> and paste it below</li></ol>' +
    '<div style="position:relative;margin:8px 0">' +
    '<textarea id="sy_code" readonly rows="6" style="font-family:monospace;font-size:11px;border-radius:10px">' + esc(APPS_SCRIPT_CODE) + '</textarea>' +
    '<button class="btn tiny ghost" style="position:absolute;top:8px;right:8px" onclick="el(\'sy_code\').select();document.execCommand(\'copy\');toast(\'Code copied\')">Copy code</button></div>' +
    '<div class="form-grid">' +
    '<label>Your Google Email<input id="sy_email" type="email" placeholder="you@gmail.com" value="' + esc(s.syncEmail || '') + '"></label>' +
    '<label>Web App URL<input id="sy_url" placeholder="https://script.google.com/macros/s/…/exec" value="' + esc(s.syncUrl || '') + '"></label>' +
    '</div>' +
    '<p class="sub" style="margin-top:8px">⚠ Keep the link private — anyone who has it can read your data. Sync needs internet; billing keeps working offline.</p>' +
    '</div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" onclick="saveSyncSetup()">Save &amp; Sync Now</button></div>',
    true
  );
}

function saveSyncSetup() {
  const url = el('sy_url').value.trim();
  const email = el('sy_email').value.trim();
  if (!url || !/^https?:\/\//.test(url)) { toast('Paste the Web App URL (starts with https://)', 'error'); return; }
  state.settings.syncUrl = url;
  state.settings.syncEmail = email;
  // persist WITHOUT bumping meta.updatedAt — configuring sync is not a data
  // change, and a fresh device must not look "newer" than the sheet
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {}
  closeModal();
  updateSyncUI();
  syncNow();
}

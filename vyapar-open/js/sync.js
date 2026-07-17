/* VyaparOpen — sync.js : sync data to the user's own Google account.
   Primary: Google Drive via "Continue with Google" (OAuth, no server).
   Fallback: personal Google Apps Script web app link (works from file://).
   One-click sync: newest side wins (compares meta.updatedAt). */
'use strict';

const LAST_SYNC_KEY = 'shopkeeper_last_sync'; // kept outside state so syncing doesn't dirty it
const DRIVE_FILE_NAME = 'Shopkeeper Sync Data.json';
const DRIVE_SCOPES = 'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/userinfo.email';

/* The app's own Google registration, baked into the shipped file — exactly how
   WhatsApp ships its registration inside the app so users never see it.
   Empty in the open-source template; the setup wizard's "Download connected
   website file" button fills it in and the owner re-uploads that file. */
const BUILT_IN_CLIENT_ID = '';

function activeClientId() {
  return state.settings.gClientId || BUILT_IN_CLIENT_ID;
}

let _gToken = null, _gTokenExp = 0, _gFresh = false;

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

/* save without bumping meta.updatedAt — sync settings are not "data",
   and a freshly configured device must not look newer than the cloud copy */
function persistQuiet() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {}
}

/* Called at boot. A link like https://…/#gcid=xxx (shared from the setup
   screen) carries the Google connection ID to a new device. */
function syncBootstrap() {
  const m = (location.hash || '').match(/gcid=([A-Za-z0-9._-]+)/);
  if (m) {
    state.settings.gClientId = m[1];
    persistQuiet();
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {}
    toast('Google sync link received — tap 🔄 Sync to connect');
  }
  // preload Google's sign-in library so the Sync click can open the popup instantly
  if (activeClientId()) loadGsi().catch(() => {});
}

function lastSyncText() {
  const t = num(localStorage.getItem(LAST_SYNC_KEY));
  if (!t) return (activeClientId() || state.settings.syncUrl) ? 'Not synced yet' : '';
  const d = new Date(t);
  return 'Last sync: ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0') +
    ' ' + fmtDate(d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'));
}

function updateSyncUI() {
  const info = el('syncInfo');
  if (info) info.textContent = lastSyncText();
  const btn = el('syncBtn');
  if (btn) btn.title = state.settings.syncEmail ? 'Sync (' + state.settings.syncEmail + ')' : 'Set up sync with Google';
}

function setSyncBusy(busy) {
  const btn = el('syncBtn');
  if (!btn) return;
  btn.disabled = busy;
  btn.textContent = busy ? '⏳ Syncing…' : '🔄 Sync';
}

async function syncNow(force) {
  const s = state.settings;
  if (!activeClientId() && !s.syncUrl) { openSyncSetup(); return; }
  setSyncBusy(true);
  try {
    if (activeClientId()) await driveSync(force);
    else await sheetSync(force);
    localStorage.setItem(LAST_SYNC_KEY, String(Date.now()));
  } catch (e) {
    toast('Sync failed: ' + e.message, 'error');
  }
  setSyncBusy(false);
  updateSyncUI();
}

/* shared decision: what to do given the remote copy and an optional force */
async function applySyncDecision(remote, force, push, where) {
  const rAt = remote && remote.meta ? num(remote.meta.updatedAt) : 0;
  const lAt = state.meta ? num(state.meta.updatedAt) : 0;
  // safety: a device with no data must never overwrite a cloud copy that has data
  const localEmpty = !state.txns.length && !state.items.length && !state.parties.length;
  const remoteHasData = !!(remote && remote.settings);

  if (!force && remoteHasData && localEmpty) {
    applyRemoteState(remote);
    toast('Synced ⬇ — your data downloaded from ' + where);
  } else if (force === 'pull') {
    if (remoteHasData) { applyRemoteState(remote); toast('Downloaded data from ' + where); }
    else toast('No data found in ' + where + ' yet', 'error');
  } else if (force === 'push') {
    await push();
    toast('Uploaded data to ' + where);
  } else if (remoteHasData && rAt > lAt) {
    applyRemoteState(remote);
    toast('Synced ⬇ — newer data downloaded from ' + where);
  } else if (!remoteHasData || lAt > rAt) {
    await push();
    toast('Synced ⬆ — data uploaded to ' + where);
  } else {
    toast('Already up to date ✓');
  }
}

function applyRemoteState(remote) {
  const keepUrl = state.settings.syncUrl, keepEmail = state.settings.syncEmail, keepCid = state.settings.gClientId;
  state = remote;
  const d = defaultState();
  state.settings = Object.assign(d.settings, state.settings || {});
  state.counters = Object.assign(d.counters, state.counters || {});
  state.parties = state.parties || []; state.items = state.items || [];
  state.txns = state.txns || []; state.adjustments = state.adjustments || [];
  if (!state.settings.syncUrl) state.settings.syncUrl = keepUrl;
  if (!state.settings.syncEmail) state.settings.syncEmail = keepEmail;
  if (!state.settings.gClientId) state.settings.gClientId = keepCid;
  save();
  applyTheme();
  const bn = el('bizName');
  if (bn) bn.textContent = state.settings.businessName;
  route();
}

/* ================= Google Drive sync (Continue with Google) ================= */

function loadGsi() {
  if (window.google && google.accounts && google.accounts.oauth2) return Promise.resolve();
  if (window._gsiLoading) return window._gsiLoading;
  window._gsiLoading = new Promise((resolve, reject) => {
    const sc = document.createElement('script');
    sc.src = 'https://accounts.google.com/gsi/client';
    sc.onload = resolve;
    sc.onerror = () => { window._gsiLoading = null; reject(new Error('could not load Google sign-in (check internet)')); };
    document.head.appendChild(sc);
  });
  return window._gsiLoading;
}

function getDriveToken(askConsent) {
  if (_gToken && Date.now() < _gTokenExp - 60000) { _gFresh = false; return Promise.resolve(_gToken); }
  return loadGsi().then(() => new Promise((resolve, reject) => {
    const tc = google.accounts.oauth2.initTokenClient({
      client_id: activeClientId(),
      scope: DRIVE_SCOPES,
      // preselect the account this shop already backs up to
      hint: state.settings.syncEmail || undefined,
      callback: (resp) => {
        if (resp && resp.access_token) {
          _gToken = resp.access_token;
          _gTokenExp = Date.now() + (num(resp.expires_in) || 3600) * 1000;
          _gFresh = true;
          resolve(_gToken);
        } else reject(new Error((resp && resp.error) || 'Google sign-in failed'));
      },
      error_callback: (err) => reject(new Error(err && err.type === 'popup_closed'
        ? 'the Google sign-in window was closed' : 'Google sign-in did not complete'))
    });
    // silent refresh once this device has connected before; full consent screen otherwise
    tc.requestAccessToken({ prompt: (!askConsent && state.settings.syncEmail) ? '' : 'consent' });
  }));
}

async function driveSync(force) {
  let token;
  try { token = await getDriveToken(false); }
  catch (e) { token = await getDriveToken(true); } // silent refresh failed → ask the user
  if (_gFresh) {
    // a newly issued token: make sure it is the SAME Google account this shop
    // backs up to, so data never lands in a different account's Drive
    const email = await fetchGoogleEmail(token);
    const expected = state.settings.syncEmail;
    if (email && expected && email !== expected) {
      _gToken = null;
      throw new Error('you chose ' + email + ' but this shop backs up to ' + expected + ' — please pick ' + expected);
    }
    if (email && !expected) { state.settings.syncEmail = email; persistQuiet(); updateSyncUI(); }
  }
  const fileId = await driveFileId(token);
  const remote = (fileId && force !== 'push') ? await driveDownload(token, fileId) : null;
  await applySyncDecision(remote, force, () => driveUpload(token, fileId), 'your Google Drive');
}

async function fetchGoogleEmail(token) {
  try {
    const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', { headers: { Authorization: 'Bearer ' + token } });
    if (res.ok) {
      const j = await res.json();
      return j.email || '';
    }
  } catch (e) {}
  return '';
}

async function driveFileId(token) {
  const q = encodeURIComponent("name='" + DRIVE_FILE_NAME + "' and trashed=false");
  const res = await fetch('https://www.googleapis.com/drive/v3/files?q=' + q + '&fields=files(id)&pageSize=1',
    { headers: { Authorization: 'Bearer ' + token } });
  if (!res.ok) throw new Error('Google Drive search failed (' + res.status + ')');
  const j = await res.json();
  return j.files && j.files[0] ? j.files[0].id : null;
}

async function driveDownload(token, fileId) {
  const res = await fetch('https://www.googleapis.com/drive/v3/files/' + fileId + '?alt=media',
    { headers: { Authorization: 'Bearer ' + token } });
  if (!res.ok) throw new Error('Google Drive download failed (' + res.status + ')');
  try { return JSON.parse(await res.text()); } catch (e) { return null; }
}

async function driveUpload(token, fileId) {
  const body = JSON.stringify(state);
  let res;
  if (fileId) {
    res = await fetch('https://www.googleapis.com/upload/drive/v3/files/' + fileId + '?uploadType=media', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' },
      body: body
    });
  } else {
    const meta = JSON.stringify({ name: DRIVE_FILE_NAME, mimeType: 'application/json' });
    const bnd = 'shopkeeper' + Date.now();
    res = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'multipart/related; boundary=' + bnd },
      body: '--' + bnd + '\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n' + meta +
        '\r\n--' + bnd + '\r\nContent-Type: application/json\r\n\r\n' + body + '\r\n--' + bnd + '--'
    });
  }
  if (!res.ok) throw new Error('Google Drive upload failed (' + res.status + ')');
}

/* ================= legacy: Apps Script web app link ================= */

async function sheetSync(force) {
  const s = state.settings;
  let remote = null;
  if (force !== 'push') {
    const res = await fetch(s.syncUrl, { method: 'GET' });
    if (!res.ok) throw new Error('server returned ' + res.status);
    try { remote = JSON.parse(await res.text()); } catch (e) { remote = null; }
  }
  await applySyncDecision(remote, force, pushStateToSheet, 'your Google Sheet');
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

/* ================= setup wizard ================= */

function syncStatusText(s) {
  if (activeClientId()) {
    return s.syncEmail
      ? 'Connected to Google Drive as <strong>' + esc(s.syncEmail) + '</strong>. Click 🔄 Sync (top right) on any device — same data everywhere.'
      : 'Setup saved. Click 🔄 Sync (top right) → <strong>Continue with Google</strong> → Allow to connect this device.';
  }
  if (s.syncUrl) {
    return 'Connected via Google Sheet link' + (s.syncEmail ? ' as <strong>' + esc(s.syncEmail) + '</strong>' : '') +
      '. Use the Sync button (top right) on any device with the same link.';
  }
  return 'Not set up. Sync backs up your data to <strong>your own Google Drive</strong> — sign in once with Google, then mobile and PC show the same data.';
}

function openSyncSetup() {
  const s = state.settings;
  const isFile = location.protocol === 'file:';
  const origin = isFile ? 'https://your-site.netlify.app' : location.origin;

  const ownerSection =
    '<div class="otp-note" style="text-align:left;margin:10px 0"><strong>👤 This page is only for the app owner — and only once.</strong><br>' +
    'Your staff and other devices will <strong>never</strong> see it. After this step they simply tap Sync → choose their Google email → Allow (like WhatsApp backup).</div>' +
    '<p class="sub" style="margin-top:6px"><strong>Why this step exists:</strong> Google shows the “Continue with Google” screen only for registered apps — ' +
    'WhatsApp registered theirs once as a company; here you register yours. It is all clicking on Google\'s website — no code:</p>' +
    '<ol style="padding-left:18px;line-height:1.9;font-size:13.5px">' +
    '<li>Open <strong>console.cloud.google.com</strong> and sign in with your Google email</li>' +
    '<li>Project list (top bar) → <strong>New project</strong> → name it <em>Shopkeeper</em> → Create → select it</li>' +
    '<li>Menu ☰ → <strong>APIs &amp; Services → Library</strong> → search <em>Google Drive API</em> → <strong>Enable</strong></li>' +
    '<li><strong>APIs &amp; Services → OAuth consent screen</strong> → External → app name <em>Shopkeeper</em> + your email → Save. Then under <strong>Test users</strong> click <em>+ Add users</em> and add your own Gmail</li>' +
    '<li><strong>APIs &amp; Services → Credentials → + Create credentials → OAuth client ID</strong> → type <strong>Web application</strong> → under <strong>Authorised JavaScript origins</strong> add:<br><code>' + esc(origin) + '</code> → Create</li>' +
    '<li>Copy the <strong>Client ID</strong> (ends with <code>.apps.googleusercontent.com</code>) and paste it below</li></ol>' +
    '<label>Google Client ID<input id="sy_cid" placeholder="1234….apps.googleusercontent.com" value="' + esc(s.gClientId || '') + '"></label>' +
    (s.gClientId ? '<div style="margin-top:8px"><button class="btn ghost" onclick="saveClientId()">Save Client ID</button></div>' : '');

  const advancedSection =
    '<details style="margin-top:14px"><summary style="cursor:pointer;font-weight:600;font-size:13px">Advanced: sync with a Google Apps Script link instead (works when opened as a file)</summary>' +
    '<ol style="padding-left:18px;line-height:1.9;font-size:13px">' +
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
    '<p class="sub" style="margin-top:8px">⚠ Keep the link private — anyone who has it can read your data.</p>' +
    '<div style="margin-top:8px"><button class="btn ghost" onclick="saveSyncSetup()">Save &amp; Sync Now</button></div>' +
    '</details>';

  let body =
    '<p class="sub">Your data backs up to <strong>your own Google Drive</strong>. Once set up, every device just clicks ' +
    '<strong>🔄 Sync → Continue with Google → Allow</strong> — same data everywhere. Sync needs internet; billing keeps working offline.</p>';

  if (isFile) {
    body += '<p class="sub" style="color:#d92027"><strong>⚠ Note:</strong> Google sign-in cannot open when the app is opened as a file from your computer. ' +
      'Use your website copy (e.g. your Netlify link) for Google Drive sync — or the “Advanced” option below, which works everywhere.</p>';
  }

  if (activeClientId()) {
    body +=
      '<div style="text-align:center;margin:16px 0"><button class="btn primary" style="font-size:15px;padding:12px 24px" onclick="closeModal();syncNow()">Continue with Google</button></div>';
    if (BUILT_IN_CLIENT_ID) {
      // this website copy already carries the registration — nothing else needed
      body += '<p class="sub" style="text-align:center">Every device that opens this website gets automatic Google sync — nothing to set up.</p>';
    } else {
      const link = (isFile ? '' : location.origin + location.pathname) + '#gcid=' + activeClientId();
      body +=
        '<p class="sub"><strong>Make it automatic for everyone:</strong> download your website file with Google built in, upload it to your site (e.g. Netlify) — then no device is ever asked for setup again:</p>' +
        '<div style="text-align:center;margin:8px 0"><button class="btn ghost" onclick="downloadConnectedSite()">⬇ Download connected website file (index.html)</button></div>' +
        '<p class="sub"><strong>Or on your phone:</strong> open this link once, then tap 🔄 Sync:</p>' +
        '<div style="display:flex;gap:6px;margin:6px 0"><input id="sy_link" readonly value="' + esc(link) + '" style="flex:1;font-size:11px">' +
        '<button class="btn tiny ghost" onclick="el(\'sy_link\').select();document.execCommand(\'copy\');toast(\'Link copied\')">Copy</button></div>';
    }
    body += '<details style="margin-top:10px"><summary style="cursor:pointer;font-weight:600;font-size:13px">Change Google registration (Client ID)</summary>' + ownerSection + '</details>';
  } else {
    body += ownerSection;
  }
  body += advancedSection;

  openModal(
    '<div class="modal-head"><h3>☁️ Sync with Google — one-time setup</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body">' + body + '</div>' +
    '<div class="modal-foot"><button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    (s.gClientId ? '' : '<button class="btn primary" onclick="saveClientId()">Save &amp; Continue with Google</button>') +
    '</div>',
    true
  );
}

/* Build a copy of this website file with the owner's Google registration baked
   in (like WhatsApp shipping its own registration inside the app). The owner
   uploads it to their site once; after that no device ever sees setup. */
async function downloadConnectedSite() {
  const cid = activeClientId();
  if (!cid) { toast('Save your Client ID first', 'error'); return; }
  if (BUILT_IN_CLIENT_ID === cid) { toast('This website copy already has Google built in'); return; }
  try {
    const res = await fetch(location.href.split('#')[0], { cache: 'no-store' });
    if (!res.ok) throw new Error('could not read the app file (' + res.status + ')');
    let src = await res.text();
    const needle = "BUILT_IN_CLIENT_ID = '" + "'";   // split so this line doesn't match itself
    if (src.indexOf(needle) < 0) throw new Error('app template marker not found');
    src = src.replace(needle, "BUILT_IN_CLIENT_ID = '" + cid + "'");
    downloadFile('index.html', src, 'text/html;charset=utf-8');
    toast('index.html downloaded — upload it to your website. Every device then syncs automatically.');
  } catch (e) {
    toast('Could not build the file: ' + e.message, 'error');
  }
}

function saveClientId() {
  const cid = el('sy_cid').value.trim();
  if (!/\.apps\.googleusercontent\.com$/.test(cid)) {
    toast('Paste the full Client ID — it ends with .apps.googleusercontent.com', 'error');
    return;
  }
  state.settings.gClientId = cid;
  persistQuiet();
  closeModal();
  updateSyncUI();
  syncNow(); // opens Google's "Continue with Google → Allow" window
}

function saveSyncSetup() {
  const url = el('sy_url').value.trim();
  const email = el('sy_email').value.trim();
  if (!url || !/^https?:\/\//.test(url)) { toast('Paste the Web App URL (starts with https://)', 'error'); return; }
  state.settings.syncUrl = url;
  state.settings.syncEmail = email;
  state.settings.gClientId = ''; // the link method takes over for this setup
  persistQuiet();
  closeModal();
  updateSyncUI();
  syncNow();
}

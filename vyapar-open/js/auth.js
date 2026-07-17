/* VyaparOpen — auth.js : WhatsApp-style login (mobile number + OTP) and the
   first-login "allow Google backup" step. Login is per-device and stored
   outside the synced state, like a SIM registration.

   Honest note: a real SMS needs a paid SMS gateway + server (this app has
   neither), so the OTP is generated on this device and shown on screen —
   it works like an app lock. Plugging in an SMS service later only needs
   sendOtp() to be pointed at it. */
'use strict';

const LOGIN_KEY = 'shopkeeper_login'; // device-local, never synced

let _otp = '', _otpPhone = '', _otpAt = 0;

function currentLogin() {
  try { return JSON.parse(localStorage.getItem(LOGIN_KEY) || 'null'); } catch (e) { return null; }
}

function isLoggedIn() {
  const l = currentLogin();
  return !!(l && l.phone);
}

function renderLogin() {
  document.body.classList.remove('modal-open');
  el('app').innerHTML =
    '<div class="login-wrap"><div class="login-card">' +
    '<div class="login-logo">S</div>' +
    '<h1 class="login-title">Shopkeeper</h1>' +
    '<p class="sub" style="margin-bottom:18px">Billing · Inventory · Khata — free &amp; works offline</p>' +
    '<label style="text-align:left">Mobile Number' +
    '<div class="login-phone"><span>+91</span>' +
    '<input id="lg_phone" inputmode="numeric" maxlength="10" placeholder="10-digit mobile number" autocomplete="tel"' +
    ' onkeydown="if(event.key===\'Enter\')sendOtp()"></div></label>' +
    '<button class="btn primary login-btn" onclick="sendOtp()">Get OTP</button>' +
    '<p class="sub" style="margin-top:14px">Your number stays on this device — no account, no server.</p>' +
    '</div></div>';
  const p = el('lg_phone');
  p.focus();
}

function sendOtp() {
  const phone = el('lg_phone') ? el('lg_phone').value.replace(/\D/g, '') : _otpPhone;
  if (!/^[6-9]\d{9}$/.test(phone)) { toast('Enter a valid 10-digit mobile number', 'error'); return; }
  _otpPhone = phone;
  _otp = String(Math.floor(100000 + Math.random() * 900000));
  _otpAt = Date.now();
  renderOtpStep();
}

function renderOtpStep() {
  el('app').innerHTML =
    '<div class="login-wrap"><div class="login-card">' +
    '<div class="login-logo">S</div>' +
    '<h1 class="login-title">Verify OTP</h1>' +
    '<p class="sub">OTP sent to <strong>+91 ' + esc(_otpPhone) + '</strong></p>' +
    '<div class="otp-note">Your OTP: <strong class="otp-code">' + esc(_otp) + '</strong>' +
    '<div class="sub" style="margin-top:4px">Shown here because no SMS service is connected — it works like an app lock. An SMS gateway can be added later.</div></div>' +
    '<label style="text-align:left">Enter OTP' +
    '<input id="lg_otp" inputmode="numeric" maxlength="6" placeholder="6-digit OTP" style="letter-spacing:6px;text-align:center;font-size:18px"' +
    ' onkeydown="if(event.key===\'Enter\')verifyOtp()"></label>' +
    '<button class="btn primary login-btn" onclick="verifyOtp()">Verify &amp; Login</button>' +
    '<div style="margin-top:12px;display:flex;justify-content:space-between">' +
    '<a class="login-link" onclick="renderLogin()">← Change number</a>' +
    '<a class="login-link" onclick="sendOtp()">Resend OTP</a></div>' +
    '</div></div>';
  el('lg_otp').focus();
}

function verifyOtp() {
  const v = el('lg_otp').value.trim();
  if (Date.now() - _otpAt > 5 * 60 * 1000) { toast('OTP expired — tap Resend OTP', 'error'); return; }
  if (v !== _otp) { toast('Wrong OTP — please check and try again', 'error'); return; }
  try { localStorage.setItem(LOGIN_KEY, JSON.stringify({ phone: _otpPhone, at: Date.now() })); } catch (e) {}
  // remember the shop's number on first ever login
  if (!state.settings.phone) { state.settings.phone = _otpPhone; persistQuiet(); }
  _otp = '';
  // WhatsApp-style: on first login, ask to allow Google backup before opening
  if (!state.settings.syncEmail && !state.settings.syncUrl) renderSyncAsk();
  else { bootApp(); syncNow(); } // already connected before → open and sync
}

function renderSyncAsk() {
  el('app').innerHTML =
    '<div class="login-wrap"><div class="login-card">' +
    '<div style="font-size:44px">☁️</div>' +
    '<h1 class="login-title">Back up to Google?</h1>' +
    '<p class="sub" style="margin:10px 0 18px">Allow Shopkeeper to save your data to <strong>your own Google account</strong> ' +
    '(like WhatsApp backup). Then your mobile and PC always show the same bills, stock and khata.</p>' +
    '<button class="btn primary login-btn" onclick="allowSyncSetup()">Continue with Google</button>' +
    '<button class="btn ghost login-btn" style="margin-top:10px" onclick="bootApp()">Not now — open the app</button>' +
    '<p class="sub" style="margin-top:14px">You can set this up any time from Settings or the 🔄 Sync button.</p>' +
    '</div></div>';
}

function allowSyncSetup() {
  bootApp();
  syncNow(); // built-in registration → Google's own account popup opens directly
}

function logout() {
  confirmDialog('Log out of this device? Your data stays saved here and in your Google backup.', () => {
    localStorage.removeItem(LOGIN_KEY);
    renderLogin();
  });
}

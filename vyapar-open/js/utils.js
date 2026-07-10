/* VyaparOpen — utils.js : formatting, DOM helpers, toasts, modals, CSV, SVG charts */
'use strict';

function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function num(v) {
  const n = parseFloat(v);
  return isNaN(n) ? 0 : n;
}

function round2(n) {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

/* Indian-style currency formatting: ₹ 1,23,456.78 */
function fmtMoney(n, withSymbol) {
  n = round2(num(n));
  const s = Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return (n < 0 ? '-' : '') + (withSymbol === false ? '' : '₹ ') + s;
}

function fmtQty(n) {
  n = num(n);
  return Number.isInteger(n) ? String(n) : n.toLocaleString('en-IN', { maximumFractionDigits: 3 });
}

function todayStr() {
  const d = new Date();
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function fmtDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return d + '/' + m + '/' + y;
}

function monthName(m) {
  return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m];
}

function addDays(iso, days) {
  const d = new Date(iso + 'T00:00:00');
  d.setDate(d.getDate() + days);
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function inRange(dateStr, from, to) {
  if (from && dateStr < from) return false;
  if (to && dateStr > to) return false;
  return true;
}

function el(id) { return document.getElementById(id); }

function h(html) {
  const t = document.createElement('template');
  t.innerHTML = html.trim();
  return t.content.firstChild;
}

/* ---------- toast ---------- */
let _toastTimer = null;
function toast(msg, kind) {
  let t = el('toast');
  if (!t) {
    t = h('<div id="toast"></div>');
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = 'show' + (kind === 'error' ? ' error' : '');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { t.className = ''; }, 2600);
}

/* ---------- modal ---------- */
function openModal(html, wide) {
  closeModal();
  const overlay = h(
    '<div class="modal-overlay" id="modalOverlay">' +
    '<div class="modal' + (wide ? ' modal-wide' : '') + '" role="dialog">' + html + '</div></div>'
  );
  overlay.addEventListener('mousedown', (e) => { if (e.target === overlay) closeModal(); });
  document.body.appendChild(overlay);
  document.body.classList.add('modal-open');
  const first = overlay.querySelector('input,select,textarea');
  if (first) setTimeout(() => first.focus(), 50);
}

function closeModal() {
  const o = el('modalOverlay');
  if (o) o.remove();
  document.body.classList.remove('modal-open');
}

document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

function confirmDialog(msg, onYes) {
  openModal(
    '<div class="modal-head"><h3>Please confirm</h3></div>' +
    '<div class="modal-body"><p>' + esc(msg) + '</p></div>' +
    '<div class="modal-foot">' +
    '<button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn danger" id="confirmYes">Delete</button></div>'
  );
  el('confirmYes').addEventListener('click', () => { closeModal(); onYes(); });
}

/* ---------- file download / CSV ---------- */
function downloadFile(name, content, mime) {
  const blob = new Blob([content], { type: mime || 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
}

function toCSV(rows) {
  return rows.map(r => r.map(c => {
    c = String(c == null ? '' : c);
    return /[",\n]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c;
  }).join(',')).join('\n');
}

function exportTableCSV(name, headers, rows) {
  downloadFile(name, toCSV([headers].concat(rows)), 'text/csv;charset=utf-8');
  toast('Exported ' + name);
}

/* ---------- SVG charts (no external libs) ----------
   Colors follow the app palette custom properties (see style.css):
   --series-1 for the single sales series; text uses ink tokens. */

function svgBarChart(data, opts) {
  // data: [{label, value}], opts: {height, valueFmt}
  const H = (opts && opts.height) || 220;
  const W = 720, padL = 56, padR = 12, padT = 14, padB = 30;
  const iw = W - padL - padR, ih = H - padT - padB;
  const max = Math.max(1, ...data.map(d => d.value));
  const step = iw / Math.max(1, data.length);
  const barW = Math.max(4, Math.min(34, step - 4));
  const fmt = (opts && opts.valueFmt) || (v => fmtMoney(v));
  let s = '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="Bar chart">';
  // gridlines (4 hairlines) + y labels
  for (let i = 0; i <= 4; i++) {
    const y = padT + ih - (ih * i / 4);
    const v = max * i / 4;
    s += '<line x1="' + padL + '" y1="' + y + '" x2="' + (W - padR) + '" y2="' + y + '" class="grid"/>';
    s += '<text x="' + (padL - 8) + '" y="' + (y + 4) + '" class="axis-label" text-anchor="end">' + shortMoney(v) + '</text>';
  }
  // bars
  data.forEach((d, i) => {
    const x = padL + i * step + (step - barW) / 2;
    const bh = Math.round(ih * d.value / max);
    const y = padT + ih - bh;
    s += '<g class="bar-g"><title>' + esc(d.label) + ': ' + esc(fmt(d.value)) + '</title>';
    if (d.value > 0) {
      s += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" rx="3" class="bar"/>';
    }
    s += '<rect x="' + (padL + i * step) + '" y="' + padT + '" width="' + step + '" height="' + ih + '" fill="transparent"/></g>';
    // x labels — show at most ~10
    const every = Math.ceil(data.length / 10);
    if (i % every === 0) {
      s += '<text x="' + (x + barW / 2) + '" y="' + (H - 8) + '" class="axis-label" text-anchor="middle">' + esc(d.label) + '</text>';
    }
  });
  s += '<line x1="' + padL + '" y1="' + (padT + ih) + '" x2="' + (W - padR) + '" y2="' + (padT + ih) + '" class="baseline"/>';
  s += '</svg>';
  return s;
}

function shortMoney(v) {
  v = num(v);
  if (Math.abs(v) >= 10000000) return (v / 10000000).toFixed(1).replace(/\.0$/, '') + 'Cr';
  if (Math.abs(v) >= 100000) return (v / 100000).toFixed(1).replace(/\.0$/, '') + 'L';
  if (Math.abs(v) >= 1000) return (v / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
  return String(Math.round(v));
}

/* number → words (Indian system) for invoice printing */
function amountInWords(n) {
  n = Math.round(num(n) * 100) / 100;
  const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve',
    'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  function two(x) { return x < 20 ? ones[x] : tens[Math.floor(x / 10)] + (x % 10 ? ' ' + ones[x % 10] : ''); }
  function words(x) {
    if (x === 0) return 'Zero';
    let out = '';
    if (x >= 10000000) { out += words(Math.floor(x / 10000000)) + ' Crore '; x %= 10000000; }
    if (x >= 100000) { out += two(Math.floor(x / 100000)) + ' Lakh '; x %= 100000; }
    if (x >= 1000) { out += two(Math.floor(x / 1000)) + ' Thousand '; x %= 1000; }
    if (x >= 100) { out += ones[Math.floor(x / 100)] + ' Hundred '; x %= 100; }
    if (x > 0) out += two(x) + ' ';
    return out.trim();
  }
  const rup = Math.floor(n), pai = Math.round((n - rup) * 100);
  let s = words(rup) + ' Rupees';
  if (pai > 0) s += ' and ' + words(pai) + ' Paise';
  return s + ' Only';
}

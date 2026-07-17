/* VyaparOpen — app.js : navigation + boot */
'use strict';

const NAV = [
  ['dashboard', '🏠', 'Dashboard'],
  ['billing', '🧾', 'Billing'],
  ['items', '📦', 'Inventory'],
  ['reports', '📊', 'Reports'],
  ['parties', '📒', 'Khata'],
  ['estimates', '📋', 'Estimates'],
  ['payments', '💰', 'Payments'],
  ['settings', '⚙️', 'Settings']
];

let currentPage = 'dashboard';

function go(page) {
  currentPage = page;
  window._txnSearch = '';
  location.hash = page;
  route();
}

function route() {
  closeModal();
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.page === currentPage));
  switch (currentPage) {
    case 'dashboard': renderDashboard(); break;
    case 'billing': renderBilling(); break;
    case 'parties': renderParties(); break;
    case 'items': renderItems(); break;
    case 'sales': currentPage = 'billing'; renderBilling(); break;
    case 'estimates': renderTxnList('estimates'); break;
    case 'purchases': renderTxnList('purchases'); break;
    case 'returns': renderTxnList('returns'); break;
    case 'payments': renderTxnList('payments'); break;
    case 'expenses': renderTxnList('expenses'); break;
    case 'reports': renderReports(); break;
    case 'settings': renderSettings(); break;
    default: renderDashboard();
  }
  const sb = el('sidebar');
  if (sb) sb.classList.remove('open');
}

function applyTheme() {
  document.documentElement.setAttribute('data-theme', state.settings.theme === 'dark' ? 'dark' : 'light');
}

function boot() {
  syncBootstrap(); // picks up a shared #gcid=… sync link on new devices
  if (!isLoggedIn()) { renderLogin(); return; }
  bootApp();
}

function bootApp() {
  const app = el('app');
  app.innerHTML =
    '<aside class="sidebar" id="sidebar">' +
    '<div class="brand"><div class="logo">S</div><div><div class="brand-name">Shopkeeper</div>' +
    '<div class="brand-biz" id="bizName">' + esc(state.settings.businessName) + '</div></div></div>' +
    '<nav>' + NAV.map(n =>
      '<a class="nav-item" data-page="' + n[0] + '" onclick="go(\'' + n[0] + '\')"><span class="ico">' + n[1] + '</span>' + n[2] + '</a>'
    ).join('') + '</nav>' +
    '<div class="sidebar-foot">Free &amp; open source<br>Data stays on your device</div>' +
    '</aside>' +
    '<div class="main"><header class="topbar">' +
    '<button class="hamburger" onclick="el(\'sidebar\').classList.toggle(\'open\')">☰</button>' +
    '<div class="topbar-title">Shopkeeper</div>' +
    '<span class="sub" id="syncInfo"></span>' +
    '<button class="btn tiny wa" id="syncBtn" onclick="syncNow()">🔄 Sync</button>' +
    '<button class="btn ghost tiny" onclick="exportBackup()">⬇ Backup</button>' +
    '</header><main id="view"></main></div>';

  applyTheme();
  updateSyncUI();
  const hash = location.hash.replace('#', '');
  if (NAV.some(n => n[0] === hash)) currentPage = hash;
  route();

  window.addEventListener('hashchange', () => {
    const p = location.hash.replace('#', '');
    if (NAV.some(n => n[0] === p) && p !== currentPage) { currentPage = p; route(); }
  });

  // keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.altKey && !e.ctrlKey && !e.metaKey) {
      if (e.key === 'n') { e.preventDefault(); go('billing'); }
      if (e.key === 'p') { e.preventDefault(); openTxnForm('PURCHASE'); }
    }
  });
}

document.addEventListener('DOMContentLoaded', boot);

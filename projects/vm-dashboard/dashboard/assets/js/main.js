// main.js — YNAI5 v0.3.0 ES Module Entry Point
// Imports and initialises all modules after auth gate passes

import { initTheme }          from './theme.js';
import { initMetrics, fetchStatus } from './metrics.js';
import { initChat }           from './chat.js';
import { getConfig }          from './secrets.js';
import { renderAgentCards }   from './agents.js';

// ── Auth Gate ──
// crypto.subtle requires HTTPS — VM runs HTTP, so use direct comparison
const ACCESS_CODE = 'YNAI5123';

function checkAuth() {
  if (sessionStorage.getItem('ynai5-auth') === '1') return true;
  const pwd = prompt('YNAI5 Control Center\nAccess Code:');
  if (!pwd) return false;
  if (pwd.trim() === ACCESS_CODE) {
    sessionStorage.setItem('ynai5-auth', '1');
    return true;
  }
  alert('Wrong access code. Try again.');
  return false;
}

// ── Tab System ──
function initTabs() {
  const tabBtns   = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      tabBtns.forEach(b   => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${target}`)?.classList.add('active');
    });
  });
}

// ── Log Sub-tabs ──
function initLogTabs() {
  const logBtns = document.querySelectorAll('.log-tab-btn');
  const logViews = document.querySelectorAll('.log-view');

  logBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.log;
      logBtns.forEach(b  => b.classList.remove('active'));
      logViews.forEach(v => v.classList.add('hidden'));
      btn.classList.add('active');
      const el = document.getElementById(`log-${target}`);
      if (el) el.classList.remove('hidden');
    });
  });
}

// ── Kill Switch ──
function initKillSwitch() {
  const btn = document.getElementById('kill-switch-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    if (!confirm('Stop all YNAI5 services? This will halt Docker + Flask.')) return;
    try {
      const res = await fetch('/api/kill', { method: 'POST' });
      const data = await res.json();
      alert(data.message || 'Kill signal sent.');
    } catch {
      alert('Kill endpoint not available — SSH to VM to stop services manually.');
    }
  });
}

// ── Nav highlight ──
function initNav() {
  const items = document.querySelectorAll('.nav-item[data-tab]');
  items.forEach(item => {
    item.addEventListener('click', () => {
      items.forEach(i => i.classList.remove('active'));
      item.classList.add('active');
      // Sync with tab system
      const tabBtn = document.querySelector(`.tab-btn[data-tab="${item.dataset.tab}"]`);
      if (tabBtn) tabBtn.click();
    });
  });
}

// ── Boot ──
async function boot() {
  const authed = checkAuth();
  if (!authed) {
    document.body.innerHTML = '<div style="display:grid;place-items:center;height:100vh;font-family:monospace;color:#666">Access denied. Reload to retry.</div>';
    return;
  }

  // Show app shell — must explicitly set display:grid (CSS sets display:none)
  const app = document.getElementById('app');
  if (app) {
    app.style.display = 'grid';
    app.removeAttribute('hidden');
  }
  document.getElementById('auth-gate')?.remove();

  // Init all modules
  initTheme();
  initTabs();
  initLogTabs();
  initKillSwitch();
  initNav();
  initChat();
  initMetrics();

  // Load safe config for display
  const cfg = await getConfig();
  const vEl = document.getElementById('version-tag');
  if (vEl) vEl.textContent = `v${cfg.version || '0.3.0'}`;

  // Render agent cards on overview tab
  renderAgentCards('agents-grid');

  console.log('[YNAI5] v0.3.0 booted — VM:', cfg.vm_hostname);
}

boot();

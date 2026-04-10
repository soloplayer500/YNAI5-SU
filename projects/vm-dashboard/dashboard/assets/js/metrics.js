// metrics.js — YNAI5 v0.3.0
// Polls status.json every 30s, renders metric cards, status board, and service logs

const REFRESH_MS = 30_000;
let _interval = null;

export function initMetrics() {
  fetchStatus();
  _interval = setInterval(fetchStatus, REFRESH_MS);
}

export async function fetchStatus() {
  try {
    const res = await fetch(`/status.json?t=${Date.now()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderSystemMetrics(data.system || {});
    renderStatusBoard(data.checks || {}, data.summary || '');
    renderServiceLogs(data.service_logs || {});
    renderBudget(data.billing || {});
    updateRefreshTime();
  } catch (e) {
    console.warn('[metrics] status.json fetch failed:', e.message);
    setEl('status-summary', '⚠️ Could not load status.json — VM connection issue?');
  }
}

function renderSystemMetrics(sys) {
  setEl('metric-ram',    sys.ram_used_mb   != null ? `${sys.ram_used_mb} MB`   : '--');
  setEl('metric-cpu',    sys.cpu_pct       != null ? `${sys.cpu_pct}%`         : '--');
  setEl('metric-disk',   sys.disk_used_pct != null ? `${sys.disk_used_pct}%`   : '--');
  setEl('metric-uptime', sys.uptime        || '--');

  // Color RAM metric by usage
  const ramEl = document.getElementById('metric-ram');
  if (ramEl && sys.ram_used_mb) {
    ramEl.className = 'metric-value ' + (
      sys.ram_used_mb > 800 ? 'red' :
      sys.ram_used_mb > 600 ? 'yellow' : ''
    );
  }
}

export function renderStatusBoard(checks, summary) {
  const grid = document.getElementById('status-grid');
  if (!grid) return;

  grid.innerHTML = '';
  const entries = Object.entries(checks);
  if (entries.length === 0) {
    grid.innerHTML = '<div style="color:var(--color-muted);font-size:0.8rem">No check data yet — status_writer.py running?</div>';
    return;
  }

  for (const [svc, info] of entries) {
    const ok   = info.status === 'ok';
    const warn = info.status === 'warn';
    const cls  = ok ? 'ok' : warn ? 'warn' : 'err';
    const icon = ok ? '✅' : warn ? '⚠️' : '❌';

    const card = document.createElement('div');
    card.className = `service-card ${cls}`;
    card.innerHTML = `
      <div class="service-icon">${icon}</div>
      <div class="service-name">${svc}</div>
      <div class="service-detail">${getDetailText(info)}</div>`;
    grid.appendChild(card);
  }

  setEl('status-summary', summary || `${entries.filter(([,v]) => v.status === 'ok').length}/${entries.length} operational`);
}

function renderServiceLogs(logs) {
  for (const [svc, lines] of Object.entries(logs)) {
    const el = document.getElementById(`log-${svc}`);
    if (el) el.textContent = Array.isArray(lines) ? lines.join('\n') : String(lines);
  }

  // Populate 'all' log tab with everything
  const allEl = document.getElementById('log-all');
  if (allEl) {
    const allLines = Object.entries(logs)
      .map(([svc, lines]) => `=== ${svc.toUpperCase()} ===\n${Array.isArray(lines) ? lines.join('\n') : lines}`)
      .join('\n\n');
    allEl.textContent = allLines || 'No log data yet.';
  }
}

function renderBudget(billing) {
  if (!billing.daily_usd) return;
  setEl('metric-budget', `$${billing.daily_usd.toFixed(2)} / $5.00`);
  const pct = (billing.daily_usd / 5) * 100;
  const fill = document.getElementById('budget-bar-fill');
  if (fill) {
    fill.style.width = `${Math.min(pct, 100)}%`;
    fill.className = 'usage-bar-fill' + (pct > 80 ? ' danger' : pct > 60 ? ' warn' : '');
  }
}

function updateRefreshTime() {
  const el = document.getElementById('last-refresh');
  if (el) {
    el.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
}

function getDetailText(info) {
  if (info.http       != null)       return `HTTP ${info.http}`;
  if (info.key_set    != null)       return info.key_set ? 'key set ✓' : '⚠ KEY MISSING';
  if (info.job_count  != null)       return `${info.job_count} jobs`;
  if (info.file_age_min != null)     return `${info.file_age_min}m ago`;
  if (info.last_commit_h != null)    return `commit ${info.last_commit_h}h ago`;
  return info.status || '--';
}

function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

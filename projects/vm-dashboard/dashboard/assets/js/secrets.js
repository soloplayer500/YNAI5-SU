// secrets.js — YNAI5 v0.3.0
// Fetches safe VM config from Flask /api/env
// NEVER returns API keys — server-side only

let _config = null;

export async function getConfig() {
  if (_config) return _config;
  try {
    const res = await fetch('/api/env');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _config = await res.json();
  } catch (e) {
    console.warn('[secrets] /api/env failed, using defaults:', e.message);
    _config = {
      vm_hostname: 'ynai5-vm',
      budget_daily_usd: 5,
      budget_daily_awg: 8.95,
      gemini_configured: false,
      brave_configured: false,
      telegram_configured: false,
      version: '0.3.0',
    };
  }
  return _config;
}

export async function hasGeminiKey() {
  const cfg = await getConfig();
  return cfg.gemini_configured === true;
}

export async function hasBraveKey() {
  const cfg = await getConfig();
  return cfg.brave_configured === true;
}

export async function getVersion() {
  const cfg = await getConfig();
  return cfg.version || '0.3.0';
}

export async function getBudget() {
  const cfg = await getConfig();
  return {
    daily_usd: cfg.budget_daily_usd || 5,
    daily_awg: cfg.budget_daily_awg || 8.95,
  };
}

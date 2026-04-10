// router.js — YNAI5 v0.3.0
// Model routing display logic (client-side label only)
// ALL actual AI calls go through POST /api/chat → Flask backend (keys server-side)
// Ollama REMOVED — not running (958MB RAM lean mode)

export const MODEL_PRIORITY = [
  {
    id: 'gemini-flash-lite',
    name: 'Gemini Flash',
    provider: 'Google',
    free: true,
    daily_limit: 1500,
    endpoint: '/api/chat',
    rank: 1,
  },
  {
    id: 'kimi-k2.5',
    name: 'Kimi K2.5',
    provider: 'Moonshot (OpenRouter)',
    free: false,
    cost_per_call: 0.0002,
    endpoint: '/api/chat',
    rank: 2,
  },
  {
    id: 'claude-haiku',
    name: 'Claude Haiku',
    provider: 'Anthropic',
    free: false,
    cost_per_call: 0.0005,
    endpoint: '/api/chat',
    rank: 3,
  },
];

/**
 * Get the active model label based on config.
 * Actual routing is done by Flask backend — this is for display only.
 */
export function getActiveModel(config = {}) {
  if (config.gemini_configured) return MODEL_PRIORITY[0];
  return MODEL_PRIORITY[2]; // fallback display label
}

/**
 * Format a model ID into a display badge string.
 */
export function formatModelBadge(modelId) {
  if (!modelId) return '[AI]';
  const m = MODEL_PRIORITY.find(m => m.id === modelId);
  return m ? `[${m.name}]` : `[${modelId}]`;
}

/**
 * Get model display name.
 */
export function getModelName(modelId) {
  const m = MODEL_PRIORITY.find(m => m.id === modelId);
  return m ? m.name : modelId;
}

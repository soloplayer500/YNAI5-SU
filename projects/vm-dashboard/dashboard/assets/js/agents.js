// agents.js — YNAI5 v0.3.0
// Agent definitions + dispatcher
// All agents route through /api/chat backend (no direct browser API calls)
// Ollama REMOVED — not available on lean VM (958MB RAM)

export const AGENTS = {
  orchestrator: {
    id:          'orchestrator',
    name:        'YNAI5 Orchestrator',
    description: 'General purpose — Lyra 5-layer prompt, Gemini Flash Lite',
    model:       'gemini-flash-lite',
    icon:        '🧠',
    endpoint:    '/api/chat',
  },
  searcher: {
    id:          'searcher',
    name:        'SearXNG Search',
    description: 'Web search via self-hosted SearXNG on port 8080',
    model:       'searxng',
    icon:        '🔍',
    endpoint:    '/api/chat',
  },
  analyst: {
    id:          'analyst',
    name:        'Content Analyst',
    description: 'Script/trend analysis — Gemini Flash Lite',
    model:       'gemini-flash-lite',
    icon:        '📊',
    endpoint:    '/api/chat',
  },
};

/**
 * Dispatch a message to a named agent via the Flask backend.
 * Returns the fetch Promise (caller handles response).
 */
export function dispatchAgent(agentId, message) {
  const agent = AGENTS[agentId] || AGENTS.orchestrator;
  return fetch(agent.endpoint, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ message, agent: agentId }),
  });
}

/**
 * Render agent cards into a container element.
 */
export function renderAgentCards(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';
  for (const agent of Object.values(AGENTS)) {
    const card = document.createElement('div');
    card.className = 'card agent-card';
    card.innerHTML = `
      <div style="font-size:1.5rem">${agent.icon}</div>
      <div style="font-weight:600;font-size:0.85rem">${agent.name}</div>
      <div style="font-size:0.75rem;color:var(--color-muted)">${agent.description}</div>
      <div class="badge badge-cyan" style="margin-top:4px">${agent.model}</div>`;
    container.appendChild(card);
  }
}

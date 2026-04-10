// chat.js — YNAI5 v0.3.0
// Chat tab UI — all messages POST to /api/chat Flask backend
// No direct LLM calls from browser (keys stay server-side)

import { formatModelBadge } from './router.js';

let thread, input, sendBtn;

export function initChat() {
  thread  = document.getElementById('chat-thread');
  input   = document.getElementById('chat-input');
  sendBtn = document.getElementById('chat-send');

  if (!thread || !input || !sendBtn) return;

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
  });

  // Show welcome message
  appendWelcome();
}

function appendWelcome() {
  if (!thread) return;
  const el = document.createElement('div');
  el.className = 'chat-welcome';
  el.innerHTML = `
    <div class="logo">YNAI5</div>
    <div>Lyra-powered AI assistant</div>
    <div style="margin-top:8px;font-size:0.75rem;color:var(--color-muted-2)">
      Powered by Gemini Flash Lite · SearXNG search available
    </div>`;
  thread.appendChild(el);
}

function appendMsg(role, text, modelId = null) {
  if (!thread) return;
  // Remove welcome on first real message
  const welcome = thread.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  const el = document.createElement('div');
  el.className = `msg msg-${role}`;
  const ts = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  el.innerHTML = `
    <div class="msg-body">${escHtml(text)}</div>
    <div class="msg-meta">
      ${modelId ? `<span class="model-badge">${formatModelBadge(modelId)}</span>` : ''}
      <span class="msg-ts">${ts}</span>
    </div>`;

  thread.appendChild(el);
  thread.scrollTop = thread.scrollHeight;
  return el;
}

function showTyping() {
  if (!thread) return;
  const existing = document.getElementById('typing-indicator');
  if (existing) return;
  const el = document.createElement('div');
  el.id = 'typing-indicator';
  el.className = 'msg msg-ai';
  el.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  thread.appendChild(el);
  thread.scrollTop = thread.scrollHeight;
}

function hideTyping() {
  document.getElementById('typing-indicator')?.remove();
}

function setLoading(loading) {
  if (sendBtn) sendBtn.disabled = loading;
  if (input)   input.disabled   = loading;
}

async function sendMessage() {
  if (!input) return;
  const msg = input.value.trim();
  if (!msg) return;

  input.value = '';
  input.style.height = 'auto';
  appendMsg('user', msg);
  showTyping();
  setLoading(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    });

    const data = await res.json();
    hideTyping();

    if (res.ok) {
      appendMsg('ai', data.reply || 'No response from server.', data.model_used);
    } else {
      appendMsg('ai', `⚠️ Error: ${data.error || res.statusText}`);
    }
  } catch (err) {
    hideTyping();
    appendMsg('ai', `⚠️ Connection error: ${err.message}\n\nMake sure the VM chat server is running.`);
  } finally {
    setLoading(false);
    input.focus();
  }
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

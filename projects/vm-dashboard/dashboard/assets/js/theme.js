// theme.js — YNAI5 v0.3.0
// Dark/light theme toggle with localStorage persistence

const STORAGE_KEY = 'ynai5-theme';
const DEFAULT     = 'dark';

export function initTheme() {
  const saved = localStorage.getItem(STORAGE_KEY) || DEFAULT;
  applyTheme(saved);

  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', toggleTheme);
    btn.title = 'Toggle light/dark mode';
  }
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || DEFAULT;
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(STORAGE_KEY, theme);

  // Update toggle icon
  const sun  = document.getElementById('icon-sun');
  const moon = document.getElementById('icon-moon');
  if (sun)  sun.style.display  = theme === 'dark'  ? 'block' : 'none';
  if (moon) moon.style.display = theme === 'light' ? 'block' : 'none';
}

export function getTheme() {
  return document.documentElement.getAttribute('data-theme') || DEFAULT;
}

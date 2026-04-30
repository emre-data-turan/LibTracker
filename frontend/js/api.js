// ── API Client & Token Management ─────────────────────────
import { API } from './config.js';

let _token = localStorage.getItem('lt_token') || null;
let _onAuthExpired = null;

export function getToken()  { return _token; }
export function getUserId() { return localStorage.getItem('lt_user_id'); }

export function setToken(token, userId) {
  _token = token;
  localStorage.setItem('lt_token', token);
  if (userId) localStorage.setItem('lt_user_id', userId);
}

export function clearToken() {
  _token = null;
  localStorage.removeItem('lt_token');
  localStorage.removeItem('lt_user_id');
}

/** Register a callback to run when a 401 (expired token) is detected. */
export function onAuthExpired(callback) {
  _onAuthExpired = callback;
}

/**
 * Fetch wrapper that automatically adds auth headers and handles 401s.
 * Returns the Response object, or null on network error.
 */
export async function apiFetch(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (_token) headers['Authorization'] = 'Bearer ' + _token;
  try {
    const r = await fetch(API + path, { ...opts, headers });
    if (r.status === 401 && path !== '/auth/login' && path !== '/auth/register') {
      clearToken();
      if (_onAuthExpired) _onAuthExpired();
    }
    return r;
  } catch {
    return null;
  }
}

// ── Authentication Module ─────────────────────────────────
import { apiFetch, getToken, setToken, clearToken } from './api.js';
import { showToast } from './utils.js';

/** Updates the nav auth button and profile button visibility. */
export function updateAuthUI() {
  const btn = document.getElementById('authBtn');
  const profBtn = document.getElementById('profileBtn');
  if (getToken()) {
    btn.textContent = 'Logout';
    btn.onclick = logout;
    if (profBtn) profBtn.style.display = 'inline-flex';
  } else {
    btn.textContent = 'Login / Register';
    btn.onclick = () => openAuthModal();
    if (profBtn) profBtn.style.display = 'none';
  }
}

export function openAuthModal() {
  document.getElementById('authModal').classList.add('active');
}

export function closeModal() {
  document.getElementById('authModal').classList.remove('active');
}

export function showProfileModal() {
  document.getElementById('profileModal').classList.add('active');
}

export async function doRegister() {
  const name  = document.getElementById('inp-name').value.trim();
  const email = document.getElementById('inp-email').value.trim();
  const pass  = document.getElementById('inp-pass').value;
  const r = await apiFetch('/auth/register', { method: 'POST', body: JSON.stringify({ name, email, password: pass }) });
  if (!r) { showToast('Unable to reach server', '⚠️'); return; }
  const data = await r.json();
  if (r.ok) {
    setToken(data.token, data.user.id);
    closeModal();
    updateAuthUI();
    showToast('Registration successful!', '✅');
    window.dispatchEvent(new Event('auth-changed'));
  } else {
    showToast(data.error || 'Error', '❌');
  }
}

export async function doLogin() {
  const email = document.getElementById('inp-email').value.trim();
  const pass  = document.getElementById('inp-pass').value;
  const r = await apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ email, password: pass }) });
  if (!r) { showToast('Unable to reach server', '⚠️'); return; }
  const data = await r.json();
  if (r.ok) {
    setToken(data.token, data.user.id);
    closeModal();
    updateAuthUI();
    showToast('Login successful!', '✅');
    window.dispatchEvent(new Event('auth-changed'));
  } else {
    showToast(data.error || 'Error', '❌');
  }
}

export async function logout() {
  await apiFetch('/auth/logout', { method: 'POST' });
  clearToken();
  updateAuthUI();
  showToast('Logged out');
  document.getElementById('resList').innerHTML =
    '<li style="color:var(--muted);padding:1rem">Please log in to see your reservations.</li>';
}

export async function updatePassword() {
  const old_password = document.getElementById('inp-old-pass').value;
  const new_password = document.getElementById('inp-new-pass').value;
  const r = await apiFetch('/auth/me/password', { method: 'PUT', body: JSON.stringify({ old_password, new_password }) });
  if (!r) { showToast('Network Error', '❌'); return; }
  const data = await r.json();
  if (r.ok) {
    showToast('Password updated!', '✅');
    document.getElementById('inp-old-pass').value = '';
    document.getElementById('inp-new-pass').value = '';
    document.getElementById('profileModal').classList.remove('active');
  } else {
    showToast(data.error || 'Error', '❌');
  }
}

export async function deleteAccount() {
  if (!confirm("Are you sure you want to permanently delete your account?")) return;
  const r = await apiFetch('/auth/me', { method: 'DELETE' });
  if (!r) { showToast('Network Error', '❌'); return; }
  if (r.ok) {
    showToast('Account deleted', '✅');
    document.getElementById('profileModal').classList.remove('active');
    logout();
  } else {
    const data = await r.json();
    showToast(data.error || 'Session Expired', '❌');
    if (r.status === 401) logout();
  }
}

/** Switches between Login and Register tabs in the auth modal. */
export function switchModalTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('modal-name-row').style.display = isLogin ? 'none' : 'block';
  const submitBtn = document.getElementById('modal-submit-btn');
  submitBtn.textContent = isLogin ? 'Login' : 'Create Account';
  submitBtn.onclick = isLogin ? doLogin : doRegister;

  document.querySelectorAll('.modal-tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById(`modal-tab-${tab}`).classList.add('active');
}

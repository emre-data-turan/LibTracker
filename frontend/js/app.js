// ── Main App Entry Point ──────────────────────────────────
import { onAuthExpired, apiFetch, getToken } from './api.js';
import { updateAuthUI, openAuthModal, closeModal, showProfileModal, doLogin, doRegister, switchModalTab, updatePassword, deleteAccount } from './auth.js';
import { loadLibraries, initCharts, apiLibraries } from './dashboard.js';
import { updateStudyAreas, fetchTakenSeats, renderSeatMap, makeReservation, loadUserReservations } from './reservation.js';
import { loadFeedback, submitFeedback, initFeedbackBadge } from './feedback.js';

// ── Expose required functions globally (for dynamic onclick in HTML) ──
window._goToReserve = goToReserve;
window._showProfileModal = showProfileModal;
window._makeReservation = makeReservation;
window._submitFeedback = submitFeedback;
window._doLogin = doLogin;
window._doRegister = doRegister;
window._switchModalTab = switchModalTab;
window._updatePassword = updatePassword;
window._deleteAccount = deleteAccount;
window._closeModal = closeModal;
window._navigateDashboard = navigateDashboard;

// ── Page Navigation ───────────────────────────────────────
function showPage(id, tabEl) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById(id);
  if (page) page.classList.add('active');

  document.querySelectorAll('.nav-tab[data-page]').forEach(b => b.classList.remove('active'));
  if (tabEl) tabEl.classList.add('active');

  if (id === 'feedback') {
    const fbLib = document.getElementById('fb-library');
    if (fbLib && fbLib.value) loadFeedback(fbLib.value);
  }
  if (id === 'reserve' && getToken()) loadUserReservations();
}

function goToReserve(libId) {
  if (!getToken()) { openAuthModal(); return; }
  const tab = document.querySelector('.nav-tab[data-page="reserve"]');
  showPage('reserve', tab);
  const sel = document.getElementById('res-library');
  if (sel) { sel.value = libId; updateStudyAreas(); }
}

function navigateDashboard() {
  const tab = document.querySelector('.nav-tab[data-page="dashboard"]');
  showPage('dashboard', tab);
}

// ── Wire up auth expiry callback ──────────────────────────
onAuthExpired(() => updateAuthUI());

// ── Auth state change handler (reload data after login) ───
window.addEventListener('auth-changed', async () => {
  const meR = await apiFetch('/auth/me');
  if (meR && meR.ok) {
    const meData = await meR.json();
    localStorage.setItem('lt_user_id', meData.user.id);
    loadUserReservations();
  }
});

// ── DOMContentLoaded ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Nav tab click handlers
  document.querySelectorAll('.nav-tab[data-page]').forEach(btn => {
    btn.addEventListener('click', function () { showPage(this.dataset.page, this); });
  });

  // Library select → update study areas
  const resLib = document.getElementById('res-library');
  if (resLib) resLib.addEventListener('change', updateStudyAreas);

  // Pre-fill reservation date/time so the map isn't blank
  const now = new Date();
  now.setMinutes(now.getMinutes() + 5); // Add 5 mins buffer to prevent 'past time' error on submit
  
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const dateStr = `${yyyy}-${mm}-${dd}`;
  
  const startStr = now.toTimeString().substring(0, 5);
  now.setHours(now.getHours() + 2);
  const endStr = now.toTimeString().substring(0, 5);
  
  const dEl = document.getElementById('res-date');
  if (dEl && !dEl.value) dEl.value = dateStr;
  const sEl = document.getElementById('res-start');
  if (sEl && !sEl.value) sEl.value = startStr;
  const eEl = document.getElementById('res-end');
  if (eEl && !eEl.value) eEl.value = endStr;

  // Area select + time changes → update seat map
  ['res-area', 'res-date', 'res-start', 'res-end'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', fetchTakenSeats);
  });

  // Feedback library select → load feedback
  const fbLib = document.getElementById('fb-library');
  if (fbLib) fbLib.addEventListener('change', () => loadFeedback(fbLib.value));

  // Close modals on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.classList.remove('active');
    });
  });

  // Initial render
  renderSeatMap();
  updateAuthUI();
  await loadLibraries();
  await initCharts();
  await initFeedbackBadge(apiLibraries);

  // Restore session
  if (getToken()) {
    const meR = await apiFetch('/auth/me');
    if (meR && meR.ok) {
      const meData = await meR.json();
      localStorage.setItem('lt_user_id', meData.user.id);
      loadUserReservations();
    } else {
      updateAuthUI();
    }
  }
});

// ── Utility Functions ─────────────────────────────────────

/** Escapes HTML special characters to prevent XSS. */
export function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/** Shows a toast notification at the bottom-right corner. */
let toastTimer;
export function showToast(msg, icon = '') {
  const t = document.getElementById('toast');
  t.textContent = (icon ? icon + '  ' : '') + msg;
  t.className = 'toast success show';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3500);
}

/** Returns a human-readable "X ago" string from an ISO date. */
export function timeSince(isoStr) {
  const diff = (Date.now() - new Date(isoStr)) / 1000;
  if (diff < 60)   return Math.round(diff) + 's ago';
  if (diff < 3600) return Math.round(diff / 60) + 'm ago';
  return Math.round(diff / 3600) + 'h ago';
}

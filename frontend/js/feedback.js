// ── Feedback Module ───────────────────────────────────────
import { apiFetch, getToken } from './api.js';
import { escapeHtml, showToast, timeSince } from './utils.js';

/** Loads feedback for a specific library and renders the feed list. */
export async function loadFeedback(libraryId) {
  const r = await apiFetch(`/feedback/${libraryId}`);
  if (!r || !r.ok) return;
  const data = await r.json();
  const list = document.getElementById('feedList');
  list.innerHTML = data.feedbacks.map(f => {
    const pct = f.reported_occupancy;
    const tag = pct < 40 ? 'quiet' : pct < 75 ? 'loud' : 'full';
    const label = pct < 40 ? 'Quiet' : pct < 75 ? 'Moderate' : 'Busy';
    const ago = timeSince(f.created_at);
    const userName = escapeHtml(f.user_name || 'Anonymous');
    const initial = (f.user_name || '?')[0];
    const commentHtml = f.comment ? `<div class="feed-text">"${escapeHtml(f.comment)}"</div>` : '';
    return `
    <li class="feed-item">
      <div class="feed-avatar">${escapeHtml(initial)}</div>
      <div class="feed-body">
        <div><span class="feed-user">${userName}</span>
          <span class="feed-tag tag-${tag}">${label} &middot; ${pct}%</span></div>
        ${commentHtml}
        <div class="feed-time">${ago}</div>
      </div>
    </li>`;
  }).join('') || '<li style="color:var(--muted);padding:1rem">No feedback yet.</li>';
}

/** Submits feedback for the selected library. */
export async function submitFeedback() {
  if (!getToken()) { showToast('Please log in first', '⚠️'); return; }
  const library_id = parseInt(document.getElementById('fb-library').value);
  const reported_occupancy = parseInt(document.getElementById('fb-occupancy').value);
  const comment = document.getElementById('fb-comment').value;

  const r = await apiFetch('/feedback/', {
    method: 'POST',
    body: JSON.stringify({ library_id, reported_occupancy, comment })
  });
  if (!r) { showToast('Network error', '❌'); return; }
  const data = await r.json();
  if (r.ok) {
    document.getElementById('fb-comment').value = '';
    showToast('Feedback submitted!', '✅');
    loadFeedback(library_id);
    // Update badge from actual count
    const fbR = await apiFetch(`/feedback/${library_id}`);
    if (fbR && fbR.ok) {
      const fbData = await fbR.json();
      document.getElementById('feedCount').textContent = fbData.count;
    }
  } else {
    showToast(data.error || 'Error', '❌');
  }
}

/** Initializes the feedback badge count from the API. */
export async function initFeedbackBadge(libraries) {
  if (libraries.length) {
    const r = await apiFetch(`/feedback/${libraries[0].id}`);
    if (r && r.ok) {
      const data = await r.json();
      document.getElementById('feedCount').textContent = data.count;
    }
  }
}

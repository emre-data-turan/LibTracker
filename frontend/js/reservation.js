// ── Reservation Module ────────────────────────────────────
import { apiFetch, getToken, getUserId } from './api.js';
import { escapeHtml, showToast } from './utils.js';
import { apiLibraries, loadLibraries } from './dashboard.js';

let selectedSeat = null;
let currentTotalSeats = 0;
let currentTakenSeats = [];

/** Loads study areas for the selected library into the area dropdown. */
export async function updateStudyAreas() {
  const libId = document.getElementById('res-library')?.value;
  if (!libId) return;
  const lib = apiLibraries.find(l => l.id == libId);
  const sel = document.getElementById('res-area');
  if (!sel || !lib || !lib.study_areas) return;
  
  const currentVal = sel.value;
  sel.innerHTML = lib.study_areas.map(a =>
    `<option value="${a.id}">${escapeHtml(a.name)}</option>`
  ).join('');
  
  if (currentVal && lib.study_areas.find(a => a.id == currentVal)) {
    sel.value = currentVal;
  }
  sel.dispatchEvent(new Event('change'));
}

/** Fetches which seats are taken for the selected area and renders the seat map. */
export async function fetchTakenSeats() {
  const areaId = document.getElementById('res-area')?.value;
  if (!areaId) return;

  const start = document.getElementById('res-start')?.value;
  const end   = document.getElementById('res-end')?.value;
  const date  = document.getElementById('res-date')?.value;

  const lib = apiLibraries.find(l => l.id == document.getElementById('res-library')?.value);
  const area = lib?.study_areas?.find(a => a.id == areaId);
  currentTotalSeats = area ? area.total_seats : 20;
  currentTakenSeats = [];

  if (date && start && end) {
    const sISO = new Date(`${date}T${start}`).toISOString();
    const eISO = new Date(`${date}T${end}`).toISOString();
    const r = await apiFetch(`/reservations/area/${areaId}/seats?start_time=${sISO}&end_time=${eISO}`);
    if (r && r.ok) {
      const data = await r.json();
      currentTakenSeats = data.taken_seats || [];
    }
  }
  renderSeatMap();
}

export function renderSeatMap() {
  const map = document.getElementById('seatMap');
  if (!map) return;
  map.innerHTML = '';
  for (let i = 1; i <= currentTotalSeats; i++) {
    const taken = currentTakenSeats.includes(i);
    const cls = taken ? 'seat taken' : (i === selectedSeat ? 'seat selected' : 'seat free');
    const div = document.createElement('div');
    div.className = cls;
    div.textContent = i;
    if (!taken) div.addEventListener('click', () => selectSeat(i));
    map.appendChild(div);
  }
}

function selectSeat(n) {
  selectedSeat = n;
  document.getElementById('res-seat').value = n;
  renderSeatMap();
}

/** Submits a new reservation to the API. */
export async function makeReservation() {
  if (!getToken()) { showToast('Please log in first', '⚠️'); return; }
  const study_area_id = parseInt(document.getElementById('res-area').value);
  const seat_number   = parseInt(document.getElementById('res-seat').value);
  const date = document.getElementById('res-date').value;
  const sTime = document.getElementById('res-start').value;
  const eTime = document.getElementById('res-end').value;

  if (!date || !sTime || !eTime || !seat_number) {
    showToast('Please fill all fields & select a seat', '⚠️');
    return;
  }

  const start_time = new Date(`${date}T${sTime}`).toISOString();
  const end_time   = new Date(`${date}T${eTime}`).toISOString();

  const r = await apiFetch('/reservations/', {
    method: 'POST',
    body: JSON.stringify({ study_area_id, seat_number, start_time, end_time })
  });
  if (!r) { showToast('Network error', '❌'); return; }
  const data = await r.json();
  if (r.ok) {
    showToast('Reservation confirmed!', '✅');
    selectedSeat = null;
    await loadLibraries();
    loadUserReservations();
    fetchTakenSeats();
  } else {
    showToast(data.error || 'Error', '❌');
  }
}

/** Cancels an existing reservation. */
export async function cancelReservation(id) {
  if (!confirm('Cancel this reservation?')) return;
  const r = await apiFetch(`/reservations/${id}`, { method: 'DELETE' });
  if (!r) { showToast('Network error', '❌'); return; }
  if (r.ok) {
    showToast('Reservation cancelled', '✅');
    await loadLibraries();
    loadUserReservations();
    fetchTakenSeats();
  } else {
    const data = await r.json();
    showToast(data.error || 'Error', '❌');
  }
}

/** Loads the current user's active reservations. */
export async function loadUserReservations() {
  const userId = getUserId();
  if (!userId) return;
  const r = await apiFetch(`/reservations/user/${userId}`);
  if (!r || !r.ok) return;
  const data = await r.json();
  const list = document.getElementById('resList');
  list.innerHTML = data.reservations.map(rv => `
    <li class="res-item">
      <div>
        <div class="res-name">${escapeHtml(rv.study_area_name || 'Study Area')}</div>
        <div class="res-meta">Seat ${rv.seat_number} · ${new Date(rv.start_time).toLocaleDateString()}</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <span class="res-time">${new Date(rv.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}–${new Date(rv.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        <button onclick="window._cancelReservation(${rv.id})" style="background:var(--red);color:#fff;border:none;padding:5px 12px;border-radius:8px;cursor:pointer;font-size:.78rem;font-weight:600;">Cancel</button>
      </div>
    </li>
  `).join('') || '<li style="color:var(--muted);padding:1rem">No active reservations.</li>';
}

// Expose for inline onclick in dynamically generated HTML
window._cancelReservation = cancelReservation;

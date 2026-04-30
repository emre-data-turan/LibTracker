// ── Dashboard Module ──────────────────────────────────────
import { apiFetch } from './api.js';
import { escapeHtml } from './utils.js';

export let apiLibraries = [];

function getStatus(pct) {
  if (pct < 50) return ['green', 'Available'];
  if (pct < 80) return ['yellow', 'Moderate'];
  return ['red', 'Busy'];
}

/** Loads libraries from the API and renders them to the dashboard. */
export async function loadLibraries() {
  const r = await apiFetch('/libraries/');
  if (r && r.ok) {
    const data = await r.json();
    apiLibraries = data.libraries;
    renderLibraries(apiLibraries);
    populateLibrarySelects(apiLibraries);
    updateStatStrip(apiLibraries);
  }
}

function renderLibraries(libs) {
  const grid = document.getElementById('libraryGrid');
  grid.innerHTML = '';
  libs.forEach(lib => {
    const pct = lib.occupancy_percentage;
    const [color, label] = getStatus(pct);
    const free = lib.total_capacity - lib.current_occupancy;
    const busyBadge = lib.is_busy_notice
      ? `<span class="status-badge" style="background:#fee2e2;color:#dc2626;border:1px solid #f87171;">🚨 Busy Notice</span>`
      : '';
    grid.innerHTML += `
      <div class="card" onclick="window._goToReserve(${lib.id})" style="cursor:pointer;">
        <div class="card-header">
          <div>
            <div class="card-title">${escapeHtml(lib.name)}</div>
            <div class="card-sub">${escapeHtml(lib.location)}</div>
          </div>
          <div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap;justify-content:flex-end;">
            ${busyBadge}
            <span class="status-badge status-${color}">
              <span class="status-dot"></span>${label}
            </span>
          </div>
        </div>
        <div class="progress-wrap">
          <div class="progress-label"><span>Occupancy</span><span>${pct}%</span></div>
          <div class="progress-bar"><div class="progress-fill fill-${color}" style="width:${pct}%"></div></div>
        </div>
        <div class="card-info">
          <span>${lib.current_occupancy} / ${lib.total_capacity} seats taken</span>
          <span><strong>${free}</strong> seats free</span>
        </div>
      </div>`;
  });
}

function populateLibrarySelects(libs) {
  ['res-library', 'fb-library'].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = libs.map(l => `<option value="${l.id}">${escapeHtml(l.name)}</option>`).join('');
  });
  // Trigger study area update for reservation page
  const resLib = document.getElementById('res-library');
  if (resLib) resLib.dispatchEvent(new Event('change'));
}

function updateStatStrip(libs) {
  const total = libs.reduce((s, l) => s + l.total_capacity, 0);
  const occupied = libs.reduce((s, l) => s + l.current_occupancy, 0);
  const free = total - occupied;
  const avgPct = total ? Math.round((occupied / total) * 100) : 0;

  const el = id => document.getElementById(id);
  el('statOccupied').textContent = occupied;
  el('statFree').textContent = free;
  el('statTotal').textContent = total;
  el('statAvg').textContent = avgPct + '%';
}

/** Initialises Chart.js dashboard charts using API data. */
export async function initCharts() {
  /* global Chart */
  const accent = '#b8860b', green = '#10b981', yellow = '#f59e0b', red = '#ef4444';

  // ── Occupancy Overview (bar)
  const weekLibNames = apiLibraries.length
    ? apiLibraries.map(l => l.name.substring(0, 10))
    : ['Lib A', 'Lib B', 'Lib C'];
  const weekLibData = apiLibraries.length
    ? apiLibraries.map(l => l.occupancy_percentage)
    : [0, 0, 0];

  new Chart(document.getElementById('chartOcc'), {
    type: 'bar',
    data: {
      labels: weekLibNames,
      datasets: [{
        label: 'Occupancy %',
        data: weekLibData,
        backgroundColor: weekLibData.map(v => v < 50 ? green : v < 80 ? yellow : red),
        borderRadius: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { max: 100, ticks: { callback: v => v + '%' } } }
    }
  });

  // ── Reservation Activity (bar) — from API
  const resChartData = apiLibraries.length
    ? apiLibraries.map(l => l.current_occupancy)
    : [0];

  new Chart(document.getElementById('chartRes'), {
    type: 'bar',
    data: {
      labels: weekLibNames,
      datasets: [{ label: 'Reservations', data: resChartData, backgroundColor: accent, borderRadius: 6 }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });
}

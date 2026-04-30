// ── Admin App Entry Point ─────────────────────────────────
import { API } from './config.js';
import { escapeHtml } from './utils.js';

let TOKEN = '';

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (TOKEN) headers['Authorization'] = 'Bearer ' + TOKEN;
  try {
    return await fetch(API + path, { ...options, headers });
  } catch {
    return null;
  }
}

async function checkAdminAuth() {
  if (!TOKEN) return false;
  const r = await apiFetch('/auth/me');
  if (r && r.ok) {
    const data = await r.json();
    if (data.user && data.user.is_admin) return true;
  }
  return false;
}

async function doAdminLogin() {
  let email = document.getElementById('inp-email').value;
  if (email === 'admin') email = 'admin@libtracker.edu';
  const pass = document.getElementById('inp-pass').value;
  try {
    const r = await fetch(API + '/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: pass })
    });
    const data = await r.json();
    if (r.ok && data.user && data.user.is_admin) {
      TOKEN = data.token;
      document.getElementById('authModalAdmin').classList.remove('active');
      initCharts();
      loadAdminLibraries();
    } else {
      alert(data.error || 'Access Denied: Admins Only.');
    }
  } catch {
    alert('Unable to reach server. Is the backend running?');
  }
}

// ── Charts ────────────────────────────────────────────────
const accent = '#4f6ef7', green = '#22c55e', yellow = '#f59e0b', red = '#ef4444';

async function initCharts() {
  /* global Chart */

  // Total occupancy
  const libR = await apiFetch('/libraries/');
  if (libR && libR.ok) {
    const ld = await libR.json();
    let occ = 0;
    if (ld.libraries) ld.libraries.forEach(l => occ += l.current_occupancy);
    document.getElementById('st-visits').textContent = occ;
  } else {
    document.getElementById('st-visits').textContent = '0';
  }

  // Overview stats
  const overviewR = await apiFetch('/stats/overview');
  if (overviewR && overviewR.ok) {
    const od = await overviewR.json();
    document.getElementById('st-res').textContent = od.active_reservations;
    const recentFb = od.recent_feedbacks || 0;
    const recentRes = od.recent_reservations || 0;
    const accuracy = recentFb > 0 ? Math.min(100, Math.round((recentFb / Math.max(1, recentRes)) * 50)) : 0;
    document.getElementById('st-accuracy').textContent = accuracy + '%';
  } else {
    document.getElementById('st-res').textContent = '0';
    document.getElementById('st-accuracy').textContent = '0%';
  }

  // Peak hours chart
  const peakR = await apiFetch('/stats/peak-hours?days=7');
  let hourlyLabels = ['08','09','10','11','12','13','14','15','16','17','18','19','20'];
  let hourlyData = [10,22,45,60,75,68,82,79,70,65,55,40,20];
  if (peakR && peakR.ok) {
    const pd = await peakR.json();
    if (pd.peak_hours && pd.peak_hours.length > 0) {
      const hourMap = {};
      pd.peak_hours.forEach(lib => {
        lib.hourly_data.forEach(h => {
          if (!hourMap[h.hour]) hourMap[h.hour] = { sum: 0, count: 0 };
          hourMap[h.hour].sum += h.avg_occupancy_pct;
          hourMap[h.hour].count += 1;
        });
      });
      const sortedHours = Object.keys(hourMap).sort((a,b) => parseInt(a) - parseInt(b));
      hourlyLabels = sortedHours.map(h => String(h).padStart(2,'0'));
      hourlyData = sortedHours.map(h => Math.round(hourMap[h].sum / hourMap[h].count));

      let maxPct = -1, peakHr = '14:00';
      hourlyData.forEach((pct, idx) => {
        if (pct > maxPct) { maxPct = pct; peakHr = hourlyLabels[idx] + ':00'; }
      });
      document.getElementById('st-peak').textContent = peakHr;
    }
  }

  new Chart(document.getElementById('chartHourly'), {
    type: 'line',
    data: { labels: hourlyLabels, datasets: [{ label: 'Occupancy %', data: hourlyData, borderColor: accent, backgroundColor: 'rgba(79,110,247,.1)', fill: true, tension: .4, pointRadius: 4 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { callback: v => v + '%' } } } }
  });

  // Daily usage chart
  const dailyR = await apiFetch('/stats/daily-usage?days=7');
  let libNames = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  let libData = [30,90,82,20,95,34,78];
  if (dailyR && dailyR.ok) {
    const dd = await dailyR.json();
    if (dd.daily_usage && dd.daily_usage.length > 0) {
      libNames = dd.daily_usage.map(d => d.library_name.substring(0,10));
      libData = dd.daily_usage.map(d => d.daily_data.length ? d.daily_data[d.daily_data.length-1].avg_pct : 0);
    }
  }

  new Chart(document.getElementById('chartWeekly'), {
    type: 'bar',
    data: { labels: libNames, datasets: [{ label: 'Avg %', data: libData, backgroundColor: libData.map(v => v < 50 ? green : v < 80 ? yellow : red) }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { max: 100 } } }
  });

  // Reservation chart from API
  const resR = await apiFetch('/stats/daily-reservations?days=7');
  let resDayLabels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  let resDayData = [45,67,89,72,94,38,21];
  if (resR && resR.ok) {
    const rd = await resR.json();
    if (rd.daily_reservations && rd.daily_reservations.length > 0) {
      resDayLabels = rd.daily_reservations.map(d => d.date.substring(5));
      resDayData = rd.daily_reservations.map(d => d.count);
    }
  }

  new Chart(document.getElementById('chartRes'), {
    type: 'bar',
    data: { labels: resDayLabels, datasets: [{ label: 'Reservations', data: resDayData, backgroundColor: accent, borderRadius: 6 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
  });

  // Distribution doughnut from live library data
  let distAvail = 3, distMod = 2, distBusy = 2;
  const distR = await apiFetch('/libraries/');
  if (distR && distR.ok) {
    const distData = await distR.json();
    if (distData.libraries) {
      distAvail = distData.libraries.filter(l => l.occupancy_percentage < 50).length;
      distMod = distData.libraries.filter(l => l.occupancy_percentage >= 50 && l.occupancy_percentage < 80).length;
      distBusy = distData.libraries.filter(l => l.occupancy_percentage >= 80).length;
    }
  }

  new Chart(document.getElementById('chartDist'), {
    type: 'doughnut',
    data: { labels: ['Available (<50%)','Moderate (50-80%)','Busy (>80%)'], datasets: [{ data: [distAvail, distMod, distBusy], backgroundColor: [green, yellow, red], hoverOffset: 8 }] },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

// ── Library CRUD ──────────────────────────────────────────
async function loadAdminLibraries() {
  const r = await apiFetch('/libraries/');
  if (r && r.ok) {
    const data = await r.json();
    const grid = document.getElementById('adminLibGrid');
    grid.innerHTML = data.libraries.map(lib => {
      const warningHtml = lib.social_science_warning 
        ? `<div style="background:#fee2e2; color:#b91c1c; padding:8px; border-radius:6px; font-size:0.85rem; font-weight:bold; margin-bottom:8px;">⚠️ Warning: More than 3 overlapping feedbacks detected for Social Science!</div>` 
        : '';
      return `
      <div class="stat-card" style="text-align:left; display:flex; flex-direction:column; gap:8px;">
        ${warningHtml}
        <label style="font-size:.8rem;color:var(--muted)">Name</label>
        <input type="text" id="edit-name-${lib.id}" value="${escapeHtml(lib.name)}" style="padding:6px; border-radius:6px; border:1px solid #ccc; width:100%;">
        <div style="display:flex; gap:10px;">
          <div style="flex:1;">
            <label style="font-size:.8rem;color:var(--muted)">Capacity</label>
            <input type="number" id="edit-cap-${lib.id}" value="${lib.total_capacity}" min="1" style="padding:6px; border-radius:6px; border:1px solid #ccc; width:100%;">
          </div>
          <div style="flex:1;">
            <label style="font-size:.8rem;color:var(--muted)">Occupied</label>
            <input type="number" id="edit-occ-${lib.id}" value="${lib.current_occupancy}" min="0" style="padding:6px; border-radius:6px; border:1px solid #ccc; width:100%;">
          </div>
        </div>
        <div style="display:flex; gap:10px; margin-top:10px;">
          <button onclick="window._saveLibrary(${lib.id})" style="flex:1; background:var(--green); color:#fff; border:none; padding:8px; border-radius:8px; cursor:pointer;">Save</button>
          <button onclick="window._deleteLib(${lib.id})" style="flex:1; background:var(--red); color:#fff; border:none; padding:8px; border-radius:8px; cursor:pointer;">Delete</button>
        </div>
      </div>
    `}).join('');

  }
}

async function saveLibrary(id) {
  const name = document.getElementById(`edit-name-${id}`).value;
  const total_capacity = parseInt(document.getElementById(`edit-cap-${id}`).value);
  const current_occupancy = parseInt(document.getElementById(`edit-occ-${id}`).value);

  if (!name.trim()) { alert('Name is required.'); return; }
  if (isNaN(total_capacity) || total_capacity <= 0) { alert('Capacity must be positive.'); return; }
  if (isNaN(current_occupancy) || current_occupancy < 0) { alert('Occupancy cannot be negative.'); return; }
  if (current_occupancy > total_capacity) { alert('Occupancy cannot exceed capacity.'); return; }

  const r = await apiFetch(`/libraries/${id}`, { method: 'PUT', body: JSON.stringify({ name, total_capacity, current_occupancy }) });
  if (r && r.ok) { alert('Updated!'); loadAdminLibraries(); } else { alert('Failed.'); }
}

async function deleteLib(id) {
  if (!confirm('Permanently delete this library?')) return;
  const r = await apiFetch(`/libraries/${id}`, { method: 'DELETE' });
  if (r && r.ok) { alert('Deleted!'); loadAdminLibraries(); } else { alert('Failed.'); }
}

function showCreateModal() {
  document.getElementById('createLibModal').classList.add('active');
}

async function createLibrary() {
  const name = document.getElementById('new-lib-name').value.trim();
  const location = document.getElementById('new-lib-loc').value.trim();
  const total_capacity = parseInt(document.getElementById('new-lib-cap').value);
  if (!name) { alert('Name required.'); return; }
  if (!location) { alert('Location required.'); return; }
  if (isNaN(total_capacity) || total_capacity <= 0) { alert('Capacity must be positive.'); return; }

  const r = await apiFetch('/libraries/', { method: 'POST', body: JSON.stringify({ name, location, total_capacity }) });
  if (r && r.ok) {
    alert('Created!');
    document.getElementById('createLibModal').classList.remove('active');
    document.getElementById('new-lib-name').value = '';
    document.getElementById('new-lib-loc').value = '';
    document.getElementById('new-lib-cap').value = '';
    loadAdminLibraries();
  } else { alert('Failed.'); }
}

// Expose for inline onclick
window._doAdminLogin = doAdminLogin;
window._saveLibrary = saveLibrary;
window._deleteLib = deleteLib;
window._showCreateModal = showCreateModal;
window._createLibrary = createLibrary;

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Close modal on overlay click
  document.querySelectorAll('.modal-overlay').forEach(ov => {
    ov.addEventListener('click', e => { if (e.target === ov) ov.classList.remove('active'); });
  });

  const isAdmin = await checkAdminAuth();
  if (isAdmin) {
    document.getElementById('authModalAdmin').classList.remove('active');
    initCharts();
    loadAdminLibraries();
  } else {
    document.getElementById('authModalAdmin').classList.add('active');
  }
});

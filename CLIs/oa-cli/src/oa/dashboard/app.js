/**
 * OA Dashboard — Vanilla JS frontend.
 * Mirrors the internal React dashboard design:
 *   - Glass morphism cards with backdrop-filter
 *   - Two-column layout: compact goal card (left) + detail chart (right)
 *   - Health summary strip with colored dots
 *   - Chart.js for time-series sparklines
 * Auto-refreshes every 30 seconds.
 */

let currentView = 'system-health';
let chartInstances = {};

// ━━━ Init ━━━

document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  loadView(currentView);
  setInterval(() => loadView(currentView), 30000);
});

function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('tab-active');
        b.classList.add('tab-inactive');
      });
      btn.classList.remove('tab-inactive');
      btn.classList.add('tab-active');
      currentView = btn.dataset.view;
      loadView(currentView);
    });
  });
}

// ━━━ Data ━━━

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function loadView(view) {
  try {
    if (view === 'system-health') {
      const [goals, health] = await Promise.all([
        fetchJSON('/api/goals'),
        fetchJSON('/api/health'),
      ]);
      renderHealthStrip(goals, health);
      renderSystemHealth(goals);
    } else if (view === 'traces') {
      document.getElementById('health-strip').classList.add('hidden');
      const traces = await fetchJSON('/api/traces');
      renderTraces(traces);
    }
  } catch (err) {
    document.getElementById('content').innerHTML = `
      <div class="glass-card p-8 max-w-md mx-auto text-center space-y-3 fade-in">
        <p class="text-sm text-gray-600">Connection Error</p>
        <p class="text-xs text-gray-400 font-mono">${esc(err.message)}</p>
        <p class="text-[10px] text-gray-400">Ensure the API server is running</p>
      </div>`;
  }
}

// ━━━ Health Summary Strip ━━━

function renderHealthStrip(goals, health) {
  const strip = document.getElementById('health-strip');
  strip.classList.remove('hidden');

  document.getElementById('overall-score').textContent =
    health.overall === 'unknown' ? '—' : `${Math.round(computeOverallScore(goals))}%`;

  const dots = document.getElementById('health-dots');
  dots.innerHTML = goals.map(g => `
    <div class="flex items-center gap-1" title="${esc(g.name)}: ${g.healthStatus}">
      <div class="health-dot ${g.healthStatus}"></div>
      <span class="text-[9px] text-gray-400 font-mono hidden sm:inline">${esc(g.name.slice(0, 4))}</span>
    </div>
  `).join('');

  document.getElementById('last-updated').textContent =
    health.lastCollected || 'No data';
}

function computeOverallScore(goals) {
  const scores = goals.map(g => {
    const metrics = Object.values(g.metrics || {});
    const primary = metrics[0];
    if (!primary || primary.value === null) return null;
    if (primary.unit === '%') return Math.min(100, Math.max(0, primary.value));
    if (primary.value >= primary.healthy) return 90;
    if (primary.value >= primary.warning) return 65;
    return 40;
  }).filter(s => s !== null);
  if (!scores.length) return 0;
  return scores.reduce((a, b) => a + b, 0) / scores.length;
}

// ━━━ System Health View ━━━

function renderSystemHealth(goals) {
  const content = document.getElementById('content');
  if (!goals.length) {
    content.innerHTML = `
      <div class="empty-state fade-in">
        <p class="text-lg font-semibold text-gray-400">No goals configured</p>
        <p class="text-sm text-gray-300 mt-2">Run <code class="bg-gray-100 px-2 py-0.5 rounded text-xs">oa init</code> to set up goals</p>
      </div>`;
    return;
  }

  // Destroy old chart instances
  Object.values(chartInstances).forEach(c => c.destroy());
  chartInstances = {};

  content.innerHTML = `<div class="space-y-4 fade-in">${goals.map((g, i) => renderGoalRow(g, i)).join('')}</div>`;

  // Initialize charts after DOM is ready
  requestAnimationFrame(() => {
    goals.forEach((g, i) => {
      if (g.sparkline && g.sparkline.length > 1) {
        createChart(g, i);
      }
    });
  });
}

// ━━━ Goal Row: Card (left) + Detail (right) ━━━

function renderGoalRow(goal, index) {
  const color = healthColor(goal.healthStatus);
  const metrics = Object.entries(goal.metrics || {});
  const primary = metrics[0];

  return `
    <div class="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4 items-stretch">
      <!-- Left: Goal Card -->
      <div class="glass-card goal-card p-5" style="--goal-color: ${color}; border-left-color: ${color}">
        <!-- Header -->
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-800">${esc(goal.name)}</h3>
          <div class="health-dot ${goal.healthStatus}" style="box-shadow: 0 0 8px ${color}40"></div>
        </div>

        <!-- Primary Metric -->
        ${primary ? `
          <div class="mb-3">
            <div class="text-3xl font-bold" style="color: ${color}">
              ${formatValue(primary[1].value, primary[1].unit)}
            </div>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-[10px] text-gray-400 uppercase tracking-wider">${formatMetricName(primary[0])}</span>
              ${renderTrend(primary[1].trend)}
            </div>
          </div>
        ` : ''}

        <!-- Sub-metrics -->
        ${metrics.length > 1 ? `
          <div class="border-t border-gray-100 pt-2 mt-2 space-y-1">
            ${metrics.slice(1).map(([name, m]) => `
              <div class="sub-metric-row">
                <span class="text-[11px] text-gray-400">${formatMetricName(name)}</span>
                <span class="text-[11px] font-semibold text-${m.status || 'gray-600'}">
                  ${formatValue(m.value, m.unit)}
                </span>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>

      <!-- Right: Detail Section with Chart -->
      <div class="glass-card detail-section p-6" style="--goal-color: ${color}; border-left-color: ${color}">
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">${esc(goal.name)} — Trend</h4>
          <span class="text-[10px] text-gray-400 font-mono">${goal.sparkline ? goal.sparkline.length : 0} days</span>
        </div>
        ${goal.sparkline && goal.sparkline.length > 1 ? `
          <div class="chart-container">
            <canvas id="chart-${index}"></canvas>
          </div>
        ` : `
          <div class="h-[160px] flex items-center justify-center">
            <span class="text-xs text-gray-300">Not enough data for chart — run <code class="bg-gray-50 px-1.5 py-0.5 rounded">oa collect</code> daily</span>
          </div>
        `}

        <!-- All Metrics Summary -->
        ${metrics.length > 0 ? `
          <div class="grid grid-cols-2 sm:grid-cols-${Math.min(metrics.length, 4)} gap-3 mt-4 pt-4 border-t border-gray-100">
            ${metrics.map(([name, m]) => `
              <div>
                <div class="text-[10px] text-gray-400 uppercase tracking-wider">${formatMetricName(name)}</div>
                <div class="text-sm font-bold text-${m.status || 'gray-600'}" style="color: ${healthColor(m.status || 'unknown')}">${formatValue(m.value, m.unit)}</div>
              </div>
            `).join('')}
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

// ━━━ Chart.js ━━━

function createChart(goal, index) {
  const canvas = document.getElementById(`chart-${index}`);
  if (!canvas) return;

  const data = goal.sparkline;
  const color = healthColor(goal.healthStatus);
  const labels = data.map(d => {
    const dt = new Date(d.date + 'T00:00:00');
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  const values = data.map(d => d.value);
  const primary = Object.values(goal.metrics || {})[0];
  const isPercent = primary && primary.unit === '%';

  chartInstances[`chart-${index}`] = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: color,
        backgroundColor: color + '15',
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: data.length > 14 ? 0 : 3,
        pointHoverRadius: 5,
        pointBackgroundColor: color,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(255,255,255,0.95)',
          titleColor: '#374151',
          bodyColor: '#6b7280',
          borderColor: 'rgba(0,0,0,0.08)',
          borderWidth: 1,
          cornerRadius: 8,
          padding: 10,
          titleFont: { size: 11, weight: '600' },
          bodyFont: { size: 11 },
          callbacks: {
            label: (ctx) => isPercent ? `${ctx.parsed.y}%` : `${ctx.parsed.y}`,
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
          ticks: { font: { size: 9 }, color: '#9ca3af', maxTicksLimit: 8 },
        },
        y: {
          min: isPercent ? 0 : undefined,
          max: isPercent ? 100 : undefined,
          grid: { color: 'rgba(0,0,0,0.04)', drawBorder: false },
          ticks: { font: { size: 9 }, color: '#9ca3af' },
        }
      },
      interaction: { mode: 'index', intersect: false },
    }
  });
}

// ━━━ Traces View ━━━

function renderTraces(traces) {
  const content = document.getElementById('content');
  if (!traces.length) {
    content.innerHTML = `
      <div class="empty-state fade-in">
        <p class="text-lg font-semibold text-gray-400">No traces yet</p>
        <p class="text-sm text-gray-300 mt-2">Run <code class="bg-gray-100 px-2 py-0.5 rounded text-xs">oa collect</code> to generate traces</p>
      </div>`;
    return;
  }

  // Group by trace_id
  const byTrace = {};
  traces.forEach(t => {
    if (!byTrace[t.trace_id]) byTrace[t.trace_id] = [];
    byTrace[t.trace_id].push(t);
  });

  const groups = Object.entries(byTrace).slice(0, 20);
  content.innerHTML = `<div class="space-y-3 fade-in">${groups.map(([tid, spans]) => {
    const root = spans.find(s => !s.parent_span_id) || spans[0];
    const totalMs = spans.reduce((s, sp) => s + (sp.duration_ms || 0), 0);
    const statusDot = root.status === 'ok'
      ? '<div class="w-2 h-2 rounded-full bg-emerald-400 inline-block mr-1.5"></div>'
      : '<div class="w-2 h-2 rounded-full bg-red-400 inline-block mr-1.5"></div>';

    const attrs = root.attributes
      ? Object.entries(root.attributes).filter(([k]) => !k.startsWith('_')).slice(0, 5)
      : [];

    return `
      <div class="glass-card trace-card p-4">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center">
            ${statusDot}
            <span class="text-sm font-semibold text-gray-800">${esc(root.name)}</span>
          </div>
          <span class="text-[11px] text-gray-400 bg-gray-50 px-2 py-0.5 rounded">${esc(root.service)}</span>
        </div>
        <div class="flex gap-4 text-[11px] text-gray-400">
          <span>${spans.length} span${spans.length > 1 ? 's' : ''}</span>
          <span>${totalMs.toFixed(0)}ms</span>
          <span>${formatDateTime(root.start_time)}</span>
          <span class="font-mono">${tid.slice(0, 8)}…</span>
        </div>
        ${attrs.length ? `
          <div class="flex flex-wrap gap-1.5 mt-2">
            ${attrs.map(([k, v]) => `<span class="text-[10px] bg-gray-50 border border-gray-100 px-1.5 py-0.5 rounded"><b class="text-gray-500">${esc(k)}:</b> ${esc(String(v))}</span>`).join('')}
          </div>
        ` : ''}
      </div>`;
  }).join('')}</div>`;
}

// ━━━ Helpers ━━━

function healthColor(status) {
  const colors = { healthy: '#34D399', warning: '#FBBF24', critical: '#F87171', unknown: '#CBD5E1' };
  return colors[status] || colors.unknown;
}

function formatValue(value, unit) {
  if (value === null || value === undefined) return '—';
  if (unit === '%') return `${Math.round(value * 10) / 10}%`;
  if (unit === 'count') return Math.round(value).toString();
  return (Math.round(value * 10) / 10) + (unit ? ` ${unit}` : '');
}

function formatMetricName(name) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function renderTrend(trend) {
  if (trend === null || trend === undefined) return '';
  if (trend > 0) return `<span class="text-[11px] font-medium trend-up">▲ +${trend}</span>`;
  if (trend < 0) return `<span class="text-[11px] font-medium trend-down">▼ ${trend}</span>`;
  return `<span class="text-[11px] font-medium trend-flat">─ 0</span>`;
}

function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' ' +
    d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

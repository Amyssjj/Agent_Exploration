/**
 * OA Dashboard — Vanilla JS frontend.
 * Fetches data from the Python API server and renders goal cards + traces.
 * Auto-refreshes every 60 seconds.
 */

const API = '';  // same origin
let currentView = 'health';
let refreshTimer = null;

// ━━━ Init ━━━

document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  loadView(currentView);
  refreshTimer = setInterval(() => loadView(currentView), 60000);
});

function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentView = tab.dataset.view;
      loadView(currentView);
    });
  });
}

// ━━━ Data Loading ━━━

async function fetchJSON(url) {
  const res = await fetch(API + url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function loadView(view) {
  const content = document.getElementById('content');
  content.innerHTML = '<div class="loading">Loading...</div>';

  try {
    if (view === 'health') {
      const [goals, health] = await Promise.all([
        fetchJSON('/api/goals'),
        fetchJSON('/api/health'),
      ]);
      renderHealthBadge(health);
      renderHealthView(goals);
    } else if (view === 'traces') {
      const traces = await fetchJSON('/api/traces');
      renderTracesView(traces);
    }
  } catch (err) {
    content.innerHTML = `<div class="empty-state"><h3>Error loading data</h3><p>${err.message}</p></div>`;
  }
}

// ━━━ Health Badge ━━━

function renderHealthBadge(health) {
  const badge = document.getElementById('health-badge');
  badge.className = `badge badge-${health.overall}`;
  badge.textContent = health.overall;

  const lastEl = document.getElementById('last-collected');
  lastEl.textContent = health.lastCollected
    ? `Last collected: ${health.lastCollected}`
    : 'No data yet';
}

// ━━━ System Health View ━━━

function renderHealthView(goals) {
  const content = document.getElementById('content');

  if (!goals.length) {
    content.innerHTML = '<div class="empty-state"><h3>No goals configured</h3><p>Run <code>oa init</code> to set up goals.</p></div>';
    return;
  }

  const html = '<div class="goals-grid">' + goals.map(renderGoalCard).join('') + '</div>';
  content.innerHTML = html;
}

function renderGoalCard(goal) {
  const metrics = Object.entries(goal.metrics || {});

  const metricsHtml = metrics.map(([name, m]) => {
    const displayValue = m.value !== null ? formatValue(m.value, m.unit) : '—';
    const status = m.status || 'unknown';
    const trendHtml = renderTrend(m.trend);

    return `
      <div class="metric-row">
        <span class="metric-name">${formatMetricName(name)}</span>
        <div class="metric-detail">
          ${trendHtml}
          <span class="metric-value ${status}">${displayValue}</span>
        </div>
      </div>
    `;
  }).join('');

  const sparklineHtml = goal.sparkline && goal.sparkline.length > 1
    ? `<div class="sparkline-container">
        <svg class="sparkline" viewBox="0 0 300 40" preserveAspectRatio="none">
          ${renderSparklinePath(goal.sparkline, goal.healthStatus)}
        </svg>
        <div class="sparkline-label">${goal.sparkline.length} days tracked</div>
       </div>`
    : '';

  return `
    <div class="goal-card">
      <div class="goal-header">
        <span class="goal-name">${escapeHtml(goal.name)}</span>
        <span class="goal-status ${goal.healthStatus}"></span>
      </div>
      <div class="metrics-list">
        ${metricsHtml}
      </div>
      ${sparklineHtml}
    </div>
  `;
}

// ━━━ Traces View ━━━

function renderTracesView(traces) {
  const content = document.getElementById('content');

  if (!traces.length) {
    content.innerHTML = '<div class="empty-state"><h3>No traces yet</h3><p>Run <code>oa collect</code> to generate execution traces.</p></div>';
    return;
  }

  // Group by trace_id
  const byTrace = {};
  traces.forEach(t => {
    if (!byTrace[t.trace_id]) byTrace[t.trace_id] = [];
    byTrace[t.trace_id].push(t);
  });

  const traceGroups = Object.entries(byTrace).slice(0, 20);

  const html = '<div class="traces-list">' + traceGroups.map(([traceId, spans]) => {
    const root = spans.find(s => !s.parent_span_id) || spans[0];
    const totalMs = spans.reduce((sum, s) => sum + (s.duration_ms || 0), 0);

    const attrsHtml = root.attributes
      ? Object.entries(root.attributes)
          .filter(([k]) => !k.startsWith('data_flow') && !k.startsWith('node_types'))
          .slice(0, 6)
          .map(([k, v]) => `<span class="trace-attr"><span class="trace-attr-key">${escapeHtml(k)}:</span> ${escapeHtml(String(v))}</span>`)
          .join('')
      : '';

    return `
      <div class="trace-card">
        <div class="trace-header">
          <div>
            <span class="trace-status ${root.status}"></span>
            <span class="trace-name">${escapeHtml(root.name)}</span>
          </div>
          <span class="trace-service">${escapeHtml(root.service)}</span>
        </div>
        <div class="trace-meta">
          <span>${spans.length} span${spans.length > 1 ? 's' : ''}</span>
          <span>${totalMs.toFixed(0)}ms total</span>
          <span>${formatDateTime(root.start_time)}</span>
          <span class="trace-id">${traceId.slice(0, 8)}...</span>
        </div>
        ${attrsHtml ? `<div class="trace-attrs">${attrsHtml}</div>` : ''}
      </div>
    `;
  }).join('') + '</div>';

  content.innerHTML = html;
}

// ━━━ Helpers ━━━

function formatValue(value, unit) {
  if (unit === '%') return `${Math.round(value * 10) / 10}%`;
  if (unit === 'count') return Math.round(value).toString();
  return Math.round(value * 10) / 10 + (unit ? ` ${unit}` : '');
}

function formatMetricName(name) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderTrend(trend) {
  if (trend === null || trend === undefined) return '';
  if (trend > 0) return `<span class="metric-trend up">+${trend}</span>`;
  if (trend < 0) return `<span class="metric-trend down">${trend}</span>`;
  return `<span class="metric-trend flat">0</span>`;
}

function renderSparklinePath(data, status) {
  if (!data || data.length < 2) return '';
  const values = data.map(d => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const w = 300, h = 40, pad = 2;
  const points = values.map((v, i) => {
    const x = pad + (i / (values.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  });

  const colors = { healthy: '#10b981', warning: '#f59e0b', critical: '#ef4444', unknown: '#9ca3af' };
  const color = colors[status] || colors.unknown;

  return `<polyline points="${points.join(' ')}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

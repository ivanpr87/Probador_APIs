/* ─────────────────────────────────────────
   API Sentinel — Frontend Logic
   ───────────────────────────────────────── */

// ── State ──────────────────────────────────
let lastResult   = null;
let historyItems = [];

// ── View titles ────────────────────────────
const VIEW_TITLES = {
  'run-test': 'Run Test',
  'results':  'Results',
  'history':  'History',
};

/* ─────────────────────────────────────────
   Navigation
   ───────────────────────────────────────── */
function switchView(viewId) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === viewId);
  });

  document.querySelectorAll('.view').forEach(el => {
    el.classList.toggle('active', el.id === `view-${viewId}`);
  });

  document.getElementById('topbar-title').textContent = VIEW_TITLES[viewId] ?? viewId;

  renderTopbarActions(viewId);

  if (viewId === 'history') loadHistory();
}

function renderTopbarActions(viewId) {
  const el = document.getElementById('topbar-actions');
  if (viewId === 'results' && lastResult) {
    el.innerHTML = `<button class="btn-secondary" id="btn-export">↓ Export JSON</button>`;
    document.getElementById('btn-export').addEventListener('click', downloadReport);
  } else {
    el.innerHTML = '';
  }
}

/* ─────────────────────────────────────────
   Run Test
   ───────────────────────────────────────── */
async function runTest() {
  const url     = document.getElementById('url').value.trim();
  const method  = document.getElementById('method').value;
  const rawBody = document.getElementById('payload').value.trim();
  const rawHdrs = document.getElementById('headers').value.trim();

  hideError();
  if (!url) { showError('Please enter an endpoint URL.'); return; }

  let payload = null;
  if (method === 'POST' && rawBody) {
    try { payload = JSON.parse(rawBody); }
    catch { showError('Invalid JSON in payload — check the syntax and try again.'); return; }
  }

  let headers = {};
  if (rawHdrs) {
    try { headers = JSON.parse(rawHdrs); }
    catch { showError('Invalid JSON in headers — check the syntax and try again.'); return; }
  }

  setLoading(true);

  try {
    const res = await fetch('/run-test', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ url, method, payload, headers }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Server error ${res.status}: ${text}`);
    }

    const data = await res.json();
    lastResult  = data;

    renderResults(data);
    switchView('results');

    document.getElementById('results-badge').style.display = 'inline';

  } catch (e) {
    showError(e.message || 'Unexpected error. Is the backend running?');
  } finally {
    setLoading(false);
  }
}

/* ─────────────────────────────────────────
   Render Results
   ───────────────────────────────────────── */
function renderResults(data) {
  const { total_tests, results, issues_detected, severity, quality_score, ai_insights } = data;

  const score    = quality_score ?? 0;
  const pct      = Math.min(100, Math.max(0, score));
  const sev      = (severity || 'low').toLowerCase();
  const scoreClr = scoreColor(pct);
  const sevClr   = sev === 'critical' ? 'var(--critical)' : sev === 'high' ? 'var(--high)' : 'var(--low)';
  const passed   = results.filter(r => r.status_code >= 200 && r.status_code < 300).length;
  const failed   = total_tests - passed;

  document.getElementById('results-content').innerHTML = `

    <!-- Metrics -->
    <div class="three-col">

      <div class="metric-card">
        <div class="metric-label">Quality Score</div>
        <div class="metric-value" style="color:${scoreClr}">${score}</div>
        <div class="score-bar-wrap">
          <div class="score-bar-fill" style="width:${pct}%;background:${scoreClr}"></div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Severity</div>
        <div class="metric-value" style="font-size:28px;color:${sevClr};margin-bottom:14px">${cap(sev)}</div>
        <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
      </div>

      <div class="metric-card">
        <div class="metric-label">Test Summary</div>
        <div style="margin-top:8px">
          <div class="chips-row">
            <span class="chip">Total <strong>${total_tests}</strong></span>
            <span class="chip" style="color:var(--low)">Passed <strong>${passed}</strong></span>
            <span class="chip" style="color:var(--critical)">Failed <strong>${failed}</strong></span>
          </div>
        </div>
      </div>

    </div>

    <!-- Issues + Insights -->
    <div class="two-col" style="margin-bottom:16px">

      <div class="card">
        <div class="card-header">
          <div class="card-title">⚠ Detected Issues</div>
          <div class="card-desc">${issues_detected.length} issue${issues_detected.length !== 1 ? 's' : ''} found</div>
        </div>
        <div class="card-body">
          ${tagList(issues_detected, 'issue')}
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">✦ AI Insights</div>
          <div class="card-desc">${ai_insights.length} recommendation${ai_insights.length !== 1 ? 's' : ''}</div>
        </div>
        <div class="card-body">
          ${tagList(ai_insights, 'insight')}
        </div>
      </div>

    </div>

    <!-- Results table -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">📋 Test Results</div>
        <div class="card-desc">${total_tests} tests executed</div>
      </div>
      <div class="card-body" style="padding:0">
        <div class="table-wrap flush">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Test Name</th>
                <th>Status</th>
                <th>Response Time</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              ${results.map(resultRow).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </div>

  `;
}

function tagList(items, type) {
  if (!items || !items.length) {
    const msg = type === 'issue' ? 'No issues detected — looking good!' : 'No insights available.';
    return `<p class="empty-msg">${msg}</p>`;
  }
  return `<div class="item-list">
    ${items.map(i => `
      <div class="list-item">
        <div class="list-dot dot-${type}"></div>
        <span>${esc(i)}</span>
      </div>`).join('')}
  </div>`;
}

function resultRow(r, idx) {
  const code   = r.status_code;
  const cls    = !code ? 'code-err' : code < 300 ? 'code-2xx' : code < 500 ? 'code-4xx' : 'code-5xx';
  const codeEl = code
    ? `<span class="code-badge ${cls}">${code}</span>`
    : `<span class="code-badge code-err">—</span>`;
  const timeEl = r.response_time != null
    ? `<span style="color:var(--muted);font-size:12px">${(r.response_time * 1000).toFixed(0)} ms</span>`
    : `<span style="color:var(--muted)">—</span>`;
  const errEl  = r.error
    ? `<span style="color:var(--critical);font-family:var(--mono);font-size:11px">${esc(r.error)}</span>`
    : `<span style="color:var(--muted)">—</span>`;

  return `<tr>
    <td style="color:var(--muted);font-size:12px">${idx + 1}</td>
    <td style="font-family:var(--mono);font-size:12px">${esc(r.test_name || '—')}</td>
    <td>${codeEl}</td>
    <td>${timeEl}</td>
    <td>${errEl}</td>
  </tr>`;
}

/* ─────────────────────────────────────────
   Export
   ───────────────────────────────────────── */
function downloadReport() {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: 'application/json' });
  const a = Object.assign(document.createElement('a'), {
    href:     URL.createObjectURL(blob),
    download: `sentinel-report-${Date.now()}.json`,
  });
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ─────────────────────────────────────────
   History
   ───────────────────────────────────────── */
async function loadHistory() {
  const container = document.getElementById('history-content');

  try {
    const res = await fetch('/history');
    if (!res.ok) throw new Error('fetch failed');
    const items = await res.json();
    historyItems = items;
    renderHistory(items, container);
  } catch {
    container.innerHTML = `
      <div class="empty-view">
        <div class="empty-icon">⚠️</div>
        <div class="empty-title">Could not load history</div>
        <div class="empty-desc">Make sure the backend is running</div>
      </div>`;
  }
}

function renderHistory(items, container) {
  if (!items || !items.length) {
    container.innerHTML = `
      <div class="empty-view">
        <div class="empty-icon">🕘</div>
        <div class="empty-title">No history yet</div>
        <div class="empty-desc">Tests you run will appear here automatically</div>
      </div>`;
    return;
  }

  const rows = items.map((item, idx) => {
    const sev   = (item.severity || 'low').toLowerCase();
    const score = item.quality_score ?? '—';
    const clr   = typeof score === 'number' ? scoreColor(score) : 'var(--muted)';
    const date  = new Date(item.created_at).toLocaleString();
    return `
      <div class="history-row clickable" data-idx="${idx}">
        <span class="hist-method">${esc(item.method)}</span>
        <span class="hist-url" title="${esc(item.url)}">${esc(item.url)}</span>
        <span class="hist-date">${date}</span>
        <span class="hist-score" style="color:${clr}">${score}</span>
        <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
      </div>`;
  }).join('');

  container.innerHTML = `
    <div class="history-wrap">
      <div class="history-row header">
        <span>Method</span>
        <span>URL</span>
        <span>Date</span>
        <span>Score</span>
        <span>Severity</span>
      </div>
      ${rows}
    </div>`;
}

/* ─────────────────────────────────────────
   History Detail panel
   ───────────────────────────────────────── */
function showHistoryDetail(item) {
  const sev   = (item.severity || 'low').toLowerCase();
  const score = item.quality_score ?? null;
  const clr   = score !== null ? scoreColor(score) : 'var(--muted)';

  document.getElementById('detail-body').innerHTML = `

    <div class="detail-row">
      <div class="detail-label">Endpoint URL</div>
      <div class="detail-mono">${esc(item.url)}</div>
    </div>

    <div class="detail-row">
      <div class="detail-label">HTTP Method</div>
      <span class="hist-method">${esc(item.method)}</span>
    </div>

    <div class="detail-row">
      <div class="detail-label">Quality Score</div>
      <div class="detail-score" style="color:${clr}">${score ?? '—'}</div>
      ${score !== null ? `
        <div class="score-bar-wrap" style="margin-top:10px">
          <div class="score-bar-fill" style="width:${score}%;background:${clr}"></div>
        </div>` : ''}
    </div>

    <div class="detail-row">
      <div class="detail-label">Severity</div>
      <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
    </div>

    <div class="detail-row">
      <div class="detail-label">Total Tests Run</div>
      <div class="detail-val">${item.total_tests ?? '—'}</div>
    </div>

    <div class="detail-row">
      <div class="detail-label">Executed At</div>
      <div class="detail-val">${new Date(item.created_at).toLocaleString()}</div>
    </div>

  `;

  document.getElementById('detail-overlay').classList.add('open');
  document.getElementById('detail-panel').classList.add('open');
}

function closeDetail() {
  document.getElementById('detail-overlay').classList.remove('open');
  document.getElementById('detail-panel').classList.remove('open');
}

/* ─────────────────────────────────────────
   Helpers
   ───────────────────────────────────────── */
function scoreColor(pct) {
  if (pct >= 70) return 'var(--low)';
  if (pct >= 40) return 'var(--high)';
  return 'var(--critical)';
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function cap(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function setLoading(on) {
  const btn     = document.getElementById('btn-run');
  const spinner = document.getElementById('spinner');
  const text    = document.getElementById('btn-text');
  btn.disabled          = on;
  spinner.style.display = on ? 'block' : 'none';
  text.textContent      = on ? 'Running tests...' : '▶ Run AI Test';
}

function showError(msg) {
  const el = document.getElementById('error-banner');
  el.textContent   = '✕  ' + msg;
  el.style.display = 'block';
}

function hideError() {
  const el = document.getElementById('error-banner');
  if (el) el.style.display = 'none';
}

/* ─────────────────────────────────────────
   Event listeners
   ───────────────────────────────────────── */

// Sidebar navigation
document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', () => switchView(el.dataset.view));
});

// Run test button
document.getElementById('btn-run').addEventListener('click', runTest);

// "Go to Run Test" button in empty results state
document.getElementById('go-run-test')?.addEventListener('click', () => switchView('run-test'));

// History row click — event delegation
document.getElementById('history-content').addEventListener('click', e => {
  const row = e.target.closest('.history-row.clickable');
  if (!row) return;
  const idx = parseInt(row.dataset.idx, 10);
  if (!isNaN(idx) && historyItems[idx]) showHistoryDetail(historyItems[idx]);
});

// Detail panel close
document.getElementById('btn-close-detail').addEventListener('click', closeDetail);
document.getElementById('detail-overlay').addEventListener('click', closeDetail);

// Escape key closes detail
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDetail();
});

/* ─────────────────────────────────────────
   Init
   ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  switchView('run-test');
});

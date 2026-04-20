/* ─────────────────────────────────────────
   API Sentinel — Frontend Logic
   ───────────────────────────────────────── */

const state = {
  lastResult:   null,
  historyItems: [],
  historyPage:  1,
  historyMeta:  null,
};

const VIEW_TITLES = {
  'run-test': 'Run Test',
  'results':  'Results',
  'history':  'History',
};

/* ─────────────────────────────────────────
   Navigation
   ───────────────────────────────────────── */
function switchView(viewId) {
  document.querySelectorAll('.nav-btn').forEach(el => {
    el.classList.toggle('active', el.dataset.view === viewId);
  });
  document.querySelectorAll('.view').forEach(el => {
    el.classList.toggle('active', el.id === `view-${viewId}`);
  });
  document.getElementById('topbar-title').textContent = VIEW_TITLES[viewId] ?? viewId;
  renderTopbarActions(viewId);
  if (viewId === 'history') loadHistory(1);
}

function renderTopbarActions(viewId) {
  const el = document.getElementById('topbar-right');
  if (viewId === 'results' && state.lastResult) {
    el.style.display = 'flex';
    el.innerHTML = `<button class="btn-secondary" id="btn-export">↓ Export JSON</button>`;
    document.getElementById('btn-export').addEventListener('click', downloadReport);
  } else {
    el.style.display = 'none';
    el.innerHTML = '';
  }
}

/* ─────────────────────────────────────────
   Run Test
   ───────────────────────────────────────── */
function _estimateTestCount(method, payload) {
  if (method === 'GET' && !payload) return '1–2';
  const keys = payload ? Object.keys(payload).length : 0;
  return keys > 1 ? '4' : '3';
}

async function runTest() {
  const url       = document.getElementById('url').value.trim();
  const method    = document.getElementById('method').value;
  const rawBody   = document.getElementById('payload').value.trim();
  const rawHdrs   = document.getElementById('headers').value.trim();
  const authToken = document.getElementById('auth-token').value.trim();

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

  // Auth token shortcut — overrides any Authorization already in headers
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const testCount = _estimateTestCount(method, payload);
  setLoading(true, testCount);

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
    state.lastResult = data;

    renderResults(data);
    switchView('results');

    const pill = document.getElementById('results-pill');
    pill.textContent = data.quality_score ?? '—';
    pill.style.display = 'inline';

    toast('Test complete', 'success');

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

  const score   = quality_score ?? 0;
  const pct     = Math.min(100, Math.max(0, score));
  const sev     = (severity || 'low').toLowerCase();
  const clr     = scoreColor(pct);
  const passed  = results.filter(r => r.status_code >= 200 && r.status_code < 300).length;
  const failed  = total_tests - passed;

  const sevClr  = sev === 'critical' ? 'var(--red)' : sev === 'high' ? 'var(--orange)' : 'var(--green)';
  const kpiSev  = sev === 'critical' ? 'kpi-bad' : sev === 'high' ? 'kpi-warn' : 'kpi-ok';
  const kpiFail = failed > 0 ? 'kpi-bad' : 'kpi-neutral';

  document.getElementById('results-inner').innerHTML = `

    <div class="kpi-grid">

      <div class="kpi-card kpi-score">
        <div class="kpi-label">Quality Score</div>
        <div class="kpi-value" style="color:${clr}">${score}</div>
        <div class="score-bar">
          <div class="score-bar-fill" style="width:${pct}%;background:${clr}"></div>
        </div>
      </div>

      <div class="kpi-card ${kpiSev}">
        <div class="kpi-label">Severity</div>
        <div class="kpi-value" style="font-size:26px;color:${sevClr};margin-bottom:10px">${cap(sev)}</div>
        <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
      </div>

      <div class="kpi-card kpi-ok">
        <div class="kpi-label">Tests Passed</div>
        <div class="kpi-value" style="color:var(--green)">${passed}</div>
        <div class="kpi-sub">of ${total_tests} total</div>
      </div>

      <div class="kpi-card ${kpiFail}">
        <div class="kpi-label">Tests Failed</div>
        <div class="kpi-value" style="color:${failed > 0 ? 'var(--red)' : 'var(--text-3)'}">${failed}</div>
        <div class="kpi-sub">of ${total_tests} total</div>
      </div>

    </div>

    <div class="two-col" style="margin-bottom:16px">

      <div class="card">
        <div class="card-hd">
          <span class="card-title">⚠ Detected Issues</span>
          <span class="card-hint">${issues_detected.length} issue${issues_detected.length !== 1 ? 's' : ''} found</span>
        </div>
        <div class="card-bd">
          ${tagList(issues_detected, 'issue')}
        </div>
      </div>

      <div class="card">
        <div class="card-hd">
          <span class="card-title">✦ AI Insights</span>
          <span class="card-hint">${ai_insights.length} recommendation${ai_insights.length !== 1 ? 's' : ''}</span>
        </div>
        <div class="card-bd">
          ${tagList(ai_insights, 'insight')}
        </div>
      </div>

    </div>

    <div class="card">
      <div class="card-hd">
        <span class="card-title">📋 Test Results</span>
        <span class="card-hint">${total_tests} tests executed in parallel</span>
      </div>
      <div class="card-bd" style="padding:0">
        <div class="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Test Name</th>
                <th>Status</th>
                <th>Time</th>
                <th>Body Preview</th>
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
    const msg = type === 'issue'
      ? 'Sin problemas detectados · No issues detected'
      : 'Sin recomendaciones · No insights available';
    return `<p class="no-items">${msg}</p>`;
  }
  return `<div class="item-list">
    ${items.map(i => `
      <div class="list-item">
        <div class="dot dot-${type}"></div>
        <span>${esc(i)}</span>
      </div>`).join('')}
  </div>`;
}

function resultRow(r, idx) {
  const code   = r.status_code;
  const cls    = !code ? 'c-err' : code < 300 ? 'c-2xx' : code < 500 ? 'c-4xx' : 'c-5xx';
  const codeEl = code
    ? `<span class="code-badge ${cls}">${code}</span>`
    : `<span class="code-badge c-err">—</span>`;
  const timeEl = r.response_time != null
    ? `<span class="mono-sm" style="color:var(--text-3)">${(r.response_time * 1000).toFixed(0)} ms</span>`
    : `<span style="color:var(--text-3)">—</span>`;
  const bodySnippet = r.response_body
    ? r.response_body.slice(0, 80).replace(/\s+/g, ' ')
    : null;
  const bodyEl = bodySnippet
    ? `<span class="mono-sm" style="color:var(--text-2);max-width:200px;display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(r.response_body)}">${esc(bodySnippet)}…</span>`
    : `<span style="color:var(--text-3)">—</span>`;
  const errEl = r.error
    ? `<span class="mono-sm" style="color:var(--red)">${esc(r.error)}</span>`
    : `<span style="color:var(--text-3)">—</span>`;

  return `<tr>
    <td style="color:var(--text-3);font-size:12px">${idx + 1}</td>
    <td class="mono-sm">${esc(r.test_name || '—')}</td>
    <td>${codeEl}</td>
    <td>${timeEl}</td>
    <td>${bodyEl}</td>
    <td>${errEl}</td>
  </tr>`;
}

/* ─────────────────────────────────────────
   Export
   ───────────────────────────────────────── */
function downloadReport() {
  if (!state.lastResult) return;
  const blob = new Blob([JSON.stringify(state.lastResult, null, 2)], { type: 'application/json' });
  const a = Object.assign(document.createElement('a'), {
    href:     URL.createObjectURL(blob),
    download: `sentinel-report-${Date.now()}.json`,
  });
  a.click();
  URL.revokeObjectURL(a.href);
  toast('Report downloaded', 'success');
}

/* ─────────────────────────────────────────
   History + Pagination
   ───────────────────────────────────────── */
async function loadHistory(page = 1) {
  state.historyPage = page;
  const container = document.getElementById('history-inner');
  container.innerHTML = `<div class="loading-row">Loading history…</div>`;

  try {
    const res = await fetch(`/history?page=${page}&limit=20`);
    if (!res.ok) throw new Error('fetch failed');
    const data = await res.json();
    state.historyItems = data.items;
    state.historyMeta  = data;
    renderHistory(data);
  } catch {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p class="empty-title">Could not load history</p>
        <p class="empty-desc">Make sure the backend is running</p>
      </div>`;
  }
}

function renderHistory(data) {
  const container = document.getElementById('history-inner');
  const { items, total, page, total_pages } = data;

  if (!items || !items.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🕘</div>
        <p class="empty-title">No history yet</p>
        <p class="empty-desc">Tests you run will appear here automatically</p>
      </div>`;
    return;
  }

  const rows = items.map((item, idx) => {
    const sev   = (item.severity || 'low').toLowerCase();
    const score = item.quality_score ?? '—';
    const clr   = typeof score === 'number' ? scoreColor(score) : 'var(--text-3)';
    const date  = new Date(item.created_at).toLocaleString();
    const bad   = typeof score === 'number' && score < 50 ? ' score-bad' : '';
    return `
      <div class="hist-row hist-data${bad}" data-idx="${idx}">
        <span class="hist-url" title="${esc(item.url)}">${esc(item.url)}</span>
        <span class="method-tag">${esc(item.method)}</span>
        <span class="hist-date">${date}</span>
        <span class="hist-score" style="color:${clr}">${score}</span>
        <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
      </div>`;
  }).join('');

  const pagination = total_pages > 1 ? _renderPagination(page, total_pages, total) : '';

  container.innerHTML = `
    <div class="hist-table">
      <div class="hist-row hist-hd">
        <span>URL</span>
        <span>Method</span>
        <span>Date</span>
        <span>Score</span>
        <span>Severity</span>
      </div>
      ${rows}
    </div>
    ${pagination}`;
}

function _renderPagination(page, totalPages, total) {
  const start = Math.max(1, page - 2);
  const end   = Math.min(totalPages, page + 2);

  let pageButtons = '';
  for (let p = start; p <= end; p++) {
    pageButtons += `<button class="btn-page${p === page ? ' active' : ''}" data-page="${p}">${p}</button>`;
  }

  return `
    <div class="pagination">
      <span class="pagination-info">${total} test${total !== 1 ? 's' : ''} · page ${page} of ${totalPages}</span>
      <div class="pagination-controls">
        <button class="btn-page" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>‹</button>
        ${pageButtons}
        <button class="btn-page" data-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>›</button>
      </div>
    </div>`;
}

async function loadHistoryItem(idx) {
  const item = state.historyItems[idx];
  if (!item) return;

  try {
    const res = await fetch(`/history/${item.id}`);
    if (!res.ok) throw new Error('Not found');
    const data = await res.json();
    state.lastResult = data;
    renderResults(data);
    switchView('results');

    const pill = document.getElementById('results-pill');
    pill.textContent = data.quality_score ?? '—';
    pill.style.display = 'inline';

    toast('History item loaded', 'info');
  } catch {
    toast('Could not load this history item', 'error');
  }
}

/* ─────────────────────────────────────────
   Toasts
   ───────────────────────────────────────── */
const TOAST_ICONS = { success: '✓', error: '✕', info: 'ℹ' };

function toast(msg, type = 'info') {
  const container = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-icon">${TOAST_ICONS[type] ?? 'ℹ'}</span><span>${esc(msg)}</span>`;
  container.appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.replace('show', 'hide');
    setTimeout(() => el.remove(), 250);
  }, 3000);
}

/* ─────────────────────────────────────────
   Helpers
   ───────────────────────────────────────── */
function scoreColor(pct) {
  if (pct >= 70) return 'var(--green)';
  if (pct >= 40) return 'var(--orange)';
  return 'var(--red)';
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

function setLoading(on, testCount = '') {
  const btn     = document.getElementById('btn-run');
  const spinner = document.getElementById('spinner');
  const text    = document.getElementById('btn-text');
  btn.disabled          = on;
  spinner.style.display = on ? 'inline' : 'none';
  text.textContent      = on
    ? `Running ${testCount} tests in parallel…`
    : '▶  Run AI Test';
}

function showError(msg) {
  document.getElementById('inline-error-text').textContent = msg;
  document.getElementById('inline-error').style.display = 'flex';
}

function hideError() {
  document.getElementById('inline-error').style.display = 'none';
}

/* ─────────────────────────────────────────
   Saved Configs
   ───────────────────────────────────────── */
async function loadConfigs() {
  try {
    const res = await fetch('/configs');
    if (!res.ok) return;
    const configs = await res.json();
    _renderConfigsSelect(configs);
  } catch { /* silent — feature degrades gracefully */ }
}

function _renderConfigsSelect(configs) {
  const sel = document.getElementById('configs-select');
  sel.innerHTML = '<option value="">— Load a saved config —</option>';
  configs.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.name;
    opt.dataset.config = JSON.stringify(c);
    sel.appendChild(opt);
  });
}

function applyConfig(config) {
  document.getElementById('url').value     = config.url    ?? '';
  document.getElementById('method').value  = config.method ?? 'GET';
  document.getElementById('payload').value = config.payload
    ? JSON.stringify(config.payload, null, 2) : '';
  document.getElementById('headers').value = config.headers
    ? JSON.stringify(config.headers, null, 2) : '';
  toast(`Config "${config.name}" loaded`, 'success');
}

async function saveCurrentConfig() {
  const name = document.getElementById('config-name').value.trim();
  if (!name) { toast('Enter a config name first', 'error'); return; }

  const url    = document.getElementById('url').value.trim();
  const method = document.getElementById('method').value;
  if (!url) { toast('Enter a URL before saving', 'error'); return; }

  const rawBody = document.getElementById('payload').value.trim();
  const rawHdrs = document.getElementById('headers').value.trim();

  let payload = null;
  if (rawBody) {
    try { payload = JSON.parse(rawBody); }
    catch { toast('Invalid JSON in payload', 'error'); return; }
  }
  let headers = null;
  if (rawHdrs) {
    try { headers = JSON.parse(rawHdrs); }
    catch { toast('Invalid JSON in headers', 'error'); return; }
  }

  try {
    const res = await fetch('/configs', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name, url, method, payload, headers }),
    });
    if (res.status === 409) { toast(`Config "${name}" already exists`, 'error'); return; }
    if (!res.ok) throw new Error('Server error');

    document.getElementById('config-name').value = '';
    await loadConfigs();
    toast(`Config "${name}" saved`, 'success');
  } catch (e) {
    toast(e.message || 'Could not save config', 'error');
  }
}

/* ─────────────────────────────────────────
   Init
   ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.nav-btn').forEach(el => {
    el.addEventListener('click', () => switchView(el.dataset.view));
  });

  document.getElementById('btn-run').addEventListener('click', runTest);

  document.getElementById('go-run-from-results')
    ?.addEventListener('click', () => switchView('run-test'));

  // History: clicks en filas y en botones de paginación (delegación)
  document.getElementById('history-inner').addEventListener('click', e => {
    const row = e.target.closest('.hist-row.hist-data');
    if (row) {
      const idx = parseInt(row.dataset.idx, 10);
      if (!isNaN(idx)) loadHistoryItem(idx);
      return;
    }
    const pageBtn = e.target.closest('.btn-page[data-page]');
    if (pageBtn && !pageBtn.disabled) {
      const p = parseInt(pageBtn.dataset.page, 10);
      if (!isNaN(p)) loadHistory(p);
    }
  });

  // Saved configs
  document.getElementById('configs-select').addEventListener('change', e => {
    const opt = e.target.selectedOptions[0];
    if (!opt || !opt.dataset.config) return;
    try { applyConfig(JSON.parse(opt.dataset.config)); }
    catch { toast('Could not parse config', 'error'); }
  });

  document.getElementById('btn-save-config').addEventListener('click', saveCurrentConfig);

  loadConfigs();
  switchView('run-test');
});

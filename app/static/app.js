/* ─────────────────────────────────────────
   API Sentinel — Frontend Logic
   ───────────────────────────────────────── */

const state = {
  lastResult:     null,
  historyItems:   [],
  historyPage:    1,
  historyMeta:    null,
  historyFilters: {},
  lastSchedules:  null,
  lang: localStorage.getItem('sentinel-lang') || 'en',
};

/* ─────────────────────────────────────────
   i18n
   ───────────────────────────────────────── */
const TRANSLATIONS = {
  en: {
    'nav.run-test': 'Run Test',
    'nav.results':  'Results',
    'nav.history':  'History',
    'run.title':         'Configure Test',
    'run.subtitle':      'Enter your API endpoint and run an automated quality analysis',
    'run.saved-configs': 'Saved Configs',
    'run.load-config':   '— Load a saved config —',
    'run.config-name-ph':'Config name…',
    'run.save-config':   'Save Config',
    'run.request':       'Request',
    'run.base-url-label':'Base URL',
    'run.base-url-hint': 'optional — prepended when URL starts with /',
    'run.base-url-ph':   'https://api.example.com',
    'run.url-label':     'Endpoint URL',
    'run.url-ph':        '/endpoint  or  https://api.example.com/endpoint',
    'run.method-label':  'Method',
    'run.payload':       'Payload',
    'run.payload-hint':  'JSON · for POST/PUT/PATCH',
    'run.schema-title':  'Expected Response Schema',
    'run.schema-hint':   'optional',
    'run.add-field':     '+ Add field',
    'run.auth-headers':  'Auth Headers',
    'run.auth-hint':     'JSON · optional',
    'run.bearer-label':  'Bearer Token (shortcut)',
    'run.custom-title':  'Custom Test Cases',
    'run.custom-hint':   'optional · run alongside auto-generated tests',
    'run.add-case':      '+ Add test case',
    'run.btn-run':       '▶  Run AI Test',
    'results.empty-title': 'No results yet',
    'results.empty-desc':  'Run a test to see your API quality analysis here',
    'results.go-run':      'Go to Run Test',
    'history.title':       'Test History',
    'history.subtitle':    'Click any row to load the full result into the Results view',
    'history.filter-url-ph': 'Filter by URL…',
    'history.apply':       'Apply',
    'history.clear':       'Clear',
    'history.empty-title': 'No tests run yet',
    'history.empty-desc':  'Your test history will appear here automatically',
    'filter.all':      'All severities',
    'filter.low':      'Low',
    'filter.high':     'High',
    'filter.critical': 'Critical',
    'schedules.title':       'Scheduled Tests',
    'schedules.subtitle':    'Run tests automatically on a recurring schedule',
    'schedules.new':         'New Schedule',
    'schedules.name-label':  'Name',
    'schedules.name-ph':     'e.g. Check prod API every hour',
    'schedules.config-label':'Saved Config',
    'schedules.config-ph':   '— Select a saved config —',
    'schedules.cron-label':  'Cron Expression',
    'schedules.add-btn':     '+ Add Schedule',
    'schedules.presets':     'Presets:',
    'schedules.p5m':         'every 5 min',
    'schedules.p30m':        'every 30 min',
    'schedules.p1h':         'every hour',
    'schedules.p6h':         'every 6 h',
    'schedules.p9':          'daily 9 am',
    'schedules.empty-title': 'No schedules yet',
    'schedules.empty-desc':  'Create one above to start running tests automatically',
    // JS-rendered strings — schedules
    'js.sched-tbl-name':    'Name',
    'js.sched-tbl-config':  'Config',
    'js.sched-tbl-cron':    'Cron',
    'js.sched-tbl-status':  'Status',
    'js.sched-tbl-lastrun': 'Last run',
    'js.sched-enabled':     'Enabled',
    'js.sched-disabled':    'Disabled',
    'js.sched-never':       'Never',
    'js.sched-deleted':     'Schedule deleted',
    'js.sched-created':     'Schedule created',
    'js.sched-toggled-on':  'Schedule enabled',
    'js.sched-toggled-off': 'Schedule disabled',
    // JS-rendered strings
    'js.kpi-score':    'Quality Score',
    'js.kpi-severity': 'Severity',
    'js.kpi-passed':   'Tests Passed',
    'js.kpi-failed':   'Tests Failed',
    'js.kpi-of':       'of',
    'js.kpi-total':    'total',
    'js.parallel':     'tests executed in parallel',
    'js.issues-card':  '⚠ Detected Issues',
    'js.insights-card':'✦ AI Insights',
    'js.results-card': '📋 Test Results',
    'js.tbl-name':     'Test Name',
    'js.tbl-status':   'Status',
    'js.tbl-time':     'Time',
    'js.tbl-body':     'Body Preview',
    'js.tbl-error':    'Error',
    'js.no-issues':    'No issues detected',
    'js.no-insights':  'No insights available',
    'js.issue':        'issue',
    'js.issues':       'issues',
    'js.found':        'found',
    'js.recommendation':  'recommendation',
    'js.recommendations': 'recommendations',
    'js.export-json':  '↓ Export JSON',
    'js.export-pdf':   '🖨 Export PDF',
    'js.loading-hist': 'Loading history…',
    'js.tbl-url':      'URL',
    'js.tbl-method':   'Method',
    'js.tbl-date':     'Date',
    'js.tbl-score':    'Score',
    'js.tbl-severity': 'Severity',
    'js.hist-err-title': 'Could not load history',
    'js.hist-err-desc':  'Make sure the backend is running',
    'js.no-hist':        'No history yet',
    'js.no-hist-desc':   'Tests you run will appear here automatically',
    'js.page': 'page',
    'js.of':   'of',
    'js.running':       'Running',
    'js.tests-parallel':'tests in parallel…',
    'js.btn-idle':      '▶  Run AI Test',
  },
  es: {
    'nav.run-test': 'Ejecutar Test',
    'nav.results':  'Resultados',
    'nav.history':  'Historial',
    'run.title':         'Configurar Test',
    'run.subtitle':      'Ingresá tu endpoint y ejecutá un análisis de calidad automatizado',
    'run.saved-configs': 'Configs Guardadas',
    'run.load-config':   '— Cargar una config guardada —',
    'run.config-name-ph':'Nombre de config…',
    'run.save-config':   'Guardar Config',
    'run.request':       'Solicitud',
    'run.base-url-label':'URL Base',
    'run.base-url-hint': 'opcional — se antepone si la URL empieza con /',
    'run.base-url-ph':   'https://api.ejemplo.com',
    'run.url-label':     'URL del Endpoint',
    'run.url-ph':        '/endpoint  o  https://api.ejemplo.com/endpoint',
    'run.method-label':  'Método',
    'run.payload':       'Payload',
    'run.payload-hint':  'JSON · para POST/PUT/PATCH',
    'run.schema-title':  'Schema de Respuesta Esperado',
    'run.schema-hint':   'opcional',
    'run.add-field':     '+ Agregar campo',
    'run.auth-headers':  'Cabeceras de Autenticación',
    'run.auth-hint':     'JSON · opcional',
    'run.bearer-label':  'Bearer Token (atajo)',
    'run.custom-title':  'Casos de Test Personalizados',
    'run.custom-hint':   'opcional · se ejecutan junto a los tests auto-generados',
    'run.add-case':      '+ Agregar caso',
    'run.btn-run':       '▶  Ejecutar Test IA',
    'results.empty-title': 'Sin resultados aún',
    'results.empty-desc':  'Ejecutá un test para ver el análisis de calidad aquí',
    'results.go-run':      'Ir a Ejecutar Test',
    'history.title':       'Historial de Tests',
    'history.subtitle':    'Hacé clic en cualquier fila para cargar el resultado completo',
    'history.filter-url-ph': 'Filtrar por URL…',
    'history.apply':       'Aplicar',
    'history.clear':       'Limpiar',
    'history.empty-title': 'Sin tests ejecutados aún',
    'history.empty-desc':  'Tu historial aparecerá aquí automáticamente',
    'filter.all':      'Todas las severidades',
    'filter.low':      'Bajo',
    'filter.high':     'Alto',
    'filter.critical': 'Crítico',
    'schedules.title':       'Tests Programados',
    'schedules.subtitle':    'Ejecutá tests automáticamente con un schedule recurrente',
    'schedules.new':         'Nuevo Schedule',
    'schedules.name-label':  'Nombre',
    'schedules.name-ph':     'ej. Verificar API prod cada hora',
    'schedules.config-label':'Config Guardada',
    'schedules.config-ph':   '— Seleccioná una config guardada —',
    'schedules.cron-label':  'Expresión Cron',
    'schedules.add-btn':     '+ Agregar Schedule',
    'schedules.presets':     'Presets:',
    'schedules.p5m':         'cada 5 min',
    'schedules.p30m':        'cada 30 min',
    'schedules.p1h':         'cada hora',
    'schedules.p6h':         'cada 6 h',
    'schedules.p9':          'diario 9 am',
    'schedules.empty-title': 'Sin schedules aún',
    'schedules.empty-desc':  'Creá uno arriba para empezar a ejecutar tests automáticamente',
    // JS-rendered strings — schedules
    'js.sched-tbl-name':    'Nombre',
    'js.sched-tbl-config':  'Config',
    'js.sched-tbl-cron':    'Cron',
    'js.sched-tbl-status':  'Estado',
    'js.sched-tbl-lastrun': 'Último run',
    'js.sched-enabled':     'Habilitado',
    'js.sched-disabled':    'Deshabilitado',
    'js.sched-never':       'Nunca',
    'js.sched-deleted':     'Schedule eliminado',
    'js.sched-created':     'Schedule creado',
    'js.sched-toggled-on':  'Schedule habilitado',
    'js.sched-toggled-off': 'Schedule deshabilitado',
    // JS-rendered strings
    'js.kpi-score':    'Score de Calidad',
    'js.kpi-severity': 'Severidad',
    'js.kpi-passed':   'Tests Pasados',
    'js.kpi-failed':   'Tests Fallidos',
    'js.kpi-of':       'de',
    'js.kpi-total':    'total',
    'js.parallel':     'tests ejecutados en paralelo',
    'js.issues-card':  '⚠ Problemas Detectados',
    'js.insights-card':'✦ Insights de IA',
    'js.results-card': '📋 Resultados de Tests',
    'js.tbl-name':     'Nombre de Test',
    'js.tbl-status':   'Estado',
    'js.tbl-time':     'Tiempo',
    'js.tbl-body':     'Vista Previa del Body',
    'js.tbl-error':    'Error',
    'js.no-issues':    'Sin problemas detectados',
    'js.no-insights':  'Sin recomendaciones',
    'js.issue':        'problema',
    'js.issues':       'problemas',
    'js.found':        'encontrado/s',
    'js.recommendation':  'recomendación',
    'js.recommendations': 'recomendaciones',
    'js.export-json':  '↓ Exportar JSON',
    'js.export-pdf':   '🖨 Exportar PDF',
    'js.loading-hist': 'Cargando historial…',
    'js.tbl-url':      'URL',
    'js.tbl-method':   'Método',
    'js.tbl-date':     'Fecha',
    'js.tbl-score':    'Score',
    'js.tbl-severity': 'Severidad',
    'js.hist-err-title': 'No se pudo cargar el historial',
    'js.hist-err-desc':  'Asegurate que el backend esté corriendo',
    'js.no-hist':        'Sin historial aún',
    'js.no-hist-desc':   'Los tests que ejecutes aparecerán aquí automáticamente',
    'js.page': 'página',
    'js.of':   'de',
    'js.running':       'Ejecutando',
    'js.tests-parallel':'tests en paralelo…',
    'js.btn-idle':      '▶  Ejecutar Test IA',
  },
};

function t(key) {
  return TRANSLATIONS[state.lang]?.[key] ?? TRANSLATIONS.en[key] ?? key;
}

function applyTranslations() {
  document.getElementById('html-root').lang = state.lang;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    const val = t(key);
    if (val !== undefined) el.textContent = val;
  });

  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.dataset.i18nPh;
    const val = t(key);
    if (val !== undefined) el.placeholder = val;
  });

  const btn = document.getElementById('btn-lang');
  if (btn) btn.textContent = state.lang === 'en' ? 'ES' : 'EN';

  // Keep btn-text in sync when not loading
  const btnText = document.getElementById('btn-text');
  if (btnText && !document.getElementById('btn-run').disabled) {
    btnText.textContent = t('run.btn-run');
  }
}

function setLang(lang) {
  state.lang = lang;
  localStorage.setItem('sentinel-lang', lang);
  applyTranslations();
  // Re-render active dynamic view so table headers / empty states update
  const active = document.querySelector('.nav-btn.active');
  if (active) {
    const view = active.dataset.view;
    document.getElementById('topbar-title').textContent = t(`nav.${view}`);
    renderTopbarActions(view);
    if (view === 'results'   && state.lastResult)   renderResults(state.lastResult);
    if (view === 'history'   && state.historyMeta)  renderHistory(state.historyMeta);
    if (view === 'schedules' && state.lastSchedules) renderSchedules(state.lastSchedules);
  }
}

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
  document.getElementById('topbar-title').textContent = t(`nav.${viewId}`);
  renderTopbarActions(viewId);
  if (viewId === 'history')   loadHistory(1);
  if (viewId === 'schedules') { loadSchedules(); _populateSchedConfigSelect(); }
}

function renderTopbarActions(viewId) {
  const el = document.getElementById('topbar-right');
  if (viewId === 'results' && state.lastResult) {
    el.style.display = 'flex';
    el.innerHTML = `
      <button class="btn-secondary" id="btn-export-json">${t('js.export-json')}</button>
      <button class="btn-secondary" id="btn-export-pdf">${t('js.export-pdf')}</button>
    `;
    document.getElementById('btn-export-json').addEventListener('click', downloadReport);
    document.getElementById('btn-export-pdf').addEventListener('click', downloadPdfReport);
  } else {
    el.style.display = 'none';
    el.innerHTML = '';
  }
}

/* ─────────────────────────────────────────
   Run Test
   ───────────────────────────────────────── */
function _estimateTestCount(method, payload) {
  if (method === 'DELETE') return '1';
  if (method === 'GET' && !payload) return '1–2';
  const keys = payload ? Object.keys(payload).length : 0;
  return keys > 1 ? '4' : '3';
}

async function runTest() {
  const rawUrl    = document.getElementById('url').value.trim();
  const baseUrl   = document.getElementById('base-url').value.trim();
  const method    = document.getElementById('method').value;
  const rawBody   = document.getElementById('payload').value.trim();
  const rawHdrs   = document.getElementById('headers').value.trim();
  const authToken = document.getElementById('auth-token').value.trim();

  hideError();
  if (!rawUrl) { showError('Please enter an endpoint URL.'); return; }

  const url = baseUrl && rawUrl.startsWith('/') ? baseUrl.replace(/\/$/, '') + rawUrl : rawUrl;

  let payload = null;
  if (method !== 'GET' && method !== 'DELETE' && rawBody) {
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
    const expected_schema = buildExpectedSchema();
    const custom_cases    = buildCustomCases();
    const auth_config     = buildOAuthConfig();
    if (custom_cases === null && document.querySelectorAll('.custom-case-row').length > 0) {
      setLoading(false);
      return; // buildCustomCases ya mostró el toast de error
    }
    if (auth_config === undefined) {
      setLoading(false);
      return;
    }

    const res = await fetch('/run-test', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ url, method, payload, headers, auth_config, expected_schema, custom_cases }),
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
  const latencyStats = renderLatencyStats(data.latency_stats);

  const score   = quality_score ?? 0;
  const pct     = Math.min(100, Math.max(0, score));
  const sev     = (severity || 'low').toLowerCase();
  const clr     = scoreColor(pct);

  // Usar summary del backend si está disponible (semántica correcta por contrato de test)
  const passed  = data.summary ? data.summary.passed  : results.filter(r => r.status_code >= 200 && r.status_code < 300).length;
  const failed  = data.summary ? data.summary.failed  : total_tests - passed;

  const sevClr = sev === 'critical' ? 'var(--red)'
               : sev === 'high'     ? 'var(--orange)'
               : sev === 'medium'   ? 'var(--yellow)'
               : 'var(--green)';
  const kpiSev = sev === 'critical' ? 'kpi-bad'
               : sev === 'high'     ? 'kpi-warn'
               : sev === 'medium'   ? 'kpi-medium'
               : 'kpi-ok';
  const kpiFail = failed > 0 ? 'kpi-bad' : 'kpi-neutral';

  const issueCount  = issues_detected.length;
  const issueLabel  = issueCount !== 1 ? t('js.issues') : t('js.issue');
  const insightCount = ai_insights.length;
  const insightLabel = insightCount !== 1 ? t('js.recommendations') : t('js.recommendation');

  document.getElementById('results-inner').innerHTML = `

    <div class="kpi-grid">

      <div class="kpi-card kpi-score">
        <div class="kpi-label">${t('js.kpi-score')}</div>
        <div class="kpi-value" style="color:${clr}">${score}</div>
        <div class="score-bar">
          <div class="score-bar-fill" style="width:${pct}%;background:${clr}"></div>
        </div>
      </div>

      <div class="kpi-card ${kpiSev}">
        <div class="kpi-label">${t('js.kpi-severity')}</div>
        <div class="kpi-value" style="font-size:26px;color:${sevClr};margin-bottom:10px">${cap(sev)}</div>
        <span class="badge badge-${sev}">${sev.toUpperCase()}</span>
      </div>

      <div class="kpi-card kpi-ok">
        <div class="kpi-label">${t('js.kpi-passed')}</div>
        <div class="kpi-value" style="color:var(--green)">${passed}</div>
        <div class="kpi-sub">${t('js.kpi-of')} ${total_tests} ${t('js.kpi-total')}</div>
      </div>

      <div class="kpi-card ${kpiFail}">
        <div class="kpi-label">${t('js.kpi-failed')}</div>
        <div class="kpi-value" style="color:${failed > 0 ? 'var(--red)' : 'var(--text-3)'}">${failed}</div>
        <div class="kpi-sub">${t('js.kpi-of')} ${total_tests} ${t('js.kpi-total')}</div>
      </div>

    </div>

    <div class="two-col" style="margin-bottom:16px">

      <div class="card">
        <div class="card-hd">
          <span class="card-title">${t('js.issues-card')}</span>
          <span class="card-hint">${issueCount} ${issueLabel} ${t('js.found')}</span>
        </div>
        <div class="card-bd">
          ${tagList(issues_detected, 'issue')}
        </div>
      </div>

      <div class="card">
        <div class="card-hd">
          <span class="card-title">⏱ Latency Percentiles</span>
          <span class="card-hint">${data.latency_stats?.sample_size ?? 0} runs</span>
        </div>
        <div class="card-bd">
          ${latencyStats}
        </div>
      </div>

    </div>

    <div class="two-col" style="margin-bottom:16px">

      <div class="card">
        <div class="card-hd">
          <span class="card-title">${t('js.insights-card')}</span>
          <span class="card-hint">${insightCount} ${insightLabel}</span>
        </div>
        <div class="card-bd">
          ${tagList(ai_insights, 'insight')}
        </div>
      </div>

    </div>

    <div class="card">
      <div class="card-hd">
        <span class="card-title">${t('js.results-card')}</span>
        <span class="card-hint">${total_tests} ${t('js.parallel')}</span>
      </div>
      <div class="card-bd" style="padding:0">
        <div class="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>${t('js.tbl-name')}</th>
                <th>${t('js.tbl-status')}</th>
                <th>${t('js.tbl-time')}</th>
                <th>${t('js.tbl-body')}</th>
                <th>${t('js.tbl-error')}</th>
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

function renderLatencyStats(stats) {
  if (!stats || !stats.sample_size) {
    return `<p class="no-items">No latency history available yet</p>`;
  }

  return `
    <div class="item-list">
      <div class="list-item"><div class="dot dot-insight"></div><span>P50: ${formatMs(stats.p50)}</span></div>
      <div class="list-item"><div class="dot dot-insight"></div><span>P95: ${formatMs(stats.p95)}</span></div>
      <div class="list-item"><div class="dot dot-insight"></div><span>P99: ${formatMs(stats.p99)}</span></div>
    </div>
  `;
}

function formatMs(value) {
  if (value == null || Number.isNaN(value)) return '—';
  return `${Math.round(value)} ms`;
}

function tagList(items, type) {
  if (!items || !items.length) {
    const msg = type === 'issue' ? t('js.no-issues') : t('js.no-insights');
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

async function downloadPdfReport() {
  if (!state.lastResult) return;

  try {
    const res = await fetch('/export-report/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.lastResult),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || 'Could not export PDF');
    }

    const blob = await res.blob();
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob),
      download: `sentinel-report-${Date.now()}.pdf`,
    });
    a.click();
    URL.revokeObjectURL(a.href);
    toast('PDF downloaded', 'success');
  } catch (e) {
    toast(e.message || 'Could not export PDF', 'error');
  }
}

/* ─────────────────────────────────────────
   History + Pagination
   ───────────────────────────────────────── */
async function loadHistory(page = 1, filters = state.historyFilters) {
  state.historyPage    = page;
  state.historyFilters = filters;
  const container = document.getElementById('history-inner');
  container.innerHTML = `<div class="loading-row">${t('js.loading-hist')}</div>`;

  try {
    const params = new URLSearchParams({ page, limit: 20 });
    if (filters.url)      params.set('url', filters.url);
    if (filters.severity) params.set('severity', filters.severity);

    const res = await fetch(`/history?${params}`);
    if (!res.ok) throw new Error('fetch failed');
    const data = await res.json();
    state.historyItems = data.items;
    state.historyMeta  = data;
    renderHistory(data);
  } catch {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p class="empty-title">${t('js.hist-err-title')}</p>
        <p class="empty-desc">${t('js.hist-err-desc')}</p>
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
        <p class="empty-title">${t('js.no-hist')}</p>
        <p class="empty-desc">${t('js.no-hist-desc')}</p>
      </div>`;
    return;
  }

  const rows = items.map((item, idx) => {
    const sev   = (item.severity || 'low').toLowerCase();
    const score = item.quality_score ?? '—';
    const clr   = typeof score === 'number' ? scoreColor(score) : 'var(--text-3)';
    const date  = new Date(item.created_at).toLocaleString();
    const bad   = typeof score === 'number' && score < 50 ? ' score-bad' : '';
    const validSev = ['low', 'medium', 'high', 'critical'].includes(sev) ? sev : 'low';
    const delta = renderDelta(item);
    return `
      <div class="hist-row hist-data${bad}" data-idx="${idx}">
        <span class="hist-url" title="${esc(item.url)}">${esc(item.url)}</span>
        <span class="method-tag">${esc(item.method)}</span>
        <span class="hist-date">${date}</span>
        <span class="hist-score" style="color:${clr}">${score}${delta}</span>
        <span class="badge badge-${validSev}">${validSev.toUpperCase()}</span>
      </div>`;
  }).join('');

  const pagination = total_pages > 1 ? _renderPagination(page, total_pages, total) : '';

  container.innerHTML = `
    <div class="hist-table">
      <div class="hist-row hist-hd">
        <span>${t('js.tbl-url')}</span>
        <span>${t('js.tbl-method')}</span>
        <span>${t('js.tbl-date')}</span>
        <span>${t('js.tbl-score')}</span>
        <span>${t('js.tbl-severity')}</span>
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
      <span class="pagination-info">${total} · ${t('js.page')} ${page} ${t('js.of')} ${totalPages}</span>
      <div class="pagination-controls">
        <button class="btn-page" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>‹</button>
        ${pageButtons}
        <button class="btn-page" data-page="${page + 1}" ${page >= totalPages ? 'disabled' : ''}>›</button>
      </div>
    </div>`;
}

function renderDelta(item) {
  if (typeof item?.delta_score !== 'number' || !item?.delta_direction) return '';

  const symbol = item.delta_direction === 'up'
    ? ' ↑'
    : item.delta_direction === 'down'
      ? ' ↓'
      : ' →';

  const sign = item.delta_score > 0 ? '+' : '';
  return ` <small style="color:var(--text-3)">${symbol}${sign}${item.delta_score}</small>`;
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
    ? `${t('js.running')} ${testCount} ${t('js.tests-parallel')}`
    : t('run.btn-run');
}

function showError(msg) {
  document.getElementById('inline-error-text').textContent = msg;
  document.getElementById('inline-error').style.display = 'flex';
}

function hideError() {
  document.getElementById('inline-error').style.display = 'none';
}

/* ─────────────────────────────────────────
   Custom Test Cases
   ───────────────────────────────────────── */
function addCustomCase() {
  const list = document.getElementById('custom-cases-list');
  const row  = document.createElement('div');
  row.className = 'custom-case-row';
  row.innerHTML = `
    <div class="custom-case-header">
      <input class="custom-case-name" type="text" placeholder="Case name (e.g. no auth)" autocomplete="off" />
      <input class="custom-case-status" type="number" min="100" max="599" placeholder="Expected status" />
      <button class="btn-remove-custom-case" title="Remove">×</button>
    </div>
    <textarea class="custom-case-payload code-area" rows="2" placeholder='{"key": "value"}  — optional payload'></textarea>
    <textarea class="custom-case-headers code-area" rows="2" placeholder='{"X-Header": "value"}  — optional headers'></textarea>
  `;
  row.querySelector('.btn-remove-custom-case').addEventListener('click', () => {
    row.remove();
    _updateCustomCasesCount();
  });
  list.appendChild(row);
  _updateCustomCasesCount();
  document.getElementById('custom-cases-section').open = true;
}

function _updateCustomCasesCount() {
  const count = document.getElementById('custom-cases-list').children.length;
  const badge = document.getElementById('custom-cases-count');
  if (count > 0) {
    badge.textContent = count;
    badge.style.display = 'inline-flex';
  } else {
    badge.style.display = 'none';
  }
}

function buildCustomCases() {
  const rows = document.querySelectorAll('.custom-case-row');
  if (!rows.length) return null;

  const cases = [];
  for (const row of rows) {
    const name = row.querySelector('.custom-case-name').value.trim();
    if (!name) continue;

    const statusRaw  = row.querySelector('.custom-case-status').value.trim();
    const payloadRaw = row.querySelector('.custom-case-payload').value.trim();
    const headersRaw = row.querySelector('.custom-case-headers').value.trim();

    let payload = null;
    if (payloadRaw) {
      try { payload = JSON.parse(payloadRaw); }
      catch { toast(`Custom case "${name}": invalid JSON in payload`, 'error'); return null; }
    }
    let headers = null;
    if (headersRaw) {
      try { headers = JSON.parse(headersRaw); }
      catch { toast(`Custom case "${name}": invalid JSON in headers`, 'error'); return null; }
    }

    cases.push({
      name,
      payload,
      headers,
      expected_status: statusRaw ? parseInt(statusRaw, 10) : null,
    });
  }
  return cases.length ? cases : null;
}

/* ─────────────────────────────────────────
   Expected Response Schema
   ───────────────────────────────────────── */
const SCHEMA_TYPES = ['string', 'int', 'float', 'bool', 'list', 'object'];

function addSchemaField(name = '', type = 'string') {
  const container = document.getElementById('schema-fields');
  const row = document.createElement('div');
  row.className = 'schema-row';
  row.innerHTML = `
    <input class="schema-field-name" type="text" placeholder="field name" value="${esc(name)}" autocomplete="off" />
    <select class="schema-field-type">
      ${SCHEMA_TYPES.map(tp => `<option value="${tp}"${tp === type ? ' selected' : ''}>${tp}</option>`).join('')}
    </select>
    <button class="btn-remove-schema-field" title="Remove">×</button>
  `;
  row.querySelector('.btn-remove-schema-field').addEventListener('click', () => row.remove());
  container.appendChild(row);
}

function buildExpectedSchema() {
  const rows = document.querySelectorAll('.schema-row');
  if (!rows.length) return null;
  const schema = {};
  rows.forEach(row => {
    const name = row.querySelector('.schema-field-name').value.trim();
    const type = row.querySelector('.schema-field-type').value;
    if (name) schema[name] = type;
  });
  return Object.keys(schema).length ? schema : null;
}

function buildOAuthConfig() {
  const tokenUrl = document.getElementById('oauth-token-url').value.trim();
  const clientId = document.getElementById('oauth-client-id').value.trim();
  const clientSecret = document.getElementById('oauth-client-secret').value.trim();
  const scope = document.getElementById('oauth-scope').value.trim();
  const audience = document.getElementById('oauth-audience').value.trim();

  const anyField = tokenUrl || clientId || clientSecret || scope || audience;
  if (!anyField) return null;

  if (!tokenUrl || !clientId || !clientSecret) {
    toast('OAuth2 requires token URL, client ID and client secret', 'error');
    return undefined;
  }

  return {
    type: 'oauth2_client_credentials',
    token_url: tokenUrl,
    client_id: clientId,
    client_secret: clientSecret,
    scope: scope || null,
    audience: audience || null,
  };
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
  sel.innerHTML = `<option value="">${t('run.load-config')}</option>`;
  configs.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.id;
    opt.textContent = c.name;
    opt.dataset.config = JSON.stringify(c);
    sel.appendChild(opt);
  });
}

function applyConfig(config) {
  document.getElementById('url').value      = config.url      ?? '';
  document.getElementById('method').value   = config.method   ?? 'GET';
  document.getElementById('base-url').value = config.base_url ?? '';
  document.getElementById('payload').value  = config.payload
    ? JSON.stringify(config.payload, null, 2) : '';
  document.getElementById('headers').value  = config.headers
    ? JSON.stringify(config.headers, null, 2) : '';
  document.getElementById('auth-token').value = '';
  document.getElementById('oauth-token-url').value = config.auth_config?.token_url ?? '';
  document.getElementById('oauth-client-id').value = config.auth_config?.client_id ?? '';
  document.getElementById('oauth-client-secret').value = config.auth_config?.client_secret ?? '';
  document.getElementById('oauth-scope').value = config.auth_config?.scope ?? '';
  document.getElementById('oauth-audience').value = config.auth_config?.audience ?? '';
  toast(`Config "${config.name}" loaded`, 'success');
}

async function deleteCurrentConfig() {
  const sel = document.getElementById('configs-select');
  const id  = sel.value;
  if (!id) return;
  const name = sel.selectedOptions[0]?.textContent ?? id;

  try {
    const res = await fetch(`/configs/${id}`, { method: 'DELETE' });
    if (res.status === 404) { toast('Config not found', 'error'); return; }
    if (!res.ok) throw new Error('Server error');

    await loadConfigs();
    document.getElementById('btn-delete-config').style.display = 'none';
    toast(`Config "${name}" deleted`, 'success');
  } catch (e) {
    toast(e.message || 'Could not delete config', 'error');
  }
}

async function saveCurrentConfig() {
  const name = document.getElementById('config-name').value.trim();
  if (!name) { toast('Enter a config name first', 'error'); return; }

  const url     = document.getElementById('url').value.trim();
  const baseUrl = document.getElementById('base-url').value.trim();
  const method  = document.getElementById('method').value;
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
  const auth_config = buildOAuthConfig();
  if (auth_config === undefined) return;

  try {
    const res = await fetch('/configs', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name, url, method, payload, headers, base_url: baseUrl || null, auth_config }),
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
   Schedules
   ───────────────────────────────────────── */
async function loadSchedules() {
  const container = document.getElementById('schedules-inner');
  try {
    const res = await fetch('/schedules');
    if (!res.ok) throw new Error('fetch failed');
    const schedules = await res.json();

    // Actualizar pill con cantidad de schedules activos
    const activeCount = schedules.filter(s => s.enabled).length;
    const pill = document.getElementById('schedules-pill');
    if (activeCount > 0) {
      pill.textContent = activeCount;
      pill.style.display = 'inline';
    } else {
      pill.style.display = 'none';
    }

    state.lastSchedules = schedules;
    renderSchedules(schedules);
  } catch {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <p class="empty-title">${t('js.hist-err-title')}</p>
        <p class="empty-desc">${t('js.hist-err-desc')}</p>
      </div>`;
  }
}

function renderSchedules(schedules) {
  const container = document.getElementById('schedules-inner');

  if (!schedules || !schedules.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🗓️</div>
        <p class="empty-title">${t('schedules.empty-title')}</p>
        <p class="empty-desc">${t('schedules.empty-desc')}</p>
      </div>`;
    return;
  }

  const rows = schedules.map(s => {
    const statusCls = s.enabled ? 'badge-low' : 'badge-disabled';
    const statusTxt = s.enabled ? t('js.sched-enabled') : t('js.sched-disabled');
    const lastRun   = s.last_run
      ? new Date(s.last_run).toLocaleString()
      : t('js.sched-never');
    const configName = esc(s.config_name || `Config #${s.config_id}`);

    return `
      <div class="sched-row" data-id="${s.id}">
        <span class="sched-name">${esc(s.name)}</span>
        <span class="sched-config">${configName}</span>
        <span class="sched-cron mono-sm">${esc(s.cron)}</span>
        <span class="badge ${statusCls}">${statusTxt}</span>
        <span class="sched-lastrun">${lastRun}</span>
        <div class="sched-actions">
          <button class="btn-sched-toggle btn-secondary ${s.enabled ? 'btn-pause' : 'btn-resume'}"
                  data-id="${s.id}" title="${s.enabled ? 'Disable' : 'Enable'}">
            ${s.enabled ? '⏸' : '▶'}
          </button>
          <button class="btn-sched-delete btn-danger" data-id="${s.id}" title="Delete">✕</button>
        </div>
      </div>`;
  }).join('');

  container.innerHTML = `
    <div class="sched-table">
      <div class="sched-row sched-hd">
        <span>${t('js.sched-tbl-name')}</span>
        <span>${t('js.sched-tbl-config')}</span>
        <span>${t('js.sched-tbl-cron')}</span>
        <span>${t('js.sched-tbl-status')}</span>
        <span>${t('js.sched-tbl-lastrun')}</span>
        <span></span>
      </div>
      ${rows}
    </div>`;
}

async function createSchedule() {
  const name     = document.getElementById('sched-name').value.trim();
  const configId = document.getElementById('sched-config').value;
  const cron     = document.getElementById('sched-cron').value.trim();

  if (!name)     { toast('Enter a schedule name', 'error'); return; }
  if (!configId) { toast('Select a saved config', 'error'); return; }
  if (!cron)     { toast('Enter a cron expression', 'error'); return; }

  try {
    const res = await fetch('/schedules', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name, config_id: parseInt(configId, 10), cron }),
    });
    if (res.status === 422) {
      const err = await res.json();
      toast(err.detail || 'Invalid cron expression', 'error');
      return;
    }
    if (res.status === 404) { toast('Config not found', 'error'); return; }
    if (!res.ok) throw new Error('Server error');

    document.getElementById('sched-name').value = '';
    document.getElementById('sched-cron').value = '';
    document.getElementById('sched-config').value = '';
    toast(t('js.sched-created'), 'success');
    await loadSchedules();
  } catch (e) {
    toast(e.message || 'Could not create schedule', 'error');
  }
}

async function toggleSchedule(scheduleId) {
  try {
    const res = await fetch(`/schedules/${scheduleId}/toggle`, { method: 'PATCH' });
    if (!res.ok) throw new Error('Server error');
    const data = await res.json();
    toast(data.enabled ? t('js.sched-toggled-on') : t('js.sched-toggled-off'), 'info');
    await loadSchedules();
  } catch (e) {
    toast(e.message || 'Could not toggle schedule', 'error');
  }
}

async function deleteSchedule(scheduleId) {
  try {
    const res = await fetch(`/schedules/${scheduleId}`, { method: 'DELETE' });
    if (res.status === 404) { toast('Schedule not found', 'error'); return; }
    if (!res.ok) throw new Error('Server error');
    toast(t('js.sched-deleted'), 'success');
    await loadSchedules();
  } catch (e) {
    toast(e.message || 'Could not delete schedule', 'error');
  }
}

async function _populateSchedConfigSelect() {
  try {
    const res = await fetch('/configs');
    if (!res.ok) return;
    const configs = await res.json();
    const sel = document.getElementById('sched-config');
    sel.innerHTML = `<option value="">${t('schedules.config-ph')}</option>`;
    configs.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      sel.appendChild(opt);
    });
  } catch { /* silencioso */ }
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
    const deleteBtn = document.getElementById('btn-delete-config');
    if (!opt || !opt.dataset.config) {
      deleteBtn.style.display = 'none';
      return;
    }
    deleteBtn.style.display = 'inline-flex';
    try { applyConfig(JSON.parse(opt.dataset.config)); }
    catch { toast('Could not parse config', 'error'); }
  });

  document.getElementById('btn-add-custom-case').addEventListener('click', addCustomCase);
  document.getElementById('btn-add-schema-field').addEventListener('click', () => addSchemaField());
  document.getElementById('btn-save-config').addEventListener('click', saveCurrentConfig);
  document.getElementById('btn-delete-config').addEventListener('click', deleteCurrentConfig);

  // History filters
  document.getElementById('btn-filter').addEventListener('click', () => {
    const url      = document.getElementById('filter-url').value.trim();
    const severity = document.getElementById('filter-severity').value;
    loadHistory(1, { url, severity });
  });

  document.getElementById('btn-filter-clear').addEventListener('click', () => {
    document.getElementById('filter-url').value      = '';
    document.getElementById('filter-severity').value = '';
    loadHistory(1, {});
  });

  // Enter en el input de filtro dispara Apply
  document.getElementById('filter-url').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('btn-filter').click();
  });

  // Language toggle
  document.getElementById('btn-lang').addEventListener('click', () => {
    setLang(state.lang === 'en' ? 'es' : 'en');
  });

  // Schedules: crear
  document.getElementById('btn-add-schedule').addEventListener('click', createSchedule);

  // Schedules: preset buttons
  document.querySelectorAll('.btn-cron-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('sched-cron').value = btn.dataset.cron;
    });
  });

  // Schedules: toggle y delete (delegación en el contenedor)
  document.getElementById('schedules-inner').addEventListener('click', e => {
    const toggleBtn = e.target.closest('.btn-sched-toggle');
    if (toggleBtn) {
      toggleSchedule(parseInt(toggleBtn.dataset.id, 10));
      return;
    }
    const deleteBtn = e.target.closest('.btn-sched-delete');
    if (deleteBtn) {
      deleteSchedule(parseInt(deleteBtn.dataset.id, 10));
    }
  });

  loadConfigs();
  applyTranslations();
  switchView('run-test');
});

/**
 * AxiomSQL Enterprise Studio - Client Application Controller
 */

let appMetadata = null;
let currentResult = null;
let lossChartInstance = null;
let benchAccuracyChartInstance = null;
let benchIterationsChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initSliders();
  initBackendToggle();
  initEventListeners();
  loadMetadata();
});

/**
 * Tab Navigation
 */
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const targetId = tab.getAttribute('data-tab');
      document.querySelectorAll('.tab-view').forEach(view => {
        view.classList.remove('active');
      });
      const targetView = document.getElementById(targetId);
      if (targetView) targetView.classList.add('active');

      if (targetId === 'tab-graph' && currentResult) {
        renderLossChart(currentResult);
      }
      if (targetId === 'tab-benchmark') {
        renderBenchmarkCharts();
      }
    });
  });
}

/**
 * Sliders sync with badges
 */
function initSliders() {
  const maxKInput = document.getElementById('maxKInput');
  const maxKVal = document.getElementById('maxKVal');
  maxKInput.addEventListener('input', () => { maxKVal.textContent = maxKInput.value; });

  const tauInput = document.getElementById('tauInput');
  const tauVal = document.getElementById('tauVal');
  tauInput.addEventListener('input', () => { tauVal.textContent = parseFloat(tauInput.value).toFixed(2); });

  const costWeightInput = document.getElementById('costWeightInput');
  const costWeightVal = document.getElementById('costWeightVal');
  costWeightInput.addEventListener('input', () => { costWeightVal.textContent = parseFloat(costWeightInput.value).toFixed(2); });
}

/**
 * Toggle API Key input based on backend selection
 */
function initBackendToggle() {
  const backendSelect = document.getElementById('backendSelect');
  const apiKeyGroup = document.getElementById('apiKeyGroup');
  backendSelect.addEventListener('change', () => {
    if (backendSelect.value === 'offline') {
      apiKeyGroup.style.display = 'none';
    } else {
      apiKeyGroup.style.display = 'block';
    }
  });
}

/**
 * Event Listeners
 */
function initEventListeners() {
  document.getElementById('dbSelect').addEventListener('change', populatePresetQueries);
  document.getElementById('presetQuerySelect').addEventListener('change', onPresetQuerySelected);
  document.getElementById('runBtn').addEventListener('click', runOptimization);
  document.getElementById('runScratchpadBtn').addEventListener('click', runScratchpad);
  document.getElementById('runBenchmarkBtn').addEventListener('click', runFullBenchmark);
  document.getElementById('copySqlBtn').addEventListener('click', copySqlToClipboard);
}

/**
 * Fetch Metadata from Backend
 */
async function loadMetadata() {
  try {
    const res = await fetch('/api/metadata');
    appMetadata = await res.json();
    populatePresetQueries();
    renderSchemaTree();
  } catch (err) {
    console.error('Failed to load metadata:', err);
  }
}

/**
 * Populate Preset Queries according to selected DB
 */
function populatePresetQueries() {
  if (!appMetadata) return;

  const dbId = document.getElementById('dbSelect').value;
  const select = document.getElementById('presetQuerySelect');
  select.innerHTML = '';

  const queries = (appMetadata.benchmark_queries || []).filter(q => q.db_id === dbId);
  queries.forEach((q, idx) => {
    const opt = document.createElement('option');
    opt.value = q.id;
    opt.textContent = `[${q.difficulty.toUpperCase()}] ${q.question}`;
    select.appendChild(opt);
  });

  const customOpt = document.createElement('option');
  customOpt.value = 'custom';
  customOpt.textContent = 'Custom Query (Write your own inquiry)';
  select.appendChild(customOpt);

  if (queries.length > 0) {
    select.selectedIndex = 0;
    onPresetQuerySelected();
  }

  renderSchemaTree();
}

/**
 * When preset query selection changes
 */
function onPresetQuerySelected() {
  const select = document.getElementById('presetQuerySelect');
  const questionInput = document.getElementById('questionInput');
  const tag = document.getElementById('queryDifficultyTag');
  const selectedId = select.value;

  if (selectedId === 'custom') {
    questionInput.value = 'Find customers with total account balance above 15000.';
    tag.textContent = 'Difficulty: Custom';
    return;
  }

  const queryObj = (appMetadata.benchmark_queries || []).find(q => q.id === selectedId);
  if (queryObj) {
    questionInput.value = queryObj.question;
    tag.textContent = `Difficulty: ${queryObj.difficulty.toUpperCase()}`;
  }
}

/**
 * Run AxiomSQL Optimization Pipeline
 */
async function runOptimization() {
  const question = document.getElementById('questionInput').value.trim();
  if (!question) {
    alert('Please specify a query question.');
    return;
  }

  const dbId = document.getElementById('dbSelect').value;
  const maxK = parseInt(document.getElementById('maxKInput').value, 10);
  const strategy = document.getElementById('stoppingStrategySelect').value;
  const tau = parseFloat(document.getElementById('tauInput').value);
  const lr = document.getElementById('learningRateSelect').value;
  const momentum = document.getElementById('momentumCheckbox').checked;
  const annealing = document.getElementById('annealingCheckbox').checked;
  const adversarial = document.getElementById('adversarialCheckbox').checked;
  const costWeight = parseFloat(document.getElementById('costWeightInput').value);
  const backend = document.getElementById('backendSelect').value;
  const apiKey = document.getElementById('apiKeyInput').value;

  const payload = {
    question,
    db_id: dbId,
    max_iterations: maxK,
    stopping_strategy: strategy,
    tau_confidence: tau,
    learning_rate: lr,
    enable_momentum: momentum,
    enable_annealing: annealing,
    enable_adversarial_testing: adversarial,
    weight_plan_cost: costWeight,
    backend,
    api_key: apiKey
  };

  const loading = document.getElementById('loadingIndicator');
  const resultsContainer = document.getElementById('resultsContainer');
  loading.style.display = 'flex';
  resultsContainer.style.display = 'none';

  try {
    const response = await fetch('/api/run-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    loading.style.display = 'none';

    if (data.error) {
      alert(`Optimization Error: ${data.error}`);
      return;
    }

    currentResult = data;
    renderResults(data);
    resultsContainer.style.display = 'block';

  } catch (err) {
    loading.style.display = 'none';
    alert(`Request Failure: ${err.message}`);
  }
}

/**
 * Render Pipeline Results into UI
 */
function renderResults(data) {
  // Telemetry Bar
  const maxK = document.getElementById('maxKInput').value;
  document.getElementById('resIterCount').textContent = `${data.total_iterations} / ${maxK}`;
  
  const statusElem = document.getElementById('resStatus');
  if (data.execution_result.success) {
    statusElem.textContent = 'Success [OK]';
    statusElem.style.color = '#34d399';
  } else {
    statusElem.textContent = 'Execution Error';
    statusElem.style.color = '#f87171';
  }

  document.getElementById('resRowCount').textContent = `${data.execution_result.row_count} rows`;
  document.getElementById('resLatency').textContent = `${(data.total_duration_seconds * 1000).toFixed(1)} ms`;
  document.getElementById('resPolicy').textContent = data.stopping_decision.strategy_used.toUpperCase();

  // Novelty Factors: AST Divergence & Adversarial Robustness
  const lastTrace = data.history && data.history.length > 0 ? data.history[data.history.length - 1] : null;
  const astDivVal = (lastTrace && lastTrace.loss_output.loss_breakdown.ast_divergence !== undefined)
    ? Number(lastTrace.loss_output.loss_breakdown.ast_divergence).toFixed(2)
    : '0.00';
  document.getElementById('resAstDiv').textContent = astDivVal;

  const robustLoss = (lastTrace && lastTrace.loss_output.loss_breakdown.adversarial_robustness !== undefined)
    ? lastTrace.loss_output.loss_breakdown.adversarial_robustness
    : 0.0;
  const robustElem = document.getElementById('resRobust');
  if (robustLoss === 0.0) {
    robustElem.textContent = 'VERIFIED';
    robustElem.style.color = '#34d399';
  } else {
    robustElem.textContent = 'MUTATED';
    robustElem.style.color = '#fbbf24';
  }

  // Stopping Decision
  document.getElementById('stoppingReasonText').textContent = data.stopping_decision.reason;

  // Final SQL Code
  document.getElementById('finalSqlCode').textContent = data.final_sql;

  // EXPLAIN Query Plan (Novelty Factor)
  const explainContainer = document.getElementById('explainPlanContainer');
  explainContainer.innerHTML = '';
  const planDetails = data.execution_result.plan_details || [];
  if (planDetails.length === 0) {
    explainContainer.innerHTML = '<div class="explain-item">No scan overhead detected (Direct evaluation).</div>';
  } else {
    planDetails.forEach(p => {
      const item = document.createElement('div');
      item.className = 'explain-item';
      const detailStr = p.detail || '';
      if (detailStr.toUpperCase().includes('SCAN TABLE')) {
        item.classList.add('scan');
      } else if (detailStr.toUpperCase().includes('USING INDEX')) {
        item.classList.add('index');
      }
      item.textContent = `[ID ${p.id}] ${detailStr}`;
      explainContainer.appendChild(item);
    });
  }

  // Execution Table
  renderTable(data.execution_result.columns, data.execution_result.data);

  // Iteration Timeline Accordion
  renderAccordion(data.history);

  // Compute Diff for Tab 2
  if (data.history && data.history.length > 0) {
    const initialSql = data.history[0].sql_value;
    const finalSql = data.final_sql;
    renderDiff(initialSql, finalSql);
  }
}

/**
 * Render Data Table
 */
function renderTable(columns, rows) {
  const head = document.getElementById('outputTableHead');
  const body = document.getElementById('outputTableBody');
  const badge = document.getElementById('resultMetaBadge');
  head.innerHTML = '';
  body.innerHTML = '';

  badge.textContent = `${rows ? rows.length : 0} rows`;

  if (!columns || columns.length === 0) {
    head.innerHTML = '<th>Output</th>';
    body.innerHTML = '<tr><td>No tabular columns returned</td></tr>';
    return;
  }

  columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    head.appendChild(th);
  });

  if (!rows || rows.length === 0) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td colspan="${columns.length}">Empty result set (0 rows returned)</td>`;
    body.appendChild(tr);
    return;
  }

  rows.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach(val => {
      const td = document.createElement('td');
      td.textContent = val !== null ? val : 'NULL';
      tr.appendChild(td);
    });
    body.appendChild(tr);
  });
}

/**
 * Render Accordion of Iteration History
 */
function renderAccordion(history) {
  const container = document.getElementById('trajectoryAccordion');
  container.innerHTML = '';

  if (!history || history.length === 0) return;

  history.forEach(t => {
    const card = document.createElement('div');
    card.className = 'accordion-card';

    const header = document.createElement('div');
    header.className = 'accordion-header';
    header.innerHTML = `
      <div>
        <strong>Iteration ${t.iteration}</strong>: Scalar Loss = ${t.loss_output.scalar_loss.toFixed(2)} | 
        Rows = ${t.execution_result.row_count} | 
        Grad Norm = ${t.gradient_norm.toFixed(3)}
      </div>
      <div>${t.exit_decision ? t.exit_decision.substring(0, 45) + '...' : 'CONTINUE'}</div>
    `;

    const body = document.createElement('div');
    body.className = 'accordion-body';
    body.style.display = 'none';

    body.innerHTML = `
      <div class="dual-grid">
        <div>
          <div class="panel-subhead">Stage 1: Schema-Linking Query Plan (V_plan)</div>
          <div class="code-container"><pre><code>${escapeHtml(t.plan_value)}</code></pre></div>
          <div class="panel-subhead" style="margin-top: 10px;">Stage 2: Synthesized SQL Query (V_sql)</div>
          <div class="code-container"><pre><code>${escapeHtml(t.sql_value)}</code></pre></div>
        </div>
        <div>
          <div class="panel-subhead">Multi-Objective Loss Vector Breakdown</div>
          <div style="font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg-primary); padding: 8px; border-radius: 4px; border: 1px solid var(--border-color);">
            <div>- Syntax Error Loss: ${t.loss_output.loss_breakdown.syntax || 0}</div>
            <div>- Schema Alignment Loss: ${t.loss_output.loss_breakdown.schema || 0}</div>
            <div>- Cardinality Loss (Empty Set): ${t.loss_output.loss_breakdown.cardinality || 0}</div>
            <div>- Semantic Discrepancy Loss: ${t.loss_output.loss_breakdown.semantic || 0}</div>
            <div>- Plan Scan Cost Penalty: ${t.loss_output.loss_breakdown.plan_cost || 0}</div>
            <div>- AST Cross-Product Penalty: ${t.loss_output.loss_breakdown.ast_cycle || 0}</div>
            <div>- AST Tree Divergence Penalty: ${t.loss_output.loss_breakdown.ast_divergence || 0}</div>
            <div>- Adversarial Boundary Robustness: ${t.loss_output.loss_breakdown.adversarial_robustness || 0}</div>
          </div>
          <div class="panel-subhead" style="margin-top: 10px;">Textual Gradient Feedback (&nabla; L)</div>
          <div class="code-container"><pre><code style="color: #fbbf24;">${escapeHtml(t.sql_gradient || 'No gradient')}</code></pre></div>
        </div>
      </div>
    `;

    header.addEventListener('click', () => {
      body.style.display = body.style.display === 'none' ? 'block' : 'none';
    });

    card.appendChild(header);
    card.appendChild(body);
    container.appendChild(card);
  });
}

/**
 * Render Diff Viewer
 */
function renderDiff(textA, textB) {
  const diffElem = document.getElementById('diffViewerCode');
  const linesA = textA.split('\n');
  const linesB = textB.split('\n');
  let diffStr = '--- Initial Attempt (Iteration 1)\n+++ Final Refinement (Optimized Solution)\n\n';

  linesA.forEach((l, i) => {
    if (linesB[i] && l !== linesB[i]) {
      diffStr += `- ${l}\n+ ${linesB[i]}\n`;
    } else if (!linesB[i]) {
      diffStr += `- ${l}\n`;
    } else {
      diffStr += `  ${l}\n`;
    }
  });

  if (linesB.length > linesA.length) {
    for (let j = linesA.length; j < linesB.length; j++) {
      diffStr += `+ ${linesB[j]}\n`;
    }
  }

  diffElem.textContent = diffStr;
}

/**
 * Render Loss Chart on Tab 2
 */
function renderLossChart(data) {
  const ctx = document.getElementById('lossChart');
  if (!ctx || !data || !data.history) return;

  const labels = data.history.map(t => `Iter ${t.iteration}`);
  const lossData = data.history.map(t => t.loss_output.scalar_loss);
  const gradData = data.history.map(t => t.gradient_norm);

  if (lossChartInstance) {
    lossChartInstance.destroy();
  }

  lossChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Scalar Loss (L_exec)',
          data: lossData,
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 2,
          tension: 0.2,
          fill: true
        },
        {
          label: 'Gradient Energy Norm (||g||)',
          data: gradData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          tension: 0.2,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 1.0,
          grid: { color: '#374151' },
          ticks: { color: '#9ca3af' }
        },
        x: {
          grid: { color: '#374151' },
          ticks: { color: '#9ca3af' }
        }
      },
      plugins: {
        legend: { labels: { color: '#f9fafb' } }
      }
    }
  });
}

/**
 * Render Benchmark Charts on Tab 3
 */
function renderBenchmarkCharts() {
  const accCtx = document.getElementById('benchmarkAccuracyChart');
  const iterCtx = document.getElementById('benchmarkIterationsChart');

  if (accCtx && !benchAccuracyChartInstance) {
    benchAccuracyChartInstance = new Chart(accCtx, {
      type: 'bar',
      data: {
        labels: ['AxiomSQL (Adaptive)', 'Zero-Shot', 'Few-Shot', 'Naive Reflexion', 'AxiomSQL (Fixed K=4)'],
        datasets: [{
          label: 'Execution Accuracy EX (%)',
          data: [81.8, 63.6, 63.6, 63.6, 45.5],
          backgroundColor: ['#10b981', '#3b82f6', '#6366f1', '#f59e0b', '#ef4444']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
          x: { grid: { color: '#374151' }, ticks: { color: '#9ca3af' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  if (iterCtx && !benchIterationsChartInstance) {
    benchIterationsChartInstance = new Chart(iterCtx, {
      type: 'bar',
      data: {
        labels: ['AxiomSQL (Adaptive)', 'Zero-Shot', 'Few-Shot', 'Naive Reflexion', 'AxiomSQL (Fixed K=4)'],
        datasets: [{
          label: 'Avg Iterations (K)',
          data: [2.09, 1.0, 1.0, 1.0, 4.0],
          backgroundColor: ['#10b981', '#6b7280', '#6b7280', '#f59e0b', '#ef4444']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true, max: 5, grid: { color: '#374151' }, ticks: { color: '#9ca3af' } },
          x: { grid: { color: '#374151' }, ticks: { color: '#9ca3af' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
}

/**
 * Execute Full Benchmark Evaluation
 */
async function runFullBenchmark() {
  const loading = document.getElementById('benchmarkLoading');
  const btn = document.getElementById('runBenchmarkBtn');
  loading.style.display = 'flex';
  btn.disabled = true;

  try {
    const res = await fetch('/api/benchmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_iterations: 4, stopping_strategy: 'execution_gated' })
    });
    const data = await res.json();
    loading.style.display = 'none';
    btn.disabled = false;

    if (data.summary) {
      const tbody = document.getElementById('benchmarkTableBody');
      tbody.innerHTML = '';
      data.summary.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${row['Method']}</strong></td>
          <td>${row['Valid SQL (%)']}%</td>
          <td>${row['Exec Accuracy EX (%)']}%</td>
          <td>${row['Avg Iterations (K)']}</td>
          <td>${row['Avg Latency (ms)']} ms</td>
          <td>${row['Method'].includes('AxiomSQL') ? 'Adaptive Stopping' : 'Baseline'}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    loading.style.display = 'none';
    btn.disabled = false;
    alert(`Benchmark error: ${err.message}`);
  }
}

/**
 * Render Relational Schema Explorer Tree
 */
function renderSchemaTree() {
  if (!appMetadata) return;
  const dbId = document.getElementById('dbSelect').value;
  const container = document.getElementById('schemaTreeContainer');
  const badge = document.getElementById('activeSchemaBadge');
  container.innerHTML = '';
  badge.textContent = dbId.toUpperCase();

  const dbData = (appMetadata.databases || {})[dbId];
  if (!dbData || !dbData.tables) {
    container.innerHTML = '<div class="column-item">Schema metadata unavailable</div>';
    return;
  }

  Object.keys(dbData.tables).forEach(tableName => {
    const tInfo = dbData.tables[tableName];
    const node = document.createElement('div');
    node.className = 'table-node';

    let colsHtml = '';
    Object.keys(tInfo.columns || {}).forEach(colName => {
      const c = tInfo.columns[colName];
      const pkBadge = c.pk ? '<span style="color:#f59e0b;font-size:0.7rem;">[PK]</span>' : '';
      colsHtml += `<div class="column-item"><span>${colName} ${pkBadge}</span><span>${c.type}</span></div>`;
    });

    let fkHtml = '';
    if (tInfo.foreign_keys && tInfo.foreign_keys.length > 0) {
      fkHtml = '<div style="margin-top:6px;font-size:0.75rem;color:#93c5fd;">Foreign Keys:</div>';
      tInfo.foreign_keys.forEach(fk => {
        fkHtml += `<div style="font-size:0.7rem;color:#60a5fa;">${fk.from} &rarr; ${fk.to_table}.${fk.to_col}</div>`;
      });
    }

    node.innerHTML = `
      <div class="table-node-name">Table: ${tableName} (${Object.keys(tInfo.columns).length} cols)</div>
      <div class="columns-list">${colsHtml}</div>
      ${fkHtml}
    `;

    container.appendChild(node);
  });
}

/**
 * Execute Scratchpad SQL Query
 */
async function runScratchpad() {
  const query = document.getElementById('scratchpadInput').value.trim();
  const dbId = document.getElementById('dbSelect').value;

  if (!query) return;

  try {
    const res = await fetch('/api/scratchpad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, db_id: dbId })
    });
    const data = await res.json();

    const head = document.getElementById('scratchpadTableHead');
    const body = document.getElementById('scratchpadTableBody');
    head.innerHTML = '';
    body.innerHTML = '';

    if (!data.success) {
      head.innerHTML = '<th>Error</th>';
      body.innerHTML = `<tr><td style="color:#f87171;">${data.error_message}</td></tr>`;
      return;
    }

    data.columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col;
      head.appendChild(th);
    });

    if (data.data.length === 0) {
      body.innerHTML = `<tr><td colspan="${data.columns.length}">0 rows returned</td></tr>`;
      return;
    }

    data.data.forEach(row => {
      const tr = document.createElement('tr');
      row.forEach(val => {
        const td = document.createElement('td');
        td.textContent = val !== null ? val : 'NULL';
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  } catch (err) {
    alert(`Scratchpad error: ${err.message}`);
  }
}

/**
 * Copy SQL code to clipboard
 */
function copySqlToClipboard() {
  const code = document.getElementById('finalSqlCode').textContent;
  if (code && code !== '--') {
    navigator.clipboard.writeText(code);
    const btn = document.getElementById('copySqlBtn');
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy SQL'; }, 2000);
  }
}

function escapeHtml(string) {
  return String(string)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

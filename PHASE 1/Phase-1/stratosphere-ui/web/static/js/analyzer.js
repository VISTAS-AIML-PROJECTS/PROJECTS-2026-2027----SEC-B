(function() {
  'use strict';

  // ── State ──
  let lastAnalysisData = null;
  let selectedSignals = new Set();
  let editingSignal = null;  // { signal_id, params, signal_name }
  let sweepCache = {};       // key: signal_id + param_name → data
  let activeSweepAbort = null;

  // ── DOM Refs ──
  const symbolInput    = document.getElementById('symbol-input');
  const intervalSelect = document.getElementById('interval-select');
  const periodSelect   = document.getElementById('period-select');
  const forwardSelect  = document.getElementById('forward-select');
  const winThreshold   = document.getElementById('win-threshold');
  const sortSelect     = document.getElementById('sort-select');
  const btnAnalyze     = document.getElementById('btn-analyze');
  const loadingEl      = document.getElementById('analyzer-loading');
  const errorEl        = document.getElementById('analyzer-error');
  const stockInfoEl    = document.getElementById('stock-info');
  const resultsEl      = document.getElementById('signal-results');
  const combinedEl     = document.getElementById('combined-result');
  const combineBar     = document.getElementById('combine-bar');
  const combineCountEl = document.getElementById('combine-count-num');
  const btnCombine     = document.getElementById('btn-combine');
  const btnClearCombine= document.getElementById('btn-clear-combine');

  // Edit modal refs
  const modalOverlay   = document.getElementById('edit-modal-overlay');
  const modalTitle     = document.getElementById('edit-modal-title');
  const paramsContainer= document.getElementById('edit-params-container');
  const resultPreview  = document.getElementById('edit-result-preview');
  const btnReeval      = document.getElementById('btn-reeval');
  const btnReset       = document.getElementById('btn-reset-params');
  const btnCloseModal  = document.getElementById('btn-close-modal');

  // ── Auto-adjust period when interval changes ──
  intervalSelect.addEventListener('change', () => {
    const iv = intervalSelect.value;
    if (iv === '1m') periodSelect.value = '5d';
    else if (['5m','15m','30m'].includes(iv)) periodSelect.value = '60d';
    else if (iv === '1h') periodSelect.value = '60d';
  });

  // ── Event Listeners ──
  btnAnalyze.addEventListener('click', analyzeStock);
  symbolInput.addEventListener('keydown', e => { if (e.key === 'Enter') analyzeStock(); });
  btnCombine.addEventListener('click', combineSelected);
  btnClearCombine.addEventListener('click', clearCombine);

  // Edit modal events
  btnCloseModal.addEventListener('click', closeEditModal);
  modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeEditModal(); });
  btnReeval.addEventListener('click', reEvaluateSignal);
  btnReset.addEventListener('click', resetParams);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeEditModal(); });

  // ══════════════════════════════════════════════════════════════════
  // ANALYZE
  // ══════════════════════════════════════════════════════════════════
  async function analyzeStock() {
    const symbol = symbolInput.value.trim();
    if (!symbol) { showError('Please enter a stock symbol.'); return; }

    hideError();
    showLoading(true);
    stockInfoEl.classList.remove('visible');
    resultsEl.innerHTML = '';
    combinedEl.innerHTML = '';
    combinedEl.classList.remove('visible');
    clearCombine();
    sweepCache = {};

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          period: periodSelect.value,
          interval: intervalSelect.value,
          forward_bars: parseInt(forwardSelect.value),
          win_threshold_pct: parseFloat(winThreshold.value),
          sort_by: sortSelect.value,
        }),
      });

      const data = await res.json();
      if (!res.ok) { showError(data.error || 'Analysis failed'); return; }

      lastAnalysisData = data;
      renderStockInfo(data);
      renderResults(data.scores);
    } catch (err) {
      showError('Network error: ' + err.message);
    } finally {
      showLoading(false);
    }
  }

  function renderStockInfo(data) {
    document.getElementById('si-name').textContent = data.stock_name;
    document.getElementById('si-symbol').textContent = data.symbol;
    document.getElementById('si-sector').textContent = data.sector;
    document.getElementById('si-interval').textContent = formatInterval(data.interval);
    document.getElementById('si-price').textContent = data.current_price
      ? '₹' + Number(data.current_price).toLocaleString('en-IN', { maximumFractionDigits: 2 })
      : '—';
    document.getElementById('si-bars').textContent = data.bars_analyzed.toLocaleString();
    document.getElementById('si-date').textContent = data.date_range;
    stockInfoEl.classList.add('visible');
  }

  // ══════════════════════════════════════════════════════════════════
  // RENDER SIGNAL CARDS
  // ══════════════════════════════════════════════════════════════════
  function renderResults(scores) {
    resultsEl.innerHTML = '';

    scores.forEach((s, i) => {
      const rank = i + 1;
      const card = document.createElement('div');
      card.className = 'signal-card';
      card.dataset.signalId = s.signal_id;
      card.style.animationDelay = (i * 0.06) + 's';
      if (s.win_rate >= 100) card.classList.add('perfect-win');

      const dirClass = s.direction_label === 'Bullish' ? 'badge-dir-bullish'
                     : s.direction_label === 'Bearish' ? 'badge-dir-bearish'
                     : 'badge-dir-both';

      const wrColor = getWinRateColor(s.win_rate);
      const hasParams = s.editable_params && s.editable_params.length > 0;

      card.innerHTML = `
        <button class="edit-btn ${hasParams ? '' : 'no-params'}"
                data-signal-id="${s.signal_id}"
                data-signal-name="${s.signal_name}"
                data-params='${JSON.stringify(s.editable_params || [])}'>
          ✏️ Edit
        </button>
        <label class="combine-check" title="Select to combine">
          <input type="checkbox" data-signal-id="${s.signal_id}" class="combine-cb">
          Combine
        </label>
        <div class="rank-number">#${rank}</div>
        <div class="signal-content">
          <div class="signal-left">
            <div class="signal-header">
              <span class="signal-name">${getCategoryIcon(s.category)} ${s.signal_name}</span>
              <span class="badge-category">${s.category}</span>
              <span class="${dirClass}">${s.direction_label}</span>
            </div>
            <div class="signal-desc">${s.description}</div>
            <div class="stats-grid">
              <div class="stat-box">
                <div class="stat-title">Total Signals</div>
                <div class="stat-val">${s.total_signals}</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Winners</div>
                <div class="stat-val positive">${s.winners}</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Losers</div>
                <div class="stat-val ${s.losers > 0 ? 'negative' : ''}">${s.losers}</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Avg Return</div>
                <div class="stat-val ${s.avg_return_pct >= 0 ? 'positive' : 'negative'}">${s.avg_return_pct > 0 ? '+' : ''}${s.avg_return_pct}%</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Avg Favorable</div>
                <div class="stat-val positive">+${s.avg_favorable_pct}%</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Avg Adverse</div>
                <div class="stat-val negative">-${s.avg_adverse_pct}%</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Best Trade</div>
                <div class="stat-val">${s.best_trade_pct > 0 ? '+' : ''}${s.best_trade_pct}%</div>
              </div>
              <div class="stat-box">
                <div class="stat-title">Profit Factor</div>
                <div class="stat-val">${s.profit_factor >= 999 ? '∞' : s.profit_factor}</div>
              </div>
            </div>
          </div>
          <div class="win-rate-panel">
            <div class="win-rate-title">Win Rate</div>
            <div class="win-rate-value" style="color: ${wrColor}">${s.win_rate}%</div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width: ${s.win_rate}%; background: ${wrColor};"></div>
            </div>
            <div class="confidence-badge">🎯 Confidence: ${s.confidence}</div>
          </div>
        </div>
      `;

      resultsEl.appendChild(card);
    });

    // Bind combine checkboxes
    resultsEl.querySelectorAll('.combine-cb').forEach(cb => {
      cb.addEventListener('change', onCombineToggle);
    });

    // Bind edit buttons
    resultsEl.querySelectorAll('.edit-btn').forEach(btn => {
      btn.addEventListener('click', onEditClick);
    });
  }

  // ══════════════════════════════════════════════════════════════════
  // EDIT MODAL
  // ══════════════════════════════════════════════════════════════════
  function onEditClick(e) {
    const btn = e.currentTarget;
    const signalId = btn.dataset.signalId;
    const signalName = btn.dataset.signalName;
    const params = JSON.parse(btn.dataset.params);

    if (!params || params.length === 0) return;

    editingSignal = { signal_id: signalId, signal_name: signalName, params: params };
    sweepCache = {};
    openEditModal(signalName, params);
  }

  function openEditModal(name, params) {
    modalTitle.textContent = '✏️ ' + name;
    paramsContainer.innerHTML = '';
    resultPreview.classList.remove('visible');
    resultPreview.innerHTML = '';

    params.forEach((p, idx) => {
      const group = document.createElement('div');
      group.className = 'edit-param-group';
      group.dataset.paramName = p.name;

      const isFloat = p.step < 1;
      const displayVal = isFloat ? p.default.toFixed(1) : p.default;
      const canvasId = `sweep-canvas-${p.name}`;

      group.innerHTML = `
        <div class="edit-param-label">
          <span>${p.label}</span>
          <span class="edit-param-value" id="val-${p.name}">${displayVal}<span class="edit-param-unit">${p.unit}</span></span>
        </div>
        <input type="range" class="edit-param-slider" id="slider-${p.name}"
               data-param-name="${p.name}"
               min="${p.min}" max="${p.max}" step="${p.step}" value="${p.default}">
        <div class="edit-param-range">
          <span>${p.min}${p.unit}</span>
          <span>${p.max}${p.unit}</span>
        </div>
        <div class="sweep-chart-container" id="sweep-container-${p.name}">
          <canvas id="${canvasId}" width="460" height="100"></canvas>
          <div class="sweep-chart-label">
            <span>Win Rate across ${p.label}</span>
            <span id="sweep-status-${p.name}"></span>
          </div>
          <div class="sweep-loading" id="sweep-loading-${p.name}" style="display:none;">⏳ Calculating...</div>
        </div>
      `;

      paramsContainer.appendChild(group);

      // Bind slider input event
      const slider = group.querySelector('.edit-param-slider');
      const valDisplay = group.querySelector('.edit-param-value');
      slider.addEventListener('input', () => {
        const v = parseFloat(slider.value);
        valDisplay.innerHTML = (isFloat ? v.toFixed(1) : v) + `<span class="edit-param-unit">${p.unit}</span>`;
      });

      // Hover to show sensitivity chart
      slider.addEventListener('mouseenter', () => fetchAndShowSweep(p));
      slider.addEventListener('focus', () => fetchAndShowSweep(p));
    });

    modalOverlay.classList.add('visible');
  }

  function closeEditModal() {
    modalOverlay.classList.remove('visible');
    editingSignal = null;
    if (activeSweepAbort) { activeSweepAbort.abort(); activeSweepAbort = null; }
  }

  function resetParams() {
    if (!editingSignal) return;
    editingSignal.params.forEach(p => {
      const slider = document.getElementById('slider-' + p.name);
      const valEl = document.getElementById('val-' + p.name);
      if (slider) {
        slider.value = p.default;
        const isFloat = p.step < 1;
        valEl.innerHTML = (isFloat ? p.default.toFixed(1) : p.default) + `<span class="edit-param-unit">${p.unit}</span>`;
      }
    });
    resultPreview.classList.remove('visible');
    sweepCache = {};
    // Hide all sweep charts
    paramsContainer.querySelectorAll('.sweep-chart-container').forEach(c => c.classList.remove('visible'));
  }

  // ══════════════════════════════════════════════════════════════════
  // SENSITIVITY SWEEP CHART
  // ══════════════════════════════════════════════════════════════════
  async function fetchAndShowSweep(param) {
    if (!editingSignal || !lastAnalysisData) return;

    const containerId = `sweep-container-${param.name}`;
    const container = document.getElementById(containerId);
    const canvasId = `sweep-canvas-${param.name}`;
    const loadingEl = document.getElementById(`sweep-loading-${param.name}`);
    const statusEl = document.getElementById(`sweep-status-${param.name}`);

    // Show the chart container
    container.classList.add('visible');

    // Check cache
    const cacheKey = editingSignal.signal_id + ':' + param.name;
    if (sweepCache[cacheKey]) {
      drawSweepChart(canvasId, sweepCache[cacheKey], param);
      return;
    }

    // Build fixed params (all current slider values except this one)
    const fixedParams = {};
    editingSignal.params.forEach(p => {
      if (p.name !== param.name) {
        const slider = document.getElementById('slider-' + p.name);
        if (slider) {
          const v = parseFloat(slider.value);
          fixedParams[p.name] = p.step >= 1 ? Math.round(v) : v;
        }
      }
    });

    // Show loading
    loadingEl.style.display = 'block';
    statusEl.textContent = '';

    if (activeSweepAbort) activeSweepAbort.abort();
    const controller = new AbortController();
    activeSweepAbort = controller;

    try {
      const res = await fetch('/api/analyze/sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          symbol: lastAnalysisData.symbol,
          signal_id: editingSignal.signal_id,
          sweep_param: param.name,
          fixed_params: fixedParams,
          period: periodSelect.value,
          interval: intervalSelect.value,
          forward_bars: parseInt(forwardSelect.value),
          win_threshold_pct: parseFloat(winThreshold.value),
          num_steps: 12,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        statusEl.textContent = data.error || 'Failed';
        return;
      }

      sweepCache[cacheKey] = data.points;
      drawSweepChart(canvasId, data.points, param);
      statusEl.textContent = `${data.points.length} points`;
    } catch (err) {
      if (err.name !== 'AbortError') statusEl.textContent = 'Error';
    } finally {
      loadingEl.style.display = 'none';
    }
  }

  function drawSweepChart(canvasId, points, param) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    if (points.length === 0) return;

    const pad = { top: 12, right: 12, bottom: 20, left: 35 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    const values = points.map(p => p.value);
    const winRates = points.map(p => p.win_rate);
    const signals = points.map(p => p.total_signals);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    const maxWR = Math.max(...winRates, 100);
    const maxSig = Math.max(...signals, 1);

    function xPos(v) { return pad.left + ((v - minV) / (maxV - minV || 1)) * chartW; }
    function yWR(wr) { return pad.top + chartH - (wr / maxWR) * chartH; }
    function ySig(s) { return pad.top + chartH - (s / maxSig) * chartH; }

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 0.5;
    for (let pct of [0, 25, 50, 75, 100]) {
      const y = yWR(pct);
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
    }

    // Y-axis labels
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.font = '9px system-ui';
    ctx.textAlign = 'right';
    for (let pct of [0, 50, 100]) {
      ctx.fillText(pct + '%', pad.left - 4, yWR(pct) + 3);
    }

    // X-axis labels
    ctx.textAlign = 'center';
    const labelStep = Math.max(1, Math.floor(points.length / 5));
    for (let i = 0; i < points.length; i += labelStep) {
      const isFloat = param.step < 1;
      const label = isFloat ? points[i].value.toFixed(1) : points[i].value;
      ctx.fillText(label + (param.unit || ''), xPos(points[i].value), h - 4);
    }

    // Signal count bars (subtle behind)
    ctx.fillStyle = 'rgba(139, 92, 246, 0.15)';
    const barW = Math.max(2, chartW / points.length * 0.6);
    points.forEach(p => {
      const bh = (p.total_signals / maxSig) * chartH;
      ctx.fillRect(xPos(p.value) - barW/2, pad.top + chartH - bh, barW, bh);
    });

    // Win rate line
    ctx.beginPath();
    ctx.strokeStyle = '#4ade80';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    points.forEach((p, i) => {
      const x = xPos(p.value);
      const y = yWR(p.win_rate);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Win rate area fill
    ctx.beginPath();
    points.forEach((p, i) => {
      const x = xPos(p.value);
      const y = yWR(p.win_rate);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(xPos(values[values.length - 1]), pad.top + chartH);
    ctx.lineTo(xPos(values[0]), pad.top + chartH);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
    grad.addColorStop(0, 'rgba(74, 222, 128, 0.25)');
    grad.addColorStop(1, 'rgba(74, 222, 128, 0.02)');
    ctx.fillStyle = grad;
    ctx.fill();

    // Data points
    points.forEach(p => {
      const x = xPos(p.value);
      const y = yWR(p.win_rate);
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fillStyle = getWinRateColor(p.win_rate);
      ctx.fill();
    });

    // Current slider value marker
    const slider = document.getElementById('slider-' + param.name);
    if (slider) {
      const currentVal = parseFloat(slider.value);
      const markerX = xPos(currentVal);
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.7)';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(markerX, pad.top);
      ctx.lineTo(markerX, pad.top + chartH);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  // ══════════════════════════════════════════════════════════════════
  // RE-EVALUATE SINGLE SIGNAL
  // ══════════════════════════════════════════════════════════════════
  async function reEvaluateSignal() {
    if (!editingSignal || !lastAnalysisData) return;

    const customParams = {};
    editingSignal.params.forEach(p => {
      const slider = document.getElementById('slider-' + p.name);
      if (slider) {
        const v = parseFloat(slider.value);
        customParams[p.name] = p.step >= 1 ? Math.round(v) : v;
      }
    });

    btnReeval.disabled = true;
    btnReeval.textContent = '⏳ Evaluating...';

    try {
      const res = await fetch('/api/analyze/single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: lastAnalysisData.symbol,
          signal_id: editingSignal.signal_id,
          custom_params: customParams,
          period: periodSelect.value,
          interval: intervalSelect.value,
          forward_bars: parseInt(forwardSelect.value),
          win_threshold_pct: parseFloat(winThreshold.value),
        }),
      });

      const data = await res.json();
      if (!res.ok) { showError(data.error || 'Re-evaluation failed'); return; }

      renderEditResult(data, customParams);
      updateCardInPlace(editingSignal.signal_id, data);
    } catch (err) {
      showError('Network error: ' + err.message);
    } finally {
      btnReeval.disabled = false;
      btnReeval.textContent = '🔄 Re-evaluate';
    }
  }

  function renderEditResult(data, customParams) {
    const wrColor = getWinRateColor(data.win_rate);
    const paramSummary = Object.entries(customParams)
      .map(([k, v]) => `${k}=${v}`).join(', ');

    resultPreview.innerHTML = `
      <div style="font-size:0.7rem; text-transform:uppercase; color:var(--accent-blue); font-weight:700; margin-bottom:0.5rem; letter-spacing:0.5px;">
        📊 Result with ${paramSummary}
      </div>
      <div class="result-row">
        <span class="result-label">Win Rate</span>
        <span class="result-val" style="color:${wrColor}; font-size:1.1rem;">${data.win_rate}%</span>
      </div>
      <div class="result-row">
        <span class="result-label">Total Signals</span>
        <span class="result-val">${data.total_signals}</span>
      </div>
      <div class="result-row">
        <span class="result-label">Winners / Losers</span>
        <span class="result-val"><span class="positive">${data.winners}</span> / <span class="${data.losers > 0 ? 'negative' : ''}">${data.losers}</span></span>
      </div>
      <div class="result-row">
        <span class="result-label">Avg Return</span>
        <span class="result-val ${data.avg_return_pct >= 0 ? 'positive' : 'negative'}">${data.avg_return_pct > 0 ? '+' : ''}${data.avg_return_pct}%</span>
      </div>
      <div class="result-row">
        <span class="result-label">Profit Factor</span>
        <span class="result-val">${data.profit_factor >= 999 ? '∞' : data.profit_factor}</span>
      </div>
      <div class="result-row">
        <span class="result-label">Confidence</span>
        <span class="result-val">${data.confidence}</span>
      </div>
    `;
    resultPreview.classList.add('visible');
  }

  function updateCardInPlace(signalId, newData) {
    const card = resultsEl.querySelector(`.signal-card[data-signal-id="${signalId}"]`);
    if (!card) return;

    const statVals = card.querySelectorAll('.stat-val');
    if (statVals.length >= 8) {
      statVals[0].textContent = newData.total_signals;
      statVals[1].textContent = newData.winners;
      statVals[2].textContent = newData.losers;
      statVals[2].className = 'stat-val' + (newData.losers > 0 ? ' negative' : '');
      statVals[3].textContent = (newData.avg_return_pct > 0 ? '+' : '') + newData.avg_return_pct + '%';
      statVals[3].className = 'stat-val ' + (newData.avg_return_pct >= 0 ? 'positive' : 'negative');
      statVals[4].textContent = '+' + newData.avg_favorable_pct + '%';
      statVals[5].textContent = '-' + newData.avg_adverse_pct + '%';
      statVals[6].textContent = (newData.best_trade_pct > 0 ? '+' : '') + newData.best_trade_pct + '%';
      statVals[7].textContent = newData.profit_factor >= 999 ? '∞' : newData.profit_factor;
    }

    const wrValue = card.querySelector('.win-rate-value');
    const wrBar = card.querySelector('.progress-bar-fill');
    const confBadge = card.querySelector('.confidence-badge');
    const wrColor = getWinRateColor(newData.win_rate);

    if (wrValue) { wrValue.textContent = newData.win_rate + '%'; wrValue.style.color = wrColor; }
    if (wrBar) { wrBar.style.width = newData.win_rate + '%'; wrBar.style.background = wrColor; }
    if (confBadge) confBadge.textContent = '🎯 Confidence: ' + newData.confidence;

    if (newData.win_rate >= 100) card.classList.add('perfect-win');
    else card.classList.remove('perfect-win');

    card.style.transition = 'none';
    card.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.4)';
    setTimeout(() => { card.style.transition = 'box-shadow 0.6s ease'; card.style.boxShadow = ''; }, 50);
  }

  // ══════════════════════════════════════════════════════════════════
  // COMBINE
  // ══════════════════════════════════════════════════════════════════
  function onCombineToggle(e) {
    const sid = e.target.dataset.signalId;
    if (e.target.checked) selectedSignals.add(sid);
    else selectedSignals.delete(sid);
    updateCombineBar();
  }

  function updateCombineBar() {
    const count = selectedSignals.size;
    combineCountEl.textContent = count;
    combineBar.classList.toggle('visible', count >= 2);
  }

  function clearCombine() {
    selectedSignals.clear();
    resultsEl.querySelectorAll('.combine-cb').forEach(cb => cb.checked = false);
    combineBar.classList.remove('visible');
    combinedEl.innerHTML = '';
    combinedEl.classList.remove('visible');
  }

  async function combineSelected() {
    if (selectedSignals.size < 2 || !lastAnalysisData) return;

    btnCombine.disabled = true;
    btnCombine.textContent = '⏳ Analyzing...';

    try {
      const res = await fetch('/api/analyze/combine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: lastAnalysisData.symbol,
          signal_ids: Array.from(selectedSignals),
          period: periodSelect.value,
          interval: intervalSelect.value,
          forward_bars: parseInt(forwardSelect.value),
          win_threshold_pct: parseFloat(winThreshold.value),
          confluence_window: 3,
        }),
      });

      const data = await res.json();
      if (!res.ok) { showError(data.error || 'Combine failed'); return; }
      renderCombinedResult(data);
    } catch (err) {
      showError('Network error: ' + err.message);
    } finally {
      btnCombine.disabled = false;
      btnCombine.textContent = '⚡ Combine & Evaluate';
    }
  }

  function renderCombinedResult(s) {
    const wrColor = getWinRateColor(s.win_rate);
    const isPerfect = s.win_rate >= 100;

    combinedEl.innerHTML = `
      <div class="combined-label">⚡ Combined Signal Result</div>
      <div class="signal-card combined-card ${isPerfect ? 'perfect-win' : ''}" style="opacity:1; animation: fadeInUp 0.4s ease;">
        <div class="signal-content">
          <div class="signal-left">
            <div class="signal-header">
              <span class="signal-name">🔗 ${s.signal_name}</span>
              <span class="badge-category">${s.category}</span>
              <span class="badge-dir-both">${s.direction_label}</span>
            </div>
            <div class="signal-desc">${s.description}</div>
            <div class="stats-grid">
              <div class="stat-box"><div class="stat-title">Co-occurrences</div><div class="stat-val">${s.total_signals}</div></div>
              <div class="stat-box"><div class="stat-title">Winners</div><div class="stat-val positive">${s.winners}</div></div>
              <div class="stat-box"><div class="stat-title">Losers</div><div class="stat-val ${s.losers > 0 ? 'negative' : ''}">${s.losers}</div></div>
              <div class="stat-box"><div class="stat-title">Avg Return</div><div class="stat-val ${s.avg_return_pct >= 0 ? 'positive' : 'negative'}">${s.avg_return_pct > 0 ? '+' : ''}${s.avg_return_pct}%</div></div>
              <div class="stat-box"><div class="stat-title">Avg Favorable</div><div class="stat-val positive">+${s.avg_favorable_pct}%</div></div>
              <div class="stat-box"><div class="stat-title">Avg Adverse</div><div class="stat-val negative">-${s.avg_adverse_pct}%</div></div>
              <div class="stat-box"><div class="stat-title">Best Trade</div><div class="stat-val">${s.best_trade_pct > 0 ? '+' : ''}${s.best_trade_pct}%</div></div>
              <div class="stat-box"><div class="stat-title">Profit Factor</div><div class="stat-val">${s.profit_factor >= 999 ? '∞' : s.profit_factor}</div></div>
            </div>
          </div>
          <div class="win-rate-panel">
            <div class="win-rate-title">Combined Win Rate</div>
            <div class="win-rate-value" style="color: ${wrColor}">${s.win_rate}%</div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width: ${s.win_rate}%; background: ${wrColor};"></div>
            </div>
            <div class="confidence-badge">🎯 Confidence: ${s.confidence}</div>
          </div>
        </div>
      </div>
    `;
    combinedEl.classList.add('visible');
    combinedEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ══════════════════════════════════════════════════════════════════
  // HELPERS
  // ══════════════════════════════════════════════════════════════════
  function getWinRateColor(rate) {
    if (rate >= 80) return '#4ade80';
    if (rate >= 60) return '#facc15';
    if (rate >= 40) return '#fb923c';
    return '#f87171';
  }

  function getCategoryIcon(cat) {
    const icons = {
      'Price Action': '📊', 'Momentum': '⚡', 'Trend': '📈',
      'Volatility': '🌊', 'Volume': '📦', 'Combined': '🔗', 'Time': '🕐',
    };
    return icons[cat] || '📌';
  }

  function formatInterval(iv) {
    const map = { '1m': '1-Minute', '5m': '5-Minute', '15m': '15-Minute',
                  '30m': '30-Minute', '1h': '1-Hour', '1d': 'Daily' };
    return map[iv] || iv;
  }

  function showLoading(on) {
    loadingEl.style.display = on ? 'block' : 'none';
    btnAnalyze.disabled = on;
  }

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add('visible');
  }

  function hideError() {
    errorEl.classList.remove('visible');
  }
})();

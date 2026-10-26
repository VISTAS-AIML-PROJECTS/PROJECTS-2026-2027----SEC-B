(function() {
  // --- STATE ---
  let metadata = null;
  let conditionCounter = 0;
  let updateTimeout = null;

  // --- SLIDER COMPONENT ---
  /**
   * Upgrade a <input type="number"> into a slider-group with:
   *   [min bound] ═══●═══ [max bound]  value + unit
   * Both min/max bounds are editable. The slider syncs with the hidden original input.
   *
   * @param {string} inputId - The ID of the existing number input
   * @param {number} min - Default slider minimum
   * @param {number} max - Default slider maximum
   * @param {number} step - Step increment
   * @param {string} unit - Display unit (e.g. '%', '₹', 'bars', '')
   * @param {object} opts - Optional: { compact: bool, decimals: number }
   */
  function upgradeToSlider(inputId, min, max, step, unit, opts = {}) {
    const input = document.getElementById(inputId);
    if (!input) return;

    const decimals = opts.decimals !== undefined ? opts.decimals : (step < 1 ? (step < 0.01 ? 4 : (step < 0.1 ? 2 : 1)) : 0);
    const compact = opts.compact || false;
    const currentVal = parseFloat(input.value) || ((min + max) / 2);

    // Create slider group
    const group = document.createElement('div');
    group.className = 'slider-group' + (compact ? ' compact' : '');

    const fill = ((currentVal - min) / (max - min)) * 100;

    group.innerHTML = `
      <div class="slider-row">
        <input type="number" class="slider-bound slider-min" value="${min}" step="${step}" title="Min bound">
        <div class="slider-track">
          <input type="range" min="${min}" max="${max}" step="${step}" value="${currentVal}"
                 style="--fill: ${fill}%"
                 data-target="${inputId}">
        </div>
        <input type="number" class="slider-bound slider-max" value="${max}" step="${step}" title="Max bound">
        <span class="slider-display">${Number(currentVal).toFixed(decimals)}${unit}</span>
      </div>
    `;

    // Hide the original input and insert the slider after it
    input.type = 'hidden';
    input.parentNode.insertBefore(group, input.nextSibling);

    // Get references
    const slider = group.querySelector('input[type="range"]');
    const minBound = group.querySelector('.slider-min');
    const maxBound = group.querySelector('.slider-max');
    const display = group.querySelector('.slider-display');

    function updateFill() {
      const mn = parseFloat(slider.min);
      const mx = parseFloat(slider.max);
      const val = parseFloat(slider.value);
      const pct = mx > mn ? ((val - mn) / (mx - mn)) * 100 : 0;
      slider.style.setProperty('--fill', pct + '%');
    }

    // Slider → sync value display + hidden input
    slider.addEventListener('input', () => {
      const val = parseFloat(slider.value);
      display.textContent = val.toFixed(decimals) + unit;
      input.value = val;
      updateFill();
      debounceUpdate();
    });

    // Min bound change → update slider min
    minBound.addEventListener('change', () => {
      const newMin = parseFloat(minBound.value);
      if (!isNaN(newMin) && newMin < parseFloat(maxBound.value)) {
        slider.min = newMin;
        if (parseFloat(slider.value) < newMin) {
          slider.value = newMin;
          input.value = newMin;
          display.textContent = newMin.toFixed(decimals) + unit;
        }
        updateFill();
      }
    });

    // Max bound change → update slider max
    maxBound.addEventListener('change', () => {
      const newMax = parseFloat(maxBound.value);
      if (!isNaN(newMax) && newMax > parseFloat(minBound.value)) {
        slider.max = newMax;
        if (parseFloat(slider.value) > newMax) {
          slider.value = newMax;
          input.value = newMax;
          display.textContent = newMax.toFixed(decimals) + unit;
        }
        updateFill();
      }
    });
  }

  /**
   * Upgrade all bounded/percentage inputs to sliders.
   * Called once during init after the DOM is ready.
   */
  function upgradeAllSliders() {
    // ── Section 2: Universe Filters ──
    upgradeToSlider('field-min-confidence',      -100, 100,   1,    '',     { decimals: 0 });
    upgradeToSlider('field-min-avg-volume',       0, 5000000, 10000,'',     { decimals: 0 });
    upgradeToSlider('field-min-avg-turnover',     0, 100000000, 100000, '', { decimals: 0 });
    upgradeToSlider('field-volume-lookback',      5, 252,      1,   ' days',{ decimals: 0 });

    // ── Section 4: Stop-Loss params ──
    upgradeToSlider('field-sl-fixed-pct',        0.1, 50,    0.1,  '%',    { decimals: 1 });
    upgradeToSlider('field-sl-atr-k',            0.1, 10,    0.1,  '×',    { decimals: 1 });
    upgradeToSlider('field-sl-atr-period',       2,   200,   1,    '',     { decimals: 0 });
    upgradeToSlider('field-sl-swing-lookback',   5,   200,   1,    ' bars', { decimals: 0 });
    upgradeToSlider('field-sl-swing-buffer',     0,   10,    0.1,  '%',    { decimals: 1 });
    upgradeToSlider('field-sl-sar-start',        0.005, 0.1, 0.005, '',   { decimals: 3 });
    upgradeToSlider('field-sl-sar-step',         0.005, 0.1, 0.005, '',   { decimals: 3 });
    upgradeToSlider('field-sl-sar-max',          0.05, 0.5,  0.01, '',    { decimals: 2 });
    upgradeToSlider('field-sl-time-bars',        1,   1000,  1,    ' bars', { decimals: 0 });

    // ── Section 4: Take-Profit ──
    upgradeToSlider('field-tp-pct',              0.5, 100,   0.5,  '%',    { decimals: 1 });
    upgradeToSlider('field-tp-partial',          1,   100,   1,    '%',    { decimals: 0 });

    // ── Section 4: Time Exit ──
    upgradeToSlider('field-time-exit-bars',      1,   1000,  1,    ' bars', { decimals: 0 });

    // ── Section 5: Position Sizing ──
    upgradeToSlider('field-sizing-qty',          1,   1000,  1,    '',     { decimals: 0 });
    upgradeToSlider('field-sizing-value',        1000, 10000000, 1000, ' ₹', { decimals: 0 });
    upgradeToSlider('field-sizing-risk',         0.1, 10,    0.1,  '%',    { decimals: 1 });
    upgradeToSlider('field-sizing-max-pos',      1,   100,   1,    '%',    { decimals: 0 });
    upgradeToSlider('field-sizing-vol-risk',     0.1, 10,    0.1,  '%',    { decimals: 1 });
    upgradeToSlider('field-sizing-vol-atr',      2,   200,   1,    '',     { decimals: 0 });
    upgradeToSlider('field-sizing-vol-k',        0.1, 10,    0.1,  '×',    { decimals: 1 });
    upgradeToSlider('field-sizing-vol-max-pos',  1,   100,   1,    '%',    { decimals: 0 });
    upgradeToSlider('field-sizing-kelly-win',    0.01, 0.99, 0.01, '',    { decimals: 2 });
    upgradeToSlider('field-sizing-kelly-avg-win', 1,  10000, 1,    ' ₹',  { decimals: 0 });
    upgradeToSlider('field-sizing-kelly-avg-loss', 1, 10000, 1,    ' ₹',  { decimals: 0 });
    upgradeToSlider('field-sizing-kelly-fraction', 0.05, 1.0, 0.05, '',   { decimals: 2 });
    upgradeToSlider('field-sizing-kelly-max-pos', 1,  100,   1,    '%',    { decimals: 0 });

    // ── Section 6: Backtest Defaults ──
    upgradeToSlider('field-bt-capital',          10000, 100000000, 10000, ' ₹', { decimals: 0 });
    upgradeToSlider('field-bt-max-pos',          1,    100,    1,    '',     { decimals: 0 });
    upgradeToSlider('field-bt-slippage',         0,    5,      0.01, '%',    { decimals: 2 });

    // ── Section 6: Advanced Costs ──
    upgradeToSlider('field-bt-commission',       0,    5,      0.001,'%',    { decimals: 3 });
    upgradeToSlider('field-bt-stt',              0,    1,      0.001,'%',    { decimals: 3 });
    upgradeToSlider('field-bt-exchange',         0,    0.1,    0.00001,'%',  { decimals: 5 });
    upgradeToSlider('field-bt-gst',              0,    30,     0.1,  '%',    { decimals: 1 });
    upgradeToSlider('field-bt-sebi',             0,    0.01,   0.0001,'%',   { decimals: 4 });
    upgradeToSlider('field-bt-stamp',            0,    1,      0.001,'%',    { decimals: 3 });

    // ── Section 6: Walk-Forward ──
    upgradeToSlider('field-wf-train',            50,   1000,   1,    ' bars', { decimals: 0 });
    upgradeToSlider('field-wf-test',             10,   500,    1,    ' bars', { decimals: 0 });
    upgradeToSlider('field-wf-step',             10,   500,    1,    ' bars', { decimals: 0 });
  }

  // --- INITIALIZATION ---
  async function init() {
    try {
      const response = await fetch('/api/builder/metadata');
      if (!response.ok) {
        throw new Error(`Failed to fetch metadata: ${response.status} ${response.statusText}`);
      }
      metadata = await response.json();
      window._metadata = metadata;
      
      setupEventListeners();
      upgradeAllSliders();
      
      // Initialize with one empty condition row
      const conditionTree = document.getElementById('condition-tree');
      if (conditionTree) {
        addConditionRow(conditionTree);
      }
      
      updateJsonPreview();
    } catch (error) {
      console.error('Error initializing builder:', error);
      const preview = document.getElementById('json-preview');
      if (preview) {
        preview.textContent = `// Error loading metadata:\n// ${error.message}`;
      }
    }
  }

  // --- EVENT LISTENERS ---
  function setupEventListeners() {
    // Event delegation for all inputs to trigger preview update
    document.addEventListener('input', debounceUpdate);
    document.addEventListener('change', debounceUpdate);

    // Section toggles are handled via onclick in the HTML template

    // Radio cards setup
    setupRadioCards('field-sl-type', 'sl-params');
    setupRadioCards('field-sizing-type', 'sizing-params');
    
    // Direction cards (entry)
    setupRadioCards('field-direction');

    // Conditional field visibility based on dropdown/checkbox state
    const orderTypeSelect = document.getElementById('field-order-type');
    if (orderTypeSelect) {
      orderTypeSelect.addEventListener('change', () => {
        const offsetContainer = document.getElementById('container-limit-offset');
        if (offsetContainer) {
          offsetContainer.style.display = orderTypeSelect.value === 'MARKET' ? 'none' : 'block';
        }
      });
    }

    const tpToggle = document.getElementById('toggle-take-profit');
    if (tpToggle) {
      tpToggle.addEventListener('change', () => {
        const tpFields = document.getElementById('container-take-profit');
        if (tpFields) tpFields.style.display = tpToggle.checked ? 'block' : 'none';
      });
    }

    const timeExitToggle = document.getElementById('toggle-time-exit');
    if (timeExitToggle) {
      timeExitToggle.addEventListener('change', () => {
        const teFields = document.getElementById('container-time-exit');
        if (teFields) teFields.style.display = timeExitToggle.checked ? 'block' : 'none';
      });
    }

    const advancedCostsToggle = document.getElementById('toggle-advanced-costs');
    if (advancedCostsToggle) {
      advancedCostsToggle.addEventListener('change', () => {
        const costFields = document.getElementById('container-advanced-costs');
        if (costFields) costFields.style.display = advancedCostsToggle.checked ? 'block' : 'none';
      });
    }

    const wfToggle = document.getElementById('toggle-walk-forward');
    if (wfToggle) {
      wfToggle.addEventListener('change', () => {
        const wfFields = document.getElementById('container-walk-forward');
        if (wfFields) wfFields.style.display = wfToggle.checked ? 'block' : 'none';
      });
    }

    // Chips input setup
    setupChipInput('field-tags-input', 'tags-container', 'btn-add-tag');
    setupChipInput('field-watchlist-input', 'watchlist-container', 'btn-add-watchlist');

    // Condition buttons
    const btnAddCondition = document.getElementById('btn-add-condition');
    if (btnAddCondition) {
      btnAddCondition.addEventListener('click', () => {
        addConditionRow(document.getElementById('condition-tree'));
        updateJsonPreview();
      });
    }

    const btnAddGroup = document.getElementById('btn-add-group');
    if (btnAddGroup) {
      btnAddGroup.addEventListener('click', () => {
        addGroupRow(document.getElementById('condition-tree'));
        updateJsonPreview();
      });
    }

    // Action buttons
    const btnValidate = document.getElementById('btn-validate');
    if (btnValidate) btnValidate.addEventListener('click', validateStrategy);

    const btnDownload = document.getElementById('btn-download');
    if (btnDownload) btnDownload.addEventListener('click', downloadJson);

    const btnCopy = document.getElementById('btn-copy');
    if (btnCopy) btnCopy.addEventListener('click', copyJson);
  }

  // --- UI HELPERS ---
  window.toggleSection = function(sectionId) {
    const body = document.getElementById('body-' + sectionId);
    const section = document.getElementById('section-' + sectionId);
    if (!body || !section) return;
    
    const toggle = section.querySelector('.section-toggle');
    
    if (body.style.display === 'none' || body.classList.contains('collapsed')) {
      body.style.display = 'block';
      body.classList.remove('collapsed');
      if (toggle) toggle.classList.remove('collapsed');
    } else {
      body.style.display = 'none';
      body.classList.add('collapsed');
      if (toggle) toggle.classList.add('collapsed');
    }
  };

  function setupRadioCards(containerId, paramsClassPrefix = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const cards = container.querySelectorAll('.radio-card');
    cards.forEach(card => {
      card.addEventListener('click', () => {
        // Remove active from all
        cards.forEach(c => c.classList.remove('active'));
        // Add active to clicked
        card.classList.add('active');
        
        // Hide all param blocks, show target
        if (paramsClassPrefix) {
          const scope = container.closest('.section-body') || container.parentElement;
          const allParams = scope.querySelectorAll(`.${paramsClassPrefix}`);
          allParams.forEach(p => {
            p.style.display = 'none';
            p.classList.remove('active');
          });
          
          const targetParamsId = `${paramsClassPrefix}-${card.dataset.value}`;
          const targetParams = document.getElementById(targetParamsId);
          if (targetParams) {
            targetParams.style.display = 'block';
            targetParams.classList.add('active');
          }
        }
        
        updateJsonPreview();
      });
    });
  }

  function setupChipInput(inputId, containerId, btnId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(containerId);
    const btn = document.getElementById(btnId);
    
    if (!input || !container) return;
    
    function addChip() {
      const val = input.value.trim();
      if (val) {
        const chip = document.createElement('div');
        chip.className = 'chip';
        chip.innerHTML = `
          <span class="chip-text">${val}</span>
          <button type="button" class="chip-remove">&times;</button>
        `;
        chip.querySelector('.chip-remove').addEventListener('click', () => {
          chip.remove();
          updateJsonPreview();
        });
        container.appendChild(chip);
        input.value = '';
        updateJsonPreview();
      }
    }
    
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addChip();
      }
    });
    
    if (btn) {
      btn.addEventListener('click', addChip);
    }
  }

  function getChips(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return [];
    return Array.from(container.querySelectorAll('.chip-text')).map(span => span.textContent);
  }

  function getSelectedRadio(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return null;
    const active = container.querySelector('.radio-card.active');
    return active ? active.dataset.value : null;
  }

  function debounceUpdate() {
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(updateJsonPreview, 300);
  }

  // --- CONDITIONS DOM ---
  function addConditionRow(container) {
    if (!metadata) return;
    const rowId = `cond-${conditionCounter++}`;
    const row = document.createElement('div');
    row.className = 'condition-row glass-panel';
    row.id = rowId;
    
    // Build options for indicators
    let indicatorOptions = '<option value="">Select Indicator...</option>';
    
    // Group by category
    const categories = {};
    metadata.indicators.forEach(ind => {
      if (!categories[ind.category]) categories[ind.category] = [];
      categories[ind.category].push(ind);
    });
    
    for (const [cat, inds] of Object.entries(categories)) {
      indicatorOptions += `<optgroup label="${cat}">`;
      inds.forEach(ind => {
        indicatorOptions += `<option value="${ind.id}">${ind.name}</option>`;
      });
      indicatorOptions += `</optgroup>`;
    }
    
    // Build comparisons
    let comparisonOptions = '';
    metadata.enums.comparisons.forEach(comp => {
      comparisonOptions += `<option value="${comp}">${comp}</option>`;
    });

    // Build threshold types
    let thresholdOptions = '';
    metadata.enums.threshold_types.forEach(tt => {
      thresholdOptions += `<option value="${tt.value}">${tt.label || tt.value}</option>`;
    });
    
    row.innerHTML = `
      <div class="cond-header">
        <select class="cond-indicator form-control">${indicatorOptions}</select>
        <button type="button" class="btn-remove btn-icon" title="Remove Condition">&times;</button>
      </div>
      <div class="cond-body" style="display:none;">
        <div class="cond-params-container">
          <label>Parameters</label>
          <div class="cond-params"></div>
        </div>
        <div class="cond-logic-container">
          <div class="cond-logic-row">
            <select class="cond-output form-control"></select>
            <select class="cond-comparison form-control">${comparisonOptions}</select>
            <select class="cond-threshold-type form-control">${thresholdOptions}</select>
          </div>
          <div class="cond-threshold-inputs"></div>
        </div>
      </div>
    `;
    
    // Setup row events
    const indSelect = row.querySelector('.cond-indicator');
    const body = row.querySelector('.cond-body');
    const btnRemove = row.querySelector('.btn-remove');
    const thresholdTypeSelect = row.querySelector('.cond-threshold-type');
    
    indSelect.addEventListener('change', () => {
      if (indSelect.value) {
        body.style.display = 'block';
        populateIndicatorParams(row, indSelect.value);
        updateThresholdInputs(row, thresholdTypeSelect.value);
      } else {
        body.style.display = 'none';
      }
      updateJsonPreview();
    });
    
    thresholdTypeSelect.addEventListener('change', () => {
      updateThresholdInputs(row, thresholdTypeSelect.value);
      updateJsonPreview();
    });
    
    btnRemove.addEventListener('click', () => {
      row.remove();
      updateJsonPreview();
    });
    
    container.appendChild(row);
  }

  function populateIndicatorParams(row, indicatorId) {
    const ind = metadata.indicators.find(i => i.id === indicatorId);
    if (!ind) return;
    
    const paramsContainer = row.querySelector('.cond-params');
    paramsContainer.innerHTML = '';
    
    (ind.parameters || []).forEach(param => {
      const pDiv = document.createElement('div');
      pDiv.className = 'param-input';
      
      let attrs = '';
      if (param.constraint) {
        if (param.constraint.min_value !== undefined) attrs += ` min="${param.constraint.min_value}"`;
        if (param.constraint.max_value !== undefined) attrs += ` max="${param.constraint.max_value}"`;
        if (param.constraint.step !== undefined) attrs += ` step="${param.constraint.step}"`;
      }
      
      if (param.param_type === 'bool') {
        pDiv.innerHTML = `
          <label>${param.name}</label>
          <input type="checkbox" data-param-name="${param.name}" ${param.default ? 'checked' : ''}>
        `;
      } else {
        const typeAttr = (param.param_type === 'int' || param.param_type === 'float') ? 'number' : 'text';
        pDiv.innerHTML = `
          <label>${param.name}</label>
          <input type="${typeAttr}" class="form-control" data-param-name="${param.name}" value="${param.default !== undefined ? param.default : ''}" ${attrs}>
        `;
      }
      paramsContainer.appendChild(pDiv);
    });
    
    const outputSelect = row.querySelector('.cond-output');
    outputSelect.innerHTML = '';
    (ind.outputs || []).forEach(out => {
      outputSelect.innerHTML += `<option value="${out.name}">${out.name}</option>`;
    });
  }

  function updateThresholdInputs(row, type) {
    const container = row.querySelector('.cond-threshold-inputs');
    container.innerHTML = '';
    
    if (type === 'static') {
      container.innerHTML = `
        <input type="number" class="form-control thresh-val" placeholder="Value" step="any">
      `;
    } else if (type === 'range') {
      container.innerHTML = `
        <input type="number" class="form-control thresh-low" placeholder="Low" step="any">
        <input type="number" class="form-control thresh-high" placeholder="High" step="any">
      `;
    } else if (type === 'indicator_ref') {
      // Very basic implementation for demo, ideally reuses indicator select
      let indicatorOptions = '<option value="">Select Indicator...</option>';
      metadata.indicators.forEach(ind => {
        indicatorOptions += `<option value="${ind.id}">${ind.name}</option>`;
      });
      container.innerHTML = `
        <select class="form-control thresh-ind">${indicatorOptions}</select>
        <div class="thresh-ind-params"></div>
        <select class="form-control thresh-ind-out"></select>
      `;
      
      const threshInd = container.querySelector('.thresh-ind');
      threshInd.addEventListener('change', () => {
        // Similar to populateIndicatorParams but for threshold reference
        const ind = metadata.indicators.find(i => i.id === threshInd.value);
        if (!ind) return;
        const outSelect = container.querySelector('.thresh-ind-out');
        outSelect.innerHTML = '';
        (ind.outputs || []).forEach(out => {
          outSelect.innerHTML += `<option value="${out.name}">${out.name}</option>`;
        });
        updateJsonPreview();
      });
    }
  }

  function addGroupRow(container) {
    const groupId = `group-${conditionCounter++}`;
    const group = document.createElement('div');
    group.className = 'condition-group glass-panel';
    group.id = groupId;
    
    group.innerHTML = `
      <div class="group-header">
        <select class="group-operator form-control">
          <option value="AND">AND</option>
          <option value="OR">OR</option>
        </select>
        <button type="button" class="btn-remove btn-icon" title="Remove Group">&times;</button>
      </div>
      <div class="group-body"></div>
      <div class="group-footer">
        <button type="button" class="btn btn-sm btn-outline btn-add-cond-to-group">+ Add Condition</button>
        <button type="button" class="btn btn-sm btn-outline btn-add-group-to-group">+ Add Group</button>
      </div>
    `;
    
    const btnRemove = group.querySelector('.btn-remove');
    btnRemove.addEventListener('click', () => {
      group.remove();
      updateJsonPreview();
    });
    
    const body = group.querySelector('.group-body');
    const btnAddCond = group.querySelector('.btn-add-cond-to-group');
    const btnAddGrp = group.querySelector('.btn-add-group-to-group');
    
    btnAddCond.addEventListener('click', () => addConditionRow(body));
    btnAddGrp.addEventListener('click', () => addGroupRow(body));
    
    // Start with one condition inside
    addConditionRow(body);
    
    container.appendChild(group);
  }

  // --- JSON GENERATION ---
  function buildConditionTree(container = document.getElementById('condition-tree')) {
    const children = Array.from(container.children);
    const conditions = [];
    
    for (const child of children) {
      if (child.classList.contains('condition-row')) {
        const indId = child.querySelector('.cond-indicator').value;
        if (!indId) continue;
        
        const params = {};
        child.querySelectorAll('.param-input input').forEach(input => {
          const name = input.dataset.paramName;
          if (input.type === 'checkbox') {
            params[name] = input.checked;
          } else if (input.type === 'number') {
            params[name] = input.value !== '' ? parseFloat(input.value) : null;
          } else {
            params[name] = input.value;
          }
        });
        
        const outputName = child.querySelector('.cond-output').value;
        const comparison = child.querySelector('.cond-comparison').value;
        const threshType = child.querySelector('.cond-threshold-type').value;
        
        let threshold = { type: threshType };
        if (threshType === 'static') {
          const val = child.querySelector('.thresh-val')?.value;
          threshold.value = val !== '' ? parseFloat(val) : 0;
        } else if (threshType === 'range') {
          const low = child.querySelector('.thresh-low')?.value;
          const high = child.querySelector('.thresh-high')?.value;
          threshold.low = low !== '' ? parseFloat(low) : 0;
          threshold.high = high !== '' ? parseFloat(high) : 0;
        } else if (threshType === 'indicator_ref') {
          const refInd = child.querySelector('.thresh-ind')?.value;
          threshold.indicator_id = refInd || 'none';
          threshold.indicator_params = {}; // Simplify for now
          threshold.output_name = child.querySelector('.thresh-ind-out')?.value || 'value';
        }
        
        conditions.push({
          type: 'leaf',
          indicator_id: indId,
          indicator_params: params,
          output_name: outputName,
          comparison: comparison,
          threshold: threshold
        });
      } else if (child.classList.contains('condition-group')) {
        const operator = child.querySelector('.group-operator').value;
        const body = child.querySelector('.group-body');
        const subConds = buildConditionTree(body);
        
        if (subConds) {
          if (subConds.type === 'compound' || subConds.type === 'leaf') {
             conditions.push(subConds);
          }
        }
      }
    }
    
    if (conditions.length === 0) return null;
    if (conditions.length === 1) return conditions[0];
    
    return {
      type: 'compound',
      operator: container.classList.contains('group-body') 
        ? container.closest('.condition-group').querySelector('.group-operator').value 
        : 'AND',
      conditions: conditions
    };
  }

  function buildStopLoss() {
    const type = getSelectedRadio('field-sl-type');
    if (!type) return { type: 'fixed_pct', pct: 2.0 };
    
    const sl = { type: type };
    if (type === 'fixed_pct') {
      const val = document.getElementById('field-sl-fixed-pct')?.value;
      sl.pct = val !== '' ? parseFloat(val) : 2.0;
    } else if (type === 'atr_based') {
      const k = document.getElementById('field-sl-atr-k')?.value;
      sl.k = k !== '' ? parseFloat(k) : 2.0;
      const period = document.getElementById('field-sl-atr-period')?.value;
      sl.atr_period = period !== '' ? parseInt(period, 10) : 14;
      sl.trailing = document.getElementById('field-sl-atr-trailing')?.checked || false;
    } else if (type === 'swing_low') {
      const lookback = document.getElementById('field-sl-swing-lookback')?.value;
      sl.lookback_bars = lookback !== '' ? parseInt(lookback, 10) : 20;
      const buffer = document.getElementById('field-sl-swing-buffer')?.value;
      sl.buffer_pct = buffer !== '' ? parseFloat(buffer) : 0.5;
    } else if (type === 'parabolic_sar') {
      sl.af_start = parseFloat(document.getElementById('field-sl-sar-start')?.value || '0.02');
      sl.af_step = parseFloat(document.getElementById('field-sl-sar-step')?.value || '0.02');
      sl.af_max = parseFloat(document.getElementById('field-sl-sar-max')?.value || '0.2');
    } else if (type === 'time_based') {
      const bars = document.getElementById('field-sl-time-bars')?.value;
      sl.max_bars = bars !== '' ? parseInt(bars, 10) : 10;
    }
    return sl;
  }

  function buildSizing() {
    const type = getSelectedRadio('field-sizing-type');
    if (!type) return { type: 'fixed_qty', quantity: 100 };
    
    const sizing = { type: type };
    if (type === 'fixed_qty') {
      const val = document.getElementById('field-sizing-qty')?.value;
      sizing.quantity = val !== '' ? parseInt(val, 10) : 100;
    } else if (type === 'fixed_value') {
      const val = document.getElementById('field-sizing-value')?.value;
      sizing.value = val !== '' ? parseFloat(val) : 100000;
    } else if (type === 'risk_pct') {
      const risk = document.getElementById('field-sizing-risk')?.value;
      sizing.risk_pct = risk !== '' ? parseFloat(risk) : 1.0;
      const maxPos = document.getElementById('field-sizing-max-pos')?.value;
      sizing.max_position_pct = maxPos !== '' ? parseFloat(maxPos) : 25.0;
    } else if (type === 'volatility_adjusted') {
      sizing.risk_pct = parseFloat(document.getElementById('field-sizing-vol-risk')?.value || '1.0');
      sizing.atr_period = parseInt(document.getElementById('field-sizing-vol-atr')?.value || '14', 10);
      sizing.k = parseFloat(document.getElementById('field-sizing-vol-k')?.value || '2.0');
      sizing.max_position_pct = parseFloat(document.getElementById('field-sizing-vol-max-pos')?.value || '25');
    } else if (type === 'kelly') {
      sizing.win_rate = parseFloat(document.getElementById('field-sizing-kelly-win')?.value || '0.55');
      sizing.avg_win = parseFloat(document.getElementById('field-sizing-kelly-avg-win')?.value || '100');
      sizing.avg_loss = parseFloat(document.getElementById('field-sizing-kelly-avg-loss')?.value || '50');
      sizing.fraction = parseFloat(document.getElementById('field-sizing-kelly-fraction')?.value || '0.5');
      sizing.max_position_pct = parseFloat(document.getElementById('field-sizing-kelly-max-pos')?.value || '25');
    }
    return sizing;
  }
  
  function buildUniverse() {
    const universe = {};
    const watchlist = getChips('watchlist-container');
    if (watchlist.length > 0) universe.watchlist = watchlist;
    
    const sectors = Array.from(
      document.querySelectorAll('#field-sector-filter input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    if (sectors.length > 0) universe.sector_filter = sectors;
    
    const mktcaps = Array.from(
      document.querySelectorAll('#field-market-cap-filter input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    if (mktcaps.length > 0) universe.market_cap_filter = mktcaps;
    
    const minVol = document.getElementById('field-min-avg-volume')?.value;
    if (minVol) universe.min_avg_volume = parseFloat(minVol);
    
    const minTurnover = document.getElementById('field-min-avg-turnover')?.value;
    if (minTurnover) universe.min_avg_turnover = parseFloat(minTurnover);
    
    const lookback = document.getElementById('field-volume-lookback')?.value;
    if (lookback && lookback !== '20') universe.volume_lookback_days = parseInt(lookback, 10);
    
    return universe;
  }
  
  function buildBacktestDefaults() {
    const btd = {};
    
    const capital = document.getElementById('field-bt-capital')?.value;
    if (capital) btd.initial_capital = parseFloat(capital);
    
    const maxPos = document.getElementById('field-bt-max-pos')?.value;
    if (maxPos) btd.max_open_positions = parseInt(maxPos, 10);
    
    const slippage = document.getElementById('field-bt-slippage')?.value;
    if (slippage) btd.slippage_pct = parseFloat(slippage);
    
    if (document.getElementById('toggle-advanced-costs')?.checked) {
      const commission = document.getElementById('field-bt-commission')?.value;
      if (commission) btd.commission_pct = parseFloat(commission);
      const stt = document.getElementById('field-bt-stt')?.value;
      if (stt) btd.stt_pct = parseFloat(stt);
      const exchange = document.getElementById('field-bt-exchange')?.value;
      if (exchange) btd.exchange_txn_pct = parseFloat(exchange);
      const gst = document.getElementById('field-bt-gst')?.value;
      if (gst) btd.gst_pct = parseFloat(gst);
      const sebi = document.getElementById('field-bt-sebi')?.value;
      if (sebi) btd.sebi_turnover_pct = parseFloat(sebi);
      const stamp = document.getElementById('field-bt-stamp')?.value;
      if (stamp) btd.stamp_duty_pct = parseFloat(stamp);
    }
    
    if (document.getElementById('toggle-walk-forward')?.checked) {
      const train = document.getElementById('field-wf-train')?.value;
      if (train) btd.wf_train_bars = parseInt(train, 10);
      const test = document.getElementById('field-wf-test')?.value;
      if (test) btd.wf_test_bars = parseInt(test, 10);
      const step = document.getElementById('field-wf-step')?.value;
      if (step) btd.wf_step_bars = parseInt(step, 10);
    }
    
    return btd;
  }

  function buildStrategy() {
    const strategy = {
      schema_version: "1.0.0",
      name: document.getElementById('field-name')?.value || 'My Strategy',
      description: document.getElementById('field-description')?.value || '',
      tags: getChips('tags-container'),
      primary_timeframe: document.getElementById('field-timeframe')?.value || 'DAILY',
      entry: {
        direction: getSelectedRadio('field-direction') || 'LONG',
        condition: buildConditionTree(),
        order_type: document.getElementById('field-order-type')?.value || 'MARKET'
      },
      exit: {
        stop_loss: buildStopLoss(),
        take_profit: null,
        time_exit: null,
        trailing_after_tp: document.getElementById('field-trailing-after-tp')?.checked || false
      },
      sizing: buildSizing()
    };
    
    // Take Profit
    if (document.getElementById('toggle-take-profit')?.checked) {
      const tpPct = document.getElementById('field-tp-pct')?.value;
      strategy.exit.take_profit = {
        pct: tpPct !== '' ? parseFloat(tpPct) : 4.0,
        partial_exit_pct: parseFloat(document.getElementById('field-tp-partial')?.value || '100')
      };
      strategy.exit.trailing_after_tp = document.getElementById('field-tp-trailing')?.checked || false;
    }
    
    // Time Exit
    if (document.getElementById('toggle-time-exit')?.checked) {
      const bars = document.getElementById('field-time-exit-bars')?.value;
      strategy.exit.time_exit = {
        max_bars: bars !== '' ? parseInt(bars, 10) : 20
      };
    }
    
    // Limit Offset
    if (strategy.entry.order_type !== 'MARKET') {
      const offset = document.getElementById('field-limit-offset')?.value;
      strategy.entry.limit_offset_pct = offset !== '' ? parseFloat(offset) : 0;
    }
    
    const universe = buildUniverse();
    if (Object.keys(universe).length > 0) strategy.universe = universe;
    
    strategy.backtest_defaults = buildBacktestDefaults();
    
    return strategy;
  }

  function updateJsonPreview() {
    const preview = document.getElementById('json-preview');
    if (!preview) return;
    
    try {
      const strategy = buildStrategy();
      const jsonStr = JSON.stringify(strategy, null, 2);
      
      // Basic syntax highlighting
      const highlighted = jsonStr
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
          let cls = 'json-value';
          if (/^"/.test(match)) {
            if (/:$/.test(match)) {
              cls = 'json-key';
            } else {
              cls = 'json-string';
            }
          } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
          } else if (/null/.test(match)) {
            cls = 'json-null';
          }
          return '<span class="' + cls + '">' + match + '</span>';
        });
        
      preview.innerHTML = highlighted;
    } catch (e) {
      preview.textContent = '// Error building strategy\n// ' + e.message;
    }
  }

  // --- ACTIONS ---
  async function validateStrategy() {
    const resultsDiv = document.getElementById('builder-results');
    if (!resultsDiv) return;
    
    resultsDiv.innerHTML = '<div class="alert alert-info">Validating...</div>';
    
    try {
      const strategy = buildStrategy();
      const response = await fetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(strategy)
      });
      
      const result = await response.json();
      
      if (response.ok && result.valid) {
        resultsDiv.innerHTML = '<div class="alert alert-success">Strategy is valid!</div>';
      } else {
        const errors = result.errors ? result.errors.map(e => `<li>${e}</li>`).join('') : 'Unknown error';
        resultsDiv.innerHTML = `<div class="alert alert-danger"><strong>Validation Failed:</strong><ul>${errors}</ul></div>`;
      }
    } catch (error) {
      resultsDiv.innerHTML = `<div class="alert alert-danger">Error calling validation API: ${error.message}</div>`;
    }
  }

  function downloadJson() {
    try {
      const strategy = buildStrategy();
      const jsonStr = JSON.stringify(strategy, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = (strategy.name.replace(/[^a-z0-9]/gi, '_').toLowerCase() || 'strategy') + '.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Error downloading JSON: ' + e.message);
    }
  }

  function copyJson() {
    try {
      const strategy = buildStrategy();
      const jsonStr = JSON.stringify(strategy, null, 2);
      
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(jsonStr).then(() => {
          showToast('JSON copied to clipboard!');
        });
      } else {
        // Fallback
        const textArea = document.createElement('textarea');
        textArea.value = jsonStr;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('JSON copied to clipboard!');
      }
    } catch (e) {
      alert('Error copying JSON: ' + e.message);
    }
  }
  
  function showToast(message) {
    let toast = document.getElementById('toast-notification');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast-notification';
      toast.style.cssText = 'position:fixed;bottom:20px;right:20px;background:rgba(0,0,0,0.8);color:white;padding:10px 20px;border-radius:4px;z-index:9999;transition:opacity 0.3s;';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = '1';
    
    setTimeout(() => {
      toast.style.opacity = '0';
    }, 3000);
  }

  // --- BOOTSTRAP ---
  document.addEventListener('DOMContentLoaded', init);
  
})();

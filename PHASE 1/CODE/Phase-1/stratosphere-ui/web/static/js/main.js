document.addEventListener('DOMContentLoaded', () => {
    
    // --- Navbar Active State ---
    const path = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === path) {
            link.classList.add('active');
        }
    });

    // --- Schema Browser ---
    const schemaTree = document.getElementById('schema-tree');
    if (schemaTree) {
        fetch('/api/schema')
            .then(res => res.json())
            .then(schema => {
                renderSchema(schema, schemaTree);
            });
    }

    function renderSchema(schema, container) {
        // Recursive function to build tree
        function buildNode(name, def, isRoot=false) {
            const node = document.createElement('div');
            node.className = isRoot ? '' : 'tree-node';
            
            const item = document.createElement('div');
            item.className = 'tree-item';
            
            // Determine type
            let type = def.type || 'unknown';
            if (def.$ref) type = 'object (ref)';
            if (def.anyOf) type = 'union';
            if (def.enum) type = 'enum';
            
            item.innerHTML = `
                <span class="toggle-icon">${(def.properties || def.$ref || def.items) ? '▶' : '•'}</span>
                <span class="field-name">${name}</span>
                <span class="field-type type-${type.split(' ')[0]}">${type}</span>
            `;
            
            // Details panel
            const details = document.createElement('div');
            details.className = 'schema-details';
            let detailsHtml = '';
            if (def.description) detailsHtml += `<p><strong>Description:</strong> ${def.description}</p>`;
            if (def.default !== undefined) detailsHtml += `<p><strong>Default:</strong> ${JSON.stringify(def.default)}</p>`;
            if (def.enum) detailsHtml += `<p><strong>Allowed Values:</strong> ${def.enum.join(', ')}</p>`;
            
            if (detailsHtml) {
                details.innerHTML = detailsHtml;
                node.appendChild(item);
                node.appendChild(details);
            } else {
                node.appendChild(item);
            }

            // Children
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';
            childrenContainer.style.display = 'none';

            let hasChildren = false;
            if (def.properties) {
                for (const [k, v] of Object.entries(def.properties)) {
                    childrenContainer.appendChild(buildNode(k, v));
                    hasChildren = true;
                }
            } else if (def.items && def.items.properties) {
                for (const [k, v] of Object.entries(def.items.properties)) {
                    childrenContainer.appendChild(buildNode(k, v));
                    hasChildren = true;
                }
            } else if (def.$ref) {
                // simple resolution
                const refName = def.$ref.split('/').pop();
                if (schema.$defs && schema.$defs[refName]) {
                    const refDef = schema.$defs[refName];
                    if (refDef.properties) {
                        for (const [k, v] of Object.entries(refDef.properties)) {
                            childrenContainer.appendChild(buildNode(k, v));
                            hasChildren = true;
                        }
                    } else if (refDef.enum) {
                        const enumDetails = document.createElement('div');
                        enumDetails.className = 'schema-details';
                        enumDetails.innerHTML = `<p><strong>Enum Values:</strong> ${refDef.enum.join(', ')}</p>`;
                        childrenContainer.appendChild(enumDetails);
                        hasChildren = true;
                    }
                }
            }
            
            if (hasChildren) {
                node.appendChild(childrenContainer);
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isExpanded = childrenContainer.style.display === 'block';
                    childrenContainer.style.display = isExpanded ? 'none' : 'block';
                    details.style.display = isExpanded ? 'none' : 'block';
                    item.querySelector('.toggle-icon').textContent = isExpanded ? '▶' : '▼';
                });
            } else {
                item.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const isExpanded = details.style.display === 'block';
                    details.style.display = isExpanded ? 'none' : 'block';
                });
            }

            return node;
        }

        container.appendChild(buildNode('StrategyConfig', schema, true));
    }

    // --- Indicator Filter ---
    const filterBtns = document.querySelectorAll('.filter-btn');
    const indicatorCards = document.querySelectorAll('.indicator-card');

    if (filterBtns.length > 0) {
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.dataset.filter;
                
                indicatorCards.forEach(card => {
                    if (filter === 'ALL' || card.dataset.category === filter) {
                        card.style.display = 'flex';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
        });
    }

    // --- Validator ---
    const validateBtn = document.getElementById('validate-btn');
    const validateInput = document.getElementById('validate-input');
    const resultsPanel = document.getElementById('results-panel');

    if (validateBtn) {
        validateBtn.addEventListener('click', () => {
            const jsonText = validateInput.value;
            
            resultsPanel.innerHTML = '<div class="result-item">Validating...</div>';
            
            fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: jsonText
            })
            .then(res => res.json())
            .then(data => {
                resultsPanel.innerHTML = '';
                
                if (data.parse_error) {
                    resultsPanel.innerHTML += `
                        <div class="result-item result-error">
                            <h4>❌ Parse Error</h4>
                            <p>${data.parse_error}</p>
                        </div>
                    `;
                    return;
                }
                
                if (data.valid) {
                    resultsPanel.innerHTML += `
                        <div class="result-item result-success">
                            <h4>✅ Valid Strategy Configuration</h4>
                            <p>The JSON passed schema validation and semantic checks.</p>
                        </div>
                    `;
                } else {
                    resultsPanel.innerHTML += `
                        <div class="result-item result-error">
                            <h4>❌ Validation Failed</h4>
                            <p>The strategy configuration has errors.</p>
                        </div>
                    `;
                }
                
                if (data.errors && data.errors.length > 0) {
                    const errHtml = data.errors.map(e => {
                        const msg = typeof e === 'string' ? e : `<strong>[${e.path}]</strong> ${e.message}`;
                        return `<li>${msg}</li>`;
                    }).join('');
                    resultsPanel.innerHTML += `
                        <div class="result-item result-error">
                            <h4>Errors</h4>
                            <ul>${errHtml}</ul>
                        </div>
                    `;
                }
                
                if (data.warnings && data.warnings.length > 0) {
                    const warnHtml = data.warnings.map(w => {
                        const msg = typeof w === 'string' ? w : `<strong>[${w.path}]</strong> ${w.message}`;
                        return `<li>${msg}</li>`;
                    }).join('');
                    resultsPanel.innerHTML += `
                        <div class="result-item result-warning">
                            <h4>Warnings</h4>
                            <ul>${warnHtml}</ul>
                        </div>
                    `;
                }
            })
            .catch(err => {
                resultsPanel.innerHTML = `
                    <div class="result-item result-error">
                        <h4>❌ Request Failed</h4>
                        <p>${err.message}</p>
                    </div>
                `;
            });
        });
    }

});


/* ═══════════════════════════════════════════════════════════════════
   STOCK AUTOCOMPLETE — Reusable across pages
   ═══════════════════════════════════════════════════════════════════ */

class StockAutocomplete {
  constructor(inputEl, options = {}) {
    this.input = typeof inputEl === 'string' ? document.getElementById(inputEl) : inputEl;
    if (!this.input) return;

    this.multi = options.multi || false;
    this.onSelect = options.onSelect || null;
    this.maxResults = options.maxResults || 20;
    this.stocks = null;
    this.activeIndex = -1;
    this.visible = false;

    this._setup();
  }

  _setup() {
    // Create dropdown as a PORTAL on document.body (escapes all stacking contexts)
    this.dropdown = document.createElement('div');
    this.dropdown.className = 'autocomplete-dropdown';
    document.body.appendChild(this.dropdown);

    // Event listeners
    this.input.addEventListener('input', () => this._onInput());
    this.input.addEventListener('focus', () => this._onInput());
    this.input.addEventListener('keydown', (e) => this._onKeyDown(e));

    // Close on outside click (neither input nor dropdown)
    document.addEventListener('click', (e) => {
      if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
        this._hide();
      }
    });

    // Reposition on scroll/resize
    window.addEventListener('scroll', () => { if (this.visible) this._position(); }, true);
    window.addEventListener('resize', () => { if (this.visible) this._position(); });
  }

  _position() {
    const rect = this.input.getBoundingClientRect();
    this.dropdown.style.position = 'fixed';
    this.dropdown.style.top = rect.bottom + 'px';
    this.dropdown.style.left = rect.left + 'px';
    this.dropdown.style.width = rect.width + 'px';
  }

  async _loadStocks() {
    if (this.stocks) return;
    try {
      const res = await fetch('/api/stocks');
      const data = await res.json();
      this.stocks = data.stocks;
    } catch (e) {
      this.stocks = [];
    }
  }

  async _onInput() {
    await this._loadStocks();

    let query = this.input.value.trim().toUpperCase();

    if (this.multi) {
      const parts = query.split(',');
      query = parts[parts.length - 1].trim();
    }

    if (!query) {
      // Empty: show top 20 most volatile Nifty 50 stocks
      const volatile = this.stocks
        .filter(s => s.volatility_rank != null)
        .sort((a, b) => a.volatility_rank - b.volatility_rank)
        .slice(0, this.maxResults);
      this._render(volatile, '', 'Top Nifty 50 by Volatility');
      return;
    }

    // Typing: alphabetical filter (starts-with first, then contains)
    const starts = [];
    const contains = [];
    for (const s of this.stocks) {
      if (s.symbol.startsWith(query)) starts.push(s);
      else if (s.symbol.includes(query)) contains.push(s);
    }
    const filtered = [...starts, ...contains].slice(0, this.maxResults);
    this._render(filtered, query);
  }

  _render(results, query, headerLabel) {
    this.activeIndex = -1;
    this.dropdown.innerHTML = '';

    if (headerLabel) {
      const hdr = document.createElement('div');
      hdr.className = 'autocomplete-count';
      hdr.style.borderTop = 'none';
      hdr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
      hdr.style.textAlign = 'left';
      hdr.style.fontWeight = '600';
      hdr.style.color = '#94a3b8';
      hdr.style.fontSize = '0.7rem';
      hdr.style.letterSpacing = '1px';
      hdr.style.textTransform = 'uppercase';
      hdr.textContent = headerLabel;
      this.dropdown.appendChild(hdr);
    }

    if (results.length === 0) {
      this.dropdown.innerHTML += '<div class="autocomplete-no-results">No matching stocks found</div>';
      this._show();
      return;
    }

    results.forEach((stock, idx) => {
      const item = document.createElement('div');
      item.className = 'autocomplete-item';
      item.dataset.index = idx;
      item.dataset.symbol = stock.symbol;

      let symbolHtml = stock.symbol;
      if (query) {
        const matchIdx = stock.symbol.indexOf(query);
        if (matchIdx >= 0) {
          symbolHtml =
            stock.symbol.slice(0, matchIdx) +
            '<span class="match">' + stock.symbol.slice(matchIdx, matchIdx + query.length) + '</span>' +
            stock.symbol.slice(matchIdx + query.length);
        }
      }

      let badges = '';
      if (stock.fno) {
        badges += '<span class="autocomplete-badge fno">F&O</span>';
      }
      if (stock.lot_size) {
        badges += `<span class="autocomplete-badge lot">Lot: ${stock.lot_size}</span>`;
      }

      item.innerHTML = `
        <span class="autocomplete-symbol">${symbolHtml}</span>
        ${badges}
      `;

      item.addEventListener('click', () => this._select(stock.symbol));
      item.addEventListener('mouseenter', () => {
        this._clearActive();
        this.activeIndex = idx;
        item.classList.add('active');
      });

      this.dropdown.appendChild(item);
    });

    const countEl = document.createElement('div');
    countEl.className = 'autocomplete-count';
    const total = this.stocks ? this.stocks.length : 0;
    countEl.textContent = results.length < total
      ? `Showing ${results.length} of ${total} stocks`
      : `${total} stocks available`;
    this.dropdown.appendChild(countEl);

    this._show();
  }

  _select(symbol) {
    if (this.multi) {
      const parts = this.input.value.split(',').map(s => s.trim()).filter(Boolean);
      parts[parts.length - 1] = symbol;
      this.input.value = parts.join(', ') + ', ';
    } else {
      this.input.value = symbol;
    }
    this._hide();
    if (this.onSelect) this.onSelect(symbol);
    this.input.focus();
  }

  _onKeyDown(e) {
    if (!this.visible) return;

    const items = this.dropdown.querySelectorAll('.autocomplete-item');
    if (!items.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this._clearActive();
      this.activeIndex = Math.min(this.activeIndex + 1, items.length - 1);
      items[this.activeIndex].classList.add('active');
      items[this.activeIndex].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this._clearActive();
      this.activeIndex = Math.max(this.activeIndex - 1, 0);
      items[this.activeIndex].classList.add('active');
      items[this.activeIndex].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (this.activeIndex >= 0 && items[this.activeIndex]) {
        this._select(items[this.activeIndex].dataset.symbol);
      } else if (items.length === 1) {
        this._select(items[0].dataset.symbol);
      } else {
        this._hide();
      }
    } else if (e.key === 'Escape') {
      this._hide();
    }
  }

  _clearActive() {
    this.dropdown.querySelectorAll('.autocomplete-item.active').forEach(el => el.classList.remove('active'));
  }

  _show() {
    this._position();
    this.dropdown.classList.add('visible');
    this.visible = true;
  }

  _hide() {
    this.dropdown.classList.remove('visible');
    this.visible = false;
    this.activeIndex = -1;
  }
}


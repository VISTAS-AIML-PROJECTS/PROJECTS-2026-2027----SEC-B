document.addEventListener('DOMContentLoaded', () => {
    const btnScan = document.getElementById('btn-scan');
    const windowSelect = document.getElementById('window-select');
    const scanSummary = document.getElementById('scan-summary');
    const resultsGrid = document.getElementById('results-grid');
    const loadingSpinner = document.getElementById('loading-spinner');
    const noResults = document.getElementById('no-results');
    const sourcesList = document.getElementById('sources-list');
    const sourcesSpinner = document.getElementById('sources-spinner');

    loadSources();
    btnScan.addEventListener('click', scanContracts);

    async function scanContracts() {
        const windowHours = parseInt(windowSelect.value);

        resultsGrid.innerHTML = '';
        noResults.style.display = 'none';
        scanSummary.style.display = 'none';
        loadingSpinner.style.display = 'block';
        btnScan.disabled = true;
        btnScan.textContent = '⏳ Scanning…';

        try {
            const response = await fetch('/api/convergence/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ window_hours: windowHours })
            });

            if (!response.ok) throw new Error('Scan failed');
            const data = await response.json();

            // Summary bar
            scanSummary.style.display = 'block';
            const convLabel = data.convergence_count > 0
                ? `<strong style="color: #34d399;">🔥 ${data.convergence_count} convergence signal${data.convergence_count > 1 ? 's' : ''}</strong> (2+ sources on same contract)`
                : `<span style="color: var(--text-muted);">No convergence — showing top individual picks</span>`;
            scanSummary.innerHTML = `
                Scanned <strong>${data.total_calls_scanned}</strong> analyst calls ·
                <strong>${data.unique_contracts}</strong> unique contracts ·
                ${convLabel}
            `;

            renderContracts(data.contracts || []);
        } catch (error) {
            console.error('Scan error:', error);
            resultsGrid.innerHTML = `<div style="color: var(--error); padding: 1rem;">Scan failed. Please try again.</div>`;
        } finally {
            loadingSpinner.style.display = 'none';
            btnScan.disabled = false;
            btnScan.textContent = '🔍 Scan All Contracts';
        }
    }

    function renderContracts(contracts) {
        if (contracts.length === 0) {
            noResults.style.display = 'block';
            return;
        }

        contracts.forEach((c, idx) => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.style.animationDelay = `${idx * 0.06}s`;

            // Convergence glow for 2+ sources
            if (c.is_convergence) {
                card.style.border = '1px solid rgba(52, 211, 153, 0.4)';
                card.style.boxShadow = '0 0 20px rgba(52, 211, 153, 0.1)';
            }

            const optBadge = c.option_type === 'CE'
                ? '<span style="background:rgba(16,185,129,0.2); color:#34d399; padding:0.2rem 0.6rem; border-radius:6px; font-weight:700; font-size:0.85rem;">CE CALL</span>'
                : '<span style="background:rgba(239,68,68,0.2); color:#fca5a5; padding:0.2rem 0.6rem; border-radius:6px; font-weight:700; font-size:0.85rem;">PE PUT</span>';

            const dirBadge = c.consensus_direction === 'LONG'
                ? '<span class="badge badge-long" style="font-size:0.75rem; padding:0.25rem 0.5rem;">BUY ↑</span>'
                : '<span class="badge badge-short" style="font-size:0.75rem; padding:0.25rem 0.5rem;">SELL ↓</span>';

            const expiry = c.expiry_date
                ? new Date(c.expiry_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
                : 'N/A';

            const convergenceTag = c.is_convergence
                ? `<span style="background: linear-gradient(135deg, rgba(16,185,129,0.3), rgba(59,130,246,0.3)); color: #6ee7b7; padding: 0.25rem 0.7rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.5px;">🔥 CONVERGENCE · ${c.source_count} SOURCES</span>`
                : `<span style="background: rgba(255,255,255,0.05); color: var(--text-muted); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem;">1 source</span>`;

            // Sources list
            let sourcesHtml = '';
            if (c.sources && c.sources.length > 0) {
                sourcesHtml = `<div style="margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem;">
                    ${c.sources.map(src => {
                        const typeBadge = getTypeBadgeClass(src.source_type);
                        const srcDir = src.direction === 'LONG'
                            ? '<span class="badge badge-long" style="font-size:0.65rem;">BUY ↑</span>'
                            : '<span class="badge badge-short" style="font-size:0.65rem;">SELL ↓</span>';
                        const time = new Date(src.published_at).toLocaleString('en-IN', {
                            day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
                        });
                        const sourceName = src.source_name || src.source_id;
                        const sourceLink = src.source_url ? `<a href="${src.source_url}" target="_blank" style="color: var(--accent-cyan); text-decoration: none; font-weight: 600;">${sourceName}</a>` : `<span class="source-name">${sourceName}</span>`;
                        
                        return `
                        <div class="source-item">
                            <div class="source-item-left">
                                <span class="badge ${typeBadge}" style="font-size:0.6rem;">${formatType(src.source_type)}</span>
                                ${sourceLink}
                            </div>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                ${srcDir}
                                <span style="font-size: 0.7rem; color: var(--text-muted);">${time}</span>
                            </div>
                        </div>`;
                    }).join('')}
                </div>`;
            }

            card.innerHTML = `
                <div class="result-header">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div class="result-symbol">${c.symbol}</div>
                        ${optBadge}
                        ${dirBadge}
                    </div>
                    ${convergenceTag}
                </div>
                <div style="display: flex; gap: 2rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Expiry</div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-main);">${expiry}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Sources</div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: ${c.is_convergence ? '#34d399' : 'var(--text-main)'};">${c.source_count} independent</div>
                    </div>
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Total Calls</div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-main);">${c.total_calls}</div>
                    </div>
                </div>
                ${sourcesHtml}
            `;
            resultsGrid.appendChild(card);
        });
    }

    async function loadSources() {
        try {
            const response = await fetch('/api/convergence/sources');
            if (!response.ok) throw new Error('Failed');
            const data = await response.json();

            sourcesSpinner.style.display = 'none';
            sourcesList.innerHTML = '';

            if (!data.sources || data.sources.length === 0) {
                sourcesList.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">No sources registered.</div>';
                return;
            }

            data.sources.forEach(src => {
                const typeBadge = getTypeBadgeClass(src.source_type);
                const sourceName = src.source_name || src.source_id;
                const sourceLink = src.source_url ? `<a href="${src.source_url}" target="_blank" style="color: var(--accent-cyan); text-decoration: none; font-weight: 600; font-size: 0.95rem;">${sourceName}</a>` : `<span class="leaderboard-name">${sourceName}</span>`;
                
                const item = document.createElement('div');
                item.className = 'leaderboard-item';
                item.innerHTML = `
                    <div style="display: flex; flex-direction: column; gap: 0.3rem;">
                        ${sourceLink}
                        <span class="badge ${typeBadge}" style="align-self: flex-start; font-size: 0.6rem;">${formatType(src.source_type)}</span>
                    </div>
                `;
                sourcesList.appendChild(item);
            });
        } catch (error) {
            sourcesSpinner.style.display = 'none';
            sourcesList.innerHTML = '<div style="color: var(--error); font-size: 0.85rem;">Failed to load sources.</div>';
        }
    }

    function getTypeBadgeClass(type) {
        const t = (type || '').toLowerCase();
        if (t.includes('analyst')) return 'badge-analyst';
        if (t.includes('news')) return 'badge-news';
        if (t.includes('public') || t.includes('commentary')) return 'badge-public';
        return 'badge-analyst';
    }

    function formatType(type) {
        return (type || 'Unknown').replace(/_/g, ' ');
    }
});

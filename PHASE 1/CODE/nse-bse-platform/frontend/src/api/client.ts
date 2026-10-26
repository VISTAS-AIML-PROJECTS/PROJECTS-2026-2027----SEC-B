import {
  InstrumentSearchResponse,
  InstrumentSearchParams,
  Instrument,
  OptionChainResponse,
  FuturesDashboardResponse,
  SyncStatus,
  SyncChangeItem,
  Universe,
  PredictionResponse,
  MarketOpportunitiesResponse
} from '../types';

const API_BASE = '/api';

export const api = {
  async searchInstruments(params: InstrumentSearchParams): Promise<InstrumentSearchResponse> {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.exchange) query.append('exchange', params.exchange);
    if (params.segment) query.append('segment', params.segment);
    if (params.instrument_type) query.append('instrument_type', params.instrument_type);
    if (params.universe_id) query.append('universe_id', params.universe_id);
    if (params.has_fno !== undefined) query.append('has_fno', String(params.has_fno));
    if (params.page) query.append('page', String(params.page));
    if (params.page_size) query.append('page_size', String(params.page_size));
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.sort_order) query.append('sort_order', params.sort_order);

    const res = await fetch(`${API_BASE}/instruments/search?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch instruments');
    return res.json();
  },

  async getInstrumentDetail(token: string): Promise<Instrument> {
    const res = await fetch(`${API_BASE}/instruments/detail/${encodeURIComponent(token)}`);
    if (!res.ok) throw new Error('Failed to fetch instrument detail');
    return res.json();
  },

  async checkDerivatives(symbol: string) {
    const res = await fetch(`${API_BASE}/instruments/check-fno/${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('Failed to check derivatives');
    return res.json();
  },

  async getOptionChain(symbol: string, expiry?: string): Promise<OptionChainResponse> {
    const query = new URLSearchParams({ symbol });
    if (expiry) query.append('expiry', expiry);
    const res = await fetch(`${API_BASE}/derivatives/option-chain?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch option chain');
    return res.json();
  },

  async getFutures(symbol: string): Promise<FuturesDashboardResponse> {
    const res = await fetch(`${API_BASE}/derivatives/futures?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('Failed to fetch futures');
    return res.json();
  },

  async getExpiries(symbol: string): Promise<{ symbol: string; expiries: string[]; has_derivatives: boolean }> {
    const res = await fetch(`${API_BASE}/derivatives/expiries?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) throw new Error('Failed to fetch expiries');
    return res.json();
  },

  async getSyncStatus(): Promise<SyncStatus> {
    const res = await fetch(`${API_BASE}/sync/status`);
    if (!res.ok) throw new Error('Failed to fetch sync status');
    return res.json();
  },

  async getSyncHistory(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/sync/history`);
    if (!res.ok) throw new Error('Failed to fetch sync history');
    return res.json();
  },

  async getSyncChanges(params?: { sync_id?: number; change_type?: string }): Promise<SyncChangeItem[]> {
    const query = new URLSearchParams();
    if (params?.sync_id) query.append('sync_id', String(params.sync_id));
    if (params?.change_type) query.append('change_type', params.change_type);
    const res = await fetch(`${API_BASE}/sync/changes?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch sync changes');
    return res.json();
  },

  async triggerSync(provider: string = 'kite') {
    const res = await fetch(`${API_BASE}/sync/trigger?provider=${provider}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to trigger sync');
    return res.json();
  },

  async getUniverses(): Promise<Universe[]> {
    const res = await fetch(`${API_BASE}/universes`);
    if (!res.ok) throw new Error('Failed to fetch universes');
    return res.json();
  },

  async getUniverseMembers(universeId: string, limit = 50, offset = 0) {
    const res = await fetch(`${API_BASE}/universes/${universeId}?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Failed to fetch universe members');
    return res.json();
  },

  async addToWatchlist(token: string) {
    const res = await fetch(`${API_BASE}/universes/watchlist/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instrument_token: token })
    });
    return res.json();
  },

  async removeFromWatchlist(token: string) {
    const res = await fetch(`${API_BASE}/universes/watchlist/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instrument_token: token })
    });
    return res.json();
  },

  async getModelBenchmarks() {
    const res = await fetch(`${API_BASE}/models/benchmarks`);
    if (!res.ok) throw new Error('Failed to fetch model benchmarks');
    return res.json();
  },

  async getModelInference(symbol: string, strategy: string = 'global') {
    const res = await fetch(`${API_BASE}/models/inference?symbol=${encodeURIComponent(symbol)}&strategy=${strategy}`);
    if (!res.ok) throw new Error('Failed to fetch model inference');
    return res.json();
  },

  async getMarketDataStats() {
    const res = await fetch(`${API_BASE}/market-data/stats`);
    if (!res.ok) throw new Error('Failed to fetch market data stats');
    return res.json();
  },

  async getForecast(symbol: string): Promise<PredictionResponse> {
    const res = await fetch(`${API_BASE}/prediction/forecast?symbol=${encodeURIComponent(symbol)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch prediction' }));
      throw new Error(err.detail || 'Failed to fetch prediction');
    }
    return res.json();
  },

  async getMarketOpportunities(): Promise<MarketOpportunitiesResponse> {
    const res = await fetch(`${API_BASE}/prediction/opportunities`);
    if (!res.ok) throw new Error('Failed to fetch market opportunities');
    return res.json();
  },

  // --- AI Copilot Endpoints ---
  async getAiConfig(): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/config`);
    if (!res.ok) throw new Error('Failed to fetch AI configuration');
    return res.json();
  },

  async updateAiConfig(payload: { provider?: string; gemini_key?: string; openai_key?: string; groq_key?: string }) {
    const res = await fetch(`${API_BASE}/ai/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to update AI configuration');
    return res.json();
  },

  async analyzeStock(symbol: string, custom_prompt?: string, provider?: string, api_key?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/analyze-stock`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, custom_prompt, provider, api_key })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to analyze stock with AI' }));
      throw new Error(err.detail || 'Failed to analyze stock with AI');
    }
    return res.json();
  },

  async chatWithAi(messages: { role: string; content: string }[], symbol?: string, provider?: string, api_key?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, symbol, provider, api_key })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to chat with AI copilot' }));
      throw new Error(err.detail || 'Failed to chat with AI copilot');
    }
    return res.json();
  }
};

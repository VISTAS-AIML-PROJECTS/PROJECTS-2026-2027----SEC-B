export interface Instrument {
  id: number;
  instrument_token: string;
  exchange_token: string;
  trading_symbol: string;
  name: string;
  exchange: 'NSE' | 'BSE' | 'NFO' | 'BFO' | string;
  segment: string;
  instrument_type: 'EQ' | 'FUTSTK' | 'OPTSTK' | 'FUTIDX' | 'OPTIDX' | 'INDEX' | string;
  isin?: string;
  series?: string;
  tick_size: number;
  lot_size: number;
  strike: number;
  option_type?: 'CE' | 'PE';
  expiry?: string;
  underlying_symbol?: string;
  is_active: number;
  listing_status: string;
  trading_status: string;
  provider: string;
  metadata_json?: string;
  last_sync_at: string;
  has_derivatives: number;
  last_price?: number;
  change?: number;
  change_percent?: number;
  volume?: number;
}

export interface InstrumentSearchParams {
  q?: string;
  exchange?: string;
  segment?: string;
  instrument_type?: string;
  universe_id?: string;
  has_fno?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface InstrumentSearchResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  instruments: Instrument[];
}

export interface OptionLeg {
  instrument_token?: string;
  trading_symbol?: string;
  ltp?: number;
  change?: number;
  change_percent?: number;
  oi?: number;
  oi_change?: number;
  volume?: number;
  iv?: number;
  bid?: number;
  ask?: number;
  is_itm: boolean;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  data_available: boolean;
}

export interface OptionChainStrikeRow {
  strike: number;
  is_atm: boolean;
  call?: OptionLeg;
  put?: OptionLeg;
}

export interface OptionAnalyticsSummary {
  pcr_oi?: number;
  pcr_volume?: number;
  total_call_oi: number;
  total_put_oi: number;
  total_call_volume: number;
  total_put_volume: number;
  max_pain_strike?: number;
  call_oi_concentration_strike?: number;
  put_oi_concentration_strike?: number;
  atm_strike?: number;
  atm_straddle_price?: number;
  atm_iv?: number;
}

export interface OptionChainResponse {
  underlying_symbol: string;
  exchange: string;
  spot_price?: number;
  atm_strike?: number;
  has_derivatives: boolean;
  message?: string;
  available_expiries: string[];
  selected_expiry?: string;
  strikes: OptionChainStrikeRow[];
  analytics?: OptionAnalyticsSummary;
}

export interface FuturesContractRow {
  instrument_token: string;
  trading_symbol: string;
  exchange: string;
  expiry: string;
  futures_price?: number;
  spot_price?: number;
  basis?: number;
  basis_percent?: number;
  oi?: number;
  oi_change?: number;
  volume?: number;
  interpretation: string;
  data_available: boolean;
}

export interface FuturesDashboardResponse {
  underlying_symbol: string;
  exchange: string;
  spot_price?: number;
  has_derivatives: boolean;
  message?: string;
  contracts: FuturesContractRow[];
  interpretation_disclaimer: string;
}

export interface SyncStatus {
  is_syncing: boolean;
  current_status: string;
  last_sync?: {
    id: number;
    started_at: string;
    completed_at?: string;
    provider: string;
    status: string;
    total_downloaded: number;
    total_inserted: number;
    total_updated: number;
    newly_listed_count: number;
    delisted_count: number;
    expired_count: number;
    lot_size_changed_count: number;
    error_message?: string;
  };
  total_active_instruments: number;
  exchange_breakdown: Record<string, number>;
}

export interface SyncChangeItem {
  id: number;
  sync_id: number;
  change_type: string;
  instrument_token: string;
  trading_symbol: string;
  exchange: string;
  old_value?: string;
  new_value?: string;
  detected_at: string;
}

export interface Universe {
  id: string;
  name: string;
  description: string;
  is_system: number;
  member_count: number;
}

export interface PivotPoints {
  pivot: number;
  r1: number;
  r2: number;
  r3: number;
  s1: number;
  s2: number;
  s3: number;
}

export interface FibonacciPivots {
  r1: number;
  r2: number;
  r3: number;
  s1: number;
  s2: number;
  s3: number;
}

export interface TradeLevels {
  strategy_name?: string;
  entry_zone: string;
  target_1: number;
  target_2: number;
  target_3?: number;
  stop_loss: number;
  trailing_stop?: number;
  expected_move_pct: string;
  volatility_atr: number;
  win_probability_pct?: number;
}

export interface TechnicalIndicators {
  rsi_14: number;
  rsi_condition: string;
  vwap: number;
  vwap_deviation_pct: number;
  ema_20: number;
  ema_50: number;
  ema_200: number;
  adx_14: number;
  adx_trend: string;
  bollinger_upper: number;
  bollinger_lower: number;
  bollinger_width_pct: number;
  macd_line: number;
  macd_signal: number;
  macd_histogram: number;
  pivot_points?: PivotPoints;
  fibonacci_pivots?: FibonacciPivots;
  supertrend?: {
    direction: 'BULLISH' | 'BEARISH';
    value: number;
  };
  volume_spike_ratio?: number;
  institutional_activity?: string;
}

export interface DerivativesConfluence {
  available: boolean;
  pcr_oi?: number;
  max_pain_strike?: number;
  futures_buildup?: string;
  basis_spread?: number;
  resistance_wall_call_oi?: number;
  support_floor_put_oi?: number;
}

export interface HistoricalAnalysis {
  perf_1w?: number;
  perf_1m?: number;
  perf_3m?: number;
  perf_6m?: number;
  perf_1y?: number;
  high_52w?: number;
  low_52w?: number;
  distance_from_52w_high_pct?: number;
  historical_volatility_pct?: number;
  quarterly_ai_target?: number;
  quarterly_ai_stop?: number;
  quarterly_risk_reward?: string;
  quarterly_catalyst?: string;
  historical_trend_summary?: string;
}

export interface HorizonItem {
  horizon_label: string;
  direction: string;
  expected_delta_pts?: number;
  expected_return_pct?: string;
  target?: number;
  stop_loss?: number;
  key_driver: string;
  confidence: number;
  risk_profile?: string;
  quarterly_catalyst?: string;
}

export interface PredictionResponse {
  symbol: string;
  name: string;
  exchange: string;
  instrument_token: string;
  has_derivatives: boolean;
  can_predict: boolean;
  status: string;
  message?: string;
  guardrail_status?: string;
  current_price?: number;
  change?: number;
  change_percent?: number;
  volume?: number;
  direction?: 'STRONG_BULLISH' | 'BULLISH' | 'NEUTRAL_RANGEBOUND' | 'BEARISH' | 'STRONG_BEARISH' | string;
  primary_bias?: string;
  bias_color?: string;
  confidence_percent?: number;
  risk_reward_ratio?: string;
  trade_levels?: TradeLevels;
  technicals?: TechnicalIndicators;
  derivatives_confluence?: DerivativesConfluence;
  horizons?: {
    ultra_short_5m: HorizonItem;
    intraday_eod: HorizonItem;
    swing_5d: HorizonItem;
    positional_1m?: HorizonItem;
    quarterly_3m?: HorizonItem;
  };
  historical_analysis?: HistoricalAnalysis;
  commentary?: string[];
  timestamp?: string;
}

// --- AI Copilot Interfaces ---
export interface AiProviderInfo {
  id: string;
  name: string;
  models: string[];
  free_key_url: string;
}

export interface AiConfigResponse {
  active_provider: string;
  has_gemini_key: boolean;
  has_openai_key: boolean;
  has_groq_key: boolean;
  gemini_key_preview: string;
  openai_key_preview: string;
  supported_providers: AiProviderInfo[];
}

export interface AiAnalyzeResponse {
  symbol: string;
  provider: string;
  model: string;
  content: string;
  trade_levels?: TradeLevels;
  technicals?: TechnicalIndicators;
  forecast?: PredictionResponse;
}

export interface AiChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface AiChatResponse {
  reply: string;
  provider: string;
  symbol: string;
}

export interface MarketOpportunitiesResponse {
  timestamp: string;
  total_scanned: number;
  top_bullish: PredictionResponse[];
  top_bearish: PredictionResponse[];
  neutral_count: number;
}


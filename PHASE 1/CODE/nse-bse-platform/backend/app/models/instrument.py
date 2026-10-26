from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class InstrumentBase(BaseModel):
    instrument_token: str
    exchange_token: str
    trading_symbol: str
    name: Optional[str] = None
    exchange: str
    segment: str
    instrument_type: str
    isin: Optional[str] = None
    series: Optional[str] = None
    tick_size: float = 0.05
    lot_size: int = 1
    strike: float = 0.0
    option_type: Optional[str] = None
    expiry: Optional[str] = None
    underlying_symbol: Optional[str] = None
    is_active: bool = True
    listing_status: str = "ACTIVE"
    trading_status: str = "TRADING"
    provider: str
    metadata_json: Optional[str] = None
    last_sync_at: str

class InstrumentResponse(InstrumentBase):
    id: int
    last_price: Optional[float] = None
    change_percent: Optional[float] = None
    volume: Optional[int] = None
    has_derivatives: Optional[bool] = None

class InstrumentSearchParams(BaseModel):
    query: str = ""
    exchange: Optional[str] = None
    segment: Optional[str] = None
    instrument_type: Optional[str] = None
    universe_id: Optional[str] = None
    has_fno: Optional[bool] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "trading_symbol"
    sort_order: str = "asc"

class OptionLeg(BaseModel):
    instrument_token: Optional[str] = None
    trading_symbol: Optional[str] = None
    ltp: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    oi: Optional[int] = None
    oi_change: Optional[int] = None
    volume: Optional[int] = None
    iv: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    is_itm: bool = False
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    data_available: bool = True

class OptionChainStrikeRow(BaseModel):
    strike: float
    is_atm: bool = False
    call: Optional[OptionLeg] = None
    put: Optional[OptionLeg] = None

class GreeksSummary(BaseModel):
    model: str = "Black-Scholes (1973)"
    risk_free_rate: float = 0.07  # 7% standard RBI T-bill rate benchmark
    calculation_valid: bool = True

class OptionAnalyticsSummary(BaseModel):
    pcr_oi: Optional[float] = None
    pcr_volume: Optional[float] = None
    total_call_oi: int = 0
    total_put_oi: int = 0
    total_call_volume: int = 0
    total_put_volume: int = 0
    max_pain_strike: Optional[float] = None
    call_oi_concentration_strike: Optional[float] = None
    put_oi_concentration_strike: Optional[float] = None
    atm_strike: Optional[float] = None
    atm_straddle_price: Optional[float] = None
    atm_iv: Optional[float] = None
    greeks: GreeksSummary = Field(default_factory=GreeksSummary)

class OptionChainResponse(BaseModel):
    underlying_symbol: str
    exchange: str
    spot_price: Optional[float] = None
    atm_strike: Optional[float] = None
    has_derivatives: bool = True
    message: Optional[str] = None
    available_expiries: List[str] = []
    selected_expiry: Optional[str] = None
    strikes: List[OptionChainStrikeRow] = []
    analytics: Optional[OptionAnalyticsSummary] = None

class FuturesContractRow(BaseModel):
    instrument_token: str
    trading_symbol: str
    exchange: str
    expiry: str
    futures_price: Optional[float] = None
    spot_price: Optional[float] = None
    basis: Optional[float] = None
    basis_percent: Optional[float] = None
    oi: Optional[int] = None
    oi_change: Optional[int] = None
    volume: Optional[int] = None
    interpretation: str  # "Potential Long Buildup", "Potential Short Buildup", "Potential Short Covering", "Potential Long Unwinding", "Neutral"
    data_available: bool = True

class FuturesDashboardResponse(BaseModel):
    underlying_symbol: str
    exchange: str
    spot_price: Optional[float] = None
    has_derivatives: bool = True
    message: Optional[str] = None
    contracts: List[FuturesContractRow] = []
    interpretation_disclaimer: str = "Market-analysis labels are quantitative classifications, not guaranteed predictions."

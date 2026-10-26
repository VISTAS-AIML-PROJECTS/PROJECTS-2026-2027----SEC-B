import logging
import math
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.services.analytics_service import OptionAnalyticsService
from app.models.instrument import (
    OptionChainResponse, OptionChainStrikeRow, OptionLeg,
    OptionAnalyticsSummary, FuturesDashboardResponse, FuturesContractRow
)

logger = logging.getLogger(__name__)

class DerivativesService:
    @staticmethod
    def get_underlying_spot(symbol: str) -> Optional[float]:
        """Fetches the latest cash/index spot price for an underlying."""
        clean_sym = symbol.strip().upper()
        alias_map = {
            "NIFTY": ["NIFTY 50", "NIFTY"],
            "BANKNIFTY": ["NIFTY BANK", "BANKNIFTY"],
            "FINNIFTY": ["NIFTY FIN SERVICE", "FINNIFTY"],
            "MIDCPNIFTY": ["NIFTY MID SELECT", "MIDCPNIFTY"],
            "SENSEX": ["SENSEX", "BSE SENSEX"],
            "BANKEX": ["BANKEX", "BSE BANKEX"]
        }
        lookup_names = alias_map.get(clean_sym, [clean_sym])
        placeholders = ",".join("?" for _ in lookup_names)

        sql = f"""
            SELECT lq.last_price 
            FROM instruments i
            JOIN live_quotes lq ON i.instrument_token = lq.instrument_token
            WHERE (i.trading_symbol IN ({placeholders}) OR i.name IN ({placeholders})) 
              AND i.exchange IN ('NSE', 'BSE') 
              AND i.instrument_type IN ('EQ', 'INDEX')
            ORDER BY CASE WHEN i.exchange = 'NSE' THEN 1 ELSE 2 END
            LIMIT 1
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, lookup_names + lookup_names)
            row = cursor.fetchone()
            if row and row["last_price"]:
                return float(row["last_price"])
        return None

    @staticmethod
    def get_available_expiries(symbol: str) -> List[str]:
        """Returns sorted list of active future expiry dates for this underlying."""
        clean_sym = symbol.strip().upper()
        today_str = date.today().isoformat()
        sql = """
            SELECT DISTINCT expiry
            FROM instruments
            WHERE underlying_symbol = ? 
              AND exchange IN ('NFO', 'BFO') 
              AND is_active = 1 
              AND expiry >= ?
            ORDER BY expiry ASC
        """
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (clean_sym, today_str))
            return [r["expiry"] for r in cursor.fetchall() if r["expiry"]]

    @classmethod
    def get_option_chain(cls, symbol: str, expiry: Optional[str] = None) -> OptionChainResponse:
        clean_sym = symbol.strip().upper()
        expiries = cls.get_available_expiries(clean_sym)

        # Dynamic derivatives check: If no active expiries exist
        if not expiries:
            return OptionChainResponse(
                underlying_symbol=clean_sym,
                exchange="NSE",
                spot_price=cls.get_underlying_spot(clean_sym),
                has_derivatives=False,
                message="Futures/Options are not available for this instrument.",
                available_expiries=[],
                selected_expiry=None,
                strikes=[]
            )

        # Pick selected expiry (default to nearest)
        selected_expiry = expiry if (expiry and expiry in expiries) else expiries[0]
        spot_price = cls.get_underlying_spot(clean_sym)

        # Query all active option contracts for this underlying & expiry
        sql = """
            SELECT 
                i.instrument_token, i.trading_symbol, i.strike, i.option_type,
                i.lot_size, i.tick_size, i.expiry, i.exchange,
                lq.last_price, lq.change, lq.change_percent,
                lq.volume, lq.oi, lq.oi_change, lq.iv, lq.bid, lq.ask, lq.status as quote_status
            FROM instruments i
            LEFT JOIN live_quotes lq ON i.instrument_token = lq.instrument_token
            WHERE i.underlying_symbol = ? 
              AND i.expiry = ? 
              AND i.instrument_type IN ('OPTSTK', 'OPTIDX')
              AND i.exchange IN ('NFO', 'BFO')
              AND i.is_active = 1
            ORDER BY i.strike ASC
        """

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (clean_sym, selected_expiry))
            rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return OptionChainResponse(
                underlying_symbol=clean_sym,
                exchange="NSE",
                spot_price=spot_price,
                has_derivatives=True,
                message="No option contracts found for the selected expiry.",
                available_expiries=expiries,
                selected_expiry=selected_expiry,
                strikes=[]
            )

        # Calculate time to expiry in years for Greeks
        try:
            exp_date = datetime.strptime(selected_expiry, "%Y-%m-%d").date()
            days_to_expiry = max(1, (exp_date - date.today()).days)
            time_to_expiry_years = days_to_expiry / 365.0
        except Exception:
            days_to_expiry = 10
            time_to_expiry_years = 10 / 365.0

        # Group rows by strike
        strikes_map: Dict[float, Dict[str, Any]] = {}
        for r in rows:
            k = float(r["strike"])
            if k not in strikes_map:
                strikes_map[k] = {"strike": k, "call": None, "put": None}

            opt_type = (r["option_type"] or "").upper()
            ltp = r.get("last_price")
            iv = r.get("iv") or 0.18

            # Calculate Greeks if spot and strike are available
            greeks = {"delta": None, "gamma": None, "theta": None, "vega": None}
            if spot_price and spot_price > 0 and k > 0:
                greeks = OptionAnalyticsService.calculate_black_scholes_greeks(
                    spot=spot_price,
                    strike=k,
                    time_to_expiry_years=time_to_expiry_years,
                    risk_free_rate=0.07,
                    volatility=iv,
                    option_type=opt_type
                )

            # Determine ITM: Call is ITM if Strike < Spot; Put is ITM if Strike > Spot
            is_itm = False
            if spot_price:
                if opt_type == "CE":
                    is_itm = k < spot_price
                elif opt_type == "PE":
                    is_itm = k > spot_price

            leg = OptionLeg(
                instrument_token=r["instrument_token"],
                trading_symbol=r["trading_symbol"],
                ltp=ltp,
                change=r.get("change"),
                change_percent=r.get("change_percent"),
                oi=r.get("oi") or 0,
                oi_change=r.get("oi_change") or 0,
                volume=r.get("volume") or 0,
                iv=round(iv * 100, 2) if iv else None,
                bid=r.get("bid"),
                ask=r.get("ask"),
                is_itm=is_itm,
                delta=greeks.get("delta"),
                gamma=greeks.get("gamma"),
                theta=greeks.get("theta"),
                vega=greeks.get("vega"),
                data_available=ltp is not None
            )

            if opt_type == "CE":
                strikes_map[k]["call"] = leg
            elif opt_type == "PE":
                strikes_map[k]["put"] = leg

        sorted_strikes = sorted(strikes_map.keys())

        # Determine ATM Strike (closest strike to spot)
        atm_strike = None
        if spot_price and sorted_strikes:
            atm_strike = min(sorted_strikes, key=lambda k: abs(k - spot_price))

        strike_rows: List[OptionChainStrikeRow] = []
        total_call_oi = 0
        total_put_oi = 0
        total_call_vol = 0
        total_put_vol = 0
        max_call_oi = -1
        max_put_oi = -1
        call_oi_strike = None
        put_oi_strike = None
        atm_straddle = None
        atm_iv = None

        for k in sorted_strikes:
            entry = strikes_map[k]
            is_atm = (k == atm_strike)

            call_leg: Optional[OptionLeg] = entry.get("call")
            put_leg: Optional[OptionLeg] = entry.get("put")

            if call_leg:
                c_oi = call_leg.oi or 0
                c_vol = call_leg.volume or 0
                total_call_oi += c_oi
                total_call_vol += c_vol
                if c_oi > max_call_oi:
                    max_call_oi = c_oi
                    call_oi_strike = k

            if put_leg:
                p_oi = put_leg.oi or 0
                p_vol = put_leg.volume or 0
                total_put_oi += p_oi
                total_put_vol += p_vol
                if p_oi > max_put_oi:
                    max_put_oi = p_oi
                    put_oi_strike = k

            if is_atm:
                c_ltp = (call_leg.ltp or 0) if call_leg else 0
                p_ltp = (put_leg.ltp or 0) if put_leg else 0
                if c_ltp > 0 or p_ltp > 0:
                    atm_straddle = round(c_ltp + p_ltp, 2)
                if call_leg and call_leg.iv:
                    atm_iv = call_leg.iv

            strike_rows.append(OptionChainStrikeRow(
                strike=k,
                is_atm=is_atm,
                call=call_leg,
                put=put_leg
            ))

        # Put-Call Ratios
        pcr_oi = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else None
        pcr_vol = round(total_put_vol / total_call_vol, 2) if total_call_vol > 0 else None

        # Max Pain
        raw_strike_dicts = [{"strike": r.strike, "call": r.call.dict() if r.call else None, "put": r.put.dict() if r.put else None} for r in strike_rows]
        max_pain = OptionAnalyticsService.calculate_max_pain(raw_strike_dicts)

        analytics = OptionAnalyticsSummary(
            pcr_oi=pcr_oi,
            pcr_volume=pcr_vol,
            total_call_oi=total_call_oi,
            total_put_oi=total_put_oi,
            total_call_volume=total_call_vol,
            total_put_volume=total_put_vol,
            max_pain_strike=max_pain,
            call_oi_concentration_strike=call_oi_strike,
            put_oi_concentration_strike=put_oi_strike,
            atm_strike=atm_strike,
            atm_straddle_price=atm_straddle,
            atm_iv=atm_iv
        )

        return OptionChainResponse(
            underlying_symbol=clean_sym,
            exchange="NSE",
            spot_price=spot_price,
            atm_strike=atm_strike,
            has_derivatives=True,
            available_expiries=expiries,
            selected_expiry=selected_expiry,
            strikes=strike_rows,
            analytics=analytics
        )

    @classmethod
    def get_futures_dashboard(cls, symbol: str) -> FuturesDashboardResponse:
        clean_sym = symbol.strip().upper()
        spot_price = cls.get_underlying_spot(clean_sym)
        today_str = date.today().isoformat()

        sql = """
            SELECT 
                i.instrument_token, i.trading_symbol, i.expiry, i.exchange,
                lq.last_price, lq.change, lq.change_percent,
                lq.volume, lq.oi, lq.oi_change, lq.status as quote_status
            FROM instruments i
            LEFT JOIN live_quotes lq ON i.instrument_token = lq.instrument_token
            WHERE i.underlying_symbol = ? 
              AND i.instrument_type IN ('FUTSTK', 'FUTIDX')
              AND i.exchange IN ('NFO', 'BFO')
              AND i.is_active = 1
              AND i.expiry >= ?
            ORDER BY i.expiry ASC
        """

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (clean_sym, today_str))
            rows = [dict(r) for r in cursor.fetchall()]

        if not rows:
            return FuturesDashboardResponse(
                underlying_symbol=clean_sym,
                exchange="NSE",
                spot_price=spot_price,
                has_derivatives=False,
                message="Futures/Options are not available for this instrument.",
                contracts=[]
            )

        contracts: List[FuturesContractRow] = []
        for r in rows:
            fut_price = r.get("last_price")
            basis = None
            basis_pct = None
            if fut_price is not None and spot_price is not None and spot_price > 0:
                basis = round(fut_price - spot_price, 2)
                basis_pct = round((basis / spot_price) * 100, 2)

            chg = r.get("change") or 0.0
            oi_chg = r.get("oi_change") or 0

            # Market Analysis Interpretation Rule
            if chg > 0 and oi_chg > 0:
                interpretation = "Potential Long Buildup"
            elif chg < 0 and oi_chg > 0:
                interpretation = "Potential Short Buildup"
            elif chg > 0 and oi_chg < 0:
                interpretation = "Potential Short Covering"
            elif chg < 0 and oi_chg < 0:
                interpretation = "Potential Long Unwinding"
            else:
                interpretation = "Neutral / Consolidation"

            contracts.append(FuturesContractRow(
                instrument_token=r["instrument_token"],
                trading_symbol=r["trading_symbol"],
                exchange=r["exchange"],
                expiry=r["expiry"],
                futures_price=fut_price,
                spot_price=spot_price,
                basis=basis,
                basis_percent=basis_pct,
                oi=r.get("oi"),
                oi_change=r.get("oi_change"),
                volume=r.get("volume"),
                interpretation=interpretation,
                data_available=fut_price is not None
            ))

        return FuturesDashboardResponse(
            underlying_symbol=clean_sym,
            exchange="NSE",
            spot_price=spot_price,
            has_derivatives=True,
            contracts=contracts
        )

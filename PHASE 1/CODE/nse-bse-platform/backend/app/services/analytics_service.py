import math
import logging
from typing import Dict, Any, Optional, Tuple
from scipy.stats import norm

logger = logging.getLogger(__name__)

class OptionAnalyticsService:
    @staticmethod
    def calculate_black_scholes_greeks(
        spot: float,
        strike: float,
        time_to_expiry_years: float,
        risk_free_rate: float = 0.07,
        volatility: float = 0.20,
        option_type: str = "CE"
    ) -> Dict[str, Optional[float]]:
        """
        Calculates European option Greeks (Delta, Gamma, Theta, Vega) using Black-Scholes formula.
        """
        if spot <= 0 or strike <= 0 or time_to_expiry_years <= 0 or volatility <= 0:
            return {"delta": None, "gamma": None, "theta": None, "vega": None}

        try:
            S = float(spot)
            K = float(strike)
            T = max(time_to_expiry_years, 0.0001)
            r = float(risk_free_rate)
            sigma = max(float(volatility), 0.01)

            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            # Standard normal pdf & cdf
            pdf_d1 = norm.pdf(d1)
            cdf_d1 = norm.cdf(d1)
            cdf_d2 = norm.cdf(d2)
            cdf_neg_d1 = norm.cdf(-d1)
            cdf_neg_d2 = norm.cdf(-d2)

            gamma = pdf_d1 / (S * sigma * math.sqrt(T))
            # Vega per 1% change in volatility
            vega = (S * pdf_d1 * math.sqrt(T)) * 0.01

            is_call = option_type.upper() == "CE"
            if is_call:
                delta = cdf_d1
                # Daily theta
                theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * cdf_d2) / 365.0
            else:
                delta = cdf_d1 - 1.0
                theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * cdf_neg_d2) / 365.0

            return {
                "delta": round(float(delta), 4),
                "gamma": round(float(gamma), 6),
                "theta": round(float(theta), 2),
                "vega": round(float(vega), 2)
            }
        except Exception as e:
            logger.warning("Error calculating Greeks: %s", str(e))
            return {"delta": None, "gamma": None, "theta": None, "vega": None}

    @staticmethod
    def calculate_max_pain(strikes_data: list) -> Optional[float]:
        """
        Calculates Max Pain strike where option writers suffer minimum cumulative loss.
        """
        if not strikes_data:
            return None

        total_loss_per_strike = {}
        for test_row in strikes_data:
            test_strike = test_row["strike"]
            loss = 0.0
            for row in strikes_data:
                k = row["strike"]
                call_oi = (row.get("call") or {}).get("oi") or 0
                put_oi = (row.get("put") or {}).get("oi") or 0

                # If underlying expires at test_strike:
                # Call loss = max(0, test_strike - k) * call_oi
                if test_strike > k:
                    loss += (test_strike - k) * call_oi
                # Put loss = max(0, k - test_strike) * put_oi
                if test_strike < k:
                    loss += (k - test_strike) * put_oi

            total_loss_per_strike[test_strike] = loss

        if not total_loss_per_strike:
            return None

        return min(total_loss_per_strike, key=total_loss_per_strike.get)

import os
import json
import logging
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.prediction_service import prediction_service

logger = logging.getLogger(__name__)

class AiAnalystService:
    def __init__(self):
        # In-memory API keys (can be set dynamically from frontend modal or .env)
        self.gemini_key: str = os.getenv("GEMINI_API_KEY", "")
        self.openai_key: str = os.getenv("OPENAI_API_KEY", "")
        self.groq_key: str = os.getenv("GROQ_API_KEY", "")
        self.active_provider: str = os.getenv("DEFAULT_AI_PROVIDER", "gemini")

    def get_config(self) -> Dict[str, Any]:
        return {
            "active_provider": self.active_provider,
            "has_gemini_key": bool(self.gemini_key),
            "has_openai_key": bool(self.openai_key),
            "has_groq_key": bool(self.groq_key),
            "gemini_key_preview": f"{self.gemini_key[:6]}...{self.gemini_key[-4:]}" if self.gemini_key else "",
            "openai_key_preview": f"{self.openai_key[:6]}...{self.openai_key[-4:]}" if self.openai_key else "",
            "supported_providers": [
                {
                    "id": "gemini",
                    "name": "Google Gemini (Recommended - Fast & Free)",
                    "models": ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
                    "free_key_url": "https://aistudio.google.com/app/apikey"
                },
                {
                    "id": "openai",
                    "name": "OpenAI ChatGPT",
                    "models": ["gpt-4o-mini", "gpt-4o"],
                    "free_key_url": "https://platform.openai.com/api-keys"
                },
                {
                    "id": "groq",
                    "name": "Groq LLaMA 3.3 (Ultra Fast)",
                    "models": ["llama-3.3-70b-versatile"],
                    "free_key_url": "https://console.groq.com/keys"
                },
                {
                    "id": "builtin",
                    "name": "Built-in Quantitative AI (Zero Key Required)",
                    "models": ["Antigravity Quant Synthesis v2.4"],
                    "free_key_url": ""
                }
            ]
        }

    def update_config(self, provider: Optional[str] = None, gemini_key: Optional[str] = None,
                      openai_key: Optional[str] = None, groq_key: Optional[str] = None) -> Dict[str, Any]:
        if provider:
            self.active_provider = provider
        if gemini_key is not None:
            self.gemini_key = gemini_key.strip()
        if openai_key is not None:
            self.openai_key = openai_key.strip()
        if groq_key is not None:
            self.groq_key = groq_key.strip()
        return self.get_config()

    def build_stock_context_prompt(self, symbol: str) -> Dict[str, Any]:
        """
        Gathers comprehensive real-time verified market data and quantitative
        indicators for the LLM context window.
        """
        forecast = prediction_service.get_forecast_for_symbol(symbol)
        if not forecast.get("can_predict"):
            return {
                "symbol": symbol,
                "can_predict": False,
                "summary": f"Could not retrieve complete quote data for {symbol}."
            }

        tech = forecast.get("technicals", {})
        levels = forecast.get("trade_levels", {})
        pivots = tech.get("pivot_points", {})
        fib_pivots = tech.get("fibonacci_pivots", {})
        supertrend = tech.get("supertrend", {})
        deriv = forecast.get("derivatives_confluence", {})
        horizons = forecast.get("horizons", {})
        hist = forecast.get("historical_analysis", {})
        q3m = horizons.get("quarterly_3m", {})

        context_text = f"""
=== REAL-TIME INDIAN MARKET VERIFIED DATA (NSE / BSE) ===
Instrument: {forecast.get('symbol')} ({forecast.get('name')})
Exchange: {forecast.get('exchange')}
Current Live Market Price (LTP): ₹{forecast.get('current_price')}
Day Change: {forecast.get('change')} ({forecast.get('change_percent')}%)
Volume: {forecast.get('volume'):,} (Institutional Activity: {tech.get('institutional_activity')}, Spike Ratio: {tech.get('volume_spike_ratio')})

--- HISTORICAL PERFORMANCE & 3-MONTH OUTLOOK ---
Past Performance: 1W: {hist.get('perf_1w')}% | 1M: {hist.get('perf_1m')}% | 3M: {hist.get('perf_3m')}% | 6M: {hist.get('perf_6m')}% | 1Y: {hist.get('perf_1y')}%
52-Week Range: Low ₹{hist.get('low_52w')} to High ₹{hist.get('high_52w')} ({hist.get('distance_from_52w_high_pct')}% from 52W High)
Annualized Historical Volatility: {hist.get('historical_volatility_pct')}%
Historical Trend Context: {hist.get('historical_trend_summary')}
3-Month Projected Target: ₹{q3m.get('target') or hist.get('quarterly_ai_target')} ({q3m.get('expected_return_pct')}) | Stop: ₹{q3m.get('stop_loss') or hist.get('quarterly_ai_stop')}
Quarterly Catalyst: {q3m.get('quarterly_catalyst')}

--- TECHNICAL INDICATORS ---
VWAP (Session Mean): ₹{tech.get('vwap')} (Deviation: {tech.get('vwap_deviation_pct')}%)
RSI (14-period): {tech.get('rsi_14')} ({tech.get('rsi_condition')})
20 EMA: ₹{tech.get('ema_20')} | 50 EMA: ₹{tech.get('ema_50')} | 200 EMA (Macro): ₹{tech.get('ema_200')}
Supertrend (14, 3.0): {supertrend.get('direction')} at ₹{supertrend.get('value')}
Bollinger Bands: Upper ₹{tech.get('bollinger_upper')} | Lower ₹{tech.get('bollinger_lower')} (Bandwidth: {tech.get('bollinger_width_pct')}%)
MACD Line: {tech.get('macd_line')} | Signal: {tech.get('macd_signal')} | Histogram: {tech.get('macd_histogram')}
ADX (Trend Strength): {tech.get('adx_14')} ({tech.get('adx_trend')})

--- PIVOT POINTS (INTRADAY KEY LEVELS) ---
Classical Floor Pivots:
- Resistance 3 (R3): ₹{pivots.get('r3')}
- Resistance 2 (R2): ₹{pivots.get('r2')}
- Resistance 1 (R1): ₹{pivots.get('r1')}
- Session Central Pivot (P): ₹{pivots.get('pivot')}
- Support 1 (S1): ₹{pivots.get('s1')}
- Support 2 (S2): ₹{pivots.get('s2')}
- Support 3 (S3): ₹{pivots.get('s3')}

Fibonacci Pivots:
- Fib R1: ₹{fib_pivots.get('r1')} | Fib R2: ₹{fib_pivots.get('r2')}
- Fib S1: ₹{fib_pivots.get('s1')} | Fib S2: ₹{fib_pivots.get('s2')}

--- DERIVATIVES CONFLUENCE (F&O) ---
Available: {deriv.get('available')}
Put-Call Ratio (PCR OI): {deriv.get('pcr_oi') or 'N/A'}
Max Pain Strike: ₹{deriv.get('max_pain_strike') or 'N/A'}
Resistance Wall (Max Call OI): ₹{deriv.get('resistance_wall_call_oi') or 'N/A'}
Support Floor (Max Put OI): ₹{deriv.get('support_floor_put_oi') or 'N/A'}
Futures Buildup: {deriv.get('futures_buildup') or 'N/A'}

--- QUANTITATIVE PREDICTION & ACTIONABLE SETUP ---
Direction Bias: {forecast.get('direction')} ({forecast.get('primary_bias')})
Confidence / Win Probability: {forecast.get('confidence_percent')}%
Strategy Name: {levels.get('strategy_name')}
Suggested Entry Zone: ₹{levels.get('entry_zone')}
Target 1 (Conservative): ₹{levels.get('target_1')}
Target 2 (Extended): ₹{levels.get('target_2')}
Target 3 (Runner): ₹{levels.get('target_3')}
Invalidation / Stop Loss: ₹{levels.get('stop_loss')}
Trailing Risk Stop: ₹{levels.get('trailing_stop')}
Risk-to-Reward Ratio: {forecast.get('risk_reward_ratio')}
ATR Volatility: ₹{levels.get('volatility_atr')}
"""
        return {
            "symbol": forecast.get("symbol"),
            "can_predict": True,
            "forecast": forecast,
            "context_text": context_text
        }

    async def analyze_stock(self, symbol: str, custom_prompt: Optional[str] = None,
                            provider: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates an institutional-grade deep AI stock analysis incorporating real live quotes,
        pivots, indicators, derivatives sentiment, and actionable setups.
        """
        ctx = self.build_stock_context_prompt(symbol)
        if not ctx.get("can_predict"):
            return {
                "symbol": symbol,
                "status": "ERROR",
                "content": f"Unable to analyze {symbol}. Instrument quote or data could not be retrieved from the exchange feed."
            }

        forecast = ctx["forecast"]
        context_text = ctx["context_text"]

        user_query = custom_prompt or (
            f"Provide a comprehensive, high-precision institutional trading and investment analysis for {symbol}. "
            "Include: (1) Executive Summary & Market Bias, (2) Price Action & Key Pivot Levels, "
            "(3) Quantitative Trade Setup (Entry, Targets, Stop-loss, Risk:Reward), "
            "(4) Derivatives & Open Interest Confluence (if F&O), and (5) Specific Multi-Horizon Action Plan (Intraday, Swing, Positional)."
        )

        system_instruction = (
            "You are an Elite Institutional Algorithmic Quantitative Trader and Technical Analyst specializing in "
            "Indian equities and derivatives (NSE/BSE). You strictly analyze verified authentic market data provided to you. "
            "Never hallucinate prices or invent strikes. Always reference the exact live LTP, VWAP, classical pivots (R1/S1/P), "
            "Supertrend, and ATR. Structure your response with clean Markdown headers, bullet points, and exact numeric trade plans."
        )

        chosen_provider = provider or self.active_provider
        override_key = api_key or (
            self.gemini_key if chosen_provider == "gemini" else (
                self.openai_key if chosen_provider == "openai" else self.groq_key
            )
        )

        # 1. Try Gemini
        if chosen_provider == "gemini" and override_key:
            try:
                response_text = await self._call_gemini(system_instruction, context_text, user_query, override_key)
                return {
                    "symbol": symbol,
                    "provider": "gemini",
                    "model": "gemini-1.5-flash",
                    "content": response_text,
                    "trade_levels": forecast.get("trade_levels"),
                    "technicals": forecast.get("technicals"),
                    "forecast": forecast
                }
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to built-in quant engine: {e}")

        # 2. Try OpenAI
        elif chosen_provider == "openai" and override_key:
            try:
                response_text = await self._call_openai(system_instruction, context_text, user_query, override_key)
                return {
                    "symbol": symbol,
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "content": response_text,
                    "trade_levels": forecast.get("trade_levels"),
                    "technicals": forecast.get("technicals"),
                    "forecast": forecast
                }
            except Exception as e:
                logger.warning(f"OpenAI API call failed, falling back to built-in quant engine: {e}")

        # 3. Try Groq
        elif chosen_provider == "groq" and override_key:
            try:
                response_text = await self._call_groq(system_instruction, context_text, user_query, override_key)
                return {
                    "symbol": symbol,
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile",
                    "content": response_text,
                    "trade_levels": forecast.get("trade_levels"),
                    "technicals": forecast.get("technicals"),
                    "forecast": forecast
                }
            except Exception as e:
                logger.warning(f"Groq API call failed, falling back to built-in quant engine: {e}")

        # 4. Fallback to High-Quality Built-In Quantitative AI Engine (Zero-Key)
        built_in_analysis = self._generate_builtin_quant_analysis(forecast)
        return {
            "symbol": symbol,
            "provider": "builtin",
            "model": "Antigravity Quant Synthesis v2.4",
            "content": built_in_analysis,
            "trade_levels": forecast.get("trade_levels"),
            "technicals": forecast.get("technicals"),
            "forecast": forecast
        }

    async def chat(self, messages: List[Dict[str, str]], symbol: Optional[str] = None,
                   provider: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Conversational chat endpoint with live stock awareness.
        """
        latest_user_message = messages[-1]["content"] if messages else "Analyze market outlook."
        sym = symbol or "NIFTY"
        
        # Build prompt with stock context
        ctx = self.build_stock_context_prompt(sym)
        context_str = ctx.get("context_text", "")
        forecast = ctx.get("forecast")

        system_instruction = (
            f"You are Antigravity Stock AI, an expert Indian Market trading copilot for NSE and BSE. "
            f"The trader is asking questions about {sym}. Use the following live market data as your single source of truth:\n\n"
            f"{context_str}\n\n"
            "Answer directly, professionally, with exact price levels, rationale, and disciplined risk management."
        )

        chosen_provider = provider or self.active_provider
        override_key = api_key or (
            self.gemini_key if chosen_provider == "gemini" else (
                self.openai_key if chosen_provider == "openai" else self.groq_key
            )
        )

        if chosen_provider == "gemini" and override_key:
            try:
                reply = await self._call_gemini_chat(system_instruction, messages, override_key)
                return {"reply": reply, "provider": "gemini", "symbol": sym}
            except Exception as e:
                logger.warning(f"Gemini chat failed: {e}")

        elif chosen_provider == "openai" and override_key:
            try:
                reply = await self._call_openai_chat(system_instruction, messages, override_key)
                return {"reply": reply, "provider": "openai", "symbol": sym}
            except Exception as e:
                logger.warning(f"OpenAI chat failed: {e}")

        elif chosen_provider == "groq" and override_key:
            try:
                reply = await self._call_groq_chat(system_instruction, messages, override_key)
                return {"reply": reply, "provider": "groq", "symbol": sym}
            except Exception as e:
                logger.warning(f"Groq chat failed: {e}")

        # Built-in response
        reply = self._generate_builtin_chat_reply(latest_user_message, forecast, sym)
        return {"reply": reply, "provider": "builtin", "symbol": sym}

    # --- HTTP Call Implementations ---
    async def _call_gemini(self, system: str, context: str, user_prompt: str, key: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system}\n\n{context}\n\nUser Question:\n{user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.25,
                "maxOutputTokens": 2048
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Gemini API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and candidates[0].get("content", {}).get("parts"):
                return candidates[0]["content"]["parts"][0]["text"]
            raise Exception("No text returned by Gemini API")

    async def _call_gemini_chat(self, system: str, messages: List[Dict[str, str]], key: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        # Convert chat history to Gemini format
        contents = []
        for m in messages[:-1]:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
        
        last_msg = messages[-1]["content"] if messages else "Hello"
        contents.append({"role": "user", "parts": [{"text": f"{system}\n\nUser Question:\n{last_msg}"}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 2048
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Gemini chat error: {resp.status_code} - {resp.text}")
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates and candidates[0].get("content", {}).get("parts"):
                return candidates[0]["content"]["parts"][0]["text"]
            raise Exception("Empty response from Gemini")

    async def _call_openai(self, system: str, context: str, user_prompt: str, key: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": f"{system}\n\n{context}"},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.25,
            "max_tokens": 2048
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"OpenAI error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_openai_chat(self, system: str, messages: List[Dict[str, str]], key: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        formatted_msgs = [{"role": "system", "content": system}] + messages
        payload = {
            "model": "gpt-4o-mini",
            "messages": formatted_msgs,
            "temperature": 0.3,
            "max_tokens": 2048
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"OpenAI error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_groq(self, system: str, context: str, user_prompt: str, key: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": f"{system}\n\n{context}"},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.25,
            "max_tokens": 2048
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"Groq error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_groq_chat(self, system: str, messages: List[Dict[str, str]], key: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        formatted_msgs = [{"role": "system", "content": system}] + messages
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": formatted_msgs,
            "temperature": 0.3,
            "max_tokens": 2048
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise Exception(f"Groq error {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # --- Built-In High Conviction Quantitative Synthesis Engine ---
    def _generate_builtin_quant_analysis(self, forecast: Dict[str, Any]) -> str:
        sym = forecast.get("symbol", "")
        ltp = forecast.get("current_price", 0.0)
        direction = forecast.get("direction", "")
        bias = forecast.get("primary_bias", "")
        conf = forecast.get("confidence_percent", 50.0)
        levels = forecast.get("trade_levels", {})
        tech = forecast.get("technicals", {})
        pivots = tech.get("pivot_points", {})
        st = tech.get("supertrend", {})
        deriv = forecast.get("derivatives_confluence", {})
        horizons = forecast.get("horizons", {})
        hist = forecast.get("historical_analysis", {})
        q3m = horizons.get("quarterly_3m", {})
        is_bullish = "BULLISH" in direction

        pcr_val = deriv.get('pcr_oi')
        pcr_formatted = f"{pcr_val:.2f}" if pcr_val is not None else "N/A"
        pcr_comment = ('Heavy Put writing; floor defended' if (pcr_val or 0) >= 1.15 else 'Call writing capping upside' if (pcr_val or 0) <= 0.8 else 'Balanced OI distribution') if pcr_val is not None else 'Data settling'

        return f"""### 📊 Quantitative Market Intelligence Report: **{sym}**

#### **1. Executive Bias & Confluence Rating**
- **Primary Directional Bias**: **{direction.replace('_', ' ')}** (`{bias}`)
- **Statistical Win Probability**: **{conf}%**
- **Current Live Market Price**: **₹{ltp:,.2f}** ({forecast.get('change_percent'):+.2f}%)
- **Supertrend (14, 3.0)**: **{st.get('direction')}** at ₹{st.get('value'):,.2f}
- **Session Institutional Footprint**: **{tech.get('institutional_activity')}** (Volume Spike: {tech.get('volume_spike_ratio')}x)

---

#### **2. Tactical Trade Setup & Execution Parameters**
| Level Category | Price (INR) | Strategic Objective |
| :--- | :--- | :--- |
| **Suggested Entry Zone** | **₹{levels.get('entry_zone')}** | Optimized liquidity pool entry |
| **Target 1 (Conservative)** | **₹{levels.get('target_1')}** | First profit take (1.0x ATR) |
| **Target 2 (Extended)** | **₹{levels.get('target_2')}** | Major structural swing target |
| **Target 3 (Runner)** | **₹{levels.get('target_3')}** | Breakout continuation target |
| **Stop Loss (Risk Gate)** | **₹{levels.get('stop_loss')}** | Invalidation level (Loss Cap) |
| **Trailing Risk Stop** | **₹{levels.get('trailing_stop')}** | Dynamic volatility protection |
| **Risk / Reward Ratio** | **{forecast.get('risk_reward_ratio')}** | Asymmetric institutional payoff |

---

#### **3. Classical & Fibonacci Pivot Grid**
- **Resistance 2 (R2)**: ₹{pivots.get('r2')} *(Major intraday supply zone)*
- **Resistance 1 (R1)**: ₹{pivots.get('r1')} *(Immediate breakout trigger)*
- **Central Pivot (P)**: ₹{pivots.get('pivot')} *(Session fulcrum; price above is net bullish)*
- **Support 1 (S1)**: ₹{pivots.get('s1')} *(High-demand absorption level)*
- **Support 2 (S2)**: ₹{pivots.get('s2')} *(Critical structural floor)*

---

#### **4. Derivatives & Open Interest Confluence**
{f'''- **Put-Call Ratio (PCR)**: **{pcr_formatted}** ({pcr_comment})
- **Resistance Wall (Max Call OI)**: Strike **₹{deriv.get('resistance_wall_call_oi') or 'N/A'}**
- **Support Floor (Max Put OI)**: Strike **₹{deriv.get('support_floor_put_oi') or 'N/A'}**
- **Max Pain Strike**: Strike **₹{deriv.get('max_pain_strike') or 'N/A'}**
- **Futures Buildup Sentiment**: **{deriv.get('futures_buildup') or 'Neutral'}**''' if deriv.get('available') else '- *Equity Only instrument (Cash segment); no derivative contracts listed.*'}

---

#### **5. 3-Month Future Horizon & Historical Price Trajectory**
- **3-Month Projected Target**: **₹{q3m.get('target') or hist.get('quarterly_ai_target')}** ({q3m.get('expected_return_pct')} from current LTP)
- **3-Month Macro Risk Stop**: **₹{q3m.get('stop_loss') or hist.get('quarterly_ai_stop')}** (Trailing institutional invalidation)
- **Historical Returns Performance**:
  - **1-Week**: `{hist.get('perf_1w')}%` | **1-Month**: `{hist.get('perf_1m')}%` | **3-Month**: `{hist.get('perf_3m')}%`
  - **6-Month**: `{hist.get('perf_6m')}%` | **1-Year**: `{hist.get('perf_1y')}%`
- **52-Week Range**: Low ₹{hist.get('low_52w')} to High ₹{hist.get('high_52w')} ({hist.get('distance_from_52w_high_pct')}% from 52W High)
- **Quarterly Trend & Catalysts**: {hist.get('historical_trend_summary')} Next key drivers include {q3m.get('quarterly_catalyst')}.

---

#### **6. Strategic Recommendation**
{'Maintain a **BUY / LONG** stance on dips toward VWAP (₹' + str(tech.get('vwap')) + '). Trail stop losses closely using Supertrend. Look for call option buying or Bull Call Spreads.' if is_bullish else 'Maintain a **SELL / SHORT** stance on rallies toward R1 resistance (₹' + str(pivots.get('r1')) + '). Protect profits using the upper ATR stop loss.'}
"""

    def _generate_builtin_chat_reply(self, query: str, forecast: Optional[Dict[str, Any]], symbol: str) -> str:
        q_lower = query.lower()
        if not forecast:
            return f"Currently gathering market feeds for {symbol}. Please verify the symbol is active in the NSE/BSE universe."

        ltp = forecast.get("current_price", 0.0)
        direction = forecast.get("direction", "")
        levels = forecast.get("trade_levels", {})
        tech = forecast.get("technicals", {})
        pivots = tech.get("pivot_points", {})
        deriv = forecast.get("derivatives_confluence", {})
        horizons = forecast.get("horizons", {})
        hist = forecast.get("historical_analysis", {})
        q3m = horizons.get("quarterly_3m", {})

        if any(w in q_lower for w in ["3 month", "quarter", "history", "trend", "future", "long term", "horizon"]):
            return (
                f"**3-Month Future Forecast & Historical Analysis for {symbol} (LTP: ₹{ltp:,.2f})**:\n\n"
                f"- **3-Month AI Target**: ₹{q3m.get('target') or hist.get('quarterly_ai_target')} ({q3m.get('expected_return_pct')})\n"
                f"- **Macro Risk Stop**: ₹{q3m.get('stop_loss') or hist.get('quarterly_ai_stop')}\n"
                f"- **Historical Returns**: 1M: {hist.get('perf_1m')}% | 3M: {hist.get('perf_3m')}% | 6M: {hist.get('perf_6m')}%\n"
                f"- **52-Week Bounds**: High ₹{hist.get('high_52w')} | Low ₹{hist.get('low_52w')}\n"
                f"- **Quarterly Catalyst**: {q3m.get('quarterly_catalyst')}\n"
                f"- **Strategic Trend**: {hist.get('historical_trend_summary')}"
            )
        elif any(w in q_lower for w in ["target", "stop", "entry", "level", "buy", "sell", "price"]):
            return (
                f"**Trade Setup for {symbol} (LTP: ₹{ltp:,.2f})**:\n\n"
                f"- **Primary Bias**: {direction.replace('_', ' ')}\n"
                f"- **Entry Range**: ₹{levels.get('entry_zone')}\n"
                f"- **Target 1**: ₹{levels.get('target_1')} ({levels.get('expected_move_pct')})\n"
                f"- **Target 2**: ₹{levels.get('target_2')}\n"
                f"- **Stop Loss**: ₹{levels.get('stop_loss')}\n"
                f"- **Risk-to-Reward**: {forecast.get('risk_reward_ratio')}\n"
                f"- **Central Pivot**: ₹{pivots.get('pivot')} | Support S1: ₹{pivots.get('s1')} | Resistance R1: ₹{pivots.get('r1')}"
            )
        elif any(w in q_lower for w in ["option", "strategy", "call", "put", "f&o"]):
            if deriv.get("available"):
                pcr = deriv.get("pcr_oi", 1.0)
                is_bull = "BULLISH" in direction
                strat = "Bull Call Spread (Buy ATM Call, Sell OTM Call)" if is_bull else "Bear Put Spread (Buy ATM Put, Sell OTM Put)"
                return (
                    f"**Options Intelligence for {symbol}**:\n\n"
                    f"- **PCR OI**: {pcr:.2f}\n"
                    f"- **Max Pain Strike**: ₹{deriv.get('max_pain_strike')}\n"
                    f"- **Institutional Resistance Wall**: ₹{deriv.get('resistance_wall_call_oi')} (Max Call OI)\n"
                    f"- **Institutional Support Floor**: ₹{deriv.get('support_floor_put_oi')} (Max Put OI)\n"
                    f"- **Recommended Strategy**: **{strat}** to cap volatility risk and optimize Greeks."
                )
            else:
                return f"{symbol} is in the Cash Equity segment without active exchange-listed derivatives. Trade pure cash equity with strict stop loss at ₹{levels.get('stop_loss')}."
        elif any(w in q_lower for w in ["support", "resistance", "pivot"]):
            return (
                f"**Key Support & Resistance Levels for {symbol}**:\n\n"
                f"- **Resistance 2 (R2)**: ₹{pivots.get('r2')}\n"
                f"- **Resistance 1 (R1)**: ₹{pivots.get('r1')}\n"
                f"- **Central Pivot (P)**: ₹{pivots.get('pivot')}\n"
                f"- **Support 1 (S1)**: ₹{pivots.get('s1')}\n"
                f"- **Support 2 (S2)**: ₹{pivots.get('s2')}\n"
                f"- **Supertrend Dynamic Stop**: ₹{tech.get('supertrend', {}).get('value')}"
            )
        else:
            return (
                f"**Market Outlook on {symbol} (₹{ltp:,.2f})**:\n\n"
                f"{symbol} is currently displaying **{direction.replace('_', ' ')}** behavior with a confidence score of **{forecast.get('confidence_percent')}%**.\n\n"
                f"- RSI (14) stands at **{tech.get('rsi_14')}** ({tech.get('rsi_condition')}).\n"
                f"- Intraday VWAP is at **₹{tech.get('vwap')}**.\n"
                f"- Suggested tactical play: **{levels.get('strategy_name')}** with Target at **₹{levels.get('target_1')}** and Stop Loss at **₹{levels.get('stop_loss')}**."
            )

ai_analyst_service = AiAnalystService()

# Stratosphere
### AI-Based Strategy Builder & Multi-Factor Confidence Scoring System for Equity and Index-Options Trading

Final Year Project | B.Tech CSE (AI & ML) | VISTAS, Chennai

**Team:** Jeyrenth Siva B, Rokith K, Yeshwandh D
**Guide:** Dr. A. Manikandan M.E., Ph.D.

> **About this repository:** this is a **UI showcase**. It contains the complete web interface running on **sample data**.
> The private core (AI models, backtesting engine, indicator and signal logic, market data, broker integration) is
> intentionally **not included**. Anything that needs the core shows a "Demo mode" message.

---

## 1. Overview
Retail traders work in volatile markets, and fixed indicator rules cannot adapt to changing conditions. Stratosphere is a
platform where a user can **design a strategy visually, measure how reliable its signals really are, let a two-model AI
filter the trades, validate the result honestly on unseen data, and forward-test it with live prices without risking money.**

## 2. Main components (high-level)
| Component | Purpose |
|---|---|
| Strategy Builder and Schema | Visual builder for entry and exit conditions, stored in a structured, versioned strategy format |
| Strategy Validator | Checks a strategy for structural and logical errors before it is used |
| Indicator Library | Catalog of technical indicators grouped into trend, momentum, volatility, volume, price action and fundamental categories |
| Signal Reliability Analyzer | Measures how well each signal has worked on a stock, tests combinations (confluence) and parameter sensitivity |
| Convergence Engine | Combines signals from several sources into one agreement view across a stock universe |
| AI Scorer | Machine-learning confidence score for a stock setup |
| Twin-Tower AI | Two cooperating models: an **Entry Gate** (selects high-probability setups) and an **Exit Manager** (decides when to leave a trade) |
| Walk-Forward Validation | Cross-expiry testing on unseen periods so results are not inflated by overfitting |
| Backtesting Engine | Historical testing of strategies, including options-based and intraday modes, with NSE trading costs applied |
| Data Layer | Historical NSE data and broker historical data, cached locally for repeatable experiments |
| Paper Trading Engine | Forward-tests strategies on live prices with simulated orders and one-trade-at-a-time risk control |
| Broker Integration | Live market data and login handling for Angel One SmartAPI and Zerodha Kite Connect (live order placement is off by default) |
| Risk Controls | Capital limits, daily loss limit and an emergency stop for trading |
| Web Interface | The dashboards and tools listed in section 4 |

## 3. How the AI part works (overview)
1. A strategy produces **raw signals** on historical data.
2. The **Entry Gate** model scores each raw signal and keeps only the high-confidence ones.
3. For the trades that are taken, the **Exit Manager** model decides when to close them.
4. The whole pipeline is evaluated with **5-fold Walk-Forward Validation**: every fold is tested on a different, unseen
   expiry, and nothing from the test period is used for training.
5. Results are reported as win rate, average profit and loss per trade, trade counts and filtering rate.

Design goals: honesty (no data leakage), transparency (every trade can be traced to raw price data), and realism
(trading costs included).

## 4. Pages in the web interface
Dashboard, Schema Browser, Indicator Catalog, Strategy Builder, Validator, Signal Analyzer, Convergence, AI Scorer,
AI Tower (Twin-Tower training, backtest and Walk-Forward views), Backtest Results, Intraday Backtest, Paper Trade,
Trading Dashboard and Broker Login.

Screenshots are in `docs/screenshots/`.

![Analyzer](docs/screenshots/02-analyzer.jpg)
![AI Tower](docs/screenshots/05-ai-tower.jpg)

## 5. Headline results (Twin-Tower AI, 5-fold Walk-Forward Validation)
| Metric | Value |
|---|---|
| Average win rate | 61.1% |
| Average P&L per trade | +7.8% |
| Total trades | 681 |
| Raw signals filtered out | about 85% |

Each fold is tested on a different unseen expiry; one of the five folds was weaker than the rest, which is reported openly.
These are research results on historical data and are **not a promise of future returns**.

## 6. Technology
- **Languages and web:** Python, FastAPI, Jinja2, HTML5, CSS3, JavaScript
- **Data and ML:** NumPy, Pandas, scikit-learn, XGBoost
- **Market connectivity:** Angel One SmartAPI (WebSocket streaming), Zerodha Kite Connect
- **Standards followed:** IEEE 29148, IEEE 1016, ISO/IEC 25010, ISO/IEC 29119, ISO/IEC 23894, ISO/IEC 27001, RFC 6455 and 8446, PEP 8

## 7. Run the UI locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn demo_server:app --reload
```
Open http://127.0.0.1:8000

## 8. What is in this repository
```
demo_server.py     demo backend (serves the pages with sample data)
web/templates/     all HTML pages
web/static/        CSS and JavaScript
mock_data/         sample JSON used by the demo
docs/              screenshots and the GitHub push guide
```

## 9. What is not included
AI models and training code, the backtesting engine, indicator and signal logic, strategy schema and validation code,
market data and caches, and all broker and API integration code. Numbers shown by the demo (for example in the Analyzer)
are **sample data**, not real market results.

## 10. Disclaimer and license
This project is for academic purposes only and is **not financial advice**. Paper trading uses simulated orders.
Copyright (c) 2026 the authors. All rights reserved (see `LICENSE`).

# 📈 Team 6: QuantPulse AI
### **NSE & BSE Full Market Coverage Terminal with Multi-Horizon Quantitative Predictions & Stock AI Copilot**
*Department of Artificial Intelligence & Machine Learning | Academic Year 2026–2027 (Section B)*

---

## 🌟 Executive Summary

**QuantPulse AI (Team 6)** is an institutional-grade algorithmic market intelligence and real-time trading analytics terminal engineered for the Indian Financial Markets (NSE & BSE). The platform integrates deep quantitative models, multi-horizon price forecasting, Black-Scholes derivative analytics, and an interactive **Stock AI Copilot** across **62,798 active equity and derivative instruments**.

---

## 📂 Phase 1 Submission Structure

```
PROJECTS-2026-2027----SEC-B (Branch: TEAM-6)
│
├── README.md                                  # Repository Root Overview (Team 6)
│
└── PHASE 1/
    ├── README.md                              # Phase 1 Documentation
    │
    ├── CODE/                                  # Full Platform Implementation
    │   ├── README.md                          # Code Architecture Guide
    │   └── nse-bse-platform/
    │       ├── backend/                       # FastAPI High-Concurrency Async API Server
    │       │   ├── app/
    │       │   │   ├── main.py                # Server Entrypoint & Lifespan Hooks
    │       │   │   ├── config.py              # Environment & Provider Settings
    │       │   │   ├── database.py            # SQLite FTS5 Full-Text Engine
    │       │   │   ├── routers/               # REST & WebSocket Endpoints (8 Modules)
    │       │   │   ├── services/              # Predictive & Analytical Engines (9 Modules)
    │       │   │   └── sync/                  # High-Speed Exchange Instrument Ingestion
    │       │   ├── requirements.txt           # Python Dependencies
    │       │   └── run.py                     # Development Server Runner
    │       ├── frontend/                      # React 18 + Vite + TypeScript Dashboard
    │       │   ├── src/
    │       │   │   ├── App.tsx                # Master Trading View Router
    │       │   │   ├── components/            # 13 Glassmorphic Financial UI Components
    │       │   │   ├── api/client.ts          # Typed REST API Client
    │       │   │   └── types/index.ts         # TypeScript Domain Types & Interfaces
    │       │   ├── package.json               # Node.js Dependencies
    │       │   └── vite.config.ts             # Reverse Proxy & Dev Server Config
    │       ├── data/
    │       │   └── market_master.db           # SQLite Master Database (62,798 Instruments)
    │       ├── start.bat                      # 1-Click Dual Server Launcher (Windows)
    │       ├── setup_new_pc.bat               # 1-Click Automated Dependency Installer
    │       ├── start.sh                       # Dual Server Launcher (Linux / macOS)
    │       └── setup_new_pc.sh                # Dependency Installer (Linux / macOS)
    │
    ├── IEEE/                                  # Research Paper Submission
    │   ├── README.md                          # Research Summary
    │   └── QuantPulse_AI_IEEE_Paper.pdf       # Full IEEE Two-Column Format Research Paper (635 KB)
    │
    └── REPORT/                                # Comprehensive Technical Reports
        ├── README.MD                          # Report Summary
        ├── TEAM_6_SOURCE_CODE_REPORT.md       # Complete 9,874-Line Source Code Report
        └── PROJECT_FULL_SOURCE_CODE_REPORT.md # Full System Code Appendix with Indexing
```

---

## 🚀 Key Architectural Innovations

### 1. Full Market Coverage (62,798 Instruments)
- Sub-millisecond FTS5 search across all listed equities, indices, index options, stock options, and currency derivatives.
- Authentic real-time quote synchronization matching NSE / Google Finance feeds.

### 2. Multi-Horizon Quantitative Prediction Matrix
- **15-Minute Scalp:** Real-time order flow momentum, VWAP slope, and micro-tick delta.
- **Intraday (Session EOD):** Classical Floor Pivots ($P, R_1-R_3, S_1-S_3$), Fibonacci extensions, and ATR bands.
- **Swing (1–5 Days):** 20/50 EMA dynamic trend continuation and volume spread analysis.
- **Positional (1 Month):** Macro 200-EMA structural channels and corporate earnings momentum.
- **Quarterly Outlook (3 Months / 90 Days):** Long-term institutional accumulation corridors, 52-week historical trend synthesis, and macro catalyst projection.

### 3. Integrated Stock AI Copilot
- Supports **Google Gemini**, **OpenAI GPT-4o**, **Groq LLaMA 3.3**, and an offline **Built-in Quantitative AI Engine** requiring zero API keys.
- Instant 1-click prompts for full trade setups, options structures, support/resistance pivots, and 3-month forecast syntheses.

### 4. Derivatives & Options Intelligence
- Real-time **Black-Scholes Greek Engine** (Delta $\Delta$, Gamma $\Gamma$, Theta $\Theta$, Vega $\nu$, Rho $\rho$).
- Put-Call Ratio (PCR) analysis, Max Pain calculation, and Call/Put Open Interest Wall detection.

---

## 🛠️ Quick Start & Running Locally

### Option A: Windows (1-Click Launcher)
1. Navigate to `PHASE 1/CODE/nse-bse-platform/`
2. Run **`setup_new_pc.bat`** *(Installs Python virtualenv & Node packages automatically)*
3. Double-click **`start.bat`** *(Starts Backend on port 8000 and Frontend on port 5173)*

### Option B: Manual Command Line
```bash
# Terminal 1: Backend
cd "PHASE 1/CODE/nse-bse-platform/backend"
python -m venv venv
.\venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend
cd "PHASE 1/CODE/nse-bse-platform/frontend"
npm install
npm run dev
```

- **Frontend Trading Terminal:** `http://localhost:5173`
- **Interactive Swagger API Docs:** `http://localhost:8000/docs`

---

## 👥 Team Information
- **Team:** Team 6
- **Class / Section:** AIML 2026–2027 (Section B)
- **Course:** Project Phase 1 Evaluation

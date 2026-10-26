# Team 6: NSE & BSE Full Market Coverage Terminal with Stock AI Copilot

### Project Overview
An institutional-grade Indian stock market terminal covering 62,000+ NSE and BSE equity and derivative instruments. Features authentic real-time price feeds, Black-Scholes Greeks, dynamic pivot matrices (Classical & Fibonacci), multi-horizon algorithmic future price targets (15M, 1D, 5D, 1M, 3M), and an integrated Stock AI Copilot.

### Directory Structure
- `nse-bse-platform/backend`: FastAPI high-concurrency API server with quantitative and machine learning models.
- `nse-bse-platform/frontend`: Vite + React + TypeScript responsive trading dashboard with WebSockets.
- `nse-bse-platform/data`: SQLite master database containing 62,798 instruments and search indexes.
- `nse-bse-platform/start.bat`: 1-click startup script for Windows.
- `nse-bse-platform/setup_new_pc.bat`: Automated dependency setup script.

### Quick Start
1. Double-click `setup_new_pc.bat` inside `nse-bse-platform/` to install dependencies.
2. Double-click `start.bat` to launch both backend (`http://localhost:8000`) and frontend (`http://localhost:5173`).

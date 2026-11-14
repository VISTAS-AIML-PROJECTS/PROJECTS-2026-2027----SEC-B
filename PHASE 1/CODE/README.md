# QuantPulse AI — Source Code Distribution

### Team 6 • SEC-B • AIML 2026-27
**Vels Institute of Science, Technology and Advanced Studies (VISTAS)**

---

### Directory Structure:
* **`nse-bse-platform/`**: Complete full-stack application
  * **`backend/`**: FastAPI REST API server, quantitative engines, ML forecasting service, options Greeks, and SQLite ORM models
  * **`frontend/`**: React 18 + Vite + Tailwind CSS terminal dashboard with interactive charts, modal dialogs, and AI copilot
  * **`data/`**: `market_master.db` containing 62,798 indexed instruments across NSE and BSE
  * **`setup_new_pc.bat` / `setup_new_pc.sh`**: One-click environment configuration
  * **`start.bat` / `start.sh`**: One-click multi-process launcher

### Quick Start:
```bash
cd "PHASE 1/CODE/nse-bse-platform"

# Run automatic setup
setup_new_pc.bat

# Start platform
start.bat
```
Access the application at `http://localhost:5173`.

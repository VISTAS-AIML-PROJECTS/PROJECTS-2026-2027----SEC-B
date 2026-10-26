#!/usr/bin/env bash
echo "============================================================"
echo "  NSE & BSE Platform - Setup Script (Linux / macOS)"
echo "============================================================"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/3] Setting up Python virtual environment in backend..."
cd "$SCRIPT_DIR/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Python backend setup complete!"
echo ""

echo "[2/3] Installing Frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
npm install
echo "Frontend dependencies installed!"
echo ""

echo "[3/3] Checking Database..."
if [ -f "$SCRIPT_DIR/data/market_master.db" ]; then
    echo "[OK] Database market_master.db found!"
else
    echo "[INFO] data/market_master.db will auto-download on first start."
fi

echo ""
echo "============================================================"
echo "  Setup Complete! Launch with: ./start.sh"
echo "============================================================"

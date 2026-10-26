#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Backend on http://127.0.0.1:8000 ..."
(cd "$SCRIPT_DIR/backend" && source venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
BACKEND_PID=$!

echo "Starting Frontend on http://127.0.0.1:5173 ..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "============================================================"
echo "  Servers are running!"
echo "  Frontend UI : http://localhost:5173"
echo "  Backend API : http://127.0.0.1:8000/docs"
echo "  Press CTRL+C to stop both servers."
echo "============================================================"

trap "kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT SIGTERM
wait

@echo off
echo ============================================================
echo   NSE ^& BSE Full Market Coverage Terminal - Quick Launch
echo ============================================================

REM Check if Python venv exists
if not exist "%~dp0backend\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in backend\venv!
    echo Please run 'setup_new_pc.bat' first to install dependencies.
    pause
    exit /b 1
)

echo Starting Backend Server on http://127.0.0.1:8000 ...
start "NSE-BSE Backend (Port 8000)" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Frontend Dev Server on http://127.0.0.1:5173 ...
start "NSE-BSE Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================================
echo   Application is now running!
echo   Frontend UI : http://localhost:5173
echo   Backend API : http://127.0.0.1:8000/docs
echo ============================================================
echo You can keep this window open or close it (servers run in their own windows).

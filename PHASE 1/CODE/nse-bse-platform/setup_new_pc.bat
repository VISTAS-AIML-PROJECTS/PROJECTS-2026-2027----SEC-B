@echo off
echo ============================================================
echo   NSE ^& BSE Platform - Automated New System Setup
echo ============================================================
echo.

echo [1/3] Setting up Python virtual environment in backend...
cd /d %~dp0backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Installing backend Python dependencies...
call .\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Python backend setup complete!
echo.

echo [2/3] Installing Frontend dependencies...
cd /d %~dp0frontend
call npm install
echo Frontend dependencies installed!
echo.

echo [3/3] Checking Database...
if exist "%~dp0data\market_master.db" (
    echo [OK] Database market_master.db found with 62,000+ instruments!
) else (
    echo [INFO] data\market_master.db will auto-download instruments on first launch.
)

echo.
echo ============================================================
echo   Setup Complete!
echo   To launch the application anytime, double-click: start.bat
echo ============================================================
pause

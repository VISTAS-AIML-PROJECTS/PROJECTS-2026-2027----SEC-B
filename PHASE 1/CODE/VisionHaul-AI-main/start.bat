@echo off
echo ======================================================================
echo   VISIONHAUL AI - HEAVY VEHICLE SURVEILLANCE & LOGISTICS SYSTEM
echo ======================================================================
echo.

echo [1/2] Starting Flask Backend Server (Port 5000)...
start "VisionHaul Backend (Flask + YOLOv26)" cmd /k "cd /d %~dp0 && python backend/app.py"

echo [2/2] Starting React Frontend Dev Server (Port 5173)...
start "VisionHaul Frontend (React + Vite)" cmd /k "cd /d %~dp0frontend && npm.cmd run dev"

echo.
echo ======================================================================
echo   Both servers are starting!
echo   Surveillance Dashboard will be live at: http://localhost:5173
echo ======================================================================
timeout /t 3 >nul
start http://localhost:5173

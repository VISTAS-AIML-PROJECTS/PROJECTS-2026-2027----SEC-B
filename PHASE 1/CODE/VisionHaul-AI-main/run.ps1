Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  VISIONHAUL AI - HEAVY VEHICLE SURVEILLANCE & LOGISTICS SYSTEM" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Starting Flask Backend Server (Port 5000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; python backend/app.py"

Write-Host "[2/2] Starting React Frontend Dev Server (Port 5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot/frontend'; npm.cmd run dev"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Both servers launched!" -ForegroundColor Green
Write-Host "  Surveillance Dashboard: http://localhost:5173" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

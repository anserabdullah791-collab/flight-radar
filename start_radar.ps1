# Flight Radar - One Click Start (Windows PowerShell)
# Double-click this file or right-click -> Run with PowerShell

Write-Host "============================================" -ForegroundColor Green
Write-Host "       FLIGHT RADAR - Starting..." -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor DarkGreen
} catch {
    Write-Host "[ERROR] Python is not installed!" -ForegroundColor Red
    Write-Host "Install from: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Check 'Add Python to PATH' during install" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install flask requests -q 2>$null

# Check file exists
if (-Not (Test-Path "flight_radar.py")) {
    Write-Host "[ERROR] flight_radar.py not found!" -ForegroundColor Red
    Write-Host "Download from: https://github.com/anserabdullah791-collab/flight-radar" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Radar is LIVE! Browser opening..." -ForegroundColor Green
Write-Host "  http://localhost:5656" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Open browser
Start-Process "http://localhost:5656"

# Run radar
python flight_radar.py

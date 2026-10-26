# PowerShell launcher for WiFi Time Roulette
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "       WIFI TIME ROULETTE - HIGH STAKES SCREEN TIME         " -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "[*] Launching browser to http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process "http://localhost:8000"

Write-Host "[*] Starting Uvicorn API server on port 8000 ..." -ForegroundColor Green
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

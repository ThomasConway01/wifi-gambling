@echo off
title WiFi Time Roulette - Bandwidth Casino
cd /d "%~dp0"

echo ============================================================
echo         WIFI TIME ROULETTE - HIGH STAKES SCREEN TIME
echo ============================================================
echo.
echo Starting Web Server and Network Radar on http://localhost:8000 ...
echo.

start "" "http://localhost:8000"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause

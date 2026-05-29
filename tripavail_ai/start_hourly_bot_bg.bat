@echo off
REM Start TripAvail AI Hourly Bot in background (minimized) with logging
setlocal

cd /d D:\posty\tripavail_ai
if not exist "logs" mkdir logs

start "TripAvail Hourly Bot" /min cmd /c "call venv\Scripts\activate.bat && python run_hourly_bot.py >> logs\tripavail_ai.log 2>&1"
echo Started Hourly Bot in background. Logs: tripavail_ai\logs\tripavail_ai.log

endlocal


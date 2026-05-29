@echo off
REM Start TripAvail AI Smart Scheduler in background (minimized) with logging
setlocal

cd /d D:\posty\tripavail_ai
if not exist "logs" mkdir logs

start "TripAvail Smart Scheduler" /min cmd /c "call venv\Scripts\activate.bat && python smart_scheduler.py --run >> logs\scheduler.log 2>&1"
echo Started Smart Scheduler in background. Logs: tripavail_ai\logs\scheduler.log

endlocal


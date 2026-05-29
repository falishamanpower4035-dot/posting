@echo off
echo Starting TripAvail AI Hourly Bot...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python run_hourly_bot.py
pause

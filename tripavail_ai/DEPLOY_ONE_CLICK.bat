@echo off
echo =====================================
echo   TripAvail AI - One-Click Deploy
echo   Target: 138.68.141.3
echo =====================================
echo.

echo [1/3] Uploading files...
scp -r smart_scheduler.py bot.py main.py requirements.txt .env config core scripts social_media assets data droplet_setup.sh system_check.py root@138.68.141.3:/opt/tripavail_ai/

if %errorlevel% neq 0 (
    echo [ERROR] Upload failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Files uploaded!
echo.

echo [2/3] Running setup on droplet...
echo This will take about 5 minutes...
echo.

ssh root@138.68.141.3 "cd /opt/tripavail_ai && bash droplet_setup.sh"

if %errorlevel% neq 0 (
    echo [ERROR] Setup failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Setup complete!
echo.

echo [3/3] Starting the bot...
ssh root@138.68.141.3 "systemctl start tripavail-scheduler && systemctl status tripavail-scheduler"

echo.
echo =====================================
echo   DEPLOYMENT COMPLETE!
echo =====================================
echo.
echo Your bot is now running 24/7!
echo.
echo View logs:
echo   ssh root@138.68.141.3
echo   tail -f /opt/tripavail_ai/logs/scheduler.log
echo.
pause


@echo off
REM TripAvail AI - Quick Launch
REM Production deployment launcher

echo ============================================================
echo TRIPAVAIL AI - PRODUCTION LAUNCHER
echo ============================================================
echo.

cd /d D:\posty\tripavail_ai

REM Activate virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

call venv\Scripts\activate

echo.
echo ============================================================
echo DEPLOYMENT OPTIONS
echo ============================================================
echo.
echo 1. Run System Check (Verify deployment readiness)
echo 2. Start Scheduler (Production mode - runs 24/7)
echo 3. View Today's Statistics
echo 4. View Performance Insights
echo 5. Generate Daily Summary
echo 6. Test Posting (Post immediately for testing)
echo 7. View Schedule
echo 8. View Top 10 Posts
echo 9. Exit
echo.
set /p choice="Select option (1-9): "

if "%choice%"=="1" goto system_check
if "%choice%"=="2" goto start_scheduler
if "%choice%"=="3" goto stats
if "%choice%"=="4" goto insights
if "%choice%"=="5" goto summary
if "%choice%"=="6" goto test_post
if "%choice%"=="7" goto schedule
if "%choice%"=="8" goto top_posts
if "%choice%"=="9" goto end

:system_check
echo.
echo ============================================================
echo RUNNING SYSTEM CHECK
echo ============================================================
python system_check.py
pause
goto end

:start_scheduler
echo.
echo ============================================================
echo STARTING PRODUCTION SCHEDULER
echo ============================================================
echo.
echo The scheduler will now run continuously and post at:
echo - 06:00 UTC (Asia morning)
echo - 09:00 UTC (Asia evening)
echo - 14:00 UTC (USA morning + Europe afternoon)
echo - 18:00 UTC (USA afternoon + Europe evening)
echo - 21:00 UTC (USA peak + Europe night)
echo - 23:00 UTC (USA evening)
echo.
echo Daily summary will be generated at 23:59 UTC
echo.
echo Press Ctrl+C to stop
echo.
pause
python smart_scheduler.py --run
goto end

:stats
echo.
python smart_scheduler.py --stats
pause
goto end

:insights
echo.
python smart_scheduler.py --insights
pause
goto end

:summary
echo.
python smart_scheduler.py --summary
pause
goto end

:test_post
echo.
echo ============================================================
echo TEST POSTING
echo ============================================================
echo This will post immediately to all platforms (for testing)
echo.
set /p confirm="Are you sure? (Y/N): "
if /i "%confirm%"=="Y" (
    python smart_scheduler.py --post-now
) else (
    echo Cancelled.
)
pause
goto end

:schedule
echo.
python smart_scheduler.py --schedule
pause
goto end

:top_posts
echo.
python smart_scheduler.py --show-top
pause
goto end

:end
echo.
echo Goodbye!


@echo off
REM Smart Scheduler Launcher for TripAvail AI
REM Posts top 10 ranked videos at global peak times

echo ============================================================
echo TRIPAVAIL AI - SMART SCHEDULER
echo ============================================================
echo.
echo Posts top 10 best videos to Instagram, Facebook, YouTube
echo at global peak times for maximum engagement
echo.
echo ============================================================
echo.

cd /d D:\posty\tripavail_ai

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate

echo Virtual environment activated
echo.

REM Show menu
:menu
echo ============================================================
echo SMART SCHEDULER - Main Menu
echo ============================================================
echo.
echo 1. Show Top 10 Ranked Posts
echo 2. View Posting Schedule
echo 3. Post Now (Test Mode)
echo 4. Run Scheduler Loop
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto show_top
if "%choice%"=="2" goto show_schedule
if "%choice%"=="3" goto post_now
if "%choice%"=="4" goto run_scheduler
if "%choice%"=="5" goto end
echo Invalid choice! Please try again.
goto menu

:show_top
echo.
echo ============================================================
echo TOP 10 RANKED POSTS
echo ============================================================
python smart_scheduler.py --show-top
echo.
pause
goto menu

:show_schedule
echo.
echo ============================================================
echo POSTING SCHEDULE
echo ============================================================
python smart_scheduler.py --schedule
echo.
pause
goto menu

:post_now
echo.
echo ============================================================
echo POST NOW (TEST MODE)
echo ============================================================
echo This will post immediately to all platforms (for testing)
echo.
set /p confirm="Are you sure? (Y/N): "
if /i "%confirm%"=="Y" (
    python smart_scheduler.py --post-now
) else (
    echo Cancelled.
)
echo.
pause
goto menu

:run_scheduler
echo.
echo ============================================================
echo STARTING SCHEDULER LOOP
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
echo Press Ctrl+C to stop the scheduler
echo.
pause
python smart_scheduler.py --run
goto menu

:end
echo.
echo Goodbye!
pause


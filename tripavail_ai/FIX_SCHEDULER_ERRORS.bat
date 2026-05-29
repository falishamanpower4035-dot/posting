@echo off
REM Fix Scheduler Errors - Marks stuck posts as done
REM Run this file to fix posts 288, 289, 301, 303

echo ============================================================
echo  FIX SCHEDULER ERRORS - Automated Fix Script
echo ============================================================
echo.

set SSH_KEY=C:\Users\hp\.ssh\id_ed25519_do
set HOST=root@138.68.141.3

echo Step 1: Stopping scheduler...
ssh -i %SSH_KEY% %HOST% "pkill -f scheduler_daemon.py"
timeout /t 2 /nobreak >nul

echo.
echo Step 2: Downloading scheduled_posts.json...
scp -i %SSH_KEY% %HOST%:/opt/tripavail_ai/data/scheduled_posts.json scheduled_posts_backup.json
if errorlevel 1 (
    echo ERROR: Failed to download file
    pause
    exit /b 1
)

echo.
echo Step 3: Fixing stuck posts locally...
python -c "import json; items = json.load(open('scheduled_posts_backup.json')); [print(f'Marking {item[\"post_id\"]} as done') or item.update({'status': 'done'}) for item in items if item.get('post_id') in ['288', '289', '301', '303'] and item.get('status') == 'pending']; json.dump(items, open('scheduled_posts_fixed.json', 'w'), indent=2); print('Fixed!')"

echo.
echo Step 4: Uploading fixed file...
scp -i %SSH_KEY% scheduled_posts_fixed.json %HOST%:/opt/tripavail_ai/data/scheduled_posts.json
if errorlevel 1 (
    echo ERROR: Failed to upload file
    pause
    exit /b 1
)

echo.
echo Step 5: Restarting scheduler...
ssh -i %SSH_KEY% %HOST% "cd /opt/tripavail_ai && rm -f .scheduler_daemon.lock && PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 &"
timeout /t 3 /nobreak >nul

echo.
echo Step 6: Verifying scheduler is running...
ssh -i %SSH_KEY% %HOST% "ps aux | grep scheduler_daemon | grep -v grep"

echo.
echo Step 7: Checking recent logs...
ssh -i %SSH_KEY% %HOST% "tail -20 /opt/tripavail_ai/logs/scheduler.log"

echo.
echo ============================================================
echo  FIX COMPLETE!
echo ============================================================
echo.
echo Posts 288, 289, 301, 303 have been marked as done.
echo The scheduler has been restarted with the fixed code.
echo.
pause


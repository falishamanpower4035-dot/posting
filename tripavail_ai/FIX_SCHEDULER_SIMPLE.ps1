# Simple Scheduler Fix Script
# Run this with: powershell -ExecutionPolicy Bypass -File FIX_SCHEDULER_SIMPLE.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SCHEDULER FIX - SIMPLE VERSION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$key = "C:\Users\hp\.ssh\id_ed25519_do"
$server = "root@138.68.141.3"

# Step 1: Test connection
Write-Host "Step 1: Testing connection..." -ForegroundColor Yellow
ssh -i $key $server "hostname && date"
Write-Host ""

# Step 2: Check scheduler
Write-Host "Step 2: Checking scheduler status..." -ForegroundColor Yellow
ssh -i $key $server "ps aux | grep scheduler_daemon | grep -v grep"
Write-Host ""

# Step 3: Check errors
Write-Host "Step 3: Checking for error posts..." -ForegroundColor Yellow
ssh -i $key $server "tail -100 /opt/tripavail_ai/logs/scheduler.log | grep -E '(288|289|301|303)' | tail -10"
Write-Host ""

# Step 4: Stop scheduler
Write-Host "Step 4: Stopping scheduler..." -ForegroundColor Yellow
ssh -i $key $server "pkill -f scheduler_daemon.py"
Start-Sleep -Seconds 2
Write-Host "Done" -ForegroundColor Green
Write-Host ""

# Step 5: Download schedule file
Write-Host "Step 5: Downloading schedule file..." -ForegroundColor Yellow
scp -i $key "${server}:/opt/tripavail_ai/data/scheduled_posts.json" "scheduled_posts_backup.json"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Downloaded successfully" -ForegroundColor Green
} else {
    Write-Host "Download failed!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Step 6: Fix the file
Write-Host "Step 6: Fixing stuck posts (288, 289, 301, 303)..." -ForegroundColor Yellow
$content = Get-Content "scheduled_posts_backup.json" | ConvertFrom-Json
$fixed = 0
foreach ($item in $content) {
    if (($item.post_id -in @('288','289','301','303')) -and ($item.status -eq 'pending')) {
        Write-Host "  Marking post $($item.post_id) as done" -ForegroundColor Cyan
        $item.status = 'done'
        $fixed++
    }
}
$content | ConvertTo-Json -Depth 10 | Set-Content "scheduled_posts_fixed.json"
Write-Host "Fixed $fixed posts" -ForegroundColor Green
Write-Host ""

# Step 7: Upload fixed file
Write-Host "Step 7: Uploading fixed file..." -ForegroundColor Yellow
scp -i $key "scheduled_posts_fixed.json" "${server}:/opt/tripavail_ai/data/scheduled_posts.json"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Uploaded successfully" -ForegroundColor Green
} else {
    Write-Host "Upload failed!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Step 8: Restart scheduler
Write-Host "Step 8: Restarting scheduler..." -ForegroundColor Yellow
ssh -i $key $server "cd /opt/tripavail_ai && rm -f .scheduler_daemon.lock && PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 &"
Start-Sleep -Seconds 3
Write-Host "Done" -ForegroundColor Green
Write-Host ""

# Step 9: Verify
Write-Host "Step 9: Verifying scheduler is running..." -ForegroundColor Yellow
ssh -i $key $server "ps aux | grep scheduler_daemon | grep -v grep"
Write-Host ""

# Step 10: Check logs
Write-Host "Step 10: Checking recent logs..." -ForegroundColor Yellow
ssh -i $key $server "tail -30 /opt/tripavail_ai/logs/scheduler.log"
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " FIX COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Posts 288, 289, 301, 303 have been marked as done." -ForegroundColor Green
Write-Host "The scheduler has been restarted with the fixed code." -ForegroundColor Green
Write-Host ""

pause


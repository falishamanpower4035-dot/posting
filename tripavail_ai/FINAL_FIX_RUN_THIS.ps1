# PowerShell Script to Fix Scheduler Errors
# RIGHT-CLICK THIS FILE -> "Run with PowerShell"

$ErrorActionPreference = "Continue"
$SSH_KEY = "C:\Users\hp\.ssh\id_ed25519_do"
$DROPLET = "root@138.68.141.3"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SCHEDULER FIX SCRIPT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test connection
Write-Host "Step 1: Testing connection..." -ForegroundColor Yellow
$result = ssh -i $SSH_KEY $DROPLET "hostname && date"
Write-Host $result
Write-Host ""

# Step 2: Check scheduler status
Write-Host "Step 2: Checking scheduler status..." -ForegroundColor Yellow
$result = ssh -i $SSH_KEY $DROPLET "ps aux | grep scheduler_daemon | grep -v grep"
Write-Host $result
Write-Host ""

# Step 3: Check for error posts
Write-Host "Step 3: Checking for error posts (288, 289, 301, 303)..." -ForegroundColor Yellow
$result = ssh -i $SSH_KEY $DROPLET "tail -100 /opt/tripavail_ai/logs/scheduler.log | grep -E '(288|289|301|303)' | tail -10"
Write-Host $result
Write-Host ""

# Step 4: Stop scheduler
Write-Host "Step 4: Stopping scheduler..." -ForegroundColor Yellow
ssh -i $SSH_KEY $DROPLET "pkill -f scheduler_daemon.py"
Start-Sleep -Seconds 2
Write-Host "Scheduler stopped" -ForegroundColor Green
Write-Host ""

# Step 5: Download schedule file
Write-Host "Step 5: Downloading schedule file..." -ForegroundColor Yellow
scp -i $SSH_KEY "${DROPLET}:/opt/tripavail_ai/data/scheduled_posts.json" "scheduled_posts_backup.json"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ File downloaded" -ForegroundColor Green
} else {
    Write-Host "❌ Download failed" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Step 6: Fix the file
Write-Host "Step 6: Fixing stuck posts..." -ForegroundColor Yellow
python -c @"
import json
with open('scheduled_posts_backup.json', 'r') as f:
    items = json.load(f)

marked = 0
for item in items:
    if item.get('post_id') in ['288', '289', '301', '303'] and item.get('status') == 'pending':
        print(f\"Marking post {item['post_id']} as done\")
        item['status'] = 'done'
        marked += 1

with open('scheduled_posts_fixed.json', 'w') as f:
    json.dump(items, f, indent=2)

print(f\"\nFixed {marked} posts!\")
"@
Write-Host ""

# Step 7: Upload fixed file
Write-Host "Step 7: Uploading fixed file..." -ForegroundColor Yellow
scp -i $SSH_KEY "scheduled_posts_fixed.json" "${DROPLET}:/opt/tripavail_ai/data/scheduled_posts.json"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ File uploaded" -ForegroundColor Green
} else {
    Write-Host "❌ Upload failed" -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# Step 8: Restart scheduler
Write-Host "Step 8: Restarting scheduler..." -ForegroundColor Yellow
ssh -i $SSH_KEY $DROPLET "cd /opt/tripavail_ai && rm -f .scheduler_daemon.lock && PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 &"
Start-Sleep -Seconds 3
Write-Host "Scheduler restarted" -ForegroundColor Green
Write-Host ""

# Step 9: Verify scheduler is running
Write-Host "Step 9: Verifying scheduler..." -ForegroundColor Yellow
$result = ssh -i $SSH_KEY $DROPLET "ps aux | grep scheduler_daemon | grep -v grep"
Write-Host $result
Write-Host ""

# Step 10: Check recent logs
Write-Host "Step 10: Checking recent logs..." -ForegroundColor Yellow
$result = ssh -i $SSH_KEY $DROPLET "tail -30 /opt/tripavail_ai/logs/scheduler.log"
Write-Host $result
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " FIX COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Posts 288, 289, 301, 303 have been marked as done." -ForegroundColor Green
Write-Host "The scheduler has been restarted." -ForegroundColor Green
Write-Host ""

pause


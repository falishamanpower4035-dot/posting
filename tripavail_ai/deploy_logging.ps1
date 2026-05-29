# Quick Deploy: Centralized Logging to Production
# Uploads updated files and restarts services

Write-Host "=== Deploying Centralized Logging to Production ===" -ForegroundColor Cyan
Write-Host ""

$droplet = "root@138.68.141.3"
$remote_path = "/opt/tripavail_ai"

# Files to upload
$files = @(
    "core/utils/logging_setup.py",
    "scripts/run_two_hour_scheduler.py",
    "production_pipeline.py",
    "smart_scheduler.py",
    "main.py",
    "run_hourly_bot.py",
    "bot.py",
    "README.md"
)

Write-Host "📤 Uploading files to droplet..." -ForegroundColor Yellow
foreach ($file in $files) {
    $remote_file = "$remote_path/$file"
    $remote_dir = Split-Path -Parent $remote_file
    
    # Ensure remote directory exists
    ssh $droplet "mkdir -p $remote_dir"
    
    Write-Host "   -> $file"
    scp $file "${droplet}:${remote_file}"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to upload $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "All files uploaded successfully" -ForegroundColor Green
Write-Host ""

# Restart services
Write-Host "Restarting services..." -ForegroundColor Yellow
ssh $droplet "systemctl restart tripavail-fourhour.service"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Services restarted" -ForegroundColor Green
} else {
    Write-Host "Service restart failed - check manually" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Verify deployment:" -ForegroundColor White
Write-Host "   ssh root@138.68.141.3 `"tail -f /opt/tripavail_ai/logs/app.log`""
Write-Host ""
Write-Host "Check errors:" -ForegroundColor White
Write-Host "   ssh root@138.68.141.3 `"tail -n 50 /opt/tripavail_ai/logs/app_error.log`""
Write-Host ""
Write-Host "Next four-hour cycle will use centralized logging" -ForegroundColor Green

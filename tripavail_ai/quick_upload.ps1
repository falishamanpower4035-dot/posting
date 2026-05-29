# Quick Upload Script
$password = "tRipavail1556--"
$server = "root@138.68.141.3"
$remotePath = "/opt/tripavail_ai/"

Write-Host "Uploading files to droplet..." -ForegroundColor Green

# Create the directory first
echo $password | ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password $server "mkdir -p $remotePath"

# Upload files
$files = @(
    "smart_scheduler.py",
    "bot.py", 
    "main.py",
    "requirements.txt",
    ".env",
    "config",
    "core",
    "scripts",
    "social_media",
    "assets",
    "data",
    "droplet_setup.sh",
    "system_check.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Uploading $file..."
        scp -o StrictHostKeyChecking=no -o PreferredAuthentications=password -r $file "${server}:${remotePath}"
    }
}

Write-Host "`nUpload complete!" -ForegroundColor Green
Write-Host "`nNow SSH to server and run:" -ForegroundColor Yellow
Write-Host "  cd /opt/tripavail_ai" -ForegroundColor Cyan
Write-Host "  bash droplet_setup.sh" -ForegroundColor Cyan



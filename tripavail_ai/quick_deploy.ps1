# Quick Deploy - Only Essential Files
Write-Host "Uploading only essential files..." -ForegroundColor Green

$server = "root@138.68.141.3"
$remote = "/opt/tripavail_ai/"

# Upload Python files
Write-Host "Uploading Python files..."
scp smart_scheduler.py bot.py main.py system_check.py ${server}:${remote}

# Upload config files
Write-Host "Uploading config files..."
scp requirements.txt .env droplet_setup.sh ${server}:${remote}

# Upload folders (excluding large files)
Write-Host "Uploading config folder..."
scp -r config ${server}:${remote}

Write-Host "Uploading core folder..."
scp -r core ${server}:${remote}

Write-Host "Uploading scripts folder..."
scp -r scripts ${server}:${remote}

Write-Host "Uploading social_media folder..."
scp -r social_media ${server}:${remote}

# Upload only essential data
Write-Host "Uploading data/posts.json..."
scp data/posts.json ${server}:${remote}data/ 2>$null

Write-Host "`nUpload complete!" -ForegroundColor Green
Write-Host "Time: ~2-3 minutes" -ForegroundColor Yellow



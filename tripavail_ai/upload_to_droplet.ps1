# TripAvail AI - Upload to DigitalOcean Droplet
# Run this on Windows PowerShell

$DROPLET_IP = "138.68.141.3"
$DROPLET_USER = "root"
$PROJECT_PATH = "D:\posty\tripavail_ai"
$REMOTE_PATH = "/opt/tripavail_ai/"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  TripAvail AI - Upload to Droplet" -ForegroundColor Cyan
Write-Host "  Target: $DROPLET_IP" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "smart_scheduler.py")) {
    Write-Host "[!] Error: Not in project directory" -ForegroundColor Red
    Write-Host "[i] Please navigate to: $PROJECT_PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "[i] Current directory: $PWD" -ForegroundColor Yellow
Write-Host ""

# Files to exclude
$EXCLUDE_PATTERNS = @(
    "venv",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git",
    ".vscode",
    "*.log",
    "drive_token.json",
    "temp_*",
    "data_backup_*"
)

Write-Host "[i] Preparing to upload..." -ForegroundColor Yellow
Write-Host ""

# Check if SCP is available
$scpAvailable = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scpAvailable) {
    Write-Host "[!] SCP not found. Please install OpenSSH or use WinSCP" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install OpenSSH on Windows:" -ForegroundColor Yellow
    Write-Host "  Settings > Apps > Optional Features > Add OpenSSH Client" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or download WinSCP: https://winscp.net/" -ForegroundColor Yellow
    exit 1
}

Write-Host "[✓] SCP available" -ForegroundColor Green
Write-Host ""

# Confirm upload
Write-Host "This will upload the entire project to:" -ForegroundColor Yellow
Write-Host "  $DROPLET_USER@$DROPLET_IP`:$REMOTE_PATH" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue? (Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "[i] Upload cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[i] Starting upload... This may take a few minutes" -ForegroundColor Yellow
Write-Host ""

# Create list of files to upload (excluding patterns)
$filesToUpload = @(
    "smart_scheduler.py",
    "bot.py",
    "main.py",
    "system_check.py",
    "requirements.txt",
    ".env",
    "droplet_setup.sh",
    "config",
    "core",
    "scripts",
    "social_media",
    "assets",
    "data"
)

# Upload files
foreach ($item in $filesToUpload) {
    if (Test-Path $item) {
        Write-Host "[↑] Uploading $item..." -ForegroundColor Cyan
        
        if (Test-Path $item -PathType Container) {
            # Directory
            scp -r $item "${DROPLET_USER}@${DROPLET_IP}:${REMOTE_PATH}"
        } else {
            # File
            scp $item "${DROPLET_USER}@${DROPLET_IP}:${REMOTE_PATH}"
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[✓] $item uploaded" -ForegroundColor Green
        } else {
            Write-Host "[✗] Failed to upload $item" -ForegroundColor Red
        }
    } else {
        Write-Host "[i] Skipping $item (not found)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Upload Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Connect to your droplet:" -ForegroundColor White
Write-Host "   ssh $DROPLET_USER@$DROPLET_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run the setup script:" -ForegroundColor White
Write-Host "   cd /opt/tripavail_ai" -ForegroundColor Cyan
Write-Host "   bash droplet_setup.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Start the scheduler:" -ForegroundColor White
Write-Host "   systemctl start tripavail-scheduler" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Monitor logs:" -ForegroundColor White
Write-Host "   tail -f /opt/tripavail_ai/logs/scheduler.log" -ForegroundColor Cyan
Write-Host ""


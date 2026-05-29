# Sync Phase 2 Sandbox from Production
# ======================================
# Copy stable production code to sandbox for experimentation

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Sync Sandbox from Production" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$PRODUCTION_ROOT = ".."
$SANDBOX_ROOT = "."

Write-Host "[i] This will copy production code to sandbox" -ForegroundColor Yellow
Write-Host "    Source: $PRODUCTION_ROOT" -ForegroundColor White
Write-Host "    Target: $SANDBOX_ROOT" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "[i] Sync cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[1/4] Syncing core modules..." -ForegroundColor Cyan

# Copy core directory structure
$coreModules = @(
    "core/__init__.py",
    "core/media",
    "core/content",
    "core/social",
    "core/scheduling",
    "core/pipeline",
    "core/news",
    "core/utils"
)

foreach ($module in $coreModules) {
    $source = Join-Path $PRODUCTION_ROOT $module
    $dest = Join-Path $SANDBOX_ROOT $module
    
    if (Test-Path $source) {
        Write-Host "  [✓] Copying $module..." -ForegroundColor White
        
        # Create parent directory if needed
        $destParent = Split-Path $dest -Parent
        if (-not (Test-Path $destParent)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }
        
        if (Test-Path $source -PathType Container) {
            Copy-Item -Path $source -Destination $dest -Recurse -Force
        } else {
            Copy-Item -Path $source -Destination $dest -Force
        }
    } else {
        Write-Host "  [!] Skipping $module (not found)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[2/4] Syncing config files..." -ForegroundColor Cyan

# Copy config (but NOT .env - keep sandbox .env separate!)
Copy-Item -Path "$PRODUCTION_ROOT/config/settings.py" -Destination "config/" -Force
Write-Host "  [✓] settings.py copied" -ForegroundColor White

Write-Host ""
Write-Host "[3/4] Syncing test scripts..." -ForegroundColor Cyan

# Copy useful scripts for reference
if (Test-Path "$PRODUCTION_ROOT/scripts") {
    Copy-Item -Path "$PRODUCTION_ROOT/scripts/*test*.py" -Destination "scripts/" -Force -ErrorAction SilentlyContinue
    Write-Host "  [✓] Test scripts copied" -ForegroundColor White
}

Write-Host ""
Write-Host "[4/4] Preserving sandbox configuration..." -ForegroundColor Cyan

# Ensure sandbox .env is NOT overwritten
if (-not (Test-Path ".env_sandbox")) {
    Write-Host "  [!] No .env_sandbox found - please create one!" -ForegroundColor Yellow
} else {
    Write-Host "  [✓] Sandbox .env preserved" -ForegroundColor Green
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Sync Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Production code synced to sandbox." -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review changes: git diff" -ForegroundColor White
Write-Host "  2. Test sandbox: python test_phase2.py" -ForegroundColor White
Write-Host "  3. Start experimenting with Phase 2 features!" -ForegroundColor White
Write-Host ""

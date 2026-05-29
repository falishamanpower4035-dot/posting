# Phase 2 Development - Quick Start
# ===================================

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "║           TRIPAVAIL AI - PHASE 2 SANDBOX                      ║" -ForegroundColor Cyan
Write-Host "║           Quick Start & Status Check                          ║" -ForegroundColor Cyan
Write-Host "║                                                               ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "[1/3] Activating Python environment..." -ForegroundColor Yellow
& "D:\posty\tripavail_ai\venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✅ Python environment activated" -ForegroundColor Green
} else {
    Write-Host "      ⚠️  Environment activation failed (may already be active)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/3] Checking sandbox status..." -ForegroundColor Yellow

# Check if .env_sandbox exists
if (Test-Path ".\phase2_sandbox\.env_sandbox") {
    Write-Host "      ✅ Sandbox environment configured" -ForegroundColor Green
} else {
    Write-Host "      ❌ .env_sandbox not found!" -ForegroundColor Red
    Write-Host "         Run: copy .\phase2_sandbox\.env_sandbox_template .\phase2_sandbox\.env_sandbox" -ForegroundColor Yellow
    Write-Host "         Then edit with TEST credentials" -ForegroundColor Yellow
}

# Check directory structure
$sandboxDirs = @("phase2_sandbox\config", "phase2_sandbox\core", "phase2_sandbox\data", "phase2_sandbox\logs")
$allPresent = $true
foreach ($dir in $sandboxDirs) {
    if (Test-Path $dir) {
        # Silent check
    } else {
        Write-Host "      ❌ Missing: $dir" -ForegroundColor Red
        $allPresent = $false
    }
}

if ($allPresent) {
    Write-Host "      ✅ All sandbox directories present" -ForegroundColor Green
}

Write-Host ""
Write-Host "[3/3] Running sandbox tests..." -ForegroundColor Yellow
Write-Host ""

# Run test suite
python .\phase2_sandbox\test_phase2.py

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  READY FOR PHASE 2 DEVELOPMENT!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📂 Sandbox Location:" -ForegroundColor Yellow
Write-Host "   D:\posty\tripavail_ai\phase2_sandbox" -ForegroundColor White
Write-Host ""
Write-Host "📖 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Review: .\phase2_sandbox\README.md" -ForegroundColor White
Write-Host "   2. Configure: Edit .\phase2_sandbox\.env_sandbox with test keys" -ForegroundColor White
Write-Host "   3. Experiment: Add your Phase 2 features to sandbox/" -ForegroundColor White
Write-Host "   4. Test: python .\phase2_sandbox\test_phase2.py" -ForegroundColor White
Write-Host ""
Write-Host "💡 Sandbox Features:" -ForegroundColor Yellow
Write-Host "   ✓ Isolated from production (changes won't affect main project)" -ForegroundColor White
Write-Host "   ✓ Separate .env_sandbox (use TEST credentials only)" -ForegroundColor White
Write-Host "   ✓ DRY_RUN mode enabled (prevents actual social media posts)" -ForegroundColor White
Write-Host "   ✓ Full core/ modules copied for experimentation" -ForegroundColor White
Write-Host "   ✓ Detailed logging to sandbox logs/" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Phase 2 Ideas to Explore:" -ForegroundColor Yellow
Write-Host "   • Advanced AI models (GPT-4o, Claude 3.5)" -ForegroundColor White
Write-Host "   • Multi-language content generation" -ForegroundColor White
Write-Host "   • New platform integrations (TikTok, LinkedIn)" -ForegroundColor White
Write-Host "   • Enhanced video generation techniques" -ForegroundColor White
Write-Host "   • Advanced image selection algorithms" -ForegroundColor White
Write-Host "   • Analytics and performance tracking" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Remember:" -ForegroundColor Red
Write-Host "   • NEVER commit .env_sandbox with real credentials" -ForegroundColor White
Write-Host "   • Keep SANDBOX_MODE=true in .env_sandbox" -ForegroundColor White
Write-Host "   • Test thoroughly before promoting to production" -ForegroundColor White
Write-Host ""

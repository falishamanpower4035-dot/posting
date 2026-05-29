# Phase 2 Development Sandbox

This is an isolated development environment for Phase 2 features of TripAvail AI. Changes made here **will not affect** the production system.

## 🎯 Purpose

- Experiment with new features safely
- Test integrations without disrupting production
- Iterate quickly on Phase 2 enhancements
- Maintain production stability while innovating

## 📁 Structure

```
phase2_sandbox/
├── config/              # Sandbox-specific configuration
├── core/                # Copy of core modules for experimentation
├── data/                # Test data (isolated from production)
├── logs/                # Sandbox logs
├── scripts/             # Test and development scripts
├── .env_sandbox         # Sandbox environment variables
└── test_phase2.py       # Quick test runner
```

## 🚀 Getting Started

### 1. Activate Python Environment

```powershell
# From project root
D:\posty\tripavail_ai\venv\Scripts\Activate.ps1
```

### 2. Configure Sandbox Environment

```powershell
# Copy and edit sandbox environment
cd phase2_sandbox
cp .env_sandbox_template .env_sandbox
# Edit .env_sandbox with your test credentials
```

### 3. Run Sandbox Tests

```powershell
# Run Phase 2 test suite
python test_phase2.py
```

## 🔒 Safety Features

- **Isolated Data**: Separate `data/` directory prevents production data corruption
- **Separate .env**: `SANDBOX_MODE=true` flag prevents production API calls
- **Test Credentials**: Use test API keys, not production keys
- **Logging**: All sandbox activity logged to `logs/phase2_*.log`

## 🧪 What to Test in Phase 2

### Current Ideas:
- [ ] Enhanced video generation techniques
- [ ] Advanced AI models (GPT-4o, Claude 3.5)
- [ ] Multi-language content support
- [ ] Advanced scheduling algorithms
- [ ] New social media platform integrations
- [ ] Improved image selection algorithms
- [ ] Voice narration enhancements
- [ ] Analytics and performance tracking

## 📊 Current Status

**Phase 1 (Production)**:
- ✅ Shutterstock integration (Priority #1)
- ✅ Pexels integration (Priority #2)
- ✅ Unsplash integration (Priority #3)
- ✅ AI fallback (DALL-E + Stability AI)
- ✅ Instagram, Facebook, YouTube posting
- ✅ Smart scheduler with 4-hour spacing
- ✅ ElevenLabs Turbo v2.5 voiceovers
- ✅ 9:16 vertical video @ 60 FPS

**Phase 2 (Experimental)**:
- 🔬 New features to be developed here
- 🔬 Experimental integrations
- 🔬 Performance optimizations

## 🔄 Syncing Changes

### From Production to Sandbox (Get latest stable code):
```powershell
./sync_from_production.ps1
```

### From Sandbox to Production (Deploy tested features):
```powershell
# First, thoroughly test in sandbox
python test_phase2.py

# Then manually review and copy specific files
# NEVER bulk copy - review each change!
```

## ⚠️ Important Guidelines

1. **Never use production credentials** in sandbox `.env_sandbox`
2. **Always test thoroughly** before considering production deployment
3. **Keep sandbox isolated** - don't modify production files from here
4. **Document experiments** - add notes to this README
5. **Commit frequently** - use git branches for major experiments

## 🎨 Experiment Ideas

Add your Phase 2 ideas here:

### Example: Advanced Image Selection
- Test multiple stock photo APIs simultaneously
- A/B test different image scoring algorithms
- Experiment with AI-based image relevance scoring

### Example: Enhanced Social Media
- Test TikTok integration
- Experiment with LinkedIn posting
- Try Pinterest integration

### Example: Content Generation
- Test GPT-4o for more creative descriptions
- Experiment with Claude 3.5 for different tone
- Try multi-modal AI for image-based story generation

---

**Last Updated**: November 5, 2025  
**Sandbox Version**: 2.0  
**Production Version**: 1.0 (with Shutterstock)

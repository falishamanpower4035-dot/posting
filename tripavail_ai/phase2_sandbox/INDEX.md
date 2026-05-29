# Phase 2 Sandbox - Documentation Index

## 📖 Quick Navigation

### Getting Started (Start Here!)
1. **[PHASE2_QUICKSTART.md](../PHASE2_QUICKSTART.md)** ⭐
   - Complete overview
   - Quick commands
   - Safety features
   - Development workflow

2. **[START_PHASE2.ps1](../START_PHASE2.ps1)** 🚀
   - One-click sandbox activation
   - Runs tests automatically
   - Displays status

3. **[WELCOME.py](WELCOME.py)** 👋
   - Interactive welcome message
   - Quick reference guide
   - Run: `python WELCOME.py`

### Detailed Documentation
4. **[README.md](README.md)** 📚
   - Comprehensive sandbox guide
   - Phase 2 feature ideas
   - Safety guidelines
   - Usage instructions

5. **[PHASE2_SETUP_COMPLETE.md](../PHASE2_SETUP_COMPLETE.md)** ✅
   - Setup completion summary
   - What was created
   - Test results
   - Next steps

### Configuration
6. **[.env_sandbox_template](.env_sandbox_template)** 🔧
   - Environment template
   - Copy to `.env_sandbox`
   - Add TEST credentials only

7. **[config/settings.py](config/settings.py)** ⚙️
   - Sandbox-specific settings
   - Loads from `.env_sandbox`
   - Feature flags for experiments

### Testing
8. **[test_phase2.py](test_phase2.py)** 🧪
   - Main test suite (5/5 passing)
   - Validates sandbox setup
   - Run: `python test_phase2.py`

### Utilities
9. **[sync_from_production.ps1](sync_from_production.ps1)** 🔄
   - Sync latest production code
   - Preserves sandbox config
   - Run when production updates

10. **[.gitignore](.gitignore)** 🚫
    - Protects `.env_sandbox`
    - Excludes data and logs
    - Prevents credential leaks

## 🎯 Common Tasks

### First Time Setup
```powershell
# 1. Start sandbox
.\START_PHASE2.ps1

# 2. Configure environment
copy phase2_sandbox\.env_sandbox_template phase2_sandbox\.env_sandbox
# Edit .env_sandbox with TEST credentials

# 3. Run tests
python phase2_sandbox\test_phase2.py
```

### Daily Development
```powershell
# Enter sandbox
cd phase2_sandbox

# Check status
python test_phase2.py

# View documentation
python WELCOME.py

# Check logs
cat logs\*.log
```

### Syncing with Production
```powershell
# Get latest production code
cd phase2_sandbox
powershell -ExecutionPolicy Bypass -File sync_from_production.ps1
```

## 📁 Directory Structure

```
phase2_sandbox/
│
├── 📖 Documentation
│   ├── README.md                    ← Sandbox guide
│   ├── WELCOME.py                   ← Welcome message
│   └── INDEX.md                     ← This file
│
├── 🔧 Configuration
│   ├── .env_sandbox_template        ← Environment template
│   ├── .env_sandbox                 ← Your config (gitignored)
│   └── config/settings.py           ← Sandbox settings
│
├── 🧪 Testing
│   └── test_phase2.py               ← Test suite (5/5 passing)
│
├── 🔄 Utilities
│   ├── sync_from_production.ps1     ← Sync script
│   └── .gitignore                   ← Git protection
│
├── 💻 Code (for experimentation)
│   └── core/                        ← Full module copy
│       ├── content/                 ← Content generation
│       ├── media/                   ← Images, video, audio
│       ├── news/                    ← News fetching
│       ├── pipeline/                ← Orchestration
│       ├── scheduling/              ← Smart scheduler
│       ├── social/                  ← Social posting
│       └── utils/                   ← Utilities
│
├── 📊 Data (isolated)
│   ├── data/                        ← Test data only
│   └── logs/                        ← Sandbox logs
│
└── 📝 Scripts
    └── scripts/                     ← Test scripts
```

## 🎓 Learning Path

### Level 1: Getting Started
1. Read [PHASE2_QUICKSTART.md](../PHASE2_QUICKSTART.md)
2. Run `.\START_PHASE2.ps1`
3. Explore [README.md](README.md)

### Level 2: Configuration
1. Copy `.env_sandbox_template` to `.env_sandbox`
2. Add test API keys
3. Run `python test_phase2.py`

### Level 3: Development
1. Choose a Phase 2 feature
2. Modify code in `core/`
3. Test frequently with `test_phase2.py`

### Level 4: Advanced
1. Create custom test scripts
2. Experiment with feature flags
3. Sync with production as needed

## ⚠️ Important Files (Never Commit!)
- `.env_sandbox` - Contains credentials
- `data/*` - Test data
- `logs/*` - Log files

These are protected by `.gitignore` ✅

## 🆘 Troubleshooting

### Tests Failing?
```powershell
# Check environment
python config\settings.py

# Verify files
python test_phase2.py

# Check logs
cat logs\*.log
```

### Need Fresh Start?
```powershell
# Sync from production
cd phase2_sandbox
powershell -ExecutionPolicy Bypass -File sync_from_production.ps1
```

### Production Broke?
**Don't worry!** Sandbox is isolated. Production is safe.
Your changes are only in `phase2_sandbox/`

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start sandbox | `.\START_PHASE2.ps1` |
| Run tests | `python phase2_sandbox\test_phase2.py` |
| View welcome | `python phase2_sandbox\WELCOME.py` |
| Sync production | `cd phase2_sandbox; .\sync_from_production.ps1` |
| Check settings | `python phase2_sandbox\config\settings.py` |
| View logs | `cat phase2_sandbox\logs\*.log` |

## 🎉 You're Ready!

Everything is documented and tested. Start exploring Phase 2 features!

```powershell
.\START_PHASE2.ps1
```

---

*Last Updated: November 5, 2025*  
*Sandbox Version: 2.0*  
*Documentation Status: Complete ✅*

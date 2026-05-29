# Centralized Logging System - Phase 0 Complete ✅

## What Was Implemented

### 1. Central Logging Module
**File**: `core/utils/logging_setup.py`

**Features**:
- **Unified configuration** from `config/settings.py` (LOG_LEVEL, LOG_ROTATION, LOG_RETENTION)
- **Multiple sinks**:
  - Console (color-coded, human-readable)
  - `app.log` (all logs, rotated daily, retained 30 days)
  - `app_error.log` (errors only, for quick troubleshooting)
  - `app.jsonl` (optional JSON logs, enable via `LOG_JSON=true`)
- **Stdlib logging interception**: All `logging.getLogger()` calls flow through Loguru
- **Automatic rotation & compression**: Logs rotate daily, compress to `.zip`, auto-delete after 30 days
- **Environment overrides**: `LOG_LEVEL`, `LOG_DIR`, `LOG_JSON` env vars

### 2. Entry Point Integration
Wired centralized logging into all entry points (zero code changes to modules):

- ✅ `main.py`
- ✅ `production_pipeline.py`
- ✅ `smart_scheduler.py`
- ✅ `run_hourly_bot.py`
- ✅ `bot.py`
- ✅ `scripts/run_two_hour_scheduler.py` (production droplet script)

**Changes made**:
- Import `from core.utils import logging_setup` at the top
- Removed duplicate `logger.add()` and `logging.basicConfig()` calls
- Replaced stdlib `logging.getLogger()` with `loguru.logger` where applicable

### 3. Documentation
**Updated**: `README.md`

Added comprehensive logging section covering:
- Log file locations and purposes
- Configuration via env vars or settings
- Rotation/retention rules
- Usage examples (Loguru + stdlib)
- Monitoring commands for production

### 4. Testing
**Created**: `scripts/test_centralized_logging.py`

**Test results**: ✅ All tests passed
- Loguru logger works (debug, info, warning, error, success)
- Stdlib logging intercepted correctly
- Context logging with extra fields works
- Log files created: `app.log` (1144 bytes), `app_error.log` (288 bytes)

## Improvements Delivered

### Before (Ad-hoc Logging)
- ❌ Scattered `logger.add()` calls across files
- ❌ Inconsistent log formats and file names
- ❌ Manual rotation/retention setup per module
- ❌ No stdlib logging interception
- ❌ Hard to change log level globally
- ❌ No JSON logs for analytics

### After (Centralized Logging)
- ✅ Single point of control (`core/utils/logging_setup.py`)
- ✅ Uniform log format with timestamps, module names, line numbers
- ✅ Automatic rotation (1 day) and retention (30 days) everywhere
- ✅ Stdlib logging flows through Loguru seamlessly
- ✅ Change log level via `LOG_LEVEL` env var (no code changes)
- ✅ Optional JSON logs via `LOG_JSON=true` for machine parsing
- ✅ Predictable file names: `app.log`, `app_error.log`, `app.jsonl`
- ✅ Compressed archives to save disk space

## Benefits

### Operations
- **Consistent logs**: Same format across all modules and scripts
- **Predictable location**: All logs in `logs/` directory
- **Disk safety**: Auto-rotation and retention prevent uncontrolled growth
- **Easier troubleshooting**: Tail `app_error.log` for quick error scans
- **Search-friendly**: Grep across `app.log` for cross-module traces

### Development
- **Zero boilerplate**: No need to configure logging in new files
- **Works everywhere**: `from loguru import logger` or `import logging` both work
- **Rich context**: Add extra fields (post_id, region, etc.) to logs
- **Fast iteration**: Change log level without code changes

### Future-Ready
- **Structured logs**: JSON mode ready for analytics pipelines (ELK, Loki, Splunk)
- **Alert integration**: Easy to add Sentry, PagerDuty, or custom webhooks
- **Metrics**: Can extract counts, latencies, errors from JSON logs

## No Disruption Strategy

### What Changed
- ✅ Added `core/utils/logging_setup.py` (new file, zero impact)
- ✅ One import line at top of each entry point
- ✅ Removed duplicate logger setup in entry points only

### What Did NOT Change
- ✅ All existing `logger.info()`, `logger.error()` calls work as-is
- ✅ No changes to core modules (they continue using `from loguru import logger`)
- ✅ Legacy per-module logs (e.g., `fourhour.log`) still work during migration
- ✅ No performance impact (Loguru is fast and efficient)

### Rollback Plan (if needed)
1. Remove `from core.utils import logging_setup` from entry points
2. Restore old `logger.add()` or `logging.basicConfig()` calls
3. Delete `core/utils/logging_setup.py`
4. Total rollback time: ~2 minutes

## Next Steps (Optional - Phase 1+)

### Phase 1: Cleanup (Recommended)
- Remove ad-hoc `logger.add()` calls in modules (rely on central setup)
- Delete legacy per-module log files (e.g., `fourhour.log`, `tourism_editor.log`)
- Consolidate all logs into `app.log` and `app_error.log`

### Phase 2: Enhancements (Optional)
- Enable JSON logs (`LOG_JSON=true`) for analytics
- Add contextual fields (post_id, job_type, region) to all log calls
- Set up log aggregation (e.g., Loki, ELK) for centralized monitoring

### Phase 3: Alerts (Optional)
- Integrate Sentry for error tracking
- Add rate-limited email/SMS alerts for critical errors
- Set up Prometheus metrics from log events

## Deployment to Production

### Local Testing
```bash
# Test centralized logging
python scripts\test_centralized_logging.py

# Verify log files
ls logs/
cat logs/app.log
cat logs/app_error.log
```

### Deploy to Droplet
```bash
# Upload updated files
scp core/utils/logging_setup.py root@138.68.141.3:/opt/tripavail_ai/core/utils/
scp scripts/run_two_hour_scheduler.py root@138.68.141.3:/opt/tripavail_ai/scripts/
scp production_pipeline.py root@138.68.141.3:/opt/tripavail_ai/
scp smart_scheduler.py root@138.68.141.3:/opt/tripavail_ai/

# Restart services
ssh root@138.68.141.3 "systemctl restart tripavail-fourhour.service"

# Verify logs on server
ssh root@138.68.141.3 "tail -f /opt/tripavail_ai/logs/app.log"
```

### Validation
After deployment, check:
- ✅ New log files created: `logs/app.log`, `logs/app_error.log`
- ✅ No errors in systemd service logs
- ✅ Legacy logs (e.g., `fourhour.log`) still work if needed
- ✅ Log format is consistent and readable

## Configuration Reference

### Environment Variables
```bash
# .env
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs            # Custom log directory
LOG_JSON=false          # Enable JSON logs (true/false)
```

### Settings (config/settings.py)
```python
LOGS_DIR = "logs"
LOG_LEVEL = "INFO"
LOG_ROTATION = "1 day"      # Also: "10 MB", "100 MB"
LOG_RETENTION = "30 days"   # Also: "7 days", "1 week"
```

### Log File Locations
- **All logs**: `logs/app.log`
- **Errors only**: `logs/app_error.log`
- **JSON logs**: `logs/app.jsonl` (if `LOG_JSON=true`)

### Monitoring Commands
```bash
# Tail live logs
tail -f logs/app.log

# Last 100 lines
tail -n 100 logs/app.log

# Search for errors
grep ERROR logs/app.log

# Search for specific event
grep "Shutterstock" logs/app.log

# Check log size
du -sh logs/
```

## Summary

**Phase 0 Status**: ✅ **COMPLETE**

- Central logging module implemented and tested
- Entry points wired (6 files)
- Documentation updated
- Zero disruption to existing code
- Rollback takes <2 minutes if needed
- Ready for production deployment

**Test Results**: ✅ **ALL PASSING**
- Loguru logging: ✅
- Stdlib interception: ✅
- Context logging: ✅
- Log files created: ✅

**Next Action**: Deploy to production droplet and validate for one 4-hour cycle.

# TripAvail AI - Simplified Pipeline (ONE BOT)

## ✅ FIXED: Now Using Only ONE Bot

### Active Systems (2 components only)

1. **tripavail-fourhour.timer** ⏰
   - Triggers every 4 hours
   - Starts `tripavail-fourhour.service`

2. **tripavail-fourhour.service** 🔄 (ALL-IN-ONE)
   - Fetches news from NewsData.io
   - Analyzes with OpenAI (filters duplicates, scores 1-10)
   - Generates posts (video, caption, images, voiceover, music)
   - Schedules posts (normal: 20 min, peak: 6/8/9 PM PKT)

3. **tripavail-daemon.service** 🤖 (Posting bot)
   - Continuously monitors scheduled posts
   - Posts to Instagram, Facebook, YouTube when due
   - Runs every 60 seconds

---

## 🎯 What Changed

**Before (CONFUSING):**
- ❌ `tripavail-fourhour.timer` → triggered `tripavail-twohour.service` 
- ❌ Two different names for same thing

**After (CLEAR):**
- ✅ `tripavail-fourhour.timer` → triggers `tripavail-fourhour.service`
- ✅ One clear naming convention
- ✅ Only ONE bot does everything (fetch + analyze + generate + schedule)

---

## 📋 Complete Flow

```
Every 4 Hours:
  tripavail-fourhour.timer
       ↓
  tripavail-fourhour.service
       ↓
  1. Fetch News
  2. Analyze News (OpenAI)
  3. Generate Posts
  4. Schedule Posts
       ↓
  data/scheduled_posts.json
       ↓
  tripavail-daemon.service (posts when due)
```

---

## ✅ Verification

```bash
# Check timer (runs every 4 hours)
systemctl status tripavail-fourhour.timer

# Check service (does everything)
systemctl status tripavail-fourhour.service

# Check posting daemon (runs continuously)
systemctl status tripavail-daemon.service

# View logs
journalctl -u tripavail-fourhour.service -f
```

---

## 🚨 Status

✅ **ONE bot** (`tripavail-fourhour.service`) does everything
✅ **ONE timer** (`tripavail-fourhour.timer`) triggers every 4 hours
✅ **ONE posting daemon** (`tripavail-daemon.service`) posts when due
✅ **No more confusion** - clear naming convention


# ⚡ Smart Scheduler - Quick Start

## 🎯 What It Does

**Automatically schedules your top 10 best videos to Instagram, Facebook, and YouTube at global peak times**

✨ **NEW: Intelligent Spacing** - Posts are automatically spaced 30-40 minutes apart for natural, non-spammy posting!

---

## 🚀 Quick Commands

### View Top 10 Posts
```bash
python smart_scheduler.py --show-top
```

### View Schedule
```bash
python smart_scheduler.py --schedule
```

### Test Posting (Immediate)
```bash
python smart_scheduler.py --post-now
```

### Run Scheduler
```bash
python smart_scheduler.py --run
```

### Windows GUI
```bash
start_scheduler.bat
```

---

## ⏰ Posting Times (UTC)

| Time | Platforms | Reaches | Spacing |
|------|-----------|---------|---------|
| **06:00** | Instagram | Asia morning | - |
| **09:00** | Facebook | Asia evening | - |
| **14:00** | Instagram | USA morning + Europe afternoon | - |
| **14:37** | YouTube | (spaced from 14:00) | +37min |
| **18:00** | Instagram | USA afternoon + Europe evening ⭐ | - |
| **18:35** | Facebook | (spaced from 18:00) | +35min |
| **19:10** | YouTube | (spaced from 18:35) | +35min |
| **21:00** | Instagram | USA peak + Europe night | - |
| **21:38** | YouTube | (spaced from 21:00) | +38min |
| **23:00** | Facebook | USA evening | - |

**Total: 10 posts/day (automatically spaced 30-40 minutes apart)**

✨ **Example at 18:00 UTC:**
- 18:00 → Post to Instagram
- 18:35 → Post to Facebook (+35 min)
- 19:10 → Post to YouTube (+35 min)

Natural posting = Better engagement!

---

## 📊 How Posts Are Ranked

**Rank Score = AI Score (40%) + Priority (30%) + Viral Potential (20%) + Freshness (10%)**

Top 10 highest-scoring posts get scheduled automatically.

---

## 🎯 Platform Distribution

- **Instagram**: 4 posts/day (highest engagement platform)
- **Facebook**: 3 posts/day (wide reach)
- **YouTube**: 3 posts/day (Shorts for discovery)

---

## ✅ What You Need

1. ✅ Posts generated in `data/posts/`
2. ✅ Final videos created (`final.mp4`)
3. ✅ API credentials configured (Instagram, Facebook, YouTube)
4. ✅ Virtual environment activated

---

## 🔧 First-Time Setup

1. **Check you have posts:**
   ```bash
   python smart_scheduler.py --show-top
   ```

2. **View the schedule:**
   ```bash
   python smart_scheduler.py --schedule
   ```

3. **Test with one post:**
   ```bash
   python smart_scheduler.py --post-now
   ```

4. **Start the scheduler:**
   ```bash
   python smart_scheduler.py --run
   ```

---

## 💡 Pro Tips

✅ **Keep generating content** - Run `python bot.py --generate-once` regularly  
✅ **Monitor rankings** - Check `--show-top` to see what's being posted  
✅ **Freshness matters** - Newer content ranks higher  
✅ **Quality over quantity** - Only top 10 get posted  

---

## 🎉 Expected Results

- **Automatic posting** at peak times
- **Top quality** content only
- **Global reach** across timezones
- **3 platforms** for maximum exposure
- **10 posts/day** for consistent presence

---

## 📞 Need Help?

- **Full Guide**: See `SMART_SCHEDULER_GUIDE.md`
- **System Docs**: See `README.md`
- **Issues**: Check logs in `logs/` directory

---

## 🚀 Ready?

```bash
# Start the scheduler
python smart_scheduler.py --run

# Or use Windows launcher
start_scheduler.bat
```

**Your top 10 videos will now post automatically at global peak times! 🌍**


# 📊 24-Hour System Monitoring Plan

**Start Time:** November 2, 2025 19:00 UTC  
**End Time:** November 3, 2025 19:00 UTC

---

## 🎯 **Current Active Systems**

### **System 1: Two-Hour Content Generator**
- **Service:** `tripavail-twohour.timer` + `tripavail-twohour.service`
- **Runs:** Every 2 hours
- **Function:** Fetches news → Generates posts → Schedules to `scheduled_posts.json`
- **Next Runs:** ~21:00, 23:00, 01:00, 03:00, 05:00, 07:00, 09:00, 11:00, 13:00, 15:00, 17:00, 19:00 UTC

### **System 2: Scheduled Post Executor (Daemon)**
- **Service:** `tripavail-daemon.service`
- **Runs:** Continuously (checks every 60 seconds)
- **Function:** Reads `scheduled_posts.json` → Posts when time arrives → Marks as done

### **System 3: Smart Scheduler / "Hourly Bot"**
- **Service:** `tripavail-scheduler.service`
- **Runs:** Continuously
- **Peak Times:** 06:00, 09:00, 14:00, 18:00, 21:00, 23:00 UTC
- **Function:** Ranks all posts (top 10) → Posts at peak times → Sends email notifications

---

## 📋 **What to Monitor**

### **1. Post Generation (System 1)**
- ✅ How many posts are generated every 2 hours?
- ✅ Are posts successfully added to `scheduled_posts.json`?
- ✅ Are high-priority posts (score 10+) scheduled for peak times?
- ✅ Are normal posts (score 7-9) scheduled for 20 minutes after generation?

### **2. Scheduled Post Execution (System 2)**
- ✅ Are scheduled posts from JSON being posted on time?
- ✅ Any posts getting stuck in "pending" status?
- ✅ Are all platforms (Instagram, Facebook, YouTube) posting successfully?

### **3. Peak-Time Smart Posting (System 3)**
- ✅ Is Smart Scheduler posting at all 6 peak times (06:00, 09:00, 14:00, 18:00, 21:00, 23:00)?
- ✅ What posts are being selected at peak times (new vs. old)?
- ✅ Are top-ranked posts being prioritized?
- ✅ Are email notifications being sent after each post?

### **4. Potential Issues**
- ⚠️ **Duplication:** Are the same posts being posted by both System 2 and System 3?
- ⚠️ **Conflicts:** Are posts being posted at the same time by different systems?
- ⚠️ **Missed Posts:** Are any posts not getting posted at all?
- ⚠️ **Timing:** Are peak times actually being hit?

---

## 🔍 **Commands to Check System Status**

### **Check All Services**
```bash
ssh root@138.68.141.3 "systemctl status tripavail-twohour.service tripavail-daemon.service tripavail-scheduler.service"
```

### **Check Scheduled Posts**
```bash
ssh root@138.68.141.3 "cat /opt/tripavail_ai/data/scheduled_posts.json | python -m json.tool"
```

### **Check Recent Posts**
```bash
ssh root@138.68.141.3 "journalctl -u tripavail-daemon.service -u tripavail-scheduler.service --since '1 hour ago' --no-pager | tail -100"
```

### **Check Post Status**
```bash
ssh root@138.68.141.3 "cd /opt/tripavail_ai && /opt/tripavail_ai/venv/bin/python -c 'from core.content.post_manager import PostManager; pm = PostManager(); posts = pm.get_all_posts(); print(f\"Total posts: {len(posts)}\"); [print(f\"{p}: IG={pm.is_posted(p,\"instagram\")}, FB={pm.is_posted(p,\"facebook\")}, YT={pm.is_posted(p,\"youtube\")}\") for p in sorted(posts)[-10:]]'"
```

### **Check Email Notifications**
- Check inbox: `holywolf92@gmail.com`
- Subject: "TripAvail - INFO"
- Should receive emails after each Smart Scheduler post

---

## 📊 **Key Metrics to Track**

### **Post Generation Rate**
- Expected: ~12 posts per day (every 2 hours)
- Monitor: Actual posts generated

### **Peak-Time Posting**
- Expected: 6 posts per day (at 06:00, 09:00, 14:00, 18:00, 21:00, 23:00 UTC)
- Monitor: Are all 6 times being hit?

### **Platform Coverage**
- Expected: ~18-30 posts per day across all platforms
- Monitor: Instagram, Facebook, YouTube posting rates

### **Email Notifications**
- Expected: 6 emails per day (one per peak-time post)
- Monitor: Are emails being received?

---

## 🎯 **Expected Behavior Over 24 Hours**

### **Hour 0-2 (19:00-21:00 UTC)**
- ✅ System 1: Next run at ~21:00 (generates new posts)
- ✅ System 2: Executes any scheduled posts from JSON
- ✅ System 3: Posts at 21:00 peak time (if content available)

### **Hour 2-4 (21:00-23:00 UTC)**
- ✅ System 1: Runs at 21:00 (generates new posts)
- ✅ System 2: Executes scheduled posts
- ✅ System 3: Posts at 23:00 peak time

### **Hour 4-6 (23:00-01:00 UTC)**
- ✅ System 1: Next run at 01:00
- ✅ System 2: Executes scheduled posts
- ✅ System 3: No peak time in this window

### **Hour 6-8 (01:00-03:00 UTC)**
- ✅ System 1: Runs at 01:00, 03:00 (generates posts)
- ✅ System 2: Executes scheduled posts
- ✅ System 3: No peak time in this window

### **Hour 8-10 (03:00-05:00 UTC)**
- ✅ System 1: Runs at 05:00
- ✅ System 2: Executes scheduled posts
- ✅ System 3: Posts at 06:00 peak time ⭐

### **Hour 10-12 (05:00-07:00 UTC)**
- ✅ System 1: Runs at 07:00
- ✅ System 2: Executes scheduled posts
- ✅ System 3: Posts at 09:00 peak time ⭐

### **Hour 12-14 (07:00-09:00 UTC)**
- ✅ System 1: Runs at 09:00, 11:00
- ✅ System 2: Executes scheduled posts
- ✅ System 3: Posts at 14:00 peak time ⭐

### **Hour 14-16 (09:00-11:00 UTC)**
- ✅ System 1: Runs at 13:00
- ✅ System 2: Executes scheduled posts
- ✅ System 3: Posts at 18:00 peak time ⭐

### **Hour 16-18 (11:00-13:00 UTC)**
- ✅ System 1: Runs at 15:00, 17:00
- ✅ System 2: Executes scheduled posts
- ✅ System 3: Posts at 21:00 peak time ⭐

---

## ✅ **Success Criteria**

After 24 hours, the system should demonstrate:

1. ✅ **Stability:** All 3 systems running without crashes
2. ✅ **Generation:** ~12 new posts generated (every 2 hours)
3. ✅ **Peak-Time Posting:** 6 posts at peak times (06:00, 09:00, 14:00, 18:00, 21:00, 23:00)
4. ✅ **No Duplication:** Same post not posted twice by different systems
5. ✅ **Email Notifications:** 6 emails received (one per peak-time post)
6. ✅ **Platform Coverage:** Posts distributed across Instagram, Facebook, YouTube

---

## 🚨 **Red Flags to Watch For**

- ❌ **Service Crashes:** Any systemd service failing repeatedly
- ❌ **Missing Posts:** Scheduled posts not executing
- ❌ **Duplication:** Same post appearing multiple times
- ❌ **Timing Conflicts:** Posts scheduled at exact same time
- ❌ **Email Failures:** No emails received after Smart Scheduler posts
- ❌ **Stuck Posts:** Posts stuck in "pending" status

---

## 📝 **Notes Section**

_Use this section to record observations:_

**Date/Time:**
- 

---

**End of Monitoring Plan**


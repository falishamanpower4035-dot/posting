# Complete System Flow - How It Works After 4-Hour Cycle

## 🎯 Overview

The system runs in **TWO PARALLEL PROCESSES**:

1. **4-Hour Timer** → Generates posts and schedules them
2. **Scheduler Daemon** → Posts scheduled items when due

---

## 📅 STEP 1: 4-Hour Timer Triggers

**What:** `tripavail-fourhour.timer`  
**When:** Every 4 hours (6 times per day)  
**Service:** `tripavail-fourhour.service`  
**Script:** `scripts/run_two_hour_scheduler.py`

### What Happens:

```
1. Timer triggers at 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
2. Runs tripavail-fourhour.service
3. Executes: python scripts/run_two_hour_scheduler.py
```

---

## 🔍 STEP 2: News Fetching & Analysis

**Script:** `scripts/run_two_hour_scheduler.py` → `fetch_and_analyze()`

### Process:

```
1. NewsFetcher().run_fetch_cycle()
   ├─> Fetches tourism news from NewsData.io API
   ├─> Saves to: data/raw_news.json
   └─> Logs to: logs/fetch_log.txt

2. TourismEditor().run_analysis()
   ├─> Filters out already-used articles (PRIMARY DUPLICATE FILTER)
   ├─> Sends to OpenAI GPT-4 for analysis
   ├─> Scores each article 1-10 (tourism relevance)
   ├─> Saves to: data/processed_news.json
   └─> Returns: List of analyzed articles with scores
```

**CRITICAL SAFETY:**
- ✅ Filters duplicates BEFORE OpenAI (saves costs)
- ✅ Preserves article URLs for duplicate detection
- ✅ Handles OpenAI quota errors gracefully

---

## 🎬 STEP 3: Post Generation & Scheduling

**Script:** `scripts/run_two_hour_scheduler.py` → `generate_and_schedule()`

### Process:

```
1. ProductionPipeline().process_single_post(topic, post_idx)
   ├─> Generates video (images + voiceover + music)
   ├─> Creates caption with hashtags
   ├─> Saves to: data/posts/XXX/ (where XXX is post ID)
   └─> Returns: Success/failure

2. For each generated post:
   
   IF score >= 10 OR score == top_score:
       → schedule_smart_peak(post_id)
       └─> Schedules for peak times: 6 PM, 8 PM, 9 PM PKT
   
   ELSE (score 7-9):
       → schedule_after_minutes(post_id, minutes=20)
       └─> Schedules for 20 minutes after generation
```

**CRITICAL SAFETY:**
- ✅ Secondary duplicate filter (checks if topic already used)
- ✅ Only processes score >= 7 articles
- ✅ Uses max post ID + 1 (handles gaps correctly)

---

## 📋 STEP 4: Scheduling Logic

**File:** `core/scheduling/scheduler.py`

### Normal Posts (Score 7-9):
```
Schedule: NOW + 20 minutes
Example: Generated at 12:00 → Scheduled for 12:20
```

### Peak Posts (Score 10+):
```
Schedule: Next peak time (6 PM, 8 PM, or 9 PM PKT)
Example: Generated at 12:00 → Scheduled for 18:00 PKT (if 18:00 is next peak)
```

### Schedule Storage:
```
File: data/scheduled_posts.json
Format: {
  "post_id": "051",
  "scheduled_at": "2025-11-05T15:00:00+00:00",
  "status": "pending",
  "priority": 1
}
```

**CRITICAL SAFETY:**
- ✅ Prevents duplicate schedules (checks if already scheduled)
- ✅ Prevents scheduling already-posted posts
- ✅ Checks all platforms before scheduling

---

## 🤖 STEP 5: Scheduler Daemon (Continuous)

**Service:** `tripavail-daemon.service`  
**Script:** `scripts/scheduler_daemon.py`  
**Status:** Always running (checks every 60 seconds)

### Main Loop:

```
WHILE True:
    1. Check for pending scheduled posts
    2. Get current time (UTC)
    3. For each pending post:
       
       IF scheduled_time <= now:
           → Check if already posted to ALL platforms
           IF all posted:
               → Mark as done, skip
           ELIF partially posted:
               → Continue posting to remaining platforms ✅
           ELSE:
               → Post to all platforms
       
    4. Wait 60 seconds
    5. Repeat
```

---

## 📤 STEP 6: Posting Process

**Function:** `post_now(post_id)` in `scheduler_daemon.py`

### Platform Posting Order:

```
1. INSTAGRAM
   ├─> Check: Already posted? → Skip
   ├─> Post video reel
   ├─> Mark as posted
   ├─> Send email notification ✅
   └─> Wait 30 seconds

2. FACEBOOK
   ├─> Check: Already posted? → Skip
   ├─> Acquire lock (prevents race conditions)
   ├─> Post video reel
   ├─> Mark as posted
   ├─> Send email notification ✅
   └─> Wait 60 seconds

3. YOUTUBE
   ├─> Check: Already posted? → Skip
   ├─> Check: Retry limit reached? → Skip
   ├─> Check: Cooldown active? → Skip
   ├─> Upload video
   ├─> Mark as posted
   ├─> Send email notification ✅
   └─> Done
```

**CRITICAL SAFETY:**
- ✅ Only skips if ALL platforms posted (not just one)
- ✅ Allows partial posting to continue
- ✅ Checks each platform individually
- ✅ Handles YouTube retry logic (5 attempts, 1-hour cooldown)
- ✅ Sends email notifications for each platform

---

## ✅ STEP 7: Completion & Marking Done

**After posting attempt:**

```
Check posting status:
├─> Instagram: Posted?
├─> Facebook: Posted?
└─> YouTube: Posted?

IF all three posted:
    → Mark schedule as "done"
    → Send summary email ✅
    → Remove from pending list

ELIF partially posted:
    → Keep schedule active
    → Will retry on next check (60 seconds)
    → YouTube has special retry logic (5 attempts max)
```

---

## 📧 Email Notifications

**Sent for:**
- ✅ Instagram post success
- ✅ Instagram post failure
- ✅ Facebook post success
- ✅ Facebook post failure
- ✅ YouTube post success
- ✅ YouTube post failure
- ✅ Complete post summary (all platforms done)

**Recipient:** `holywolf92@gmail.com`  
**Method:** Gmail API (fallback to SMTP)

---

## 🛡️ Safety Mechanisms

### 1. Duplicate Prevention (Multiple Layers):

```
Layer 1: TourismEditor (before OpenAI)
  → Filters already-used articles by URL/title

Layer 2: generate_and_schedule()
  → Checks if topic already used (secondary check)

Layer 3: scheduler.add_schedule()
  → Prevents duplicate schedules
  → Checks if already posted to any platform

Layer 4: scheduler_daemon.post_now()
  → Checks if all platforms already posted
  → Only skips if ALL posted (not just one)
```

### 2. Race Condition Protection:

```
- File locks for Facebook posting
- File locks for scheduler daemon
- Double-check posting status before/after
- Small delays for metadata file writes
```

### 3. Partial Posting Support:

```
- If Instagram posted but Facebook/YouTube failed
- System continues posting to remaining platforms
- Does NOT skip entire post if one platform succeeds
```

### 4. Error Handling:

```
- YouTube: 5 retry attempts with 1-hour cooldown
- Facebook: Rate limit detection
- Instagram: Error logging
- All errors: Email notifications sent
```

---

## 📊 Example Timeline

```
00:00 UTC → 4-hour timer triggers
00:01 UTC → Fetch news from NewsData.io
00:02 UTC → Analyze with OpenAI (filter duplicates)
00:05 UTC → Generate 3 posts (scores 8, 9, 10)
00:10 UTC → Schedule posts:
           - Post 051 (score 8): 00:30 UTC
           - Post 052 (score 9): 00:30 UTC
           - Post 053 (score 10): 18:00 PKT (peak time)

00:30 UTC → Scheduler daemon checks
           → Posts 051 and 052 are due
           → Post to Instagram (success)
           → Email sent ✅
           → Post to Facebook (success)
           → Email sent ✅
           → Post to YouTube (success)
           → Email sent ✅
           → Summary email sent ✅
           → Mark as done

18:00 PKT → Scheduler daemon checks
           → Post 053 is due (peak time)
           → Post to Instagram (success)
           → Email sent ✅
           → Post to Facebook (success)
           → Email sent ✅
           → Post to YouTube (success)
           → Email sent ✅
           → Summary email sent ✅
           → Mark as done

04:00 UTC → Next 4-hour cycle begins...
```

---

## ✅ Guarantees

1. **No Duplicate Posts:**
   - Multiple layers of duplicate detection
   - URL and title matching
   - Schedule deduplication

2. **All Platforms Posted:**
   - Partial posting continues
   - Only skips if ALL platforms posted
   - Retry logic for YouTube

3. **Email Notifications:**
   - Every post attempt
   - Success/failure status
   - Summary when complete

4. **Error Recovery:**
   - YouTube retry with cooldown
   - Facebook rate limit handling
   - Graceful error handling

---

## 🎯 Summary

**After 4-hour cycle:**
1. ✅ News fetched and analyzed
2. ✅ Posts generated and scheduled
3. ✅ Scheduler daemon posts when due
4. ✅ Email notifications sent
5. ✅ All platforms receive posts
6. ✅ No duplicates

**The system is bulletproof!** 🛡️


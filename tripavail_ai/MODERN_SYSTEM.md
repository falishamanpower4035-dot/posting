# TripAvail AI - Modern System Architecture

## 🎯 Overview

The modern TripAvail AI system is **fully automated** and runs with **minimal intervention**. It consists of **2 main components** that work together seamlessly.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM COMPONENTS                         │
└─────────────────────────────────────────────────────────────┘

1. TRIGGER SYSTEM (Timer)
   └─> tripavail-fourhour.timer
       • Runs every 4 hours
       • Triggers content generation

2. CONTENT GENERATION (Service)
   └─> tripavail-fourhour.service
       • Fetches news
       • Analyzes content
       • Generates posts
       • Schedules for posting

3. POSTING SYSTEM (Daemon)
   └─> tripavail-daemon.service
       • Runs continuously
       • Monitors schedules
       • Posts to platforms

4. CLEANUP SYSTEM (Timer)
   └─> tripavail-cleanup.timer
       • Runs daily at midnight
       • Deletes old files
```

---

## 🔄 Complete Workflow

### Phase 1: Content Generation (Every 4 Hours)

**Trigger:** `tripavail-fourhour.timer` fires every 4 hours

**Process:**
```
1. FETCH NEWS
   ├─> NewsData.io API
   ├─> Tourism-related queries
   └─> Saves to: data/raw_news.json

2. ANALYZE NEWS
   ├─> Loads raw news
   ├─> Filters already-used articles (duplicate prevention)
   ├─> OpenAI GPT-4 analysis
   ├─> Scores each article (1-10 scale)
   ├─> Filters articles with score >= 7
   └─> Saves to: data/processed_news.json

3. GENERATE POSTS
   For each article (score >= 7):
   ├─> Story Analysis (OpenAI)
   │   ├─> Determines video duration (15-60s)
   │   ├─> Determines image count (8-15 images)
   │   ├─> Generates narrative script
   │   └─> Creates story beats
   │
   ├─> Image Generation
   │   ├─> Generates images based on story beats
   │   ├─> Uses Pexels API (primary) or Unsplash (fallback)
   │   └─> Resizes to 1080x1920 (vertical format)
   │
   ├─> Voiceover Generation
   │   ├─> Converts narrative script to speech
   │   └─> ElevenLabs TTS (premium voice)
   │
   ├─> Music Generation
   │   ├─> Generates 20-second background music
   │   └─> ElevenLabs Music API
   │
   ├─> Video Assembly
   │   ├─> Combines images into slideshow
   │   ├─> Syncs voiceover timing
   │   ├─> Mixes background music
   │   ├─> Adds text overlays (hook + captions)
   │   └─> Exports final video (1080x1920, 60 FPS)
   │
   ├─> Thumbnail Generation
   │   ├─> AI-powered thumbnail (Gemini)
   │   ├─> Multi-layer text overlay
   │   └─> OCR validation
   │
   └─> Saves to: data/posts/post_XXX/

4. SCHEDULE POSTS
   ├─> Normal Posts (Score 7-9)
   │   └─> Schedule for 20 minutes after generation
   │
   └─> Peak Posts (Score 10)
       └─> Schedule for peak times:
           • 6 PM PKT (1 PM UTC)
           • 8 PM PKT (3 PM UTC)
           • 9 PM PKT (4 PM UTC)
   
   Saves to: data/scheduled_posts.json
```

**Duration:** ~15-30 minutes per post (depending on complexity)

---

### Phase 2: Automated Posting (Every 60 Seconds)

**Trigger:** `tripavail-daemon.service` runs continuously, checks every 60 seconds

**Process:**
```
1. CHECK SCHEDULE
   ├─> Loads data/scheduled_posts.json
   ├─> Finds posts with status="pending"
   └─> Checks if scheduled_time <= now

2. TRIPLE-CHECK DUPLICATES
   ├─> Check 1: Before attempting (main loop)
   ├─> Check 2: Double-check with delay (post_now function)
   └─> Check 3: After posting (verify status)
   
   If already posted to ANY platform:
   └─> Skip and mark schedule as done

3. POST TO PLATFORMS
   
   Instagram:
   ├─> Upload video to Dropbox (temporary)
   ├─> Create Instagram media container
   ├─> Publish with caption + hashtags
   └─> Mark as posted

   Facebook:
   ├─> Acquire file lock (.facebook_post.lock)
   ├─> Double-check if already posted
   ├─> Upload video with caption + hashtags
   ├─> Release lock
   └─> Mark as posted

   YouTube:
   ├─> Check retry count (max 5 attempts)
   ├─> Check cooldown (1 hour between retries)
   ├─> Upload video as Short
   ├─> Add title, description, tags, thumbnail
   └─> Mark as posted

4. MARK AS DONE
   ├─> If posted to all platforms: mark_done()
   ├─> If YouTube retry limit reached: mark_done()
   ├─> If Facebook rate limited: mark_done()
   └─> Otherwise: Keep schedule active for retries
```

**Duration:** ~2-5 minutes per post (all platforms)

---

### Phase 3: Cleanup (Daily at Midnight)

**Trigger:** `tripavail-cleanup.timer` fires daily at 00:00 UTC

**Process:**
```
1. DELETE OLD POSTS
   ├─> Find posts older than 24 hours
   ├─> Delete post directories
   └─> Archive ElevenLabs music files
```

---

## 📊 Timeline Example

```
Day 1 - 00:00 UTC (4 AM PKT)
├─> Timer triggers
├─> Fetch news
├─> Analyze news
├─> Generate 3 posts (score >= 7)
│   ├─> Post 001 (score 8) → Scheduled for 00:20 UTC
│   ├─> Post 002 (score 10) → Scheduled for 13:00 UTC (6 PM PKT)
│   └─> Post 003 (score 7) → Scheduled for 00:20 UTC
└─> Daemon posts Post 001 and 003 at 00:20 UTC

Day 1 - 04:00 UTC (8 AM PKT)
├─> Timer triggers again
├─> Fetch new news
├─> Analyze news
├─> Generate 2 posts
│   ├─> Post 004 (score 9) → Scheduled for 04:20 UTC
│   └─> Post 005 (score 10) → Scheduled for 15:00 UTC (8 PM PKT)
└─> Daemon posts Post 004 at 04:20 UTC

Day 1 - 13:00 UTC (6 PM PKT)
└─> Daemon posts Post 002 (peak time)

Day 1 - 15:00 UTC (8 PM PKT)
└─> Daemon posts Post 005 (peak time)

Day 1 - 23:40 UTC (Next cycle)
└─> Timer triggers again → Repeat process
```

---

## 🛡️ Protection Mechanisms

### 1. Duplicate Prevention (4 Layers)
```
Layer 1: Source Filtering
└─> Filters already-used articles BEFORE OpenAI analysis

Layer 2: Generation Filtering
└─> Checks if news article already used before generating post

Layer 3: Schedule Filtering
└─> Prevents duplicate schedules for same post

Layer 4: Posting Filtering
└─> Triple-checks if already posted before posting
```

### 2. Race Condition Prevention
```
File Locks:
├─> .scheduler_daemon.lock (prevents multiple daemon instances)
└─> .facebook_post.lock (prevents concurrent Facebook posts)

Double-Checks:
└─> Checks is_posted() multiple times with delays
```

### 3. Metadata Protection
```
Merge Instead of Overwrite:
└─> save_metadata() preserves posted_platforms

File Write Delays:
└─> 0.5s delay after posting to ensure file writes flush
```

### 4. Retry Logic
```
YouTube:
├─> Max 5 retries
└─> 1-hour cooldown between attempts

Facebook:
└─> Rate limit handling (marks as done if rate limited)

Instagram:
└─> Single attempt (usually succeeds)
```

---

## 📁 File Structure

```
tripavail_ai/
├── data/
│   ├── raw_news.json              # Raw news from NewsData.io
│   ├── processed_news.json        # News analyzed by OpenAI
│   ├── scheduled_posts.json       # Post schedules
│   └── posts/
│       └── post_XXX/              # Each post gets its own directory
│           ├── metadata.json      # Post metadata
│           ├── images/            # Generated images
│           ├── audio/
│           │   ├── voiceover.mp3  # ElevenLabs TTS
│           │   └── music.mp3      # ElevenLabs Music
│           └── video/
│               └── final.mp4      # Final video
│
├── scripts/
│   ├── run_two_hour_scheduler.py  # Content generation (triggered every 4h)
│   └── scheduler_daemon.py        # Posting daemon (runs continuously)
│
└── core/
    ├── news/                      # News fetching & analysis
    ├── content/                   # Post management & generation
    ├── media/                     # Image, audio, video generation
    └── social/                    # Platform posting logic
```

---

## 🔑 Key Features

### ✅ Fully Automated
- Zero manual intervention required
- Runs 24/7 without supervision

### ✅ Intelligent Scheduling
- Normal posts: 20 minutes after generation
- Peak posts: Optimal engagement times (6/8/9 PM PKT)
- Smart spacing to avoid rate limits

### ✅ Quality Content
- AI-powered analysis ensures tourism relevance
- Story-driven content generation
- Professional video production

### ✅ Multi-Platform
- Simultaneous posting to Instagram, Facebook, YouTube
- Platform-specific optimizations
- Retry logic for reliability

### ✅ Duplicate Prevention
- 4-layer protection system
- Prevents posting same content twice
- Handles race conditions

### ✅ Resource Efficient
- Filters duplicates before expensive API calls
- Auto-cleanup of old files
- Optimized API usage

---

## 📈 Daily Output

**Expected Posts Per Day:**
- **4-hour cycles:** 6 cycles per day
- **Posts per cycle:** 2-5 posts (depending on news quality)
- **Total:** ~12-30 posts per day

**Distribution:**
- Instagram: All posts
- Facebook: All posts
- YouTube: All posts

**Peak Posts:**
- Score 10 posts scheduled at optimal times
- Maximum engagement potential

---

## 🎯 System Goals

1. **Automation:** Zero manual work required
2. **Quality:** AI ensures tourism relevance (score >= 7)
3. **Efficiency:** 4-hour intervals avoid rate limits
4. **Reliability:** Multiple protection layers prevent errors
5. **Scalability:** Handles multiple posts per cycle
6. **Engagement:** Peak-time scheduling for maximum reach

---

## 🔍 Monitoring Commands

```bash
# Check timer status
systemctl status tripavail-fourhour.timer

# Check service status
systemctl status tripavail-fourhour.service

# Check posting daemon
systemctl status tripavail-daemon.service

# View content generation logs
journalctl -u tripavail-fourhour.service -f

# View posting logs
journalctl -u tripavail-daemon.service -f

# Safety check
python scripts/final_comprehensive_verification.py
```

---

## 🚀 How It Works: Simple Summary

1. **Every 4 Hours:** System fetches news, analyzes it, generates posts, and schedules them
2. **Every 60 Seconds:** Posting daemon checks for due posts and publishes them
3. **Daily:** Cleanup system removes old files

**Result:** Fully automated content creation and posting system that runs 24/7 without any manual intervention!


# TripAvail AI - Complete Pipeline Architecture

## 🎯 System Overview

**TripAvail AI** is an automated content creation and social media posting system that:
1. Fetches tourism-related news from NewsData.io
2. Analyzes news for tourism relevance using OpenAI
3. Generates complete social media posts (video, caption, hashtags)
4. Schedules posts at optimal times
5. Automatically posts to Instagram, Facebook, and YouTube

---

## 📋 Active System Components

### 1. **tripavail-fourhour.timer** ⏰
**Purpose:** Triggers news collection and post generation every 4 hours

**Implementation:**
- Systemd timer that runs every 4 hours
- Triggers `tripavail-fourhour.service` when activated
- Persistent (survives reboots)

**File:** `/etc/systemd/system/tripavail-fourhour.timer`

**Schedule:** Every 4 hours (e.g., 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)

---

### 2. **tripavail-fourhour.service** 🔄
**Purpose:** Fetches news, analyzes, generates posts, and schedules them (ALL-IN-ONE)

**Script:** `scripts/run_two_hour_scheduler.py`

**Note:** Script name says "two_hour" but it's triggered every 4 hours to avoid rate limits

**What it does:**
1. **Fetches News** (`NewsFetcher().run_fetch_cycle()`)
   - Connects to NewsData.io API
   - Fetches tourism-related news articles
   - Saves to `data/raw_news.json`
   - Rotates through multiple queries (travel, tourism, flights, hotels, etc.)

2. **Analyzes News** (`TourismEditor().run_analysis()`)
   - Loads raw news articles
   - **FILTERS OUT already-used articles** (prevents duplicates)
   - Sends to OpenAI GPT-4 for tourism relevance scoring
   - Scores each article (1-10 scale)
   - Filters articles with score >= 7
   - Saves to `data/processed_news.json`

3. **Generates Posts** (`ProductionPipeline()`)
   - For each news article (score >= 7):
     - Creates post directory: `data/posts/post_XXX/`
     - Generates story analysis (narrative script, duration, image count)
     - Generates caption and hashtags
     - Generates images (10 images based on story beats)
     - Generates voiceover (ElevenLabs TTS)
     - Generates background music (ElevenLabs Music API)
     - Creates video (combines images, voiceover, music, captions)
     - Generates thumbnail (Gemini AI)
     - Saves metadata to `metadata.json`

4. **Schedules Posts**
   - **Normal posts (score 7-9):** Schedule for 20 minutes after generation
   - **Peak posts (score 10):** Schedule for peak times (6 PM, 8 PM, 9 PM PKT)
   - Saves schedule to `data/scheduled_posts.json`

**File:** `/etc/systemd/system/tripavail-fourhour.service`

**Type:** oneshot (runs once per timer trigger - every 4 hours)

---

### 3. **tripavail-daemon.service** 🤖
**Purpose:** Continuously monitors scheduled posts and posts them when due

**Script:** `scripts/scheduler_daemon.py`

**What it does:**
1. **Checks Schedule** (every 60 seconds)
   - Loads `data/scheduled_posts.json`
   - Finds posts with `status="pending"` and scheduled time <= now
   - **TRIPLE-CHECKS** if post is already posted (prevents duplicates)

2. **Posts to Platforms** (`post_now()`)
   - **Instagram:**
     - Uploads video to Dropbox temporary storage
     - Creates Instagram media container
     - Publishes with caption and hashtags
     - Marks as posted: `pm.mark_as_posted(post_id, "instagram")`

   - **Facebook:**
     - Uses file lock (`.facebook_post.lock`) to prevent race conditions
     - Double-checks if already posted
     - Uploads video with caption and hashtags
     - Marks as posted: `pm.mark_as_posted(post_id, "facebook")`

   - **YouTube:**
     - Checks retry count (max 5 attempts)
     - Checks cooldown period (1 hour between retries)
     - Uploads video as Short with title, description, tags, thumbnail
     - Marks as posted: `pm.mark_as_posted(post_id, "youtube", video_url)`

3. **Mark as Done**
   - If posted to all platforms: `mark_done(post_id)`
   - If YouTube retry limit reached: `mark_done(post_id)`
   - If Facebook rate limited but Instagram posted: `mark_done(post_id)`
   - Otherwise: Keeps schedule active for retries

**File:** `/etc/systemd/system/tripavail-daemon.service`

**Type:** simple (runs continuously)

**Interval:** Checks every 60 seconds

---

### 4. **tripavail-cleanup.timer** 🧹
**Purpose:** Daily cleanup of old post files (24+ hours old)

**Implementation:**
- Runs daily at midnight (00:00 UTC)
- Triggers `tripavail-cleanup.service`
- Deletes post directories older than 24 hours to save disk space

**File:** `/etc/systemd/system/tripavail-cleanup.timer`

---

## 🔄 Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVERY 4 HOURS                                │
│           tripavail-fourhour.timer                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│         tripavail-fourhour.service                              │
│         (scripts/run_two_hour_scheduler.py)                      │
│         ALL-IN-ONE: Fetch + Analyze + Generate + Schedule       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
    ┌──────┐    ┌──────────┐   ┌─────────┐
    │Fetch │───▶│ Analyze  │───▶│Generate│
    │ News │    │  News    │   │ Posts   │
    └──────┘    └──────────┘   └────┬────┘
                    │               │
                    │               ▼
                    │         ┌──────────┐
                    │         │ Schedule │
                    │         │  Posts   │
                    │         └────┬─────┘
                    │              │
                    └──────────────┘
                          │
                          ▼
                data/scheduled_posts.json
                          │
                          │
┌─────────────────────────┼───────────────────────────────────────┐
│           CONTINUOUSLY (every 60 seconds)                       │
│           tripavail-daemon.service                              │
│           (scripts/scheduler_daemon.py)                          │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Check Schedule  │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  Time to post?   │
                └────────┬─────────┘
                         │
                    ┌────┴────┐
                    │   YES   │
                    └────┬────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Triple-check: Already posted? │
        └────────────┬───────────────────┘
                      │
              ┌───────┴───────┐
              │               │
              ▼               ▼
          ┌──────┐      ┌──────────┐
          │ YES  │      │   NO     │
          │ SKIP │      │  POST    │
          └──────┘      └────┬─────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Post to:       │
                    │  • Instagram    │
                    │  • Facebook     │
                    │  • YouTube      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Mark as Done   │
                    │  (if successful)│
                    └─────────────────┘
```

---

## 🛡️ Protection Mechanisms

### 1. **Duplicate Prevention**
- **Source-level:** Filters already-used articles before OpenAI analysis
- **Generation-level:** Checks if news article already used before generating post
- **Schedule-level:** Prevents duplicate schedules for same post
- **Posting-level:** Triple-checks if already posted before posting

### 2. **Race Condition Prevention**
- **File locks:** `.scheduler_daemon.lock` (prevents multiple daemon instances)
- **Facebook lock:** `.facebook_post.lock` (prevents concurrent Facebook posts)
- **Double-checks:** Checks `is_posted()` multiple times with delays

### 3. **Metadata Protection**
- **Merge instead of overwrite:** `save_metadata()` preserves `posted_platforms`
- **File write delays:** 0.5s delay after posting to ensure file writes flush

### 4. **Retry Logic**
- **YouTube:** Max 5 retries with 1-hour cooldown between attempts
- **Facebook:** Rate limit handling (marks as done if rate limited)
- **Instagram:** Single attempt (usually succeeds)

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
│           ├── metadata.json      # Post metadata (caption, hashtags, etc.)
│           ├── images/            # Generated images (10 images)
│           ├── audio/
│           │   ├── voiceover.mp3  # ElevenLabs TTS
│           │   └── music.mp3      # ElevenLabs Music
│           └── video/
│               └── final.mp4      # Final video with captions
│
├── core/
│   ├── news/
│   │   ├── fetcher/
│   │   │   └── fetch_news.py      # NewsData.io API client
│   │   └── editor.py              # OpenAI tourism analyzer
│   ├── content/
│   │   ├── post_manager.py        # Post directory management
│   │   ├── story_analyzer.py      # Story depth analysis
│   │   └── generator/
│   │       └── generate_caption.py # Caption & hashtag generation
│   ├── media/
│   │   ├── images/
│   │   │   └── generator/          # Image generation (Pexels/DALL-E)
│   │   ├── audio/
│   │   │   └── elevenlabs_music.py # Music generation
│   │   └── video/
│   │       └── generator/          # Video assembly
│   └── social/
│       └── platforms/
│           ├── instagram_poster.py
│           ├── facebook_poster.py
│           └── youtube_uploader.py
│
└── scripts/
    ├── scheduler_daemon.py        # Main posting daemon
    └── run_two_hour_scheduler.py  # News fetch + post generation
```

---

## 🔑 Key APIs Used

1. **NewsData.io:** Tourism news fetching
2. **OpenAI GPT-4:** 
   - News analysis (tourism relevance scoring)
   - Story analysis (narrative script, duration, image count)
   - Caption generation
   - Thumbnail prompt generation
3. **ElevenLabs:**
   - Text-to-speech (voiceover)
   - Music generation (background music)
4. **Pexels/Unsplash:** Stock images
5. **Instagram Graph API:** Video posting
6. **Facebook Graph API:** Video posting
7. **YouTube Data API:** Video upload (Shorts)

---

## 📊 Post Generation Process

For each news article (score >= 7):

1. **Story Analysis** (OpenAI)
   - Analyzes story depth
   - Determines video duration (15-60 seconds)
   - Determines image count (8-15 images)
   - Generates narrative script
   - Creates story beats (scene descriptions)

2. **Image Generation**
   - Generates images based on story beats
   - Uses Pexels API (primary) or Unsplash (fallback)
   - Resizes to 1080x1920 (vertical format)

3. **Voiceover Generation**
   - Converts narrative script to speech (ElevenLabs TTS)
   - Premium voice, high quality

4. **Music Generation**
   - Generates 20-second background music (ElevenLabs Music)
   - Matches story mood/tone

5. **Video Assembly**
   - Combines images into video slideshow
   - Syncs voiceover timing
   - Mixes background music
   - Adds text overlays (hook text + captions)
   - Exports final video (1080x1920, 60 FPS)

6. **Thumbnail Generation**
   - Generates AI-powered thumbnail (Gemini)
   - Adds multi-layer text overlay
   - Validates with OCR

---

## ⏰ Scheduling Logic

### Normal Posts (Score 7-9)
- **Schedule:** 20 minutes after generation
- **Platforms:** Instagram, Facebook, YouTube (all at once)

### Peak Posts (Score 10)
- **Schedule:** Peak times (6 PM, 8 PM, 9 PM Pakistan Time)
- **Platforms:** Instagram, Facebook, YouTube
- **Spacing:** 1-hour gap between peak posts

---

## 🎯 System Goals

1. **Automated Content Creation:** Zero manual intervention
2. **Quality Content:** AI-powered analysis ensures tourism relevance
3. **Optimal Timing:** Posts scheduled at peak engagement times
4. **Multi-Platform:** Simultaneous posting to Instagram, Facebook, YouTube
5. **No Duplicates:** Multiple layers of duplicate prevention
6. **Reliable:** Retry logic, error handling, file locks

---

## 🔍 Monitoring

### Check System Status
```bash
systemctl status tripavail-daemon.service
systemctl status tripavail-fourhour.timer
```

### View Logs
```bash
journalctl -u tripavail-daemon.service -f
journalctl -u tripavail-fourhour.service -f
```

### Safety Check
```bash
python scripts/final_comprehensive_verification.py
```

---

## 🚨 Current Status

✅ **Only ONE scheduler running** (`tripavail-daemon.service`)
✅ **No duplicate schedules**
✅ **All protection mechanisms active**
✅ **System ready for production**


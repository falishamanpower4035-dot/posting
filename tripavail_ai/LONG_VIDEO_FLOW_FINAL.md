# 🎬 Long-Format Video System - Final Flow

## 📋 Complete System Overview

### **1. Trend Detection System (OpenAI + pytrends)**
```
┌─────────────────────────────────────────────────┐
│  TREND DETECTION (Every 4 Hours)                │
├─────────────────────────────────────────────────┤
│                                                  │
│  Step 1: Fetch News Articles                    │
│  └─> NewsData.io API                            │
│                                                  │
│  Step 2: OpenAI Analysis                        │
│  └─> Analyze news for trending destinations     │
│  └─> Extract destinations, topics, hashtags     │
│  └─> Score: 0-100                               │
│                                                  │
│  Step 3: pytrends Analysis (NEW)                │
│  └─> Search Google Trends for destinations      │
│  └─> Get interest scores (0-100)                │
│  └─> Get related queries                        │
│                                                  │
│  Step 4: Combine Results                        │
│  └─> Merge OpenAI + pytrends scores             │
│  └─> Weighted average: 60% OpenAI, 40% pytrends │
│  └─> Final trend score: 0-100                   │
│                                                  │
│  Step 5: Store Trending Destinations            │
│  └─> Save to trending_topics.json               │
│  └─> Track new vs existing destinations         │
│                                                  │
└─────────────────────────────────────────────────┘
```

### **2. Short Video Generation (Existing)**
```
┌─────────────────────────────────────────────────┐
│  SHORT VIDEO PIPELINE (Every 4 Hours)           │
├─────────────────────────────────────────────────┤
│                                                  │
│  Format: 9:16 Vertical (1080×1920)              │
│  Duration: 20-45 seconds                        │
│  Images: 6-20 images (vertical/portrait)        │
│  Platforms: Instagram, Facebook, YouTube Shorts │
│                                                  │
│  Flow:                                          │
│  1. Fetch news → Analyze → Generate posts       │
│  2. Generate vertical images (9:16)             │
│  3. Create short video (20-45s)                 │
│  4. Schedule posting                            │
│                                                  │
└─────────────────────────────────────────────────┘
```

### **3. Long Video Generation (NEW)**
```
┌─────────────────────────────────────────────────┐
│  LONG VIDEO PIPELINE (End of Day - 20:00 UTC)   │
├─────────────────────────────────────────────────┤
│                                                  │
│  Format: 16:9 Horizontal (1920×1080)            │
│  Duration: 3-4 minutes (180-240 seconds)        │
│  Images: 60-85 images (horizontal/landscape)    │
│  Platform: YouTube (long format)                │
│                                                  │
│  Trigger: New trending destination detected     │
│  Timing: After last scheduler run (20:00 UTC)   │
│  Resources: Use idle end-of-day resources       │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: TREND DETECTION (Every 4 Hours)                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  1. Fetch News (NewsData.io)          │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  2. OpenAI Analysis                   │
        │     - Analyze news articles           │
        │     - Extract trending destinations   │
        │     - Score: 0-100                    │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  3. pytrends Analysis (NEW)           │
        │     - Search Google Trends            │
        │     - Get interest scores (0-100)     │
        │     - Get related queries             │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  4. Combine Results                   │
        │     - Merge OpenAI + pytrends         │
        │     - Weighted average                │
        │     - Final trend score               │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  5. Store Trending Destinations       │
        │     - Save to trending_topics.json    │
        │     - Track new vs existing           │
        └───────────────────────────────────────┘
                            │
                            ├──────────────────────┐
                            │                      │
                            ▼                      ▼
        ┌───────────────────────────┐  ┌──────────────────────────┐
        │  SHORT VIDEO PATH         │  │  LONG VIDEO PATH         │
        │  (Score >= 7)             │  │  (New Trending Dest)     │
        └───────────────────────────┘  └──────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2A: SHORT VIDEO GENERATION (Every 4 Hours)               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  1. Generate Story Beats              │
        │     - 6-20 story beats                │
        │     - Narrative script                │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  2. Generate Vertical Images (9:16)   │
        │     - Pexels → Unsplash → Shutterstock│
        │     - Orientation: vertical/portrait  │
        │     - Resolution: 1080×1920           │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  3. Create Short Video                │
        │     - Duration: 20-45 seconds         │
        │     - Format: 9:16 vertical           │
        │     - Add voiceover + music           │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  4. Schedule Posting                  │
        │     - Instagram, Facebook, YouTube    │
        │     - Peak times with spacing         │
        └───────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2B: LONG VIDEO GENERATION (End of Day - 20:00 UTC)       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  1. Check for New Trending Destinations│
        │     - Compare with last check         │
        │     - Identify new destinations       │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  2. Check Image Cache (30 days)       │
        │     - If cached → Use cached images   │
        │     - If not cached → Search images   │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  3. Search Horizontal Images (16:9)   │
        │     - Distributed search:             │
        │       • Attractions → Pexels          │
        │       • Activities → Unsplash         │
        │       • Food/Culture → Pexels         │
        │       • Local Life → Unsplash         │
        │       • Scenic Views → Shutterstock   │
        │     - Orientation: horizontal/landscape│
        │     - Resolution: 1920×1080           │
        │     - Total: 60-85 images             │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  4. Validate Images                   │
        │     - Check orientation (16:9)        │
        │     - Verify aspect ratio (1.6-1.8)   │
        │     - Check resolution (≥1920×1080)   │
        │     - Filter duplicates               │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  5. Cache Images (30 days)            │
        │     - Save to destination folder      │
        │     - Store metadata                  │
        │     - Track expiration                │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  6. Generate Catchy Title             │
        │     - Use OpenAI to generate          │
        │     - Include destination name        │
        │     - Optimize for YouTube SEO        │
        │     - Word-boundary truncation (60-70)│
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  7. Create Long Video                 │
        │     - Duration: 3-4 minutes           │
        │     - Format: 16:9 horizontal         │
        │     - 60-85 images with transitions   │
        │     - Add voiceover + music           │
        │     - Add captions + overlays         │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  8. Upload to YouTube                 │
        │     - Use catchy title                │
        │     - Add description + tags          │
        │     - Schedule or publish             │
        └───────────────────────────────────────┘
```

---

## 📊 Key Specifications

### **Short Videos (Existing)**
- **Format**: 9:16 Vertical (1080×1920)
- **Duration**: 20-45 seconds
- **Images**: 6-20 images (vertical/portrait)
- **Image Duration**: 3.5 seconds per image
- **Platforms**: Instagram, Facebook, YouTube Shorts
- **Schedule**: Every 4 hours (6 times/day)
- **Priority**: High (score >= 7)

### **Long Videos (NEW)**
- **Format**: 16:9 Horizontal (1920×1080)
- **Duration**: 3-4 minutes (180-240 seconds)
- **Images**: 60-85 images (horizontal/landscape)
- **Image Duration**: Variable (hero: 5s, standard: 3.5s, quick: 2.5s)
- **Platform**: YouTube (long format)
- **Schedule**: End of day (20:00 UTC) when trending destination detected
- **Priority**: Normal (on-demand)

---

## 🔍 Trend Detection Details

### **OpenAI Analysis**
- **Input**: News articles from NewsData.io
- **Output**: Trending destinations with scores (0-100)
- **Method**: GPT-4 analysis of news content
- **Factors**: Frequency, attention, viral potential

### **pytrends Analysis (NEW)**
- **Input**: Destination keywords
- **Output**: Google Trends interest scores (0-100)
- **Method**: Google Trends data scraping
- **Factors**: Search interest, related queries, regional trends

### **Combined Scoring**
- **Formula**: `Final Score = (OpenAI Score × 0.6) + (pytrends Score × 0.4)`
- **Threshold**: Score >= 7 for short videos
- **Long Videos**: New trending destinations only

---

## 🖼️ Image Search Strategy

### **Short Videos (9:16 Vertical)**
- **Orientation**: vertical/portrait
- **Aspect Ratio**: 9:16 (0.56)
- **Resolution**: 1080×1920
- **Services**: Pexels → Unsplash → Shutterstock
- **Fallback**: AI generation (if stock fails)

### **Long Videos (16:9 Horizontal)**
- **Orientation**: horizontal/landscape
- **Aspect Ratio**: 16:9 (1.78)
- **Resolution**: 1920×1080
- **Services**: Distributed search across services
- **Fallback**: Wait and retry (NO AI generation)

### **Search Distribution (Long Videos)**
```
Category          │ Service      │ Orientation  │ Images
──────────────────┼──────────────┼──────────────┼────────
Attractions       │ Pexels       │ horizontal   │ 15-20
Activities        │ Unsplash     │ horizontal   │ 15-20
Food & Culture    │ Pexels       │ horizontal   │ 10-15
Local Life        │ Unsplash     │ horizontal   │ 10-15
Scenic Views      │ Shutterstock │ horizontal   │ 10-15
──────────────────┴──────────────┴──────────────┴────────
Total: 60-85 images
```

### **Image Validation (Long Videos)**
- **Orientation**: Must be horizontal/landscape
- **Aspect Ratio**: 1.6 - 1.8 (16:9 range)
- **Resolution**: Minimum 1920×1080
- **Quality**: High resolution, no watermarks
- **Duplicates**: Filter duplicate images

### **Image Caching**
- **Duration**: 30 days
- **Structure**: `data/image_cache/{destination_name}/`
- **Categories**: Separate folders for each category
- **Metadata**: Cache creation date, expiration, image count

---

## ⚙️ Error Handling & Retry Logic

### **Image Search Failures**
- **Strategy**: Wait and retry (NO AI fallback)
- **Retry Attempts**: 3 attempts
- **Wait Period**: 24 hours between attempts
- **Service Rotation**: Rotate services on retry
- **Query Variation**: Try alternative queries

### **Rate Limiting**
- **Pexels**: 200 requests/day
- **Unsplash**: 50 requests/day
- **Shutterstock**: Varies by plan
- **Strategy**: Distribute searches across services
- **Wait Period**: 10 seconds between searches

### **Resource Management**
- **Check Resources**: Before starting video generation
- **CPU Usage**: < 70%
- **Memory**: < 80%
- **Disk Space**: > 5GB free
- **FileLock**: Prevent concurrent video generation

---

## 📅 Scheduling

### **Short Videos**
- **Frequency**: Every 4 hours (6 times/day)
- **Times**: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
- **Priority**: High (score >= 7)
- **Platforms**: Instagram, Facebook, YouTube Shorts

### **Long Videos**
- **Frequency**: On-demand (when trending destination detected)
- **Timing**: End of day (20:00 UTC) after last scheduler run
- **Priority**: Normal
- **Platform**: YouTube (long format)
- **Resources**: Use idle end-of-day resources

---

## 🎯 Final System Flow Summary

1. **Trend Detection** (Every 4 hours)
   - Fetch news → OpenAI analysis → pytrends analysis → Combine results
   - Store trending destinations

2. **Short Video Generation** (Every 4 hours)
   - Generate vertical images (9:16)
   - Create short video (20-45s)
   - Schedule posting

3. **Long Video Generation** (End of day - 20:00 UTC)
   - Check for new trending destinations
   - Search horizontal images (16:9)
   - Cache images (30 days)
   - Create long video (3-4 min)
   - Upload to YouTube

---

## ✅ Confirmed Specifications

- ✅ **Trend Detection**: OpenAI + pytrends
- ✅ **Short Videos**: 9:16 vertical, 20-45s, 6-20 images
- ✅ **Long Videos**: 16:9 horizontal, 3-4 min, 60-85 images
- ✅ **Image Search**: Pexels, Unsplash, Shutterstock (distributed)
- ✅ **Image Caching**: 30-day destination-based cache
- ✅ **No AI Fallback**: Wait and retry for long videos
- ✅ **Scheduling**: 4-hour cycles for short, end-of-day for long
- ✅ **Resource Management**: Use idle end-of-day resources

---

**Status**: ✅ **FINAL FLOW CONFIRMED**


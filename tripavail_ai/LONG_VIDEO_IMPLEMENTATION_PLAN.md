# 🎬 Long Video System - Step-by-Step Implementation Plan

## 📋 System Overview

### **Key Points:**
- ✅ **Completely separate** from short video system
- ✅ **Naming convention**: All files/components use "Long" suffix
- ✅ **Timing**: End of day (20:00 UTC) for trend detection
- ✅ **Independent**: Short video system continues unchanged
- ✅ **Learning**: Use existing components as reference, but create new ones

---

## 🎯 Complete Component List

### **1. Trend Detection System** ✅
- **File**: `core/content/intelligence/trending_detector_long.py`
- **Function**: Detect trending destinations (OpenAI + pytrends)
- **Timing**: End of day (20:00 UTC)
- **Output**: Trending destinations with scores

### **2. Destination Script Generator** ⚠️ MISSING
- **File**: `core/content/script_generator_long.py`
- **Function**: Generate 3-4 minute voiceover script for destination
- **Input**: Destination name, trend data, images
- **Output**: Complete narrative script (300-400 words)

### **3. Image Search System** ⚠️ MISSING
- **File**: `core/media/images/generator/destination_image_generator_long.py`
- **Function**: Search horizontal images (16:9) for destinations
- **Services**: Pexels, Unsplash, Shutterstock (distributed)
- **Output**: 60-85 horizontal images per destination
- **Caching**: 30-day destination-based cache

### **4. Voiceover Generator** ⚠️ MISSING
- **File**: `core/media/audio/voiceover_generator_long.py`
- **Function**: Generate voiceover using ElevenLabs
- **API Key**: `ArF6APsmGwM8GvJpglJ6` (provided)
- **Input**: Script from script generator
- **Output**: Audio file (3-4 minutes)

### **5. Caption Generator** ⚠️ MISSING
- **File**: `core/media/video/generator/caption_generator_long.py`
- **Function**: Generate captions synced with voiceover
- **Input**: Voiceover script, audio duration
- **Output**: Caption file with timestamps

### **6. Hook Generator** ⚠️ MISSING
- **File**: `core/content/hook_generator_long.py`
- **Function**: Generate catchy hook for YouTube video
- **Input**: Destination name, trend data
- **Output**: Hook text (60-70 characters)

### **7. Thumbnail Generator** ⚠️ MISSING
- **File**: `core/media/images/generator/thumbnail_generator_long.py`
- **Function**: Generate thumbnail with consistent character
- **Requirement**: Same person in every thumbnail
- **Format**: 16:9 horizontal (1920×1080)
- **Input**: Destination name, hook text

### **8. Video Generator** ⚠️ MISSING
- **File**: `core/media/video/generator/youtube_long_video_generator.py`
- **Function**: Create 3-4 minute video (16:9)
- **Input**: Images, voiceover, captions, hook
- **Output**: Final video file (1920×1080, 3-4 min)

### **9. Audio Mixer** ⚠️ MISSING
- **File**: `core/media/audio/audio_mixer_long.py`
- **Function**: Mix voiceover with background music
- **Input**: Voiceover, background music
- **Output**: Mixed audio file

### **10. Production Pipeline** ⚠️ MISSING
- **File**: `production_pipeline_long.py`
- **Function**: Orchestrate entire long video generation
- **Timing**: End of day (20:00 UTC)
- **Trigger**: New trending destination detected

### **11. Scheduler Integration** ⚠️ MISSING
- **File**: `scripts/run_long_video_generator.py`
- **Function**: Run long video generation at end of day
- **Timing**: 20:00 UTC (after last scheduler run)
- **Integration**: Check for trending destinations

---

## 📝 Step-by-Step Implementation

### **PHASE 1: Setup & Configuration** 🔧

#### **Step 1.1: Create Configuration**
- **File**: `config/settings_long.py`
- **Content**:
  - Long video settings (duration, format, image count)
  - ElevenLabs API key configuration
  - Image cache settings
  - Thumbnail character settings

#### **Step 1.2: Update Environment Template**
- **File**: `env_template.txt`
- **Add**:
  - `ELEVENLABS_API_KEY_LONG=ArF6APsmGwM8GvJpglJ6`
  - `LONG_VIDEO_ENABLED=true`
  - `LONG_VIDEO_GENERATION_TIME=20:00`

#### **Step 1.3: Install Dependencies**
- **Package**: `pytrends`
- **Command**: `pip install pytrends`

---

### **PHASE 2: Trend Detection System** 🔍

#### **Step 2.1: Enhance Trending Detector**
- **File**: `core/content/intelligence/trending_detector_long.py`
- **Features**:
  - Integrate pytrends for Google Trends data
  - Combine OpenAI + pytrends scores
  - Detect new trending destinations
  - Store trending destinations
- **Timing**: Every **12 hours** (not 4 hours) - trends don't change that often
- **Schedule**: `08:00 UTC` and `20:00 UTC`

#### **Step 2.2: Create Trend Detection Script**
- **File**: `scripts/detect_trending_destinations_long.py`
- **Function**: Run trend detection every 12 hours
- **Timing**: `08:00 UTC` and `20:00 UTC`
- **Output**: List of new trending destinations

---

### **PHASE 3: Image Search System** 🖼️

#### **Step 3.1: Create Destination Image Generator**
- **File**: `core/media/images/generator/destination_image_generator_long.py`
- **Features**:
  - Search horizontal images (16:9) only
  - Distributed search across services
  - Image caching (30 days)
  - Validation (aspect ratio, resolution)
  - No AI fallback (wait and retry)
- **API Keys**: 
  - **Pexels**: `PEXELS_API_KEY_LONG` - **ONLY for long videos** (separate from short videos)
  - **Unsplash**: `UNSPLASH_ACCESS_KEY_LONG`, `UNSPLASH_SECRET_KEY_LONG`, `UNSPLASH_APP_ID_LONG`
  - **Shutterstock**: Uses same key as short videos (or separate if configured)
- **Important**: Pexels key is ONLY used for long videos. Short videos use `PEXELS_API_KEY`.

#### **Step 3.2: Create Image Cache Manager**
- **File**: `core/media/images/cache_manager_long.py`
- **Features**:
  - 30-day destination-based cache
  - Category-based organization
  - Cache validation and cleanup
  - Metadata tracking

#### **Step 3.3: Create Image Search Distribution**
- **Strategy**:
  - Attractions → Pexels
  - Activities → Unsplash
  - Food/Culture → Pexels
  - Local Life → Unsplash
  - Scenic Views → Shutterstock

---

### **PHASE 4: Script Generation** 📝

#### **Step 4.1: Create Destination Script Generator**
- **File**: `core/content/script_generator_long.py`
- **Features**:
  - Generate 3-4 minute script (300-400 words)
  - Structure: Introduction → Main Content → Conclusion
  - Include destination highlights
  - Narrative style (storytelling)
  - Optimize for voiceover pacing

#### **Step 4.2: Integrate with Image Data**
- **Function**: Use image categories to structure script
- **Example**:
  - Introduction (attractions)
  - Main content (activities, food, local life)
  - Conclusion (scenic views)

---

### **PHASE 5: Voiceover Generation** 🎙️

#### **Step 5.1: Create Voiceover Generator**
- **File**: `core/media/audio/voiceover_generator_long.py`
- **Features**:
  - Use ElevenLabs API
  - API Key: `ArF6APsmGwM8GvJpglJ6`
  - Generate 3-4 minute audio
  - Voice selection (consistent voice)
  - Quality settings (premium)

#### **Step 5.2: Voice Selection**
- **Strategy**: Use same voice for all long videos
- **Voice ID**: Select from ElevenLabs voices
- **Settings**: Premium quality, natural pacing

#### **Step 5.3: Audio Processing**
- **Function**: Ensure audio matches video duration
- **Format**: MP3, high quality
- **Duration**: 3-4 minutes (180-240 seconds)

---

### **PHASE 6: Caption Generation** 📺

#### **Step 6.1: Create Caption Generator**
- **File**: `core/media/video/generator/caption_generator_long.py`
- **Features**:
  - Generate captions from script
  - Sync with voiceover timing
  - Word-level timing
  - Format: SRT or VTT
  - Styling: Professional, readable

#### **Step 6.2: Caption Styling**
- **Style**: White text, black outline
- **Position**: Bottom center
- **Font**: Large, readable
- **Timing**: Word-level synchronization

---

### **PHASE 7: Hook Generation** 🎣

#### **Step 7.1: Create Hook Generator**
- **File**: `core/content/hook_generator_long.py`
- **Features**:
  - Generate catchy YouTube title/hook
  - Length: 60-70 characters
  - Word-boundary aware truncation
  - SEO optimized
  - Include destination name

#### **Step 7.2: Hook Examples**
- "Bali: The Ultimate 4-Minute Travel Guide 2025"
- "Why Everyone's Traveling to Thailand Right Now"
- "Japan Uncovered: Attractions, Culture & Hidden Gems"

---

### **PHASE 8: Thumbnail Generation** 🖼️

#### **Step 8.1: Create Thumbnail Generator**
- **File**: `core/media/images/generator/thumbnail_generator_long.py`
- **Features**:
  - Generate 16:9 horizontal thumbnail
  - Include consistent character (same person)
  - Destination background
  - Hook text overlay
  - Professional design

#### **Step 8.2: Character Consistency**
- **Strategy**: Use same character/person in all thumbnails
- **Implementation**: 
  - Create character reference image
  - Use AI to generate character in different scenes
  - Maintain consistent appearance
  - Position: Center or side of thumbnail

#### **Step 8.3: Thumbnail Design**
- **Format**: 16:9 (1920×1080)
- **Elements**: Character + Destination + Hook text
- **Style**: Eye-catching, professional
- **Text**: Hook text overlay

---

### **PHASE 9: Video Generation** 🎬

#### **Step 9.1: Create Video Generator**
- **File**: `core/media/video/generator/youtube_long_video_generator.py`
- **Features**:
  - Create 3-4 minute video (16:9)
  - 60-85 images with transitions
  - Variable image durations
  - Ken Burns effect
  - Crossfade transitions

#### **Step 9.2: Video Settings**
- **Resolution**: 1920×1080 (Full HD)
- **Frame Rate**: 30 FPS
- **Format**: MP4 (H.264)
- **Duration**: 3-4 minutes (180-240 seconds)
- **Aspect Ratio**: 16:9 horizontal

#### **Step 9.3: Image Timing**
- **Hero shots**: 5-6 seconds
- **Key moments**: 4-4.5 seconds
- **Supporting scenes**: 3-3.5 seconds
- **Quick transitions**: 2.5-3 seconds

#### **Step 9.4: Add Elements**
- **Voiceover**: Sync with images
- **Captions**: Overlay on video
- **Hook text**: Display at beginning
- **Background music**: Mix with voiceover
- **Transitions**: Smooth crossfades

---

### **PHASE 10: Audio Mixing** 🎵

#### **Step 10.1: Create Audio Mixer**
- **File**: `core/media/audio/audio_mixer_long.py`
- **Features**:
  - Mix voiceover with background music
  - Adjust volume levels
  - Sync with video duration
  - Quality: High (320kbps)

#### **Step 10.2: Music Selection**
- **Strategy**: Use archived music (no generation)
- **Style**: Travel-themed, ambient
- **Volume**: Lower than voiceover
- **Duration**: Match video length

---

### **PHASE 11: Production Pipeline** 🏭

#### **Step 11.1: Create Production Pipeline**
- **File**: `production_pipeline_long.py`
- **Features**:
  - Orchestrate entire long video generation
  - Check for trending destinations
  - Generate images, script, voiceover
  - Create video, thumbnail, captions
  - Upload to YouTube

#### **Step 11.2: Pipeline Flow**
```
1. Check trending destinations
2. Generate images (or use cache)
3. Generate script
4. Generate voiceover
5. Generate captions
6. Generate hook
7. Generate thumbnail
8. Create video
9. Mix audio
10. Upload to YouTube
```

---

### **PHASE 12: Scheduler Integration** ⏰

#### **Step 12.1: Create Scheduler Script**
- **File**: `scripts/run_long_video_generator.py`
- **Features**:
  - Run at end of day (20:00 UTC)
  - Check for trending destinations
  - Trigger video generation
  - Log results

#### **Step 12.2: Integration with Existing Scheduler**
- **Strategy**: Run after last scheduler run
- **Timing**: 20:00 UTC
- **Condition**: New trending destination detected
- **Resources**: Use idle end-of-day resources

---

### **PHASE 13: YouTube Upload** 📤

#### **Step 13.1: Create YouTube Uploader**
- **File**: `core/social/platforms/youtube_uploader_long.py`
- **Features**:
  - Upload long videos to YouTube
  - Use catchy title (hook)
  - Add description + tags
  - Set thumbnail
  - Schedule or publish immediately

#### **Step 13.2: Video Metadata**
- **Title**: Hook text (60-70 characters)
- **Description**: Destination information + links
- **Tags**: Destination, travel, tourism keywords
- **Category**: Travel & Events
- **Thumbnail**: Generated thumbnail

---

## 📊 File Structure

```
tripavail_ai/
├── config/
│   └── settings_long.py                    # Long video configuration
├── core/
│   ├── content/
│   │   ├── intelligence/
│   │   │   └── trending_detector_long.py   # Trend detection (OpenAI + pytrends)
│   │   ├── script_generator_long.py        # Script generation
│   │   └── hook_generator_long.py          # Hook generation
│   ├── media/
│   │   ├── images/
│   │   │   ├── generator/
│   │   │   │   ├── destination_image_generator_long.py  # Image search
│   │   │   │   └── thumbnail_generator_long.py          # Thumbnail generation
│   │   │   └── cache_manager_long.py       # Image cache management
│   │   ├── audio/
│   │   │   ├── voiceover_generator_long.py # Voiceover generation
│   │   │   └── audio_mixer_long.py         # Audio mixing
│   │   └── video/
│   │       └── generator/
│   │           ├── youtube_long_video_generator.py  # Video generation
│   │           └── caption_generator_long.py        # Caption generation
│   └── social/
│       └── platforms/
│           └── youtube_uploader_long.py    # YouTube upload
├── scripts/
│   ├── detect_trending_destinations_long.py  # Trend detection script
│   └── run_long_video_generator.py          # Main scheduler script
├── production_pipeline_long.py              # Production pipeline
└── data/
    └── long_videos/
        ├── destinations/                    # Destination data
        ├── images/                          # Cached images
        ├── scripts/                         # Generated scripts
        ├── voiceovers/                      # Voiceover audio
        ├── videos/                          # Generated videos
        └── thumbnails/                      # Thumbnails
```

---

## 🎯 Implementation Order

### **Week 1: Foundation**
1. ✅ Phase 1: Setup & Configuration
2. ✅ Phase 2: Trend Detection System
3. ✅ Phase 3: Image Search System

### **Week 2: Content Generation**
4. ✅ Phase 4: Script Generation
5. ✅ Phase 5: Voiceover Generation
6. ✅ Phase 6: Caption Generation
7. ✅ Phase 7: Hook Generation

### **Week 3: Video Production**
8. ✅ Phase 8: Thumbnail Generation
9. ✅ Phase 9: Video Generation
10. ✅ Phase 10: Audio Mixing

### **Week 4: Integration & Testing**
11. ✅ Phase 11: Production Pipeline
12. ✅ Phase 12: Scheduler Integration
13. ✅ Phase 13: YouTube Upload

---

## 🔍 Missing Components Checklist

### **Core Components** ✅
- [x] Trend Detection (OpenAI + pytrends)
- [ ] Destination Script Generator
- [ ] Image Search System (16:9 horizontal)
- [ ] Voiceover Generator (ElevenLabs)
- [ ] Caption Generator
- [ ] Hook Generator
- [ ] Thumbnail Generator (with consistent character)
- [ ] Video Generator (16:9, 3-4 min)
- [ ] Audio Mixer
- [ ] Production Pipeline
- [ ] Scheduler Integration
- [ ] YouTube Upload

### **Supporting Components** ✅
- [ ] Image Cache Manager
- [ ] Configuration File
- [ ] Environment Variables
- [ ] Logging System
- [ ] Error Handling
- [ ] Retry Logic

---

## 🚀 Next Steps

1. **Start with Phase 1**: Setup & Configuration
2. **Implement Phase 2**: Trend Detection System
3. **Build Phase 3**: Image Search System
4. **Continue with remaining phases** in order

---

## ✅ Final Checklist

- [x] System is completely separate from short videos
- [x] All files use "Long" suffix
- [x] Trend detection at end of day (20:00 UTC)
- [x] All missing components identified
- [x] Step-by-step implementation plan created
- [x] File structure defined
- [x] Implementation order established

---

**Status**: ✅ **READY FOR IMPLEMENTATION**


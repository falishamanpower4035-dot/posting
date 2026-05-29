# 🔑 Long Video System - Configuration Summary

## ✅ API Keys & Credentials

### **Pexels API (Long Videos Only)**
- **API Key**: `WaaZwYKSLwrBEnvVNXcWLBvWZS48auiNghb34tQE2sufUGa5GQ9bpg4X`
- **Usage**: **ONLY for long videos** (separate from short videos)
- **Environment Variable**: `PEXELS_API_KEY_LONG`
- **Note**: Short videos continue to use `PEXELS_API_KEY` from existing config

### **Unsplash API (Long Videos)**
- **Application ID**: `829529`
- **Access Key**: `OSlM5giq8LVThEDf1HcTsLvo59tZl0BywfUpXxkcksI`
- **Secret Key**: `4_T4Wem3tnqyE6DIRMZnk2pKxcHV-0mc5OvIiQgyCRI`
- **Environment Variables**: 
  - `UNSPLASH_APP_ID_LONG=829529`
  - `UNSPLASH_ACCESS_KEY_LONG=OSlM5giq8LVThEDf1HcTsLvo59tZl0BywfUpXxkcksI`
  - `UNSPLASH_SECRET_KEY_LONG=4_T4Wem3tnqyE6DIRMZnk2pKxcHV-0mc5OvIiQgyCRI`
- **Note**: Unsplash uses Access Key for API requests (not App ID)

### **ElevenLabs API (Long Videos)**
- **API Key**: `ArF6APsmGwM8GvJpglJ6`
- **Environment Variable**: `ELEVENLABS_API_KEY_LONG`
- **Usage**: Voiceover generation for long videos

### **Shutterstock API (Long Videos)**
- **Usage**: Same as short videos (or separate if configured)
- **Environment Variables**: 
  - `SHUTTERSTOCK_ACCESS_TOKEN_LONG` (optional, falls back to regular token)
  - `SHUTTERSTOCK_CLIENT_ID_LONG` (optional)
  - `SHUTTERSTOCK_CLIENT_SECRET_LONG` (optional)

---

## ⏰ Timing & Scheduling

### **Trend Detection**
- **Interval**: Every **12 hours** (not 4 hours)
- **Times**: `08:00 UTC` and `20:00 UTC`
- **Reason**: Trends don't change that often, so 12-hour interval is sufficient
- **Environment Variable**: `TRENDING_DETECTION_TIME=08:00,20:00`

### **Video Generation**
- **Timing**: After trend detection (when new destination detected)
- **Default Time**: `20:00 UTC` (end of day)
- **Environment Variable**: `LONG_VIDEO_GENERATION_TIME=20:00`

---

## 🖼️ Image Search Strategy

### **Service Distribution**
- **Attractions**: Pexels (long videos only)
- **Activities**: Unsplash (long videos)
- **Food & Culture**: Pexels (long videos only)
- **Local Life**: Unsplash (long videos)
- **Scenic Views**: Shutterstock

### **Key Points**
- ✅ **Pexels is ONLY used for long videos** (separate API key)
- ✅ Short videos continue to use existing Pexels key
- ✅ Long videos use separate Unsplash credentials
- ✅ Distributed search to avoid duplicates
- ✅ Horizontal/landscape images only (16:9)

---

## 📁 Configuration Files

### **Main Configuration**
- **File**: `config/settings_long.py`
- **Purpose**: All long video system settings
- **Includes**: API keys, timing, image search, video settings

### **Environment Variables**
- **File**: `.env` (or `env_template.txt`)
- **Added Variables**:
  ```
  PEXELS_API_KEY_LONG=WaaZwYKSLwrBEnvVNXcWLBvWZS48auiNghb34tQE2sufUGa5GQ9bpg4X
  UNSPLASH_APP_ID_LONG=829529
  UNSPLASH_ACCESS_KEY_LONG=OSlM5giq8LVThEDf1HcTsLvo59tZl0BywfUpXxkcksI
  UNSPLASH_SECRET_KEY_LONG=4_T4Wem3tnqyE6DIRMZnk2pKxcHV-0mc5OvIiQgyCRI
  ELEVENLABS_API_KEY_LONG=ArF6APsmGwM8GvJpglJ6
  LONG_VIDEO_ENABLED=true
  LONG_VIDEO_GENERATION_TIME=20:00
  TRENDING_DETECTION_INTERVAL_HOURS=12
  TRENDING_DETECTION_TIME=08:00,20:00
  ```

---

## ✅ Validation Checklist

### **API Keys** ✅
- [x] Pexels API key for long videos configured
- [x] Unsplash credentials for long videos configured
- [x] ElevenLabs API key for long videos configured
- [x] Shutterstock API key (shared or separate)

### **Timing** ✅
- [x] Trend detection: 12-hour interval (08:00, 20:00 UTC)
- [x] Video generation: After trend detection
- [x] No conflict with short video system

### **Image Search** ✅
- [x] Pexels ONLY for long videos (separate key)
- [x] Unsplash for long videos (separate credentials)
- [x] Distributed search strategy
- [x] Horizontal/landscape images only

### **System Independence** ✅
- [x] Separate configuration file
- [x] Separate API keys
- [x] Separate directory structure
- [x] No mixing with short video system

---

## 🚀 Next Steps

1. ✅ **Configuration Created**: `config/settings_long.py`
2. ✅ **Environment Variables Updated**: `env_template.txt`
3. ⏳ **Implementation**: Start building components
4. ⏳ **Testing**: Test with sample destination
5. ⏳ **Deployment**: Deploy to production

---

## 📝 Important Notes

### **Pexels API Key**
- ⚠️ **CRITICAL**: Pexels key is **ONLY for long videos**
- ✅ Short videos continue to use existing `PEXELS_API_KEY`
- ✅ Long videos use `PEXELS_API_KEY_LONG`
- ✅ No mixing of keys between systems

### **Trend Detection**
- ⚠️ **CHANGED**: Every 12 hours (not 4 hours)
- ✅ Times: 08:00 UTC and 20:00 UTC
- ✅ Reason: Trends don't change that often

### **System Independence**
- ✅ Completely separate from short video system
- ✅ All files use "Long" suffix
- ✅ Separate API keys and credentials
- ✅ No mixing of systems

---

**Status**: ✅ **CONFIGURATION COMPLETE**


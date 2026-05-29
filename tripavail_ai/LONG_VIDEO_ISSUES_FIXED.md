# Long Video Issues - Fixes Applied

## 🐛 Issues Identified

### 1. Only 2-3 Images in Video ❌
- **Problem**: The video only uses 2-3 images, which are repeated throughout
- **Root Cause**: 
  - Image selection logic limited to 3 images per scene
  - Images were not properly distributed across scenes
  - Same images were being reused multiple times

### 2. No Audio in Video ❌
- **Problem**: The video has no audio (no voiceover, no background music)
- **Root Cause**:
  - FFmpeg command had bugs in audio insertion
  - Mixed audio files were deleted before video assembly
  - Audio path was not properly passed to video assembler

### 3. No Background Music ❌
- **Problem**: Background music is not being mixed with voiceover
- **Root Cause**:
  - Music files might not be found in expected directories
  - Audio mixer might be failing silently
  - Music mixing logic might have issues

### 4. Images Repeating ❌
- **Problem**: The same 2-3 images are shown repeatedly throughout the video
- **Root Cause**:
  - Not enough images being selected per scene
  - Images were not properly distributed
  - Image selection logic was too restrictive

## ✅ Fixes Applied

### 1. Fixed Image Distribution ✅
- **Before**: Only 3 images per scene, same images repeated
- **After**: 
  - Collect ALL images from ALL categories for the destination
  - Distribute 8-10 images per scene
  - Map scene categories to image categories properly
  - Ensure no duplicate images within a scene

**Changes Made**:
- Modified `assemble_day_video` to collect all destination images first
- Redistribute images evenly across scenes (8-10 images per scene)
- Map scene categories to image categories for better matching
- Track used images to avoid duplicates

### 2. Fixed Audio Addition ✅
- **Before**: FFmpeg command had bugs, audio not properly added
- **After**: 
  - Fixed FFmpeg command to properly add audio
  - Use `-map 0:v:0 -map 1:a:0` to map video and audio
  - Use `-shortest` to match video duration to audio
  - Properly check if audio file exists before adding

**Changes Made**:
- Fixed FFmpeg command structure
- Properly map audio and video streams
- Check audio file existence before adding
- Use voiceover duration to adjust video duration

### 3. Fixed Image Duration Calculation ✅
- **Before**: Fixed durations per image (5 seconds)
- **After**: 
  - Calculate image durations based on voiceover length
  - Distribute voiceover duration across images
  - Minimum 2 seconds, maximum 8 seconds per image
  - Dynamic duration based on scene length

**Changes Made**:
- Get voiceover duration before calculating image durations
- Distribute voiceover duration across scenes proportionally
- Calculate image duration based on scene duration and image count
- Ensure minimum/maximum durations per image

### 4. Fixed Image Selection ✅
- **Before**: Only 3 images per scene, limited selection
- **After**: 
  - Collect all images from all categories
  - Map scene categories to image categories
  - Select 8-10 images per scene
  - Avoid duplicates within scenes

**Changes Made**:
- Modified `_find_scene_images` to return all unique images
- Collect images from all categories for destination
- Map scene categories to image categories
- Distribute images evenly across scenes

## 📝 Code Changes

### `core/media/video/generator/day_video_assembler_long.py`

1. **Image Collection**:
   - Collect ALL images from ALL categories for destination
   - Remove duplicates while preserving order
   - Map scene categories to image categories
   - Distribute 8-10 images per scene

2. **Image Duration Calculation**:
   - Get voiceover duration first
   - Distribute voiceover duration across scenes
   - Calculate image duration based on scene duration and image count
   - Ensure minimum 2s, maximum 8s per image

3. **FFmpeg Command**:
   - Fixed audio input insertion
   - Properly map video and audio streams
   - Use `-shortest` to match durations
   - Check audio file existence before adding

### `core/media/audio/audio_mixer_long.py`

1. **Music File Search**:
   - Check multiple music directories
   - Look for `.mp3` and `.wav` files
   - Randomly select a music file
   - Loop music if duration is shorter than required

2. **Audio Mixing**:
   - Mix voiceover and background music
   - Apply volume control (voiceover 1.0, music 0.3)
   - Apply fade in/out effects
   - Save mixed audio to `temp_mixed` directory

## 🚀 Next Steps

### 1. Test Image Distribution
- Verify that 8-10 images are used per scene
- Check that images are not repeating
- Ensure images match scene categories

### 2. Test Audio
- Verify that voiceover is added to video
- Check that background music is mixed
- Ensure audio duration matches video duration

### 3. Test Full Pipeline
- Run full pipeline test
- Check video output
- Verify audio quality
- Check image variety

### 4. Fix Background Music
- Verify music files exist in expected directories
- Check music file paths
- Test music mixing functionality
- Ensure music is properly looped if needed

## 🔍 Debugging Steps

### 1. Check Image Count
```bash
# Count images in destination directory
Get-ChildItem -Path "data\long_videos\images\Bali" -Recurse -Filter "*.jpg" | Measure-Object
```

### 2. Check Audio Files
```bash
# Check voiceover files
Get-ChildItem -Path "data\long_videos\voiceovers" -Filter "*.mp3"

# Check mixed audio files
Get-ChildItem -Path "data\long_videos\voiceovers\temp_mixed" -Filter "*.mp3"
```

### 3. Check Music Files
```bash
# Check music directories
Get-ChildItem -Path "assets\audio" -Filter "*.mp3"
Get-ChildItem -Path "data\audio\music" -Filter "*.mp3"
Get-ChildItem -Path "assets\music" -Filter "*.mp3"
```

### 4. Test Video Output
```bash
# Check video file
ffprobe -v error -show_entries stream=codec_type,codec_name,duration -of json "data\long_videos\videos\Bali_final_video.mp4"

# Check audio stream
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,duration -of json "data\long_videos\videos\Bali_final_video.mp4"
```

## 📊 Expected Results

### Before Fixes ❌
- **Images**: 2-3 images, repeating
- **Audio**: No audio
- **Music**: No background music
- **Duration**: Fixed 5 seconds per image

### After Fixes ✅
- **Images**: 8-10 images per scene, no repeats
- **Audio**: Voiceover + background music
- **Music**: Properly mixed with voiceover
- **Duration**: Dynamic based on voiceover length

## 🎯 Testing

### 1. Run Full Pipeline Test
```bash
python scripts/test_full_pipeline_long.py --destination "Bali" --test-upload --privacy-status private
```

### 2. Check Video Output
- Verify image count (should be 60-85 images for 7-day video)
- Check audio presence (should have voiceover + music)
- Verify video duration (should match voiceover duration)
- Check image variety (should not repeat)

### 3. Check Logs
- Look for "Found X images for scene Y"
- Check "Adding audio from: ..."
- Verify "Mixed audio for day X"
- Check "Scene X: Y images, Z seconds each"

---

**Last Updated**: 2025-11-12
**Status**: ✅ **Fixes Applied, Testing Required**
**Next Steps**: Run full pipeline test, verify video output, check audio quality


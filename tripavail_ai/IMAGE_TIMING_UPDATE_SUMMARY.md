# Image Timing Update Summary

## Overview
Updated the system to use a consistent **2.5 seconds per image** based on voiceover timing. The system now calculates the number of images needed from voiceover duration and displays each image for exactly 2.5 seconds.

## Changes Made

### 1. Image Generator (`core/media/images/generator/destination_image_generator_long.py`)
- **Updated image calculation**: Changed from 4.0 seconds per image to **2.5 seconds per image**
- **Formula**: `images_needed = voiceover_duration_seconds / 2.5`
- **Example**: 
  - Voiceover: 80 seconds → Images needed: 80 / 2.5 = 32 images
  - Voiceover: 95 seconds → Images needed: 95 / 2.5 = 38 images
- **Distribution**: Images are distributed across scenes (minimum 3 images per scene for visual variety)

### 2. Video Assembler (`core/media/video/generator/day_video_assembler_long.py`)
- **Fixed image duration**: All images display for exactly **2.5 seconds**
- **Calculation logic**:
  1. Get voiceover duration
  2. Calculate images needed: `voiceover_duration / 2.5`
  3. Use exactly 2.5 seconds per image for all images
  4. If voiceover is longer than image duration, extend the last image
  5. If images are longer than voiceover, trim the last image
- **Removed variable durations**: No longer uses different durations for different scene categories (hero, standard, quick)
- **Consistent timing**: All images use the same 2.5-second duration

## Workflow

### Per Day:
1. **Generate Script & Voiceover**
   - Script includes narration duration estimate (e.g., "≈ 80 s")
   - Voiceover is generated from script

2. **Calculate Images Needed**
   - Formula: `images_needed = voiceover_duration / 2.5`
   - Example: 80s voiceover → 32 images needed

3. **Generate Images**
   - Generate scene-specific images based on keywords
   - Distribute images across scenes (minimum 3 per scene)
   - Target: Generate at least `images_needed` images

4. **Assemble Day Video**
   - Use exactly 2.5 seconds per image
   - Use only the required number of images
   - Match video duration to voiceover duration

### Final Compilation:
1. **Compile All Days**
   - Combine all day videos into one final video
   - Each day follows the 2.5 seconds per image rule
   - Final video duration = sum of all day voiceovers

## Example Calculation

### Day 1: Uluwatu & Jimbaran
- Voiceover: 80 seconds
- Images needed: 80 / 2.5 = 32 images
- Images per scene: 32 / 4 scenes = 8 images per scene
- Video duration: 32 images × 2.5s = 80 seconds ✅

### Day 2: Ubud
- Voiceover: 95 seconds
- Images needed: 95 / 2.5 = 38 images
- Images per scene: 38 / 5 scenes = ~7-8 images per scene
- Video duration: 38 images × 2.5s = 95 seconds ✅

### Day 3: Canggu & Seminyak
- Voiceover: 85 seconds
- Images needed: 85 / 2.5 = 34 images
- Images per scene: 34 / 5 scenes = ~6-7 images per scene
- Video duration: 34 images × 2.5s = 85 seconds ✅

### Total Video
- Total voiceover: 80 + 95 + 85 = 260 seconds (4.3 minutes)
- Total images: 32 + 38 + 34 = 104 images
- Total video duration: 260 seconds ✅

## Benefits

1. **Consistent Timing**: All images display for exactly 2.5 seconds
2. **Accurate Calculation**: Image count is calculated directly from voiceover duration
3. **Simple Logic**: No complex duration calculations per scene or category
4. **Predictable Results**: Video duration matches voiceover duration exactly
5. **Per-Day Processing**: Each day is processed independently, then compiled

## Testing

To test the updated system:
```bash
python scripts/test_full_pipeline_long.py --destination "Bali, Indonesia" --privacy-status private
```

The system will:
1. Generate script with narration duration estimates
2. Generate voiceover from script
3. Calculate images needed: `voiceover_duration / 2.5`
4. Generate scene-specific images
5. Assemble day videos with 2.5 seconds per image
6. Compile all days into final video

## Logging

The system now logs:
- Voiceover duration per day
- Images needed per day (calculated from voiceover)
- Images available per day
- Images used per day
- Image duration (2.5 seconds)
- Total video duration per day

Example log output:
```
Voiceover duration: 80.00s
Target: 2.5s per image
Images needed: 32
Images available: 35
Total images used: 32 (target: 32)
```


# Long Video Day-Based Image Organization - Implementation Summary

## Overview
Restructured the long video generation system to organize images **per day** instead of globally. This ensures that each day has its own set of images based on that day's script and scenes.

## Key Changes

### 1. Image Directory Structure

**OLD Structure:**
```
data/long_videos/images/Bali/
  ├── attractions/
  ├── activities/
  ├── food_culture/
  ├── local_life/
  └── scenic_views/
```

**NEW Structure:**
```
data/long_videos/images/Bali/
  ├── day_1/
  │   ├── attractions/
  │   ├── activities/
  │   ├── food_culture/
  │   ├── local_life/
  │   ├── scenic_views/
  │   └── hotel_stay/  (NEW)
  ├── day_2/
  │   ├── attractions/
  │   ├── activities/
  │   ├── food_culture/
  │   ├── local_life/
  │   ├── scenic_views/
  │   └── hotel_stay/
  └── ...
```

### 2. Image Generation Workflow

**NEW Workflow:**
1. Generate itinerary (all days)
2. Generate script (all days)
3. **For EACH DAY:**
   - Generate voiceover (to get duration)
   - Extract keywords from script/narration
   - Estimate image count based on voiceover duration
   - Check if images exist for that day
   - Generate images for that day (organized by category)
   - Generate voiceover for that day (if not done)
   - Mix audio for that day
   - Assemble day video
4. Combine all day videos into final video

### 3. Keyword Extraction

- Extracts keywords from script narration (`image_keywords` field)
- Extracts keywords from itinerary scenes (`image_search_keywords` field)
- Combines both for better image search results
- Uses keywords in search queries: `"{keyword1} {keyword2} {keyword3} {category} in {destination}"`

### 4. Image Count Estimation

- Estimates image count based on voiceover duration
- Target: 3-5 seconds per image (default: 4 seconds)
- Minimum: 8 images per scene
- Formula: `max(int(voiceover_duration / 4.0), len(scenes) * 8)`
- Distributes images proportionally across categories based on scene counts

### 5. Category Mapping

**Scene Categories → Image Categories:**
- `arrival` → `scenic_views`, `local_life`
- `attraction` → `attractions`, `scenic_views`
- `food` → `food_culture`, `local_life`
- `stay` → `hotel_stay`, `scenic_views` (NEW: hotel_stay category)
- `scenic` → `scenic_views`, `attractions`
- `nightlife` → `local_life`, `activities`
- `transit` → `scenic_views`, `local_life`

### 6. Image Generation Logic

**NEW Method: `generate_images_for_day()`**
- Takes day number, scenes, voiceover duration, and keywords
- Estimates image count based on voiceover duration
- Maps scene categories to image categories
- Distributes images proportionally across categories
- Generates images using keywords from script
- Saves images to day-specific directories

**Updated Method: `generate_images_for_destination()`**
- Now supports optional `day_number` parameter
- If `day_number` is provided, saves images to day-specific directory
- If `day_number` is None, uses legacy structure (backward compatibility)

### 7. Cache System

**Updated Methods:**
- `get_cached_images()`: Now supports `day_number` parameter
- `cache_image()`: Now supports `day_number` parameter
- Checks day-specific directories first, then legacy structure
- Cache filenames include day number: `{destination}_day_{day_number}_{category}_{timestamp}.jpg`

### 8. Production Pipeline

**NEW Workflow:**
1. Generate itinerary
2. Generate script
3. **Generate voiceovers** (moved earlier to get duration)
4. **For EACH DAY:**
   - Extract keywords from script
   - Get voiceover duration
   - Generate images for that day
5. Mix audio for all days
6. Assemble day videos
7. Combine day videos into final video

### 9. Day Video Assembler

**Updated Image Collection:**
- **FIRST**: Tries day-specific directory: `images_dir / destination / f"day_{day_number}" / category`
- **FALLBACK**: If no day-specific directory, tries legacy structure
- Collects images from day-specific directories
- Maps images to scenes based on category preference
- Ensures no image repetition across scenes

### 10. Hotel Stay Category

**NEW Category: `hotel_stay`**
- Added to image categories list
- Maps from scene category `stay`
- Used for hotel/accommodation images
- Enables future paid content opportunities

## Files Modified

1. **`core/media/images/generator/destination_image_generator_long.py`**
   - Added `day_number` parameter to `generate_images_for_destination()`
   - Added new method `generate_images_for_day()`
   - Updated `get_cached_images()` to support `day_number`
   - Updated `cache_image()` to support `day_number`
   - Added `hotel_stay` to default categories

2. **`core/production/production_pipeline_long.py`**
   - Reordered workflow: voiceovers generated before images
   - Added day-by-day image generation loop
   - Added keyword extraction from script
   - Added voiceover duration retrieval
   - Calls `generate_images_for_day()` for each day

3. **`core/media/video/generator/day_video_assembler_long.py`**
   - Updated image collection to look for day-specific directories first
   - Added fallback to legacy structure
   - Updated `_map_scene_category_to_image_category()` to include `hotel_stay`
   - Updated image search to prioritize day-specific directories

## Benefits

1. **Better Organization**: Images are organized by day, making it easier to manage and debug
2. **Keyword-Based Search**: Uses keywords from script for more relevant image searches
3. **Dynamic Image Count**: Estimates image count based on voiceover duration
4. **No Image Repetition**: Each day has its own set of images
5. **Hotel Stay Support**: Added `hotel_stay` category for future paid content
6. **Backward Compatibility**: Still supports legacy structure as fallback

## Testing

To test the new system:
```bash
python scripts/test_full_pipeline_long.py --destination "Bali, Indonesia" --duration 7
```

Expected behavior:
1. Images should be generated in `data/long_videos/images/Bali/day_1/`, `day_2/`, etc.
2. Each day should have images in categories based on that day's scenes
3. Image count should be based on voiceover duration
4. Images should be searched using keywords from script
5. Day videos should use images from day-specific directories

## Next Steps

1. Test the full pipeline with a real destination
2. Verify image generation works correctly for all days
3. Verify day videos are assembled correctly
4. Verify final video combines all days correctly
5. Test with different destinations and durations

## Notes

- Legacy structure is still supported as fallback
- Cache system supports both day-specific and legacy caching
- Image validation remains the same (16:9 horizontal, min 1280x720)
- No AI fallback (waits for next day if all services fail)


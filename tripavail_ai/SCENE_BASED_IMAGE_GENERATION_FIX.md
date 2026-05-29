# Scene-Based Image Generation Fix

## Problem
Previously, images were generated per category (attractions, food_culture, etc.) using generic queries like "attractions in Bali", resulting in:
- Same images for all scenes in Day 1
- Images not matching specific script content (e.g., "Uluwatu Temple", "Jimbaran Bay seafood")
- Generic images instead of scene-specific images

## Solution: Scene-Based Keyword Search

### Key Changes

1. **Scene-Based Generation** (not category-based)
   - Each scene gets images based on its specific keywords
   - Images are generated per scene, not per category
   - Each scene uses its own unique search query

2. **Keyword Extraction Per Scene**
   - From itinerary: `scene.image_search_keywords` (primary)
   - From script: `script_scene.image_keywords` (secondary)
   - From script narration: Extract location/attraction names (e.g., "Uluwatu", "Jimbaran Bay")
   - Combined keywords are used only for that specific scene

3. **Scene-Specific Search Queries**
   - **Before**: `"keyword1 keyword2 keyword3 attractions in Bali"` (generic)
   - **After**: `"Uluwatu Temple cliff sunset Bali"` (scene-specific)
   - **After**: `"Jimbaran Bay seafood grilled fish Bali"` (scene-specific)
   - Uses actual keywords from script/itinerary, not generic category names

4. **Scene-to-Category Mapping**
   - Each scene maps to a single image category:
     - `attraction` → `attractions`
     - `food` → `food_culture`
     - `stay` → `hotel_stay`
     - `arrival` → `scenic_views`
     - `scenic` → `scenic_views`
     - `nightlife` → `local_life`
     - `transit` → `scenic_views`
   - Images are saved to the appropriate category folder

## Implementation Details

### Updated Files

1. **`core/media/images/generator/destination_image_generator_long.py`**
   - Changed `generate_images_for_day` method signature:
     - `keywords_from_script: Optional[List[str]]` → `keywords_from_script: Optional[Dict[int, List[str]]]`
     - Now accepts a dictionary mapping scene order to keywords
   - Changed from category-based to scene-based generation:
     - Loops through each scene individually
     - Extracts scene-specific keywords
     - Builds scene-specific query
     - Searches for images using scene keywords
     - Saves images to scene-specific category folder

2. **`core/production/production_pipeline_long.py`**
   - Updated keyword extraction logic:
     - Extracts keywords from script scenes and maps them by scene order
     - Extracts location/attraction names from script narration using regex
     - Creates a dictionary: `{scene_order: [keywords]}`
   - Passes scene-specific keywords to `generate_images_for_day`

### Example Flow

#### Day 1, Scene 1 (Attraction)
- **Script**: "Your first stop is Uluwatu Temple, where you'll discover..."
- **Itinerary Keywords**: ["Uluwatu Temple", "cliff sunset", "Kecak fire dance"]
- **Script Keywords**: ["Uluwatu Temple", "Kecak fire dance"]
- **Narration Extraction**: ["Uluwatu"]
- **Combined Keywords**: ["Uluwatu Temple", "cliff sunset", "Kecak fire dance", "Uluwatu"]
- **Query**: `"Uluwatu Temple cliff sunset Kecak fire dance Bali"`
- **Category**: `attractions`
- **Save to**: `data/long_videos/images/Bali/day_1/attractions/`
- **Filename**: `Bali_day_1_scene_01_attractions_001.jpg`

#### Day 1, Scene 2 (Food)
- **Script**: "Your first stop is Jimbaran Bay seafood, where you'll enjoy..."
- **Itinerary Keywords**: ["Jimbaran Bay", "seafood", "grilled fish"]
- **Script Keywords**: ["Jimbaran Bay", "seafood", "beach dinner"]
- **Narration Extraction**: ["Jimbaran"]
- **Combined Keywords**: ["Jimbaran Bay", "seafood", "grilled fish", "beach dinner", "Jimbaran"]
- **Query**: `"Jimbaran Bay seafood grilled fish beach dinner Bali"`
- **Category**: `food_culture`
- **Save to**: `data/long_videos/images/Bali/day_1/food_culture/`
- **Filename**: `Bali_day_1_scene_02_food_culture_001.jpg`

#### Day 1, Scene 3 (Local Life)
- **Script**: "Explore Ubud market, where you'll experience local life..."
- **Itinerary Keywords**: ["Ubud market", "local life", "traditional market"]
- **Script Keywords**: ["Ubud market", "local life"]
- **Narration Extraction**: ["Ubud"]
- **Combined Keywords**: ["Ubud market", "local life", "traditional market", "Ubud"]
- **Query**: `"Ubud market local life traditional market Bali"`
- **Category**: `local_life`
- **Save to**: `data/long_videos/images/Bali/day_1/local_life/`
- **Filename**: `Bali_day_1_scene_03_local_life_001.jpg`

## Benefits

1. **Scene-Specific Images**: Each scene gets images based on its specific content
2. **Keyword-Based Search**: Uses actual keywords from script/itinerary
3. **Unique Images Per Scene**: No repetition across scenes
4. **Better Relevance**: Images match script content exactly
5. **Location-Aware**: Uses specific locations/attractions mentioned in script
6. **Day-Specific**: Each day gets different images based on its scenes

## Testing

After implementation, verify:
1. ✅ Day 1 Scene 1 has images of "Uluwatu Temple" (not generic attractions)
2. ✅ Day 1 Scene 2 has images of "Jimbaran Bay seafood" (not generic food)
3. ✅ Day 2 Scene 1 has different images (not same as Day 1)
4. ✅ Each scene has unique, relevant images based on its keywords
5. ✅ Images are saved to correct day-specific category folders
6. ✅ Image filenames include scene number for tracking

## Next Steps

1. Run a test with a real destination (e.g., "Bali, Indonesia")
2. Verify that each scene gets unique, relevant images
3. Check that images match the script content
4. Ensure images are organized correctly in day-specific folders


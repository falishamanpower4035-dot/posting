# Keyword-Based Image Generation Plan

## Problem
Currently, images are generated using generic queries like "attractions in Bali" for all scenes in a day, resulting in:
- Same images for all categories in Day 1
- Images not matching specific script content (e.g., "Uluwatu Temple", "Jimbaran Bay seafood")
- Generic images instead of scene-specific images

## Solution: Scene-Based Keyword Search

### Current Flow (WRONG)
1. Collect ALL keywords from ALL scenes
2. Generate images per category (attractions, food_culture, etc.)
3. Use generic query: "keyword1 keyword2 keyword3 attractions in Bali"
4. Same images for all scenes in a category

### New Flow (CORRECT)
1. **For each scene individually:**
   - Extract scene-specific keywords from script and itinerary
   - Determine image category from scene category (attraction → attractions, food → food_culture)
   - Build scene-specific query: "Uluwatu Temple Bali" or "Jimbaran Bay seafood Bali"
   - Search for images using scene-specific keywords
   - Save images to day-specific category folder

2. **Keyword extraction per scene:**
   - From itinerary: `scene.image_search_keywords` (e.g., ["Uluwatu Temple", "cliff sunset"])
   - From script: `script_scene.image_keywords` (e.g., ["Uluwatu Temple", "Kecak fire dance"])
   - From script narration: Extract location/attraction names (e.g., "Uluwatu", "Jimbaran Bay")
   - Combine all keywords for that specific scene

3. **Search query building:**
   - For attraction scene: "Uluwatu Temple Bali" or "Uluwatu Temple cliff sunset Bali"
   - For food scene: "Jimbaran Bay seafood Bali" or "Jimbaran Bay grilled fish Bali"
   - For local life scene: "Ubud local life Bali" or "Ubud market local life Bali"
   - Always include destination name

4. **Image distribution:**
   - Generate images per scene (not per category)
   - Map scene to image category (attraction → attractions, food → food_culture)
   - Save images to: `data/long_videos/images/Bali/day_1/attractions/` (scene 1)
   - Save images to: `data/long_videos/images/Bali/day_1/food_culture/` (scene 2)
   - Each scene gets its own set of images based on its keywords

## Implementation Plan

### Step 1: Update `generate_images_for_day` Method
- Change from category-based to scene-based generation
- For each scene:
  - Extract scene-specific keywords
  - Build scene-specific query
  - Search for images using scene keywords
  - Save to appropriate category folder

### Step 2: Improve Keyword Extraction
- Extract keywords from script narration (parse for location/attraction names)
- Combine itinerary keywords + script keywords
- Use all keywords for that specific scene only

### Step 3: Update Search Query Logic
- Build query: `"{scene_keywords} {destination}"` (not generic category query)
- Example: "Uluwatu Temple cliff sunset Bali" (not "attractions in Bali")
- Example: "Jimbaran Bay seafood grilled fish Bali" (not "food_culture in Bali")

### Step 4: Scene-to-Category Mapping
- Map each scene to its image category
- Save images to scene-specific category folder
- Ensure images are unique per scene

## Example Flow

### Day 1, Scene 1 (Attraction)
- **Script**: "Your first stop is Uluwatu Temple, where you'll discover..."
- **Keywords**: ["Uluwatu Temple", "cliff sunset", "Kecak fire dance"]
- **Query**: "Uluwatu Temple cliff sunset Kecak fire dance Bali"
- **Category**: attractions
- **Save to**: `data/long_videos/images/Bali/day_1/attractions/`

### Day 1, Scene 2 (Food)
- **Script**: "Your first stop is Jimbaran Bay seafood, where you'll enjoy..."
- **Keywords**: ["Jimbaran Bay", "seafood", "grilled fish", "beach dinner"]
- **Query**: "Jimbaran Bay seafood grilled fish beach dinner Bali"
- **Category**: food_culture
- **Save to**: `data/long_videos/images/Bali/day_1/food_culture/`

### Day 1, Scene 3 (Local Life)
- **Script**: "Explore Ubud market, where you'll experience local life..."
- **Keywords**: ["Ubud market", "local life", "traditional market"]
- **Query**: "Ubud market local life traditional market Bali"
- **Category**: local_life
- **Save to**: `data/long_videos/images/Bali/day_1/local_life/`

## Benefits

1. **Scene-Specific Images**: Each scene gets images based on its specific content
2. **Keyword-Based Search**: Uses actual keywords from script/itinerary
3. **Unique Images Per Scene**: No repetition across scenes
4. **Better Relevance**: Images match script content exactly
5. **Location-Aware**: Uses specific locations/attractions mentioned in script

## Implementation Details

### Keyword Extraction Strategy
1. **From Itinerary**: `scene.image_search_keywords` (primary)
2. **From Script**: `script_scene.image_keywords` (secondary)
3. **From Script Narration**: Extract location/attraction names using NLP (optional)
4. **Combine**: Merge all keywords, remove duplicates

### Query Building
- **Format**: `"{keyword1} {keyword2} {keyword3} {destination}"`
- **Max Keywords**: Use top 3-5 most relevant keywords
- **Destination**: Always include destination name at the end
- **Category**: Don't include category in query (let keywords determine relevance)

### Image Count Per Scene
- **Calculate**: Based on voiceover duration for that scene
- **Minimum**: 8 images per scene
- **Maximum**: 12 images per scene
- **Distribution**: Evenly distribute across scenes

## Testing

After implementation, verify:
1. Day 1 Scene 1 has images of "Uluwatu Temple" (not generic attractions)
2. Day 1 Scene 2 has images of "Jimbaran Bay seafood" (not generic food)
3. Day 2 Scene 1 has different images (not same as Day 1)
4. Each scene has unique, relevant images based on its keywords


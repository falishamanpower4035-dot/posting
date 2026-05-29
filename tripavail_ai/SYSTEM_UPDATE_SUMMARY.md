# System Update Summary: Premium Travel Video Format

## Overview
Updated the itinerary and script generation system to match the premium travel video format shown in the sample. The system now generates content in a more cinematic, poetic style with explicit visual order descriptions and narration duration estimates.

## Changes Made

### 1. Itinerary Generator (`core/content/generation/itinerary_generator_long.py`)
- **Day Title Format**: Updated to generate day titles in the format: `"DAY X – LOCATION(S): Theme"`
  - Example: `"DAY 1 – ULUWATU & JIMBARAN: Ocean Cliffs and Culture"`
  - Example: `"DAY 2 – UBUD: Rice Terraces, Temples & Local Life"`
- **Enhanced Image Keywords**: Added requirement for more specific, vivid keywords using location names and landmarks
  - Example: `"Uluwatu Temple cliff sunset"`, `"Jimbaran Bay grilled seafood"`, `"Tegalalang rice terraces sunrise"`

### 2. Script Generator (`core/content/generation/script_generator_long.py`)
- **Narration Style**: Updated to generate poetic, cinematic, evocative narration like premium travel documentaries
  - Uses vivid imagery, sensory details, and emotional language
  - Example: `"Your Bali adventure begins on the southern coast. From Ngurah Rai International Airport, the drive opens to turquoise waves and limestone cliffs."`
- **Narration Duration Estimate**: Added explicit duration estimates in format: `"≈ 80 s"`, `"≈ 95 s"`, etc.
- **Visual Order Field**: Added `visual_order` field for each scene with numbered emoji descriptions
  - Example: `"1️⃣ Arrival – airport exterior, road to Uluwatu"`
  - Example: `"2️⃣ Temple – cliff panoramas, sunset waves, dancers"`
  - Example: `"3️⃣ Food – Jimbaran Bay dinner, sizzling grill close-ups"`
- **System Prompt**: Updated to emphasize premium travel documentary style

### 3. Production Pipeline (`core/production/production_pipeline_long.py`)
- **Visual Order Keyword Extraction**: Added logic to extract keywords from `visual_order` field
  - Removes emoji and numbering
  - Extracts meaningful words from visual descriptions
  - Enhances image search with more specific visual descriptions
- **Enhanced Keyword Extraction**: Improved keyword extraction from script scenes
  - Combines `image_keywords`, `visual_order` descriptions, and location names from narration
  - Creates more comprehensive keyword sets for better image matching

## New JSON Structure

### Itinerary Format
```json
{
  "destination": "Bali",
  "ideal_days": 3,
  "itinerary": [
    {
      "day_number": 1,
      "title": "DAY 1 – ULUWATU & JIMBARAN: Ocean Cliffs and Culture",
      "scenes": [
        {
          "order": 1,
          "category": "arrival",
          "image_search_keywords": ["Ngurah Rai Airport", "Bali airport terminal", "road to Uluwatu"]
        }
      ]
    }
  ]
}
```

### Script Format
```json
{
  "destination": "Bali",
  "total_duration_estimate_seconds": 260,
  "days": [
    {
      "day_number": 1,
      "narration": "Your Bali adventure begins on the southern coast. From Ngurah Rai International Airport, the drive opens to turquoise waves and limestone cliffs...",
      "narration_duration_estimate": "≈ 80 s",
      "narration_word_count": 120,
      "estimated_voiceover_seconds": 80,
      "scenes": [
        {
          "order": 1,
          "scene_narration": "Your Bali adventure begins on the southern coast. From Ngurah Rai International Airport, the drive opens to turquoise waves and limestone cliffs.",
          "visual_order": "1️⃣ Arrival – airport exterior, road to Uluwatu",
          "image_keywords": ["Ngurah Rai Airport", "Bali airport terminal", "road to Uluwatu"]
        },
        {
          "order": 2,
          "scene_narration": "The legendary Uluwatu Temple sits above the ocean like a guardian of the island. As the sun melts into the horizon, the hypnotic rhythm of the Kecak fire dance fills the air.",
          "visual_order": "2️⃣ Temple – cliff panoramas, sunset waves, dancers",
          "image_keywords": ["Uluwatu Temple", "cliff sunset", "Kecak fire dance"]
        }
      ]
    }
  ]
}
```

## Benefits

1. **Better Visual Descriptions**: Visual order descriptions provide clear guidance on what visuals should appear, making image selection more accurate
2. **Premium Content Style**: Poetic, cinematic narration creates more engaging, professional travel videos
3. **Better Image Matching**: Enhanced keyword extraction from multiple sources (image_keywords, visual_order, narration) improves image relevance
4. **Clear Duration Estimates**: Explicit narration duration estimates help with video planning and timing
5. **Consistent Format**: Day titles follow a consistent, professional format that's easy to read and understand

## Testing

To test the updated system:
```bash
python scripts/test_full_pipeline_long.py --destination "Bali, Indonesia" --privacy-status private
```

The system will:
1. Generate itinerary with new day title format
2. Generate script with poetic narration, visual order, and duration estimates
3. Extract keywords from visual_order and narration
4. Generate scene-specific images using enhanced keywords
5. Create video with proper images and audio

## Next Steps

1. Run a test with the new format
2. Review generated itinerary and script to ensure they match the sample style
3. Verify that visual_order descriptions are being used for image selection
4. Check that narration duration estimates are accurate
5. Adjust prompts if needed to better match the sample format


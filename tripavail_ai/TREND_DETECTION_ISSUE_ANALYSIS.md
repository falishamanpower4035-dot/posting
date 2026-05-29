# Trend Detection Issue Analysis

## Problem Identified

The system keeps selecting **Karnataka, India** even though it's been 4 days and should select a different destination.

## Root Causes

### 1. **Destination Selection Logic** (FIXED ✅)
- **Issue**: Script always selects `trending_destinations[0]` (highest score), regardless of whether it's new or already processed
- **Fixed**: Now prioritizes:
  1. **NEW destinations** (not in processed list) without videos
  2. Any trending destination without existing video
  3. Top trending (only if all have videos)

### 2. **No Video Existence Check** (FIXED ✅)
- **Issue**: Script doesn't check if video already exists before generating
- **Fixed**: Added `video_exists()` check to skip destinations with existing videos

### 3. **Same News Articles** (NEEDS ATTENTION ⚠️)
- **Issue**: Using same 2 news articles repeatedly, so same destinations keep trending
- **Impact**: Without fresh news, trend detection will keep finding Karnataka and Australia
- **Solution Needed**: 
  - Fetch fresh news articles daily
  - Check `last_updated` in `processed_news.json`
  - Force news refresh if older than 24 hours

### 4. **Trend Cache Not Filtering Old Destinations** (NEEDS REVIEW)
- **Issue**: Destinations stay in trending list even after being processed
- **Current Behavior**: `destinations_processed` list tracks what's been processed, but destinations still appear in `trending_destinations`
- **Question**: Should we filter out processed destinations from trending list? Or keep them but mark them?

## Current State

From `trending_destinations_long.json`:
```json
{
  "last_updated": "2025-11-16T03:50:09.506517",  // Today
  "trending_destinations": [
    {
      "name": "Karnataka, India",
      "trend_score": 45.0,
      ...
    },
    {
      "name": "Australia",
      "trend_score": 36.0,
      ...
    }
  ],
  "destinations_processed": [
    "Karnataka, India",  // Already processed!
    "Australia",
    ...
  ],
  "new_destinations_count": 0  // No new destinations found
}
```

## Fixes Applied

### ✅ Fix 1: Smart Destination Selection
```python
# Priority 1: New destinations without videos
if new_destinations:
    for dest in sorted(new_destinations, key=lambda x: x.get('trend_score', 0), reverse=True):
        if not video_exists(dest.get('name', '')):
            selected_destination = dest
            break

# Priority 2: Any trending destination without video
if not selected_destination:
    for dest in sorted(trending_destinations, ...):
        if not video_exists(dest.get('name', '')):
            selected_destination = dest
            break
```

### ✅ Fix 2: Video Existence Check
```python
def video_exists(dest_name: str) -> bool:
    safe_destination = dest_name.replace(",", "_").replace(" ", "_")
    videos_dir = Path(settings_long.VIDEOS_DIR)
    video_path = videos_dir / f"{safe_destination}_final.mp4"
    return video_path.exists()
```

## Remaining Issues

### ⚠️ Issue 1: Stale News Articles
- Only 2 news articles in `processed_news.json`
- News is likely stale (no date check)
- Need to fetch fresh news daily

**Recommendation**:
1. Check `processed_news.json` `last_updated` timestamp
2. If older than 24 hours, force fresh news fetch
3. Use `NewsFetcher().run_fetch_cycle()` to get latest articles

### ⚠️ Issue 2: Same Destinations Keep Trending
- Karnataka and Australia keep appearing because news articles are the same
- Need fresh news to discover new trends

**Recommendation**:
- Add date-based filtering: Only use news from last 48 hours
- Or: Filter out destinations that have been trending for > 3 days

### ⚠️ Issue 3: No Automatic News Refresh
- `run_trend_and_generate_video.py` uses existing news if available
- Should check if news is fresh before using

## Next Steps

1. ✅ **DONE**: Fixed destination selection logic
2. ✅ **DONE**: Added video existence check
3. ⏳ **TODO**: Add news freshness check
4. ⏳ **TODO**: Force news refresh if stale
5. ⏳ **TODO**: Consider filtering out destinations that have been trending > 3 days

## Testing

After fixes:
- Script should select **Australia** if Karnataka video exists (but Australia doesn't)
- Or skip both if both videos exist
- Should log which priority level was used for selection


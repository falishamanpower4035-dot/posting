# ISSUE DIAGNOSIS - 8 Hours No Posts Generated

## ROOT CAUSE

1. **Posts 056-061 Failed Video Generation**
   - All posts failed at FFmpeg audio mixing step
   - Error: FFmpeg mixing failed (but FFmpeg actually works - bug in error detection)
   - Result: Posts generated but NOT scheduled (line 106-110 in run_two_hour_scheduler.py)
   - Posts exist with draft.mp4 but no final video

2. **No New Posts Being Generated**
   - All articles with score >= 7 have already been used
   - System filters out already-used articles before generation
   - Result: "No new topics to generate" message (but not logged)

## FIXES NEEDED

### Fix 1: FFmpeg Error Handling
- Current: Only shows first 200 chars of stderr (includes FFmpeg banner)
- Problem: FFmpeg warnings in stderr treated as errors
- Fix: Check return code AND file existence properly, ignore FFmpeg banner

### Fix 2: Schedule Even Without Music
- Current: Falls back to voiceover-only mix if music missing
- Problem: Music generation failed (ElevenLabs quota), but code should still work
- Fix: Ensure simple mix path works correctly

### Fix 3: Better Error Messages
- Current: "FFmpeg mixing failed" with truncated stderr
- Fix: Show full error, check actual FFmpeg return code

### Fix 4: Manual Recovery for Failed Posts
- Posts 056-061 have draft videos but failed final mixing
- Can manually fix or regenerate final videos

## IMMEDIATE ACTION

1. Fix FFmpeg mixing bug
2. Check why all articles are marked as "used"
3. Verify next 4-hour cycle will generate new posts



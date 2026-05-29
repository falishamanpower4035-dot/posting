# Latest Fixes Summary - Video Generation Errors

## Errors Found

### 1. **FFmpeg SAR (Sample Aspect Ratio) Mismatch** ❌
- **Error**: `Input link in0:v0 parameters (size 1920x1080, SAR 691200:691313) do not match the corresponding output link in0:v0 parameters (1920x1080, SAR 1382400:1382713)`
- **Cause**: Different images have different SAR values, causing FFmpeg concat filter to fail
- **Fix**: Added `setsar=1:1` to normalize SAR in the filter chain
- **File**: `core/media/video/generator/day_video_assembler_long.py`

### 2. **FFprobe Command Syntax Error** ❌
- **Error**: `Unrecognized option 'show_entries'` when using FFmpeg as FFprobe fallback
- **Cause**: FFmpeg doesn't support FFprobe-specific options like `-show_entries`
- **Fix**: Detect when FFmpeg is used as fallback and use FFmpeg-compatible syntax (`-i file -hide_banner -f null -`) and parse duration from stderr
- **Files**: 
  - `core/media/video/generator/day_video_assembler_long.py`
  - `core/media/audio/audio_mixer_long.py`
  - `core/media/video/generator/final_video_assembler_long.py`

## Fixes Applied

### 1. SAR Normalization Fix ✅
**File**: `core/media/video/generator/day_video_assembler_long.py` (line 582)

**Before**:
```python
f"setsar=1:1,setpts=PTS-STARTPTS,fps={self.fps}[v{i}]"
```

**After**:
```python
f"setsar=1:1,setpts=PTS-STARTPTS,fps={self.fps}[v{i}]"
```

Actually, the fix was adding `setsar=1:1` to normalize the Sample Aspect Ratio:
```python
f"[{i}:v]scale=...pad=...,setsar=1:1,setpts=PTS-STARTPTS,fps={self.fps}[v{i}]"
```

### 2. FFprobe/FFmpeg Fallback Fix ✅

**Detection Logic**: Check if `ffprobe_path == ffmpeg_path` to detect fallback usage

**FFmpeg Syntax** (when used as FFprobe):
```python
cmd = [
    ffprobe_path,  # Actually FFmpeg
    '-i', str(audio_path),
    '-hide_banner',
    '-f', 'null',
    '-'
]
# Parse from stderr: "Duration: 00:00:42.87"
duration_match = re.search(r'Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
hours, minutes, seconds = duration_match.groups()
duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
```

**FFprobe Syntax** (when actual FFprobe available):
```python
cmd = [
    ffprobe_path,
    '-v', 'error',
    '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1',
    str(audio_path)
]
# Parse from stdout: "42.87"
duration = float(result.stdout.strip())
```

## Files Modified

1. `core/media/video/generator/day_video_assembler_long.py`
   - Added `setsar=1:1` to filter chain
   - Fixed FFprobe/FFmpeg fallback detection for voiceover duration

2. `core/media/audio/audio_mixer_long.py`
   - Fixed FFprobe/FFmpeg fallback detection for audio duration

3. `core/media/video/generator/final_video_assembler_long.py`
   - Fixed FFprobe/FFmpeg fallback detection for video duration

## Next Steps

After these fixes:
1. Video assembly should work with normalized SAR
2. Audio/video duration detection should work with FFmpeg fallback
3. All day videos should assemble successfully
4. Final video assembly should complete

## Testing

Re-run the video generation script to verify all fixes:
```bash
python scripts/generate_karnataka_video.py
```


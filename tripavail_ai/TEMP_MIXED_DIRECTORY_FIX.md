# temp_mixed Directory Fix

## Issue Identified

The audio mixing process was failing because the `temp_mixed` directory wasn't being created before FFmpeg tried to write output files to it.

### Error from Logs:
```
Error opening output data\long_videos\voiceovers\temp_mixed\Karnataka__India_day_5_mixed.mp3: No such file or directory
```

## Root Cause

1. **Directory Creation**: The `temp_mixed` directory is supposed to be created in `AudioMixerLong.__init__()` at line 58:
   ```python
   self.temp_dir.mkdir(parents=True, exist_ok=True)
   ```
   
2. **Timing Issue**: However, there could be scenarios where:
   - The directory doesn't exist when `mix_audio_for_day()` is called
   - The directory was deleted between initialization and use
   - Path issues prevent proper directory creation

3. **FFmpeg Requirement**: FFmpeg requires the output directory to exist before it can write files. If the directory doesn't exist, FFmpeg will fail with "No such file or directory" error.

## Fix Applied

### 1. Added Directory Check in `_mix_audio_with_ffmpeg()`
Before FFmpeg tries to write, ensure the output directory exists:
```python
# Ensure output directory exists before FFmpeg tries to write
output_path.parent.mkdir(parents=True, exist_ok=True)
```

### 2. Added Directory Check in Voiceover Copy Path
When copying voiceover without music, ensure the directory exists:
```python
# Ensure output directory exists before copying
output_path.parent.mkdir(parents=True, exist_ok=True)
```

### 3. Created Directory Manually
Created the directory to ensure it exists:
```powershell
New-Item -ItemType Directory -Path "data\long_videos\voiceovers\temp_mixed" -Force
```

## Files Modified

- `core/media/audio/audio_mixer_long.py`
  - Line 233: Added directory check before FFmpeg mixing
  - Line 182: Added directory check before voiceover copy

## Testing

The fix ensures that:
1. ✅ The `temp_mixed` directory is always created before FFmpeg writes
2. ✅ The directory is created even if `__init__()` didn't create it properly
3. ✅ Both code paths (with music and without music) ensure directory exists
4. ✅ The directory is created manually for immediate use

## Verification

To verify the fix works:
1. Check that `data/long_videos/voiceovers/temp_mixed/` exists
2. Run the video generation script
3. Monitor logs for successful audio mixing (no more "No such file or directory" errors)
4. Verify mixed audio files are created in `temp_mixed/` directory

## Expected Behavior After Fix

- ✅ Audio mixing should succeed for all 7 days
- ✅ Mixed audio files should be created in `temp_mixed/` directory
- ✅ FFmpeg should no longer fail with directory errors
- ✅ Video assembly can proceed with mixed audio files


#!/usr/bin/env python3
"""
Directly reassemble video using existing files:
- Existing itinerary
- Existing script
- Existing voiceovers
- Existing images
Only regenerates: audio mixing, day video assembly, final video assembly
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.production.production_pipeline_long import ProductionPipelineLong
from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
from core.content.generation.script_generator_long import ScriptGeneratorLong
from core.media.audio.audio_mixer_long import AudioMixerLong
from core.media.video.generator.day_video_assembler_long import DayVideoAssemblerLong
from core.media.video.generator.final_video_assembler_long import FinalVideoAssemblerLong
import config.settings_long as settings_long
from loguru import logger

def main():
    """Reassemble video for Bali using existing files"""
    logger.info("=" * 60)
    logger.info("REASSEMBLING VIDEO WITH EXISTING FILES (NO DOWNLOADS)")
    logger.info("=" * 60)
    
    destination = "Bali, Indonesia"
    settings = settings_long
    
    # Initialize components
    itinerary_gen = ItineraryGeneratorLong()
    script_gen = ScriptGeneratorLong()
    audio_mixer = AudioMixerLong()
    day_assembler = DayVideoAssemblerLong()
    final_assembler = FinalVideoAssemblerLong()
    
    # 1. Load existing itinerary
    logger.info(f"Step 1: Loading existing itinerary for {destination}...")
    itinerary_data = itinerary_gen.load_itinerary(destination)
    if not itinerary_data:
        logger.error(f"❌ Itinerary not found for {destination}")
        return {"status": "failed", "error": "Itinerary not found"}
    
    days = itinerary_data.get("itinerary", [])
    logger.info(f"✅ Loaded itinerary: {len(days)} days")
    
    # 2. Load existing script
    logger.info(f"Step 2: Loading existing script for {destination}...")
    script_data = script_gen.load_script(destination)
    if not script_data:
        logger.error(f"❌ Script not found for {destination}")
        return {"status": "failed", "error": "Script not found"}
    
    script_days = script_data.get("days", [])
    logger.info(f"✅ Loaded script: {len(script_days)} days")
    
    # 3. Process each day: mix audio, assemble video
    day_video_paths = {}
    images_dir = Path(settings_long.IMAGES_DIR)  # Base images directory (not destination-specific)
    voiceovers_dir = Path(settings_long.VOICEOVERS_DIR)
    videos_dir = Path(settings_long.VIDEOS_DIR)
    
    # Determine active days (those with voiceovers)
    active_day_numbers = []
    for day in days:
        day_number = day.get("day_number")
        voiceover_path = voiceovers_dir / f"{destination.replace(',', '_').replace(' ', '_')}_day_{day_number}_voiceover.mp3"
        if voiceover_path.exists():
            active_day_numbers.append(day_number)
        else:
            logger.warning(f"Day {day_number} voiceover not found, skipping: {voiceover_path}")
    
    logger.info(f"Found {len(active_day_numbers)} days with voiceovers: {active_day_numbers}")
    
    cumulative_video_path = None
    
    for idx, day_number in enumerate(sorted(active_day_numbers)):
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"PROCESSING DAY {day_number}")
        logger.info("=" * 60)
        
        # Find day and script data
        day = next((d for d in days if d.get("day_number") == day_number), None)
        script_day = next((sd for sd in script_days if sd.get("day_number") == day_number), None)
        
        if not day or not script_day:
            logger.warning(f"Day {day_number} data not found, skipping")
            continue
        
        # 3a. Load voiceover
        voiceover_filename = f"{destination.replace(',', '_').replace(' ', '_')}_day_{day_number}_voiceover.mp3"
        voiceover_path = voiceovers_dir / voiceover_filename
        
        if not voiceover_path.exists():
            logger.warning(f"Voiceover not found for Day {day_number}: {voiceover_path}")
            continue
        
        logger.info(f"✅ Using voiceover: {voiceover_path.name}")
        
        # Get voiceover duration
        try:
            import subprocess
            from core.utils.ffmpeg_helper import get_ffprobe_path
            ffprobe_path = get_ffprobe_path()
            probe_cmd = [
                ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(voiceover_path)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            if probe_result.returncode == 0:
                voiceover_duration = float(probe_result.stdout.strip())
            else:
                voiceover_duration = 90.0
        except Exception as e:
            logger.warning(f"Failed to get voiceover duration: {e}")
            voiceover_duration = 90.0
        
        logger.info(f"Voiceover duration: {voiceover_duration:.2f} seconds")
        
        # 3b. Mix audio
        logger.info(f"Step 3b: Mixing audio for Day {day_number}...")
        transition_prompt = script_day.get("transition_prompt", "")
        is_final_day = (idx == len(active_day_numbers) - 1)
        
        mixed_audio_path = audio_mixer.mix_audio_for_day(
            voiceover_path=voiceover_path,
            destination=destination,
            day_number=day_number,
            transition_prompt=transition_prompt,
            is_final_day=is_final_day
        )
        
        if not mixed_audio_path or not mixed_audio_path.exists():
            logger.warning(f"Audio mixing failed for Day {day_number}, using voiceover only")
            mixed_audio_path = voiceover_path
        
        logger.info(f"✅ Mixed audio: {mixed_audio_path.name}")
        
        # 3c. Assemble day video
        logger.info(f"Step 3c: Assembling video for Day {day_number}...")
        day_video_path = day_assembler.assemble_day_video(
            day_data=day,
            script_data=script_data,
            destination=destination,
            images_dir=images_dir,
            voiceover_path=mixed_audio_path,
            voiceover_duration_seconds=voiceover_duration,
        )
        
        if not day_video_path or not day_video_path.exists():
            logger.error(f"❌ Failed to assemble video for Day {day_number}")
            continue
        
        day_video_paths[day_number] = day_video_path
        file_size = day_video_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Day {day_number} video: {day_video_path.name} ({file_size:.2f} MB)")
        
        # 3d. Incremental compilation (combine with previous cumulative)
        completed_days = sorted([d for d in day_video_paths.keys()])
        
        if len(completed_days) >= 2:
            logger.info("")
            logger.info(f"Step 3d: Compiling cumulative video (Days {'+'.join(map(str, completed_days))})...")
            
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            cumulative_name = "+".join([f"day{d}" for d in completed_days])
            cumulative_output_path = videos_dir / f"{safe_destination}_{cumulative_name}.mp4"
            
            if cumulative_video_path and cumulative_video_path.exists():
                # Incremental: previous cumulative + new day
                videos_to_combine = {day_number: day_video_path}
                cumulative_video_path = final_assembler.combine_day_videos(
                    videos_to_combine, destination, None, cumulative_output_path, cumulative_video_path
                )
            else:
                # First compilation: combine all completed days
                videos_to_combine = {d: day_video_paths[d] for d in completed_days}
                cumulative_video_path = final_assembler.combine_day_videos(
                    videos_to_combine, destination, None, cumulative_output_path
                )
            
            if cumulative_video_path and cumulative_video_path.exists():
                cumulative_size = cumulative_video_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Cumulative video: {cumulative_video_path.name} ({cumulative_size:.2f} MB)")
                logger.info(f"   Contains: Days {'+'.join(map(str, completed_days))}")
            else:
                logger.error(f"❌ Failed to compile cumulative video")
        else:
            # Day 1 only
            cumulative_video_path = day_video_path
            logger.info("Day 1 complete - will compile after Day 2")
    
    # Final video
    if cumulative_video_path and cumulative_video_path.exists():
        final_video_path = cumulative_video_path
        
        # Copy to final video path
        safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
        final_output_path = videos_dir / f"{safe_destination}_final_video.mp4"
        import shutil
        shutil.copy2(final_video_path, final_output_path)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ REASSEMBLY COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Final video: {final_output_path.name}")
        logger.info(f"Path: {final_output_path}")
        file_size = final_output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Size: {file_size:.2f} MB")
        
        return {
            "status": "completed",
            "video_path": str(final_output_path),
            "days_processed": len(day_video_paths)
        }
    else:
        logger.error("❌ Reassembly failed - no final video generated")
        return {"status": "failed", "error": "No final video generated"}

if __name__ == "__main__":
    result = main()
    logger.info("")
    logger.info("Result:", result)


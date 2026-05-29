#!/usr/bin/env python3
"""
Production Pipeline for Long Videos
Integrates all components: itinerary → script → images → voiceover → video → upload
Processes per day, combines at end
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

# Import components
from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
from core.content.generation.script_generator_long import ScriptGeneratorLong
from core.utils.error_handler_long import ErrorHandlerLong
from core.media.images.generator.destination_image_generator_long import DestinationImageGeneratorLong
from core.media.audio.voiceover_generator_long import VoiceoverGeneratorLong
from core.media.audio.audio_mixer_long import AudioMixerLong
from core.media.video.generator.day_video_assembler_long import DayVideoAssemblerLong
from core.media.video.generator.final_video_assembler_long import FinalVideoAssemblerLong
from core.media.video.generator.thumbnail_generator_long import ThumbnailGeneratorLong
from core.social.platforms.youtube_uploader_long import YouTubeUploaderLong
from core.utils.quality_validator_long import QualityValidatorLong  # PHASE 3.1: Quality validation
try:
    from core.utils.pacing_analyzer_long import PacingAnalyzerLong  # PHASE 3.2: Pacing analysis
except ImportError:
    PacingAnalyzerLong = None  # Pacing analyzer not available


class ProductionPipelineLong:
    """
    Production pipeline for long videos
    Integrates all components and processes videos per day
    """
    
    def __init__(self):
        # Initialize components
        self.itinerary_generator = ItineraryGeneratorLong()
        self.script_generator = ScriptGeneratorLong()
        self.error_handler = ErrorHandlerLong()
        self.image_generator = DestinationImageGeneratorLong()
        self.voiceover_generator = VoiceoverGeneratorLong()
        self.audio_mixer = AudioMixerLong()
        self.day_assembler = DayVideoAssemblerLong()
        self.final_assembler = FinalVideoAssemblerLong()
        self.thumbnail_generator = ThumbnailGeneratorLong()
        self.youtube_uploader = YouTubeUploaderLong()
        self.quality_validator = QualityValidatorLong()  # PHASE 3.1: Quality validation
        if PacingAnalyzerLong:
            self.pacing_analyzer = PacingAnalyzerLong()  # PHASE 3.2: Pacing analysis
        else:
            self.pacing_analyzer = None  # Pacing analysis disabled if not available
        
        # Directories
        self.data_dir = Path(settings_long.DATA_DIR)
        self.long_videos_dir = Path(settings_long.LONG_VIDEOS_DIR)
        self.images_dir = Path(settings_long.IMAGES_DIR)
        self.voiceovers_dir = Path(settings_long.VOICEOVERS_DIR)
        self.videos_dir = Path(settings_long.VIDEOS_DIR)
        self.thumbnails_dir = Path(settings_long.THUMBNAILS_DIR)
        
        logger.info("Production Pipeline Long initialized")
    
    def cleanup_previous_data(self, destination: str) -> bool:
        """
        Clean up previous video data for a destination
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            logger.info(f"Cleaning up previous data for: {destination}")
            
            # Clean destination name for file paths
            safe_destination = destination.replace(",", "_").replace(" ", "_")
            
            # 1. Delete images directory for this destination
            images_dest_dir = self.images_dir / destination
            if images_dest_dir.exists():
                import shutil
                shutil.rmtree(images_dest_dir)
                logger.info(f"✅ Deleted images directory: {images_dest_dir}")
            
            # Also check for safe destination name
            images_safe_dir = self.images_dir / safe_destination
            if images_safe_dir.exists():
                import shutil
                shutil.rmtree(images_safe_dir)
                logger.info(f"✅ Deleted images directory: {images_safe_dir}")
            
            # 2. Delete voiceover files
            voiceover_pattern = f"{safe_destination}_day_*.mp3"
            voiceover_files = list(self.voiceovers_dir.glob(voiceover_pattern))
            # Also check for destination with comma
            voiceover_pattern2 = f"{destination.replace(',', '__')}_day_*.mp3"
            voiceover_files.extend(list(self.voiceovers_dir.glob(voiceover_pattern2.replace(" ", "_"))))
            # Also check direct destination name
            voiceover_pattern3 = destination.replace(",", "_").replace(" ", "_")
            voiceover_files.extend(list(self.voiceovers_dir.glob(f"{voiceover_pattern3}_day_*.mp3")))
            
            for voiceover_file in voiceover_files:
                if voiceover_file.exists():
                    voiceover_file.unlink()
                    logger.info(f"✅ Deleted voiceover: {voiceover_file.name}")
            
            # Delete temp_mixed directory if it exists
            temp_mixed_dir = self.voiceovers_dir / "temp_mixed"
            if temp_mixed_dir.exists():
                import shutil
                shutil.rmtree(temp_mixed_dir)
                logger.info(f"✅ Deleted temp_mixed directory")
            
            # 3. Delete video files
            video_pattern = f"{safe_destination}*.mp4"
            video_files = list(self.videos_dir.glob(video_pattern))
            # Also check for destination with comma
            video_pattern2 = destination.replace(",", "__").replace(" ", "_")
            video_files.extend(list(self.videos_dir.glob(f"{video_pattern2}*.mp4")))
            
            for video_file in video_files:
                if video_file.exists():
                    video_file.unlink()
                    logger.info(f"✅ Deleted video: {video_file.name}")
            
            # Delete temp_days directory if it exists
            temp_days_dir = self.videos_dir / "temp_days"
            if temp_days_dir.exists():
                import shutil
                shutil.rmtree(temp_days_dir)
                logger.info(f"✅ Deleted temp_days directory")
            
            # 4. Delete thumbnail files
            thumbnail_pattern = f"{safe_destination}*.jpg"
            thumbnail_files = list(self.thumbnails_dir.glob(thumbnail_pattern))
            # Also check for destination with comma
            thumbnail_pattern2 = destination.replace(",", "__").replace(" ", "_")
            thumbnail_files.extend(list(self.thumbnails_dir.glob(f"{thumbnail_pattern2}*.jpg")))
            
            for thumbnail_file in thumbnail_files:
                if thumbnail_file.exists():
                    thumbnail_file.unlink()
                    logger.info(f"✅ Deleted thumbnail: {thumbnail_file.name}")
            
            # 5. Delete script files
            scripts_dir = Path(settings_long.SCRIPTS_DIR)
            if scripts_dir.exists():
                script_pattern = f"{safe_destination}_script.json"
                script_files = list(scripts_dir.glob(script_pattern))
                # Also check for destination with comma (Bali, Indonesia -> Bali__Indonesia)
                script_pattern2 = destination.replace(",", "__").replace(" ", "_")
                script_files.extend(list(scripts_dir.glob(f"{script_pattern2}_script.json")))
                # Also check for destination with comma replaced (Bali, Indonesia -> Bali_Indonesia)
                script_pattern3 = destination.replace(", ", "_").replace(",", "_")
                script_files.extend(list(scripts_dir.glob(f"{script_pattern3}_script.json")))
                
                for script_file in script_files:
                    if script_file.exists():
                        script_file.unlink()
                        logger.info(f"✅ Deleted script: {script_file.name}")
            
            # 6. Delete itinerary files
            destinations_dir = Path(settings_long.DESTINATIONS_DIR)
            if destinations_dir.exists():
                itinerary_pattern = f"{safe_destination}_itinerary.json"
                itinerary_files = list(destinations_dir.glob(itinerary_pattern))
                # Also check for destination with comma (Bali, Indonesia -> Bali__Indonesia)
                itinerary_pattern2 = destination.replace(",", "__").replace(" ", "_")
                itinerary_files.extend(list(destinations_dir.glob(f"{itinerary_pattern2}_itinerary.json")))
                # Also check for destination with comma replaced (Bali, Indonesia -> Bali_Indonesia)
                itinerary_pattern3 = destination.replace(", ", "_").replace(",", "_")
                itinerary_files.extend(list(destinations_dir.glob(f"{itinerary_pattern3}_itinerary.json")))
                
                for itinerary_file in itinerary_files:
                    if itinerary_file.exists():
                        itinerary_file.unlink()
                        logger.info(f"✅ Deleted itinerary: {itinerary_file.name}")
            
            logger.info(f"✅ Cleanup complete for: {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def generate_video_for_destination(
        self,
        destination: str,
        max_duration_minutes: int = 8,
        upload_to_youtube: bool = True,
        privacy_status: str = "public",
        skip_cleanup: bool = False,
        reuse_existing: bool = False,
        process_days: Optional[List[int]] = None  # NEW: restrict processing to specific day numbers
    ) -> Dict[str, Any]:
        """
        Generate complete video for destination
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            max_duration_minutes: Maximum video duration in minutes (default: 8)
            upload_to_youtube: Whether to upload to YouTube (default: True)
            privacy_status: YouTube privacy status (default: "public")
            
        Returns:
            Dictionary with generation results
        """
        try:
            logger.info("=" * 60)
            logger.info(f"LONG VIDEO GENERATION: {destination}")
            logger.info("=" * 60)
            
            # Clean up previous data for this destination (unless resuming)
            if skip_cleanup:
                logger.info("Skipping cleanup (resume mode enabled)...")
            else:
                logger.info("Cleaning up previous data...")
                self.cleanup_previous_data(destination)
            
            result = {
                "destination": destination,
                "status": "pending",
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "video_path": None,
                "thumbnail_path": None,
                "youtube_video_id": None,
                "youtube_url": None,
                "errors": []
            }
            
            # Step 1: Generate itinerary (or reuse existing)
            logger.info("Step 1: Generating itinerary...")
            safe_destination = destination.replace(",", "__").replace(" ", "_")
            itinerary_path = self.data_dir / "long_videos" / "destinations" / f"{safe_destination}_itinerary.json"
            itinerary_data = None
            if reuse_existing:
                # Exact match
                if itinerary_path.exists():
                    logger.info(f"Reusing existing itinerary at {itinerary_path.name}")
                    try:
                        with open(itinerary_path, "r", encoding="utf-8") as f:
                            itinerary_data = json.load(f)
                    except Exception as e:
                        logger.warning(f"Failed to load existing itinerary: {e}")
                        itinerary_data = None
                # Fallback tolerant search
                if itinerary_data is None:
                    try:
                        dest_dir = self.data_dir / "long_videos" / "destinations"
                        candidates = sorted(dest_dir.glob("*_itinerary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                        key_tokens = [t.strip().lower().replace(" ", "") for t in destination.split(",")]
                        for cand in candidates:
                            name_key = cand.name.lower().replace("_", "").replace("__", "")
                            if all(t in name_key for t in key_tokens if t):
                                logger.info(f"Reusing nearest itinerary match: {cand.name}")
                                with open(cand, "r", encoding="utf-8") as f:
                                    itinerary_data = json.load(f)
                                break
                    except Exception as e:
                        logger.warning(f"Itinerary fallback search failed: {e}")
                        itinerary_data = None
            if itinerary_data is None:
                itinerary_data = self.itinerary_generator.generate_itinerary(destination, max_duration_minutes)
            
            # Validate and fix itinerary
            is_valid, fixed_itinerary, errors = self.error_handler.validate_and_fix_itinerary(
                itinerary_data, destination, max_retries=3
            )
            
            if not is_valid:
                logger.error(f"Itinerary validation failed: {errors}")
                result["errors"].extend(errors)
                if not self.error_handler.should_proceed_with_errors(errors, "itinerary"):
                    result["status"] = "failed"
                    result["completed_at"] = datetime.now().isoformat()
                    return result
            
            itinerary_data = fixed_itinerary
            self.itinerary_generator.save_itinerary(itinerary_data, destination)
            
            # Step 2: Generate script (or reuse existing)
            logger.info("Step 2: Generating script...")
            scripts_dir = Path(settings_long.SCRIPTS_DIR)
            scripts_dir.mkdir(parents=True, exist_ok=True)
            safe_name = destination.replace(",", "__").replace(" ", "_")
            script_path = scripts_dir / f"{safe_name}_script.json"
            script_data = None
            if reuse_existing:
                if script_path.exists():
                    logger.info(f"Reusing existing script at {script_path.name}")
                    try:
                        with open(script_path, "r", encoding="utf-8") as f:
                            script_data = json.load(f)
                    except Exception as e:
                        logger.warning(f"Failed to load existing script: {e}")
                        script_data = None
                if script_data is None:
                    try:
                        candidates = sorted(scripts_dir.glob("*_script.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                        key_tokens = [t.strip().lower().replace(" ", "") for t in destination.split(",")]
                        for cand in candidates:
                            name_key = cand.name.lower().replace("_", "").replace("__", "")
                            if all(t in name_key for t in key_tokens if t):
                                logger.info(f"Reusing nearest script match: {cand.name}")
                                with open(cand, "r", encoding="utf-8") as f:
                                    script_data = json.load(f)
                                break
                    except Exception as e:
                        logger.warning(f"Script fallback search failed: {e}")
                        script_data = None
            if script_data is None:
                script_data = self.script_generator.generate_script(itinerary_data)
            
            # Validate and fix script
            is_valid, fixed_script, errors = self.error_handler.validate_and_fix_script(
                script_data, itinerary_data, destination, max_retries=3
            )
            
            if not is_valid:
                logger.error(f"Script validation failed: {errors}")
                result["errors"].extend(errors)
                if not self.error_handler.should_proceed_with_errors(errors, "script"):
                    result["status"] = "failed"
                    result["completed_at"] = datetime.now().isoformat()
                    return result
            
            script_data = fixed_script
            self.script_generator.save_script(script_data, destination)
            
            # Step 3: Generate itinerary introduction voiceover (reuse if available in resume mode)
            logger.info("Step 3: Generating itinerary introduction...")
            introduction_voiceover_path = None
            introduction_text = script_data.get('itinerary_introduction', '')
            
            if introduction_text:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                introduction_voiceover_path = self.voiceovers_dir / f"{safe_destination}_introduction_voiceover.mp3"
                
                if reuse_existing and introduction_voiceover_path.exists():
                    logger.info(f"Reusing existing introduction voiceover: {introduction_voiceover_path.name}")
                else:
                    logger.info("Generating introduction voiceover...")
                    success = self.voiceover_generator.generate_voiceover(
                        introduction_text,
                        introduction_voiceover_path
                    )
                    
                    if success and introduction_voiceover_path.exists():
                        logger.info(f"✅ Generated introduction voiceover: {introduction_voiceover_path.name}")
                    else:
                        logger.warning("Failed to generate introduction voiceover, continuing without it")
                        introduction_voiceover_path = None
            else:
                logger.info("No itinerary introduction found in script, skipping")
            
            # Step 4: Estimate total duration for music selection (use script estimates)
            logger.info("Step 4: Estimating total video duration for music selection...")
            script_days = script_data.get('days', [])
            itinerary = itinerary_data.get('itinerary', [])
            
            # Estimate total voiceover duration from script data
            total_voiceover_duration = 0.0
            for script_day in script_days:
                estimated_duration = script_day.get('estimated_voiceover_seconds', 0)
                if estimated_duration:
                    total_voiceover_duration += estimated_duration
                else:
                    total_voiceover_duration += 90.0  # Default 90 seconds per day
            
            # Add introduction duration if exists
            if introduction_voiceover_path and introduction_voiceover_path.exists():
                try:
                    from core.utils.ffmpeg_helper import get_ffprobe_path
                    import subprocess
                    ffprobe_path = get_ffprobe_path()
                    probe_cmd = [
                        ffprobe_path,
                        '-v', 'error',
                        '-show_entries', 'format=duration',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        str(introduction_voiceover_path)
                    ]
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                    if probe_result.returncode == 0:
                        total_voiceover_duration += float(probe_result.stdout.strip())
                    else:
                        total_voiceover_duration += 30.0  # Default 30 seconds for introduction
                except Exception:
                    total_voiceover_duration += 30.0  # Default 30 seconds for introduction
            
            # PHASE 1.1: Select ONE music track for entire video (music consistency)
            logger.info("Selecting background music for entire video (music consistency)...")
            shared_music_path = self.audio_mixer.get_background_music(total_voiceover_duration)
            if shared_music_path:
                logger.info(f"✅ Selected shared background music: {shared_music_path.name} (will be used for all days)")
            else:
                logger.warning("No background music found, videos will use voiceover only")
            
            # Step 5: Process each day completely (voiceover → images → audio → video) and compile incrementally
            logger.info("Step 5: Processing each day completely (voiceover → images → audio → video) and compiling incrementally...")
            day_video_paths = {}
            completed_days = []  # Track completed days for cumulative naming
            cumulative_video_path = None  # Track cumulative video (day1+day2+day3+...)
            
            process_day_set = set(process_days) if process_days else None
            active_days = [
                day for day in itinerary
                if not process_day_set or day.get('day_number') in process_day_set
            ]
            
            if not active_days:
                logger.error("No days selected for processing (check process_days filter)")
                result["status"] = "failed"
                result["errors"].append("No days selected for processing")
                result["completed_at"] = datetime.now().isoformat()
                return result
            
            active_day_numbers = [day.get('day_number', 0) for day in active_days]
            
            # Process each day: voiceover → images → audio mixing → video assembly → compile with previous days (DAY-BY-DAY)
            for day in active_days:
                day_number = day.get('day_number', 0)
                scenes = day.get('scenes', [])
                
                logger.info("=" * 60)
                logger.info(f"PROCESSING DAY {day_number} - Complete Pipeline (Day-by-Day)")
                logger.info("=" * 60)
                
                # Find corresponding script day
                script_day = next((d for d in script_days if d.get('day_number') == day_number), None)
                if not script_day:
                    logger.warning(f"No script data found for Day {day_number}, skipping")
                    continue
                
                # 5a. Generate voiceover for this day (FIRST - needed for duration estimation)
                logger.info(f"Step 5a: Generating voiceover for Day {day_number}...")
                voiceover_path = self.voiceover_generator.generate_voiceover_for_day(
                    script_day, destination, self.voiceovers_dir
                )
                
                if not voiceover_path or not voiceover_path.exists():
                    logger.error(f"❌ Failed to generate voiceover for Day {day_number}, skipping day")
                    continue
                
                logger.info(f"✅ Generated voiceover for Day {day_number}: {voiceover_path.name}")
                
                # Get voiceover duration (prefer actual file measurement over script estimate)
                estimated_voiceover_seconds = script_day.get('estimated_voiceover_seconds')
                voiceover_duration = None
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
                except Exception as e:
                    logger.warning(f"Failed to get voiceover duration for Day {day_number}: {e}")

                if not voiceover_duration or voiceover_duration <= 0:
                    # Fall back to script estimate if ffprobe fails
                    voiceover_duration = float(estimated_voiceover_seconds or 90.0)

                # Update script and itinerary metadata so downstream steps use the accurate duration
                script_day['estimated_voiceover_seconds'] = voiceover_duration
                day['voiceover_duration_seconds'] = voiceover_duration
                
                # Extract scene-level image prompts from script scenes (NEW - scene-based)
                script_scenes = script_day.get('scenes', [])
                
                # Extract day-specific location from day title (e.g., "DAY 1 – BENGALURU: ..." -> "Bengaluru")
                day_title = day.get('title', '')
                day_location = None
                if day_title:
                    # Parse day title format: "DAY X – LOCATION: Theme" or "DAY X – LOCATION & LOCATION2: Theme"
                    # Extract location(s) after "DAY X – " and before ":"
                    match = re.search(r'DAY\s+\d+\s*[–-]\s*([^:]+):', day_title)
                    if match:
                        locations_str = match.group(1).strip()
                        # Take first location if multiple (e.g., "BENGALURU & MYSURU" -> "BENGALURU")
                        first_location = locations_str.split('&')[0].split('AND')[0].strip()
                        # Convert to title case for better search results
                        day_location = first_location.title() if first_location.isupper() else first_location
                        logger.info(f"Day {day_number} location: {day_location} (from title: {day_title})")
                    else:
                        logger.warning(f"Could not extract location from day title: {day_title}")
                
                # Extract specific locations and dishes from script day (for fallback)
                specific_locations = script_day.get('specific_locations', [])
                specific_dishes = script_day.get('specific_dishes', [])
                
                if specific_locations:
                    logger.info(f"Day {day_number} specific locations: {', '.join(specific_locations[:5])}")
                if specific_dishes:
                    logger.info(f"Day {day_number} specific dishes: {', '.join(specific_dishes[:5])}")
                
                # 5b. Generate images for this day (SCENE-BASED - using image_prompt from blueprint segments)
                logger.info(f"Step 5b: Generating images for Day {day_number} (voiceover {voiceover_duration:.2f}s, {len(script_scenes)} scenes)...")
                
                if script_scenes and any(scene.get('image_prompt') for scene in script_scenes):
                    # Use new scene-based method
                    day_image_results = self.image_generator.generate_images_for_day_with_scenes(
                        destination=destination,
                        day_number=day_number,
                        voiceover_duration_seconds=voiceover_duration,
                        scenes=script_scenes,  # Scene-level data with image_prompt
                        day_location=day_location,  # Day-specific city (e.g., "Kuta")
                        specific_locations=specific_locations,  # List of exact locations (fallback)
                        specific_dishes=specific_dishes  # List of exact dishes (fallback)
                    )
                else:
                    # Fallback to simple method if no scenes or image_prompts
                    logger.warning(f"Day {day_number} has no scenes with image_prompt, falling back to simple method")
                    day_keywords = script_day.get('image_keywords', [])
                    day_image_results = self.image_generator.generate_images_for_day_simple(
                        destination=destination,
                        day_number=day_number,
                        voiceover_duration_seconds=voiceover_duration,
                        day_keywords=day_keywords,
                        day_location=day_location,
                        specific_locations=specific_locations,
                        specific_dishes=specific_dishes,
                        specific_restaurants=script_day.get('specific_restaurants', [])
                    )
                
                if not day_image_results:
                    logger.warning(f"No images generated for Day {day_number}, skipping video assembly")
                    continue
                
                total_images = sum(len(images) for images in day_image_results.values())
                logger.info(f"✅ Generated {total_images} images for Day {day_number}")
                
                # 5c. Mix audio for this day (with shared music for consistency)
                logger.info(f"Step 5c: Mixing audio for Day {day_number}...")
                is_final_day = day_number == active_day_numbers[-1]
                transition_prompt = script_day.get('transition_prompt')
                
                mixed_audio_path = self.audio_mixer.mix_audio_for_day(
                    voiceover_path=voiceover_path,
                    day_number=day_number,
                    destination=destination,
                    music_path=shared_music_path,  # Use shared music for consistency
                    transition_prompt=transition_prompt,
                    is_final_day=is_final_day
                )
                
                # Fallback to voiceover if mixing failed
                if not mixed_audio_path or not mixed_audio_path.exists():
                    logger.warning(f"Audio mixing failed for Day {day_number}, using voiceover only")
                    mixed_audio_path = voiceover_path
                
                # 5d. Assemble video for this day
                logger.info(f"Step 5d: Assembling video for Day {day_number}...")
                day_video_path = self.day_assembler.assemble_day_video(
                    day_data=day,
                    script_data=script_data,
                    destination=destination,
                    images_dir=self.images_dir,
                    voiceover_path=mixed_audio_path,
                    voiceover_duration_seconds=voiceover_duration,
                )
                
                if day_video_path and day_video_path.exists():
                    day_video_paths[day_number] = day_video_path
                    file_size = day_video_path.stat().st_size / (1024 * 1024)  # MB
                    logger.info(f"✅ DAY {day_number} COMPLETE: {day_video_path.name} ({file_size:.2f} MB)")
                    logger.info(f"   Images: {total_images}, Audio: {mixed_audio_path.name}, Video: {day_video_path.name}")
                    
                    # INCREMENTAL COMPILATION: After Day 2+, compile with previous cumulative video
                    completed_days.append(day_number)
                    
                    # Only compile if we have 2+ days (Day 1 alone doesn't need compilation)
                    if len(completed_days) >= 2:
                        logger.info("")
                        logger.info("=" * 60)
                        logger.info(f"Step 5e: Compiling cumulative video (Days {'+'.join(map(str, completed_days))})...")
                        logger.info("=" * 60)
                        
                        # Create cumulative video name: day1+day2+day3+...
                        safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                        cumulative_name = "+".join([f"day{d}" for d in completed_days])
                        cumulative_output_path = self.videos_dir / f"{safe_destination}_{cumulative_name}.mp4"
                        
                        # Combine: previous cumulative video (if exists) + new day video
                        if cumulative_video_path and cumulative_video_path.exists():
                            # Incremental: existing cumulative + new day
                            videos_to_combine = {day_number: day_video_path}  # Only the new day
                            cumulative_video_path = self.final_assembler.combine_day_videos(
                                videos_to_combine, destination, None, cumulative_output_path, cumulative_video_path
                            )
                        else:
                            # First compilation (Day 1 + Day 2): combine both days
                            videos_to_combine = {d: day_video_paths[d] for d in completed_days}
                            cumulative_video_path = self.final_assembler.combine_day_videos(
                                videos_to_combine, destination, None, cumulative_output_path
                            )
                        
                        if cumulative_video_path and cumulative_video_path.exists():
                            cumulative_size = cumulative_video_path.stat().st_size / (1024 * 1024)  # MB
                            logger.info(f"✅ CUMULATIVE VIDEO COMPLETE: {cumulative_video_path.name} ({cumulative_size:.2f} MB)")
                            logger.info(f"   Contains: Days {'+'.join(map(str, completed_days))}")
                        else:
                            logger.error(f"❌ Failed to compile cumulative video for Days {'+'.join(map(str, completed_days))}")
                            # Continue with next day even if compilation failed
                        
                        logger.info("")
                    else:
                        # Day 1 only - save reference for next compilation
                        cumulative_video_path = day_video_path  # Reference to Day 1 video
                        logger.info("Day 1 complete - will compile after Day 2")
                        logger.info("")
                else:
                    logger.error(f"❌ Failed to assemble video for Day {day_number}, skipping")
                    continue
                
                logger.info(f"✅ Day {day_number} processing complete - moving to next day")
                logger.info("")
            
            if not day_video_paths:
                logger.error("Day video assembly failed - no videos generated")
                result["status"] = "failed"
                result["errors"].append("Day video assembly failed")
                result["completed_at"] = datetime.now().isoformat()
                return result
            
            logger.info(f"✅ All {len(day_video_paths)} day videos completed successfully!")
            
            # Final video is already compiled incrementally (cumulative_video_path)
            # Use the last cumulative video as the final video
            final_video_path = cumulative_video_path if cumulative_video_path and cumulative_video_path.exists() else None
            
            if not final_video_path:
                logger.error("Final video assembly failed - no cumulative video generated")
                result["status"] = "failed"
                result["errors"].append("Final video assembly failed")
                result["completed_at"] = datetime.now().isoformat()
                return result
            
            logger.info(f"✅ Final cumulative video: {final_video_path.name}")
            result["video_path"] = str(final_video_path)
            
            # PHASE 3.2: Analyze pacing consistency (optional, after assembly)
            pacing_metrics = {}
            pacing_warnings = []
            if self.pacing_analyzer and (not process_days or len(process_days) > 1):
                logger.info("Analyzing pacing consistency across days...")
                pacing_metrics, pacing_warnings = self.pacing_analyzer.analyze_pacing(
                    day_video_paths=day_video_paths,
                    day_image_results=None,  # Optional: pass if available for detailed analysis
                    script_data=script_data
                )
                
                if pacing_warnings:
                    logger.warning(f"Pacing warnings ({len(pacing_warnings)}):")
                    for warning in pacing_warnings:
                        logger.warning(f"  ⚠️  {warning}")
                else:
                    logger.info(f"✅ Pacing analysis passed - Overall score: {pacing_metrics.get('overall_pacing_score', 1.0):.2f}/1.0")
                
                # Log pacing metrics
                if pacing_metrics.get('day_duration_stats'):
                    stats = pacing_metrics['day_duration_stats']
                    logger.info(f"Pacing metrics: Avg={stats.get('average', 0):.1f}s, "
                               f"Variance={stats.get('variance_percent', 0):.1f}%, "
                               f"Score={pacing_metrics.get('overall_pacing_score', 1.0):.2f}/1.0")
            else:
                logger.info("Pacing analyzer not available, skipping pacing analysis")
            
            result["pacing_metrics"] = pacing_metrics
            result["pacing_warnings"] = pacing_warnings
            
            # Step 8: Quality validation (PHASE 3.1: Validate before upload)
            logger.info("Step 8: Validating video quality...")
            is_valid, quality_warnings, quality_metrics = self.quality_validator.validate_video(
                final_video_path,
                skip_black_frame_check=True  # Skip black frame check for speed (optional)
            )
            
            if quality_warnings:
                logger.warning(f"Quality validation warnings ({len(quality_warnings)}):")
                for warning in quality_warnings:
                    logger.warning(f"  ⚠️  {warning}")
            else:
                logger.info("✅ Video quality validation passed with no warnings")
            
            # Log quality metrics
            logger.info(f"Quality metrics: Duration={quality_metrics.get('duration_minutes', 0):.2f} min, "
                       f"Size={quality_metrics.get('file_size_mb', 0):.2f} MB, "
                       f"Resolution={quality_metrics.get('resolution', 'N/A')}")
            
            result["quality_metrics"] = quality_metrics
            result["quality_warnings"] = quality_warnings
            
            # Step 9: Generate thumbnail (PHASE 2.2: Story-optimized)
            logger.info("Step 9: Generating story-optimized thumbnail...")
            thumbnail_path = self.thumbnail_generator.generate_thumbnail(
                destination, itinerary_data, script_data=script_data  # PHASE 2.2: Pass script_data for story-based thumbnail
            )
            
            if thumbnail_path:
                result["thumbnail_path"] = str(thumbnail_path)
            
            # Step 10: Upload to YouTube
            if upload_to_youtube:
                logger.info("Step 10: Uploading to YouTube...")
                youtube_video_id = self.youtube_uploader.upload_video(
                    video_path=final_video_path,
                    destination=destination,
                    itinerary_data=itinerary_data,
                    thumbnail_path=thumbnail_path,
                    privacy_status=privacy_status
                )
                
                if youtube_video_id:
                    result["youtube_video_id"] = youtube_video_id
                    result["youtube_url"] = f"https://www.youtube.com/watch?v={youtube_video_id}"
                    logger.info(f"✅ Video uploaded to YouTube: {result['youtube_url']}")
                else:
                    logger.error("YouTube upload failed")
                    result["errors"].append("YouTube upload failed")
            
            # Step 11: Cleanup
            # IMPORTANT: Don't cleanup audio files until AFTER video assembly is complete
            # The video assembler needs the audio files during assembly
            logger.info("Step 11: Cleaning up temporary files...")
            self.final_assembler.cleanup_temp_files(day_video_paths, keep_final=True)
            # Cleanup audio files AFTER video assembly (they're needed during assembly)
            # self.audio_mixer.cleanup_temp_files(mixed_audio_files, keep_final=True)
            logger.info("Keeping mixed audio files (needed for video assembly)")
            
            # Update result
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            
            logger.info("=" * 60)
            logger.info("✅ LONG VIDEO GENERATION COMPLETED")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Video: {result['video_path']}")
            if result.get('youtube_url'):
                logger.info(f"YouTube: {result['youtube_url']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating video for destination: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            result["status"] = "failed"
            result["errors"].append(str(e))
            result["completed_at"] = datetime.now().isoformat()
            return result
    
    def _create_introduction_video(
        self,
        introduction_voiceover_path: Path,
        destination: str,
        itinerary_data: Dict[str, Any]
    ) -> Optional[Path]:
        """
        Create introduction video segment with itinerary overview
        
        Args:
            introduction_voiceover_path: Path to introduction voiceover file
            destination: Destination name
            itinerary_data: Itinerary data with days
            
        Returns:
            Path to introduction video or None if failed
        """
        try:
            logger.info("Creating introduction video segment...")
            
            # Get itinerary overview for visual display
            itinerary = itinerary_data.get('itinerary', [])
            day_count = len(itinerary)
            
            # Create a simple video with destination name and day overview
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            output_path = self.videos_dir / "temp_days" / f"{safe_destination}_introduction.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            from core.utils.ffmpeg_helper import get_ffmpeg_path, get_ffprobe_path
            ffmpeg_path = get_ffmpeg_path()
            ffprobe_path = get_ffprobe_path()
            
            # Get voiceover duration
            import subprocess
            probe_cmd = [
                ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(introduction_voiceover_path)
            ]
            
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.warning("Failed to get introduction voiceover duration")
                return None
            
            duration = float(result.stdout.strip())
            
            # Get resolution from day assembler
            resolution = self.day_assembler.resolution  # (1920, 1080)
            
            # Escape destination name for FFmpeg text filter
            destination_escaped = destination.replace("'", "\\'").replace(":", "\\:").replace(",", " ")
            
            # Create a simple colored background video with text overlay
            # Use FFmpeg to create a video with destination name and day overview
            cmd = [
                ffmpeg_path,
                '-y',
                '-f', 'lavfi',
                '-i', f'color=c=0x1a1a2e:s={resolution[0]}x{resolution[1]}:d={duration}',
                '-i', str(introduction_voiceover_path),
                '-vf', f"drawtext=text='{destination_escaped}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-50:borderw=3:bordercolor=black,"
                       f"drawtext=text='{day_count} Day Itinerary':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2+50:borderw=2:bordercolor=black",
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"✅ Created introduction video: {output_path.name}")
                return output_path
            else:
                logger.error(f"Failed to create introduction video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating introduction video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_video_for_trending_destination(
        self,
        destination: str,
        max_duration_minutes: int = 8,
        upload_to_youtube: bool = True,
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """
        Generate video for trending destination
        
        Args:
            destination: Destination name from trend detection
            max_duration_minutes: Maximum video duration in minutes (default: 8)
            upload_to_youtube: Whether to upload to YouTube (default: True)
            privacy_status: YouTube privacy status (default: "public")
            
        Returns:
            Dictionary with generation results
        """
        try:
            logger.info(f"Generating video for trending destination: {destination}")
            
            # Generate video
            result = self.generate_video_for_destination(
                destination=destination,
                max_duration_minutes=max_duration_minutes,
                upload_to_youtube=upload_to_youtube,
                privacy_status=privacy_status
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating video for trending destination: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "destination": destination,
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.now().isoformat()
            }


def main():
    """Test production pipeline"""
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing production pipeline for {test_destination}")
    
    # Initialize pipeline
    pipeline = ProductionPipelineLong()
    
    # Generate video
    result = pipeline.generate_video_for_destination(
        destination=test_destination,
        max_duration_minutes=8,
        upload_to_youtube=False,  # Don't upload during testing
        privacy_status="private"
    )
    
    # Print results
    logger.info("=" * 60)
    logger.info("GENERATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Status: {result['status']}")
    logger.info(f"Video: {result.get('video_path', 'N/A')}")
    logger.info(f"Thumbnail: {result.get('thumbnail_path', 'N/A')}")
    if result.get('youtube_url'):
        logger.info(f"YouTube: {result['youtube_url']}")
    if result.get('errors'):
        logger.error(f"Errors: {result['errors']}")


if __name__ == "__main__":
    main()


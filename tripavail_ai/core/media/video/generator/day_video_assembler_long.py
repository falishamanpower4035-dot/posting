#!/usr/bin/env python3
"""
Day Video Assembler for Long Videos
Generates temporary per-day videos from images and voiceover
Processes one day at a time (lighter server load)
Uses subprocess to call ffmpeg binary (not ffmpeg-python module)
"""

import os
import subprocess
import json
import tempfile
import math
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

# Import FFmpeg helper
from core.utils.ffmpeg_helper import get_ffmpeg_path, get_ffprobe_path


class DayVideoAssemblerLong:
    """
    Assembles per-day videos from images and voiceover
    Creates temporary video files for each day
    Uses subprocess to call ffmpeg binary
    """
    
    def __init__(self):
        # Video settings
        self.resolution = settings_long.LONG_VIDEO_RESOLUTION  # (1920, 1080)
        self.fps = settings_long.LONG_VIDEO_FPS  # 30
        self.aspect_ratio = settings_long.LONG_VIDEO_ASPECT_RATIO  # 1.78 (16:9)
        
        # Image duration settings
        self.image_duration_hero = settings_long.LONG_VIDEO_IMAGE_DURATION_HERO  # 5.0 seconds
        self.image_duration_standard = settings_long.LONG_VIDEO_IMAGE_DURATION_STANDARD  # 3.5 seconds
        self.image_duration_quick = settings_long.LONG_VIDEO_IMAGE_DURATION_QUICK  # 2.5 seconds
        self.fade_duration = settings_long.LONG_VIDEO_FADE_DURATION  # 0.8 seconds
        
        # Video codec settings
        self.video_codec = settings_long.VIDEO_CODEC  # "libx264"
        self.video_preset = settings_long.VIDEO_PRESET  # "medium"
        self.video_crf = settings_long.VIDEO_CRF  # 20
        self.video_pix_fmt = settings_long.VIDEO_PIX_FMT  # "yuv420p"
        
        # Output directory
        self.videos_dir = Path(settings_long.VIDEOS_DIR)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporary directory for day videos
        self.temp_dir = self.videos_dir / "temp_days"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Day Video Assembler Long initialized")
        logger.info(f"Resolution: {self.resolution[0]}x{self.resolution[1]}")
        logger.info(f"FPS: {self.fps}")
        logger.info(f"Aspect Ratio: {self.aspect_ratio}")
    
    def get_image_duration(self, scene_category: str, scene_order: int) -> float:
        """
        Get image duration based on scene category and order
        
        Args:
            scene_category: Scene category (arrival, attraction, food, stay, scenic, nightlife, transit)
            scene_order: Scene order (1, 2, 3, ...)
            
        Returns:
            Image duration in seconds
        """
        # Hero shots (first scene of day) get longer duration
        if scene_order == 1:
            return self.image_duration_hero
        
        # Attractions and scenic views get standard duration
        if scene_category in ['attraction', 'scenic']:
            return self.image_duration_standard
        
        # Food, stay, nightlife get quick duration
        if scene_category in ['food', 'stay', 'nightlife']:
            return self.image_duration_quick
        
        # Arrival and transit get standard duration
        return self.image_duration_standard
    
    def assemble_day_video(
        self,
        day_data: Dict[str, Any],
        script_data: Dict[str, Any],
        destination: str,
        images_dir: Path,
        voiceover_path: Optional[Path] = None,
        voiceover_duration_seconds: Optional[float] = None,
    ) -> Optional[Path]:
        """
        Assemble video for a single day
        
        Args:
            day_data: Day data from itinerary
            script_data: Script data with narration
            destination: Destination name
            images_dir: Directory containing images for this destination
            voiceover_path: Path to voiceover file (optional)
            
        Returns:
            Path to assembled day video or None if failed
        """
        try:
            day_number = day_data.get('day_number', 0)
            scenes = day_data.get('scenes', [])
            
            logger.info(f"Assembling video for day {day_number}...")
            
            # Get script data for this day
            script_days = script_data.get('days', [])
            script_day = next((d for d in script_days if d.get('day_number') == day_number), None)
            
            if not script_day:
                logger.error(f"No script data found for day {day_number}")
                return None
            
            # Get voiceover duration to calculate image durations
            voiceover_duration = 0.0
            duration_sources = []
            
            # Priority 1: explicit duration passed from pipeline
            if voiceover_duration_seconds and voiceover_duration_seconds > 0:
                voiceover_duration = float(voiceover_duration_seconds)
                duration_sources.append("pipeline")
            
            # Priority 2: script day metadata
            if voiceover_duration <= 0:
                script_duration = (
                    script_day.get("voiceover_duration_seconds")
                    or script_day.get("estimated_voiceover_seconds")
                )
                if script_duration:
                    voiceover_duration = float(script_duration)
                    duration_sources.append("script_metadata")
            
            # Priority 3: probe actual audio file (mixed or raw voiceover)
            if voiceover_duration <= 0 and voiceover_path and voiceover_path.exists():
                try:
                    ffprobe_path = get_ffprobe_path()
                    probe_cmd = [
                        ffprobe_path,
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        str(voiceover_path),
                    ]
                    probe_result = subprocess.run(
                        probe_cmd, capture_output=True, text=True, timeout=10
                    )
                    if probe_result.returncode == 0:
                        voiceover_duration = float(probe_result.stdout.strip())
                        duration_sources.append("ffprobe")
                except Exception as e:
                    logger.warning(f"Failed to get voiceover duration via ffprobe: {e}")
            
            if voiceover_duration > 0:
                logger.info(
                    f"Voiceover duration for day {day_number}: {voiceover_duration:.2f}s "
                    f"(source: {', '.join(duration_sources)})"
                )
            
            # SCENE-SYNCHRONIZED IMAGE COLLECTION: Use scene-specific folders if available
            # Structure: data/long_videos/images/Bali/day_1/scene_1/, scene_2/, etc.
            
            # Get script scenes for scene timing
            script_scenes = script_day.get('scenes', [])
            
            destination_variants = [
                destination,  # Original: "Bali, Indonesia"
                destination.replace(",", ""),  # "Bali Indonesia"
                destination.split(",")[0].strip(),  # "Bali"
                destination.replace(",", "_").replace(" ", "_"),  # "Bali_Indonesia"
            ]
            
            # Try to collect scene-specific images first
            scene_images_dict = {}  # Maps scene_order -> list of image paths
            day_dir = None
            
            for dest_variant in destination_variants:
                potential_day_dir = images_dir / dest_variant / f"day_{day_number}"
                if potential_day_dir.exists():
                    day_dir = potential_day_dir
                    break
            
            if day_dir and day_dir.exists():
                # Try scene folders first (scene_1, scene_2, etc.)
                scene_folders_found = False
                for script_scene in script_scenes:
                    scene_order = script_scene.get('order', 0)
                    scene_dir = day_dir / f"scene_{scene_order}"
                    if scene_dir.exists():
                        scene_folders_found = True
                        scene_imgs = sorted(list(scene_dir.glob("*.jpg")) + 
                                           list(scene_dir.glob("*.jpeg")) + 
                                           list(scene_dir.glob("*.png")))
                        scene_images_dict[scene_order] = scene_imgs
                        logger.debug(f"Found {len(scene_imgs)} images in scene_{scene_order}")
                
                if scene_folders_found:
                    logger.info(f"✅ Using SCENE-SYNCHRONIZED images from scene folders for Day {day_number}")
                    
                    # Also check "all" folder as fallback for scenes without images
                    all_dir = day_dir / "all"
                    all_images = []
                    if all_dir.exists():
                        all_images = sorted(list(all_dir.glob("*.jpg")) + 
                                          list(all_dir.glob("*.jpeg")) + 
                                          list(all_dir.glob("*.png")))
                        logger.debug(f"Found {len(all_images)} images in 'all' folder (fallback)")
                    
                    # Fill missing scenes with images from "all" folder
                    for script_scene in script_scenes:
                        scene_order = script_scene.get('order', 0)
                        if scene_order not in scene_images_dict or len(scene_images_dict[scene_order]) == 0:
                            if all_images:
                                # Take some images from "all" folder for this scene
                                images_needed = max(2, int(len(script_scenes) / 2))  # At least 2 per scene
                                scene_images_dict[scene_order] = all_images[:images_needed]
                                all_images = all_images[images_needed:]
                                logger.debug(f"Scene {scene_order}: Using {len(scene_images_dict[scene_order])} fallback images from 'all' folder")
                            else:
                                scene_images_dict[scene_order] = []
                else:
                    # No scene folders - use "all" folder or legacy structure
                    logger.info(f"⚠️  No scene folders found for Day {day_number}, using 'all' folder or legacy structure")
                    all_dir = day_dir / "all"
                    if all_dir.exists():
                        all_images = sorted(list(all_dir.glob("*.jpg")) + 
                                          list(all_dir.glob("*.jpeg")) + 
                                          list(all_dir.glob("*.png")))
                        logger.info(f"Found {len(all_images)} images in 'all' folder")
                        # Distribute evenly across scenes
                        if script_scenes and all_images:
                            images_per_scene = max(2, len(all_images) // len(script_scenes))
                            for i, script_scene in enumerate(script_scenes):
                                scene_order = script_scene.get('order', i + 1)
                                start_idx = i * images_per_scene
                                end_idx = start_idx + images_per_scene
                                scene_images_dict[scene_order] = all_images[start_idx:end_idx]
                        else:
                            # Fallback to sequential (no scene breakdown)
                            unique_all_images = all_images
                    else:
                        # FALLBACK: Try legacy category-based structure
                        logger.warning(f"Trying legacy category structure for day {day_number}...")
                        image_categories = ["attractions", "activities", "food_culture", "local_life", "scenic_views", "hotel_stay"]
                        all_destination_images = []
                        for category in image_categories:
                            category_dir = day_dir / category
                            if category_dir.exists():
                                category_images = sorted(list(category_dir.glob("*.jpg")) + 
                                                        list(category_dir.glob("*.jpeg")) + 
                                                        list(category_dir.glob("*.png")))
                                all_destination_images.extend(category_images)
                        
                        # Remove duplicates
                        seen_paths = set()
                        unique_all_images = []
                        for img_path in all_destination_images:
                            img_str = str(img_path)
                            if img_str not in seen_paths:
                                unique_all_images.append(img_path)
                                seen_paths.add(img_str)
                        
                        # Distribute evenly across scenes
                        if script_scenes and unique_all_images:
                            images_per_scene = max(2, len(unique_all_images) // len(script_scenes))
                            for i, script_scene in enumerate(script_scenes):
                                scene_order = script_scene.get('order', i + 1)
                                start_idx = i * images_per_scene
                                end_idx = start_idx + images_per_scene
                                scene_images_dict[scene_order] = unique_all_images[start_idx:end_idx]
                        else:
                            unique_all_images = unique_all_images
            
            # FALLBACK: If no day-specific directory at all, try legacy structure
            if not day_dir or not day_dir.exists():
                logger.warning(f"No day-specific directory found for day {day_number}, trying legacy structure...")
                all_destination_images = []
                for dest_variant in destination_variants:
                    image_categories = ["attractions", "activities", "food_culture", "local_life", "scenic_views", "hotel_stay"]
                    for category in image_categories:
                        category_dir = images_dir / dest_variant / category
                        if category_dir.exists():
                            category_images = sorted(list(category_dir.glob("*.jpg")) + 
                                                    list(category_dir.glob("*.jpeg")) + 
                                                    list(category_dir.glob("*.png")))
                            all_destination_images.extend(category_images)
                
                # Remove duplicates
                seen_paths = set()
                unique_all_images = []
                for img_path in all_destination_images:
                    img_str = str(img_path)
                    if img_str not in seen_paths:
                        unique_all_images.append(img_path)
                        seen_paths.add(img_str)
                
                # Distribute evenly across scenes
                if script_scenes and unique_all_images:
                    images_per_scene = max(2, len(unique_all_images) // len(script_scenes))
                    for i, script_scene in enumerate(script_scenes):
                        scene_order = script_scene.get('order', i + 1)
                        start_idx = i * images_per_scene
                        end_idx = start_idx + images_per_scene
                        scene_images_dict[scene_order] = unique_all_images[start_idx:end_idx]
                else:
                    unique_all_images = unique_all_images
            
            # Check if we have scene-based images
            total_scene_images = sum(len(imgs) for imgs in scene_images_dict.values())
            if total_scene_images > 0 and scene_images_dict:
                logger.info(f"✅ Found {total_scene_images} scene-synchronized images across {len(scene_images_dict)} scenes for Day {day_number}")
                # Use scene-based assembly (will be handled below)
                use_scene_assembly = True
            else:
                # Fallback to sequential assembly
                logger.warning(f"⚠️  No scene images found, using sequential fallback")
                unique_all_images = []
                for scene_imgs in scene_images_dict.values():
                    unique_all_images.extend(scene_imgs)
                if not unique_all_images:
                    logger.error(f"No images found for Day {day_number} of {destination}")
                    return None
                use_scene_assembly = False
            
            if not scene_images_dict and not unique_all_images:
                logger.error(f"No images found for Day {day_number} of {destination}")
                return None
            
            # SCENE-SYNCHRONIZED IMAGE DURATION CALCULATION
            if use_scene_assembly and scene_images_dict and script_scenes:
                # Distribute voiceover duration across scenes based on scene narration length
                # Strategy: Use word count per scene to determine proportional timing, fallback to even division
                logger.info(f"📹 Using SCENE-SYNCHRONIZED assembly for Day {day_number} ({len(script_scenes)} scenes)")
                
                if voiceover_duration > 0:
                    # Calculate scene durations based on narration word counts (more accurate timing)
                    scene_word_counts = []
                    total_words = 0
                    
                    for script_scene in sorted(script_scenes, key=lambda s: s.get('order', 0)):
                        scene_narration = script_scene.get('scene_narration', '')
                        if scene_narration:
                            word_count = len(scene_narration.split())
                            scene_word_counts.append((script_scene.get('order', 0), word_count))
                            total_words += word_count
                        else:
                            # Fallback: estimate based on scene title/description
                            scene_word_counts.append((script_scene.get('order', 0), 50))  # Default 50 words
                            total_words += 50
                    
                    # If we have word counts, use proportional distribution
                    if total_words > 0:
                        scene_durations = {}
                        for scene_order, word_count in scene_word_counts:
                            # Proportional duration based on word count
                            scene_duration = (word_count / total_words) * voiceover_duration
                            scene_durations[scene_order] = scene_duration
                        
                        logger.debug(f"Scene durations based on word counts: {[(k, f'{v:.2f}s') for k, v in sorted(scene_durations.items())]}")
                    else:
                        # Fallback: divide voiceover evenly across scenes
                        duration_per_scene = voiceover_duration / len(script_scenes)
                        scene_durations = {scene.get('order', i+1): duration_per_scene 
                                         for i, scene in enumerate(sorted(script_scenes, key=lambda s: s.get('order', 0)))}
                        logger.debug(f"Scene durations evenly distributed: {duration_per_scene:.2f}s per scene")
                    
                    image_paths = []
                    image_durations = []
                    
                    # Process each scene in order
                    for script_scene in sorted(script_scenes, key=lambda s: s.get('order', 0)):
                        scene_order = script_scene.get('order', 0)
                        scene_imgs = scene_images_dict.get(scene_order, [])
                        duration_per_scene = scene_durations.get(scene_order, voiceover_duration / len(script_scenes))
                        
                        if scene_imgs:
                            # Divide scene duration evenly across its images
                            images_in_scene = len(scene_imgs)
                            duration_per_image_in_scene = duration_per_scene / images_in_scene
                            min_duration = 1.0
                            duration_per_image_in_scene = max(min_duration, duration_per_image_in_scene)
                            
                            # Add scene images with their durations
                            image_paths.extend(scene_imgs)
                            scene_image_durations = [duration_per_image_in_scene] * images_in_scene
                            
                            # Fine-tune last image in scene to match scene duration exactly
                            total_scene_duration = sum(scene_image_durations)
                            if abs(total_scene_duration - duration_per_scene) > 0.01:
                                duration_diff = duration_per_scene - total_scene_duration
                                scene_image_durations[-1] = max(min_duration, scene_image_durations[-1] + duration_diff)
                            
                            image_durations.extend(scene_image_durations)
                            
                            logger.debug(
                                f"  Scene {scene_order}: {images_in_scene} images, "
                                f"{duration_per_image_in_scene:.2f}s per image, "
                                f"{duration_per_scene:.2f}s total"
                            )
                    
                    # Fine-tune last image of entire video to match voiceover exactly
                    total_image_duration = sum(image_durations)
                    if abs(total_image_duration - voiceover_duration) > 0.01:
                        duration_diff = voiceover_duration - total_image_duration
                        image_durations[-1] = max(1.0, image_durations[-1] + duration_diff)
                        total_image_duration = sum(image_durations)
                    
                    logger.info(
                        f"✅ Scene-synchronized: {len(image_paths)} images across {len(script_scenes)} scenes, "
                        f"total duration: {total_image_duration:.2f}s (voiceover: {voiceover_duration:.2f}s)"
                    )
                else:
                    # Fallback: use default duration per scene
                    logger.warning(f"No voiceover duration available, using default 2.5s per image")
                    target_seconds_per_image = 2.5
                    image_paths = []
                    image_durations = []
                    for script_scene in sorted(script_scenes, key=lambda s: s.get('order', 0)):
                        scene_order = script_scene.get('order', 0)
                        scene_imgs = scene_images_dict.get(scene_order, [])
                        image_paths.extend(scene_imgs)
                        image_durations.extend([target_seconds_per_image] * len(scene_imgs))
            else:
                # FALLBACK: Sequential assembly (all images sequentially)
                logger.info(f"📹 Using SEQUENTIAL assembly for Day {day_number} (no scene breakdown)")
                image_paths = unique_all_images
                
                if voiceover_duration > 0 and len(image_paths) > 0:
                    # Calculate duration per image: divide voiceover evenly across all images
                    duration_per_image = voiceover_duration / len(image_paths)
                    min_duration = 1.0  # Minimum 1s per image for visual variety
                    duration_per_image = max(min_duration, duration_per_image)
                    
                    # Apply calculated duration to all images
                    image_durations = [duration_per_image] * len(image_paths)
                    total_image_duration = sum(image_durations)
                    
                    # Fine-tune last image only if needed for exact match (minimal adjustment)
                    if abs(total_image_duration - voiceover_duration) > 0.01:
                        duration_diff = voiceover_duration - total_image_duration
                        image_durations[-1] = max(min_duration, image_durations[-1] + duration_diff)
                        total_image_duration = sum(image_durations)
                    
                    logger.info(
                        f"Using ALL {len(image_paths)} images sequentially for Day {day_number} "
                        f"({duration_per_image:.2f}s per image - distributed evenly across {voiceover_duration:.2f}s voiceover)"
                    )
                    logger.info(
                        f"Total image duration: {total_image_duration:.2f}s, "
                        f"Voiceover duration: {voiceover_duration:.2f}s"
                    )
                else:
                    # Fallback: use default duration when voiceover duration not available
                    target_seconds_per_image = 2.5
                    image_durations = [target_seconds_per_image] * len(image_paths)
                    logger.warning(
                        f"No voiceover duration available, using default {target_seconds_per_image}s per image "
                        f"for all {len(image_paths)} images"
                    )
            
            if not image_paths:
                logger.error(f"No images to use for day {day_number}")
                return None
            
            # Create output path
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            output_path = self.temp_dir / f"{safe_destination}_day_{day_number}.mp4"
            
            # Build FFmpeg command using subprocess
            success = self._build_and_run_ffmpeg_command(
                image_paths,
                image_durations,
                output_path,
                voiceover_path
            )
            
            if success:
                logger.info(f"✅ Assembled day {day_number} video: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to assemble day {day_number} video")
                return None
                
        except Exception as e:
            logger.error(f"Error assembling day {day_number} video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _map_scene_category_to_image_category(self, scene_category: str) -> List[str]:
        """
        Map scene category to image generator category
        
        Args:
            scene_category: Scene category (arrival, attraction, food, stay, scenic, nightlife, transit)
            
        Returns:
            List of possible image categories to search
        """
        # Map scene categories to image generator categories
        category_map = {
            "arrival": ["scenic_views", "local_life"],  # Airport, arrival scenes
            "attraction": ["attractions", "scenic_views"],  # Attractions and activities
            "food": ["food_culture", "local_life"],  # Food and culture
            "stay": ["hotel_stay", "scenic_views"],  # Hotels, accommodations (NEW: hotel_stay category)
            "scenic": ["scenic_views", "attractions"],  # Scenic views
            "nightlife": ["local_life", "activities"],  # Nightlife, local life
            "transit": ["scenic_views", "local_life"],  # Transit, travel scenes
        }
        
        # Return mapped categories, or default to attractions if not found
        return category_map.get(scene_category, ["attractions", "activities", "scenic_views"])
    
    def _find_scene_images(
        self,
        images_dir: Path,
        destination: str,
        category: str,
        scene_order: int,
        keywords: List[str]
    ) -> List[Path]:
        """
        Find images for a scene
        
        Args:
            images_dir: Base images directory
            destination: Destination name
            category: Scene category (arrival, attraction, food, stay, scenic, nightlife, transit)
            scene_order: Scene order
            keywords: Image keywords
            
        Returns:
            List of image paths
        """
        try:
            # Map scene category to image generator categories
            image_categories = self._map_scene_category_to_image_category(category)
            
            # Clean destination name (handle commas, spaces)
            safe_destination = destination.replace(",", "").replace(" ", "_")
            
            # Try each mapped category until we find images
            all_images = []
            for image_category in image_categories:
                # Try multiple destination name formats
                destination_variants = [
                    destination,  # Original: "Bali, Indonesia"
                    destination.replace(",", ""),  # "Bali Indonesia"
                    destination.split(",")[0].strip(),  # "Bali"
                    safe_destination,  # "Bali_Indonesia"
                ]
                
                for dest_variant in destination_variants:
                    # Look for images in destination/category directory
                    category_dir = images_dir / dest_variant / image_category
                    
                    if category_dir.exists():
                        # Find images matching scene order or keywords
                        scene_images = sorted(category_dir.glob(f"*_scene_{scene_order}_*.jpg"))
                        if not scene_images:
                            scene_images = sorted(category_dir.glob(f"*_scene_{scene_order}_*.jpeg"))
                        if not scene_images:
                            scene_images = sorted(category_dir.glob(f"*_scene_{scene_order}_*.png"))
                        
                        if scene_images:
                            all_images.extend(scene_images)
                        else:
                            # Fallback: get any images from category directory
                            category_images = sorted(list(category_dir.glob("*.jpg")) + 
                                                    list(category_dir.glob("*.jpeg")) + 
                                                    list(category_dir.glob("*.png")))
                            all_images.extend(category_images)
            
            # Remove duplicates (by path)
            unique_images = []
            seen_paths = set()
            for img_path in all_images:
                if str(img_path) not in seen_paths:
                    unique_images.append(img_path)
                    seen_paths.add(str(img_path))
            
            # If we found images, return all unique images for this scene
            # The caller will distribute them properly across scenes
            if unique_images:
                # Return all unique images (will be distributed by caller)
                logger.info(f"Found {len(unique_images)} unique images for {destination} - {category} (scene {scene_order})")
                # Return up to 10 images per scene (caller will distribute properly)
                return unique_images[:10]
            
            # If no images found, try searching in parent directory
            logger.warning(f"No images found for {destination} - {category} (scene {scene_order})")
            logger.warning(f"Searched categories: {image_categories}")
            logger.warning(f"Searched destination variants: {destination_variants}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error finding scene images: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _build_and_run_ffmpeg_command(
        self,
        image_paths: List[Path],
        image_durations: List[float],
        output_path: Path,
        voiceover_path: Optional[Path] = None
    ) -> bool:
        """
        Build and run FFmpeg command to create video using subprocess
        
        Args:
            image_paths: List of image paths
            image_durations: List of image durations (seconds)
            output_path: Output video path
            voiceover_path: Path to voiceover file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if len(image_paths) != len(image_durations):
                logger.error("Image paths and durations mismatch")
                return False
            
            if not image_paths:
                logger.error("No images provided")
                return False
            
            # Ensure output directory exists before FFmpeg tries to write
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Calculate total video duration
            total_duration = sum(image_durations)
            logger.info(f"Total image duration: {total_duration:.2f}s for {len(image_paths)} images")
            
            # Check if we have audio
            has_audio = voiceover_path and voiceover_path.exists()
            vo_duration = total_duration
            
            if has_audio:
                # Get voiceover duration using ffprobe or ffmpeg
                try:
                    ffprobe_path = get_ffprobe_path()
                    # Check if we're using FFmpeg as fallback (same path as FFmpeg)
                    ffmpeg_path = get_ffmpeg_path()
                    if ffprobe_path == ffmpeg_path:
                        # Use FFmpeg syntax instead of FFprobe
                        probe_cmd = [
                            ffprobe_path,
                            '-i', str(voiceover_path),
                            '-hide_banner',
                            '-f', 'null',
                            '-'
                        ]
                        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                        # Parse duration from stderr output like "Duration: 00:00:42.87"
                        if probe_result.returncode == 0 or 'Duration:' in probe_result.stderr:
                            import re
                            duration_match = re.search(r'Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)', probe_result.stderr)
                            if duration_match:
                                hours, minutes, seconds = duration_match.groups()
                                vo_duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                            else:
                                raise ValueError("Could not parse duration from FFmpeg output")
                        else:
                            raise ValueError("FFmpeg probe failed")
                    else:
                        # Use FFprobe syntax
                        probe_cmd = [
                            ffprobe_path,
                            '-v', 'error',
                            '-show_entries', 'format=duration',
                            '-of', 'default=noprint_wrappers=1:nokey=1',
                            str(voiceover_path)
                        ]
                        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                        if probe_result.returncode == 0:
                            vo_duration = float(probe_result.stdout.strip())
                        else:
                            raise ValueError("FFprobe failed")
                    
                    logger.info(f"Voiceover duration: {vo_duration:.2f}s, Image duration: {total_duration:.2f}s")
                    
                    if vo_duration > total_duration:
                        duration_diff = vo_duration - total_duration
                        if image_durations:
                            image_durations[-1] += duration_diff
                            total_duration = sum(image_durations)
                            logger.info(f"Extended last image duration by {duration_diff:.2f}s to match voiceover")
                    elif vo_duration < total_duration:
                        excess = total_duration - vo_duration
                        if image_durations:
                            image_durations[-1] = max(0.5, image_durations[-1] - excess)
                            total_duration = sum(image_durations)
                            logger.info(f"Trimmed last image duration by {excess:.2f}s to match voiceover")
                except Exception as e:
                    logger.warning(f"Error getting voiceover duration: {e}")
                    vo_duration = total_duration
            else:
                # No audio found
                if not voiceover_path:
                    logger.error(f"Voiceover path not provided for day video")
                elif not voiceover_path.exists():
                    logger.error(f"Voiceover file not found: {voiceover_path}")
                    logger.error(f"Expected path: {voiceover_path}")
                    if voiceover_path.parent.exists():
                        logger.error(f"Directory exists: {voiceover_path.parent}")
                        files_in_dir = list(voiceover_path.parent.glob('*.mp3'))
                        logger.error(f"Files in directory ({len(files_in_dir)}): {[f.name for f in files_in_dir[:10]]}")
                    else:
                        logger.error(f"Directory does not exist: {voiceover_path.parent}")
            
            # Build filter_complex string to create video from images with specific durations
            # We'll create individual video segments for each image and concatenate them
            filter_parts = []
            input_args = []
            
            # Create video segments for each image with Ken Burns zoom effects
            # First image: static (no zoom) for YouTube thumbnail selection
            freeze_duration = 1.5  # Freeze first image for 1.5 seconds
            
            for i, (img_path, duration) in enumerate(zip(image_paths, image_durations)):
                # Use absolute path - FFmpeg handles Windows paths if we use forward slashes
                # or if we quote the path properly
                abs_img_path = str(img_path.absolute())
                # On Windows, convert backslashes to forward slashes for FFmpeg
                import platform
                if platform.system() == 'Windows':
                    abs_img_path = abs_img_path.replace('\\', '/')
                # Loop input image for duration; set SAR later in filter graph
                input_args.extend(['-loop', '1', '-t', str(duration), '-i', abs_img_path])
                
                # Scale and pad each image
                # Images are preprocessed to exactly 1920x1080, so no padding needed
                # Direct scale to ensure correct resolution (no aspect ratio changes needed)
                if i == 0:
                    # First image: NO zoom effect - freeze frame for YouTube thumbnail
                    # Static image (no zoom, no motion) for better thumbnail selection
                    # Images are already 1920x1080, so just ensure correct size and SAR
                    filter_parts.append(
                        f"[{i}:v]scale={self.resolution[0]}:{self.resolution[1]},"
                        f"setsar=1:1,setpts=PTS-STARTPTS,fps={self.fps}[v{i}]"
                    )
                else:
                    # Other images: Subtle Ken Burns zoom for dynamic feel
                    # Calculate frames for zoom effect
                    zoom_frames = int(duration * self.fps)
                    zoom_filter = f"zoompan=z='min(zoom+0.001,1.15)':d={zoom_frames}:s={self.resolution[0]}x{self.resolution[1]}:fps={self.fps}"
                    # Images are already 1920x1080, apply zoom with correct size
                    filter_parts.append(
                        f"[{i}:v]scale={self.resolution[0]}:{self.resolution[1]},"
                        f"setsar=1:1,{zoom_filter}[v{i}]"
                    )
            
            # Apply crossfade transitions between images (replaces hard concat cuts)
            if len(image_paths) == 1:
                # Single image, no transition needed
                filter_parts.append("[v0]copy[outv]")
            else:
                # Start with first image (frozen for thumbnail selection)
                current_label = "[v0]"
                
                for i in range(1, len(image_paths)):
                    next_label = f"[v{i}]"
                    output_label = f"[vt{i}]" if i < len(image_paths) - 1 else "[outv]"
                    
                    # Calculate offset for crossfade
                    # Use average image duration for consistent spacing
                    avg_image_duration = image_durations[0] if image_durations else 2.5
                    if i == 1:
                        # First transition: starts after freeze duration (1.5s)
                        offset = freeze_duration
                    else:
                        # Subsequent transitions: spaced by (image_duration - fade_duration)
                        # This ensures smooth transitions without gaps
                        offset = freeze_duration + (avg_image_duration - self.fade_duration) * (i - 1)
                    
                    # Apply crossfade transition (smooth left fade)
                    filter_parts.append(
                        f"{current_label}{next_label}xfade=transition=smoothleft:duration={self.fade_duration}:offset={offset}{output_label}"
                    )
                    
                    current_label = output_label
            
            filter_complex = ';'.join(filter_parts)
            
            # Build FFmpeg command
            ffmpeg_path = get_ffmpeg_path()
            if has_audio:
                cmd = [
                    ffmpeg_path,
                    '-y',  # Overwrite output
                ] + input_args + [
                    '-i', str(voiceover_path),  # Audio input (last input)
                    '-filter_complex', filter_complex,
                    '-map', '[outv]',  # Map concatenated video
                    '-map', f'{len(image_paths)}:a',  # Map audio from voiceover input
                    '-c:v', self.video_codec,
                    '-preset', self.video_preset,
                    '-crf', str(self.video_crf),
                    '-pix_fmt', self.video_pix_fmt,
                    '-c:a', 'aac',
                    '-b:a', '320k',
                    '-shortest',  # End when shortest stream ends
                    str(output_path)
                ]
                logger.info(f"Adding audio from: {voiceover_path}")
            else:
                cmd = [
                    ffmpeg_path,
                    '-y',  # Overwrite output
                ] + input_args + [
                    '-filter_complex', filter_complex,
                    '-map', '[outv]',  # Map concatenated video
                    '-c:v', self.video_codec,
                    '-preset', self.video_preset,
                    '-crf', str(self.video_crf),
                    '-pix_fmt', self.video_pix_fmt,
                    str(output_path)
                ]
                logger.warning("Creating video without audio (no voiceover file found)")
            
            logger.info(f"Running FFmpeg command for day video (duration: {total_duration:.2f}s, {len(image_paths)} images, {'with audio' if has_audio else 'no audio'})...")
            logger.debug(f"FFmpeg command (first 25 args): {' '.join(cmd[:25])}...")
            logger.debug(f"Total command length: {len(cmd)} arguments")
            
            # Run FFmpeg
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            except subprocess.TimeoutExpired:
                logger.error(f"FFmpeg command timed out after 600 seconds")
                return False
            except Exception as e:
                logger.error(f"Error running FFmpeg: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
            
            if result.returncode == 0:
                if output_path.exists():
                    file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                    # Verify video has audio if we added it
                    if has_audio:
                        try:
                            # Check if video has audio stream
                            ffprobe_path = get_ffprobe_path()
                            probe_cmd = [
                                ffprobe_path,
                                '-v', 'error',
                                '-select_streams', 'a',
                                '-show_entries', 'stream=codec_type,codec_name',
                                '-of', 'json',
                                str(output_path)
                            ]
                            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                            if probe_result.returncode == 0:
                                import json
                                probe_data = json.loads(probe_result.stdout)
                                if 'streams' in probe_data and len(probe_data['streams']) > 0:
                                    logger.info(f"✅ Created day video with audio: {output_path} ({file_size:.2f} MB)")
                                else:
                                    logger.warning(f"⚠️ Created day video but audio stream not found: {output_path}")
                                    logger.warning(f"FFmpeg stdout: {result.stdout[-500:]}")
                        except Exception as e:
                            logger.warning(f"Could not verify audio in video: {e}")
                    else:
                        logger.info(f"✅ Created day video (no audio): {output_path} ({file_size:.2f} MB)")
                    return True
                else:
                    logger.error(f"Video file not created: {output_path}")
                    logger.error(f"FFmpeg stdout: {result.stdout[-500:]}")
                    logger.error(f"FFmpeg stderr: {result.stderr[-500:]}")
                    return False
            else:
                logger.error(f"FFmpeg error (return code {result.returncode})")
                logger.error(f"FFmpeg stdout: {result.stdout[-1000:]}")
                logger.error(f"FFmpeg stderr: {result.stderr[-1000:]}")
                # Log command for debugging (first and last parts)
                logger.debug(f"FFmpeg command (first 10 args): {' '.join(cmd[:10])}...")
                logger.debug(f"FFmpeg command (last 5 args): ...{' '.join(cmd[-5:])}")
                return False
                
        except Exception as e:
            logger.error(f"Error building or running FFmpeg command: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


def main():
    """Test day video assembler"""
    from core.content.generation.script_generator_long import ScriptGeneratorLong
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    from core.media.audio.voiceover_generator_long import VoiceoverGeneratorLong
    from core.media.audio.audio_mixer_long import AudioMixerLong
    
    # Generate script and itinerary
    itinerary_generator = ItineraryGeneratorLong()
    script_generator = ScriptGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing day video assembler for {test_destination}")
    
    # Load or generate itinerary and script
    itinerary_data = itinerary_generator.load_itinerary(test_destination)
    script_data = script_generator.load_script(test_destination)
    
    if not itinerary_data or not script_data:
        logger.error("Itinerary or script not found")
        return
    
    # Generate voiceovers
    voiceover_generator = VoiceoverGeneratorLong()
    voiceover_files = voiceover_generator.generate_voiceovers_for_script(script_data, test_destination)
    
    # Mix audio
    audio_mixer = AudioMixerLong()
    mixed_audio_files = audio_mixer.mix_audio_for_all_days(voiceover_files, test_destination)
    
    # Assemble day videos
    day_assembler = DayVideoAssemblerLong()
    images_dir = Path(settings_long.IMAGES_DIR)
    
    day_videos = {}
    for day in itinerary_data.get('itinerary', []):
        day_number = day.get('day_number', 0)
        mixed_audio_path = mixed_audio_files.get(day_number)
        
        day_video_path = day_assembler.assemble_day_video(
            day_data=day,
            script_data=script_data,
            destination=test_destination,
            images_dir=images_dir,
            voiceover_path=mixed_audio_path
        )
        
        if day_video_path:
            day_videos[day_number] = day_video_path
    
    logger.info(f"Assembled {len(day_videos)} day videos")


if __name__ == "__main__":
    main()

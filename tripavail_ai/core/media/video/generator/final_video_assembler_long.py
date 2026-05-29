#!/usr/bin/env python3
"""
Final Video Assembler for Long Videos
Combines all day videos into one final video
Adds transitions between days
Ensures total duration ≤ 8 minutes
"""

import os
import subprocess
import json
import shutil
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


class FinalVideoAssemblerLong:
    """
    Combines all day videos into one final video
    Adds transitions between days
    Ensures total duration ≤ 8 minutes
    """
    
    def __init__(self):
        # Video settings
        self.resolution = settings_long.LONG_VIDEO_RESOLUTION  # (1920, 1080)
        self.fps = settings_long.LONG_VIDEO_FPS  # 30
        self.max_duration_minutes = 8  # Maximum video duration in minutes
        self.max_duration_seconds = self.max_duration_minutes * 60  # 480 seconds
        
        # Transition settings
        self.transition_duration = settings_long.VIDEO_TRANSITION_DURATION  # 0.8 seconds
        self.audio_crossfade_duration = 0.8  # Audio crossfade duration in seconds (Phase 1.2)
        self.video_crossfade_duration = 0.8  # Video crossfade duration in seconds (Phase 2.1)
        
        # Video codec settings
        self.video_codec = settings_long.VIDEO_CODEC  # "libx264"
        self.video_preset = settings_long.VIDEO_PRESET  # "medium"
        self.video_crf = settings_long.VIDEO_CRF  # 20
        
        # Output directory
        self.videos_dir = Path(settings_long.VIDEOS_DIR)
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporary directory for day videos
        self.temp_dir = self.videos_dir / "temp_days"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Final Video Assembler Long initialized")
        logger.info(f"Max duration: {self.max_duration_minutes} minutes ({self.max_duration_seconds} seconds)")
    
    def combine_day_videos(
        self,
        day_video_paths: Dict[int, Path],
        destination: str,
        output_path: Optional[Path] = None,
        introduction_video_path: Optional[Path] = None,
        previous_cumulative_video: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Combine introduction video (if exists) and all day videos into one final video
        Uses incremental compilation: if previous cumulative video provided, combines it with new day videos
        
        Args:
            day_video_paths: Dictionary mapping day numbers to video paths
            destination: Destination name
            output_path: Output video path (optional)
            introduction_video_path: Path to introduction video segment (optional)
            previous_cumulative_video: Path to previous cumulative video (for incremental compilation)
            
        Returns:
            Path to final combined video or None if failed
        """
        temp_previous_copy: Optional[Path] = None
        
        try:
            # If previous cumulative video provided, use it as base (incremental compilation)
            if previous_cumulative_video and previous_cumulative_video.exists():
                if not day_video_paths:
                    logger.warning("No new day videos to add, returning previous cumulative video")
                    return previous_cumulative_video
                
                logger.info(f"Found previous cumulative video: {previous_cumulative_video.name}")
                logger.info("Using incremental compilation: previous cumulative video + new day videos")
                
                # IMPORTANT: Copy previous cumulative video before combining since FFmpeg overwrites outputs
                temp_previous_copy = self.temp_dir / (
                    f"prev_cumulative_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                    f"{previous_cumulative_video.suffix or '.mp4'}"
                )
                shutil.copy2(previous_cumulative_video, temp_previous_copy)
                logger.debug(f"Copied previous cumulative video to temporary path: {temp_previous_copy}")
                
                # Build list: previous cumulative video + new day videos
                videos_to_combine = [temp_previous_copy]
                
                # Sort new day videos by day number
                sorted_days = sorted(day_video_paths.items())
                new_day_videos = [video_path for _, video_path in sorted_days]
                videos_to_combine.extend(new_day_videos)
                
                logger.info(f"Incremental: Using previous cumulative video + {len(new_day_videos)} new day video(s)")
            elif not day_video_paths:
                logger.error("No day videos to combine")
                return None
            else:
                # STANDARD COMPILATION: Combine all individual day videos
                logger.info("No previous cumulative video found, combining all individual day videos")
                
                # Build list of videos to combine: introduction first, then day videos
                videos_to_combine = []
                
                if introduction_video_path and introduction_video_path.exists():
                    logger.info(f"Including introduction video: {introduction_video_path.name}")
                    videos_to_combine.append(introduction_video_path)
                
                # Sort day videos by day number
                sorted_days = sorted(day_video_paths.items())
                day_videos = [video_path for _, video_path in sorted_days]
                videos_to_combine.extend(day_videos)
            
            # Create output path if not provided
            if output_path is None:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                output_path = self.videos_dir / f"{safe_destination}_final_video.mp4"
            
            total_video_count = len(videos_to_combine)
            intro_text = " (with introduction)" if introduction_video_path and not previous_cumulative_video else ""
            compilation_type = "incremental" if previous_cumulative_video else "standard"
            
            logger.info(f"Combining {total_video_count} videos ({compilation_type} compilation){intro_text}...")
            
            # Check total duration
            total_duration = self._get_total_duration(videos_to_combine)
            logger.info(f"Total duration: {total_duration:.2f} seconds ({total_duration / 60:.2f} minutes)")
            
            if total_duration > self.max_duration_seconds:
                logger.warning(f"Total duration ({total_duration / 60:.2f} minutes) exceeds maximum ({self.max_duration_minutes} minutes)")
                # Note: We removed the duration check, so videos can exceed 8 minutes
                # But we can still log it as a warning
                logger.info("Continuing with full duration (duration limit removed)")
            
            # Combine videos using FFmpeg concat
            success = self._combine_videos_with_ffmpeg(videos_to_combine, output_path)
            
            if success:
                intro_text = " (with introduction)" if introduction_video_path else ""
                logger.info(f"✅ Combined {total_video_count} videos{intro_text} into: {output_path}")
                return output_path
            else:
                logger.error("Failed to combine day videos")
                return None
                
        except Exception as e:
            logger.error(f"Error combining day videos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
        finally:
            if temp_previous_copy and temp_previous_copy.exists():
                try:
                    temp_previous_copy.unlink()
                    logger.debug(f"Deleted temporary previous cumulative copy: {temp_previous_copy}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete temporary copy {temp_previous_copy}: {cleanup_error}")
    
    def _get_video_duration(self, video_path: Path) -> float:
        """
        Get duration of a single video
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
        """
        try:
            if not video_path.exists():
                logger.warning(f"Video file not found: {video_path}")
                return 0.0
            
            ffprobe_path = get_ffprobe_path()
            ffmpeg_path = get_ffmpeg_path()
            
            if ffprobe_path == ffmpeg_path:
                # Use FFmpeg syntax (when FFmpeg is used as FFprobe fallback)
                cmd = [
                    ffprobe_path,
                    '-i', str(video_path),
                    '-hide_banner',
                    '-f', 'null',
                    '-'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if 'Duration:' in result.stderr:
                    import re
                    duration_match = re.search(r'Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
                    if duration_match:
                        hours, minutes, seconds = duration_match.groups()
                        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            else:
                # Use FFprobe syntax
                cmd = [
                    ffprobe_path,
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(video_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return float(result.stdout.strip())
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error getting video duration: {e}")
            return 0.0
    
    def _get_total_duration(self, video_paths: List[Path]) -> float:
        """
        Get total duration of all videos
        
        Args:
            video_paths: List of video paths
            
        Returns:
            Total duration in seconds
        """
        try:
            total_duration = 0.0
            
            for video_path in video_paths:
                duration = self._get_video_duration(video_path)
                total_duration += duration
            
            return total_duration
            
        except Exception as e:
            logger.error(f"Error getting total duration: {e}")
            return 0.0
    
    def _trim_videos_to_fit(self, video_paths: List[Path], max_duration_seconds: float) -> List[Path]:
        """
        Trim videos to fit within max duration
        
        Args:
            video_paths: List of video paths
            max_duration_seconds: Maximum duration in seconds
            
        Returns:
            List of trimmed video paths (or original if trimmed)
        """
        try:
            # Calculate duration per video
            num_videos = len(video_paths)
            duration_per_video = max_duration_seconds / num_videos
            
            logger.info(f"Trimming {num_videos} videos to {duration_per_video:.2f} seconds each")
            
            trimmed_videos = []
            
            for i, video_path in enumerate(video_paths):
                if not video_path.exists():
                    continue
                
                # Get original duration using the helper method
                original_duration = self._get_video_duration(video_path)
                
                if original_duration > 0:
                    
                    if original_duration <= duration_per_video:
                        # No trimming needed
                        trimmed_videos.append(video_path)
                    else:
                        # Trim video
                        trimmed_path = video_path.parent / f"{video_path.stem}_trimmed.mp4"
                        
                        trim_cmd = [
                            'ffmpeg',
                            '-i', str(video_path),
                            '-t', str(duration_per_video),
                            '-c', 'copy',
                            '-y',
                            str(trimmed_path)
                        ]
                        
                        result = subprocess.run(trim_cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            trimmed_videos.append(trimmed_path)
                            logger.info(f"Trimmed video {i + 1} to {duration_per_video:.2f} seconds")
                        else:
                            logger.warning(f"Failed to trim video {i + 1}: {result.stderr}")
                            trimmed_videos.append(video_path)  # Use original
                else:
                    logger.warning(f"Failed to get duration for video {i + 1}")
                    trimmed_videos.append(video_path)  # Use original
            
            return trimmed_videos
            
        except Exception as e:
            logger.error(f"Error trimming videos: {e}")
            return video_paths
    
    def _combine_videos_with_ffmpeg(self, video_paths: List[Path], output_path: Path) -> bool:
        """
        Combine videos using FFmpeg with audio crossfade transitions (Phase 1.2)
        
        Args:
            video_paths: List of video paths
            output_path: Output video path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists before FFmpeg tries to write
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # If only one video, just copy it
            if len(video_paths) == 1:
                import shutil
                shutil.copy2(video_paths[0], output_path)
                logger.info(f"✅ Copied single video: {output_path}")
                return True
            
            # PHASE 1.2: Add audio crossfade transitions between videos
            # For 2+ videos, use filter_complex to add audio crossfades
            ffmpeg_path = get_ffmpeg_path()
            
            # Build input arguments
            input_args = []
            for video_path in video_paths:
                abs_path = str(video_path.absolute()).replace('\\', '/')
                input_args.extend(['-i', abs_path])
            
            # PHASE 2.1: Build filter_complex for video crossfade + audio crossfade
            filter_parts = []
            
            # Video: Scale and prepare all video streams
            for i in range(len(video_paths)):
                # Scale and normalize each video stream
                filter_parts.append(
                    f"[{i}:v]scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=decrease,"
                    f"pad={self.resolution[0]}:{self.resolution[1]}:({self.resolution[0]}-iw)/2:({self.resolution[1]}-ih)/2,"
                    f"setsar=1:1,fps={self.fps}[v{i}]"
                )
            
            # PHASE 2.1: Add crossfade transitions between video streams
            if len(video_paths) == 2:
                # Simple crossfade between two videos
                # Get video durations for offset calculation
                video1_duration = self._get_video_duration(video_paths[0])
                # Offset: start crossfade slightly before end of first video
                offset = max(0, video1_duration - self.video_crossfade_duration)
                filter_parts.append(
                    f"[v0][v1]xfade=transition=fade:duration={self.video_crossfade_duration}:offset={offset}[v]"
                )
            else:
                # Multiple videos: chain crossfades
                # Get durations for offset calculation
                video_durations = [self._get_video_duration(vp) for vp in video_paths]
                
                current_label = "[v0]"
                cumulative_time = video_durations[0] if video_durations else 90.0
                
                for i in range(1, len(video_paths)):
                    next_label = f"[v{i}]"
                    output_label = f"[vf{i}]" if i < len(video_paths) - 1 else "[v]"
                    
                    # Offset: start crossfade slightly before end of previous video
                    offset = max(0, cumulative_time - self.video_crossfade_duration)
                    
                    filter_parts.append(
                        f"{current_label}{next_label}xfade=transition=fade:duration={self.video_crossfade_duration}:offset={offset}{output_label}"
                    )
                    
                    current_label = output_label
                    # Update cumulative time (subtract crossfade overlap)
                    cumulative_time += video_durations[i] - self.video_crossfade_duration
            
            # Audio: Extract audio streams
            audio_inputs = [f'[{i}:a]' for i in range(len(video_paths))]
            
            # PHASE 1.2: Add crossfade transitions between consecutive audio tracks
            # Note: acrossfade filter only supports 'd' (duration) parameter, not o1/o2 offsets
            if len(video_paths) == 2:
                # Simple crossfade between two videos
                filter_parts.append(
                    f"{audio_inputs[0]}{audio_inputs[1]}acrossfade=d={self.audio_crossfade_duration}[a]"
                )
            else:
                # Multiple videos: chain crossfades
                # First crossfade
                filter_parts.append(
                    f"{audio_inputs[0]}{audio_inputs[1]}acrossfade=d={self.audio_crossfade_duration}[af1]"
                )
                
                # Chain remaining crossfades
                for i in range(2, len(video_paths)):
                    prev_label = f"[af{i-1}]" if i > 2 else "[af1]"
                    # Last crossfade outputs directly to [a], others to intermediate labels
                    output_label = "[a]" if i == len(video_paths) - 1 else f"[af{i}]"
                    filter_parts.append(
                        f"{prev_label}{audio_inputs[i]}acrossfade=d={self.audio_crossfade_duration}{output_label}"
                    )
            
            filter_complex = ';'.join(filter_parts)
            
            # Build FFmpeg command
            cmd = [
                ffmpeg_path,
                '-y',  # Overwrite output
            ] + input_args + [
                '-filter_complex', filter_complex,
                '-map', '[v]',
                '-map', '[a]',
                '-c:v', self.video_codec,
                '-preset', self.video_preset,
                '-crf', str(self.video_crf),
                '-c:a', 'aac',
                '-b:a', '192k',
                '-r', str(self.fps),
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg command to combine videos with audio & video crossfades...")
            logger.debug(f"Video crossfade duration: {self.video_crossfade_duration}s")
            logger.debug(f"Audio crossfade duration: {self.audio_crossfade_duration}s")
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully combined videos with audio & video crossfades: {output_path}")
                return True
            else:
                # Log full error for debugging
                logger.error(f"FFmpeg error (return code {result.returncode})")
                logger.error(f"FFmpeg stderr: {result.stderr}")
                logger.error(f"FFmpeg stdout: {result.stdout}")
                logger.debug(f"Filter complex: {filter_complex}")
                # Fallback to simple concat if crossfade fails
                logger.warning("Falling back to simple concat without crossfades...")
                return self._combine_videos_simple_concat(video_paths, output_path)
                
        except Exception as e:
            logger.error(f"Error combining videos with FFmpeg: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback to simple concat
            logger.warning("Falling back to simple concat without crossfades...")
            return self._combine_videos_simple_concat(video_paths, output_path)
    
    def _combine_videos_simple_concat(self, video_paths: List[Path], output_path: Path) -> bool:
        """
        Combine videos using simple FFmpeg concat (fallback method)
        
        Args:
            video_paths: List of video paths
            output_path: Output video path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create concat file list
            concat_file = self.temp_dir / "concat_list.txt"
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                for video_path in video_paths:
                    # Use absolute path and escape single quotes
                    abs_path = str(video_path.absolute()).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")
            
            # Build FFmpeg command
            ffmpeg_path = get_ffmpeg_path()
            cmd = [
                ffmpeg_path,
                '-y',  # Overwrite output
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c:v', self.video_codec,
                '-preset', self.video_preset,
                '-crf', str(self.video_crf),
                '-c:a', 'aac',
                '-b:a', '192k',
                '-r', str(self.fps),
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg command to combine videos (simple concat)...")
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up concat file
            if concat_file.exists():
                concat_file.unlink()
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully combined videos: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error combining videos with simple concat: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def add_day_titles(
        self,
        video_path: Path,
        itinerary_data: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Add day titles to video (optional)
        
        Args:
            video_path: Input video path
            itinerary_data: Itinerary data with day titles
            output_path: Output video path (optional)
            
        Returns:
            Path to video with day titles or None if failed
        """
        try:
            # This is optional - can be implemented later if needed
            # For now, just return the original video
            logger.info("Day titles feature not yet implemented")
            return video_path
            
        except Exception as e:
            logger.error(f"Error adding day titles: {e}")
            return video_path
    
    def cleanup_temp_files(self, day_video_paths: Dict[int, Path], keep_final: bool = True):
        """
        Clean up temporary day video files
        
        Args:
            day_video_paths: Dictionary mapping day numbers to video paths
            keep_final: Whether to keep the final combined video
        """
        try:
            logger.info("Cleaning up temporary files...")
            
            # Delete day videos
            for day_number, video_path in day_video_paths.items():
                if video_path.exists():
                    video_path.unlink()
                    logger.info(f"Deleted day {day_number} video: {video_path}")
            
            # Clean up temp directory
            temp_files = list(self.temp_dir.glob("*.mp4"))
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.info(f"Deleted temp file: {temp_file}")
            
            logger.info("✅ Cleaned up temporary files")
            
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")


def main():
    """Test final video assembler"""
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    from core.media.video.generator.day_video_assembler_long import DayVideoAssemblerLong
    
    # Generate itinerary
    itinerary_generator = ItineraryGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing final video assembler for {test_destination}")
    
    # Load itinerary
    itinerary_data = itinerary_generator.load_itinerary(test_destination)
    
    if not itinerary_data:
        logger.error("Itinerary not found")
        return
    
    # Assemble day videos (mock for testing)
    day_assembler = DayVideoAssemblerLong()
    day_video_paths = {}
    
    # For testing, create mock day videos
    # In production, these would be generated by DayVideoAssemblerLong
    temp_dir = Path(settings_long.VIDEOS_DIR) / "temp_days"
    for day in itinerary_data.get('itinerary', []):
        day_number = day.get('day_number', 0)
        # Mock video path (would be actual video in production)
        day_video_paths[day_number] = temp_dir / f"{test_destination}_day_{day_number}.mp4"
    
    # Combine day videos
    final_assembler = FinalVideoAssemblerLong()
    final_video_path = final_assembler.combine_day_videos(
        day_video_paths,
        test_destination
    )
    
    if final_video_path:
        logger.info(f"✅ Final video created: {final_video_path}")
    else:
        logger.error("Failed to create final video")


if __name__ == "__main__":
    main()


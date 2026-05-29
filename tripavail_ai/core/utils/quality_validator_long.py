#!/usr/bin/env python3
"""
Quality Validator for Long Videos
Validates video quality before upload (Phase 3.1)
Checks: duration, audio levels, resolution, file size, black frames, playback
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

from core.utils.ffmpeg_helper import get_ffmpeg_path, get_ffprobe_path


class QualityValidatorLong:
    """
    Validates video quality before upload
    Checks duration, audio levels, resolution, file size, black frames, playback
    """
    
    def __init__(self):
        # Quality thresholds
        self.min_duration_seconds = 60.0  # Minimum 1 minute
        self.max_duration_seconds = 7200.0  # Maximum 2 hours (120 minutes)
        self.expected_resolution = (1920, 1080)  # Expected 1920x1080
        self.resolution_tolerance = 50  # Allow ±50 pixels
        self.max_file_size_mb = 2000.0  # Maximum 2GB
        self.min_file_size_mb = 1.0  # Minimum 1MB
        
        # Audio thresholds
        self.min_voiceover_db = -40.0  # Minimum voiceover level (-40 dB)
        self.max_voiceover_db = 0.0  # Maximum voiceover level (0 dB)
        self.min_music_db = -60.0  # Minimum background music level (-60 dB)
        
        logger.info("Quality Validator Long initialized")
    
    def validate_video(
        self,
        video_path: Path,
        skip_black_frame_check: bool = False
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate video quality before upload
        
        Args:
            video_path: Path to video file
            skip_black_frame_check: Skip black frame detection (slower check)
            
        Returns:
            Tuple of (is_valid, warnings, metrics)
        """
        try:
            if not video_path.exists():
                return False, ["Video file not found"], {}
            
            warnings = []
            metrics = {}
            
            # 1. Check file size
            file_size_mb = video_path.stat().st_size / (1024 * 1024)
            metrics['file_size_mb'] = file_size_mb
            
            if file_size_mb < self.min_file_size_mb:
                warnings.append(f"File size too small: {file_size_mb:.2f} MB (minimum: {self.min_file_size_mb} MB)")
            
            if file_size_mb > self.max_file_size_mb:
                warnings.append(f"File size too large: {file_size_mb:.2f} MB (maximum: {self.max_file_size_mb} MB)")
            
            # 2. Check duration
            duration = self._get_video_duration(video_path)
            metrics['duration_seconds'] = duration
            metrics['duration_minutes'] = duration / 60.0
            
            if duration < self.min_duration_seconds:
                warnings.append(f"Duration too short: {duration:.2f}s (minimum: {self.min_duration_seconds}s)")
            
            if duration > self.max_duration_seconds:
                warnings.append(f"Duration too long: {duration:.2f}s (maximum: {self.max_duration_seconds}s)")
            
            # 3. Check resolution
            resolution = self._get_video_resolution(video_path)
            metrics['resolution'] = resolution
            
            if resolution:
                width, height = resolution
                expected_width, expected_height = self.expected_resolution
                
                width_diff = abs(width - expected_width)
                height_diff = abs(height - expected_height)
                
                if width_diff > self.resolution_tolerance or height_diff > self.resolution_tolerance:
                    warnings.append(
                        f"Resolution mismatch: {width}x{height} "
                        f"(expected: {expected_width}x{expected_height} ±{self.resolution_tolerance})"
                    )
            else:
                warnings.append("Could not determine video resolution")
            
            # 4. Check audio levels (voiceover and music)
            audio_metrics = self._check_audio_levels(video_path)
            metrics['audio'] = audio_metrics
            
            if audio_metrics.get('voiceover_present'):
                voiceover_db = audio_metrics.get('voiceover_max_db', -100.0)
                if voiceover_db < self.min_voiceover_db:
                    warnings.append(
                        f"Voiceover too quiet: {voiceover_db:.2f} dB "
                        f"(minimum: {self.min_voiceover_db} dB)"
                    )
                if voiceover_db > self.max_voiceover_db:
                    warnings.append(
                        f"Voiceover too loud: {voiceover_db:.2f} dB "
                        f"(maximum: {self.max_voiceover_db} dB)"
                    )
            else:
                warnings.append("No voiceover detected in audio")
            
            if audio_metrics.get('music_present'):
                music_max_db = audio_metrics.get('music_max_db', -100.0)
                if music_max_db < self.min_music_db:
                    warnings.append(
                        f"Background music too quiet: {music_max_db:.2f} dB "
                        f"(minimum: {self.min_music_db} dB)"
                    )
            
            # 5. Check for black frames (optional, slower)
            if not skip_black_frame_check:
                black_frame_ratio = self._check_black_frames(video_path)
                metrics['black_frame_ratio'] = black_frame_ratio
                
                if black_frame_ratio > 0.1:  # More than 10% black frames
                    warnings.append(
                        f"Too many black frames: {black_frame_ratio*100:.1f}% "
                        f"(threshold: 10%)"
                    )
            
            # Determine if valid (warnings are acceptable, but errors should fail)
            is_valid = True  # For now, warnings don't fail validation
            
            logger.info(f"Video quality validation: {'PASSED' if is_valid else 'FAILED'}")
            if warnings:
                logger.warning(f"Quality warnings: {len(warnings)}")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
            
            return is_valid, warnings, metrics
            
        except Exception as e:
            logger.error(f"Error validating video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, [f"Validation error: {str(e)}"], {}
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds"""
        try:
            ffprobe_path = get_ffprobe_path()
            ffmpeg_path = get_ffmpeg_path()
            
            if ffprobe_path == ffmpeg_path:
                # Use FFmpeg syntax
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
    
    def _get_video_resolution(self, video_path: Path) -> Optional[Tuple[int, int]]:
        """Get video resolution (width, height)"""
        try:
            ffprobe_path = get_ffprobe_path()
            ffmpeg_path = get_ffmpeg_path()
            
            if ffprobe_path == ffmpeg_path:
                # Use FFmpeg syntax
                cmd = [
                    ffprobe_path,
                    '-i', str(video_path),
                    '-hide_banner',
                    '-f', 'null',
                    '-'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                # Parse resolution from stderr like "Stream #0:0: Video: h264, 1920x1080"
                if 'Video:' in result.stderr:
                    import re
                    resolution_match = re.search(r'(\d+)x(\d+)', result.stderr)
                    if resolution_match:
                        width, height = resolution_match.groups()
                        return (int(width), int(height))
            else:
                # Use FFprobe syntax
                cmd = [
                    ffprobe_path,
                    '-v', 'error',
                    '-select_streams', 'v:0',
                    '-show_entries', 'stream=width,height',
                    '-of', 'csv=s=x:p=0',
                    str(video_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    parts = result.stdout.strip().split('x')
                    if len(parts) == 2:
                        return (int(parts[0]), int(parts[1]))
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting video resolution: {e}")
            return None
    
    def _check_audio_levels(self, video_path: Path) -> Dict[str, Any]:
        """Check audio levels (voiceover and music)"""
        try:
            ffmpeg_path = get_ffmpeg_path()
            
            # Use FFmpeg to analyze audio levels
            # Extract audio and analyze volume
            cmd = [
                ffmpeg_path,
                '-i', str(video_path),
                '-af', 'volumedetect',
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            audio_metrics = {
                'voiceover_present': False,
                'voiceover_max_db': -100.0,
                'music_present': False,
                'music_max_db': -100.0,
                'mean_volume_db': -100.0,
                'max_volume_db': -100.0
            }
            
            if result.returncode == 0 and 'mean_volume:' in result.stderr:
                import re
                
                # Parse mean_volume
                mean_match = re.search(r'mean_volume:\s*(-?\d+\.?\d*)\s*dB', result.stderr)
                if mean_match:
                    audio_metrics['mean_volume_db'] = float(mean_match.group(1))
                
                # Parse max_volume
                max_match = re.search(r'max_volume:\s*(-?\d+\.?\d*)\s*dB', result.stderr)
                if max_match:
                    audio_metrics['max_volume_db'] = float(max_match.group(1))
                
                # Detect voiceover (typically -20 to 0 dB)
                if audio_metrics['mean_volume_db'] > -40.0:
                    audio_metrics['voiceover_present'] = True
                    audio_metrics['voiceover_max_db'] = audio_metrics['max_volume_db']
                
                # Detect music (typically -40 to -20 dB, but present in background)
                if audio_metrics['mean_volume_db'] > -60.0:
                    audio_metrics['music_present'] = True
                    audio_metrics['music_max_db'] = audio_metrics['max_volume_db']
            
            return audio_metrics
            
        except Exception as e:
            logger.warning(f"Error checking audio levels: {e}")
            return {
                'voiceover_present': False,
                'voiceover_max_db': -100.0,
                'music_present': False,
                'music_max_db': -100.0,
                'mean_volume_db': -100.0,
                'max_volume_db': -100.0
            }
    
    def _check_black_frames(self, video_path: Path, sample_count: int = 30) -> float:
        """Check for black frames (returns ratio of black frames)"""
        try:
            ffmpeg_path = get_ffmpeg_path()
            
            # Get video duration
            duration = self._get_video_duration(video_path)
            if duration == 0:
                return 0.0
            
            # Sample frames at intervals
            interval = duration / sample_count
            black_frame_count = 0
            
            for i in range(sample_count):
                timestamp = i * interval
                
                # Extract frame and check if it's black
                cmd = [
                    ffmpeg_path,
                    '-i', str(video_path),
                    '-ss', str(timestamp),
                    '-vframes', '1',
                    '-vf', 'blackdetect=d=0.1:pix_th=0.1',
                    '-f', 'null',
                    '-'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if 'black_start:' in result.stderr or 'black_end:' in result.stderr:
                    black_frame_count += 1
            
            return black_frame_count / sample_count if sample_count > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Error checking black frames: {e}")
            return 0.0


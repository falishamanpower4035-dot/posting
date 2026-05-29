#!/usr/bin/env python3
"""
Pacing Analyzer for Long Videos
Analyzes pacing consistency across days (Phase 3.2)
Checks: day durations, image durations, scene lengths
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from loguru import logger

from core.utils.ffmpeg_helper import get_ffprobe_path, get_ffmpeg_path
import subprocess


class PacingAnalyzerLong:
    """
    Analyzes pacing consistency across days
    Checks day durations, image durations, scene lengths
    """
    
    def __init__(self):
        # Pacing thresholds
        self.max_day_duration_variance = 0.3  # Allow ±30% variance between days
        self.max_image_duration_variance = 0.2  # Allow ±20% variance between images
        self.max_scene_duration_variance = 0.4  # Allow ±40% variance between scenes
        
        logger.info("Pacing Analyzer Long initialized")
    
    def analyze_pacing(
        self,
        day_video_paths: Dict[int, Path],
        day_image_results: Optional[Dict[int, Dict[str, List[Path]]]] = None,
        script_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Analyze pacing consistency across days
        
        Args:
            day_video_paths: Dictionary mapping day numbers to video paths
            day_image_results: Dictionary mapping day numbers to image results (optional)
            script_data: Script data with day information (optional)
            
        Returns:
            Tuple of (pacing_metrics, warnings)
        """
        try:
            warnings = []
            metrics = {
                'day_durations': {},
                'day_duration_stats': {},
                'image_durations': {},
                'scene_durations': {},
                'overall_pacing_score': 1.0
            }
            
            # 1. Analyze day durations
            day_durations = {}
            for day_number, video_path in day_video_paths.items():
                duration = self._get_video_duration(video_path)
                day_durations[day_number] = duration
                metrics['day_durations'][day_number] = duration
            
            if day_durations:
                durations_list = list(day_durations.values())
                avg_duration = sum(durations_list) / len(durations_list)
                min_duration = min(durations_list)
                max_duration = max(durations_list)
                
                metrics['day_duration_stats'] = {
                    'average': avg_duration,
                    'min': min_duration,
                    'max': max_duration,
                    'variance': max_duration - min_duration,
                    'variance_percent': ((max_duration - min_duration) / avg_duration * 100) if avg_duration > 0 else 0
                }
                
                # Check for significant variance
                variance_percent = metrics['day_duration_stats']['variance_percent']
                if variance_percent > (self.max_day_duration_variance * 100):
                    warnings.append(
                        f"Day duration variance too high: {variance_percent:.1f}% "
                        f"(threshold: {self.max_day_duration_variance * 100:.1f}%)"
                    )
                    warnings.append(
                        f"  Shortest day: {min_duration:.1f}s, Longest day: {max_duration:.1f}s, "
                        f"Average: {avg_duration:.1f}s"
                    )
            
            # 2. Analyze image durations (if image results provided)
            if day_image_results:
                image_duration_stats = self._analyze_image_durations(day_image_results, script_data)
                metrics['image_durations'] = image_duration_stats
                
                if image_duration_stats.get('variance_percent', 0) > (self.max_image_duration_variance * 100):
                    warnings.append(
                        f"Image duration variance too high: {image_duration_stats.get('variance_percent', 0):.1f}% "
                        f"(threshold: {self.max_image_duration_variance * 100:.1f}%)"
                    )
            
            # 3. Analyze scene durations (if script data provided)
            if script_data:
                scene_duration_stats = self._analyze_scene_durations(script_data)
                metrics['scene_durations'] = scene_duration_stats
                
                if scene_duration_stats.get('variance_percent', 0) > (self.max_scene_duration_variance * 100):
                    warnings.append(
                        f"Scene duration variance too high: {scene_duration_stats.get('variance_percent', 0):.1f}% "
                        f"(threshold: {self.max_scene_duration_variance * 100:.1f}%)"
                    )
            
            # 4. Calculate overall pacing score (0.0 to 1.0)
            pacing_score = 1.0
            
            # Deduct points for variances
            if metrics['day_duration_stats'].get('variance_percent', 0) > (self.max_day_duration_variance * 100):
                pacing_score -= 0.3
            
            if metrics.get('image_durations', {}).get('variance_percent', 0) > (self.max_image_duration_variance * 100):
                pacing_score -= 0.2
            
            if metrics.get('scene_durations', {}).get('variance_percent', 0) > (self.max_scene_duration_variance * 100):
                pacing_score -= 0.2
            
            pacing_score = max(0.0, pacing_score)  # Ensure non-negative
            metrics['overall_pacing_score'] = pacing_score
            
            if warnings:
                logger.warning(f"Pacing analysis warnings ({len(warnings)}):")
                for warning in warnings:
                    logger.warning(f"  ⚠️  {warning}")
            else:
                logger.info(f"✅ Pacing analysis passed - Overall score: {pacing_score:.2f}/1.0")
            
            return metrics, warnings
            
        except Exception as e:
            logger.error(f"Error analyzing pacing: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}, [f"Pacing analysis error: {str(e)}"]
    
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
    
    def _analyze_image_durations(
        self,
        day_image_results: Dict[int, Dict[str, List[Path]]],
        script_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze image durations across days"""
        try:
            # Estimate image durations based on voiceover duration and image count
            # Standard duration per image: 2.5 seconds
            standard_image_duration = 2.5
            
            image_durations_per_day = {}
            all_image_durations = []
            
            script_days = script_data.get('days', []) if script_data else []
            
            for day_number, scene_images in day_image_results.items():
                # Count total images for this day
                total_images = sum(len(images) for images in scene_images.values())
                
                # Find corresponding script day for voiceover duration
                script_day = next((d for d in script_days if d.get('day_number') == day_number), None)
                voiceover_duration = script_day.get('estimated_voiceover_seconds', 90.0) if script_day else 90.0
                
                # Calculate average image duration for this day
                if total_images > 0:
                    avg_image_duration = voiceover_duration / total_images
                    image_durations_per_day[day_number] = avg_image_duration
                    all_image_durations.append(avg_image_duration)
            
            if all_image_durations:
                avg_duration = sum(all_image_durations) / len(all_image_durations)
                min_duration = min(all_image_durations)
                max_duration = max(all_image_durations)
                variance_percent = ((max_duration - min_duration) / avg_duration * 100) if avg_duration > 0 else 0
                
                return {
                    'average': avg_duration,
                    'min': min_duration,
                    'max': max_duration,
                    'variance': max_duration - min_duration,
                    'variance_percent': variance_percent,
                    'per_day': image_durations_per_day
                }
            
            return {}
            
        except Exception as e:
            logger.warning(f"Error analyzing image durations: {e}")
            return {}
    
    def _analyze_scene_durations(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze scene durations from script data"""
        try:
            script_days = script_data.get('days', [])
            scene_durations = []
            
            for script_day in script_days:
                scenes = script_day.get('scenes', [])
                for scene in scenes:
                    scene_duration = scene.get('estimated_duration_seconds', 0)
                    if scene_duration > 0:
                        scene_durations.append(scene_duration)
            
            if scene_durations:
                avg_duration = sum(scene_durations) / len(scene_durations)
                min_duration = min(scene_durations)
                max_duration = max(scene_durations)
                variance_percent = ((max_duration - min_duration) / avg_duration * 100) if avg_duration > 0 else 0
                
                return {
                    'average': avg_duration,
                    'min': min_duration,
                    'max': max_duration,
                    'variance': max_duration - min_duration,
                    'variance_percent': variance_percent,
                    'count': len(scene_durations)
                }
            
            return {}
            
        except Exception as e:
            logger.warning(f"Error analyzing scene durations: {e}")
            return {}


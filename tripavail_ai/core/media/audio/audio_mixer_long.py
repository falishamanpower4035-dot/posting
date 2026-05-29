#!/usr/bin/env python3
"""
Audio Mixer for Long Videos
Mixes voiceover with background music
Creates per-day audio files (temporary) and final combined audio
"""

import os
import subprocess
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


class AudioMixerLong:
    """
    Mixes voiceover with background music
    Creates per-day audio files (temporary) and final combined audio
    """
    
    def __init__(self):
        # Audio settings
        self.voiceover_volume = settings_long.AUDIO_VOICEOVER_VOLUME  # 1.0
        self.music_volume = settings_long.AUDIO_MUSIC_VOLUME  # 0.3
        self.music_fade_in = settings_long.AUDIO_MUSIC_FADE_IN  # 1.0 seconds
        self.music_fade_out = settings_long.AUDIO_MUSIC_FADE_OUT  # 2.0 seconds
        self.transition_tail_mid = getattr(settings_long, "AUDIO_TRANSITION_TAIL_MID", 1.0)
        self.transition_tail_final = getattr(settings_long, "AUDIO_TRANSITION_TAIL_FINAL", 2.0)
        
        # Audio codec settings
        self.audio_codec = settings_long.AUDIO_CODEC  # "aac"
        self.audio_bitrate = settings_long.AUDIO_BITRATE  # "320k"
        
        # Output directory
        self.voiceovers_dir = Path(settings_long.VOICEOVERS_DIR)
        self.voiceovers_dir.mkdir(parents=True, exist_ok=True)
        
        # Music directories (check multiple locations for existing music files)
        self.music_dirs = [
            Path("assets") / "audio",
            Path("data") / "audio" / "music",
            Path("assets") / "music",
            Path("data") / "music_archive",  # Archived music directory
        ]
        
        # Ensure directories exist
        for music_dir in self.music_dirs:
            music_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporary directory for mixed audio
        self.temp_dir = self.voiceovers_dir / "temp_mixed"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Audio Mixer Long initialized")
        logger.info(f"Voiceover volume: {self.voiceover_volume}")
        logger.info(f"Music volume: {self.music_volume}")
    
    def get_background_music(self, duration: float) -> Optional[Path]:
        """
        Get background music file from existing music directories
        
        Args:
            duration: Required duration in seconds
            
        Returns:
            Path to background music file or None if not found
        """
        try:
            import random
            
            # Look for music files in all music directories
            music_files = []
            for music_dir in self.music_dirs:
                if music_dir.exists():
                    music_files.extend(list(music_dir.glob("*.mp3")))
                    music_files.extend(list(music_dir.glob("*.wav")))
            
            if not music_files:
                logger.warning("No background music files found in any directory")
                logger.warning(f"Checked directories: {[str(d) for d in self.music_dirs]}")
                return None
            
            # Randomly select a music file for variety
            music_file = random.choice(music_files)
            logger.info(f"Using background music: {music_file}")
            
            # Check if music file is long enough
            music_duration = self._get_audio_duration(music_file)
            if music_duration < duration:
                logger.info(f"Music file duration ({music_duration:.2f}s) is shorter than required ({duration:.2f}s), will loop")
                # Loop music if needed (will be handled in mixing)
            
            return music_file
            
        except Exception as e:
            logger.error(f"Error getting background music: {e}")
            return None
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        Get audio duration in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            # Use ffprobe or ffmpeg to get duration
            ffprobe_path = get_ffprobe_path()
            ffmpeg_path = get_ffmpeg_path()
            
            # Check if we're using FFmpeg as fallback (same path as FFmpeg)
            if ffprobe_path == ffmpeg_path:
                # Use FFmpeg syntax instead of FFprobe
                cmd = [
                    ffprobe_path,
                    '-i', str(audio_path),
                    '-hide_banner',
                    '-f', 'null',
                    '-'
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                # Parse duration from stderr output like "Duration: 00:00:42.87"
                if 'Duration:' in result.stderr:
                    import re
                    duration_match = re.search(r'Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)', result.stderr)
                    if duration_match:
                        hours, minutes, seconds = duration_match.groups()
                        duration = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                        return duration
                    else:
                        logger.warning(f"Failed to parse duration from FFmpeg output: {result.stderr[:200]}")
                        return 0.0
                else:
                    logger.warning(f"Failed to get audio duration: {result.stderr[:200]}")
                    return 0.0
            else:
                # Use FFprobe syntax
                cmd = [
                    ffprobe_path,
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(audio_path)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    duration = float(result.stdout.strip())
                    return duration
                else:
                    logger.warning(f"Failed to get audio duration: {result.stderr}")
                    return 0.0
                
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
    
    def mix_audio_for_day(
        self,
        voiceover_path: Path,
        day_number: int,
        destination: str,
        output_path: Optional[Path] = None,
        music_path: Optional[Path] = None,
        transition_prompt: Optional[str] = None,
        is_final_day: bool = False
    ) -> Optional[Path]:
        """
        Mix voiceover with background music for a day
        
        Args:
            voiceover_path: Path to voiceover file
            day_number: Day number
            destination: Destination name
            output_path: Output audio path (optional)
            music_path: Optional background music to reuse
            transition_prompt: Optional descriptive string for logging / future cues
            is_final_day: Whether this is the last day in the itinerary (affects tail length)
            
        Returns:
            Path to mixed audio file or None if failed
        """
        try:
            if not voiceover_path.exists():
                logger.error(f"Voiceover file not found: {voiceover_path}")
                return None
            
            # Get voiceover duration
            voiceover_duration = self._get_audio_duration(voiceover_path)
            if voiceover_duration == 0:
                logger.error("Failed to get voiceover duration")
                return None
            
            logger.info(f"Mixing audio for day {day_number} (voiceover duration: {voiceover_duration:.2f}s)...")
            if transition_prompt:
                logger.debug(f"Transition prompt: {transition_prompt}")
            
            # Get background music (use provided music_path if available, otherwise select randomly)
            if not music_path:
                music_path = self.get_background_music(voiceover_duration)
                if music_path:
                    logger.info(f"Selected background music for Day {day_number}: {music_path.name}")
            else:
                logger.info(f"Using provided background music for Day {day_number}: {music_path.name}")
            
            if not music_path:
                logger.warning("No background music found, using voiceover only")
                # Return voiceover as-is if no music
                if output_path is None:
                    safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                    output_path = self.temp_dir / f"{safe_destination}_day_{day_number}_mixed.mp3"
                
                # Ensure output directory exists before copying
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy voiceover to output path
                import shutil
                shutil.copy2(voiceover_path, output_path)
                logger.info(f"✅ Copied voiceover to: {output_path}")
                return output_path
            
            # Create output path
            if output_path is None:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                output_path = self.temp_dir / f"{safe_destination}_day_{day_number}_mixed.mp3"
            
            # Mix audio using FFmpeg
            tail_duration = self.transition_tail_final if is_final_day else self.transition_tail_mid
            
            success = self._mix_audio_with_ffmpeg(
                voiceover_path,
                music_path,
                voiceover_duration,
                output_path,
                tail_duration=tail_duration
            )
            
            if success:
                logger.info(f"✅ Mixed audio for day {day_number}: {output_path}")
                return output_path
            else:
                logger.error(f"Failed to mix audio for day {day_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error mixing audio for day {day_number}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _mix_audio_with_ffmpeg(
        self,
        voiceover_path: Path,
        music_path: Path,
        duration: float,
        output_path: Path,
        tail_duration: float = 0.0
    ) -> bool:
        """
        Mix audio using FFmpeg
        
        Args:
            voiceover_path: Path to voiceover file
            music_path: Path to background music file
            duration: Voiceover duration in seconds
            output_path: Output audio path
            tail_duration: Additional music tail length after narration (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists before FFmpeg tries to write
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            total_duration = duration + max(tail_duration, 0.0)
            
            # Build FFmpeg command
            # Mix voiceover and music with volume control and fade effects
            ffmpeg_path = get_ffmpeg_path()

            # Choose codec based on output extension to avoid container/codec mismatch
            out_ext = output_path.suffix.lower()
            codec = self.audio_codec
            if out_ext == ".mp3":
                codec = "libmp3lame"
            elif out_ext in [".m4a", ".aac"]:
                codec = "aac"
            elif out_ext == ".wav":
                codec = "pcm_s16le"

            fade_out_start = max(total_duration - self.music_fade_out, 0)
            voiceover_fade = max(duration - 0.4, 0)
            
            cmd = [
                ffmpeg_path,
                '-y',  # Overwrite output
                '-i', str(voiceover_path),  # Voiceover input
                '-i', str(music_path),  # Music input
                '-filter_complex',
                f"[0:a]volume={self.voiceover_volume},"
                f"afade=t=out:st={voiceover_fade}:d=0.4[vo];"
                f"[1:a]volume={self.music_volume},"
                f"afade=t=in:st=0:d={self.music_fade_in},"
                f"aloop=loop=-1:size=2e+09,"
                f"atrim=0:{total_duration + self.music_fade_out},"
                f"afade=t=out:st={fade_out_start}:d={self.music_fade_out}[music];"
                f"[vo][music]amix=inputs=2:duration=longest:dropout_transition=2[mixed]",
                '-map', '[mixed]',
                '-c:a', codec,
                '-b:a', self.audio_bitrate,
                '-t', str(total_duration),
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg command to mix audio...")
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully mixed audio: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error mixing audio with FFmpeg: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def mix_audio_for_all_days(
        self,
        voiceover_files: Dict[int, Path],
        destination: str
    ) -> Dict[int, Path]:
        """
        Mix audio for all days
        
        Args:
            voiceover_files: Dictionary mapping day numbers to voiceover paths
            destination: Destination name
            
        Returns:
            Dictionary mapping day numbers to mixed audio paths
        """
        try:
            mixed_audio_files = {}
            
            logger.info(f"Mixing audio for {len(voiceover_files)} days...")
            
            for day_number, voiceover_path in voiceover_files.items():
                mixed_audio_path = self.mix_audio_for_day(
                    voiceover_path,
                    day_number,
                    destination
                )
                
                if mixed_audio_path:
                    mixed_audio_files[day_number] = mixed_audio_path
                else:
                    logger.warning(f"Failed to mix audio for day {day_number}")
            
            logger.info(f"✅ Mixed audio for {len(mixed_audio_files)} days")
            return mixed_audio_files
            
        except Exception as e:
            logger.error(f"Error mixing audio for all days: {e}")
            return {}
    
    def combine_audio_files(
        self,
        audio_files: List[Path],
        output_path: Path
    ) -> bool:
        """
        Combine multiple audio files into one
        
        Args:
            audio_files: List of audio file paths
            output_path: Output audio path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not audio_files:
                logger.error("No audio files to combine")
                return False
            
            # Create concat file list
            concat_file = self.temp_dir / "audio_concat.txt"
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                for audio_path in audio_files:
                    # Use absolute path and escape single quotes
                    abs_path = str(audio_path.absolute()).replace("'", "'\\''")
                    f.write(f"file '{abs_path}'\n")
            
            # Build FFmpeg command
            ffmpeg_path = get_ffmpeg_path()
            cmd = [
                ffmpeg_path,
                '-y',  # Overwrite output
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c:a', self.audio_codec,
                '-b:a', self.audio_bitrate,
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg command to combine audio files...")
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up concat file
            if concat_file.exists():
                concat_file.unlink()
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully combined audio files: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error combining audio files: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def cleanup_temp_files(self, mixed_audio_files: Dict[int, Path], keep_final: bool = True):
        """
        Clean up temporary mixed audio files
        
        Args:
            mixed_audio_files: Dictionary mapping day numbers to mixed audio paths
            keep_final: Whether to keep the final combined audio
        """
        try:
            logger.info("Cleaning up temporary audio files...")
            
            # Delete mixed audio files
            for day_number, audio_path in mixed_audio_files.items():
                if audio_path.exists():
                    audio_path.unlink()
                    logger.info(f"Deleted day {day_number} mixed audio: {audio_path}")
            
            # Clean up temp directory
            temp_files = list(self.temp_dir.glob("*.mp3"))
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.info(f"Deleted temp audio file: {temp_file}")
            
            logger.info("✅ Cleaned up temporary audio files")
            
        except Exception as e:
            logger.error(f"Error cleaning up temporary audio files: {e}")


def main():
    """Test audio mixer"""
    from core.media.audio.voiceover_generator_long import VoiceoverGeneratorLong
    from core.content.generation.script_generator_long import ScriptGeneratorLong
    
    # Generate voiceovers
    script_generator = ScriptGeneratorLong()
    voiceover_generator = VoiceoverGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing audio mixer for {test_destination}")
    
    # Load or generate script
    script_data = script_generator.load_script(test_destination)
    
    if not script_data:
        logger.error("Script not found")
        return
    
    # Generate voiceovers
    voiceover_files = voiceover_generator.generate_voiceovers_for_script(script_data, test_destination)
    
    # Mix audio
    audio_mixer = AudioMixerLong()
    mixed_audio_files = audio_mixer.mix_audio_for_all_days(voiceover_files, test_destination)
    
    logger.info(f"✅ Mixed audio for {len(mixed_audio_files)} days")


if __name__ == "__main__":
    main()


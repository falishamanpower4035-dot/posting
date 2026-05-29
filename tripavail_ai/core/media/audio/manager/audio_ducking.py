#!/usr/bin/env python3
"""
Audio Ducking Module for TripAvail AI
Lowers background music volume when voiceover is playing
"""

from pathlib import Path
from typing import Optional, Tuple, Dict
from loguru import logger
from moviepy import AudioFileClip, CompositeAudioClip
import numpy as np


class AudioDucker:
    """Handles audio ducking - lowering background music during voiceover"""
    
    def __init__(self, music_volume: float = 0.15, ducked_volume: float = 0.05):
        """
        Initialize audio ducker
        
        Args:
            music_volume: Normal background music volume (0.0-1.0)
            ducked_volume: Reduced volume when voiceover plays (0.0-1.0)
        """
        self.music_volume = music_volume
        self.ducked_volume = ducked_volume
        
        logger.info(f"Audio Ducker initialized (normal: {music_volume}, ducked: {ducked_volume})")
    
    def create_ducked_audio(
        self,
        voiceover_path: Path,
        music_path: Path,
        output_path: Path,
        fade_duration: float = 0.5
    ) -> bool:
        """
        Create audio track with ducking effect
        
        Args:
            voiceover_path: Path to voiceover audio file
            music_path: Path to background music file
            output_path: Path to save mixed audio
            fade_duration: Duration of fade in/out for ducking effect
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating ducked audio mix...")
            
            # Load audio files
            voiceover = AudioFileClip(str(voiceover_path))
            music = AudioFileClip(str(music_path))
            
            # Get voiceover duration
            vo_duration = voiceover.duration
            
            # Loop or trim music to match voiceover duration
            if music.duration < vo_duration:
                # Loop music if it's shorter than voiceover
                loops_needed = int(np.ceil(vo_duration / music.duration))
                music = music.loop(n=loops_needed)
            
            # Trim music to exact voiceover duration
            music = music.subclipped(0, vo_duration)
            
            # Apply ducking: lower music volume when voiceover plays
            # We'll create a time-varying volume effect
            music_ducked = self._apply_ducking_effect(
                music, 
                vo_duration,
                fade_duration
            )
            
            # Composite: voiceover at full volume + ducked music
            final_audio = CompositeAudioClip([
                voiceover.with_volume_scaled(1.0),  # Full volume voiceover
                music_ducked
            ])
            
            # Write output
            final_audio.write_audiofile(
                str(output_path),
                fps=44100,
                nbytes=2,
                codec='libmp3lame',
                bitrate='192k',
                logger=None
            )
            
            # Close clips
            voiceover.close()
            music.close()
            final_audio.close()
            
            logger.info(f"Ducked audio saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ducked audio: {e}")
            return False
    
    def _apply_ducking_effect(
        self,
        music_clip: AudioFileClip,
        duration: float,
        fade_duration: float
    ) -> AudioFileClip:
        """
        Apply ducking effect to music clip
        
        The music will:
        - Start at ducked volume (intro fade)
        - Stay at ducked volume during voiceover
        - Fade to normal volume at end (outro fade)
        """
        # Simple approach: keep music at ducked volume throughout
        # with smooth fade in/out
        ducked_music = music_clip.with_volume_scaled(self.ducked_volume)
        
        # Add fade in at start
        if fade_duration > 0:
            ducked_music = ducked_music.with_effects([
                lambda clip: clip.with_volume_scaled(
                    lambda t: min(1.0, t / fade_duration) if t < fade_duration else 1.0
                )
            ])
        
        return ducked_music
    
    def create_simple_mix(
        self,
        voiceover_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: Optional[float] = None
    ) -> bool:
        """
        Create simple audio mix without advanced ducking
        
        Args:
            voiceover_path: Path to voiceover audio file
            music_path: Path to background music file
            output_path: Path to save mixed audio
            music_volume: Background music volume (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating simple audio mix...")
            
            volume = music_volume if music_volume is not None else self.ducked_volume
            
            # Load audio files
            voiceover = AudioFileClip(str(voiceover_path))
            music = AudioFileClip(str(music_path))
            
            # Get voiceover duration
            vo_duration = voiceover.duration
            
            # Loop or trim music to match voiceover duration
            if music.duration < vo_duration:
                loops_needed = int(np.ceil(vo_duration / music.duration))
                music = music.loop(n=loops_needed)
            
            music = music.subclipped(0, vo_duration)
            
            # Set music volume
            music = music.with_volume_scaled(volume)
            
            # Composite audio
            final_audio = CompositeAudioClip([
                voiceover.with_volume_scaled(1.0),
                music
            ])
            
            # Write output
            final_audio.write_audiofile(
                str(output_path),
                fps=44100,
                nbytes=2,
                codec='libmp3lame',
                bitrate='192k',
                logger=None
            )
            
            # Close clips
            voiceover.close()
            music.close()
            final_audio.close()
            
            logger.info(f"Mixed audio saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create audio mix: {e}")
            return False
    
    def analyze_audio_levels(self, audio_path: Path) -> Dict[str, float]:
        """
        Analyze audio levels of a file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio statistics
        """
        try:
            audio = AudioFileClip(str(audio_path))
            
            # Get audio array
            audio_array = audio.to_soundarray(fps=44100)
            
            # Calculate statistics
            max_amplitude = float(np.max(np.abs(audio_array)))
            avg_amplitude = float(np.mean(np.abs(audio_array)))
            rms = float(np.sqrt(np.mean(audio_array ** 2)))
            
            audio.close()
            
            stats = {
                "duration": audio.duration,
                "max_amplitude": max_amplitude,
                "avg_amplitude": avg_amplitude,
                "rms": rms,
                "peak_db": 20 * np.log10(max_amplitude) if max_amplitude > 0 else -np.inf
            }
            
            logger.info(f"Audio analysis for {audio_path.name}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to analyze audio: {e}")
            return {}


def main():
    """Test audio ducking"""
    ducker = AudioDucker(music_volume=0.2, ducked_volume=0.05)
    
    # Test paths (adjust as needed)
    voiceover = Path("data/audio/voiceovers/1.mp3")
    music = Path("data/audio/music/upbeat_travel_1.mp3")
    output = Path("data/audio/test_ducked_output.mp3")
    
    if voiceover.exists() and music.exists():
        print("\n=== Testing Audio Ducking ===")
        success = ducker.create_simple_mix(voiceover, music, output)
        if success:
            print(f"✅ Ducked audio created: {output}")
        else:
            print("❌ Failed to create ducked audio")
    else:
        print("⚠️ Test files not found")
        print(f"Voiceover: {voiceover} (exists: {voiceover.exists()})")
        print(f"Music: {music} (exists: {music.exists()})")


if __name__ == "__main__":
    main()


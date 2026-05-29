#!/usr/bin/env python3
"""
Voiceover Generator for Long Videos
Generates voiceovers using ElevenLabs API
Creates per-day voiceover files from narration
"""

import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv

# Import synthesize function at module level to avoid import issues
try:
    from core.media.audio.manager.elevenlabs_tts import synthesize
except ImportError as e:
    logger.warning(f"Could not import synthesize function: {e}")
    synthesize = None

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

load_dotenv()


class VoiceoverGeneratorLong:
    """
    Generates voiceovers using ElevenLabs API
    Creates per-day voiceover files from narration
    """
    
    def __init__(self):
        self.api_key = settings_long.ELEVENLABS_API_KEY_LONG
        self.api_url = "https://api.elevenlabs.io/v1/text-to-speech"
        self.voice_id = settings_long.ELEVENLABS_VOICE_ID_LONG or os.getenv('ELEVENLABS_VOICE_ID_LONG', '')
        self.model = settings_long.ELEVENLABS_MODEL_LONG
        self.tts_settings = settings_long.ELEVENLABS_TTS_LONG
        
        # Output directory
        self.voiceovers_dir = Path(settings_long.VOICEOVERS_DIR)
        self.voiceovers_dir.mkdir(parents=True, exist_ok=True)
        
        # Use fallback voice ID if not set (should be set in config)
        if not self.voice_id:
            logger.warning("Voice ID not set, attempting to get default voice...")
            self.voice_id = self._get_default_voice_id()
            if not self.voice_id:
                # Final fallback
                self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - common default voice
                logger.warning(f"Using fallback voice ID: {self.voice_id}")
        
        logger.info("Voiceover Generator Long initialized")
        logger.info(f"Using voice ID: {self.voice_id}")
        logger.info(f"Using model: {self.model}")
        logger.info(f"API Key: {self.api_key[:10]}...{self.api_key[-10:]}" if self.api_key else "API Key: NOT SET")
    
    def _get_default_voice_id(self) -> str:
        """
        Get default voice ID from ElevenLabs
        
        Returns:
            Default voice ID
        """
        try:
            url = "https://api.elevenlabs.io/v1/voices"
            headers = {
                "xi-api-key": self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            voices = data.get('voices', [])
            
            if voices:
                # Get first available voice
                default_voice = voices[0]
                voice_id = default_voice.get('voice_id', '')
                voice_name = default_voice.get('name', 'Unknown')
                
                logger.info(f"Using default voice: {voice_name} (ID: {voice_id})")
                return voice_id
            
            logger.warning("No voices found, using empty voice ID")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get default voice ID: {e}")
            return ""
    
    def generate_voiceover(self, text: str, output_path: Path, voice_id: Optional[str] = None) -> bool:
        """
        Generate voiceover from text using ElevenLabs TTS manager
        
        Args:
            text: Text to convert to speech
            output_path: Path to save voiceover file
            voice_id: Voice ID to use (default: self.voice_id)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.api_key:
                logger.error("ElevenLabs API key not found")
                return False
            
            if not voice_id:
                voice_id = self.voice_id
            
            # Use fallback voice ID if not set
            if not voice_id:
                logger.warning("Voice ID not found, using fallback voice ID")
                voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - common default voice
            
            # Use the TTS manager function for consistency
            if synthesize is None:
                logger.error("synthesize function not available")
                return False
            
            success = synthesize(
                text=text,
                output_path=output_path,
                api_key=self.api_key,
                voice_id=voice_id,
                model=self.model,
                voice_stability=self.tts_settings.get("stability", 0.5),
                voice_similarity_boost=self.tts_settings.get("similarity_boost", 0.75),
                style=self.tts_settings.get("style", 0.4),
                use_speaker_boost=self.tts_settings.get("use_speaker_boost", True),
            )
            
            if success:
                logger.info(f"✅ Generated voiceover: {output_path}")
                return True
            else:
                logger.error(f"Failed to generate voiceover: {output_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating voiceover: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def generate_voiceover_for_day(
        self,
        day_data: Dict[str, Any],
        destination: str,
        output_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Generate voiceover for a day
        
        Args:
            day_data: Day data with narration
            destination: Destination name
            output_dir: Output directory (default: self.voiceovers_dir)
            
        Returns:
            Path to voiceover file or None if failed
        """
        try:
            if output_dir is None:
                output_dir = self.voiceovers_dir
            
            day_number = day_data.get('day_number', 0)
            narration = day_data.get('narration', '')
            
            if not narration:
                logger.warning(f"Day {day_number} has no narration")
                return None
            
            # Create output path
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            output_path = output_dir / f"{safe_destination}_day_{day_number}_voiceover.mp3"
            
            # Generate voiceover
            success = self.generate_voiceover(narration, output_path)
            
            if success:
                return output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate voiceover for day {day_data.get('day_number', 0)}: {e}")
            return None
    
    def generate_voiceovers_for_script(
        self,
        script_data: Dict[str, Any],
        destination: str,
        output_dir: Optional[Path] = None
    ) -> Dict[int, Path]:
        """
        Generate voiceovers for all days in script
        
        Args:
            script_data: Script data with days
            destination: Destination name
            output_dir: Output directory (default: self.voiceovers_dir)
            
        Returns:
            Dictionary mapping day numbers to voiceover file paths
        """
        try:
            if output_dir is None:
                output_dir = self.voiceovers_dir
            
            days = script_data.get('days', [])
            voiceover_files = {}
            
            logger.info(f"Generating voiceovers for {len(days)} days...")
            
            for day in days:
                day_number = day.get('day_number', 0)
                
                logger.info(f"Generating voiceover for day {day_number}...")
                
                voiceover_path = self.generate_voiceover_for_day(day, destination, output_dir)
                
                if voiceover_path:
                    voiceover_files[day_number] = voiceover_path
                else:
                    logger.warning(f"Failed to generate voiceover for day {day_number}")
            
            logger.info(f"✅ Generated {len(voiceover_files)} voiceovers")
            return voiceover_files
            
        except Exception as e:
            logger.error(f"Failed to generate voiceovers for script: {e}")
            return {}
    
    def get_voiceover_duration(self, voiceover_path: Path) -> float:
        """
        Get duration of voiceover file in seconds
        
        Args:
            voiceover_path: Path to voiceover file
            
        Returns:
            Duration in seconds
        """
        try:
            # Try to use mutagen for MP3 duration
            try:
                from mutagen.mp3 import MP3
                audio = MP3(voiceover_path)
                duration = audio.info.length
                return duration
            except ImportError:
                logger.warning("mutagen not available, using ffprobe for duration")
                # Fallback to ffprobe
                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(voiceover_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    duration = float(result.stdout.strip())
                    return duration
                else:
                    logger.error(f"Failed to get duration using ffprobe: {result.stderr}")
                    return 0.0
                    
        except Exception as e:
            logger.error(f"Failed to get voiceover duration: {e}")
            return 0.0


def main():
    """Test voiceover generator"""
    from core.content.generation.script_generator_long import ScriptGeneratorLong
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    
    # Generate script first
    itinerary_generator = ItineraryGeneratorLong()
    script_generator = ScriptGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing voiceover generator for {test_destination}")
    
    # Load or generate script
    script_data = script_generator.load_script(test_destination)
    if not script_data:
        # Load or generate itinerary
        itinerary_data = itinerary_generator.load_itinerary(test_destination)
        if not itinerary_data:
            logger.info("Generating itinerary first...")
            itinerary_data = itinerary_generator.generate_itinerary(test_destination, max_duration_minutes=8)
            itinerary_generator.save_itinerary(itinerary_data, test_destination)
        
        # Generate script
        logger.info("Generating script...")
        script_data = script_generator.generate_script(itinerary_data)
        script_generator.save_script(script_data, test_destination)
    
    # Generate voiceovers
    voiceover_generator = VoiceoverGeneratorLong()
    voiceover_files = voiceover_generator.generate_voiceovers_for_script(script_data, test_destination)
    
    # Print results
    logger.info(f"Generated {len(voiceover_files)} voiceovers:")
    for day_number, voiceover_path in voiceover_files.items():
        duration = voiceover_generator.get_voiceover_duration(voiceover_path)
        logger.info(f"  Day {day_number}: {voiceover_path} ({duration:.2f} seconds)")


if __name__ == "__main__":
    main()


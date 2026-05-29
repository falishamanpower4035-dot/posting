"""
Ambient Sound Manager - ElevenLabs Sound Effects Integration
PREMIUM Creator Plan Feature
"""

import os
from pathlib import Path
from typing import Optional, Dict
from loguru import logger


class AmbientSoundManager:
    """
    Manages ambient background sounds using ElevenLabs Sound Generation API
    Creator Plan premium feature for adding atmospheric audio
    """
    
    def __init__(self):
        self.sounds_dir = Path("assets/audio/ambient_elevenlabs")
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Load settings
        try:
            from config import settings
            self.api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
            self.enabled = getattr(settings, 'ELEVENLABS_SOUND_EFFECTS', {}).get('enabled', True)
            self.duration = getattr(settings, 'ELEVENLABS_SOUND_EFFECTS', {}).get('duration', 3.0)
            self.prompt_influence = getattr(settings, 'ELEVENLABS_SOUND_EFFECTS', {}).get('prompt_influence', 0.3)
            self.prompts = getattr(settings, 'ELEVENLABS_SOUND_PROMPTS', {})
        except:
            self.api_key = os.getenv('ELEVENLABS_API_KEY')
            self.enabled = True
            self.duration = 3.0
            self.prompt_influence = 0.3
            self.prompts = {}
        
        logger.info(f"AmbientSoundManager initialized (enabled: {self.enabled})")
    
    def get_ambient_for_content_type(
        self,
        content_type: str,
        duration: Optional[float] = None,
        force_regenerate: bool = False
    ) -> Optional[Path]:
        """
        Get or generate ambient sound for a content type
        
        Args:
            content_type: Type of content (adventure, beach, cultural, etc.)
            duration: Sound duration in seconds (default from config)
            force_regenerate: Force new generation even if cached
        
        Returns:
            Path to ambient sound file, or None if disabled/failed
        """
        if not self.enabled or not self.api_key:
            logger.debug("ElevenLabs Sound Effects disabled or API key missing")
            return None
        
        # Check cache first
        cache_file = self.sounds_dir / f"{content_type}_ambient.mp3"
        if cache_file.exists() and not force_regenerate:
            logger.info(f"Using cached ambient sound: {cache_file}")
            return cache_file
        
        # Get prompt for content type
        prompt = self.prompts.get(content_type, self.prompts.get('default', 
            "Subtle ambient background suitable for travel content"))
        
        # Generate new sound
        sound_duration = duration or self.duration
        logger.info(f"Generating ambient sound for '{content_type}' ({sound_duration}s)")
        
        success = self._generate_sound_effect(prompt, cache_file, sound_duration)
        
        if success and cache_file.exists():
            return cache_file
        
        logger.warning(f"Failed to generate ambient sound for '{content_type}'")
        return None
    
    def _generate_sound_effect(
        self,
        prompt: str,
        output_path: Path,
        duration: float
    ) -> bool:
        """
        Generate sound effect using ElevenLabs API
        
        Args:
            prompt: Description of sound
            output_path: Where to save
            duration: Length in seconds
        
        Returns:
            True if successful
        """
        try:
            from core.media.audio.manager.elevenlabs_tts import generate_sound_effect
            
            return generate_sound_effect(
                prompt=prompt,
                output_path=output_path,
                api_key=self.api_key,
                duration_seconds=duration,
                prompt_influence=self.prompt_influence
            )
        except Exception as e:
            logger.error(f"Error generating sound effect: {e}")
            return False
    
    def generate_all_ambient_sounds(self, force: bool = False) -> Dict[str, Path]:
        """
        Pre-generate all ambient sounds for caching
        Useful for initial setup
        
        Args:
            force: Force regeneration of existing sounds
        
        Returns:
            Dictionary mapping content_type to sound file path
        """
        results = {}
        
        for content_type in self.prompts.keys():
            sound_path = self.get_ambient_for_content_type(
                content_type,
                force_regenerate=force
            )
            if sound_path:
                results[content_type] = sound_path
                logger.info(f"✓ {content_type}: {sound_path}")
            else:
                logger.warning(f"✗ {content_type}: Failed")
        
        return results
    
    def clear_cache(self):
        """Remove all cached ambient sounds"""
        import shutil
        if self.sounds_dir.exists():
            shutil.rmtree(self.sounds_dir)
            self.sounds_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Ambient sound cache cleared")


def main():
    """Test ambient sound generation"""
    manager = AmbientSoundManager()
    
    print("\n=== ElevenLabs Ambient Sound Generator ===\n")
    print(f"API Key: {'✓ Configured' if manager.api_key else '✗ Missing'}")
    print(f"Enabled: {manager.enabled}")
    print(f"Sound Directory: {manager.sounds_dir}\n")
    
    if not manager.enabled or not manager.api_key:
        print("⚠️  ElevenLabs Sound Effects not configured")
        print("Set ELEVENLABS_API_KEY and enable in config/settings.py")
        return
    
    print("Generating ambient sounds for all content types...\n")
    
    results = manager.generate_all_ambient_sounds(force=False)
    
    print(f"\n✅ Generated {len(results)} ambient sounds!")
    print(f"📂 Saved to: {manager.sounds_dir}")
    print("\nSound files:")
    for content_type, path in results.items():
        print(f"  • {content_type}: {path.name}")


if __name__ == "__main__":
    main()


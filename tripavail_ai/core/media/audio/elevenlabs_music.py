#!/usr/bin/env python3
"""
ElevenLabs Music Generator - Smart Background Music
Generates AI-powered instrumental background music based on content type
"""

from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import os

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs library not available. Install with: pip install elevenlabs")


class ElevenLabsMusicGenerator:
    """
    Smart background music generator using ElevenLabs Music API
    
    Features:
    - Content-aware music selection (luxury, adventure, cultural, etc.)
    - AI-generated instrumental tracks (20 seconds)
    - Professional quality (44.1kHz, MP3)
    - Commercial use cleared
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize ElevenLabs Music Generator
        
        Args:
            api_key: ElevenLabs API key (or use ELEVENLABS_MUSIC_API_KEY env var)
        """
        # Try multiple sources for API key
        if not api_key:
            try:
                from config.settings import ELEVENLABS_MUSIC_API_KEY
                api_key = ELEVENLABS_MUSIC_API_KEY
            except (ImportError, AttributeError):
                pass
        
        self.api_key = api_key or os.getenv("ELEVENLABS_MUSIC_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        
        if not self.api_key:
            logger.error("No ElevenLabs API key provided")
            self.client = None
            return
        
        if not ELEVENLABS_AVAILABLE:
            logger.error("ElevenLabs library not installed")
            self.client = None
            return
        
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            logger.info("✅ ElevenLabs Music API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs client: {e}")
            self.client = None
        
        # Smart music prompts for different content types
        self.music_prompts = {
            "luxury": "Elegant and sophisticated instrumental with piano, strings, and subtle electronic elements. Tempo: 85 bpm, refined and upscale mood. Perfect for luxury travel content.",
            
            "adventure": "Energetic and adventurous instrumental featuring acoustic guitar, light drums, and uplifting melodies. Tempo: 120 bpm, exciting and inspiring mood. Perfect for adventure travel.",
            
            "cultural": "World music inspired instrumental with ethnic instruments, ambient textures, and meditative tones. Tempo: 90 bpm, contemplative and enriching mood. Perfect for cultural experiences.",
            
            "beach": "Tropical and relaxing instrumental with steel drums, acoustic guitar, and ocean-inspired sounds. Tempo: 95 bpm, carefree and sunny mood. Perfect for beach destinations.",
            
            "wellness": "Calm and peaceful instrumental featuring soft piano, nature sounds, and ambient pads. Tempo: 70 bpm, serene and restorative mood. Perfect for wellness and spa content.",
            
            "family": "Warm and friendly instrumental with cheerful melodies, light percussion, and playful elements. Tempo: 110 bpm, joyful and welcoming mood. Perfect for family travel.",
            
            "city": "Modern and dynamic instrumental with electronic beats, synth melodies, and urban energy. Tempo: 115 bpm, vibrant and cosmopolitan mood. Perfect for city exploration.",
            
            "nature": "Organic and tranquil instrumental featuring acoustic instruments, ambient textures, and natural soundscapes. Tempo: 80 bpm, peaceful and grounding mood. Perfect for nature content.",
            
            "hotel": "Professional and refined instrumental with piano, strings, and sophisticated ambiance. Tempo: 90 bpm, elegant and welcoming mood. Perfect for hotel and resort content.",
            
            "resort": "Luxurious and relaxing instrumental with tropical influences, smooth melodies, and resort ambiance. Tempo: 85 bpm, indulgent and escapist mood. Perfect for resort content.",
            
            "government": "Formal and authoritative instrumental with orchestral elements, dignified tones, and official atmosphere. Tempo: 80 bpm, serious and professional mood. Perfect for government announcements.",
            
            "good_news": "Uplifting and positive instrumental with bright melodies, cheerful tones, and optimistic energy. Tempo: 120 bpm, joyful and hopeful mood. Perfect for positive news.",
            
            "motivational": "Inspiring and powerful instrumental with building crescendos, epic strings, and motivational energy. Tempo: 125 bpm, empowering and uplifting mood. Perfect for motivational content.",
            
            "default": "Upbeat instrumental background music featuring piano, acoustic guitar, and light percussion. Tempo: 105 bpm, positive and engaging mood. Perfect for travel content."
        }
    
    def generate_music_for_post(self, metadata: Dict[str, Any], output_path: Path) -> bool:
        """
        Generate background music for a post based on its content type
        
        Args:
            metadata: Post metadata containing content_type and other info
            output_path: Where to save the generated music (MP3)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return False
        
        try:
            # Determine content type
            content_type = metadata.get("content_type", "default")
            logger.info(f"🎵 Generating background music for content type: {content_type}")
            
            # Get appropriate prompt
            prompt = self._get_music_prompt(content_type, metadata)
            logger.info(f"📝 Music prompt: {prompt[:80]}...")
            
            # Generate music (20 seconds max)
            logger.info("🎼 Calling ElevenLabs Music API...")
            track = self.client.music.compose(
                prompt=prompt,
                music_length_ms=20000,  # 20 seconds (API limit)
            )
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                # track is a generator, need to iterate and write
                for chunk in track:
                    f.write(chunk)
            
            logger.info(f"✅ Background music generated: {output_path}")
            logger.info(f"🎵 Duration: 20 seconds | Format: MP3 | Type: {content_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate music: {e}")
            return False
    
    def _get_music_prompt(self, content_type: str, metadata: Dict[str, Any]) -> str:
        """
        Get the appropriate music prompt based on content type
        
        Args:
            content_type: Type of content (luxury, adventure, etc.)
            metadata: Post metadata for additional context
            
        Returns:
            Music generation prompt
        """
        # Get base prompt for content type
        prompt = self.music_prompts.get(content_type, self.music_prompts["default"])
        
        # You could enhance the prompt based on metadata
        # For example, add location-specific elements:
        # locations = metadata.get("locations", {})
        # if locations.get("region") == "Asia":
        #     prompt = prompt.replace("acoustic", "traditional Asian")
        
        return prompt
    
    def get_available_styles(self) -> Dict[str, str]:
        """
        Get all available music styles
        
        Returns:
            Dictionary of content_type: description
        """
        return {
            content_type: prompt.split(".")[0]  # First sentence as description
            for content_type, prompt in self.music_prompts.items()
        }


def test_music_generator():
    """Test the music generator with a sample post"""
    from config.settings import ELEVENLABS_API_KEY
    
    generator = ElevenLabsMusicGenerator(api_key=ELEVENLABS_API_KEY)
    
    # Test metadata
    test_metadata = {
        "post_id": "test",
        "content_type": "adventure",
        "original_title": "Epic Mountain Trekking in Nepal"
    }
    
    output_path = Path("data/test_music.mp3")
    
    print("\n🎵 Testing ElevenLabs Music Generator...")
    print(f"Content Type: {test_metadata['content_type']}")
    print(f"Output: {output_path}")
    
    success = generator.generate_music_for_post(test_metadata, output_path)
    
    if success:
        print(f"✅ Music generated successfully!")
        print(f"📁 File: {output_path}")
        print(f"📊 Size: {output_path.stat().st_size / 1024:.1f} KB")
        print("\n🎧 Play the file to hear the result!")
    else:
        print("❌ Music generation failed")


if __name__ == "__main__":
    test_music_generator()


#!/usr/bin/env python3
"""
Enhanced Voiceover Generator for TripAvail AI
Supports multiple voices, accents, and styles
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from loguru import logger
from openai import OpenAI
from importlib import import_module
from dotenv import load_dotenv

load_dotenv()


class EnhancedVoiceoverGenerator:
    """
    Enhanced voiceover generator with multiple voice options
    Supports different voices, accents, and speaking styles
    """
    
    def __init__(self):
        # OpenAI for script generation and optional TTS fallback
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Try to load ElevenLabs config from env or settings
        self.eleven_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.eleven_voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        self.eleven_voice_map = None
        self.eleven_tts_cfg = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35, "use_speaker_boost": True}
        try:
            # Always load settings to get voice_map and TTS config
            settings = import_module('config.settings')
            # Load API key (env takes precedence, then settings)
            if not self.eleven_api_key:
                self.eleven_api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
            # Load voice ID (env takes precedence, then settings)
            if not self.eleven_voice_id:
                self.eleven_voice_id = getattr(settings, 'ELEVENLABS_VOICE_ID', self.eleven_voice_id)
            # CRITICAL: Always load voice_map from settings (contains premium voice list)
            self.eleven_voice_map = getattr(settings, 'ELEVENLABS_VOICE_MAP', None)
            # Load TTS config from settings
            self.eleven_tts_cfg = getattr(settings, 'ELEVENLABS_TTS', self.eleven_tts_cfg)
            
            # Log voice map status for debugging
            if self.eleven_voice_map:
                logger.info(f"✅ Loaded ELEVENLABS_VOICE_MAP with {len(self.eleven_voice_map)} premium voices")
            else:
                logger.warning("⚠️ ELEVENLABS_VOICE_MAP not found in settings - will use default voice only")
        except Exception as e:
            logger.warning(f"Failed to load ElevenLabs settings: {e}")
            pass
        self.data_dir = Path("data")
        self.audio_dir = self.data_dir / "audio" / "voiceovers"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Available voices from OpenAI TTS
        self.voice_profiles = {
            "alloy": {
                "gender": "neutral",
                "style": "balanced",
                "accent": "american",
                "description": "Neutral, balanced voice suitable for most content"
            },
            "echo": {
                "gender": "male",
                "style": "warm",
                "accent": "american",
                "description": "Warm, friendly male voice"
            },
            "fable": {
                "gender": "male",
                "style": "narrative",
                "accent": "british",
                "description": "British-accented narrative voice"
            },
            "onyx": {
                "gender": "male",
                "style": "deep",
                "accent": "american",
                "description": "Deep, authoritative male voice"
            },
            "nova": {
                "gender": "female",
                "style": "energetic",
                "accent": "american",
                "description": "Energetic, upbeat female voice"
            },
            "shimmer": {
                "gender": "female",
                "style": "warm",
                "accent": "american",
                "description": "Warm, friendly female voice"
            }
        }
        
        # Voice selection rules based on content (UPDATED for more energy!)
        self.content_voice_mapping = {
            "adventure": ["nova", "echo"],      # Changed: Nova (energetic) first!
            "luxury": ["shimmer", "fable"],     # Shimmer is warmer than Fable
            "beach": ["nova", "shimmer"],       # Nova perfect for beach energy
            "cultural": ["alloy", "fable"],     # Alloy more balanced than Fable
            "family": ["nova", "shimmer"],      # Friendly, warm voices
            "wellness": ["shimmer", "alloy"],   # Keep shimmer for calm
            "city": ["nova", "echo"],           # Changed: More energetic
            "nature": ["shimmer", "nova"],      # Warm and engaging
            "default": ["nova", "shimmer"]      # Changed: Nova first for energy!
        }
        
        logger.info("Enhanced Voiceover Generator initialized")
    
    def select_voice_for_content(
        self, 
        caption: str, 
        region: str,
        preferred_gender: Optional[str] = None
    ) -> str:
        """
        Select appropriate voice based on content analysis
        
        Args:
            caption: Post caption/content
            region: Geographic region
            preferred_gender: Optional gender preference (male/female/neutral)
            
        Returns:
            Voice ID to use
        """
        caption_lower = caption.lower()
        region_lower = region.lower()
        
        # Determine content type
        content_type = "default"
        
        if any(word in caption_lower for word in ['adventure', 'explore', 'trek', 'hike']):
            content_type = "adventure"
        elif any(word in caption_lower for word in ['luxury', 'premium', 'exclusive', 'resort']):
            content_type = "luxury"
        elif any(word in caption_lower for word in ['beach', 'ocean', 'island', 'tropical']):
            content_type = "beach"
        elif any(word in caption_lower for word in ['culture', 'heritage', 'tradition', 'historic']):
            content_type = "cultural"
        elif any(word in caption_lower for word in ['family', 'kids', 'children']):
            content_type = "family"
        elif any(word in caption_lower for word in ['wellness', 'spa', 'yoga', 'meditation']):
            content_type = "wellness"
        elif any(word in region_lower for word in ['city', 'urban', 'downtown']):
            content_type = "city"
        elif any(word in region_lower for word in ['forest', 'mountain', 'nature', 'park']):
            content_type = "nature"
        
        # Get suggested voices for content type
        suggested_voices = self.content_voice_mapping.get(content_type, self.content_voice_mapping["default"])
        
        # Filter by gender preference if specified
        if preferred_gender:
            filtered_voices = [
                voice for voice in suggested_voices
                if self.voice_profiles[voice]["gender"] == preferred_gender
            ]
            if filtered_voices:
                suggested_voices = filtered_voices
        
        # Select first suggested voice
        selected_voice = suggested_voices[0]
        
        logger.info(f"Selected voice '{selected_voice}' for content type '{content_type}'")
        return selected_voice
    
    def generate_voiceover(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        model: str = "tts-1-hd",
        speed: float = 1.05,  # Slightly faster for energy (was 1.0)
        eleven_voice_id: Optional[str] = None,
        content_type: str = "default",
    ) -> bool:
        """
        Generate voiceover audio from text
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice: Voice ID (uses AI-selected voice if None)
            model: TTS model to use (tts-1 or tts-1-hd)
            speed: Speaking speed (0.25 to 4.0)
            content_type: Content type for voice selection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if voice is None:
                # Use AI to select the best voice for this content
                voice = self.select_voice_for_content(content_type)
            
            logger.info(f"Generating voiceover with voice '{voice}'...")

            # Prefer ElevenLabs PREMIUM if configured
            if self.eleven_api_key:
                try:
                    from core.media.audio.manager.elevenlabs_tts import synthesize
                    
                    # Get premium Turbo v2.5 model from settings
                    try:
                        from config import settings
                        turbo_model = getattr(settings, 'ELEVENLABS_MODEL', 'eleven_turbo_v2_5')
                    except:
                        turbo_model = 'eleven_turbo_v2_5'  # Default to premium
                    
                    # Use selected voice_id (from voice_map) or fallback to default
                    final_voice_id = eleven_voice_id or self.eleven_voice_id
                    logger.info(f"🎙️ Using ElevenLabs voice: {final_voice_id[:8]}... (content_type: {content_type})")
                    
                    ok = synthesize(
                        text=text,
                        output_path=output_path,
                        api_key=self.eleven_api_key,
                        voice_id=final_voice_id,
                        model=turbo_model,  # PREMIUM: Turbo v2.5
                        voice_stability=self.eleven_tts_cfg.get("stability", 0.5),
                        voice_similarity_boost=self.eleven_tts_cfg.get("similarity_boost", 0.75),
                        style=self.eleven_tts_cfg.get("style", 0.4),
                        use_speaker_boost=self.eleven_tts_cfg.get("use_speaker_boost", True),
                    )
                    if ok:
                        logger.info(f"✅ Voiceover saved to {output_path} (ElevenLabs Turbo v2.5 PREMIUM, voice: {final_voice_id[:8]}...)")
                        return True
                    else:
                        logger.warning("ElevenLabs PREMIUM TTS failed, falling back to OpenAI TTS")
                except Exception as e:
                    logger.warning(f"ElevenLabs PREMIUM TTS error: {e}, falling back to OpenAI TTS")

            # Fallback: OpenAI TTS
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                speed=speed
            )
            response.stream_to_file(str(output_path))
            logger.info(f"Voiceover saved to {output_path} (OpenAI)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate voiceover: {e}")
            return False
    
    def generate_for_post(
        self,
        post: Dict[str, Any],
        voice: Optional[str] = None,
        preferred_gender: Optional[str] = None,
        speed: float = 1.0
    ) -> bool:
        """
        Generate voiceover for a post
        
        Args:
            post: Post data dictionary
            voice: Optional specific voice to use
            preferred_gender: Optional gender preference
            speed: Speaking speed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            post_id = post.get('topic_id', 'unknown')
            caption = post.get('caption', '')
            region = post.get('region', 'Unknown')
            
            # Select OpenAI voice and ElevenLabs voice id
            if voice is None:
                voice = self.select_voice_for_content(caption, region, preferred_gender)
            eleven_voice_id = None
            if self.eleven_api_key:
                content_voice = self._content_type_from_text(caption, region)
                if self.eleven_voice_map and content_voice in self.eleven_voice_map:
                    eleven_voice_id = self.eleven_voice_map.get(content_voice) or self.eleven_voice_id
                else:
                    eleven_voice_id = self.eleven_voice_id
            
            # Generate voiceover script (simplified caption for audio)
            script = self._create_voiceover_script(caption)
            
            # Output path
            output_path = self.audio_dir / f"{post_id}.mp3"
            
            # Generate voiceover
            success = self.generate_voiceover(
                text=script,
                output_path=output_path,
                voice=voice,
                speed=speed,
                eleven_voice_id=eleven_voice_id
            )
            
            if success:
                logger.info(f"Generated voiceover for post {post_id} using voice '{voice}'")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to generate voiceover for post: {e}")
            return False

    def _content_type_from_text(self, caption: str, region: str) -> str:
        """
        SMART VOICE SELECTION: Analyze content to select the perfect voice
        
        Priority order:
        1. Hotel/Resort news
        2. Government/Official announcements
        3. Specific travel types (luxury, adventure, cultural)
        4. Good news/Positive stories
        5. Motivational/Inspiring content
        6. General types (beach, wellness, family, city, nature)
        7. Default
        """
        caption_lower = caption.lower()
        region_lower = region.lower()
        
        # Priority 1: Hotel & Resort News
        hotel_keywords = ['hotel', 'resort', 'accommodation', 'stay', 'suite', 'room', 
                         'booking', 'check-in', 'hospitality', 'lodging', 'inn', 'villa']
        if any(word in caption_lower for word in hotel_keywords):
            logger.debug("🎙️ Detected: HOTEL content")
            return "hotel"
        
        # Priority 2: Government & Official Announcements
        government_keywords = ['government', 'minister', 'ministry', 'official', 'announcement', 
                              'authority', 'regulation', 'policy', 'inaugurate', 'launch',
                              'department', 'administration', 'state', 'federal', 'municipal']
        if any(word in caption_lower for word in government_keywords):
            logger.debug("🎙️ Detected: GOVERNMENT announcement")
            return "government"
        
        # Priority 3: Specific Travel Types (checked before good_news/motivational)
        # Luxury
        if any(word in caption_lower for word in ['luxury', 'premium', 'exclusive', 'five-star', 
                                                   'opulent', 'lavish', 'elegant', 'sophisticated']):
            logger.debug("🎙️ Detected: LUXURY")
            return "luxury"
        
        # Adventure
        if any(word in caption_lower for word in ['trek', 'trekking', 'hike', 'hiking', 'climbing', 
                                                   'safari', 'expedition', 'thrill', 'extreme']):
            logger.debug("🎙️ Detected: ADVENTURE")
            return "adventure"
        
        # Cultural (check before good_news to avoid "celebrates" conflict)
        if any(word in caption_lower for word in ['culture', 'cultural', 'heritage', 'tradition', 'historic',
                                                   'temple', 'monument', 'ancient', 'museum']):
            logger.debug("🎙️ Detected: CULTURAL")
            return "cultural"
        
        # Priority 4: Good News & Positive Stories
        good_news_keywords = ['unveils', 'celebrates', 'opens', 'new', 'amazing', 'stunning',
                             'success', 'win', 'achievement', 'breakthrough', 'milestone',
                             'proud', 'excited', 'thrilled', 'delighted', 'wonderful']
        if any(word in caption_lower for word in good_news_keywords):
            logger.debug("🎙️ Detected: GOOD NEWS")
            return "good_news"
        
        # Priority 5: Motivational & Inspiring Content
        motivational_keywords = ['inspire', 'dream', 'achieve', 'transform', 'journey',
                                'discover', 'experience', 'explore', 'unlock',
                                'elevate', 'empower', 'believe', 'aspire', 'pursue']
        if any(word in caption_lower for word in motivational_keywords):
            logger.debug("🎙️ Detected: MOTIVATIONAL")
            return "motivational"
        
        # Priority 6: General Travel Types
        
        # Beach
        if any(word in caption_lower for word in ['beach', 'ocean', 'island', 'tropical',
                                                   'coast', 'seaside', 'shore']):
            logger.debug("🎙️ Detected: BEACH")
            return "beach"
        
        # Family
        if any(word in caption_lower for word in ['family', 'kids', 'children', 'parents']):
            logger.debug("🎙️ Detected: FAMILY")
            return "family"
        
        # Wellness
        if any(word in caption_lower for word in ['wellness', 'spa', 'yoga', 'meditation',
                                                   'relaxation', 'rejuvenate', 'healing']):
            logger.debug("🎙️ Detected: WELLNESS")
            return "wellness"
        
        # City
        if any(word in region_lower for word in ['city', 'urban', 'downtown', 'metropolitan']):
            logger.debug("🎙️ Detected: CITY")
            return "city"
        
        # Nature
        if any(word in region_lower for word in ['forest', 'mountain', 'nature', 'park',
                                                  'wildlife', 'national park']):
            logger.debug("🎙️ Detected: NATURE")
            return "nature"
        
        # Default fallback
        logger.debug("🎙️ Using DEFAULT voice")
        return "default"
    
    def _create_voiceover_script(self, caption: str) -> str:
        """
        Create a PREMIUM, cinematic voiceover script from caption using AI
        """
        try:
            # Use OpenAI to create a better voiceover script
            prompt = f"""
Transform this social media caption into a compelling 10-15 second voiceover script for a luxury travel video.

Caption: {caption}

VOICEOVER REQUIREMENTS:
✨ Length: 25-40 words (10-15 seconds when spoken)
✨ Style: Cinematic, evocative, documentary-quality narration
✨ Tone: Sophisticated storyteller sharing a secret
✨ Structure: Hook → Sensory detail → Emotional payoff
✨ NO hashtags, emojis, or "you" language
✨ USE: Second person ("you"), present tense, active voice
✨ Add natural rhythm and pacing (short sentences, pauses)

EXAMPLES:

Caption: "As twilight falls, the aroma of jasmine fills the air"
Voiceover: "Twilight. The scent of jasmine drifts through ancient alleyways. This is Bangkok as only locals know it. Feel the pulse of the night market awaken."

Caption: "Sip velvety matcha amidst Kyoto's misty hills"
Voiceover: "In Kyoto's mist-covered highlands, tea farmers have perfected their craft for centuries. One sip. That's all it takes. This is matcha, elevated to art."

Caption: "At 84, every moment radiates vitality"
Voiceover: "Age is just a number. At 84, the world still calls. Every sunrise brings new adventures. This is what living fully looks like."

Create a voiceover script (25-40 words) that captures the essence and makes viewers FEEL the experience:
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a master documentary filmmaker creating cinematic voiceover scripts. Write SHORT (25-40 words), evocative narration that makes viewers feel like they're experiencing something extraordinary. Use sensory language, short punchy sentences, and natural pauses."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=150
            )
            
            script = response.choices[0].message.content.strip()
            
            # Remove any quotes if AI added them
            script = script.strip('"').strip("'")
            
            logger.info(f"Generated premium voiceover script: {script[:50]}...")
            return script
            
        except Exception as e:
            logger.error(f"AI voiceover generation failed: {e}, using fallback")
            # Fallback: simple cleanup
            words = caption.split()
            script_words = [word for word in words if not word.startswith('#')]
            script = ' '.join(script_words)
            script = ''.join(char for char in script if ord(char) < 0x1F600 or ord(char) > 0x1F64F)
            return ' '.join(script.split())
    
    def generate_multiple_versions(
        self,
        post: Dict[str, Any],
        voice_list: List[str]
    ) -> Dict[str, Path]:
        """
        Generate multiple voiceover versions with different voices
        
        Args:
            post: Post data dictionary
            voice_list: List of voice IDs to generate
            
        Returns:
            Dictionary mapping voice ID to output path
        """
        results = {}
        post_id = post.get('topic_id', 'unknown')
        
        for voice in voice_list:
            output_path = self.audio_dir / f"{post_id}_{voice}.mp3"
            success = self.generate_for_post(post, voice=voice)
            
            if success:
                results[voice] = output_path
                logger.info(f"Generated {voice} version for post {post_id}")
        
        return results
    
    def list_available_voices(self) -> Dict[str, Dict[str, str]]:
        """Get all available voice profiles"""
        return self.voice_profiles
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, str]]:
        """Get information about a specific voice"""
        return self.voice_profiles.get(voice_id)
    
    def generate_voice_report(self) -> str:
        """Generate a report of available voices"""
        report = "\n=== TripAvail AI Voice Library ===\n\n"
        report += f"Total Voices: {len(self.voice_profiles)}\n\n"
        
        # Group by gender
        for gender in ["male", "female", "neutral"]:
            voices = {k: v for k, v in self.voice_profiles.items() if v["gender"] == gender}
            report += f"\n{gender.upper()} VOICES ({len(voices)}):\n"
            for voice_id, info in voices.items():
                report += f"  - {voice_id}: {info['description']}\n"
                report += f"    Style: {info['style']}, Accent: {info['accent']}\n"
        
        # Content type recommendations
        report += "\n\nVOICE RECOMMENDATIONS BY CONTENT TYPE:\n"
        for content_type, voices in self.content_voice_mapping.items():
            report += f"  {content_type.upper()}: {', '.join(voices)}\n"
        
        return report


def main():
    """Test enhanced voiceover generator"""
    generator = EnhancedVoiceoverGenerator()
    
    print(generator.generate_voice_report())
    
    # Test voice selection
    print("\n=== Testing Voice Selection ===")
    
    test_cases = [
        {"caption": "Explore the thrilling adventures in Swiss Alps", "region": "Switzerland"},
        {"caption": "Discover luxury resorts in the Maldives", "region": "Maldives"},
        {"caption": "Experience cultural heritage in Kyoto", "region": "Japan"},
        {"caption": "Relax at our wellness spa retreat", "region": "Bali"}
    ]
    
    for test in test_cases:
        voice = generator.select_voice_for_content(test["caption"], test["region"])
        voice_info = generator.get_voice_info(voice)
        print(f"\nContent: {test['caption'][:50]}...")
        print(f"Selected Voice: {voice} ({voice_info['description']})")


if __name__ == "__main__":
    main()


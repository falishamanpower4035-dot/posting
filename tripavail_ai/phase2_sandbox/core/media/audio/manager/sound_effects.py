#!/usr/bin/env python3
"""
Sound Effects Manager for TripAvail AI
Manages sound effects for video transitions and enhancements
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import os
from importlib import import_module
from moviepy import AudioFileClip


class SoundEffectsManager:
    """Manages sound effects for video transitions"""
    
    def __init__(self):
        self.sfx_dir = Path("data/audio/sound_effects")
        self.sfx_manifest_file = self.sfx_dir / "sfx_manifest.json"
        # Try to read ElevenLabs config to enable on-demand SFX generation
        self.eleven_api_key = os.getenv('ELEVENLABS_API_KEY')
        self.eleven_voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        try:
            if not self.eleven_api_key:
                settings = import_module('config.settings')
                self.eleven_api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
                self.eleven_voice_id = getattr(settings, 'ELEVENLABS_VOICE_ID', self.eleven_voice_id)
        except Exception:
            pass
        
        # Create directories
        self.sfx_dir.mkdir(parents=True, exist_ok=True)
        
        # Sound effect categories
        self.sfx_categories = {
            "transition": ["whoosh", "swipe", "fade", "slide"],
            "ambient": ["wind", "waves", "birds", "city"],
            "impact": ["boom", "hit", "pop", "click"],
            "ui": ["beep", "notification", "success", "error"]
        }
        
        # Initialize manifest
        self.sfx_manifest = self.load_manifest()
        
        logger.info("Sound Effects Manager initialized")
    
    def load_manifest(self) -> Dict:
        """Load sound effects manifest"""
        if self.sfx_manifest_file.exists():
            try:
                with open(self.sfx_manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load SFX manifest: {e}")
        
        return self.create_default_manifest()
    
    def create_default_manifest(self) -> Dict:
        """Create default sound effects manifest"""
        manifest = {
            "version": "1.0",
            "sound_effects": [
                {
                    "id": "whoosh_1",
                    "name": "Smooth Whoosh",
                    "category": "transition",
                    "type": "whoosh",
                    "duration": 0.5,
                    "file_path": "data/audio/sound_effects/whoosh_1.mp3",
                    "volume": 0.3,
                    "license": "Royalty-Free"
                },
                {
                    "id": "swipe_1",
                    "name": "Quick Swipe",
                    "category": "transition",
                    "type": "swipe",
                    "duration": 0.3,
                    "file_path": "data/audio/sound_effects/swipe_1.mp3",
                    "volume": 0.25,
                    "license": "Royalty-Free"
                },
                {
                    "id": "fade_1",
                    "name": "Gentle Fade",
                    "category": "transition",
                    "type": "fade",
                    "duration": 0.8,
                    "file_path": "data/audio/sound_effects/fade_1.mp3",
                    "volume": 0.2,
                    "license": "Royalty-Free"
                },
                {
                    "id": "waves_ambient",
                    "name": "Ocean Waves",
                    "category": "ambient",
                    "type": "waves",
                    "duration": 10.0,
                    "file_path": "data/audio/sound_effects/waves_ambient.mp3",
                    "volume": 0.15,
                    "license": "Royalty-Free"
                },
                {
                    "id": "city_ambient",
                    "name": "City Sounds",
                    "category": "ambient",
                    "type": "city",
                    "duration": 10.0,
                    "file_path": "data/audio/sound_effects/city_ambient.mp3",
                    "volume": 0.12,
                    "license": "Royalty-Free"
                },
                {
                    "id": "pop_1",
                    "name": "Light Pop",
                    "category": "impact",
                    "type": "pop",
                    "duration": 0.2,
                    "file_path": "data/audio/sound_effects/pop_1.mp3",
                    "volume": 0.4,
                    "license": "Royalty-Free"
                }
            ],
            "free_sfx_sources": [
                {
                    "name": "Freesound",
                    "url": "https://freesound.org/",
                    "license": "Creative Commons"
                },
                {
                    "name": "Zapsplat",
                    "url": "https://www.zapsplat.com/",
                    "license": "Royalty-Free"
                },
                {
                    "name": "Pixabay Sound Effects",
                    "url": "https://pixabay.com/sound-effects/",
                    "license": "Pixabay License"
                },
                {
                    "name": "BBC Sound Effects",
                    "url": "https://sound-effects.bbcrewind.co.uk/",
                    "license": "RemArc License"
                }
            ]
        }
        
        self.save_manifest(manifest)
        return manifest
    
    def save_manifest(self, manifest: Dict):
        """Save sound effects manifest"""
        try:
            with open(self.sfx_manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved SFX manifest to {self.sfx_manifest_file}")
        except Exception as e:
            logger.error(f"Failed to save SFX manifest: {e}")
    
    def get_transition_effect(self, transition_type: str = "whoosh") -> Optional[Dict]:
        """Get a transition sound effect"""
        effects = self.sfx_manifest.get('sound_effects', [])
        transition_effects = [
            sfx for sfx in effects 
            if sfx.get('category') == 'transition' and sfx.get('type') == transition_type
        ]
        
        if transition_effects:
            effect = transition_effects[0]
            self._ensure_file(effect)
            return effect
        
        # Return any transition effect as fallback
        transition_effects = [sfx for sfx in effects if sfx.get('category') == 'transition']
        return transition_effects[0] if transition_effects else None
    
    def get_ambient_effect(self, region: str) -> Optional[Dict]:
        """Get ambient sound effect based on region"""
        region_lower = region.lower()
        
        # Region-based ambient selection
        if any(keyword in region_lower for keyword in ['beach', 'ocean', 'island', 'coast']):
            effect_type = "waves"
        elif any(keyword in region_lower for keyword in ['city', 'urban', 'downtown']):
            effect_type = "city"
        elif any(keyword in region_lower for keyword in ['forest', 'jungle', 'nature']):
            effect_type = "birds"
        else:
            return None
        
        effects = self.sfx_manifest.get('sound_effects', [])
        ambient_effects = [
            sfx for sfx in effects 
            if sfx.get('category') == 'ambient' and sfx.get('type') == effect_type
        ]
        
        if ambient_effects:
            effect = ambient_effects[0]
            self._ensure_file(effect)
            return effect
        return None

    def _ensure_file(self, sfx: Dict):
        """Ensure the SFX file exists; try to generate via ElevenLabs if missing."""
        try:
            path = Path(sfx.get('file_path', ''))
            if path.exists():
                return
            # Attempt to synthesize short SFX with ElevenLabs (best-effort)
            if self.eleven_api_key:
                prompt = self._prompt_for_type(sfx.get('type', 'whoosh'))
                out = path
                out.parent.mkdir(parents=True, exist_ok=True)
                try:
                    from core.media.audio.manager.elevenlabs_tts import synthesize as tts
                    # Use TTS to produce a short effect-like sound by descriptive prompt
                    ok = tts(prompt, out, api_key=self.eleven_api_key, voice_id=self.eleven_voice_id)
                    if ok:
                        logger.info(f"Generated SFX via ElevenLabs: {out}")
                except Exception as e:
                    logger.debug(f"Unable to auto-generate SFX: {e}")
        except Exception:
            pass

    def _prompt_for_type(self, effect_type: str) -> str:
        mapping = {
            'whoosh': 'A short cinematic whoosh transition sound, airy and modern',
            'swipe': 'A quick swipe whoosh sound, clean, techy',
            'fade': 'A gentle swell that fades smoothly',
            'waves': 'Soft ocean wave ambience, distant shoreline',
            'city': 'Light city ambience: soft traffic hum, distant chatter',
            'birds': 'Subtle tropical birds ambience',
            'pop': 'Short soft pop click for UI',
        }
        return mapping.get(effect_type, 'Short cinematic transition sound')
    
    def list_all_effects(self) -> List[Dict]:
        """List all available sound effects"""
        return self.sfx_manifest.get('sound_effects', [])
    
    def add_sound_effect(self, sfx_info: Dict) -> bool:
        """Add a new sound effect to the library"""
        try:
            effects = self.sfx_manifest.get('sound_effects', [])
            
            # Check if effect already exists
            if any(sfx['id'] == sfx_info['id'] for sfx in effects):
                logger.warning(f"Sound effect {sfx_info['id']} already exists")
                return False
            
            effects.append(sfx_info)
            self.sfx_manifest['sound_effects'] = effects
            self.save_manifest(self.sfx_manifest)
            
            logger.info(f"Added sound effect: {sfx_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add sound effect: {e}")
            return False
    
    def generate_sfx_report(self) -> str:
        """Generate a report of available sound effects"""
        effects = self.list_all_effects()
        report = "\n=== TripAvail AI Sound Effects Library ===\n\n"
        report += f"Total Effects: {len(effects)}\n\n"
        
        # Group by category
        for category in self.sfx_categories.keys():
            category_effects = [sfx for sfx in effects if sfx.get('category') == category]
            report += f"\n{category.upper()} ({len(category_effects)} effects):\n"
            for sfx in category_effects:
                report += f"  - {sfx['name']} ({sfx['duration']}s, volume: {sfx['volume']})\n"
        
        # Add sources
        report += "\n\nFree Sound Effects Sources:\n"
        for source in self.sfx_manifest.get('free_sfx_sources', []):
            report += f"  - {source['name']}: {source['url']}\n"
        
        return report


def main():
    """Test sound effects manager"""
    sfx_manager = SoundEffectsManager()
    
    print("\n=== Testing Sound Effects Manager ===")
    
    # Test transition effects
    whoosh = sfx_manager.get_transition_effect("whoosh")
    if whoosh:
        print(f"\nTransition Effect: {whoosh['name']}")
        print(f"File: {whoosh['file_path']}")
    
    # Test ambient effects
    test_regions = ["Maldives Beach", "New York City", "Amazon Rainforest"]
    for region in test_regions:
        ambient = sfx_manager.get_ambient_effect(region)
        if ambient:
            print(f"\nRegion: {region}")
            print(f"Ambient Effect: {ambient['name']}")
    
    # Generate report
    print(sfx_manager.generate_sfx_report())


if __name__ == "__main__":
    main()


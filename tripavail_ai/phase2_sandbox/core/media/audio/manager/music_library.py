#!/usr/bin/env python3
"""
Music Library Manager for TripAvail AI
Manages royalty-free background music for videos
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
import random


class MusicLibrary:
    """Manages background music selection and library"""
    
    def __init__(self):
        self.music_dir = Path("data/audio/music")
        self.music_manifest_file = self.music_dir / "music_manifest.json"
        
        # Create directories if they don't exist
        self.music_dir.mkdir(parents=True, exist_ok=True)
        
        # Music categories and moods
        self.music_categories = {
            "upbeat": ["energetic", "positive", "exciting"],
            "calm": ["relaxing", "peaceful", "ambient"],
            "cinematic": ["epic", "dramatic", "inspiring"],
            "tropical": ["beach", "island", "vacation"],
            "adventure": ["exploration", "journey", "discovery"],
            "cultural": ["traditional", "ethnic", "world"]
        }
        
        # Initialize or load manifest
        self.music_manifest = self.load_manifest()
        
        logger.info("Music Library initialized")
    
    def load_manifest(self) -> Dict:
        """Load music manifest from file"""
        if self.music_manifest_file.exists():
            try:
                with open(self.music_manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load music manifest: {e}")
        
        # Create default manifest
        return self.create_default_manifest()
    
    def create_default_manifest(self) -> Dict:
        """Create default music manifest with sample entries"""
        manifest = {
            "version": "1.0",
            "music_tracks": [
                {
                    "id": "upbeat_travel_1",
                    "name": "Sunny Journey",
                    "category": "upbeat",
                    "mood": "energetic",
                    "duration": 180,
                    "file_path": "data/audio/music/upbeat_travel_1.mp3",
                    "bpm": 128,
                    "license": "Royalty-Free",
                    "source": "Free Music Archive",
                    "suitable_for": ["beach", "tropical", "adventure"]
                },
                {
                    "id": "calm_ambient_1",
                    "name": "Peaceful Waters",
                    "category": "calm",
                    "mood": "relaxing",
                    "duration": 200,
                    "file_path": "data/audio/music/calm_ambient_1.mp3",
                    "bpm": 85,
                    "license": "Royalty-Free",
                    "source": "Free Music Archive",
                    "suitable_for": ["spa", "wellness", "nature"]
                },
                {
                    "id": "cinematic_epic_1",
                    "name": "Epic Discovery",
                    "category": "cinematic",
                    "mood": "inspiring",
                    "duration": 150,
                    "file_path": "data/audio/music/cinematic_epic_1.mp3",
                    "bpm": 110,
                    "license": "Royalty-Free",
                    "source": "Free Music Archive",
                    "suitable_for": ["adventure", "mountains", "exploration"]
                },
                {
                    "id": "tropical_beach_1",
                    "name": "Island Dreams",
                    "category": "tropical",
                    "mood": "beach",
                    "duration": 165,
                    "file_path": "data/audio/music/tropical_beach_1.mp3",
                    "bpm": 95,
                    "license": "Royalty-Free",
                    "source": "Free Music Archive",
                    "suitable_for": ["beach", "island", "tropical"]
                },
                {
                    "id": "adventure_journey_1",
                    "name": "Road Trip Vibes",
                    "category": "adventure",
                    "mood": "discovery",
                    "duration": 175,
                    "file_path": "data/audio/music/adventure_journey_1.mp3",
                    "bpm": 120,
                    "license": "Royalty-Free",
                    "source": "Free Music Archive",
                    "suitable_for": ["road trip", "adventure", "exploration"]
                },
                {
                    "id": "cultural_world_1",
                    "name": "World Traveler",
                    "category": "cultural",
                    "mood": "traditional",
                    "duration": 190,
                    "file_path": "data/audio/music/cultural_world_1.mp3",
                    "bpm": 100,
                    "license": "Royalty-Free",
                    "source": "Free Music Archive",
                    "suitable_for": ["cultural", "heritage", "traditional"]
                }
            ],
            "free_music_sources": [
                {
                    "name": "Free Music Archive",
                    "url": "https://freemusicarchive.org/",
                    "license": "Creative Commons"
                },
                {
                    "name": "YouTube Audio Library",
                    "url": "https://www.youtube.com/audiolibrary",
                    "license": "Royalty-Free"
                },
                {
                    "name": "Pixabay Music",
                    "url": "https://pixabay.com/music/",
                    "license": "Pixabay License"
                },
                {
                    "name": "Incompetech",
                    "url": "https://incompetech.com/music/",
                    "license": "Creative Commons Attribution"
                },
                {
                    "name": "Bensound",
                    "url": "https://www.bensound.com/",
                    "license": "Creative Commons / Attribution Required"
                }
            ]
        }
        
        # Save manifest
        self.save_manifest(manifest)
        return manifest
    
    def save_manifest(self, manifest: Dict):
        """Save music manifest to file"""
        try:
            with open(self.music_manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved music manifest to {self.music_manifest_file}")
        except Exception as e:
            logger.error(f"Failed to save music manifest: {e}")
    
    def get_music_by_category(self, category: str) -> List[Dict]:
        """Get all music tracks by category"""
        tracks = self.music_manifest.get('music_tracks', [])
        return [track for track in tracks if track.get('category') == category]
    
    def get_music_by_mood(self, mood: str) -> List[Dict]:
        """Get all music tracks by mood"""
        tracks = self.music_manifest.get('music_tracks', [])
        return [track for track in tracks if track.get('mood') == mood]
    
    def get_music_for_region(self, region: str) -> Optional[Dict]:
        """Select appropriate music based on region"""
        region_lower = region.lower()
        
        # Region-based music selection
        if any(keyword in region_lower for keyword in ['beach', 'island', 'caribbean', 'maldives', 'hawaii', 'bali']):
            tracks = self.get_music_by_category('tropical')
        elif any(keyword in region_lower for keyword in ['mountain', 'alps', 'himalaya', 'adventure', 'trek']):
            tracks = self.get_music_by_category('adventure')
        elif any(keyword in region_lower for keyword in ['spa', 'wellness', 'retreat', 'yoga']):
            tracks = self.get_music_by_category('calm')
        elif any(keyword in region_lower for keyword in ['cultural', 'heritage', 'temple', 'traditional']):
            tracks = self.get_music_by_category('cultural')
        elif any(keyword in region_lower for keyword in ['city', 'urban', 'modern', 'dynamic']):
            tracks = self.get_music_by_category('upbeat')
        else:
            # Default to cinematic for general travel content
            tracks = self.get_music_by_category('cinematic')
        
        # Select random track from category
        if tracks:
            selected = random.choice(tracks)
            logger.info(f"Selected music '{selected['name']}' for region '{region}'")
            return selected
        
        # Fallback to any track
        all_tracks = self.music_manifest.get('music_tracks', [])
        if all_tracks:
            return random.choice(all_tracks)
        
        return None
    
    def get_music_for_content(self, caption: str, region: str, score: int = 7) -> Optional[Dict]:
        """Select music based on content analysis"""
        caption_lower = caption.lower()
        
        # Keyword-based selection
        if any(keyword in caption_lower for keyword in ['exciting', 'adventure', 'thrilling', 'explore']):
            tracks = self.get_music_by_category('adventure')
        elif any(keyword in caption_lower for keyword in ['peaceful', 'relaxing', 'calm', 'serene', 'tranquil']):
            tracks = self.get_music_by_category('calm')
        elif any(keyword in caption_lower for keyword in ['beach', 'tropical', 'island', 'paradise']):
            tracks = self.get_music_by_category('tropical')
        elif any(keyword in caption_lower for keyword in ['culture', 'heritage', 'traditional', 'historic']):
            tracks = self.get_music_by_category('cultural')
        elif any(keyword in caption_lower for keyword in ['epic', 'amazing', 'stunning', 'incredible']):
            tracks = self.get_music_by_category('cinematic')
        else:
            # Use region-based selection as fallback
            return self.get_music_for_region(region)
        
        if tracks:
            return random.choice(tracks)
        
        return self.get_music_for_region(region)
    
    def add_music_track(self, track_info: Dict) -> bool:
        """Add a new music track to the library"""
        try:
            tracks = self.music_manifest.get('music_tracks', [])
            
            # Check if track already exists
            if any(t['id'] == track_info['id'] for t in tracks):
                logger.warning(f"Track {track_info['id']} already exists")
                return False
            
            tracks.append(track_info)
            self.music_manifest['music_tracks'] = tracks
            self.save_manifest(self.music_manifest)
            
            logger.info(f"Added music track: {track_info['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add music track: {e}")
            return False
    
    def list_all_tracks(self) -> List[Dict]:
        """List all available music tracks"""
        return self.music_manifest.get('music_tracks', [])
    
    def get_free_music_sources(self) -> List[Dict]:
        """Get list of free music sources"""
        return self.music_manifest.get('free_music_sources', [])
    
    def generate_music_report(self) -> str:
        """Generate a report of available music"""
        tracks = self.list_all_tracks()
        report = "\n=== TripAvail AI Music Library Report ===\n\n"
        report += f"Total Tracks: {len(tracks)}\n\n"
        
        # Group by category
        for category in self.music_categories.keys():
            category_tracks = self.get_music_by_category(category)
            report += f"\n{category.upper()} ({len(category_tracks)} tracks):\n"
            for track in category_tracks:
                report += f"  - {track['name']} ({track['duration']}s, {track['bpm']} BPM)\n"
        
        # Add sources
        report += "\n\nFree Music Sources:\n"
        for source in self.get_free_music_sources():
            report += f"  - {source['name']}: {source['url']}\n"
        
        return report


def main():
    """Test the music library"""
    library = MusicLibrary()
    
    # Test music selection
    print("\n=== Testing Music Selection ===")
    
    test_regions = [
        "Maldives Beach Resort",
        "Swiss Alps Adventure",
        "Tokyo Cultural Heritage",
        "New York City Tour",
        "Bali Wellness Retreat"
    ]
    
    for region in test_regions:
        music = library.get_music_for_region(region)
        if music:
            print(f"\nRegion: {region}")
            print(f"Selected: {music['name']} ({music['category']})")
    
    # Generate report
    print(library.generate_music_report())


if __name__ == "__main__":
    main()


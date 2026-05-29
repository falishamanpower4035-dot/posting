#!/usr/bin/env python3
"""
Test Script for Long Video System Updates
Tests: existing music files, Pixabay credit, SEO-optimized tags
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Import components (only what we need for testing updates)
from core.media.audio.audio_mixer_long import AudioMixerLong
from core.social.platforms.youtube_uploader_long import YouTubeUploaderLong
from config import settings_long


class LongVideoUpdatesTester:
    """
    Test script for long video system updates
    Tests: existing music files, Pixabay credit, SEO-optimized tags
    """
    
    def __init__(self):
        # Initialize components
        self.audio_mixer = AudioMixerLong()
        self.youtube_uploader = YouTubeUploaderLong()
        
        logger.info("Long Video Updates Tester initialized")
    
    def test_audio_mixer_music_files(self) -> bool:
        """Test audio mixer with existing music files"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 1: AUDIO MIXER (Existing Music Files)")
            logger.info("=" * 60)
            
            # Test music file detection
            logger.info("Testing music file detection...")
            music_files = []
            for music_dir in self.audio_mixer.music_dirs:
                if music_dir.exists():
                    files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
                    if files:
                        logger.info(f"  ✅ Found {len(files)} music files in {music_dir}")
                        music_files.extend(files)
                    else:
                        logger.info(f"  ⚠️ No music files in {music_dir}")
                else:
                    logger.info(f"  ⚠️ Directory does not exist: {music_dir}")
            
            if not music_files:
                logger.warning("⚠️ No music files found in any directory")
                logger.warning("  Music directories checked:")
                for music_dir in self.audio_mixer.music_dirs:
                    logger.warning(f"    - {music_dir}")
                logger.warning("  Please add music files to one of these directories")
                return False
            
            logger.info(f"✅ Found {len(music_files)} total music files")
            
            # Test music file selection
            test_duration = 60.0  # 60 seconds
            logger.info(f"Testing music file selection (duration: {test_duration}s)...")
            
            music_file = self.audio_mixer.get_background_music(test_duration)
            
            if not music_file:
                logger.error("❌ Failed to get background music")
                return False
            
            logger.info(f"✅ Selected music file: {music_file}")
            
            # Test audio duration
            duration = self.audio_mixer._get_audio_duration(music_file)
            logger.info(f"✅ Music file duration: {duration:.2f} seconds")
            
            if duration < test_duration:
                logger.info(f"  ℹ️ Music file will be looped to match {test_duration}s duration")
            
            logger.info("=" * 60)
            logger.info("✅ Audio mixer test passed")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Audio mixer test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_youtube_uploader_pixabay_credit(self) -> bool:
        """Test YouTube uploader with Pixabay credit"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 2: YOUTUBE UPLOADER (Pixabay Credit)")
            logger.info("=" * 60)
            
            # Create sample itinerary data
            sample_itinerary = {
                "destination": "Bali, Indonesia",
                "ideal_days": 8,
                "itinerary": [
                    {
                        "day_number": 1,
                        "title": "Uluwatu & Jimbaran – The Coastal Beginning",
                        "scenes": [
                            {"order": 1, "category": "arrival", "image_search_keywords": ["airport", "arrival"]},
                            {"order": 2, "category": "attraction", "image_search_keywords": ["temple", "cliff"]},
                            {"order": 3, "category": "food", "image_search_keywords": ["seafood", "dinner"]},
                            {"order": 4, "category": "stay", "image_search_keywords": ["hotel", "resort"]},
                        ]
                    },
                    {
                        "day_number": 2,
                        "title": "Ubud – Rice Terraces & Temples",
                        "scenes": [
                            {"order": 1, "category": "attraction", "image_search_keywords": ["rice terraces", "temple"]},
                            {"order": 2, "category": "food", "image_search_keywords": ["food", "market"]},
                            {"order": 3, "category": "stay", "image_search_keywords": ["hotel", "villa"]},
                        ]
                    }
                ]
            }
            
            # Test description generation
            logger.info("Testing description generation...")
            description = self.youtube_uploader.generate_description(
                "Bali, Indonesia",
                sample_itinerary
            )
            
            logger.info(f"✅ Generated description ({len(description)} chars)")
            
            # Verify Pixabay credit
            if "Pixabay" in description:
                logger.info("✅ Pixabay credit found in description")
            else:
                logger.error("❌ Pixabay credit not found in description")
                return False
            
            # Print description preview
            logger.info("\n" + "=" * 60)
            logger.info("DESCRIPTION PREVIEW:")
            logger.info("=" * 60)
            logger.info(description[:1000] + "..." if len(description) > 1000 else description)
            logger.info("=" * 60)
            
            logger.info("=" * 60)
            logger.info("✅ YouTube uploader (Pixabay credit) test passed")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube uploader test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_youtube_uploader_seo_tags(self) -> bool:
        """Test YouTube uploader with SEO-optimized tags"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 3: YOUTUBE UPLOADER (SEO-Optimized Tags)")
            logger.info("=" * 60)
            
            # Create sample itinerary data
            sample_itinerary = {
                "destination": "Bali, Indonesia",
                "ideal_days": 8,
                "itinerary": [
                    {
                        "day_number": 1,
                        "title": "Uluwatu & Jimbaran – The Coastal Beginning",
                        "scenes": [
                            {"order": 1, "category": "arrival", "image_search_keywords": ["airport", "arrival"]},
                            {"order": 2, "category": "attraction", "image_search_keywords": ["temple", "cliff"]},
                            {"order": 3, "category": "food", "image_search_keywords": ["seafood", "dinner"]},
                            {"order": 4, "category": "stay", "image_search_keywords": ["hotel", "resort"]},
                            {"order": 5, "category": "scenic", "image_search_keywords": ["beach", "sunset"]},
                        ]
                    },
                    {
                        "day_number": 2,
                        "title": "Ubud – Rice Terraces & Temples",
                        "scenes": [
                            {"order": 1, "category": "attraction", "image_search_keywords": ["rice terraces", "temple"]},
                            {"order": 2, "category": "food", "image_search_keywords": ["food", "market"]},
                            {"order": 3, "category": "local_life", "image_search_keywords": ["culture", "local"]},
                        ]
                    }
                ]
            }
            
            # Test tags generation
            logger.info("Testing SEO-optimized tags generation...")
            tags = self.youtube_uploader.generate_tags(
                "Bali, Indonesia",
                sample_itinerary
            )
            
            logger.info(f"✅ Generated {len(tags)} SEO-optimized tags")
            
            # Calculate total tag characters
            total_chars = sum(len(tag) + 1 for tag in tags) - 1  # -1 for last comma
            logger.info(f"✅ Total tag characters: {total_chars} (max 500)")
            
            if total_chars > 500:
                logger.error(f"❌ Total tag characters ({total_chars}) exceeds YouTube limit (500)")
                return False
            
            # Verify tag categories
            logger.info("\n" + "=" * 60)
            logger.info("TAGS BREAKDOWN:")
            logger.info("=" * 60)
            
            # Primary tags
            primary_tags = [tag for tag in tags if tag.lower() in ["bali", "bali, indonesia", "bali travel", "bali itinerary"]]
            logger.info(f"Primary Tags ({len(primary_tags)}): {', '.join(primary_tags[:5])}")
            
            # Day count tags
            day_tags = [tag for tag in tags if "8 day" in tag.lower() or "8 days" in tag.lower()]
            logger.info(f"Day Count Tags ({len(day_tags)}): {', '.join(day_tags)}")
            
            # Year tags
            current_year = datetime.now().year
            year_tags = [tag for tag in tags if str(current_year) in tag]
            logger.info(f"Year Tags ({len(year_tags)}): {', '.join(year_tags)}")
            
            # Category tags
            category_tags = [tag for tag in tags if any(cat in tag.lower() for cat in ["attraction", "food", "scenic", "hotel", "culture"])]
            logger.info(f"Category Tags ({len(category_tags)}): {', '.join(category_tags[:5])}")
            
            # Long-tail keywords
            longtail_tags = [tag for tag in tags if any(phrase in tag.lower() for phrase in ["how to", "travel tips", "travel guide", "best places", "must see"])]
            logger.info(f"Long-tail Keywords ({len(longtail_tags)}): {', '.join(longtail_tags[:5])}")
            
            # Print all tags
            logger.info("\n" + "=" * 60)
            logger.info("ALL TAGS:")
            logger.info("=" * 60)
            logger.info(", ".join(tags))
            logger.info("=" * 60)
            
            logger.info("=" * 60)
            logger.info("✅ YouTube uploader (SEO tags) test passed")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube uploader test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_youtube_uploader_title(self) -> bool:
        """Test YouTube uploader title generation"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 4: YOUTUBE UPLOADER (Title Generation)")
            logger.info("=" * 60)
            
            # Create sample itinerary data
            sample_itinerary = {
                "destination": "Bali, Indonesia",
                "ideal_days": 8,
                "itinerary": []
            }
            
            # Test title generation
            logger.info("Testing title generation...")
            title = self.youtube_uploader.generate_title(
                "Bali, Indonesia",
                8,
                sample_itinerary
            )
            
            logger.info(f"✅ Generated title: {title}")
            
            # Verify title format
            expected_format = "[Destination] [X]-Day Itinerary [emoji] | Complete Travel Guide for [Year]"
            logger.info(f"Expected format: {expected_format}")
            
            # Check title components
            if "Bali" in title:
                logger.info("✅ Destination name found in title")
            else:
                logger.error("❌ Destination name not found in title")
                return False
            
            if "8-Day" in title or "8 Day" in title:
                logger.info("✅ Day count found in title")
            else:
                logger.error("❌ Day count not found in title")
                return False
            
            if "Itinerary" in title:
                logger.info("✅ 'Itinerary' found in title")
            else:
                logger.error("❌ 'Itinerary' not found in title")
                return False
            
            if "Complete Travel Guide" in title:
                logger.info("✅ 'Complete Travel Guide' found in title")
            else:
                logger.error("❌ 'Complete Travel Guide' not found in title")
                return False
            
            current_year = datetime.now().year
            if str(current_year) in title:
                logger.info(f"✅ Year ({current_year}) found in title")
            else:
                logger.error(f"❌ Year ({current_year}) not found in title")
                return False
            
            logger.info("=" * 60)
            logger.info("✅ YouTube uploader (Title) test passed")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube uploader test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests"""
        try:
            logger.info("=" * 60)
            logger.info("LONG VIDEO SYSTEM UPDATES TEST SUITE")
            logger.info("=" * 60)
            logger.info("Testing: existing music files, Pixabay credit, SEO-optimized tags")
            logger.info("=" * 60)
            
            results = {
                "audio_mixer_music_files": False,
                "youtube_uploader_pixabay_credit": False,
                "youtube_uploader_seo_tags": False,
                "youtube_uploader_title": False,
            }
            
            # Run tests
            results["audio_mixer_music_files"] = self.test_audio_mixer_music_files()
            results["youtube_uploader_pixabay_credit"] = self.test_youtube_uploader_pixabay_credit()
            results["youtube_uploader_seo_tags"] = self.test_youtube_uploader_seo_tags()
            results["youtube_uploader_title"] = self.test_youtube_uploader_title()
            
            # Print summary
            logger.info("=" * 60)
            logger.info("TEST RESULTS SUMMARY")
            logger.info("=" * 60)
            
            for test_name, result in results.items():
                status = "✅ PASSED" if result else "❌ FAILED"
                logger.info(f"{test_name}: {status}")
            
            # Calculate pass rate
            passed = sum(1 for r in results.values() if r)
            total = len(results)
            pass_rate = (passed / total) * 100
            
            logger.info("=" * 60)
            logger.info(f"Pass Rate: {passed}/{total} ({pass_rate:.1f}%)")
            logger.info("=" * 60)
            
            if pass_rate == 100:
                logger.info("✅ ALL TESTS PASSED!")
            elif pass_rate >= 75:
                logger.warning("⚠️ Most tests passed, but some failed")
            else:
                logger.error("❌ Many tests failed, please check errors above")
            
            return results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}


def main():
    """Main function"""
    try:
        logger.info("=" * 60)
        logger.info("LONG VIDEO SYSTEM UPDATES TEST SCRIPT")
        logger.info("=" * 60)
        logger.info("Testing: existing music files, Pixabay credit, SEO-optimized tags")
        logger.info("=" * 60)
        
        # Initialize tester
        tester = LongVideoUpdatesTester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Print final summary
        logger.info("=" * 60)
        logger.info("TEST COMPLETE")
        logger.info("=" * 60)
        
        # Exit with appropriate code
        if all(results.values()):
            logger.info("✅ All tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


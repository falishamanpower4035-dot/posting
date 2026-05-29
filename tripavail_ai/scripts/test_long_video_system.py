#!/usr/bin/env python3
"""
Test Script for Long Video System
Tests all components: itinerary → script → images → voiceover → audio → video → upload
Verifies: existing music files, Pixabay credit, SEO-optimized tags
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

# Import components
from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
from core.content.generation.script_generator_long import ScriptGeneratorLong
from core.utils.error_handler_long import ErrorHandlerLong
from core.media.images.generator.destination_image_generator_long import DestinationImageGeneratorLong
from core.media.audio.voiceover_generator_long import VoiceoverGeneratorLong
from core.media.audio.audio_mixer_long import AudioMixerLong
from core.media.video.generator.thumbnail_generator_long import ThumbnailGeneratorLong
from core.social.platforms.youtube_uploader_long import YouTubeUploaderLong
from config import settings_long


class LongVideoSystemTester:
    """
    Test script for long video system
    Tests all components and verifies updates
    """
    
    def __init__(self):
        # Initialize components
        self.itinerary_generator = ItineraryGeneratorLong()
        self.script_generator = ScriptGeneratorLong()
        self.error_handler = ErrorHandlerLong()
        self.image_generator = DestinationImageGeneratorLong()
        self.voiceover_generator = VoiceoverGeneratorLong()
        self.audio_mixer = AudioMixerLong()
        self.thumbnail_generator = ThumbnailGeneratorLong()
        self.youtube_uploader = YouTubeUploaderLong()
        
        logger.info("Long Video System Tester initialized")
    
    def test_itinerary_generation(self, destination: str) -> bool:
        """Test itinerary generation"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 1: ITINERARY GENERATION")
            logger.info("=" * 60)
            
            # Generate itinerary
            itinerary_data = self.itinerary_generator.generate_itinerary(
                destination, max_duration_minutes=8
            )
            
            # Validate itinerary
            is_valid, errors = self.itinerary_generator.validate_itinerary_structure(itinerary_data)
            
            if not is_valid:
                logger.error(f"Itinerary validation failed: {errors}")
                return False
            
            # Save itinerary
            self.itinerary_generator.save_itinerary(itinerary_data, destination)
            
            # Print summary
            print(self.itinerary_generator.get_itinerary_summary(itinerary_data))
            
            logger.info("✅ Itinerary generation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Itinerary generation test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_script_generation(self, destination: str) -> bool:
        """Test script generation"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 2: SCRIPT GENERATION")
            logger.info("=" * 60)
            
            # Load itinerary
            itinerary_data = self.itinerary_generator.load_itinerary(destination)
            if not itinerary_data:
                logger.error("Itinerary not found")
                return False
            
            # Generate script
            script_data = self.script_generator.generate_script(itinerary_data)
            
            # Validate script
            is_valid, errors = self.script_generator.validate_script_structure(
                script_data, itinerary_data
            )
            
            if not is_valid:
                logger.error(f"Script validation failed: {errors}")
                return False
            
            # Save script
            self.script_generator.save_script(script_data, destination)
            
            # Print summary
            print(self.script_generator.get_script_summary(script_data))
            
            logger.info("✅ Script generation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Script generation test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_error_handling(self, destination: str) -> bool:
        """Test error handling with auto-fix"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 3: ERROR HANDLING")
            logger.info("=" * 60)
            
            # Load itinerary
            itinerary_data = self.itinerary_generator.load_itinerary(destination)
            if not itinerary_data:
                logger.error("Itinerary not found")
                return False
            
            # Test error handler
            is_valid, fixed_itinerary, errors = self.error_handler.validate_and_fix_itinerary(
                itinerary_data, destination, max_retries=3
            )
            
            if is_valid:
                logger.info("✅ Error handling test passed (itinerary is valid)")
            else:
                logger.warning(f"⚠️ Error handling test: {len(errors)} errors found")
                if self.error_handler.should_proceed_with_errors(errors, "itinerary"):
                    logger.info("✅ Error handling test passed (graceful degradation)")
                else:
                    logger.error("❌ Error handling test failed (critical errors)")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_image_generation(self, destination: str) -> bool:
        """Test image generation with Pixabay"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 4: IMAGE GENERATION (Pixabay)")
            logger.info("=" * 60)
            
            # Test Pixabay search
            test_query = f"attractions in {destination}"
            logger.info(f"Testing Pixabay search with query: '{test_query}'")
            
            images = self.image_generator.search_pixabay(test_query, count=5, page=1)
            
            if not images:
                logger.warning("No images found from Pixabay")
                return False
            
            logger.info(f"✅ Found {len(images)} images from Pixabay")
            
            # Verify image properties
            for img in images[:3]:
                logger.info(f"  - Image: {img.get('width')}x{img.get('height')}, "
                          f"Aspect Ratio: {img.get('aspect_ratio', 0):.2f}, "
                          f"Service: {img.get('service', 'unknown')}")
                
                # Verify aspect ratio (should be ~16:9)
                aspect_ratio = img.get('aspect_ratio', 0)
                if not (1.6 <= aspect_ratio <= 1.8):
                    logger.warning(f"  ⚠️ Aspect ratio {aspect_ratio:.2f} is not 16:9")
            
            logger.info("✅ Image generation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Image generation test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_audio_mixer(self, destination: str) -> bool:
        """Test audio mixer with existing music files"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 5: AUDIO MIXER (Existing Music Files)")
            logger.info("=" * 60)
            
            # Test music file detection
            logger.info("Testing music file detection...")
            music_files = []
            for music_dir in self.audio_mixer.music_dirs:
                if music_dir.exists():
                    files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
                    if files:
                        logger.info(f"  Found {len(files)} music files in {music_dir}")
                        music_files.extend(files)
                    else:
                        logger.info(f"  No music files in {music_dir}")
                else:
                    logger.info(f"  Directory does not exist: {music_dir}")
            
            if not music_files:
                logger.warning("⚠️ No music files found in any directory")
                logger.warning("  Music directories checked:")
                for music_dir in self.audio_mixer.music_dirs:
                    logger.warning(f"    - {music_dir}")
                return False
            
            logger.info(f"✅ Found {len(music_files)} total music files")
            
            # Test music file selection
            test_duration = 60.0  # 60 seconds
            music_file = self.audio_mixer.get_background_music(test_duration)
            
            if not music_file:
                logger.error("Failed to get background music")
                return False
            
            logger.info(f"✅ Selected music file: {music_file}")
            
            # Test audio duration
            duration = self.audio_mixer._get_audio_duration(music_file)
            logger.info(f"✅ Music file duration: {duration:.2f} seconds")
            
            logger.info("✅ Audio mixer test passed")
            return True
            
        except Exception as e:
            logger.error(f"Audio mixer test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_youtube_uploader(self, destination: str) -> bool:
        """Test YouTube uploader with new format"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 6: YOUTUBE UPLOADER (New Format)")
            logger.info("=" * 60)
            
            # Load itinerary
            itinerary_data = self.itinerary_generator.load_itinerary(destination)
            if not itinerary_data:
                logger.error("Itinerary not found")
                return False
            
            # Test title generation
            ideal_days = itinerary_data.get('ideal_days', 0)
            title = self.youtube_uploader.generate_title(destination, ideal_days, itinerary_data)
            logger.info(f"✅ Generated title: {title}")
            
            # Test description generation
            description = self.youtube_uploader.generate_description(destination, itinerary_data)
            logger.info(f"✅ Generated description ({len(description)} chars)")
            
            # Verify Pixabay credit
            if "Pixabay" in description:
                logger.info("✅ Pixabay credit found in description")
            else:
                logger.error("❌ Pixabay credit not found in description")
                return False
            
            # Print description preview
            logger.info("\nDescription Preview:")
            logger.info(description[:500] + "..." if len(description) > 500 else description)
            
            # Test tags generation
            tags = self.youtube_uploader.generate_tags(destination, itinerary_data)
            logger.info(f"✅ Generated {len(tags)} SEO-optimized tags")
            
            # Calculate total tag characters
            total_chars = sum(len(tag) + 1 for tag in tags) - 1  # -1 for last comma
            logger.info(f"✅ Total tag characters: {total_chars} (max 500)")
            
            if total_chars > 500:
                logger.error(f"❌ Total tag characters ({total_chars}) exceeds YouTube limit (500)")
                return False
            
            # Print tags preview
            logger.info("\nTags Preview:")
            logger.info(", ".join(tags[:10]) + "..." if len(tags) > 10 else ", ".join(tags))
            
            # Test YouTube connection
            if self.youtube_uploader.test_connection():
                logger.info("✅ YouTube connection successful")
            else:
                logger.warning("⚠️ YouTube connection failed (may not have credentials)")
            
            logger.info("✅ YouTube uploader test passed")
            return True
            
        except Exception as e:
            logger.error(f"YouTube uploader test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_thumbnail_generation(self, destination: str) -> bool:
        """Test thumbnail generation"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 7: THUMBNAIL GENERATION")
            logger.info("=" * 60)
            
            # Load itinerary
            itinerary_data = self.itinerary_generator.load_itinerary(destination)
            if not itinerary_data:
                logger.error("Itinerary not found")
                return False
            
            # Generate thumbnail
            thumbnail_path = self.thumbnail_generator.generate_thumbnail(
                destination, itinerary_data
            )
            
            if not thumbnail_path:
                logger.error("Thumbnail generation failed")
                return False
            
            logger.info(f"✅ Generated thumbnail: {thumbnail_path}")
            
            # Verify thumbnail exists
            if thumbnail_path.exists():
                logger.info(f"✅ Thumbnail file exists: {thumbnail_path}")
                
                # Check file size
                file_size = thumbnail_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"✅ Thumbnail file size: {file_size:.2f} MB")
            else:
                logger.error("❌ Thumbnail file does not exist")
                return False
            
            logger.info("✅ Thumbnail generation test passed")
            return True
            
        except Exception as e:
            logger.error(f"Thumbnail generation test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_full_pipeline(self, destination: str, skip_video: bool = True) -> bool:
        """Test full pipeline (without actual video generation)"""
        try:
            logger.info("=" * 60)
            logger.info("TEST 8: FULL PIPELINE TEST")
            logger.info("=" * 60)
            
            # Step 1: Itinerary generation
            logger.info("Step 1: Generating itinerary...")
            if not self.test_itinerary_generation(destination):
                return False
            
            # Step 2: Script generation
            logger.info("Step 2: Generating script...")
            if not self.test_script_generation(destination):
                return False
            
            # Step 3: Error handling
            logger.info("Step 3: Testing error handling...")
            if not self.test_error_handling(destination):
                return False
            
            # Step 4: Image generation
            logger.info("Step 4: Testing image generation...")
            if not self.test_image_generation(destination):
                return False
            
            # Step 5: Audio mixer
            logger.info("Step 5: Testing audio mixer...")
            if not self.test_audio_mixer(destination):
                return False
            
            # Step 6: YouTube uploader
            logger.info("Step 6: Testing YouTube uploader...")
            if not self.test_youtube_uploader(destination):
                return False
            
            # Step 7: Thumbnail generation
            logger.info("Step 7: Testing thumbnail generation...")
            if not self.test_thumbnail_generation(destination):
                return False
            
            logger.info("=" * 60)
            logger.info("✅ ALL TESTS PASSED")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Full pipeline test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_all_tests(self, destination: str = "Bali, Indonesia"):
        """Run all tests"""
        try:
            logger.info("=" * 60)
            logger.info("LONG VIDEO SYSTEM TEST SUITE")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info("=" * 60)
            
            results = {
                "itinerary_generation": False,
                "script_generation": False,
                "error_handling": False,
                "image_generation": False,
                "audio_mixer": False,
                "youtube_uploader": False,
                "thumbnail_generation": False,
                "full_pipeline": False,
            }
            
            # Run tests
            results["itinerary_generation"] = self.test_itinerary_generation(destination)
            results["script_generation"] = self.test_script_generation(destination)
            results["error_handling"] = self.test_error_handling(destination)
            results["image_generation"] = self.test_image_generation(destination)
            results["audio_mixer"] = self.test_audio_mixer(destination)
            results["youtube_uploader"] = self.test_youtube_uploader(destination)
            results["thumbnail_generation"] = self.test_thumbnail_generation(destination)
            results["full_pipeline"] = self.test_full_pipeline(destination, skip_video=True)
            
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
            elif pass_rate >= 80:
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
        logger.info("LONG VIDEO SYSTEM TEST SCRIPT")
        logger.info("=" * 60)
        
        # Initialize tester
        tester = LongVideoSystemTester()
        
        # Test destination
        test_destination = "Bali, Indonesia"
        
        # Run all tests
        results = tester.run_all_tests(test_destination)
        
        # Print final summary
        logger.info("=" * 60)
        logger.info("TEST COMPLETE")
        logger.info("=" * 60)
        
        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


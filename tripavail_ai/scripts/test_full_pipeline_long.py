#!/usr/bin/env python3
"""
Full Pipeline Test for Long Video System
Tests complete pipeline: itinerary → script → images → voiceover → audio → video → upload
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
from core.production.production_pipeline_long import ProductionPipelineLong
from core.social.platforms.youtube_uploader_long import YouTubeUploaderLong
from config import settings_long


class FullPipelineTester:
    """
    Full pipeline tester for long video system
    Tests complete pipeline with actual video generation
    """
    
    def __init__(self):
        # Initialize components
        self.production_pipeline = ProductionPipelineLong()
        self.youtube_uploader = YouTubeUploaderLong()
        
        logger.info("Full Pipeline Tester initialized")
    
    def test_full_pipeline(self, destination: str, upload_to_youtube: bool = False, privacy_status: str = "private") -> Dict[str, Any]:
        """
        Test full pipeline with actual video generation
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            upload_to_youtube: Whether to upload to YouTube (default: False for testing)
            privacy_status: YouTube privacy status (default: "private" for testing)
            
        Returns:
            Dictionary with generation results
        """
        try:
            logger.info("=" * 60)
            logger.info("FULL PIPELINE TEST")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Upload to YouTube: {upload_to_youtube}")
            logger.info(f"Privacy Status: {privacy_status}")
            logger.info("=" * 60)
            
            # Generate video
            result = self.production_pipeline.generate_video_for_destination(
                destination=destination,
                max_duration_minutes=8,
                upload_to_youtube=upload_to_youtube,
                privacy_status=privacy_status
            )
            
            # Print results
            logger.info("=" * 60)
            logger.info("GENERATION RESULTS")
            logger.info("=" * 60)
            logger.info(f"Status: {result.get('status', 'unknown')}")
            logger.info(f"Video Path: {result.get('video_path', 'N/A')}")
            logger.info(f"Thumbnail Path: {result.get('thumbnail_path', 'N/A')}")
            
            if result.get('youtube_video_id'):
                logger.info(f"YouTube Video ID: {result['youtube_video_id']}")
                logger.info(f"YouTube URL: {result.get('youtube_url', 'N/A')}")
            
            if result.get('errors'):
                logger.error(f"Errors: {result['errors']}")
            
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"Full pipeline test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.now().isoformat()
            }
    
    def test_youtube_upload(self, video_path: Path, destination: str, itinerary_data: Dict[str, Any], thumbnail_path: Optional[Path] = None, privacy_status: str = "private") -> Dict[str, Any]:
        """
        Test YouTube upload with generated video
        
        Args:
            video_path: Path to generated video
            destination: Destination name
            itinerary_data: Itinerary data
            thumbnail_path: Path to thumbnail (optional)
            privacy_status: YouTube privacy status (default: "private" for testing)
            
        Returns:
            Dictionary with upload results
        """
        try:
            logger.info("=" * 60)
            logger.info("YOUTUBE UPLOAD TEST")
            logger.info("=" * 60)
            logger.info(f"Video Path: {video_path}")
            logger.info(f"Destination: {destination}")
            logger.info(f"Privacy Status: {privacy_status}")
            logger.info("=" * 60)
            
            # Check if video exists
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return {
                    "status": "failed",
                    "errors": [f"Video file not found: {video_path}"],
                    "completed_at": datetime.now().isoformat()
                }
            
            # Get video file size
            file_size = video_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Video file size: {file_size:.2f} MB")
            
            # Test YouTube connection
            logger.info("Testing YouTube connection...")
            if not self.youtube_uploader.test_connection():
                logger.error("YouTube connection failed")
                return {
                    "status": "failed",
                    "errors": ["YouTube connection failed"],
                    "completed_at": datetime.now().isoformat()
                }
            
            logger.info("✅ YouTube connection successful")
            
            # Generate title, description, and tags
            ideal_days = itinerary_data.get('ideal_days', 0)
            title = self.youtube_uploader.generate_title(destination, ideal_days, itinerary_data)
            description = self.youtube_uploader.generate_description(destination, itinerary_data)
            tags = self.youtube_uploader.generate_tags(destination, itinerary_data)
            
            logger.info(f"Title: {title}")
            logger.info(f"Description: {len(description)} chars")
            logger.info(f"Tags: {len(tags)} tags")
            
            # Verify Pixabay credit
            if "Pixabay" in description:
                logger.info("✅ Pixabay credit found in description")
            else:
                logger.error("❌ Pixabay credit not found in description")
            
            # Upload video
            logger.info("Uploading video to YouTube...")
            youtube_video_id = self.youtube_uploader.upload_video(
                video_path=video_path,
                destination=destination,
                itinerary_data=itinerary_data,
                thumbnail_path=thumbnail_path,
                privacy_status=privacy_status
            )
            
            if youtube_video_id:
                youtube_url = f"https://www.youtube.com/watch?v={youtube_video_id}"
                logger.info(f"✅ Video uploaded successfully!")
                logger.info(f"YouTube Video ID: {youtube_video_id}")
                logger.info(f"YouTube URL: {youtube_url}")
                
                return {
                    "status": "success",
                    "youtube_video_id": youtube_video_id,
                    "youtube_url": youtube_url,
                    "completed_at": datetime.now().isoformat()
                }
            else:
                logger.error("Video upload failed")
                return {
                    "status": "failed",
                    "errors": ["Video upload failed"],
                    "completed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"YouTube upload test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.now().isoformat()
            }
    
    def test_pipeline_with_upload(self, destination: str, privacy_status: str = "private") -> Dict[str, Any]:
        """
        Test full pipeline with YouTube upload
        
        Args:
            destination: Destination name
            privacy_status: YouTube privacy status (default: "private" for testing)
            
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("=" * 60)
            logger.info("FULL PIPELINE TEST WITH YOUTUBE UPLOAD")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Privacy Status: {privacy_status}")
            logger.info("=" * 60)
            
            # Step 1: Generate video
            logger.info("Step 1: Generating video...")
            result = self.test_full_pipeline(
                destination=destination,
                upload_to_youtube=True,
                privacy_status=privacy_status
            )
            
            # Check if video was generated
            if result.get('status') != 'completed':
                logger.error("Video generation failed")
                return result
            
            # Step 2: Verify video exists
            video_path = Path(result.get('video_path', ''))
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return {
                    "status": "failed",
                    "errors": [f"Video file not found: {video_path}"],
                    "completed_at": datetime.now().isoformat()
                }
            
            logger.info(f"✅ Video generated: {video_path}")
            
            # Step 3: Verify thumbnail exists
            thumbnail_path = None
            if result.get('thumbnail_path'):
                thumbnail_path = Path(result['thumbnail_path'])
                if thumbnail_path.exists():
                    logger.info(f"✅ Thumbnail generated: {thumbnail_path}")
                else:
                    logger.warning(f"Thumbnail file not found: {thumbnail_path}")
            
            # Step 4: Load itinerary data for upload
            from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
            itinerary_generator = ItineraryGeneratorLong()
            itinerary_data = itinerary_generator.load_itinerary(destination)
            
            if not itinerary_data:
                logger.error("Itinerary data not found")
                return {
                    "status": "failed",
                    "errors": ["Itinerary data not found"],
                    "completed_at": datetime.now().isoformat()
                }
            
            # Step 5: Test YouTube upload
            logger.info("Step 2: Testing YouTube upload...")
            upload_result = self.test_youtube_upload(
                video_path=video_path,
                destination=destination,
                itinerary_data=itinerary_data,
                thumbnail_path=thumbnail_path,
                privacy_status=privacy_status
            )
            
            # Combine results
            combined_result = {
                **result,
                **upload_result,
                "video_path": str(video_path),
                "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
            }
            
            # Print final summary
            logger.info("=" * 60)
            logger.info("FINAL RESULTS")
            logger.info("=" * 60)
            logger.info(f"Status: {combined_result.get('status', 'unknown')}")
            logger.info(f"Video Path: {combined_result.get('video_path', 'N/A')}")
            logger.info(f"Thumbnail Path: {combined_result.get('thumbnail_path', 'N/A')}")
            
            if combined_result.get('youtube_video_id'):
                logger.info(f"YouTube Video ID: {combined_result['youtube_video_id']}")
                logger.info(f"YouTube URL: {combined_result.get('youtube_url', 'N/A')}")
            
            if combined_result.get('errors'):
                logger.error(f"Errors: {combined_result['errors']}")
            
            logger.info("=" * 60)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Full pipeline test with upload failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.now().isoformat()
            }
    
    def run_tests(self, destination: str = "Bali, Indonesia", test_upload: bool = False, privacy_status: str = "private") -> Dict[str, Any]:
        """
        Run all tests
        
        Args:
            destination: Destination name
            test_upload: Whether to test YouTube upload
            privacy_status: YouTube privacy status
            
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("=" * 60)
            logger.info("FULL PIPELINE TEST SUITE")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Test Upload: {test_upload}")
            logger.info(f"Privacy Status: {privacy_status}")
            logger.info("=" * 60)
            
            results = {
                "destination": destination,
                "test_upload": test_upload,
                "privacy_status": privacy_status,
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "status": "pending",
                "results": {}
            }
            
            # Test 1: Full pipeline (without upload)
            logger.info("Test 1: Full pipeline (without upload)...")
            pipeline_result = self.test_full_pipeline(
                destination=destination,
                upload_to_youtube=False,
                privacy_status=privacy_status
            )
            results["results"]["pipeline"] = pipeline_result
            
            # Check if pipeline succeeded
            if pipeline_result.get('status') != 'completed':
                logger.error("Pipeline test failed")
                results["status"] = "failed"
                results["completed_at"] = datetime.now().isoformat()
                return results
            
            # Test 2: YouTube upload (if requested)
            if test_upload:
                logger.info("Test 2: YouTube upload...")
                
                # Load itinerary data
                from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
                itinerary_generator = ItineraryGeneratorLong()
                itinerary_data = itinerary_generator.load_itinerary(destination)
                
                if itinerary_data:
                    video_path = Path(pipeline_result.get('video_path', ''))
                    thumbnail_path = Path(pipeline_result.get('thumbnail_path', '')) if pipeline_result.get('thumbnail_path') else None
                    
                    upload_result = self.test_youtube_upload(
                        video_path=video_path,
                        destination=destination,
                        itinerary_data=itinerary_data,
                        thumbnail_path=thumbnail_path,
                        privacy_status=privacy_status
                    )
                    results["results"]["upload"] = upload_result
                else:
                    logger.error("Itinerary data not found for upload test")
                    results["results"]["upload"] = {
                        "status": "failed",
                        "errors": ["Itinerary data not found"],
                        "completed_at": datetime.now().isoformat()
                    }
            else:
                logger.info("Skipping YouTube upload test (test_upload=False)")
                results["results"]["upload"] = {
                    "status": "skipped",
                    "reason": "test_upload=False",
                    "completed_at": datetime.now().isoformat()
                }
            
            # Update status
            if results["results"]["pipeline"].get('status') == 'completed':
                if test_upload:
                    if results["results"]["upload"].get('status') == 'success':
                        results["status"] = "completed"
                    else:
                        results["status"] = "partial"
                else:
                    results["status"] = "completed"
            else:
                results["status"] = "failed"
            
            results["completed_at"] = datetime.now().isoformat()
            
            # Print final summary
            logger.info("=" * 60)
            logger.info("TEST RESULTS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Status: {results['status']}")
            logger.info(f"Pipeline: {results['results']['pipeline'].get('status', 'unknown')}")
            logger.info(f"Upload: {results['results']['upload'].get('status', 'unknown')}")
            
            if results["results"]["pipeline"].get('video_path'):
                logger.info(f"Video Path: {results['results']['pipeline']['video_path']}")
            
            if results["results"]["upload"].get('youtube_url'):
                logger.info(f"YouTube URL: {results['results']['upload']['youtube_url']}")
            
            logger.info("=" * 60)
            
            return results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.now().isoformat()
            }


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Full Pipeline Test for Long Video System")
    parser.add_argument(
        "--destination",
        type=str,
        default="Bali, Indonesia",
        help="Destination name (default: 'Bali, Indonesia')"
    )
    parser.add_argument(
        "--test-upload",
        action="store_true",
        help="Test YouTube upload (default: False)"
    )
    parser.add_argument(
        "--privacy-status",
        type=str,
        default="private",
        choices=["private", "unlisted", "public"],
        help="YouTube privacy status (default: 'private')"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("FULL PIPELINE TEST SCRIPT")
        logger.info("=" * 60)
        logger.info(f"Destination: {args.destination}")
        logger.info(f"Test Upload: {args.test_upload}")
        logger.info(f"Privacy Status: {args.privacy_status}")
        logger.info("=" * 60)
        
        # Initialize tester
        tester = FullPipelineTester()
        
        # Run tests
        results = tester.run_tests(
            destination=args.destination,
            test_upload=args.test_upload,
            privacy_status=args.privacy_status
        )
        
        # Print final summary
        logger.info("=" * 60)
        logger.info("TEST COMPLETE")
        logger.info("=" * 60)
        
        # Exit with appropriate code
        if results.get('status') == 'completed':
            logger.info("✅ All tests passed!")
            sys.exit(0)
        elif results.get('status') == 'partial':
            logger.warning("⚠️ Pipeline completed, but upload failed")
            sys.exit(1)
        else:
            logger.error("❌ Tests failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
YouTube Upload Test for Long Video System
Tests YouTube upload with mock video file
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Import components
from core.social.platforms.youtube_uploader_long import YouTubeUploaderLong
from config import settings_long


class YouTubeUploadTester:
    """
    YouTube upload tester for long video system
    Tests YouTube upload with mock video file
    """
    
    def __init__(self):
        # Initialize components
        self.youtube_uploader = YouTubeUploaderLong()
        
        logger.info("YouTube Upload Tester initialized")
    
    def create_mock_video(self, destination: str, duration_seconds: int = 60, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Create mock video file for testing
        
        Args:
            destination: Destination name
            duration_seconds: Video duration in seconds
            output_path: Output video path (optional)
            
        Returns:
            Path to mock video file or None if failed
        """
        try:
            logger.info("=" * 60)
            logger.info("CREATING MOCK VIDEO")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Duration: {duration_seconds} seconds")
            logger.info("=" * 60)
            
            # Create output path
            if output_path is None:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                videos_dir = Path(settings_long.VIDEOS_DIR)
                videos_dir.mkdir(parents=True, exist_ok=True)
                output_path = videos_dir / f"{safe_destination}_test_video.mp4"
            
            logger.info(f"Creating mock video: {output_path}")
            
            # Create a simple test video using FFmpeg
            # This creates a video with a solid color background and text overlay
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-f', 'lavfi',
                '-i', f'color=c=blue:size=1920x1080:d={duration_seconds}',
                '-vf', f'drawtext=text=\'{destination}\':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration_seconds),
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                logger.info(f"✅ Mock video created: {output_path}")
                
                # Check file size
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"Video file size: {file_size:.2f} MB")
                
                return output_path
            else:
                logger.error(f"Failed to create mock video: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating mock video: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def create_mock_thumbnail(self, destination: str, output_path: Optional[Path] = None) -> Optional[Path]:
        """
        Create mock thumbnail file for testing
        
        Args:
            destination: Destination name
            output_path: Output thumbnail path (optional)
            
        Returns:
            Path to mock thumbnail file or None if failed
        """
        try:
            logger.info("=" * 60)
            logger.info("CREATING MOCK THUMBNAIL")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info("=" * 60)
            
            # Create output path
            if output_path is None:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                thumbnails_dir = Path(settings_long.THUMBNAILS_DIR)
                thumbnails_dir.mkdir(parents=True, exist_ok=True)
                output_path = thumbnails_dir / f"{safe_destination}_test_thumbnail.jpg"
            
            logger.info(f"Creating mock thumbnail: {output_path}")
            
            # Create a simple test thumbnail using FFmpeg
            # This creates a 1920x1080 image with a solid color background and text overlay
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output
                '-f', 'lavfi',
                '-i', 'color=c=green:size=1920x1080',
                '-vf', f'drawtext=text=\'{destination}\':fontsize=80:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2',
                '-frames:v', '1',
                '-q:v', '2',
                str(output_path)
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"✅ Mock thumbnail created: {output_path}")
                
                # Check file size
                file_size = output_path.stat().st_size / (1024)  # KB
                logger.info(f"Thumbnail file size: {file_size:.2f} KB")
                
                return output_path
            else:
                logger.error(f"Failed to create mock thumbnail: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating mock thumbnail: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def test_youtube_upload(self, destination: str, video_path: Path, thumbnail_path: Optional[Path] = None, privacy_status: str = "private") -> Dict[str, Any]:
        """
        Test YouTube upload with mock video
        
        Args:
            destination: Destination name
            video_path: Path to video file
            thumbnail_path: Path to thumbnail file (optional)
            privacy_status: YouTube privacy status (default: "private")
            
        Returns:
            Dictionary with upload results
        """
        try:
            logger.info("=" * 60)
            logger.info("YOUTUBE UPLOAD TEST")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Video Path: {video_path}")
            logger.info(f"Thumbnail Path: {thumbnail_path}")
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
                logger.error("❌ YouTube connection failed")
                return {
                    "status": "failed",
                    "errors": ["YouTube connection failed"],
                    "completed_at": datetime.now().isoformat()
                }
            
            logger.info("✅ YouTube connection successful")
            
            # Create sample itinerary data
            sample_itinerary = {
                "destination": destination,
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
            
            # Generate title, description, and tags
            ideal_days = sample_itinerary.get('ideal_days', 0)
            title = self.youtube_uploader.generate_title(destination, ideal_days, sample_itinerary)
            description = self.youtube_uploader.generate_description(destination, sample_itinerary)
            tags = self.youtube_uploader.generate_tags(destination, sample_itinerary)
            
            logger.info(f"Title: {title}")
            logger.info(f"Description: {len(description)} chars")
            logger.info(f"Tags: {len(tags)} tags ({sum(len(t) + 1 for t in tags) - 1} chars)")
            
            # Verify Pixabay credit
            if "Pixabay" in description:
                logger.info("✅ Pixabay credit found in description")
            else:
                logger.error("❌ Pixabay credit not found in description")
            
            # Print description preview
            logger.info("\n" + "=" * 60)
            logger.info("DESCRIPTION PREVIEW:")
            logger.info("=" * 60)
            logger.info(description[:500] + "..." if len(description) > 500 else description)
            logger.info("=" * 60)
            
            # Print tags preview
            logger.info("\n" + "=" * 60)
            logger.info("TAGS PREVIEW:")
            logger.info("=" * 60)
            logger.info(", ".join(tags[:10]) + "..." if len(tags) > 10 else ", ".join(tags))
            logger.info("=" * 60)
            
            # Upload video
            logger.info("\n" + "=" * 60)
            logger.info("UPLOADING VIDEO TO YOUTUBE...")
            logger.info("=" * 60)
            
            youtube_video_id = self.youtube_uploader.upload_video(
                video_path=video_path,
                destination=destination,
                itinerary_data=sample_itinerary,
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
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "completed_at": datetime.now().isoformat()
                }
            else:
                logger.error("❌ Video upload failed")
                return {
                    "status": "failed",
                    "errors": ["Video upload failed"],
                    "completed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ YouTube upload test failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "failed",
                "errors": [str(e)],
                "completed_at": datetime.now().isoformat()
            }
    
    def run_test(self, destination: str = "Bali, Indonesia", duration_seconds: int = 60, privacy_status: str = "private", create_files: bool = True) -> Dict[str, Any]:
        """
        Run complete YouTube upload test
        
        Args:
            destination: Destination name
            duration_seconds: Video duration in seconds
            privacy_status: YouTube privacy status
            create_files: Whether to create mock video and thumbnail files
            
        Returns:
            Dictionary with test results
        """
        try:
            logger.info("=" * 60)
            logger.info("YOUTUBE UPLOAD TEST SUITE")
            logger.info("=" * 60)
            logger.info(f"Destination: {destination}")
            logger.info(f"Duration: {duration_seconds} seconds")
            logger.info(f"Privacy Status: {privacy_status}")
            logger.info(f"Create Files: {create_files}")
            logger.info("=" * 60)
            
            results = {
                "destination": destination,
                "duration_seconds": duration_seconds,
                "privacy_status": privacy_status,
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "status": "pending",
                "results": {}
            }
            
            # Step 1: Create mock video
            video_path = None
            if create_files:
                logger.info("Step 1: Creating mock video...")
                video_path = self.create_mock_video(destination, duration_seconds)
                
                if not video_path:
                    logger.error("Failed to create mock video")
                    results["status"] = "failed"
                    results["errors"] = ["Failed to create mock video"]
                    results["completed_at"] = datetime.now().isoformat()
                    return results
                
                results["results"]["video_creation"] = {
                    "status": "success",
                    "video_path": str(video_path)
                }
            else:
                # Use existing video file
                videos_dir = Path(settings_long.VIDEOS_DIR)
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                video_path = videos_dir / f"{safe_destination}_test_video.mp4"
                
                if not video_path.exists():
                    logger.error(f"Video file not found: {video_path}")
                    results["status"] = "failed"
                    results["errors"] = [f"Video file not found: {video_path}"]
                    results["completed_at"] = datetime.now().isoformat()
                    return results
            
            # Step 2: Create mock thumbnail
            thumbnail_path = None
            if create_files:
                logger.info("Step 2: Creating mock thumbnail...")
                thumbnail_path = self.create_mock_thumbnail(destination)
                
                if thumbnail_path:
                    results["results"]["thumbnail_creation"] = {
                        "status": "success",
                        "thumbnail_path": str(thumbnail_path)
                    }
                else:
                    logger.warning("Failed to create mock thumbnail (continuing without thumbnail)")
                    results["results"]["thumbnail_creation"] = {
                        "status": "failed",
                        "errors": ["Failed to create mock thumbnail"]
                    }
            else:
                # Use existing thumbnail file
                thumbnails_dir = Path(settings_long.THUMBNAILS_DIR)
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                thumbnail_path = thumbnails_dir / f"{safe_destination}_test_thumbnail.jpg"
                
                if not thumbnail_path.exists():
                    logger.warning(f"Thumbnail file not found: {thumbnail_path} (continuing without thumbnail)")
                    thumbnail_path = None
            
            # Step 3: Test YouTube upload
            logger.info("Step 3: Testing YouTube upload...")
            upload_result = self.test_youtube_upload(
                destination=destination,
                video_path=video_path,
                thumbnail_path=thumbnail_path,
                privacy_status=privacy_status
            )
            
            results["results"]["upload"] = upload_result
            
            # Update status
            if upload_result.get('status') == 'success':
                results["status"] = "completed"
            else:
                results["status"] = "failed"
            
            results["completed_at"] = datetime.now().isoformat()
            
            # Print final summary
            logger.info("=" * 60)
            logger.info("TEST RESULTS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Status: {results['status']}")
            logger.info(f"Video Path: {video_path}")
            logger.info(f"Thumbnail Path: {thumbnail_path}")
            
            if upload_result.get('youtube_url'):
                logger.info(f"YouTube URL: {upload_result['youtube_url']}")
            
            if upload_result.get('errors'):
                logger.error(f"Errors: {upload_result['errors']}")
            
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
    
    parser = argparse.ArgumentParser(description="YouTube Upload Test for Long Video System")
    parser.add_argument(
        "--destination",
        type=str,
        default="Bali, Indonesia",
        help="Destination name (default: 'Bali, Indonesia')"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Video duration in seconds (default: 60)"
    )
    parser.add_argument(
        "--privacy-status",
        type=str,
        default="private",
        choices=["private", "unlisted", "public"],
        help="YouTube privacy status (default: 'private')"
    )
    parser.add_argument(
        "--no-create-files",
        action="store_true",
        help="Don't create mock video and thumbnail files (use existing files)"
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 60)
        logger.info("YOUTUBE UPLOAD TEST SCRIPT")
        logger.info("=" * 60)
        logger.info(f"Destination: {args.destination}")
        logger.info(f"Duration: {args.duration} seconds")
        logger.info(f"Privacy Status: {args.privacy_status}")
        logger.info(f"Create Files: {not args.no_create_files}")
        logger.info("=" * 60)
        
        # Initialize tester
        tester = YouTubeUploadTester()
        
        # Run test
        results = tester.run_test(
            destination=args.destination,
            duration_seconds=args.duration,
            privacy_status=args.privacy_status,
            create_files=not args.no_create_files
        )
        
        # Print final summary
        logger.info("=" * 60)
        logger.info("TEST COMPLETE")
        logger.info("=" * 60)
        
        # Exit with appropriate code
        if results.get('status') == 'completed':
            logger.info("✅ All tests passed!")
            sys.exit(0)
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


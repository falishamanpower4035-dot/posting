#!/usr/bin/env python3
"""
Test YouTube Upload with Minimal Tags
Tests YouTube upload with a minimal set of safe tags to debug tag validation issue
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Import components
from core.social.platforms.youtube_uploader_long import YouTubeUploaderLong
from config import settings_long


class MinimalTagTester:
    """
    Test YouTube upload with minimal tags
    """
    
    def __init__(self):
        self.youtube_uploader = YouTubeUploaderLong()
        logger.info("Minimal Tag Tester initialized")
    
    def test_minimal_tags(self, video_path: Path, destination: str = "Bali", privacy_status: str = "private") -> Dict[str, Any]:
        """
        Test YouTube upload with minimal safe tags
        
        Args:
            video_path: Path to video file
            destination: Destination name
            privacy_status: YouTube privacy status
            
        Returns:
            Dictionary with upload results
        """
        try:
            logger.info("=" * 60)
            logger.info("TESTING YOUTUBE UPLOAD WITH MINIMAL TAGS")
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
                "itinerary": []
            }
            
            # Generate title and description
            ideal_days = sample_itinerary.get('ideal_days', 0)
            title = self.youtube_uploader.generate_title(destination, ideal_days, sample_itinerary)
            description = self.youtube_uploader.generate_description(destination, sample_itinerary)
            
            # Test with minimal safe tags (5-10 tags)
            minimal_tags = [
                "travel",
                "bali",
                "itinerary",
                "travel guide",
                "travel vlog"
            ]
            
            logger.info(f"Title: {title}")
            logger.info(f"Description: {len(description)} chars")
            logger.info(f"Minimal Tags: {minimal_tags}")
            logger.info(f"Tag Count: {len(minimal_tags)}")
            logger.info(f"Total Tag Chars: {sum(len(t) + 1 for t in minimal_tags) - 1}")
            
            # Prepare video metadata with minimal tags
            try:
                from googleapiclient.http import MediaFileUpload
                from googleapiclient.errors import HttpError
                
                request_body = {
                    "snippet": {
                        "categoryId": "22",  # Travel & Events
                        "title": title,
                        "description": description,
                        "tags": minimal_tags
                    },
                    "status": {
                        "privacyStatus": privacy_status
                    }
                }
                
                # Create media upload object
                media_file = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
                
                logger.info("Uploading video to YouTube with minimal tags...")
                
                # Execute upload
                request = self.youtube_uploader.youtube.videos().insert(
                    part="snippet,status",
                    body=request_body,
                    media_body=media_file
                )
                
                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"Upload progress: {progress}%")
                
                if 'id' in response:
                    video_id = response['id']
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    logger.info(f"✅ Video uploaded successfully!")
                    logger.info(f"YouTube Video ID: {video_id}")
                    logger.info(f"YouTube URL: {youtube_url}")
                    
                    return {
                        "status": "success",
                        "youtube_video_id": video_id,
                        "youtube_url": youtube_url,
                        "tags_used": minimal_tags,
                        "completed_at": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Upload failed: {response}")
                    return {
                        "status": "failed",
                        "errors": [f"Upload failed: {response}"],
                        "completed_at": datetime.now().isoformat()
                    }
                    
            except HttpError as e:
                error_details = str(e)
                logger.error(f"YouTube API error: {error_details}")
                
                # Try to extract more details
                if hasattr(e, 'content'):
                    import json
                    try:
                        error_content = json.loads(e.content.decode())
                        logger.error(f"Error content: {error_content}")
                    except:
                        pass
                
                return {
                    "status": "failed",
                    "errors": [error_details],
                    "tags_used": minimal_tags,
                    "completed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Test failed: {e}")
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
    
    parser = argparse.ArgumentParser(description="Test YouTube Upload with Minimal Tags")
    parser.add_argument(
        "--video-path",
        type=str,
        required=True,
        help="Path to video file"
    )
    parser.add_argument(
        "--destination",
        type=str,
        default="Bali",
        help="Destination name (default: 'Bali')"
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
        logger.info("YOUTUBE UPLOAD TEST WITH MINIMAL TAGS")
        logger.info("=" * 60)
        logger.info(f"Video Path: {args.video_path}")
        logger.info(f"Destination: {args.destination}")
        logger.info(f"Privacy Status: {args.privacy_status}")
        logger.info("=" * 60)
        
        # Initialize tester
        tester = MinimalTagTester()
        
        # Run test
        video_path = Path(args.video_path)
        results = tester.test_minimal_tags(
            video_path=video_path,
            destination=args.destination,
            privacy_status=args.privacy_status
        )
        
        # Print results
        logger.info("=" * 60)
        logger.info("TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Status: {results.get('status', 'unknown')}")
        
        if results.get('youtube_url'):
            logger.info(f"YouTube URL: {results['youtube_url']}")
        
        if results.get('errors'):
            logger.error(f"Errors: {results['errors']}")
        
        logger.info("=" * 60)
        
        # Exit with appropriate code
        if results.get('status') == 'success':
            logger.info("✅ Test passed!")
            sys.exit(0)
        else:
            logger.error("❌ Test failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


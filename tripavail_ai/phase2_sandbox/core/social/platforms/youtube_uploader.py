#!/usr/bin/env python3
"""
YouTube API Integration for TripAvail AI
Automated video uploads to YouTube using refresh token
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
except ImportError:
    logger.error("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    raise

# Import centralized configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import settings

# YouTube API settings
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


class YouTubeUploader:
    """
    YouTube API integration for automated video uploads using refresh token
    """
    
    def __init__(self):
        """Initialize YouTube uploader with centralized credentials"""
        self.youtube = None
        self.credentials = None
        
        # Initialize with refresh token
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize credentials using refresh token from centralized config"""
        try:
            # Build credentials using refresh token from settings - SINGLE SOURCE OF TRUTH
            self.credentials = Credentials(
                None,  # No access token initially
                refresh_token=settings.YOUTUBE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET,
                scopes=[
                    "https://www.googleapis.com/auth/youtube.readonly",
                    "https://www.googleapis.com/auth/youtube.upload"
                ]  # Match the refresh token scopes
            )
            
            # Build YouTube service
            self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=self.credentials)
            
            logger.info("YouTube credentials initialized successfully")
            logger.info(f"Account: {settings.YOUTUBE_EMAIL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize YouTube credentials: {e}")
            self.youtube = None
            self.credentials = None
    
    def authenticate(self) -> bool:
        """
        Test authentication (credentials are already initialized)
        
        Returns:
            True if successful, False otherwise
        """
        return self.test_connection()
    
    def upload_video(self, video_path: Path, title: str, description: str, 
                    tags: list = None, category_id: str = "22", 
                    privacy_status: str = "public", thumbnail_path: Path = None) -> Optional[str]:
        """
        Upload video to YouTube using TripAvail credentials
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (22 = People & Blogs)
            privacy_status: public, private, or unlisted
            
        Returns:
            Video ID if successful, None otherwise
        """
        try:
            if not self.youtube:
                logger.error("YouTube service not initialized")
                return None
            
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None
            
            # Prepare video metadata
            request_body = {
                "snippet": {
                    "categoryId": category_id,
                    "title": title,
                    "description": description,
                    "tags": tags or []
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
            
            # Create media upload object
            media_file = MediaFileUpload(str(video_path))
            
            logger.info(f"Uploading video: {video_path.name}")
            logger.info(f"Title: {title}")
            logger.info(f"Privacy: {privacy_status}")
            logger.info(f"Account: {settings.YOUTUBE_EMAIL}")
            
            # Execute upload
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media_file
            )
            
            response = request.execute()
            
            if 'id' in response:
                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"Video uploaded successfully!")
                logger.info(f"Video ID: {video_id}")
                logger.info(f"Video URL: {video_url}")
                
                # Upload thumbnail if provided
                if thumbnail_path and thumbnail_path.exists():
                    try:
                        self._upload_thumbnail(video_id, thumbnail_path)
                        logger.info(f"9:16 thumbnail uploaded successfully!")
                    except Exception as e:
                        logger.warning(f"Failed to upload thumbnail: {e}")
                
                return video_id
            else:
                logger.error(f"Upload failed: {response}")
                return None
                
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path):
        """Upload custom 9:16 thumbnail for video"""
        try:
            # YouTube accepts 9:16 thumbnails for Shorts
            from PIL import Image
            
            # Load and ensure thumbnail is 9:16 (1080x1920)
            with Image.open(thumbnail_path) as img:
                # Ensure it's 9:16 format
                if img.size != (1080, 1920):
                    thumbnail = img.resize((1080, 1920), Image.Resampling.LANCZOS)
                else:
                    thumbnail = img
                
                # Save temporary thumbnail
                temp_path = thumbnail_path.parent / f"temp_yt_thumb_{video_id}.jpg"
                thumbnail.save(temp_path, "JPEG", quality=95)
            
            # Upload thumbnail
            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(temp_path), mimetype='image/jpeg')
            )
            
            request.execute()
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
                
        except Exception as e:
            logger.error(f"Thumbnail upload error: {e}")
            raise
    
    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """
        Get channel information
        
        Returns:
            Channel info if successful, None otherwise
        """
        try:
            if not self.youtube:
                logger.error("YouTube service not initialized")
                return None
            
            response = self.youtube.channels().list(part='snippet,statistics', mine=True).execute()
            
            if 'items' in response and response['items']:
                channel = response['items'][0]
                info = {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet']['description'],
                    'subscriber_count': channel['statistics'].get('subscriberCount', '0'),
                    'video_count': channel['statistics'].get('videoCount', '0'),
                    'view_count': channel['statistics'].get('viewCount', '0'),
                    'email': EMAIL
                }
                logger.info(f"Channel: {info['title']}")
                logger.info(f"Email: {info['email']}")
                logger.info(f"Subscribers: {info['subscriber_count']}")
                logger.info(f"Videos: {info['video_count']}")
                return info
            else:
                logger.error("No channel found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test YouTube API connection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.youtube:
                logger.error("YouTube service not initialized")
                return False
            
            # Test with a simple API call
            try:
                response = self.youtube.channels().list(part='snippet', mine=True).execute()
                if 'items' in response and response['items']:
                    channel = response['items'][0]
                    logger.info(f"YouTube API connection successful!")
                    logger.info(f"Channel: {channel['snippet']['title']}")
                    logger.info(f"Account: {settings.YOUTUBE_EMAIL}")
                    return True
                else:
                    logger.error("No channel found")
                    return False
            except Exception as e:
                logger.error(f"API test failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"YouTube connection test failed: {e}")
            return False


def main():
    """Test YouTube integration"""
    print("\n" + "="*60)
    print("YOUTUBE API INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Initialize YouTube uploader
    youtube_uploader = YouTubeUploader()
    
    # Test connection
    print("Testing YouTube API connection...")
    if youtube_uploader.test_connection():
        print("SUCCESS: Connected to YouTube successfully!")
        
        # Test with a sample video if available
        sample_video = Path("data/videos/reel_1_final.mp4")
        if sample_video.exists():
            print(f"\nTesting video upload with: {sample_video.name}")
            
            title = "Bangkok Night Market - Premium Travel Experience | TripAvail"
            description = """Discover the magic of Bangkok's night markets! 

As twilight falls, the aroma of jasmine fills the air, and the vibrant night market pulses with life. This is where your senses ignite.

#Travel #Bangkok #NightMarket #TripAvail #Adventure #Thailand #TravelVlog #LuxuryTravel"""
            tags = ["Travel", "Bangkok", "Night Market", "TripAvail", "Adventure", "Thailand", "Travel Vlog", "Luxury Travel"]
            
            video_id = youtube_uploader.upload_video(
                video_path=sample_video,
                title=title,
                description=description,
                tags=tags,
                privacy_status="unlisted"  # Start as unlisted for testing
            )
            
            if video_id:
                print(f"SUCCESS: Video uploaded! ID: {video_id}")
                print(f"URL: https://www.youtube.com/watch?v={video_id}")
            else:
                print("ERROR: Video upload failed")
        else:
            print("INFO: No sample video found for testing")
    else:
        print("ERROR: YouTube connection failed")
    
    print("\n" + "="*60)
    print("YOUTUBE INTEGRATION TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()

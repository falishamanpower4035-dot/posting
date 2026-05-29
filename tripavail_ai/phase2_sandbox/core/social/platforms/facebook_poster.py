#!/usr/bin/env python3
"""
Facebook Graph API Integration for TripAvail AI
Automated posting to Facebook Pages
"""

import os
import json
import requests
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import centralized configuration
from config import settings


class FacebookPoster:
    """
    Facebook Graph API integration for automated posting
    """
    
    def __init__(self):
        # Load from centralized config - SINGLE SOURCE OF TRUTH
        self.access_token = settings.FACEBOOK_GRAPH_TOKEN
        self.api_version = settings.FACEBOOK_API_VERSION
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        # Validate token
        if not self.access_token or self.access_token == "your_facebook_token_here":
            logger.error("Facebook Graph API token not configured")
            raise ValueError("Facebook Graph API token required")
        
        logger.info("Facebook Poster initialized")
    
    def get_page_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the Facebook Page
        """
        try:
            url = f"{self.base_url}/me"
            params = {
                'access_token': self.access_token,
                'fields': 'id,name,category,fan_count'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            page_info = response.json()
            logger.info(f"Connected to Facebook Page: {page_info.get('name', 'Unknown')}")
            logger.info(f"Page ID: {page_info.get('id', 'Unknown')}")
            logger.info(f"Category: {page_info.get('category', 'Unknown')}")
            logger.info(f"Fan Count: {page_info.get('fan_count', 'Unknown')}")
            
            return page_info
            
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return None
    
    def upload_video_reel(self, video_path: Path, description: str) -> Optional[str]:
        """
        Upload video to Facebook Page as a Reel (short-form vertical video)
        
        Args:
            video_path: Path to video file (9:16 aspect ratio)
            description: Reel description/caption
            
        Returns:
            Reel ID if successful, None otherwise
        """
        try:
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return None
            
            # Step 1: Initialize upload session for Reels
            init_url = f"{self.base_url}/me/video_reels"
            
            # Get file size
            file_size = video_path.stat().st_size
            
            init_data = {
                'access_token': self.access_token,
                'upload_phase': 'start',
                'file_size': file_size
            }
            
            logger.info(f"📤 Initializing Reel upload session for: {video_path.name} ({file_size / (1024*1024):.1f} MB)")
            init_response = requests.post(init_url, data=init_data, timeout=30)
            init_response.raise_for_status()
            init_result = init_response.json()
            
            video_id = init_result.get('video_id')
            upload_url = init_result.get('upload_url')
            
            if not video_id or not upload_url:
                logger.error(f"Failed to initialize upload: {init_result}")
                return None
            
            logger.info(f"✅ Upload session created - Video ID: {video_id}")
            
            # Step 2: Upload video file
            logger.info(f"📤 Uploading Reel video...")
            with open(video_path, 'rb') as video_file:
                upload_response = requests.post(
                    upload_url,
                    files={'file': video_file},
                    data={'access_token': self.access_token},
                    timeout=300  # 5 minutes for large files
                )
                upload_response.raise_for_status()
            
            logger.info(f"✅ Reel video uploaded successfully!")
            
            # Step 3: Finish upload and publish
            finish_data = {
                'access_token': self.access_token,
                'upload_phase': 'finish',
                'video_id': video_id,
                'video_state': 'PUBLISHED',
                'description': description
            }
            
            logger.info(f"📤 Publishing Reel...")
            finish_response = requests.post(init_url, data=finish_data, timeout=30)
            finish_response.raise_for_status()
            finish_result = finish_response.json()
            
            if finish_result.get('success'):
                logger.info(f"✅ Reel published successfully! ID: {video_id}")
                logger.info(f"🎬 Your Reel is now live on Facebook!")
                return video_id
            else:
                logger.error(f"Failed to publish Reel: {finish_result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            # Log detailed error response
            if hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error = error_data['error']
                        error_code = error.get('code')
                        error_msg = error.get('message')
                        error_type = error.get('type')
                        logger.error(f"❌ Facebook API Error: Code {error_code} ({error_type}): {error_msg}")
                        
                        # Check for rate limiting (Code 368)
                        if error_code == 368:
                            logger.error("🚫 Rate limit exceeded! Facebook is throttling posts to prevent spam.")
                            logger.warning("💡 Solution: Reduce posting frequency or wait before retrying.")
                            # Don't fallback on rate limit - just fail
                            return None
                except:
                    pass
            
            logger.error(f"❌ Failed to upload Reel: {e}")
            # Fallback to regular video upload (only if not rate limited)
            logger.warning(f"⚠️ Falling back to regular video upload...")
            return self.upload_video_fallback(video_path, description)
        except Exception as e:
            logger.error(f"❌ Failed to upload Reel: {e}")
            # Fallback to regular video upload
            logger.warning(f"⚠️ Falling back to regular video upload...")
            return self.upload_video_fallback(video_path, description)
    
    def upload_video_fallback(self, video_path: Path, description: str) -> Optional[str]:
        """
        Fallback: Upload video as regular video if Reel upload fails
        
        Args:
            video_path: Path to video file
            description: Video description/caption
            
        Returns:
            Video ID if successful, None otherwise
        """
        try:
            # Upload as regular video
            url = f"{self.base_url}/me/videos"
            
            files = {
                'file': open(video_path, 'rb')
            }
            
            data = {
                'access_token': self.access_token,
                'description': description,
                'published': 'true'
            }
            
            logger.info(f"📤 Uploading as regular video: {video_path.name}")
            response = requests.post(url, files=files, data=data, timeout=120)
            files['file'].close()
            
            response.raise_for_status()
            result = response.json()
            
            video_id = result.get('id')
            if video_id:
                logger.info(f"✅ Video uploaded successfully! ID: {video_id}")
                return video_id
            else:
                logger.error(f"Upload failed: {result}")
                return None
                
        except requests.exceptions.HTTPError as e:
            # Log detailed error response
            if hasattr(e.response, 'json'):
                try:
                    error_data = e.response.json()
                    if 'error' in error_data:
                        error = error_data['error']
                        error_code = error.get('code')
                        error_msg = error.get('message')
                        error_type = error.get('type')
                        logger.error(f"❌ Facebook API Error: Code {error_code} ({error_type}): {error_msg}")
                        
                        # Check for rate limiting (Code 368)
                        if error_code == 368:
                            logger.error("🚫 Rate limit exceeded! Facebook is throttling posts to prevent spam.")
                            logger.warning("💡 Solution: Reduce posting frequency or wait before retrying.")
                        elif error_code == 390:
                            logger.error("⏱️ Upload timeout. Video may be too large or network too slow.")
                except:
                    pass
            
            logger.error(f"Failed to upload video: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return None
    
    def publish_video(self, video_id: str, caption: str, hashtags: list = None) -> bool:
        """
        Publish uploaded video to Facebook Page
        
        Args:
            video_id: ID of uploaded video
            caption: Post caption (may already include hashtags)
            hashtags: List of hashtags (optional - only used if caption doesn't already have them)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # CRITICAL: Preserve exact hashtag casing
            # If caption already includes hashtags, use it as-is
            # Otherwise, append hashtags preserving exact case
            full_caption = caption
            if hashtags and "#" not in caption:
                # Only add hashtags if they're not already in the caption
                hashtag_text = " ".join(hashtags)  # Preserve exact case
                full_caption = f"{caption}\n\n{hashtag_text}"
            
            # Method 1: Try to publish the existing video
            url = f"{self.base_url}/{video_id}"
            data = {
                'access_token': self.access_token,
                'description': full_caption,
                'published': 'true'
            }
            
            logger.info(f"Publishing video {video_id} to Facebook")
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"Video published successfully! Post ID: {video_id}")
                    return True
            
            # Method 2: If that fails, try creating a new post with the video
            logger.info("Trying alternative publishing method...")
            url = f"{self.base_url}/me/feed"
            data = {
                'access_token': self.access_token,
                'message': full_caption,
                'attached_media': f"[{{\"media_fbid\":\"{video_id}\"}}]"
            }
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('id'):
                logger.info(f"Video published successfully! Post ID: {result.get('id')}")
                return True
            else:
                logger.error(f"Publish failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to publish video: {e}")
            return False
    
    def post_video(self, video_path: Path, caption: str, hashtags: list = None) -> bool:
        """
        Complete workflow: Upload and publish video as Facebook Reel
        
        Args:
            video_path: Path to video file (9:16 aspect ratio for Reels)
            caption: Post caption (may already include hashtags)
            hashtags: List of hashtags (optional - only used if caption doesn't already have them)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🎬 Starting Facebook Reel post for: {video_path.name}")
            
            # CRITICAL: Preserve exact hashtag casing
            # Caption from scheduler_daemon already includes hashtags, so use it as-is
            # Don't add hashtags again if they're already in the caption
            full_caption = caption
            if hashtags and "#" not in caption:
                # Only add hashtags if they're not already in the caption
                hashtag_text = " ".join(hashtags)  # Preserve exact case - no modification
                full_caption = f"{caption}\n\n{hashtag_text}"
            # If caption already has hashtags, use it as-is (preserves exact case)
            
            # Upload and publish as Reel
            video_id = self.upload_video_reel(video_path, full_caption)
            if video_id:
                logger.info("✅ Facebook Reel posted successfully!")
                logger.info(f"🎉 Reel ID: {video_id}")
                return True
            else:
                logger.error("❌ Failed to post Reel to Facebook")
                return False
                
        except Exception as e:
            logger.error(f"Facebook Reel posting failed: {e}")
            return False
    
    def get_insights(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get insights for a published post
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            Insights data if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{post_id}/insights"
            params = {
                'access_token': self.access_token,
                'metric': 'post_impressions,post_engaged_users,post_video_views'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            insights = response.json()
            logger.info(f"Retrieved insights for post {post_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test Facebook API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            page_info = self.get_page_info()
            if page_info:
                logger.info("✅ Facebook API connection successful!")
                return True
            else:
                logger.error("❌ Facebook API connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Facebook API test failed: {e}")
            return False


def main():
    """Test Facebook Reels integration"""
    print("\n" + "="*60)
    print("🎬 FACEBOOK REELS INTEGRATION TEST")
    print("="*60 + "\n")
    
    try:
        # Initialize Facebook poster
        fb_poster = FacebookPoster()
        
        # Test connection
        print("Testing Facebook API connection...")
        if fb_poster.test_connection():
            print("✅ SUCCESS: Connected to Facebook successfully!")
            
            # Test with a sample video if available
            sample_video = Path("data/posts/post_010/video/final.mp4")
            if sample_video.exists():
                print(f"\n🎬 Testing Reel upload with: {sample_video.name}")
                
                caption = "Discover the magic of travel! ✈️"
                hashtags = ["#Travel", "#TripAvail", "#Reels", "#Adventure", "#Explore"]
                
                success = fb_poster.post_video(sample_video, caption, hashtags)
                if success:
                    print("✅ SUCCESS: Reel posted to Facebook successfully!")
                    print("🎉 Check your Facebook Page for the new Reel!")
                else:
                    print("❌ ERROR: Reel posting failed")
            else:
                print("⚠️  INFO: No sample video found for testing")
                print(f"    Looking for: {sample_video}")
        else:
            print("❌ ERROR: Facebook connection failed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print("🎬 FACEBOOK REELS TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()

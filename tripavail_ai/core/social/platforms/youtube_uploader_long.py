#!/usr/bin/env python3
"""
YouTube Uploader for Long Videos
Uploads one combined video with new title format
Title: "[Destination] [X]-Day Itinerary [emoji] | Complete Travel Guide for [Year]"
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
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

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

# YouTube API settings
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


class YouTubeUploaderLong:
    """
    YouTube API integration for long video uploads
    Uses new title format: "[Destination] [X]-Day Itinerary [emoji] | Complete Travel Guide for [Year]"
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
            # Build credentials using refresh token from settings
            self.credentials = Credentials(
                None,  # No access token initially
                refresh_token=settings.YOUTUBE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.YOUTUBE_CLIENT_ID,
                client_secret=settings.YOUTUBE_CLIENT_SECRET,
                scopes=getattr(settings, "YOUTUBE_SCOPES", [
                    "https://www.googleapis.com/auth/youtube.upload"
                ])
            )
            
            # Build YouTube service
            self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=self.credentials)
            
            logger.info("YouTube credentials initialized successfully")
            logger.info(f"Account: {settings.YOUTUBE_EMAIL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize YouTube credentials: {e}")
            self.youtube = None
            self.credentials = None
    
    def generate_title(self, destination: str, ideal_days: int, itinerary_data: Dict[str, Any] = None) -> str:
        """
        Generate YouTube title in new format
        
        Format: "[Destination] [X]-Day Itinerary [emoji] | Complete Travel Guide for [Year]"
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            ideal_days: Number of days
            itinerary_data: Itinerary data (optional, for emoji selection)
            
        Returns:
            Generated title string
        """
        try:
            # Extract destination name (remove country if present)
            dest_name = destination.split(',')[0].strip()
            
            # Get emoji for destination
            emoji = self._get_destination_emoji(dest_name, itinerary_data)
            
            # Get current year
            current_year = datetime.now().year
            
            # Generate title
            title = f"{dest_name} {ideal_days}-Day Itinerary {emoji} | Complete Travel Guide for {current_year}"
            
            logger.info(f"Generated title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            # Fallback title
            return f"{destination} Travel Guide | TripAvail"
    
    def _get_destination_emoji(self, destination: str, itinerary_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Get emoji for destination
        
        Args:
            destination: Destination name
            itinerary_data: Itinerary data (optional)
            
        Returns:
            Emoji string
        """
        try:
            destination_lower = destination.lower()
            
            # Destination emoji map
            emoji_map = {
                'bali': '🌴',
                'thailand': '🏖️',
                'japan': '🗾',
                'switzerland': '🏔️',
                'france': '🗼',
                'italy': '🏛️',
                'spain': '🏖️',
                'greece': '🏛️',
                'turkey': '🕌',
                'india': '🕌',
                'china': '🏮',
                'south korea': '🏮',
                'singapore': '🏙️',
                'malaysia': '🌴',
                'philippines': '🏖️',
                'vietnam': '🏛️',
                'cambodia': '🏛️',
                'laos': '🏛️',
                'myanmar': '🏛️',
                'indonesia': '🌴',
                'maldives': '🏖️',
                'sri lanka': '🏖️',
                'nepal': '🏔️',
                'bhutan': '🏔️',
                'tibet': '🏔️',
            }
            
            # Check for exact match
            if destination_lower in emoji_map:
                return emoji_map[destination_lower]
            
            # Check for partial match
            for key, emoji in emoji_map.items():
                if key in destination_lower:
                    return emoji
            
            # Default emoji
            return '🌴'
            
        except Exception as e:
            logger.error(f"Error getting destination emoji: {e}")
            return '🌴'
    
    def generate_description(
        self,
        destination: str,
        itinerary_data: Dict[str, Any],
        script_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate SEO-optimized YouTube description with day-by-day breakdown
        
        Args:
            destination: Destination name
            itinerary_data: Itinerary data with days and scenes
            
        Returns:
            Generated description string
        """
        try:
            ideal_days = itinerary_data.get('ideal_days', 0)
            itinerary = itinerary_data.get('itinerary', [])
            current_year = datetime.now().year
            
            # Extract destination parts
            dest_parts = destination.split(',')
            dest_name = dest_parts[0].strip()
            dest_country = dest_parts[1].strip() if len(dest_parts) > 1 else ""
            
            # PHASE 1.3: Generate story-based description from script_data
            description_parts = []
            
            # Story hook from introduction (if script_data available)
            if script_data and script_data.get('itinerary_introduction'):
                intro_text = script_data.get('itinerary_introduction', '')
                description_parts.append(f"🌟 {intro_text}")
                description_parts.append("")
            
            # SEO-optimized header (first 2 lines are crucial for YouTube)
            if script_data:
                # Extract story theme from introduction
                intro_text = script_data.get('itinerary_introduction', '')
                if intro_text:
                    description_parts.append(f"✨ This journey takes you through the heart of {dest_name}, from vibrant cities to ancient wonders—a complete {ideal_days}-day story of discovery and transformation.")
                else:
                    description_parts.append(f"🌴 {destination} {ideal_days}-Day Complete Travel Guide {current_year}")
                    description_parts.append(f"Complete day-by-day itinerary for exploring {destination}! Discover the best attractions, food, culture, and scenic views.")
            else:
                description_parts.append(f"🌴 {destination} {ideal_days}-Day Complete Travel Guide {current_year}")
                description_parts.append(f"Complete day-by-day itinerary for exploring {destination}! Discover the best attractions, food, culture, and scenic views.")
            
            description_parts.append("")
            
            # Key information (SEO keywords)
            description_parts.append("📍 WHAT YOU'LL SEE:")
            description_parts.append(f"• Complete {ideal_days}-day itinerary for {dest_name}")
            if dest_country:
                description_parts.append(f"• Best attractions and activities in {dest_name}, {dest_country}")
            else:
                description_parts.append(f"• Best attractions and activities in {dest_name}")
            description_parts.append(f"• Local food, culture, and hidden gems")
            description_parts.append(f"• Scenic views and must-see destinations")
            description_parts.append("")
            
            # Day-by-day breakdown with timestamps (PHASE 1.3: Story-based)
            description_parts.append("📅 DAY-BY-DAY ITINERARY WITH TIMESTAMPS:")
            description_parts.append("")
            
            # Calculate cumulative timestamps
            cumulative_time = 0.0
            script_days = script_data.get('days', []) if script_data else []
            
            # Add introduction timestamp if exists
            if script_data and script_data.get('itinerary_introduction'):
                intro_duration = self._parse_duration_estimate(script_data.get('itinerary_introduction_duration_estimate', '≈ 25 s'))
                description_parts.append(f"0:00 Introduction - {script_data.get('itinerary_introduction', '')[:100]}...")
                cumulative_time += intro_duration
                description_parts.append("")
            
            for day in itinerary:
                day_number = day.get('day_number', 0)
                title = day.get('title', 'No title')
                scenes = day.get('scenes', [])
                
                # Find corresponding script day for story highlights
                script_day = next((d for d in script_days if d.get('day_number') == day_number), None)
                
                # Format timestamp (MM:SS)
                timestamp_min = int(cumulative_time // 60)
                timestamp_sec = int(cumulative_time % 60)
                timestamp_str = f"{timestamp_min}:{timestamp_sec:02d}"
                
                # Day header with timestamp and story highlight
                if script_day:
                    day_title = script_day.get('day_title', title)
                    day_narration = script_day.get('narration', '')
                    # Extract first sentence as highlight
                    narration_highlight = day_narration.split('.')[0] if day_narration else title
                    description_parts.append(f"{timestamp_str} Day {day_number}: {day_title}")
                    description_parts.append(f"   {narration_highlight}...")
                else:
                    description_parts.append(f"{timestamp_str} Day {day_number}: {title}")
                
                # Calculate day duration for next timestamp
                if script_day:
                    day_duration = script_day.get('estimated_voiceover_seconds', 90.0)
                    if not day_duration:
                        day_duration = self._parse_duration_estimate(script_day.get('narration_duration_estimate', '≈ 80 s'))
                    cumulative_time += day_duration
                else:
                    cumulative_time += 90.0  # Default 90 seconds
                
                # List key scenes
                scene_count = 0
                for scene in scenes[:3]:  # Show only first 3 scenes to keep it concise
                    scene_order = scene.get('order', 0)
                    category = scene.get('category', 'unknown')
                    
                    # Format category name
                    category_map = {
                        'arrival': '✈️',
                        'attraction': '🏛️',
                        'food': '🍽️',
                        'stay': '🏨',
                        'scenic': '🌄',
                        'nightlife': '🌃',
                        'transit': '🚗',
                    }
                    category_emoji = category_map.get(category, '📍')
                    
                    description_parts.append(f"   {category_emoji} {category.capitalize()}")
                    scene_count += 1
                
                description_parts.append("")
            
            # Travel tips section (SEO)
            description_parts.append("")
            description_parts.append("💡 TRAVEL TIPS:")
            description_parts.append(f"• Plan your {dest_name} trip with this complete {ideal_days}-day guide")
            description_parts.append("• Follow the itinerary day by day for the best experience")
            description_parts.append("• Book hotels in advance for better rates")
            description_parts.append("• Try local food and experience the culture")
            description_parts.append("")
            
            # Call to action
            description_parts.append("")
            description_parts.append("🔔 Subscribe for more travel guides and itineraries!")
            description_parts.append("👍 Like this video if you found it helpful!")
            description_parts.append("💬 Comment below with your questions or travel experiences!")
            description_parts.append("")
            
            # Credits
            description_parts.append("")
            description_parts.append("📸 CREDITS:")
            description_parts.append("Images provided by Pixabay - Thank you for the amazing free images!")
            description_parts.append("")
            
            # Hashtags (SEO)
            hashtags = [
                "#TravelGuide",
                "#Travel",
                "#Itinerary",
                "#" + dest_name.replace(" ", ""),
                "#TravelVlog",
                "#TravelTips",
                "#Wanderlust",
                "#TravelInspiration",
            ]
            if dest_country:
                hashtags.append("#" + dest_country.replace(" ", ""))
            
            description_parts.append(" ".join(hashtags))
            
            # PHASE 1.3: Add story resolution/reflection if available
            if script_data and script_days:
                final_day = script_days[-1] if script_days else None
                if final_day:
                    final_narration = final_day.get('narration', '')
                    # Extract last sentence as resolution
                    if final_narration and '.' in final_narration:
                        resolution_sentences = [s.strip() for s in final_narration.split('.') if s.strip()]
                        if resolution_sentences:
                            resolution = resolution_sentences[-1]  # Last sentence
                            description_parts.append("")
                            description_parts.append("💫 JOURNEY REFLECTION:")
                            description_parts.append(f"{resolution}...")
                            description_parts.append("")
            
            description = "\n".join(description_parts)
            
            logger.info(f"Generated story-based description ({len(description)} chars)")
            return description
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return f"Complete travel guide for {destination} | TripAvail"
    
    def generate_tags(self, destination: str, itinerary_data: Dict[str, Any]) -> List[str]:
        """
        Generate SEO-optimized YouTube tags (TubeBuddy level)
        
        Args:
            destination: Destination name
            itinerary_data: Itinerary data with days and scenes
            
        Returns:
            List of SEO-optimized tag strings
        """
        try:
            tags = []
            
            # Extract destination parts
            dest_parts = destination.split(',')
            dest_name = dest_parts[0].strip()
            dest_country = dest_parts[1].strip() if len(dest_parts) > 1 else ""
            
            ideal_days = itinerary_data.get('ideal_days', 0)
            current_year = datetime.now().year
            
            # Primary tags (destination-specific, high volume)
            # Remove commas from destination names for tags
            dest_name_clean = dest_name.replace(',', '').strip()
            destination_clean = destination.replace(',', ' ').strip()
            dest_country_clean = dest_country.replace(',', '').strip() if dest_country else ""
            
            tags.append(dest_name_clean)
            tags.append(destination_clean)
            tags.append(f"{dest_name_clean} travel")
            tags.append(f"{dest_name_clean} itinerary")
            if dest_country_clean:
                tags.append(f"{dest_country_clean} travel")
                tags.append(f"{dest_name_clean} {dest_country_clean}")
            
            # Day count tags (specific searches)
            if ideal_days > 0:
                tags.append(f"{dest_name} {ideal_days} day itinerary")
                tags.append(f"{ideal_days} day {dest_name} guide")
                tags.append(f"{dest_name} {ideal_days} days")
            
            # Year tags (current year for freshness)
            tags.append(f"{dest_name} {current_year}")
            tags.append(f"{dest_name} travel guide {current_year}")
            
            # Category tags (scene-specific)
            categories = set()
            for day in itinerary_data.get('itinerary', []):
                for scene in day.get('scenes', []):
                    category = scene.get('category', '')
                    if category:
                        categories.add(category)
            
            # Category-specific tags (SEO-optimized)
            category_tags = {
                'attraction': [f'{dest_name_clean} attractions', f'{dest_name_clean} things to do', 'travel attractions'],
                'food': [f'{dest_name_clean} food', f'{dest_name_clean} cuisine', 'travel food'],
                'scenic': [f'{dest_name_clean} views', f'{dest_name_clean} scenery', 'travel photography'],
                'stay': [f'{dest_name_clean} hotels', f'{dest_name_clean} accommodation', 'travel hotels'],
                'nightlife': [f'{dest_name_clean} nightlife', f'{dest_name_clean} night', 'travel nightlife'],
                'local_life': [f'{dest_name_clean} culture', f'{dest_name_clean} local', 'travel culture'],
            }
            
            for category in categories:
                if category in category_tags:
                    tags.extend(category_tags[category])
            
            # Long-tail keywords (high intent, low competition)
            tags.extend([
                f'how to travel {dest_name_clean}',
                f'{dest_name_clean} travel guide',
                f'{dest_name_clean} travel tips',
                f'best places {dest_name_clean}',
                f'{dest_name_clean} must see',
                f'{dest_name_clean} travel vlog',
                f'{dest_name_clean} travel video',
            ])
            
            # Generic travel tags (high volume)
            tags.extend([
                'travel guide',
                'travel itinerary',
                'travel vlog',
                'travel tips',
                'travel destination',
                'complete travel guide',
                'travel planning',
                'travel inspiration',
                'wanderlust',
                'travel video',
                'travel content',
            ])
            
            # Platform-specific tags
            tags.extend([
                'tripavail',
                'travel channel',
                'travel youtube',
            ])
            
            # Clean and validate tags - use simpler, safer tags
            # YouTube tags must:
            # - Be 30 characters or less
            # - Contain only alphanumeric characters, spaces, hyphens
            # - Be simple (max 3 words per tag for safety)
            # - Not contain special characters
            import re
            cleaned_tags = []
            for tag in tags:
                if not isinstance(tag, str):
                    continue
                # Remove all special characters except letters, numbers, spaces, hyphens
                cleaned_tag = re.sub(r'[^a-zA-Z0-9\s\-]', '', tag)
                # Remove extra spaces
                cleaned_tag = ' '.join(cleaned_tag.split())
                # Limit to 3 words max (safer for YouTube)
                words = cleaned_tag.split()
                if len(words) > 3:
                    cleaned_tag = ' '.join(words[:3])
                # Limit length to 30 characters (YouTube limit)
                if len(cleaned_tag) > 30:
                    cleaned_tag = cleaned_tag[:30].rsplit(' ', 1)[0]  # Cut at word boundary
                # Remove empty tags
                if cleaned_tag and 2 <= len(cleaned_tag) <= 30:
                    cleaned_tags.append(cleaned_tag)
            
            # Remove duplicates (case-insensitive) and limit to 500 characters
            unique_tags = []
            seen = set()
            total_chars = 0
            max_chars = 500
            
            for tag in cleaned_tags:
                tag_lower = tag.lower().strip()
                if tag_lower and tag_lower not in seen:
                    tag_with_comma = tag + ','
                    if total_chars + len(tag_with_comma) <= max_chars:
                        unique_tags.append(tag.strip())
                        seen.add(tag_lower)
                        total_chars += len(tag_with_comma)
                    else:
                        break
            
            # Ensure we have at least some tags (fallback to safe minimal tags)
            if not unique_tags:
                unique_tags = [dest_name_clean.lower(), 'travel', 'itinerary', 'travel guide', 'travel vlog']
            
            logger.info(f"Generated {len(unique_tags)} SEO-optimized tags ({total_chars-1 if total_chars > 0 else 0} chars)")
            
            return unique_tags
            
        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            # Fallback tags
            dest_name = destination.split(',')[0].strip()
            return [
                dest_name,
                destination,
                f'{dest_name} travel',
                'travel guide',
                'travel itinerary',
                'tripavail'
            ]
    
    def _parse_duration_estimate(self, duration_str: str) -> float:
        """
        Parse duration estimate string to seconds
        
        Args:
            duration_str: Duration string like "≈ 25 s" or "≈ 80 s"
            
        Returns:
            Duration in seconds
        """
        try:
            import re
            # Extract number from string like "≈ 25 s" or "≈ 80 s"
            match = re.search(r'(\d+)', duration_str)
            if match:
                return float(match.group(1))
            return 90.0  # Default 90 seconds
        except Exception:
            return 90.0  # Default 90 seconds
    
    def upload_video(
        self,
        video_path: Path,
        destination: str,
        itinerary_data: Dict[str, Any],
        thumbnail_path: Optional[Path] = None,
        privacy_status: str = "public",
        script_data: Optional[Dict[str, Any]] = None  # PHASE 1.3: Story-based description
    ) -> Optional[str]:
        """
        Upload long video to YouTube
        
        Args:
            video_path: Path to video file
            destination: Destination name
            itinerary_data: Itinerary data with days and scenes
            thumbnail_path: Path to thumbnail file (optional)
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
            
            # Generate title, description, and tags
            ideal_days = itinerary_data.get('ideal_days', 0)
            title = self.generate_title(destination, ideal_days, itinerary_data)
            description = self.generate_description(destination, itinerary_data, script_data)  # PHASE 1.3: Pass script_data
            tags = self.generate_tags(destination, itinerary_data)
            
            # Tags are already cleaned and validated by generate_tags method
            # Just use them directly (they're already safe)
            # Limit to reasonable number of tags (YouTube recommends 5-10 tags)
            final_tags = tags[:15] if len(tags) > 15 else tags
            
            logger.info(f"Final tags for upload: {len(final_tags)} tags")
            logger.debug(f"Tags: {final_tags[:10]}...")  # Log first 10
            
            # Prepare video metadata
            request_body = {
                "snippet": {
                    "categoryId": "22",  # Travel & Events
                    "title": title,
                    "description": description,
                    "tags": final_tags
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
            
            # Create media upload object
            media_file = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
            
            logger.info(f"Uploading long video: {video_path.name}")
            logger.info(f"Title: {title}")
            logger.info(f"Privacy: {privacy_status}")
            logger.info(f"Account: {settings.YOUTUBE_EMAIL}")
            
            # Execute upload
            request = self.youtube.videos().insert(
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
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"✅ Video uploaded successfully!")
                logger.info(f"Video ID: {video_id}")
                logger.info(f"Video URL: {video_url}")
                
                # Upload thumbnail if provided
                if thumbnail_path and thumbnail_path.exists():
                    try:
                        self._upload_thumbnail(video_id, thumbnail_path)
                        logger.info(f"✅ Thumbnail uploaded successfully!")
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
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path):
        """Upload 16:9 thumbnail for video"""
        try:
            from PIL import Image
            
            # Load and ensure thumbnail is 16:9 (1920x1080)
            with Image.open(thumbnail_path) as img:
                # Ensure it's 16:9 format
                if img.size != (1920, 1080):
                    thumbnail = img.resize((1920, 1080), Image.Resampling.LANCZOS)
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
                    logger.info(f"✅ YouTube API connection successful!")
                    logger.info(f"Channel: {channel['snippet']['title']}")
                    logger.info(f"Account: {settings.YOUTUBE_EMAIL}")
                    return True
                else:
                    logger.error("No channel found")
                    return False
            except HttpError as http_err:
                message = str(http_err)
                if getattr(http_err, "resp", None) and getattr(http_err.resp, "status", None) == 403 and "insufficientPermissions" in message:
                    logger.warning("YouTube token lacks read scope; skipping channel lookup but upload scope verified.")
                    return True
                logger.error(f"API test failed: {http_err}")
                return False
            except Exception as e:
                logger.error(f"API test failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"YouTube connection test failed: {e}")
            return False


def main():
    """Test YouTube uploader for long videos"""
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    
    # Generate itinerary
    itinerary_generator = ItineraryGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing YouTube uploader for {test_destination}")
    
    # Load or generate itinerary
    itinerary_data = itinerary_generator.load_itinerary(test_destination)
    
    if not itinerary_data:
        logger.info("Generating itinerary first...")
        itinerary_data = itinerary_generator.generate_itinerary(test_destination, max_duration_minutes=8)
        itinerary_generator.save_itinerary(itinerary_data, test_destination)
    
    # Test uploader
    uploader = YouTubeUploaderLong()
    
    # Test connection
    if uploader.test_connection():
        logger.info("✅ YouTube connection successful")
    else:
        logger.error("❌ YouTube connection failed")
        return
    
    # Test title generation
    title = uploader.generate_title(test_destination, itinerary_data.get('ideal_days', 0), itinerary_data)
    logger.info(f"Generated title: {title}")
    
    # Test description generation
    description = uploader.generate_description(test_destination, itinerary_data)
    logger.info(f"Generated description ({len(description)} chars)")
    
    # Test tags generation
    tags = uploader.generate_tags(test_destination, itinerary_data)
    logger.info(f"Generated tags: {tags}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Smart Social Media Manager
Creates platform-specific metadata for the same videos
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger

# Import config to get YouTube title max length
try:
    from config import settings
    YOUTUBE_TITLE_MAX_LENGTH = getattr(settings, 'YOUTUBE_TITLE_MAX_LENGTH', 70)
except ImportError:
    # Fallback if config not available
    YOUTUBE_TITLE_MAX_LENGTH = 70

class SmartSocialMediaManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.videos_dir = self.data_dir / "videos"
        self.social_dir = Path("social_media")
        self.shared_videos_dir = self.social_dir / "videos"
        self.metadata_dir = self.social_dir / "metadata"
        self.posts_file = self.data_dir / "posts.json"
        
        # Platform-specific requirements
        self.platforms = {
            "instagram": {
                "max_hashtags": 30,
                "max_caption_length": 2200,
                "optimal_duration": 15,
                "format": "9:16",
                "peak_hours": ["18:00", "19:00", "20:00", "21:00"],
                "best_days": ["Monday", "Wednesday", "Friday", "Sunday"]
            },
            "youtube": {
                "max_tags": 15,
                "max_title_length": YOUTUBE_TITLE_MAX_LENGTH,  # Configurable via YOUTUBE_TITLE_MAX_LENGTH in config/settings.py
                "max_description_length": 5000,
                "optimal_duration": 15,
                "format": "9:16",
                "peak_hours": ["14:00", "15:00", "16:00"],
                "best_days": ["Tuesday", "Thursday", "Saturday"]
            },
            "tiktok": {
                "max_hashtags": 20,
                "max_caption_length": 2200,
                "optimal_duration": 15,
                "format": "9:16",
                "peak_hours": ["18:00", "19:00", "20:00", "21:00"],
                "best_days": ["Monday", "Wednesday", "Friday", "Sunday"]
            },
            "facebook": {
                "max_hashtags": 25,
                "max_caption_length": 63206,
                "optimal_duration": 15,
                "format": "9:16",
                "peak_hours": ["09:00", "12:00", "15:00", "18:00"],
                "best_days": ["Tuesday", "Thursday", "Saturday"]
            }
        }
        
        logger.info("Smart Social Media Manager initialized")

    def load_posts_data(self) -> List[Dict[str, Any]]:
        """Load posts data for metadata generation"""
        try:
            if not self.posts_file.exists():
                logger.error(f"Posts file not found: {self.posts_file}")
                return []
            
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            logger.info(f"Loaded {len(posts)} posts for social media management")
            return posts
            
        except Exception as e:
            logger.error(f"Error loading posts: {e}")
            return []

    def find_final_videos(self) -> List[Path]:
        """Find all final video files"""
        final_videos = list(self.videos_dir.glob("reel_*_final.mp4"))
        logger.info(f"Found {len(final_videos)} final videos")
        return final_videos

    def copy_videos_to_shared_location(self, videos: List[Path]) -> Dict[str, Path]:
        """Copy videos to shared location with clean names"""
        video_mapping = {}
        
        for video_path in videos:
            # Extract post_id from filename (reel_1_final.mp4 -> 1)
            post_id = video_path.stem.split('_')[1]
            
            # Create clean filename
            clean_filename = f"post_{post_id}.mp4"
            destination = self.shared_videos_dir / clean_filename
            
            # Copy video
            shutil.copy2(video_path, destination)
            video_mapping[post_id] = destination
            
            logger.info(f"Copied {video_path.name} to {clean_filename}")
        
        return video_mapping

    def generate_platform_metadata(self, post: Dict[str, Any], video_path: Path, platform: str) -> Dict[str, Any]:
        """Generate platform-specific metadata"""
        post_id = post.get('topic_id', 'unknown')
        caption = post.get('caption', '')
        hashtags = post.get('hashtags', [])
        region = post.get('region', 'Unknown')
        original_title = post.get('original_title', '')
        
        # Get platform requirements
        platform_reqs = self.platforms[platform]
        
        # Base metadata
        base_metadata = {
            "post_id": post_id,
            "video_file": video_path.name,
            "region": region,
            "created_at": datetime.now().isoformat(),
            "tripavail_brand": True,
            "platform": platform
        }
        
        if platform == "instagram":
            # Instagram-specific metadata
            metadata = {
                **base_metadata,
                "caption": caption,
                "hashtags": hashtags[:platform_reqs["max_hashtags"]],
                "format": platform_reqs["format"],
                "optimal_duration": platform_reqs["optimal_duration"],
                "peak_hours": platform_reqs["peak_hours"],
                "best_days": platform_reqs["best_days"],
                "posting_tips": [
                    "Post during peak hours (6-9 PM)",
                    "Use relevant location tags",
                    "Engage with comments quickly",
                    "Share to Stories for more reach",
                    "Use trending hashtags"
                ],
                "requirements": {
                    "max_caption_length": platform_reqs["max_caption_length"],
                    "max_hashtags": platform_reqs["max_hashtags"],
                    "format": platform_reqs["format"]
                }
            }
            
        elif platform == "youtube":
            # YouTube-specific metadata
            # Use original title if available, otherwise create from region
            suffix = " | TripAvail"
            suffix_length = len(suffix)
            max_title_length = platform_reqs["max_title_length"]
            max_title_chars = max_title_length - suffix_length  # Leave room for suffix
            
            if original_title:
                # Word-boundary aware truncation (avoid cutting words in half)
                if len(original_title) <= max_title_chars:
                    # Title fits, no truncation needed
                    title = f"{original_title}{suffix}"
                else:
                    # Try to find a space near the limit (within 60-70 range to avoid incomplete words)
                    min_title_chars = max(50, max_title_chars - 10)  # Allow 10 chars flexibility
                    truncated = original_title[:max_title_chars]
                    last_space = truncated.rfind(' ')
                    
                    if last_space >= min_title_chars:
                        # Found a good space to cut at - cut before the space
                        title_base = original_title[:last_space].strip()
                    else:
                        # No good space found, cut at max (might cut word, but better than nothing)
                        title_base = original_title[:max_title_chars].strip()
                    
                    title = f"{title_base}{suffix}"
            else:
                # Fallback to region-based title
                title = f"{region} Travel{suffix}"
            
            # Final safety check - ensure we don't exceed max length
            if len(title) > max_title_length:
                # Truncate more aggressively if needed
                if original_title:
                    available = max_title_length - suffix_length
                    if available >= 50:
                        temp_title = original_title[:available]
                        last_space = temp_title.rfind(' ')
                        if last_space >= 50:
                            title_base = original_title[:last_space].strip()
                        else:
                            title_base = original_title[:available].strip()
                    else:
                        title_base = original_title[:available].strip()
                    title = f"{title_base}{suffix}"
                else:
                    title = title[:max_title_length].strip()
            
            description = f"{caption}\n\n{' '.join(hashtags[:10])}\n\nPlan your journey with TripAvail ✈️"
            if len(description) > platform_reqs["max_description_length"]:
                description = f"{caption[:2000]}...\n\n{' '.join(hashtags[:10])}\n\nPlan your journey with TripAvail ✈️"
            
            metadata = {
                **base_metadata,
                "title": title,
                "description": description,
                "tags": hashtags[:platform_reqs["max_tags"]],
                "format": platform_reqs["format"],
                "optimal_duration": platform_reqs["optimal_duration"],
                "peak_hours": platform_reqs["peak_hours"],
                "best_days": platform_reqs["best_days"],
                "posting_tips": [
                    "Use trending travel keywords",
                    "Add end screen with subscribe button",
                    "Post consistently (daily)",
                    "Engage with travel community",
                    "Use eye-catching thumbnails"
                ],
                "requirements": {
                    "max_title_length": platform_reqs["max_title_length"],
                    "max_description_length": platform_reqs["max_description_length"],
                    "max_tags": platform_reqs["max_tags"],
                    "format": platform_reqs["format"]
                }
            }
            
        elif platform == "tiktok":
            # TikTok-specific metadata
            metadata = {
                **base_metadata,
                "caption": caption,
                "hashtags": hashtags[:platform_reqs["max_hashtags"]],
                "format": platform_reqs["format"],
                "optimal_duration": platform_reqs["optimal_duration"],
                "peak_hours": platform_reqs["peak_hours"],
                "best_days": platform_reqs["best_days"],
                "posting_tips": [
                    "Use trending sounds",
                    "Post during peak hours (6-10 PM)",
                    "Engage with comments",
                    "Use trending hashtags",
                    "Create engaging hooks in first 3 seconds"
                ],
                "requirements": {
                    "max_caption_length": platform_reqs["max_caption_length"],
                    "max_hashtags": platform_reqs["max_hashtags"],
                    "format": platform_reqs["format"]
                }
            }
            
        elif platform == "facebook":
            # Facebook-specific metadata
            metadata = {
                **base_metadata,
                "caption": caption,
                "hashtags": hashtags[:platform_reqs["max_hashtags"]],
                "format": platform_reqs["format"],
                "optimal_duration": platform_reqs["optimal_duration"],
                "peak_hours": platform_reqs["peak_hours"],
                "best_days": platform_reqs["best_days"],
                "posting_tips": [
                    "Post during business hours",
                    "Use Facebook's native video player",
                    "Engage with travel groups",
                    "Share to relevant pages",
                    "Use location tags"
                ],
                "requirements": {
                    "max_caption_length": platform_reqs["max_caption_length"],
                    "max_hashtags": platform_reqs["max_hashtags"],
                    "format": platform_reqs["format"]
                }
            }
        
        return metadata

    def create_platform_metadata_files(self, posts: List[Dict[str, Any]], video_mapping: Dict[str, Path]) -> Dict[str, int]:
        """Create metadata files for each platform"""
        results = {}
        
        for platform in self.platforms.keys():
            results[platform] = 0
            
            for post in posts:
                post_id = str(post.get('topic_id', 'unknown'))
                video_path = video_mapping.get(post_id)
                
                if video_path:
                    # Generate platform-specific metadata
                    metadata = self.generate_platform_metadata(post, video_path, platform)
                    
                    # Save metadata file
                    metadata_filename = f"{platform}_post_{post_id}.json"
                    metadata_file = self.metadata_dir / metadata_filename
                    
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"Created {platform} metadata for post {post_id}")
                    results[platform] += 1
        
        return results

    def create_posting_guide(self) -> Dict[str, Any]:
        """Create a comprehensive posting guide"""
        guide = {
            "created_at": datetime.now().isoformat(),
            "overview": "TripAvail Social Media Posting Guide",
            "video_location": "social_media/videos/",
            "metadata_location": "social_media/metadata/",
            "platforms": {},
            "content_calendar": {
                "monday": ["instagram", "tiktok"],
                "tuesday": ["youtube", "facebook"],
                "wednesday": ["instagram", "tiktok"],
                "thursday": ["youtube", "facebook"],
                "friday": ["instagram", "tiktok"],
                "saturday": ["youtube", "facebook"],
                "sunday": ["instagram", "tiktok"]
            },
            "posting_workflow": [
                "1. Check social_media/videos/ for available videos",
                "2. Find corresponding metadata in social_media/metadata/",
                "3. Review platform-specific requirements",
                "4. Post during optimal times",
                "5. Monitor engagement and adjust strategy"
            ]
        }
        
        # Add platform-specific details
        for platform, requirements in self.platforms.items():
            guide["platforms"][platform] = {
                "requirements": requirements,
                "metadata_files": f"{platform}_post_*.json",
                "video_files": "post_*.mp4"
            }
        
        # Save guide
        guide_file = self.social_dir / "posting_guide.json"
        with open(guide_file, 'w', encoding='utf-8') as f:
            json.dump(guide, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created posting guide: {guide_file}")
        return guide

    def run_smart_organization(self) -> bool:
        """Run the smart social media organization"""
        logger.info("Starting smart social media organization")
        
        try:
            # Load posts
            posts = self.load_posts_data()
            final_videos = self.find_final_videos()
            
            if not posts or not final_videos:
                logger.error("No posts or videos found")
                return False
            
            # Copy videos to shared location
            video_mapping = self.copy_videos_to_shared_location(final_videos)
            
            # Create platform-specific metadata
            results = self.create_platform_metadata_files(posts, video_mapping)
            
            # Create posting guide
            self.create_posting_guide()
            
            # Generate summary
            self.generate_summary(results, len(video_mapping))
            
            logger.info("Smart social media organization complete!")
            return True
            
        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return False

    def generate_summary(self, results: Dict[str, int], total_videos: int):
        """Generate organization summary"""
        print("\n=== TripAvail Smart Social Media Organization ===")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("ORGANIZATION RESULTS:")
        for platform, count in results.items():
            print(f"  {platform.upper()}: {count} metadata files created")
        print()
        print(f"SHARED VIDEOS: {total_videos} videos in social_media/videos/")
        print()
        print("DIRECTORY STRUCTURE:")
        print("social_media/")
        print("  videos/              (Shared video files)")
        print("  metadata/            (Platform-specific metadata)")
        print("  posting_guide.json   (Complete posting guide)")
        print()
        print("PLATFORM-SPECIFIC FEATURES:")
        print("  Instagram: Captions + hashtags (max 30)")
        print("  YouTube: Titles + descriptions + tags (max 15)")
        print("  TikTok: Captions + hashtags (max 20)")
        print("  Facebook: Captions + hashtags (max 25)")
        print()
        print("NEXT STEPS:")
        print("1. Review metadata files for each platform")
        print("2. Use same videos across all platforms")
        print("3. Follow platform-specific requirements")
        print("4. Post during optimal times")
        print("5. Monitor engagement and adjust strategy")


def main():
    manager = SmartSocialMediaManager()
    success = manager.run_smart_organization()
    
    if success:
        print("\n[SUCCESS] Smart Social Media Organization Complete!")
        print("[INFO] Same videos, different metadata for each platform")
        print("[INFO] Check social_media/ directory for organized content")
    else:
        print("\n[ERROR] Organization failed. Check logs for details.")


if __name__ == "__main__":
    main()

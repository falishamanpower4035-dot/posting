#!/usr/bin/env python3
"""
Social Media Organization Script
Organizes videos into platform-specific directories and creates metadata files
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger

class SocialMediaOrganizer:
    def __init__(self):
        self.data_dir = Path("data")
        self.videos_dir = self.data_dir / "videos"
        self.social_dir = Path("social_media")
        self.posts_file = self.data_dir / "posts.json"
        
        # Platform directories
        self.platforms = {
            "instagram": self.social_dir / "instagram" / "reels",
            "youtube": self.social_dir / "youtube" / "shorts", 
            "tiktok": self.social_dir / "tiktok" / "videos",
            "facebook": self.social_dir / "facebook" / "reels"
        }
        
        logger.info("Social Media Organizer initialized")

    def load_posts_data(self) -> List[Dict[str, Any]]:
        """Load posts data for metadata generation"""
        try:
            if not self.posts_file.exists():
                logger.error(f"Posts file not found: {self.posts_file}")
                return []
            
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            logger.info(f"Loaded {len(posts)} posts for organization")
            return posts
            
        except Exception as e:
            logger.error(f"Error loading posts: {e}")
            return []

    def find_final_videos(self) -> List[Path]:
        """Find all final video files"""
        final_videos = list(self.videos_dir.glob("reel_*_final.mp4"))
        logger.info(f"Found {len(final_videos)} final videos")
        return final_videos

    def generate_platform_metadata(self, post: Dict[str, Any], video_path: Path) -> Dict[str, Dict[str, Any]]:
        """Generate platform-specific metadata"""
        post_id = post.get('topic_id', 'unknown')
        caption = post.get('caption', '')
        hashtags = post.get('hashtags', [])
        region = post.get('region', 'Unknown')
        
        # Base metadata
        base_metadata = {
            "post_id": post_id,
            "video_file": video_path.name,
            "region": region,
            "created_at": datetime.now().isoformat(),
            "tripavail_brand": True
        }
        
        # Platform-specific metadata
        metadata = {
            "instagram": {
                **base_metadata,
                "caption": caption,
                "hashtags": hashtags[:30],  # Instagram limit
                "format": "9:16",
                "max_duration": 90,
                "optimal_duration": 15,
                "posting_tips": [
                    "Post during peak hours (6-9 PM)",
                    "Use relevant location tags",
                    "Engage with comments quickly",
                    "Share to Stories for more reach"
                ]
            },
            "youtube": {
                **base_metadata,
                "title": f"Travel Update: {region} | TripAvail",
                "description": f"{caption}\n\n{' '.join(hashtags[:10])}\n\nPlan your journey with TripAvail ✈️",
                "tags": hashtags[:15],  # YouTube limit
                "format": "9:16",
                "max_duration": 60,
                "optimal_duration": 15,
                "posting_tips": [
                    "Use trending travel keywords",
                    "Add end screen with subscribe button",
                    "Post consistently (daily)",
                    "Engage with travel community"
                ]
            },
            "tiktok": {
                **base_metadata,
                "caption": caption,
                "hashtags": hashtags[:20],  # TikTok limit
                "format": "9:16",
                "max_duration": 60,
                "optimal_duration": 15,
                "posting_tips": [
                    "Use trending sounds",
                    "Post during peak hours (6-10 PM)",
                    "Engage with comments",
                    "Use trending hashtags"
                ]
            },
            "facebook": {
                **base_metadata,
                "caption": caption,
                "hashtags": hashtags[:25],  # Facebook limit
                "format": "9:16",
                "max_duration": 240,
                "optimal_duration": 15,
                "posting_tips": [
                    "Post during business hours",
                    "Use Facebook's native video player",
                    "Engage with travel groups",
                    "Share to relevant pages"
                ]
            }
        }
        
        return metadata

    def organize_video_for_platform(self, video_path: Path, post: Dict[str, Any], platform: str) -> bool:
        """Organize a single video for a specific platform"""
        try:
            platform_dir = self.platforms[platform]
            platform_dir.mkdir(parents=True, exist_ok=True)
            
            # Create platform-specific filename
            post_id = post.get('topic_id', 'unknown')
            new_filename = f"{platform}_{post_id}_{video_path.stem}.mp4"
            destination = platform_dir / new_filename
            
            # Copy video file
            shutil.copy2(video_path, destination)
            logger.info(f"Copied {video_path.name} to {platform}/{new_filename}")
            
            # Generate and save metadata
            metadata = self.generate_platform_metadata(post, destination)
            metadata_file = destination.with_suffix('.json')
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata[platform], f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created metadata file: {metadata_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error organizing {video_path.name} for {platform}: {e}")
            return False

    def organize_all_videos(self) -> Dict[str, int]:
        """Organize all videos for all platforms"""
        posts = self.load_posts_data()
        final_videos = self.find_final_videos()
        
        if not posts or not final_videos:
            logger.error("No posts or videos found to organize")
            return {}
        
        # Create a mapping of post_id to post data
        posts_by_id = {str(post.get('topic_id')): post for post in posts}
        
        results = {}
        
        for platform in self.platforms.keys():
            results[platform] = 0
            
            for video_path in final_videos:
                # Extract post_id from filename (reel_1_final.mp4 -> 1)
                post_id = video_path.stem.split('_')[1]
                post = posts_by_id.get(post_id)
                
                if post:
                    if self.organize_video_for_platform(video_path, post, platform):
                        results[platform] += 1
                else:
                    logger.warning(f"No post data found for post_id: {post_id}")
        
        return results

    def create_posting_schedule(self) -> Dict[str, Any]:
        """Create a posting schedule for all platforms"""
        schedule = {
            "created_at": datetime.now().isoformat(),
            "platforms": {
                "instagram": {
                    "optimal_times": ["18:00", "19:00", "20:00", "21:00"],
                    "frequency": "daily",
                    "best_days": ["Monday", "Wednesday", "Friday", "Sunday"]
                },
                "youtube": {
                    "optimal_times": ["14:00", "15:00", "16:00"],
                    "frequency": "daily", 
                    "best_days": ["Tuesday", "Thursday", "Saturday"]
                },
                "tiktok": {
                    "optimal_times": ["18:00", "19:00", "20:00", "21:00"],
                    "frequency": "daily",
                    "best_days": ["Monday", "Wednesday", "Friday", "Sunday"]
                },
                "facebook": {
                    "optimal_times": ["09:00", "12:00", "15:00", "18:00"],
                    "frequency": "daily",
                    "best_days": ["Tuesday", "Thursday", "Saturday"]
                }
            },
            "content_calendar": {
                "monday": ["instagram", "tiktok"],
                "tuesday": ["youtube", "facebook"],
                "wednesday": ["instagram", "tiktok"],
                "thursday": ["youtube", "facebook"],
                "friday": ["instagram", "tiktok"],
                "saturday": ["youtube", "facebook"],
                "sunday": ["instagram", "tiktok"]
            }
        }
        
        # Save schedule
        schedule_file = self.social_dir / "posting_schedule.json"
        with open(schedule_file, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created posting schedule: {schedule_file}")
        return schedule

    def generate_summary_report(self, results: Dict[str, int]) -> str:
        """Generate a summary report of the organization"""
        total_videos = sum(results.values())
        
        report = f"""
=== TripAvail Social Media Organization Report ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ORGANIZATION RESULTS:
"""
        
        for platform, count in results.items():
            report += f"  {platform.upper()}: {count} videos organized\n"
        
        report += f"""
DIRECTORY STRUCTURE:
  social_media/
    ├── instagram/reels/     (Instagram Reels)
    ├── youtube/shorts/      (YouTube Shorts)
    ├── tiktok/videos/       (TikTok Videos)
    └── facebook/reels/      (Facebook Reels)

METADATA FILES:
  Each video has a corresponding .json file with:
  - Platform-specific captions and hashtags
  - Posting tips and optimal timing
  - Format specifications and limits

POSTING SCHEDULE:
  Check social_media/posting_schedule.json for:
  - Optimal posting times per platform
  - Content calendar recommendations
  - Frequency guidelines

NEXT STEPS:
  1. Review metadata files for each platform
  2. Schedule posts according to optimal times
  3. Monitor engagement and adjust strategy
  4. Use platform-specific tips for better reach

Total Videos Organized: {total_videos}
"""
        
        return report

    def run_organization(self) -> bool:
        """Run the complete organization process"""
        logger.info("Starting social media organization")
        
        try:
            # Organize videos
            results = self.organize_all_videos()
            
            # Create posting schedule
            self.create_posting_schedule()
            
            # Generate report
            report = self.generate_summary_report(results)
            print(report)
            
            # Save report
            report_file = self.social_dir / "organization_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Organization complete! Report saved to: {report_file}")
            return True
            
        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return False


def main():
    organizer = SocialMediaOrganizer()
    success = organizer.run_organization()
    
    if success:
        print("\n[SUCCESS] Social Media Organization Complete!")
        print("[INFO] Check the 'social_media' directory for organized content")
        print("[INFO] Review metadata files for posting guidelines")
    else:
        print("\n[ERROR] Organization failed. Check logs for details.")


if __name__ == "__main__":
    main()

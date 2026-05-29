#!/usr/bin/env python3
"""
Simple Social Media Summary
Shows organized content without Unicode issues
"""

from pathlib import Path

def show_summary():
    social_dir = Path("social_media")
    
    print("=== TripAvail Social Media Organization Summary ===")
    print()
    
    platforms = ["instagram", "youtube", "tiktok", "facebook"]
    
    for platform in platforms:
        platform_dir = social_dir / platform
        if platform == "instagram":
            content_dir = platform_dir / "reels"
        elif platform == "youtube":
            content_dir = platform_dir / "shorts"
        elif platform == "tiktok":
            content_dir = platform_dir / "videos"
        elif platform == "facebook":
            content_dir = platform_dir / "reels"
        
        if content_dir.exists():
            videos = list(content_dir.glob("*.mp4"))
            metadata = list(content_dir.glob("*.json"))
            
            print(f"{platform.upper()}:")
            print(f"  Videos: {len(videos)}")
            print(f"  Metadata: {len(metadata)}")
            print(f"  Location: {content_dir}")
            print()
    
    print("DIRECTORY STRUCTURE:")
    print("social_media/")
    print("  instagram/reels/     (Instagram Reels)")
    print("  youtube/shorts/      (YouTube Shorts)")
    print("  tiktok/videos/       (TikTok Videos)")
    print("  facebook/reels/      (Facebook Reels)")
    print()
    print("Each video has a corresponding .json file with:")
    print("- Platform-specific captions and hashtags")
    print("- Posting tips and optimal timing")
    print("- Format specifications and limits")
    print()
    print("Check social_media/posting_schedule.json for:")
    print("- Optimal posting times per platform")
    print("- Content calendar recommendations")
    print("- Frequency guidelines")

if __name__ == "__main__":
    show_summary()

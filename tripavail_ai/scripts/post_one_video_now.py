#!/usr/bin/env python3
"""
Quick test: Post one video to Facebook and YouTube right now
"""

import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging
from core.utils import logging_setup  # noqa
from loguru import logger

from core.social.platforms.facebook_poster import FacebookPoster
from core.social.platforms.youtube_uploader import YouTubeUploader

DATA = Path("data")
VIDEOS = DATA / "videos"

def main():
    logger.info("=== Quick Video Post Test ===")
    
    # Load posts
    posts_file = DATA / "posts.json"
    if not posts_file.exists():
        logger.error("No posts.json found. Run the pipeline first.")
        return
    
    posts = json.loads(posts_file.read_text(encoding="utf-8")).get("posts", [])
    if not posts:
        logger.error("No posts available.")
        return
    
    # Find a post with score >= 7
    good_posts = [p for p in posts if int(p.get('score', 0)) >= 7]
    if not good_posts:
        logger.warning("No posts with score >= 7. Using the first post instead.")
        post = posts[0]
    else:
        post = good_posts[0]
    
    pid = str(post.get("topic_id"))
    title = post.get('original_title', '')
    caption = post.get('caption', '')
    hashtags = post.get('hashtags', [])
    
    # Find the final video
    final_video = VIDEOS / f"reel_{pid}_final.mp4"
    if not final_video.exists():
        logger.error(f"Video not found: {final_video}")
        logger.info("Available videos:")
        for v in VIDEOS.glob("*.mp4"):
            logger.info(f"  - {v.name}")
        return
    
    logger.info(f"Posting video for post {pid}: {title}")
    logger.info(f"Video: {final_video}")
    logger.info(f"Caption: {caption[:100]}...")
    
    # Post to Facebook
    logger.info("\n--- Posting to Facebook ---")
    try:
        fb = FacebookPoster()
        # Test connection first
        page_info = fb.get_page_info()
        if page_info:
            logger.info(f"Connected to Facebook page: {page_info.get('name', 'Unknown')}")
            success = fb.post_video(final_video, caption, hashtags)
            if success:
                logger.info("✅ Facebook post successful!")
            else:
                logger.error("❌ Facebook post failed - check video format (must be H.264, max 1GB)")
        else:
            logger.error("❌ Facebook connection failed - token may be expired")
            logger.info("To refresh token, run: python create_long_lived_token.py")
    except Exception as e:
        logger.error(f"Facebook error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Post to YouTube
    logger.info("\n--- Posting to YouTube ---")
    try:
        yt = YouTubeUploader()
        yt.authenticate()
        
        tags = [t.replace('#','') for t in hashtags[:10]] + ['TripAvail','Travel','Shorts']
        # Use truncate_title to ensure max 60 characters (will be truncated in upload_video too)
        yt_title = yt.truncate_title(title, " | TripAvail")
        yt_description = f"{caption}\n\n#Shorts\n\n" + " ".join(hashtags[:10])
        
        video_id = yt.upload_video(
            final_video,
            title=yt_title,
            description=yt_description,
            tags=tags
        )
        if video_id:
            logger.info(f"✅ YouTube upload successful! Video ID: {video_id}")
            logger.info(f"   Watch at: https://youtube.com/shorts/{video_id}")
        else:
            logger.error("❌ YouTube upload failed")
    except Exception as e:
        logger.error(f"YouTube error: {e}")
    
    logger.info("\n=== Test Complete ===")

if __name__ == "__main__":
    main()


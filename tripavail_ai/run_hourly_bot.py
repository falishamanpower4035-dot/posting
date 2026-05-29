#!/usr/bin/env python3
"""
Hourly bot: wait 1 hour, fetch news, generate posts with score >= 7,
produce Shorts, validate outputs, and auto-post to Facebook and YouTube.
Keeps running until manually stopped. Uses new clean folder structure.
"""

import time
import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

# Now import logger
import logging
from loguru import logger as loguru_logger
# Use loguru logger instead of stdlib
logger = loguru_logger

try:
    from core.pipeline.orchestrator.lock import FileLock
    from core.content.post_manager import PostManager
    from core.content.auto_deletion import AutoDeletionManager
    from core.news.fetcher.fetch_news import NewsFetcher
    from core.news.editor import TourismEditor
    from production_pipeline import ProductionPipeline
    from core.social.platforms.facebook_poster import FacebookPoster
    from core.social.platforms.youtube_uploader import YouTubeUploader
    from core.social.platforms.instagram_poster import InstagramPoster
    from config import settings
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please activate the virtual environment first: venv\\Scripts\\activate")
    sys.exit(1)


DATA = Path("data")
POSTS_DIR = DATA / "posts"


def fetch_and_process_news():
    """Fetch fresh news and process with AI tourism editor"""
    logger.info("=== Fetching News ===")
    try:
        # Fetch news
        news_fetcher = NewsFetcher()
        news_fetcher.run_fetch_cycle()
        
        # Process with tourism editor
        tourism_editor = TourismEditor()
        tourism_editor.run_analysis()
        
        logger.info("News fetching and processing complete")
        return True
    except Exception as e:
        logger.error(f"News fetch/process failed: {e}")
        return False


def generate_posts_from_news(max_posts: int = 5) -> list:
    """
    Generate posts from processed news using production pipeline
    
    Args:
        max_posts: Maximum number of posts to generate
    
    Returns:
        List of successfully generated post IDs
    """
    logger.info(f"=== Generating Posts (max: {max_posts}) ===")
    
    try:
        # Load processed news
        processed_news_file = DATA / "processed_news.json"
        if not processed_news_file.exists():
            logger.error("No processed news found")
            return []
        
        with open(processed_news_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        topics = data.get('top_tourism_stories', [])
        
        # Filter by score >= 7
        quality_topics = [t for t in topics if t.get('score', 0) >= 7]
        logger.info(f"Found {len(quality_topics)} quality topics (score >= 7)")
        
        if not quality_topics:
            logger.warning("No quality topics found")
            return []
        
        # Initialize production pipeline
        pipeline = ProductionPipeline()
        post_manager = PostManager()
        
        # Get next post ID
        existing_posts = post_manager.get_all_posts()
        next_id = len(existing_posts) + 1
        
        successful_posts = []
        
        # Generate posts
        for i, topic in enumerate(quality_topics[:max_posts], start=next_id):
            post_id = f"{i:03d}"
            
            # Check if already exists
            if post_id in existing_posts:
                logger.info(f"Post {post_id} already exists, skipping")
                continue
            
            logger.info(f"\n--- Generating Post {post_id} ---")
            success = pipeline.process_single_post(topic, i)
            
            if success:
                successful_posts.append(post_id)
                logger.info(f"✅ Post {post_id} generated successfully")
            else:
                logger.error(f"❌ Post {post_id} generation failed")
        
        logger.info(f"Generated {len(successful_posts)} posts: {successful_posts}")
        return successful_posts
    
    except Exception as e:
        logger.error(f"Post generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def post_to_platforms(post_id: str) -> bool:
    """
    Post a video to Facebook and YouTube
    
    Args:
        post_id: Post identifier (e.g., "001")
    
    Returns:
        True if posted to at least one platform, False otherwise
    """
    logger.info(f"=== Posting {post_id} to Platforms ===")
    
    try:
        post_manager = PostManager()
        
        # Check if already posted
        if post_manager.is_posted(post_id):
            logger.info(f"Post {post_id} already posted, skipping")
            return True
        
        # Get metadata and video
        metadata = post_manager.get_metadata(post_id)
        if not metadata:
            logger.error(f"No metadata found for post {post_id}")
            return False
        
        final_video = post_manager.get_final_video_path(post_id)
        # Prefer platform-optimized renditions if available
        video_dir = post_manager.get_video_dir(post_id)
        square_video = video_dir / "final_1x1.mp4"
        landscape_video = video_dir / "final_16x9.mp4"
        if not final_video.exists():
            logger.error(f"No final video found for post {post_id}")
            return False
        
        title = metadata.get('original_title', '')[:70]
        caption = metadata.get('caption', '')
        hashtags = metadata.get('hashtags', [])
        
        posted_anywhere = False
        
        # Post to Facebook Reels (9:16 vertical video)
        if not post_manager.is_posted(post_id, "facebook"):
            logger.info("🎬 Posting to Facebook Reels...")
            try:
                fb = FacebookPoster()
                # Always use final_video (9:16 aspect ratio) for Reels
                fb_video = final_video
                if fb_video.exists():
                    success = fb.post_video(fb_video, caption, hashtags)
                    if success:
                        post_manager.mark_as_posted(post_id, "facebook")
                        logger.info("✅ Facebook Reel posted successfully!")
                        posted_anywhere = True
                    else:
                        logger.error("❌ Facebook Reel posting failed")
                else:
                    logger.error(f"❌ Video not found: {fb_video}")
            except Exception as e:
                logger.error(f"Facebook Reel error: {e}")
        else:
            logger.info("Already posted to Facebook")
        
        # Post to YouTube
        if not post_manager.is_posted(post_id, "youtube"):
            logger.info("Posting to YouTube...")
            try:
                yt = YouTubeUploader()
                yt.authenticate()
                
                tags = [t.replace('#','') for t in hashtags[:10]] + ['TripAvail','Travel','Shorts']
                # Use truncate_title to ensure max 60 characters (will be truncated in upload_video too)
                yt_title = yt.truncate_title(title, " | TripAvail")
                yt_description = f"{caption}\n\n#Shorts\n\n" + " ".join(hashtags[:10])
                
                # Shorts prefer 9:16
                yt_video = final_video
                
                # Get thumbnail path if available (9:16 format)
                thumbnail_path = None
                if 'thumbnails' in metadata and 'vertical' in metadata['thumbnails']:
                    thumbnail_path = Path(metadata['thumbnails']['vertical'])
                
                video_id = yt.upload_video(
                    yt_video,
                    title=yt_title,
                    description=yt_description,
                    tags=tags,
                    thumbnail_path=thumbnail_path
                )
                
                if video_id:
                    post_url = f"https://youtube.com/shorts/{video_id}"
                    post_manager.mark_as_posted(post_id, "youtube", post_url)
                    logger.info(f"✅ YouTube upload successful: {post_url}")
                    posted_anywhere = True
                else:
                    logger.error("❌ YouTube upload failed")
            except Exception as e:
                logger.error(f"YouTube error: {e}")
        else:
            logger.info("Already posted to YouTube")

        # Post to Instagram (Reels) - optional, may require Facebook Graph token + IG Business account
        if not post_manager.is_posted(post_id, "instagram"):
            logger.info("Posting to Instagram...")
            try:
                ig = InstagramPoster()
                ig_video = final_video
                # Build caption limiting hashtags to Instagram limits
                ig_caption = caption
                if hashtags:
                    ig_caption = f"{ig_caption}\n\n{' '.join(hashtags[:30])}"

                success = ig.post_reel(ig_video, ig_caption)
                if success:
                    post_manager.mark_as_posted(post_id, "instagram")
                    logger.info("✅ Instagram Reel posted successfully!")
                    posted_anywhere = True
                else:
                    logger.error("❌ Instagram posting failed")
            except Exception as e:
                logger.error(f"Instagram error: {e}")
        else:
            logger.info("Already posted to Instagram")
        
        return posted_anywhere
    
    except Exception as e:
        logger.error(f"Posting failed for {post_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def run_cycle():
    """Run one complete cycle: fetch news, generate posts, and post"""
    logger.info("\n" + "="*60)
    logger.info("STARTING NEW CYCLE")
    logger.info("="*60)
    
    # Step 1: Fetch and process news
    if not fetch_and_process_news():
        logger.error("News fetch/process failed, skipping this cycle")
        return
    
    # Step 2: Generate posts from quality topics
    new_posts = generate_posts_from_news(max_posts=3)
    
    if not new_posts:
        logger.info("No new posts generated this cycle")
        return
    
    # Step 3: Post to platforms
    for post_id in new_posts:
        post_to_platforms(post_id)
        time.sleep(5)  # Small delay between posts
    
    logger.info("\n" + "="*60)
    logger.info("CYCLE COMPLETE")
    logger.info("="*60)


def main():
    """Main bot loop"""
    lock = FileLock(Path(".hourly_bot.lock"), timeout_sec=30)
    
    if not lock.acquire():
        logger.error("Bot already running. Exiting.")
        return
    
    try:
        logger.info("="*60)
        logger.info("HOURLY BOT STARTED (New Clean Structure)")
        logger.info("="*60)
        logger.info("- Fetches news every hour")
        logger.info("- Generates posts with score >= 7")
        logger.info("- Uses isolated post directories")
        logger.info("- Posts to Facebook & YouTube")
        logger.info("- Press Ctrl+C to stop")
        logger.info("="*60)
        
        # Initial wait: Run immediately for testing (normally 1 hour)
        logger.info("\n🚀 Starting IMMEDIATELY for testing...")
        logger.info("(Normally waits 1 hour before first cycle)")
        # time.sleep(3600)  # Commented out for immediate testing
        
        # Initialize auto-deletion manager
        auto_deletion = AutoDeletionManager()
        
        # Main loop
        while True:
            try:
                # Run content generation cycle
                run_cycle()
                
                # Run auto-deletion cleanup (every cycle) - configurable hours
                policy_hours = getattr(settings, 'AUTO_DELETION_HOURS', 24)
                logger.info(f"=== Auto-Deletion Cleanup ({policy_hours}-Hour Policy) ===")
                deleted_count = auto_deletion.cleanup_old_posts()
                if deleted_count > 0:
                    logger.info(f"✅ Auto-deleted {deleted_count} posts ({policy_hours}+ hours old) - Server space freed!")
                else:
                    logger.info(f"No posts ready for auto-deletion ({policy_hours}-hour policy)")
                
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Sleep 1 hour between cycles
            logger.info("\nWaiting 1 hour until next cycle...")
            time.sleep(3600)
    
    except KeyboardInterrupt:
        logger.info("\n\nBot stopped by user (Ctrl+C)")
    finally:
        lock.release()
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Recovery Script - Finish Unfinished Posts
Fixes posts that failed during video generation and schedules them evenly
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import add_schedule
from production_pipeline import ProductionPipeline


def find_unfinished_posts() -> list:
    """Find posts with draft videos but no final videos"""
    pm = PostManager()
    posts_dir = Path("data/posts")
    
    unfinished = []
    
    for post_dir in sorted(posts_dir.glob("post_*")):
        if not post_dir.is_dir():
            continue
        
        post_id = post_dir.name.replace("post_", "")
        draft_video = post_dir / "video" / "draft.mp4"
        final_video = post_dir / "video" / "final.mp4"
        voiceover = post_dir / "audio" / "voiceover.mp3"
        metadata_file = post_dir / "metadata.json"
        
        # Check if post is unfinished
        if draft_video.exists() and not final_video.exists():
            if voiceover.exists() and metadata_file.exists():
                unfinished.append({
                    "post_id": post_id,
                    "draft_path": draft_video,
                    "voiceover_path": voiceover,
                    "metadata_path": metadata_file
                })
                logger.info(f"Found unfinished post: {post_id}")
    
    return unfinished


def finish_post(post_id: str, pipeline: ProductionPipeline) -> bool:
    """Finish a single post by creating final video"""
    logger.info(f"🎬 Finishing post {post_id}...")
    
    try:
        pm = PostManager()
        post_dir = pm.get_post_directory(post_id)
        
        # Check assets
        draft_path = post_dir / "video" / "draft.mp4"
        voiceover_path = post_dir / "audio" / "voiceover.mp3"
        music_path = post_dir / "audio" / "background_music.mp3"
        final_path = post_dir / "video" / "final.mp4"
        metadata = pm.get_metadata(post_id)
        
        if not draft_path.exists():
            logger.error(f"Post {post_id}: No draft video found")
            return False
        
        if not voiceover_path.exists():
            logger.error(f"Post {post_id}: No voiceover found")
            return False
        
        # Get music from archive if not exists
        if not music_path.exists():
            logger.info(f"Post {post_id}: Getting music from archive...")
            from core.media.audio.music_archive_manager import MusicArchiveManager
            archive_manager = MusicArchiveManager()
            if archive_manager.get_available_count() > 0:
                archive_manager.use_archived_music(music_path)
            else:
                logger.warning(f"Post {post_id}: No archived music available")
        
        # Check if music file is valid (not empty or corrupted)
        use_music = False
        if music_path.exists():
            try:
                import subprocess
                result = subprocess.run(
                    ["ffprobe", "-v", "error", str(music_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and music_path.stat().st_size > 1000:
                    use_music = True
                else:
                    logger.warning(f"Post {post_id}: Music file is invalid or empty, using voiceover only")
            except Exception:
                logger.warning(f"Post {post_id}: Could not validate music file, using voiceover only")
        
        # Mix audio (draft + voiceover + music if valid, otherwise voiceover only)
        logger.info(f"Post {post_id}: Mixing audio ({'with music' if use_music else 'voiceover only'})...")
        
        if use_music:
            success = pipeline._mix_audio_with_music(
                draft_path, voiceover_path, music_path, final_path, post_id
            )
        else:
            # Simple mix: video + voiceover only (no music)
            import subprocess
            cmd = [
                "ffmpeg", "-y",
                "-i", str(draft_path),
                "-i", str(voiceover_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(final_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            success = (result.returncode == 0 and final_path.exists())
            if not success:
                logger.error(f"Post {post_id}: FFmpeg failed: {result.stderr[-500:]}")
        
        if not success:
            logger.error(f"Post {post_id}: Audio mixing failed")
            return False
        
        # Apply text overlays if needed
        if final_path.exists() and metadata:
            logger.info(f"Post {post_id}: Applying text overlays...")
            try:
                overlaid_path = pipeline._apply_text_overlays_ffmpeg(
                    final_path, metadata, voiceover_path
                )
                if overlaid_path and overlaid_path != final_path and overlaid_path.exists():
                    import shutil
                    shutil.move(str(overlaid_path), str(final_path))
                    logger.info(f"Post {post_id}: Text overlays applied")
            except Exception as e:
                logger.warning(f"Post {post_id}: Text overlay failed (continuing): {e}")
        
        if final_path.exists():
            logger.info(f"✅ Post {post_id} finished successfully!")
            return True
        else:
            logger.error(f"Post {post_id}: Final video not created")
            return False
            
    except Exception as e:
        logger.error(f"Post {post_id}: Error finishing post: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def schedule_posts_evenly(post_ids: list, start_time: datetime, duration_minutes: int):
    """Schedule posts evenly over the duration"""
    if not post_ids:
        logger.warning("No posts to schedule")
        return
    
    total_posts = len(post_ids)
    interval_minutes = duration_minutes / total_posts
    
    logger.info(f"📅 Scheduling {total_posts} posts over {duration_minutes} minutes")
    logger.info(f"   Interval: {interval_minutes:.1f} minutes between posts")
    
    for i, post_id in enumerate(post_ids):
        schedule_time = start_time + timedelta(minutes=i * interval_minutes)
        logger.info(f"   Post {post_id}: {schedule_time.strftime('%H:%M:%S UTC')}")
        
        # Schedule post
        success = add_schedule(
            post_id=post_id,
            when_dt_utc=schedule_time,
            priority="normal",
            platforms=["instagram", "facebook", "youtube"]
        )
        
        if success:
            logger.info(f"   ✅ Scheduled post {post_id}")
        else:
            logger.warning(f"   ⚠️ Failed to schedule post {post_id} (may already be scheduled)")


def main():
    """Main recovery process"""
    logger.info("="*60)
    logger.info("RECOVERY SCRIPT - Finishing Unfinished Posts")
    logger.info("="*60)
    
    # Find unfinished posts
    unfinished = find_unfinished_posts()
    
    if not unfinished:
        logger.info("✅ No unfinished posts found!")
        return
    
    logger.info(f"\nFound {len(unfinished)} unfinished posts:")
    for post in unfinished:
        logger.info(f"  - Post {post['post_id']}")
    
    # Initialize pipeline
    pipeline = ProductionPipeline()
    
    # Finish each post
    finished_posts = []
    failed_posts = []
    
    logger.info(f"\n🎬 Finishing posts...")
    for post in unfinished:
        post_id = post["post_id"]
        success = finish_post(post_id, pipeline)
        
        if success:
            finished_posts.append(post_id)
        else:
            failed_posts.append(post_id)
    
    logger.info(f"\n✅ Finished: {len(finished_posts)} posts")
    if failed_posts:
        logger.warning(f"❌ Failed: {len(failed_posts)} posts: {failed_posts}")
    
    if not finished_posts:
        logger.error("No posts were finished successfully!")
        return
    
    # Schedule posts evenly over next 3h 40m (until next cycle)
    now = datetime.now(timezone.utc)
    next_cycle = now.replace(hour=11, minute=40, second=0, microsecond=0)
    
    # If next cycle is past, schedule for tomorrow
    if next_cycle <= now:
        next_cycle += timedelta(days=1)
    
    # Calculate duration until next cycle
    duration_minutes = int((next_cycle - now).total_seconds() / 60)
    
    logger.info(f"\n📅 Scheduling posts evenly until next cycle:")
    logger.info(f"   Current time: {now.strftime('%H:%M:%S UTC')}")
    logger.info(f"   Next cycle: {next_cycle.strftime('%H:%M:%S UTC')}")
    logger.info(f"   Duration: {duration_minutes} minutes")
    
    # Schedule finished posts
    schedule_posts_evenly(finished_posts, now, duration_minutes)
    
    logger.info(f"\n✅ Recovery complete!")
    logger.info(f"   Finished: {len(finished_posts)} posts")
    logger.info(f"   Scheduled: {len(finished_posts)} posts")
    logger.info(f"   Next cycle starts fresh at {next_cycle.strftime('%H:%M:%S UTC')}")


if __name__ == "__main__":
    main()


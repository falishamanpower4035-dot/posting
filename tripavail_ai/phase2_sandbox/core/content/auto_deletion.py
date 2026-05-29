"""
Auto-Deletion System for TripAvail AI
Automatically deletes posts after 24 hours of posting to save server space
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from loguru import logger
import shutil

# Load centralized settings
try:
    from config import settings
except Exception:
    settings = None


class AutoDeletionManager:
    def __init__(self, posts_dir: Path = Path("data/posts")):
        self.posts_dir = posts_dir
        self.deletion_log_file = Path("logs/auto_deletion.log")
        self.deletion_log_file.parent.mkdir(exist_ok=True)
        
        # Retention window (hours) from settings/env, default 24
        retention_hours = 24
        if settings and hasattr(settings, "AUTO_DELETION_HOURS"):
            try:
                retention_hours = int(getattr(settings, "AUTO_DELETION_HOURS"))
            except Exception:
                retention_hours = 24
        self.deletion_delay_seconds = retention_hours * 60 * 60
        
        logger.info(f"🗑️ Auto-Deletion Manager initialized ({retention_hours}-hour delay for server space)")
    
    def log_deletion(self, post_id: str, reason: str):
        """Log deletion activity"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} - DELETED post_{post_id}: {reason}\n"
        
        with open(self.deletion_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        logger.info(f"Auto-deleted post_{post_id}: {reason}")
    
    def get_post_creation_time(self, post_id: str) -> datetime:
        """Get the creation time of a post from its metadata"""
        metadata_path = self.posts_dir / f"post_{post_id}" / "metadata.json"
        
        if not metadata_path.exists():
            return datetime.now()  # Default to now if no metadata
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Try to get creation time from metadata
            created_at = metadata.get('created_at')
            if created_at:
                return datetime.fromisoformat(created_at)
            
            # Fallback to file modification time
            return datetime.fromtimestamp(metadata_path.stat().st_mtime)
            
        except Exception as e:
            logger.warning(f"Could not get creation time for post_{post_id}: {e}")
            return datetime.now()
    
    def is_post_ready_for_deletion(self, post_id: str) -> bool:
        """Check if a post is ready for deletion (24+ hours old)"""
        creation_time = self.get_post_creation_time(post_id)
        age_seconds = (datetime.now() - creation_time).total_seconds()
        
        return age_seconds >= self.deletion_delay_seconds
    
    def delete_post_directory(self, post_id: str) -> bool:
        """Delete a post's entire directory"""
        post_dir = self.posts_dir / f"post_{post_id}"
        
        if not post_dir.exists():
            logger.warning(f"Post directory does not exist: {post_dir}")
            return False
        
        try:
            shutil.rmtree(post_dir)
            logger.info(f"Successfully deleted post directory: {post_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete post directory {post_dir}: {e}")
            return False
    
    def cleanup_old_posts(self) -> int:
        """Clean up all posts that are 24+ hours old to save server space"""
        deleted_count = 0
        
        if not self.posts_dir.exists():
            logger.info("No posts directory found")
            return 0
        
        # Get all post directories
        post_dirs = [d for d in self.posts_dir.iterdir() if d.is_dir() and d.name.startswith("post_")]
        
        if not post_dirs:
            logger.info("No posts found for cleanup")
            return 0
        
        logger.info(f"🗑️ Checking {len(post_dirs)} posts for auto-deletion (24-hour policy)...")
        
        for post_dir in post_dirs:
            post_id = post_dir.name.replace("post_", "")
            
            if self.is_post_ready_for_deletion(post_id):
                # Check if post was actually posted (has final video)
                final_video = post_dir / "video" / "final.mp4"
                
                if final_video.exists():
                    # Post was successfully created and posted
                    if self.delete_post_directory(post_id):
                        self.log_deletion(post_id, "24-hour auto-deletion after successful posting (server space)")
                        deleted_count += 1
                    else:
                        logger.error(f"Failed to delete post_{post_id}")
                else:
                    # Post was never completed, safe to delete
                    if self.delete_post_directory(post_id):
                        self.log_deletion(post_id, "24-hour auto-deletion (incomplete post)")
                        deleted_count += 1
            else:
                # Calculate remaining time
                creation_time = self.get_post_creation_time(post_id)
                age_seconds = (datetime.now() - creation_time).total_seconds()
                remaining_seconds = self.deletion_delay_seconds - age_seconds
                remaining_hours = remaining_seconds / 3600
                
                logger.debug(f"Post_{post_id} not ready for deletion (remaining: {remaining_hours:.1f}h)")
        
        if deleted_count > 0:
            logger.info(f"✅ Auto-deletion completed: {deleted_count} posts deleted (freed server space)")
        else:
            logger.info("No posts ready for auto-deletion")
        
        return deleted_count
    
    def get_deletion_status(self) -> Dict[str, Any]:
        """Get status of all posts regarding deletion"""
        status = {
            "total_posts": 0,
            "ready_for_deletion": 0,
            "posts_status": []
        }
        
        if not self.posts_dir.exists():
            return status
        
        post_dirs = [d for d in self.posts_dir.iterdir() if d.is_dir() and d.name.startswith("post_")]
        status["total_posts"] = len(post_dirs)
        
        for post_dir in post_dirs:
            post_id = post_dir.name.replace("post_", "")
            creation_time = self.get_post_creation_time(post_id)
            age_seconds = (datetime.now() - creation_time).total_seconds()
            remaining_seconds = max(0, self.deletion_delay_seconds - age_seconds)
            remaining_hours = remaining_seconds / 3600
            
            is_ready = self.is_post_ready_for_deletion(post_id)
            if is_ready:
                status["ready_for_deletion"] += 1
            
            status["posts_status"].append({
                "post_id": post_id,
                "created_at": creation_time.isoformat(),
                "age_hours": age_seconds / 3600,
                "remaining_hours": remaining_hours,
                "ready_for_deletion": is_ready
            })
        
        return status


def main():
    """Test the auto-deletion system"""
    manager = AutoDeletionManager()
    
    print("Auto-Deletion System Status:")
    print("=" * 50)
    
    status = manager.get_deletion_status()
    print(f"Total posts: {status['total_posts']}")
    print(f"Ready for deletion: {status['ready_for_deletion']}")
    print()
    
    if status["posts_status"]:
        print("Post Details:")
        for post in status["posts_status"]:
            print(f"  Post {post['post_id']}: {post['age_hours']:.1f}h old, "
                  f"{post['remaining_hours']:.1f}h remaining, "
                  f"Ready: {'YES' if post['ready_for_deletion'] else 'NO'}")
    
    print()
    print("Running cleanup...")
    deleted = manager.cleanup_old_posts()
    print(f"Deleted {deleted} posts")


if __name__ == "__main__":
    main()

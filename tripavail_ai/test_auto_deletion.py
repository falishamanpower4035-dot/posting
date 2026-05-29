#!/usr/bin/env python3
"""
Test Auto-Deletion System
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.content.auto_deletion import AutoDeletionManager

def main():
    """Test the auto-deletion system"""
    print("Testing Auto-Deletion System")
    print("=" * 50)
    
    manager = AutoDeletionManager()
    
    # Get current status
    status = manager.get_deletion_status()
    
    print(f"Total posts: {status['total_posts']}")
    print(f"Ready for deletion: {status['ready_for_deletion']}")
    print()
    
    if status["posts_status"]:
        print("Post Details:")
        for post in status["posts_status"]:
            print(f"  Post {post['post_id']}:")
            print(f"    Created: {post['created_at']}")
            print(f"    Age: {post['age_hours']:.1f} hours")
            print(f"    Remaining: {post['remaining_hours']:.1f} hours")
            print(f"    Ready for deletion: {'YES' if post['ready_for_deletion'] else 'NO'}")
            print()
    
    # Run cleanup
    print("Running cleanup...")
    deleted = manager.cleanup_old_posts()
    print(f"Deleted {deleted} posts")
    
    if deleted > 0:
        print("\nCheck logs/auto_deletion.log for details")

if __name__ == "__main__":
    main()

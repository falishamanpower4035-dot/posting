#!/usr/bin/env python3
"""Check why overdue posts aren't posting"""
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytz

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled

def main():
    pm = PostManager()
    items = list_scheduled("pending")
    now = datetime.now(timezone.utc)
    
    print("=" * 60)
    print("OVERDUE POSTS ANALYSIS")
    print("=" * 60)
    
    overdue = []
    for item in items:
        when = datetime.fromisoformat(item.scheduled_at)
        if when.tzinfo is None:
            when = pytz.utc.localize(when)
        if when <= now:
            overdue.append((item.post_id, item.scheduled_at, item.priority))
    
    print(f"\nFound {len(overdue)} overdue posts:\n")
    
    for post_id, scheduled_at, priority in sorted(overdue, key=lambda x: x[1]):
        print(f"Post {post_id} (scheduled: {scheduled_at}, priority: {priority})")
        
        # Check posting status
        ig = pm.is_posted(post_id, "instagram")
        fb = pm.is_posted(post_id, "facebook")
        yt = pm.is_posted(post_id, "youtube")
        
        print(f"  Status: IG={ig}, FB={fb}, YT={yt}")
        
        # Check if video exists
        video = pm.get_final_video_path(post_id)
        video_exists = video.exists() if video else False
        print(f"  Video exists: {video_exists}")
        if video:
            print(f"  Video path: {video}")
        
        # Check metadata
        meta = pm.get_metadata(post_id)
        if meta:
            title = meta.get('original_title', 'N/A')[:60]
            print(f"  Title: {title}")
        else:
            print(f"  ⚠️  No metadata found!")
        
        # Check if fully posted
        if ig and fb and yt:
            print(f"  ✅ Already fully posted - should be marked as done")
        else:
            print(f"  ⚠️  Not fully posted - should be posting")
        
        print()

if __name__ == "__main__":
    main()


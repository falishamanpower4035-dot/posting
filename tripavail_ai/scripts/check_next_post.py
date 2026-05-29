#!/usr/bin/env python3
"""Check next scheduled posts"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

def check_scheduled_posts():
    scheduled_file = Path("data/scheduled_posts.json")
    
    if not scheduled_file.exists():
        print("No scheduled_posts.json found")
        return
    
    data = json.loads(scheduled_file.read_text())
    
    # Handle both dict and list formats
    if isinstance(data, dict):
        posts = data.get("posts", [])
    elif isinstance(data, list):
        posts = data
    else:
        posts = []
    
    if not posts:
        print("No scheduled posts found")
        return
    
    now = datetime.now(timezone.utc)
    
    # Filter pending posts
    pending = []
    for post in posts:
        scheduled_time_str = post.get("scheduled_time", "")
        if scheduled_time_str:
            try:
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                if scheduled_time >= now:
                    pending.append((scheduled_time, post))
            except:
                pass
    
    pending.sort(key=lambda x: x[0])
    
    print("="*60)
    print("SCHEDULED POSTS STATUS")
    print("="*60)
    print(f"\nCurrent time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Total scheduled posts: {len(posts)}")
    print(f"Pending posts: {len(pending)}")
    print()
    
    if pending:
        print("NEXT POSTS TO BE PUBLISHED:")
        print("-"*60)
        for scheduled_time, post in pending[:10]:
            post_id = post.get("post_id", "unknown")
            time_until = scheduled_time - now
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)
            
            print(f"Post {post_id}:")
            print(f"  Scheduled: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  In: {hours}h {minutes}m ({time_until.total_seconds()/60:.0f} minutes)")
            print()
    else:
        print("No pending posts scheduled")
    
    # Check done posts
    done_posts = [p for p in posts if p.get("done", False)]
    print(f"Already posted: {len(done_posts)} posts")
    
    if done_posts:
        print("\nRECENTLY POSTED:")
        print("-"*60)
        for post in sorted(done_posts, key=lambda x: x.get("scheduled_time", ""), reverse=True)[:5]:
            post_id = post.get("post_id", "unknown")
            scheduled_time_str = post.get("scheduled_time", "")
            print(f"Post {post_id}: {scheduled_time_str}")

if __name__ == "__main__":
    check_scheduled_posts()


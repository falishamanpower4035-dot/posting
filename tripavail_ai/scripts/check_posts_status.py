#!/usr/bin/env python3
"""Check status of specific posts"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
import json

pm = PostManager()

for post_id in ['047', '048', '049']:
    print(f"\n{'='*60}")
    print(f"POST {post_id}")
    print(f"{'='*60}")
    
    meta = pm.get_metadata(post_id)
    if not meta:
        print("❌ No metadata found")
        continue
    
    title = meta.get('original_title', 'N/A')
    print(f"Title: {title}")
    print(f"Created: {meta.get('created_at', 'N/A')}")
    
    # Check posting status
    ig_posted = pm.is_posted(post_id, 'instagram')
    fb_posted = pm.is_posted(post_id, 'facebook')
    yt_posted = pm.is_posted(post_id, 'youtube')
    
    print(f"\nPosting Status:")
    print(f"  Instagram: {'✅ Posted' if ig_posted else '❌ Not posted'}")
    print(f"  Facebook: {'✅ Posted' if fb_posted else '❌ Not posted'}")
    print(f"  YouTube: {'✅ Posted' if yt_posted else '❌ Not posted'}")
    
    # Check video
    video = pm.get_final_video_path(post_id)
    print(f"\nVideo:")
    print(f"  Path: {video}")
    print(f"  Exists: {'✅ Yes' if video.exists() else '❌ No'}")
    
    # Check scheduled posts
    schedule_file = Path('data/scheduled_posts.json')
    if schedule_file.exists():
        schedules = json.loads(schedule_file.read_text())
        post_schedules = [s for s in schedules if s.get('post_id') == post_id]
        if post_schedules:
            print(f"\nSchedule Status:")
            for sched in post_schedules:
                print(f"  Scheduled: {sched.get('scheduled_at', 'N/A')}")
                print(f"  Status: {sched.get('status', 'N/A')}")
                print(f"  Priority: {sched.get('priority', 'N/A')}")
        else:
            print(f"\nSchedule Status: ❌ Not in scheduled_posts.json")


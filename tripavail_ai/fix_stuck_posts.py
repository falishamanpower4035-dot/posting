#!/usr/bin/env python3
"""Fix stuck posts by marking them as done in the scheduler"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.scheduling.scheduler import mark_done, list_scheduled

# Posts that are stuck in a loop
stuck_posts = ['288', '289', '301', '303']

print("Current scheduled posts:")
scheduled = list_scheduled()
for post in scheduled:
    if post['post_id'] in stuck_posts:
        print(f"  - Post {post['post_id']}: {post}")

print("\nMarking stuck posts as done...")
for post_id in stuck_posts:
    try:
        mark_done(post_id)
        print(f"✅ Marked post {post_id} as done")
    except Exception as e:
        print(f"❌ Failed to mark post {post_id}: {e}")

print("\nRemaining scheduled posts:")
scheduled = list_scheduled()
for post in scheduled:
    if post['post_id'] in stuck_posts:
        print(f"  - Post {post['post_id']}: {post}")

print("\nDone!")


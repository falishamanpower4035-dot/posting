#!/usr/bin/env python3
"""Mark all duplicate NZ visa posts as done"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scheduling.scheduler import mark_done
from core.content.post_manager import PostManager

pm = PostManager()

# All duplicate posts for NZ visa story
duplicate_posts = ['019', '021', '023', '025', '039', '041', '043', '045', '046']

print("="*60)
print("MARKING DUPLICATE POSTS AS DONE")
print("="*60)

# Keep only the first posted one (Post 039 - fully posted to all platforms)
# Mark all others as done
posts_to_mark_done = ['019', '021', '023', '025', '041', '043', '045', '046']

print(f"\nPosts to mark as done: {posts_to_mark_done}")
print(f"Keeping Post 039 (first fully posted)")

for post_id in posts_to_mark_done:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get('original_title', 'N/A')[:60]
    ig_posted = pm.is_posted(post_id, 'instagram')
    fb_posted = pm.is_posted(post_id, 'facebook')
    yt_posted = pm.is_posted(post_id, 'youtube')
    
    print(f"\nPost {post_id}: {title}")
    print(f"  Posted: IG={ig_posted}, FB={fb_posted}, YT={yt_posted}")
    
    # Mark as done
    mark_done(post_id)
    print(f"  ✅ Marked as done")

print("\n" + "="*60)
print("COMPLETE: All duplicate posts marked as done")
print("="*60)


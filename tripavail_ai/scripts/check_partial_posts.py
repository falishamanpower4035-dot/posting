#!/usr/bin/env python3
"""Check posts that are partially posted (Instagram but not FB/YT)"""
import sys
sys.path.insert(0, '/opt/tripavail_ai')

from dotenv import load_dotenv
load_dotenv()

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled

pm = PostManager()

# Get all posts
all_posts = pm.get_all_posts()
recent_posts = sorted(all_posts)[-20:]  # Last 20 posts

print("="*70)
print("RECENT POSTS - PARTIAL POSTING STATUS")
print("="*70)
print("\nPosts posted to Instagram but NOT Facebook/YouTube:\n")

partial_posts = []
for post_id in recent_posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    ig = pm.is_posted(post_id, "instagram")
    fb = pm.is_posted(post_id, "facebook")
    yt = pm.is_posted(post_id, "youtube")
    
    # Find posts posted to Instagram but not FB/YT
    if ig and (not fb or not yt):
        title = meta.get('original_title', 'N/A')[:60]
        status = []
        if ig: status.append("✅IG")
        if fb: status.append("✅FB")
        else: status.append("❌FB")
        if yt: status.append("✅YT")
        else: status.append("❌YT")
        
        print(f"Post {post_id}: {title}")
        print(f"  Status: {' '.join(status)}")
        
        # Check if still scheduled
        pending = list_scheduled(status="pending")
        scheduled = any(p.post_id == post_id for p in pending)
        if scheduled:
            print(f"  ⚠️ Still scheduled - will post to FB/YT when due!")
        else:
            print(f"  ℹ️ Not scheduled - already marked as done")
        print()
        partial_posts.append(post_id)

if not partial_posts:
    print("✅ No partially posted posts found!")
    print("All recent posts are either fully posted or not posted yet.")


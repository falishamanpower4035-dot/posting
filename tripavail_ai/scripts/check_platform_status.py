#!/usr/bin/env python3
"""Check recent posts and their platform posting status"""
import sys
sys.path.insert(0, '/opt/tripavail_ai')

from dotenv import load_dotenv
load_dotenv()

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled

pm = PostManager()

print("="*70)
print("RECENT POSTS STATUS")
print("="*70)

# Get all posts and check last 10
all_posts = pm.get_all_posts()
recent_posts = sorted(all_posts)[-10:]

for post_id in recent_posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get('original_title', 'N/A')[:60]
    ig = pm.is_posted(post_id, "instagram")
    fb = pm.is_posted(post_id, "facebook")
    yt = pm.is_posted(post_id, "youtube")
    
    status = []
    if ig: status.append("✅IG")
    else: status.append("❌IG")
    if fb: status.append("✅FB")
    else: status.append("❌FB")
    if yt: status.append("✅YT")
    else: status.append("❌YT")
    
    print(f"Post {post_id}: {title}")
    print(f"  Status: {' '.join(status)}")

print("\n" + "="*70)
print("PENDING SCHEDULED POSTS")
print("="*70)

pending = list_scheduled(status="pending")
for item in pending[:10]:
    ig = pm.is_posted(item.post_id, "instagram")
    fb = pm.is_posted(item.post_id, "facebook")
    yt = pm.is_posted(item.post_id, "youtube")
    
    status = []
    if ig: status.append("✅IG")
    else: status.append("❌IG")
    if fb: status.append("✅FB")
    else: status.append("❌FB")
    if yt: status.append("✅YT")
    else: status.append("❌YT")
    
    print(f"Post {item.post_id}: scheduled_at={item.scheduled_at}")
    print(f"  Current status: {' '.join(status)}")

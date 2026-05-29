#!/usr/bin/env python3
"""Check recent Facebook posting activity"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
import json

pm = PostManager()
posts = sorted(pm.get_all_posts())[-15:]

print("Recent posts Facebook posting status:")
print("=" * 60)
for post_id in posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    fb_posted = pm.is_posted(post_id, "facebook")
    fb_info = meta.get("posted_platforms", {}).get("facebook", {})
    
    if fb_info:
        posted_at = fb_info.get("posted_at", "Unknown")
        url = fb_info.get("url", "No URL")
        print(f"Post {post_id}: FB={fb_posted}, Posted at: {posted_at}")
        if url != "No URL":
            print(f"  URL: {url}")


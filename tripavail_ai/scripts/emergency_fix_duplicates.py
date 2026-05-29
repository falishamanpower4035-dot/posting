#!/usr/bin/env python3
"""Emergency fix: Mark all duplicate posts as done"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import mark_done

pm = PostManager()

# Load schedules
schedule_file = Path('data/scheduled_posts.json')
schedules = json.loads(schedule_file.read_text()) if schedule_file.exists() else []

print("="*70)
print("EMERGENCY FIX: MARKING ALL DUPLICATE POSTS AS DONE")
print("="*70)

# Find all duplicate titles
all_posts = pm.get_all_posts()
title_map = {}
for post_id in all_posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    title = meta.get('original_title', '').strip()
    if not title:
        continue
    normalized = ' '.join(title.lower().split())
    if normalized not in title_map:
        title_map[normalized] = []
    title_map[normalized].append(post_id)

duplicate_titles = {t: posts for t, posts in title_map.items() if len(posts) > 1}

print(f"\nFound {len(duplicate_titles)} duplicate titles\n")

posts_to_mark_done = set()

for normalized_title, post_ids in duplicate_titles.items():
    # Sort by post_id to keep the first one
    sorted_posts = sorted(post_ids)
    keep_post = sorted_posts[0]  # Keep the first one
    
    # Get metadata for the keep post
    keep_meta = pm.get_metadata(keep_post)
    title = keep_meta.get('original_title', 'N/A')[:60] if keep_meta else 'N/A'
    
    print(f"Title: {title}")
    print(f"  Keeping: Post {keep_post}")
    print(f"  Marking as done: Posts {sorted_posts[1:]}")
    
    # Mark all duplicates as done (except the first one)
    for post_id in sorted_posts[1:]:
        posts_to_mark_done.add(post_id)

print(f"\n{'='*70}")
print(f"Marking {len(posts_to_mark_done)} duplicate posts as done...")
print(f"{'='*70}\n")

for post_id in sorted(posts_to_mark_done):
    meta = pm.get_metadata(post_id)
    title = meta.get('original_title', 'N/A')[:60] if meta else 'N/A'
    ig_posted = pm.is_posted(post_id, 'instagram')
    fb_posted = pm.is_posted(post_id, 'facebook')
    yt_posted = pm.is_posted(post_id, 'youtube')
    
    print(f"Post {post_id}: {title}")
    print(f"  Posted: IG={ig_posted}, FB={fb_posted}, YT={yt_posted}")
    
    mark_done(post_id)
    print(f"  ✅ Marked as done\n")

print(f"{'='*70}")
print("COMPLETE: All duplicate posts marked as done")
print(f"{'='*70}")


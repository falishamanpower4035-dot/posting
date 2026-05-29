#!/usr/bin/env python3
"""Check all posts and schedules for duplicates"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

pm = PostManager()

# Load schedules
schedule_file = Path('data/scheduled_posts.json')
schedules = json.loads(schedule_file.read_text()) if schedule_file.exists() else []

print("="*70)
print("CHECKING FOR DUPLICATE POSTS AND SCHEDULES")
print("="*70)

# Group by post_id
pending_by_post = {}
for sched in schedules:
    if sched.get('status') == 'pending':
        post_id = sched.get('post_id')
        if post_id not in pending_by_post:
            pending_by_post[post_id] = []
        pending_by_post[post_id].append(sched)

print(f"\n📊 SUMMARY:")
print(f"  Total pending schedules: {len([s for s in schedules if s.get('status') == 'pending'])}")
print(f"  Posts with pending schedules: {len(pending_by_post)}")

# Check for posts with multiple pending schedules
duplicate_schedules = {pid: scheds for pid, scheds in pending_by_post.items() if len(scheds) > 1}
if duplicate_schedules:
    print(f"\n⚠️  FOUND {len(duplicate_schedules)} POSTS WITH MULTIPLE PENDING SCHEDULES:")
    for post_id, scheds in duplicate_schedules.items():
        meta = pm.get_metadata(post_id)
        title = meta.get('original_title', 'N/A')[:60] if meta else 'N/A'
        ig_posted = pm.is_posted(post_id, 'instagram')
        fb_posted = pm.is_posted(post_id, 'facebook')
        yt_posted = pm.is_posted(post_id, 'youtube')
        print(f"\n  Post {post_id}: {title}")
        print(f"    Posted: IG={ig_posted}, FB={fb_posted}, YT={yt_posted}")
        print(f"    Has {len(scheds)} pending schedules:")
        for s in sorted(scheds, key=lambda x: x.get('scheduled_at', '')):
            print(f"      - {s.get('scheduled_at')} (priority={s.get('priority')})")

# Check for duplicate titles
print(f"\n" + "="*70)
print("CHECKING FOR DUPLICATE TITLES:")
print("="*70)

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
    title_map[normalized].append({
        'post_id': post_id,
        'title': title,
        'created': meta.get('created_at', ''),
        'ig_posted': pm.is_posted(post_id, 'instagram'),
        'fb_posted': pm.is_posted(post_id, 'facebook'),
        'yt_posted': pm.is_posted(post_id, 'youtube'),
    })

duplicate_titles = {t: posts for t, posts in title_map.items() if len(posts) > 1}
if duplicate_titles:
    print(f"\n⚠️  FOUND {len(duplicate_titles)} DUPLICATE TITLES:")
    for normalized_title, posts in sorted(duplicate_titles.items()):
        print(f"\n  '{posts[0]['title'][:70]}'")
        print(f"    {len(posts)} posts with same title:")
        for post in sorted(posts, key=lambda x: x['post_id']):
            posted_status = f"IG={post['ig_posted']}, FB={post['fb_posted']}, YT={post['yt_posted']}"
            print(f"      Post {post['post_id']}: {posted_status} (created: {post['created'][:19] if post['created'] else 'N/A'})")
else:
    print("\n✅ No duplicate titles found")

print("\n" + "="*70)


#!/usr/bin/env python3
"""Check wellness wonder post and detect multiple daemon instances"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

pm = PostManager()

print("="*70)
print("WELLNESS WONDER POST ANALYSIS + MULTIPLE DAEMON CHECK")
print("="*70)

# Find wellness wonder posts
all_posts = pm.get_all_posts()
wellness_posts = []

for post_id in sorted(all_posts):
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = (meta.get('original_title', '') or '').lower()
    if 'wellness' in title or 'wonder' in title:
        wellness_posts.append({
            'post_id': post_id,
            'title': meta.get('original_title', ''),
            'url': meta.get('original_url', '') or meta.get('link', ''),
            'created': meta.get('created_at', ''),
            'ig_posted': pm.is_posted(post_id, 'instagram'),
            'fb_posted': pm.is_posted(post_id, 'facebook'),
            'yt_posted': pm.is_posted(post_id, 'youtube'),
            'posted_platforms': meta.get('posted_platforms', {})
        })

if wellness_posts:
    print("\n1. WELLNESS WONDER POSTS FOUND:")
    print("-" * 70)
    for post in wellness_posts:
        print(f"\nPost {post['post_id']}:")
        print(f"  Title: {post['title'][:70]}")
        print(f"  URL: {post['url'][:70] if post['url'] else 'NO URL'}")
        print(f"  Created: {post['created'][:19] if post['created'] else 'N/A'}")
        print(f"  Posted: IG={post['ig_posted']}, FB={post['fb_posted']}, YT={post['yt_posted']}")
        if post['posted_platforms']:
            print(f"  Posting History:")
            for platform, info in post['posted_platforms'].items():
                posted_at = info.get('posted_at', 'N/A')[:19] if isinstance(info, dict) else 'N/A'
                print(f"    {platform}: {posted_at}")
else:
    print("\n1. No wellness wonder posts found")

# Check schedules
schedule_file = Path('data/scheduled_posts.json')
if schedule_file.exists():
    schedules = json.loads(schedule_file.read_text())
    wellness_schedules = []
    if wellness_posts:
        wellness_schedules = [s for s in schedules if any(p['post_id'] == s.get('post_id') for p in wellness_posts)]
    
    if wellness_schedules:
        print(f"\n\n2. SCHEDULES FOR WELLNESS POSTS:")
        print("-" * 70)
        for sched in sorted(wellness_schedules, key=lambda x: x.get('scheduled_at', '')):
            print(f"  Post {sched.get('post_id')}: {sched.get('scheduled_at')[:19]} - {sched.get('status')}")

# Check for duplicates
if len(wellness_posts) > 1:
    print(f"\n\n3. DUPLICATE CHECK:")
    print("-" * 70)
    print(f"  ⚠️  FOUND {len(wellness_posts)} POSTS ABOUT WELLNESS:")
    titles = [p['title'] for p in wellness_posts]
    if len(set(titles)) < len(titles):
        print("  ⚠️ DUPLICATE TITLES DETECTED!")
        from collections import Counter
        title_counts = Counter(titles)
        for title, count in title_counts.items():
            if count > 1:
                print(f"    '{title[:60]}' - {count} posts")

print("\n" + "="*70)


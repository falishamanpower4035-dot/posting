#!/usr/bin/env python3
"""Check duplicate posts by title and URL"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
import json

pm = PostManager()

print("="*60)
print("CHECKING DUPLICATE POSTS - NZ VISA STORY")
print("="*60)

# Find all posts with visa/NZ/Chinese keywords
all_posts = pm.get_all_posts()
relevant_posts = []

for post_id in sorted(all_posts):
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get('original_title', '').lower()
    url = meta.get('original_url', '')
    
    if any(keyword in title for keyword in ['visa', 'nz', 'new zealand', 'chinese', 'australia']):
        relevant_posts.append({
            'post_id': post_id,
            'title': meta.get('original_title', ''),
            'url': url,
            'created': meta.get('created_at', ''),
            'ig_posted': pm.is_posted(post_id, 'instagram'),
            'fb_posted': pm.is_posted(post_id, 'facebook'),
            'yt_posted': pm.is_posted(post_id, 'youtube'),
        })

print(f"\nFound {len(relevant_posts)} relevant posts:\n")

for post in relevant_posts:
    print(f"Post {post['post_id']}:")
    print(f"  Title: {post['title'][:80]}")
    print(f"  URL: {post['url'][:80] if post['url'] else 'No URL'}")
    print(f"  Created: {post['created'][:19] if post['created'] else 'N/A'}")
    print(f"  Posted: IG={post['ig_posted']}, FB={post['fb_posted']}, YT={post['yt_posted']}")
    print()

# Check for duplicates by title
print("\n" + "="*60)
print("DUPLICATE CHECK BY TITLE:")
print("="*60)

title_map = {}
for post in relevant_posts:
    normalized_title = ' '.join(post['title'].lower().split())
    if normalized_title not in title_map:
        title_map[normalized_title] = []
    title_map[normalized_title].append(post)

duplicates_found = False
for normalized_title, posts in title_map.items():
    if len(posts) > 1:
        duplicates_found = True
        print(f"\n⚠️ DUPLICATE TITLE FOUND ({len(posts)} posts):")
        print(f"   Title: {posts[0]['title'][:80]}")
        for post in posts:
            print(f"   - Post {post['post_id']}: Created {post['created'][:19]}, Posted: IG={post['ig_posted']}, FB={post['fb_posted']}")

if not duplicates_found:
    print("\n✅ No exact title duplicates found")

# Check scheduled posts
print("\n" + "="*60)
print("SCHEDULED POSTS CHECK:")
print("="*60)

schedule_file = Path('data/scheduled_posts.json')
if schedule_file.exists():
    schedules = json.loads(schedule_file.read_text())
    for post in relevant_posts:
        post_schedules = [s for s in schedules if s.get('post_id') == post['post_id']]
        if post_schedules:
            print(f"\nPost {post['post_id']}: {len(post_schedules)} schedule(s)")
            for sched in post_schedules:
                print(f"  - {sched.get('scheduled_at', 'N/A')}: {sched.get('status', 'N/A')}")


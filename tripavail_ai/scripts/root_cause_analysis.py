#!/usr/bin/env python3
"""Root Cause Analysis: Why are duplicate posts being created?"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

pm = PostManager()

print("="*70)
print("ROOT CAUSE ANALYSIS: DUPLICATE POSTS")
print("="*70)

# Check duplicate posts
all_posts = pm.get_all_posts()
title_map = {}
url_map = {}

for post_id in sorted(all_posts):
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get('original_title', '').strip()
    url = meta.get('original_url', '') or meta.get('link', '')
    
    if title:
        normalized = ' '.join(title.lower().split())
        if normalized not in title_map:
            title_map[normalized] = []
        title_map[normalized].append({
            'post_id': post_id,
            'title': title,
            'url': url,
            'created': meta.get('created_at', ''),
        })
    
    if url:
        if url not in url_map:
            url_map[url] = []
        url_map[url].append({
            'post_id': post_id,
            'title': title,
            'created': meta.get('created_at', ''),
        })

print("\n1. CHECKING FOR MISSING URLs:")
print("-" * 70)
posts_without_url = 0
for post_id in sorted(all_posts):
    meta = pm.get_metadata(post_id)
    if meta:
        url = meta.get('original_url', '') or meta.get('link', '')
        if not url:
            posts_without_url += 1
            title = meta.get('original_title', 'N/A')[:50]
            print(f"  Post {post_id}: NO URL - {title}")

print(f"\n  Total posts without URL: {posts_without_url}/{len(all_posts)}")

print("\n2. CHECKING DUPLICATE TITLES:")
print("-" * 70)
duplicate_titles = {t: posts for t, posts in title_map.items() if len(posts) > 1}
if duplicate_titles:
    print(f"  Found {len(duplicate_titles)} duplicate titles:")
    for normalized_title, posts in sorted(duplicate_titles.items()):
        print(f"\n  Title: '{posts[0]['title'][:60]}'")
        print(f"  {len(posts)} posts with same title:")
        for post in sorted(posts, key=lambda x: x['post_id']):
            url_status = "HAS URL" if post['url'] else "NO URL"
            print(f"    Post {post['post_id']}: {url_status}, Created: {post['created'][:19] if post['created'] else 'N/A'}")

print("\n3. CHECKING DUPLICATE URLs:")
print("-" * 70)
duplicate_urls = {url: posts for url, posts in url_map.items() if len(posts) > 1}
if duplicate_urls:
    print(f"  Found {len(duplicate_urls)} duplicate URLs:")
    for url, posts in sorted(duplicate_urls.items()):
        print(f"\n  URL: {url[:60]}")
        print(f"  {len(posts)} posts with same URL:")
        for post in sorted(posts, key=lambda x: x['post_id']):
            print(f"    Post {post['post_id']}: {post['title'][:50]}, Created: {post['created'][:19] if post['created'] else 'N/A'}")
else:
    print("  ✅ No duplicate URLs found")

print("\n4. TESTING DUPLICATE DETECTION:")
print("-" * 70)
# Test with a known duplicate
test_topic = {
    'title': 'Visa-free access to NZ via Australia for Chinese tourists',
    'link': '',
    'url': ''
}

print(f"\n  Testing topic: '{test_topic['title']}'")
print(f"  URL: {test_topic.get('link') or test_topic.get('url') or 'EMPTY'}")

result = pm.is_news_already_used(test_topic)
print(f"  Duplicate check result: {result}")

# Check what titles are stored
used_titles = pm.get_used_news_titles()
normalized_test = ' '.join(test_topic['title'].lower().split())
print(f"  Normalized test title: '{normalized_test}'")
print(f"  Found in used titles: {normalized_test in used_titles}")

if normalized_test in used_titles:
    print(f"  ✅ Duplicate detection WORKS for this title")
else:
    print(f"  ❌ Duplicate detection FAILED for this title")

print("\n5. ANALYZING ROOT CAUSE:")
print("-" * 70)

if posts_without_url > len(all_posts) * 0.5:
    print("  ⚠️ ISSUE #1: Most posts are missing URLs!")
    print("     - Duplicate detection relies on URL first, then title")
    print("     - If URLs are missing, it falls back to title matching")
    print("     - This might fail if titles are slightly different")

if duplicate_titles:
    print(f"\n  ⚠️ ISSUE #2: {len(duplicate_titles)} duplicate titles found!")
    print("     - Same news article created multiple posts")
    print("     - Possible causes:")
    print("       a) News fetcher keeps fetching same articles")
    print("       b) Duplicate detection failed during generation")
    print("       c) Posts created before duplicate detection was implemented")

if duplicate_urls:
    print(f"\n  ⚠️ ISSUE #3: {len(duplicate_urls)} duplicate URLs found!")
    print("     - Same URL used for multiple posts")
    print("     - This should NEVER happen if duplicate detection works")

print("\n" + "="*70)


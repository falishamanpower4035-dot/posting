#!/usr/bin/env python3
"""Check if multiple posts use the same news article"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from core.content.post_manager import PostManager
from collections import Counter

pm = PostManager()
posts = sorted(pm.get_all_posts())[-20:]

print("Checking for duplicate news articles across posts:\n")
print("=" * 80)

# Track news by URL and title
news_urls = {}
news_titles = {}

for post_id in posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get("original_title", "")
    url = meta.get("original_url", "")
    
    if title:
        if title not in news_titles:
            news_titles[title] = []
        news_titles[title].append(post_id)
    
    if url:
        if url not in news_urls:
            news_urls[url] = []
        news_urls[url].append(post_id)

# Find duplicates
duplicate_titles = {k: v for k, v in news_titles.items() if len(v) > 1}
duplicate_urls = {k: v for k, v in news_urls.items() if len(v) > 1}

if duplicate_titles:
    print("\n⚠️ DUPLICATE NEWS TITLES FOUND:")
    for title, post_ids in duplicate_titles.items():
        print(f"\n  Title: {title[:70]}")
        print(f"  Used in posts: {', '.join(post_ids)}")
else:
    print("\n✅ No duplicate titles found")

if duplicate_urls:
    print("\n⚠️ DUPLICATE NEWS URLS FOUND:")
    for url, post_ids in duplicate_urls.items():
        print(f"\n  URL: {url}")
        print(f"  Used in posts: {', '.join(post_ids)}")
else:
    print("\n✅ No duplicate URLs found")

print("\n" + "=" * 80)


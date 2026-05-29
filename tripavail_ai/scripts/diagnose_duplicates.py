#!/usr/bin/env python3
"""Diagnostic script to identify duplicate posting issues"""
import sys
import os
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from core.content.post_manager import PostManager

pm = PostManager()
posts = sorted(pm.get_all_posts())

print("=" * 80)
print("DUPLICATE POSTING DIAGNOSTIC REPORT")
print("=" * 80)

# 1. Check for duplicate news articles used in multiple posts
print("\n1. CHECKING FOR DUPLICATE NEWS ARTICLES:")
print("-" * 80)

news_by_url = defaultdict(list)
news_by_title = defaultdict(list)

for post_id in posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get('original_title', '').strip()
    url = meta.get('original_url') or meta.get('link', '')
    
    if url:
        news_by_url[url].append(post_id)
    if title:
        normalized_title = ' '.join(title.lower().split())
        news_by_title[normalized_title].append(post_id)

# Find duplicates
url_duplicates = {k: v for k, v in news_by_url.items() if len(v) > 1}
title_duplicates = {k: v for k, v in news_by_title.items() if len(v) > 1}

if url_duplicates:
    print(f"\n⚠️  Found {len(url_duplicates)} news URLs used in multiple posts:")
    for url, post_ids in list(url_duplicates.items())[:5]:
        print(f"   URL: {url[:60]}...")
        print(f"   Posts: {', '.join(post_ids)}")
else:
    print("\n✅ No duplicate URLs found")

if title_duplicates:
    print(f"\n⚠️  Found {len(title_duplicates)} news titles used in multiple posts:")
    for title, post_ids in list(title_duplicates.items())[:5]:
        print(f"   Title: {title[:60]}...")
        print(f"   Posts: {', '.join(post_ids)}")
else:
    print("\n✅ No duplicate titles found")

# 2. Check posting status across platforms
print("\n\n2. CHECKING POSTING STATUS ACROSS PLATFORMS:")
print("-" * 80)

platform_status = defaultdict(lambda: {'posted': 0, 'not_posted': 0})
posting_times = defaultdict(lambda: defaultdict(list))

for post_id in posts[-20:]:  # Last 20 posts
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    for platform in ['instagram', 'facebook', 'youtube']:
        is_posted = pm.is_posted(post_id, platform)
        if is_posted:
            platform_status[platform]['posted'] += 1
            posted_info = meta.get('posted_platforms', {}).get(platform, {})
            posted_at = posted_info.get('posted_at', 'Unknown')
            posting_times[platform][post_id].append(posted_at)
        else:
            platform_status[platform]['not_posted'] += 1

for platform in ['instagram', 'facebook', 'youtube']:
    stats = platform_status[platform]
    total = stats['posted'] + stats['not_posted']
    print(f"\n{platform.upper()}:")
    print(f"   Posted: {stats['posted']}/{total}")
    print(f"   Not Posted: {stats['not_posted']}/{total}")

# 3. Check for posts posted multiple times to same platform
print("\n\n3. CHECKING FOR MULTIPLE POSTINGS TO SAME PLATFORM:")
print("-" * 80)

multi_posted = defaultdict(lambda: defaultdict(list))

for post_id in posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    posted_platforms = meta.get('posted_platforms', {})
    for platform, info in posted_platforms.items():
        posted_at = info.get('posted_at')
        if posted_at:
            # Check if this post appears multiple times in scheduled_posts.json
            multi_posted[platform][post_id].append(posted_at)

# Check scheduled_posts.json for duplicates
print("\n\n4. CHECKING SCHEDULED_POSTS.JSON FOR DUPLICATES:")
print("-" * 80)

scheduled_file = Path("data/scheduled_posts.json")
if scheduled_file.exists():
    with open(scheduled_file, 'r') as f:
        scheduled = json.load(f)
    
    post_ids_in_schedule = [item.get('post_id') for item in scheduled if item.get('status') == 'pending']
    duplicate_scheduled = Counter(post_ids_in_schedule)
    duplicates = {pid: count for pid, count in duplicate_scheduled.items() if count > 1}
    
    if duplicates:
        print(f"\n⚠️  Found {len(duplicates)} post_ids scheduled multiple times:")
        for post_id, count in duplicates.items():
            print(f"   Post {post_id}: scheduled {count} times")
            # Show scheduled times
            times = [item.get('scheduled_at') for item in scheduled if item.get('post_id') == post_id and item.get('status') == 'pending']
            for t in times:
                print(f"      - {t}")
    else:
        print("\n✅ No duplicate scheduled entries found")
else:
    print("\n⚠️  scheduled_posts.json not found")

# 5. Check recent posts for posting patterns
print("\n\n5. RECENT POSTS POSTING PATTERNS (Last 10 posts):")
print("-" * 80)

for post_id in posts[-10:]:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    title = meta.get('original_title', 'N/A')[:50]
    posted_platforms = meta.get('posted_platforms', {})
    
    print(f"\nPost {post_id}: {title}")
    print(f"   Created: {meta.get('created_at', 'Unknown')}")
    for platform in ['instagram', 'facebook', 'youtube']:
        if platform in posted_platforms:
            posted_at = posted_platforms[platform].get('posted_at', 'Unknown')
            print(f"   {platform}: ✅ Posted at {posted_at}")
        else:
            print(f"   {platform}: ❌ Not posted")

print("\n" + "=" * 80)


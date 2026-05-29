#!/usr/bin/env python3
"""Comprehensive safety check - ensure NO duplicate posting"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled

pm = PostManager()

print("="*70)
print("COMPREHENSIVE SAFETY CHECK - NO DUPLICATE POSTING")
print("="*70)

# 1. Check all pending schedules
print("\n1. PENDING SCHEDULES:")
print("-" * 70)
pending = list_scheduled(status="pending")
if pending:
    print(f"  ⚠️  Found {len(pending)} pending schedules:")
    for item in pending[:10]:  # Show first 10
        meta = pm.get_metadata(item.post_id)
        title = meta.get('original_title', 'Unknown')[:50] if meta else 'Unknown'
        ig = pm.is_posted(item.post_id, "instagram")
        fb = pm.is_posted(item.post_id, "facebook")
        yt = pm.is_posted(item.post_id, "youtube")
        
        if ig or fb or yt:
            print(f"  ⚠️  Post {item.post_id}: {title}")
            print(f"       Scheduled: {item.scheduled_at[:19]}")
            print(f"       Already posted: IG={ig}, FB={fb}, YT={yt}")
            print(f"       ⚠️ RISK: This post will be posted again!")
        else:
            print(f"  ✅ Post {item.post_id}: {title[:50]} - Not posted yet")
else:
    print("  ✅ No pending schedules")

# 2. Check for duplicate schedules
print("\n2. DUPLICATE SCHEDULE CHECK:")
print("-" * 70)
all_schedules = list_scheduled(status="pending")
post_ids = [s.post_id for s in all_schedules]
from collections import Counter
duplicates = {pid: count for pid, count in Counter(post_ids).items() if count > 1}
if duplicates:
    print(f"  ⚠️  Found {len(duplicates)} posts scheduled multiple times:")
    for pid, count in duplicates.items():
        meta = pm.get_metadata(pid)
        title = meta.get('original_title', 'Unknown')[:50] if meta else 'Unknown'
        print(f"  ⚠️  Post {pid}: {title} - scheduled {count} times!")
else:
    print("  ✅ No duplicate schedules found")

# 3. Check recent posts for duplicates
print("\n3. RECENT POSTS STATUS:")
print("-" * 70)
all_posts = sorted(pm.get_all_posts(), reverse=True)[:20]
for post_id in all_posts:
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    ig = pm.is_posted(post_id, "instagram")
    fb = pm.is_posted(post_id, "facebook")
    yt = pm.is_posted(post_id, "youtube")
    
    # Check if post is scheduled but already posted
    is_scheduled = any(s.post_id == post_id for s in all_schedules)
    
    if is_scheduled and (ig or fb or yt):
        title = meta.get('original_title', 'Unknown')[:50]
        print(f"  ⚠️  Post {post_id}: {title}")
        print(f"       Scheduled AND posted: IG={ig}, FB={fb}, YT={yt}")
        print(f"       ⚠️ RISK: Will be posted again!")

# 4. Check metadata integrity
print("\n4. METADATA INTEGRITY CHECK:")
print("-" * 70)
posts_without_urls = []
posts_without_platforms = []
for post_id in pm.get_all_posts():
    meta = pm.get_metadata(post_id)
    if not meta:
        continue
    
    if not meta.get('original_url') and not meta.get('link'):
        posts_without_urls.append(post_id)
    
    if not meta.get('posted_platforms'):
        # Check if actually posted
        if pm.is_posted(post_id, "instagram") or pm.is_posted(post_id, "facebook") or pm.is_posted(post_id, "youtube"):
            posts_without_platforms.append(post_id)

if posts_without_urls:
    print(f"  ⚠️  {len(posts_without_urls)} posts missing URLs (duplicate detection weakened)")
if posts_without_platforms:
    print(f"  ⚠️  {len(posts_without_platforms)} posted posts missing posted_platforms metadata")
    print(f"       This indicates metadata overwrite bug affected these posts")
else:
    print("  ✅ Metadata integrity OK")

print("\n" + "="*70)
print("SAFETY SUMMARY:")
print("="*70)

if duplicates or (pending and any(pm.is_posted(s.post_id, "instagram") or pm.is_posted(s.post_id, "facebook") or pm.is_posted(s.post_id, "youtube") for s in pending)):
    print("  ⚠️  RISKS DETECTED - ACTION REQUIRED")
else:
    print("  ✅ No immediate risks detected")

print("="*70)


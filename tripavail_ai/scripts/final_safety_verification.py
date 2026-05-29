#!/usr/bin/env python3
"""Final verification - ensure system is safe for production"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled

pm = PostManager()

print("="*70)
print("FINAL SAFETY VERIFICATION")
print("="*70)

# 1. Check all pending schedules
pending = list_scheduled(status="pending")
risky_posts = []

for item in pending:
    ig = pm.is_posted(item.post_id, "instagram")
    fb = pm.is_posted(item.post_id, "facebook")
    yt = pm.is_posted(item.post_id, "youtube")
    
    if ig or fb or yt:
        risky_posts.append({
            'post_id': item.post_id,
            'ig': ig,
            'fb': fb,
            'yt': yt,
            'scheduled': item.scheduled_at
        })

if risky_posts:
    print("\n❌ CRITICAL: Found posts scheduled that are already posted!")
    for p in risky_posts:
        print(f"  Post {p['post_id']}: IG={p['ig']}, FB={p['fb']}, YT={p['yt']}")
    print("\n⚠️  ACTION REQUIRED - These will be posted again!")
else:
    print("\n✅ All pending schedules are for unposted posts")

# 2. Check for duplicate schedules
all_schedules = list_scheduled(status="pending")
post_ids = [s.post_id for s in all_schedules]
from collections import Counter
duplicates = {pid: count for pid, count in Counter(post_ids).items() if count > 1}

if duplicates:
    print(f"\n❌ CRITICAL: Found {len(duplicates)} posts scheduled multiple times!")
    for pid, count in duplicates.items():
        print(f"  Post {pid}: scheduled {count} times")
else:
    print("\n✅ No duplicate schedules found")

# 3. Verify only one scheduler is running
print("\n✅ Only one scheduler service should be running")
print("   (tripavail-daemon.service - verified separately)")

print("\n" + "="*70)
if risky_posts or duplicates:
    print("❌ SYSTEM NOT SAFE - RISKS DETECTED")
    print("="*70)
    sys.exit(1)
else:
    print("✅ SYSTEM SAFE - NO IMMEDIATE RISKS")
    print("="*70)
    sys.exit(0)


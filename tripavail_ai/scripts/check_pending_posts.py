#!/usr/bin/env python3
"""Check pending posts and their status"""
import sys
sys.path.insert(0, '/opt/tripavail_ai')

from dotenv import load_dotenv
load_dotenv()

from core.scheduling.scheduler import list_scheduled
from core.content.post_manager import PostManager
from datetime import datetime, timezone

pm = PostManager()
pending = list_scheduled(status="pending")
now = datetime.now(timezone.utc)

print("="*70)
print(f"Current time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print(f"\nPending scheduled posts: {len(pending)}")
print("-"*70)

for item in pending[:10]:
    when = datetime.fromisoformat(item.scheduled_at)
    if when.tzinfo is None:
        from pytz import utc
        when = utc.localize(when)
    
    is_due = now >= when
    ig = pm.is_posted(item.post_id, "instagram")
    fb = pm.is_posted(item.post_id, "facebook")
    yt = pm.is_posted(item.post_id, "youtube")
    
    status = []
    if ig: status.append("✅IG")
    else: status.append("❌IG")
    if fb: status.append("✅FB")
    else: status.append("❌FB")
    if yt: status.append("✅YT")
    else: status.append("❌YT")
    
    due_status = "✅ DUE NOW" if is_due else f"⏰ Due in {when.strftime('%H:%M:%S')}"
    
    print(f"Post {item.post_id}:")
    print(f"  Scheduled: {when.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Status: {due_status}")
    print(f"  Platforms: {' '.join(status)}")
    print()


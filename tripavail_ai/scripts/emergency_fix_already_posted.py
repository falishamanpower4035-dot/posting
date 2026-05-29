#!/usr/bin/env python3
"""EMERGENCY FIX: Mark all already-posted scheduled posts as done"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled, mark_done

pm = PostManager()

print("="*70)
print("EMERGENCY FIX: MARKING ALREADY-POSTED SCHEDULES AS DONE")
print("="*70)

pending = list_scheduled(status="pending")
fixed_count = 0

for item in pending:
    ig = pm.is_posted(item.post_id, "instagram")
    fb = pm.is_posted(item.post_id, "facebook")
    yt = pm.is_posted(item.post_id, "youtube")
    
    if ig or fb or yt:
        meta = pm.get_metadata(item.post_id)
        title = meta.get('original_title', 'Unknown')[:50] if meta else 'Unknown'
        
        print(f"\n⚠️  Post {item.post_id}: {title}")
        print(f"   Already posted: IG={ig}, FB={fb}, YT={yt}")
        print(f"   Scheduled: {item.scheduled_at[:19]}")
        print(f"   ✅ Marking as done to prevent duplicate posting...")
        
        mark_done(item.post_id)
        fixed_count += 1

print(f"\n" + "="*70)
print(f"✅ FIXED {fixed_count} posts that would have been posted again")
print("="*70)


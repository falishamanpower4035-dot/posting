#!/usr/bin/env python3
"""Check Post 050 status immediately"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import mark_done

pm = PostManager()

print("="*70)
print("POST 050 EMERGENCY CHECK")
print("="*70)

meta = pm.get_metadata('050')
if meta:
    print(f"\nTitle: {meta.get('original_title', 'N/A')[:70]}")
    
    ig = pm.is_posted('050', 'instagram')
    fb = pm.is_posted('050', 'facebook')
    yt = pm.is_posted('050', 'youtube')
    
    print(f"\nCurrent Status:")
    print(f"  IG: {ig}")
    print(f"  FB: {fb}")
    print(f"  YT: {yt}")
    
    posted_platforms = meta.get('posted_platforms', {})
    if posted_platforms:
        print(f"\nPosted Platforms Recorded:")
        for platform, info in posted_platforms.items():
            posted_at = info.get('posted_at', 'N/A')[:19] if isinstance(info, dict) else 'N/A'
            print(f"  {platform}: {posted_at}")
    
    # If posted to ANY platform, mark as done immediately
    if ig or fb or yt:
        print(f"\n⚠️  Post 050 already posted to at least one platform!")
        print(f"   Marking as done IMMEDIATELY to prevent duplicate...")
        mark_done('050')
        print(f"   ✅ Marked as done")
    else:
        print(f"\n✅ Post 050 not posted yet (safe to post)")
else:
    print("\n❌ Post 050 metadata not found")

print("\n" + "="*70)


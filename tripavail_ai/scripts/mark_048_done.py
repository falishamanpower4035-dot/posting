#!/usr/bin/env python3
"""Check and mark Post 048 as done"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import mark_done

pm = PostManager()

print("="*70)
print("POST 048 (WELLNESS WONDER) STATUS")
print("="*70)

meta = pm.get_metadata('048')
if meta:
    print(f"\nTitle: {meta.get('original_title', 'N/A')[:70]}")
    print(f"URL: {meta.get('original_url', 'N/A')[:70] if meta.get('original_url') else 'NO URL'}")
    print(f"\nPosted Platforms:")
    posted_platforms = meta.get('posted_platforms', {})
    if posted_platforms:
        for platform, info in posted_platforms.items():
            posted_at = info.get('posted_at', 'N/A')[:19] if isinstance(info, dict) else 'N/A'
            print(f"  {platform}: {posted_at}")
    else:
        print("  None recorded (BUG: metadata overwrite)")
    
    print(f"\nCurrent Status:")
    print(f"  IG: {pm.is_posted('048', 'instagram')}")
    print(f"  FB: {pm.is_posted('048', 'facebook')}")
    print(f"  YT: {pm.is_posted('048', 'youtube')}")
    
    print(f"\n⚠️  Logs show Post 048 was posted 20+ times!")
    print(f"Marking as done to prevent further duplicates...")
    
    mark_done('048')
    print(f"\n✅ Post 048 marked as done")
else:
    print("\n❌ Post 048 metadata not found")

print("\n" + "="*70)


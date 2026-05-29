#!/usr/bin/env python3
"""Check Post 049 status and mark as done if needed"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import mark_done

pm = PostManager()

print("="*70)
print("POST 049 STATUS CHECK")
print("="*70)

meta = pm.get_metadata('049')
if not meta:
    print("\n❌ Post 049 metadata not found!")
else:
    print(f"\nPost 049:")
    print(f"  Title: {meta.get('original_title', 'N/A')[:70]}")
    print(f"  URL: {meta.get('original_url', 'N/A')[:70] if meta.get('original_url') else 'NO URL'}")
    print(f"  Created: {meta.get('created_at', 'N/A')[:19]}")
    
    print(f"\n  Posted Platforms:")
    posted_platforms = meta.get('posted_platforms', {})
    if posted_platforms:
        for platform, info in posted_platforms.items():
            posted_at = info.get('posted_at', 'N/A')[:19] if isinstance(info, dict) else 'N/A'
            url = info.get('url', 'N/A')
            print(f"    {platform}: {posted_at} - {url}")
    else:
        print("    None recorded")
    
    ig_posted = pm.is_posted('049', 'instagram')
    fb_posted = pm.is_posted('049', 'facebook')
    yt_posted = pm.is_posted('049', 'youtube')
    
    print(f"\n  Current Status:")
    print(f"    IG: {ig_posted}")
    print(f"    FB: {fb_posted}")
    print(f"    YT: {yt_posted}")
    
    if ig_posted or fb_posted or yt_posted:
        print(f"\n  ✅ Post 049 has been posted to at least one platform")
        print(f"     Marking as done to prevent further duplicate posts...")
        mark_done('049')
        print(f"     ✅ Marked as done")
    else:
        print(f"\n  ⚠️ Post 049 not posted to any platform")
        print(f"     (This might be correct if it's still scheduled)")

print("\n" + "="*70)


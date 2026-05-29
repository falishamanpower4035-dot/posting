#!/usr/bin/env python3
"""Comprehensive analysis: Two schedulers running simultaneously"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

pm = PostManager()

print("="*70)
print("CRITICAL ISSUE: TWO SCHEDULERS RUNNING SIMULTANEOUSLY")
print("="*70)

print("\n1. SERVICES RUNNING:")
print("-" * 70)
print("  ✅ tripavail-daemon.service → scripts/scheduler_daemon.py")
print("  ✅ tripavail-scheduler.service → smart_scheduler.py --run")
print("\n  ⚠️  BOTH SERVICES POST TO INSTAGRAM, FACEBOOK, YOUTUBE!")
print("  ⚠️  THIS CAUSES DUPLICATE POSTS!")

print("\n2. POST 048 STATUS (Wellness Wonder):")
print("-" * 70)
meta = pm.get_metadata('048')
if meta:
    print(f"  Title: {meta.get('original_title', 'N/A')[:60]}")
    print(f"  Posted Platforms: {meta.get('posted_platforms', {})}")
    print(f"  IG: {pm.is_posted('048', 'instagram')}")
    print(f"  FB: {pm.is_posted('048', 'facebook')}")
    print(f"  YT: {pm.is_posted('048', 'youtube')}")
    print(f"\n  ⚠️  Logs show Post 048 was posted 20+ times!")
else:
    print("  No metadata found")

print("\n3. ROOT CAUSE:")
print("-" * 70)
print("  • scheduler_daemon.py posts scheduled posts")
print("  • smart_scheduler.py ALSO posts at peak times")
print("  • Both check is_posted() BUT:")
print("    - Race condition: Both check before either posts")
print("    - Metadata overwrite bug (FIXED)")
print("    - File lock only prevents concurrent Facebook posts")
print("    - No coordination between the two schedulers")

print("\n4. SOLUTION:")
print("-" * 70)
print("  Option A: Disable smart_scheduler service (recommended)")
print("    → Only use scheduler_daemon.py")
print("  Option B: Make smart_scheduler use scheduler_daemon's schedule")
print("    → Don't post directly, just schedule")
print("  Option C: Add comprehensive file locks for all platforms")
print("    → More complex, higher risk")

print("\n" + "="*70)


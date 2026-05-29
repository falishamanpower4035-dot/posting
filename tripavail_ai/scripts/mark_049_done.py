#!/usr/bin/env python3
"""Mark Post 049 as done since it was posted multiple times"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import mark_done

pm = PostManager()

print("="*70)
print("MARKING POST 049 AS DONE")
print("="*70)

meta = pm.get_metadata('049')
if meta:
    print(f"\nPost 049: {meta.get('original_title', 'N/A')[:60]}")
    print(f"  Logs show it was posted multiple times")
    print(f"  Marking as done to prevent further duplicates...")
    
    mark_done('049')
    print(f"\n  ✅ Post 049 marked as done")
else:
    print("\n  ❌ Post 049 metadata not found")

print("\n" + "="*70)


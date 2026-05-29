#!/usr/bin/env python3
"""Check post numbering and potential issues"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

def main():
    pm = PostManager()
    posts = sorted(pm.get_all_posts())
    
    print("=" * 60)
    print("POST NUMBERING ANALYSIS")
    print("=" * 60)
    
    print(f"\nTotal posts: {len(posts)}")
    print(f"Post IDs: {posts[:20]}...")
    print(f"Latest 10: {posts[-10:]}")
    
    # Check for gaps
    print("\n📋 Checking for gaps in numbering:")
    if posts:
        post_nums = [int(p) for p in posts]
        gaps = []
        for i in range(min(post_nums), max(post_nums) + 1):
            if i not in post_nums:
                gaps.append(i)
        
        if gaps:
            print(f"  ⚠️ Found gaps: {gaps[:10]}")
        else:
            print("  ✅ No gaps found")
        
        # Check for duplicates
        duplicates = [pid for pid, count in defaultdict(int, {p: posts.count(p) for p in posts}).items() if count > 1]
        if duplicates:
            print(f"  ⚠️ Found duplicate IDs: {duplicates}")
        else:
            print("  ✅ No duplicate IDs")
    
    # Check posts with same title but different IDs
    print("\n📋 Posts with same title but different IDs:")
    by_title = defaultdict(list)
    for post_id in posts:
        meta = pm.get_metadata(post_id)
        if not meta:
            continue
        title = meta.get('original_title', '').strip()
        if title:
            normalized = ' '.join(title.lower().split())
            by_title[normalized].append(post_id)
    
    duplicate_titles = {k: v for k, v in by_title.items() if len(v) > 1}
    if duplicate_titles:
        print(f"  ⚠️ Found {len(duplicate_titles)} titles with multiple posts:")
        for title, post_ids in list(duplicate_titles.items())[:5]:
            print(f"    '{title[:60]}...': {post_ids}")
    else:
        print("  ✅ No duplicate titles")
    
    # Check what would be the next post ID
    print(f"\n📋 Next post ID calculation:")
    current_count = len(posts)
    next_id = current_count + 1
    print(f"  Current count: {current_count}")
    print(f"  Next ID would be: {next_id:03d}")
    
    # Check if there are any posts manually created with higher IDs
    if posts:
        max_id = max([int(p) for p in posts])
        print(f"  Maximum ID: {max_id:03d}")
        if max_id != current_count:
            print(f"  ⚠️ WARNING: Max ID ({max_id}) != count ({current_count})")
            print(f"     This suggests posts were created manually or gaps exist")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()


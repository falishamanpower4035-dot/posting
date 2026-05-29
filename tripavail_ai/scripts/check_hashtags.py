#!/usr/bin/env python3
"""Check hashtag preservation in posts"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

def main():
    pm = PostManager()
    posts = sorted(pm.get_all_posts())
    
    print("=" * 60)
    print("HASHTAG PRESERVATION CHECK")
    print("=" * 60)
    
    print(f"\nChecking latest 5 posts:\n")
    
    for post_id in posts[-5:]:
        meta = pm.get_metadata(post_id)
        if not meta:
            continue
        
        hashtags = meta.get("hashtags", [])
        print(f"Post {post_id}:")
        print(f"  Hashtags ({len(hashtags)}): {hashtags[:5]}")
        print(f"  Sample: {hashtags[0] if hashtags else 'N/A'}")
        print()
    
    print("=" * 60)
    print("\nHashtags should be preserved exactly as stored in metadata.")
    print("If hashtags are wrong, check caption generation or metadata storage.")

if __name__ == "__main__":
    main()


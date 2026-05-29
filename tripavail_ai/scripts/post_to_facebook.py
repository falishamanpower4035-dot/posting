#!/usr/bin/env python3
"""
Post TripAvail videos to Facebook automatically
"""

import json
from pathlib import Path
from loguru import logger
from modules.social_media.facebook_poster import FacebookPoster

def main():
    print("\n" + "="*70)
    print("AUTOMATED FACEBOOK POSTING - TRIPAVAIL AI")
    print("="*70 + "\n")
    
    # Initialize Facebook poster
    fb_poster = FacebookPoster()
    
    # Test connection first
    print("Testing Facebook connection...")
    if not fb_poster.test_connection():
        print("ERROR: Cannot connect to Facebook. Check your token.")
        return
    
    print("SUCCESS: Connected to Facebook!\n")
    
    # Load posts data
    posts_file = Path("data/posts.json")
    if not posts_file.exists():
        print("ERROR: No posts.json found. Run the pipeline first.")
        return
    
    with open(posts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data['posts']
    print(f"Found {len(posts)} posts to process\n")
    
    # Process each post
    for i, post in enumerate(posts, 1):
        post_id = post.get('topic_id')
        title = post.get('original_title', '')[:60]
        caption = post.get('caption', '')
        hashtags = post.get('hashtags', [])
        
        print(f"[POST #{i}/{len(posts)}]")
        print(f"Title: {title}...")
        print(f"Caption: {caption[:70]}...")
        
        # Check if video exists
        video_path = Path(f"data/videos/reel_{post_id}_final.mp4")
        if not video_path.exists():
            print(f"  ERROR: Video not found: {video_path.name}")
            continue
        
        # Prepare Facebook caption
        fb_caption = caption
        if hashtags:
            hashtag_text = " ".join(hashtags[:10])  # Limit hashtags for Facebook
            fb_caption = f"{caption}\n\n{hashtag_text}"
        
        print(f"  Posting to Facebook...")
        
        # Post to Facebook
        success = fb_poster.post_video(video_path, fb_caption, hashtags)
        
        if success:
            print(f"  SUCCESS: Posted to Facebook!")
        else:
            print(f"  ERROR: Failed to post to Facebook")
        
        print("-" * 70 + "\n")
    
    print("="*70)
    print("FACEBOOK POSTING COMPLETE!")
    print("="*70)
    print("\nCheck your Facebook page to see the posted videos!")
    print("="*70)

if __name__ == "__main__":
    main()

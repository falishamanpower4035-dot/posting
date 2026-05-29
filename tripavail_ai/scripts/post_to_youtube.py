#!/usr/bin/env python3
"""
Post TripAvail videos to YouTube automatically
"""

import json
from pathlib import Path
from loguru import logger
from core.social.platforms.youtube_uploader import YouTubeUploader

def main():
    print("\n" + "="*70)
    print("AUTOMATED YOUTUBE UPLOADING - TRIPAVAIL AI")
    print("="*70 + "\n")
    
    # Initialize YouTube uploader
    youtube_uploader = YouTubeUploader()
    
    # Test connection first
    print("Testing YouTube connection...")
    if not youtube_uploader.test_connection():
        print("ERROR: Cannot connect to YouTube. Please authenticate first.")
        print("The browser will open for Google OAuth authentication.")
        return
    
    print("SUCCESS: Connected to YouTube!\n")
    
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
        
        # Prepare YouTube metadata
        # Use truncate_title to ensure max 60 characters
        youtube_title = youtube_uploader.truncate_title(title, " | TripAvail")
        youtube_description = f"""{caption}

{chr(10).join(hashtags)}

#TripAvail #Travel #Adventure #LuxuryTravel #TravelVlog

Follow TripAvail for premium travel content and exclusive experiences around the world.

Website: https://tripavail.com
Instagram: @tripavail
Facebook: TripAvail Explore"""
        
        # Convert hashtags to YouTube tags
        youtube_tags = [tag.replace('#', '') for tag in hashtags[:10]]  # Limit to 10 tags
        youtube_tags.extend(['TripAvail', 'Travel', 'Adventure', 'Luxury Travel', 'Travel Vlog'])
        
        print(f"  Uploading to YouTube...")
        print(f"  Title: {youtube_title} ({len(youtube_title)} chars)")
        print(f"  Tags: {', '.join(youtube_tags[:5])}...")
        
        # Upload to YouTube
        video_id = youtube_uploader.upload_video(
            video_path=video_path,
            title=youtube_title,
            description=youtube_description,
            tags=youtube_tags,
            privacy_status="public"  # Set to public
        )
        
        if video_id:
            print(f"  SUCCESS: Uploaded to YouTube!")
            print(f"  Video ID: {video_id}")
            print(f"  URL: https://www.youtube.com/watch?v={video_id}")
        else:
            print(f"  ERROR: Failed to upload to YouTube")
        
        print("-" * 70 + "\n")
    
    print("="*70)
    print("YOUTUBE UPLOADING COMPLETE!")
    print("="*70)
    print("\nCheck your YouTube channel to see the uploaded videos!")
    print("="*70)

if __name__ == "__main__":
    main()

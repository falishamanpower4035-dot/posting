#!/usr/bin/env python3
"""
Direct YouTube upload using TripAvail credentials
"""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path
import json
from moviepy import VideoFileClip

# TripAvail YouTube Credentials — set via environment or .env file
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

def _is_vertical(video_path: Path) -> bool:
    """Return True if video is portrait (9:16-like)."""
    try:
        with VideoFileClip(str(video_path)) as clip:
            try:
                width, height = clip.size
            except Exception:
                # Fallback if .size not available
                width, height = getattr(clip, 'w', 0), getattr(clip, 'h', 0)
        return height > width
    except Exception:
        return True  # If unsure, don't block


def upload_video(video_path: Path, title: str, description: str, tags: list = None):
    """Upload video to YouTube"""
    try:
        print("="*70)
        print("UPLOADING TO YOUTUBE - TRIPAVAIL AI")
        print("="*70 + "\n")
        
        # Build credentials
        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/youtube"]  # Use basic YouTube scope
        )
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=creds)
        print("SUCCESS: YouTube service initialized")
        
        # Ensure vertical video for Shorts
        if not _is_vertical(video_path):
            print(f"ERROR: {video_path.name} is not vertical (9:16). Skipping upload.")
            return None

        # Video metadata
        request_body = {
            "snippet": {
                "categoryId": "22",  # People & Blogs
                "title": title[:95],
                "description": (description + "\n\n#Shorts").strip(),
                "tags": tags or []
            },
            "status": {
                "privacyStatus": "public"  # Set to public
            }
        }
        
        print(f"Uploading: {video_path.name}")
        print(f"Title: {title[:95]}")
        print(f"Tags: {', '.join(tags[:5]) if tags else 'None'}...")
        
        # Upload
        media_file = MediaFileUpload(str(video_path))
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )
        
        response = request.execute()
        
        if 'id' in response:
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"\nSUCCESS: Video uploaded!")
            print(f"Video ID: {video_id}")
            print(f"Video URL: {video_url}")
            return video_id
        else:
            print(f"ERROR: Upload failed: {response}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    """Upload all TripAvail videos to YouTube"""
    
    # Load posts data
    posts_file = Path("data/posts.json")
    if not posts_file.exists():
        print("ERROR: No posts.json found. Run the pipeline first.")
        return
    
    with open(posts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data['posts']
    print(f"Found {len(posts)} posts to upload\n")
    
    success_count = 0
    
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
        # Get YouTube title max length from config (default: 70)
        try:
            from config import settings
            max_title_length = getattr(settings, 'YOUTUBE_TITLE_MAX_LENGTH', 70)
        except ImportError:
            max_title_length = 70
        
        # Word-boundary aware truncation (avoid cutting words in half)
        suffix = " | TripAvail"
        suffix_length = len(suffix)
        max_title_chars = max_title_length - suffix_length
        
        if len(title) <= max_title_chars:
            # Title fits, no truncation needed
            youtube_title = f"{title}{suffix}"
        else:
            # Try to find a space near the limit (within 60-70 range to avoid incomplete words)
            min_title_chars = max(50, max_title_chars - 10)  # Allow 10 chars flexibility
            truncated = title[:max_title_chars]
            last_space = truncated.rfind(' ')
            
            if last_space >= min_title_chars:
                # Found a good space to cut at - cut before the space
                title_base = title[:last_space].strip()
            else:
                # No good space found, cut at max (might cut word, but better than nothing)
                title_base = title[:max_title_chars].strip()
            
            youtube_title = f"{title_base}{suffix}"
        
        # Final safety check - ensure we don't exceed max length
        if len(youtube_title) > max_title_length:
            available = max_title_length - suffix_length
            if available >= 50:
                temp_title = title[:available]
                last_space = temp_title.rfind(' ')
                if last_space >= 50:
                    title_base = title[:last_space].strip()
                else:
                    title_base = title[:available].strip()
            else:
                title_base = title[:available].strip()
            youtube_title = f"{title_base}{suffix}"
        
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
        
        # Upload to YouTube
        video_id = upload_video(
            video_path=video_path,
            title=youtube_title,
            description=youtube_description,
            tags=youtube_tags
        )
        
        if video_id:
            success_count += 1
            print(f"  SUCCESS: Uploaded to YouTube!")
        else:
            print(f"  ERROR: Failed to upload to YouTube")
        
        print("-" * 70 + "\n")
    
    print("="*70)
    print(f"YOUTUBE UPLOADING COMPLETE: {success_count}/{len(posts)} videos uploaded")
    print("="*70)
    print("\nCheck your YouTube channel to see the uploaded videos!")
    print("="*70)

if __name__ == "__main__":
    main()

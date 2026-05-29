#!/usr/bin/env python3
"""Test YouTube upload with the new token"""
import sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.social.platforms.youtube_uploader import YouTubeUploader
from core.content.post_manager import PostManager

def test_youtube():
    print("Testing YouTube connection...")
    yt = YouTubeUploader()
    
    # Test connection
    if yt.test_connection():
        print("✅ YouTube connection successful!")
    else:
        print("❌ YouTube connection failed")
        return False
    
    # Try to upload post_047
    post_id = "047"
    pm = PostManager()
    post = pm.get_post(post_id)
    
    if not post:
        print(f"❌ Post {post_id} not found")
        return False
    
    video_path = Path(f"data/posts/post_{post_id}/video/final.mp4")
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return False
    
    print(f"\n📤 Uploading post {post_id} to YouTube...")
    print(f"   Title: {post.get('original_title', 'No title')}")
    print(f"   Video: {video_path}")
    
    result = yt.upload_video(
        video_path=str(video_path),
        title=post.get('original_title', 'TripAvail Post') + " | TripAvail",
        description=post.get('caption', ''),
        tags=["travel", "tourism", "tripavail"],
        category_id="19",  # Travel & Events
        privacy_status="public"
    )
    
    if result:
        print(f"✅ Upload successful!")
        print(f"   Video ID: {result}")
        print(f"   URL: https://youtube.com/shorts/{result}")
        
        # Update metadata
        pm.mark_as_posted(post_id, "youtube", f"https://youtube.com/shorts/{result}")
        return True
    else:
        print("❌ Upload failed")
        return False

if __name__ == "__main__":
    success = test_youtube()
    sys.exit(0 if success else 1)


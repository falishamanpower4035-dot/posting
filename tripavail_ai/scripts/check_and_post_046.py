#!/usr/bin/env python3
"""Check post 046 status and post to YouTube if needed"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from core.content.post_manager import PostManager
from core.social.platforms.youtube_uploader import YouTubeUploader

pm = PostManager()
post_id = "046"

print(f"Checking Post {post_id} Status:")
print("=" * 60)

meta = pm.get_metadata(post_id)
if not meta:
    print(f"❌ No metadata found for post {post_id}")
    sys.exit(1)

print(f"Title: {meta.get('original_title', 'N/A')[:60]}")
print(f"Created: {meta.get('created_at', 'N/A')}")

posted_platforms = meta.get('posted_platforms', {})
print(f"\nPosting Status:")
for platform in ['instagram', 'facebook', 'youtube']:
    if platform in posted_platforms:
        posted_at = posted_platforms[platform].get('posted_at', 'Unknown')
        url = posted_platforms[platform].get('url', '')
        print(f"  {platform.upper()}: ✅ Posted at {posted_at}")
        if url:
            print(f"           URL: {url}")
    else:
        print(f"  {platform.upper()}: ❌ Not posted")

video = pm.get_final_video_path(post_id)
if not video.exists():
    print(f"\n❌ Video file not found: {video}")
    sys.exit(1)

print(f"\nVideo file exists: {video}")
print(f"Video size: {video.stat().st_size / (1024*1024):.1f} MB")

# Check if YouTube posting is needed
if not pm.is_posted(post_id, "youtube"):
    print(f"\n🔵 Post {post_id} is NOT posted to YouTube. Attempting to post now...")
    
    try:
        yt = YouTubeUploader()
        yt.authenticate()
        
        title = meta.get("original_title", "")
        caption = meta.get("caption", meta.get("context_caption", ""))
        hashtags = meta.get("hashtags", [])
        
        tags = [t.replace('#','') for t in hashtags[:10]] + ['TripAvail','Travel','Shorts']
        # Use truncate_title to ensure max 60 characters (will be truncated in upload_video too)
        yt_title = yt.truncate_title(title, " | TripAvail")
        yt_description = f"{caption}\n\n#Shorts\n\n" + " ".join(hashtags[:10])
        
        print(f"Uploading to YouTube...")
        print(f"  Title: {yt_title} ({len(yt_title)} chars)")
        print(f"  Tags: {tags[:5]}...")
        
        vid = yt.upload_video(video, title=yt_title, description=yt_description, tags=tags)
        
        if vid:
            pm.mark_as_posted(post_id, "youtube", f"https://youtube.com/shorts/{vid}")
            print(f"✅ Successfully posted to YouTube!")
            print(f"   Video ID: {vid}")
            print(f"   URL: https://youtube.com/shorts/{vid}")
        else:
            print(f"❌ Failed to upload to YouTube")
            
    except Exception as e:
        print(f"❌ Error posting to YouTube: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n✅ Post {post_id} is already posted to YouTube")


#!/usr/bin/env python3
"""
Simple YouTube upload test
"""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

# TripAvail YouTube Credentials — set via environment or .env file
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

def main():
    print("="*60)
    print("SIMPLE YOUTUBE UPLOAD TEST")
    print("="*60 + "\n")
    
    try:
        # Build credentials
        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=creds)
        print("SUCCESS: YouTube service initialized")
        
        # Test channel access
        response = youtube.channels().list(part='snippet', mine=True).execute()
        if 'items' in response and response['items']:
            channel = response['items'][0]
            print(f"Channel: {channel['snippet']['title']}")
            print(f"Channel ID: {channel['id']}")
        else:
            print("ERROR: No channel found")
            return
        
        # Test upload with existing video
        video_file = Path("data/videos/reel_1_final.mp4")
        if not video_file.exists():
            print(f"ERROR: Video file not found: {video_file}")
            return
        
        print(f"\nUploading video: {video_file.name}")
        
        # Video metadata
        request_body = {
            "snippet": {
                "categoryId": "22",  # People & Blogs
                "title": "Test Upload from TripAvail AI - Bangkok Night Market",
                "description": """Discover the magic of Bangkok's night markets! 

As twilight falls, the aroma of jasmine fills the air, and the vibrant night market pulses with life. This is where your senses ignite.

#TripAvail #Bangkok #NightMarket #Travel #Adventure #Thailand #TravelVlog #LuxuryTravel

Follow TripAvail for premium travel content and exclusive experiences around the world.

Website: https://tripavail.com
Instagram: @tripavail
Facebook: TripAvail Explore""",
                "tags": ["TripAvail", "Bangkok", "Night Market", "Travel", "Adventure", "Thailand", "Travel Vlog", "Luxury Travel"]
            },
            "status": {
                "privacyStatus": "unlisted"  # Start as unlisted for testing
            }
        }
        
        # Upload
        media_file = MediaFileUpload(str(video_file))
        request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_file
        )
        
        response = request.execute()
        
        if 'id' in response:
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"SUCCESS: Video uploaded!")
            print(f"Video ID: {video_id}")
            print(f"Video URL: {video_url}")
        else:
            print(f"ERROR: Upload failed: {response}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("\n" + "="*60)
    print("YOUTUBE TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()

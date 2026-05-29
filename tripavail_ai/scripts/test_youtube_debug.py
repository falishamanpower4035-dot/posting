#!/usr/bin/env python3
"""
Debug YouTube API connection and scopes
"""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# TripAvail YouTube Credentials — set via environment or .env file
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

def test_different_scopes():
    """Test different scope combinations"""
    
    scopes_to_test = [
        ["https://www.googleapis.com/auth/youtube.upload"],
        ["https://www.googleapis.com/auth/youtube.readonly"],
        ["https://www.googleapis.com/auth/youtube"],
        ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"],
        ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"]
    ]
    
    for i, scopes in enumerate(scopes_to_test, 1):
        print(f"\n{'='*60}")
        print(f"TEST #{i}: Testing scopes: {scopes}")
        print(f"{'='*60}")
        
        try:
            # Build credentials
            creds = Credentials(
                None,
                refresh_token=REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scopes=scopes
            )
            
            # Build YouTube service
            youtube = build('youtube', 'v3', credentials=creds)
            print("SUCCESS: YouTube service initialized")
            
            # Test 1: Get channel info
            try:
                response = youtube.channels().list(part='snippet', mine=True).execute()
                if 'items' in response and response['items']:
                    channel = response['items'][0]
                    print(f"SUCCESS: Channel access - {channel['snippet']['title']}")
                else:
                    print("WARNING: No channel found")
            except Exception as e:
                print(f"ERROR: Channel access failed - {e}")
            
            # Test 2: Try to upload (if upload scope is present)
            if "youtube.upload" in scopes:
                try:
                    # Just test the upload endpoint without actually uploading
                    print("Testing upload endpoint...")
                    # This will fail but give us more info about the error
                    youtube.videos().insert(
                        part="snippet,status",
                        body={"snippet": {"title": "Test"}},
                        media_body=None
                    ).execute()
                except Exception as e:
                    print(f"Upload test error: {e}")
            
        except Exception as e:
            print(f"ERROR: {e}")

def test_token_info():
    """Test what we can get from the token"""
    print(f"\n{'='*60}")
    print("TOKEN INFORMATION TEST")
    print(f"{'='*60}")
    
    try:
        # Try to get token info
        import requests
        
        # Test the token directly
        url = "https://www.googleapis.com/oauth2/v1/tokeninfo"
        params = {
            'access_token': 'dummy'  # We'll use the refresh token flow
        }
        
        print("Testing token validation...")
        
        # Build credentials and try to refresh
        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        
        # Try to refresh the token
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        
        print(f"SUCCESS: Token refreshed")
        print(f"Access token: {creds.token[:20]}...")
        print(f"Expires: {creds.expiry}")
        print(f"Valid: {creds.valid}")
        print(f"Scopes: {creds.scopes}")
        
    except Exception as e:
        print(f"ERROR: Token test failed - {e}")

def main():
    print("YOUTUBE API DEBUG TEST")
    print("Testing different scopes and token validation")
    
    test_different_scopes()
    test_token_info()
    
    print(f"\n{'='*60}")
    print("DEBUG TEST COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

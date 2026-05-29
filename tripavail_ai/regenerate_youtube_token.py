#!/usr/bin/env python3
"""
Regenerate YouTube Refresh Token
This script helps you get a new refresh token for YouTube API
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required for YouTube uploads
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.upload'
]

def main():
    print("\n" + "="*60)
    print("  YouTube Token Regeneration")
    print("="*60 + "\n")
    
    # Check for client secret file
    client_secret_file = Path("client_secret.json")
    
    if not client_secret_file.exists():
        print("❌ Error: client_secret.json not found")
        print("\nPlease download it from:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Find your OAuth 2.0 Client ID")
        print("3. Download JSON and save as 'client_secret.json'")
        return
    
    print("🔐 Starting OAuth flow...")
    print("   This will open a browser window")
    print("   Please log in with: tripavail92@gmail.com")
    print("")
    
    try:
        # Run OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_file), 
            SCOPES
        )
        
        credentials = flow.run_local_server(
            port=8080,
            prompt='consent',
            authorization_prompt_message='Opening browser for YouTube authorization...'
        )
        
        print("\n✅ Authorization successful!")
        print("\nYour new YouTube credentials:")
        print("="*60)
        print(f"YOUTUBE_CLIENT_ID = \"{credentials.client_id}\"")
        print(f"YOUTUBE_CLIENT_SECRET = \"{credentials.client_secret}\"")
        print(f"YOUTUBE_REFRESH_TOKEN = \"{credentials.refresh_token}\"")
        print("="*60)
        
        print("\n📝 Next steps:")
        print("1. Copy the values above")
        print("2. Update config/settings.py with these new values")
        print("3. Restart the bot services on your droplet")
        print("")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you're using the correct Google account")
        print("- Check that OAuth consent screen is configured")
        print("- Ensure YouTube Data API v3 is enabled")

if __name__ == "__main__":
    main()


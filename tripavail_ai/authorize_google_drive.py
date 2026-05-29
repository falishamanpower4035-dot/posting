#!/usr/bin/env python3
"""
Manual Google Drive Authorization
This will guide you through the OAuth process step by step.
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def authorize():
    print("=" * 70)
    print("Google Drive Authorization")
    print("=" * 70)
    
    # Check for client secret file
    secret_file = "client_secret_1055967706845-fsq2hnofrsrjvd78rgi0dg82p4hjh7es.apps.googleusercontent.com.json"
    if not Path(secret_file).exists():
        secret_file = "client_secret.json"
    
    if not Path(secret_file).exists():
        print(f"❌ Error: {secret_file} not found!")
        return
    
    print(f"\n✅ Found: {secret_file}")
    print("\nStarting OAuth flow...")
    print("A browser window should open automatically.")
    print("If it doesn't open, copy the URL that appears and paste it in your browser.")
    print("\n" + "=" * 70)
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
        
        # This will open browser automatically or show a URL
        creds = flow.run_local_server(port=0)
        
        # Save the token
        token_path = Path("drive_token.json")
        token_path.write_text(creds.to_json())
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! Authorization complete!")
        print("=" * 70)
        print(f"\nToken saved to: {token_path}")
        print("\nYou can now upload videos to Google Drive!")
        
    except Exception as e:
        print(f"\n❌ Error during authorization: {e}")
        print("\nPossible issues:")
        print("1. Make sure tripavail92@gmail.com is added as a test user")
        print("2. Check your Google Cloud Console: https://console.cloud.google.com/")
        print("3. Ensure you're logged in with the correct Google account")

if __name__ == "__main__":
    authorize()


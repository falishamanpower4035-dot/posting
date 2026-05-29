#!/usr/bin/env python3
"""
Manual Google Drive Authorization - Console Based
You'll copy a URL, authorize in browser, then paste the code back.
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def authorize_manual():
    print("=" * 70)
    print("Google Drive Manual Authorization")
    print("=" * 70)
    
    # Check for client secret file
    secret_file = "client_secret_1055967706845-fsq2hnofrsrjvd78rgi0dg82p4hjh7es.apps.googleusercontent.com.json"
    if not Path(secret_file).exists():
        secret_file = "client_secret.json"
    
    if not Path(secret_file).exists():
        print(f"❌ Error: {secret_file} not found!")
        return
    
    print(f"\n✅ Found: {secret_file}")
    print("\nStarting manual OAuth flow...")
    print("\n" + "=" * 70)
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            secret_file, 
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Manual copy-paste flow
        )
        
        # Get the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print("\nSTEP 1: Open this URL in your browser:")
        print("-" * 70)
        print(auth_url)
        print("-" * 70)
        
        print("\nSTEP 2: Log in with: tripavail92@gmail.com")
        print("\nSTEP 3: After authorizing, Google will show you an authorization code.")
        print("        Copy that code and paste it here.")
        print("\n" + "=" * 70)
        
        # Get the code from user
        code = input("\nPaste the authorization code here: ").strip()
        
        if not code:
            print("❌ No code provided. Exiting.")
            return
        
        # Exchange code for credentials
        print("\nExchanging code for credentials...")
        flow.fetch_token(code=code)
        creds = flow.credentials
        
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
        print("2. The authorization code might have expired - try again")
        print("3. Check your Google Cloud Console: https://console.cloud.google.com/")

if __name__ == "__main__":
    authorize_manual()


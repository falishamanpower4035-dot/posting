#!/usr/bin/env python3
"""
Helper script to generate a new YouTube refresh token.
Run this locally and update the YOUTUBE_REFRESH_TOKEN in .env
"""

import json
from pathlib import Path

# Load client secret
client_secret_file = Path("client_secret.json")
if not client_secret_file.exists():
    print("❌ client_secret.json not found!")
    print("Please ensure client_secret.json is in the project root.")
    exit(1)

with open(client_secret_file) as f:
    client_data = json.load(f)
    client_id = client_data["web"]["client_id"]
    client_secret = client_data["web"]["client_secret"]

print("=" * 70)
print("YouTube Refresh Token Generator")
print("=" * 70)
print()
print("Follow these steps to get a new refresh token:")
print()
print("1. Go to: https://developers.google.com/oauthplayground")
print()
print("2. Click the gear icon (⚙️) in the top right")
print()
print("3. Check 'Use your own OAuth credentials'")
print()
print(f"4. Enter OAuth Client ID: {client_id}")
print()
print(f"5. Enter OAuth Client secret: {client_secret}")
print()
print("6. Close the settings")
print()
print("7. In 'Step 1', find and select:")
print("   - YouTube Data API v3")
print("   - https://www.googleapis.com/auth/youtube.upload")
print()
print("8. Click 'Authorize APIs'")
print()
print("9. Sign in with your YouTube account (tripavail92@gmail.com)")
print()
print("10. Click 'Exchange authorization code for tokens'")
print()
print("11. Copy the 'Refresh token' value")
print()
print("12. Update your .env file:")
print("    YOUTUBE_REFRESH_TOKEN=<paste_the_refresh_token_here>")
print()
print("13. Restart the bot services on the droplet")
print()
print("=" * 70)


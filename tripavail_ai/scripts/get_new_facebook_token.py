#!/usr/bin/env python3
"""
Get New Facebook Long-Lived Token
Step-by-step guide to get a fresh 60-day token
"""

import os
import requests
import json
from pathlib import Path

# Your Facebook App credentials — set via environment or .env file
APP_ID = os.getenv("FACEBOOK_APP_ID", "")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")

def get_long_lived_token(short_token):
    """Exchange short-lived token for long-lived token"""
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': APP_ID,
        'client_secret': APP_SECRET,
        'fb_exchange_token': short_token
    }
    
    print("\nRequesting long-lived token from Facebook...")
    response = requests.get(url, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if 'access_token' in data:
            return data['access_token'], data.get('expires_in', 'Unknown')
    
    print(f"ERROR: {response.status_code}")
    print(f"Response: {response.text}")
    return None, None

def update_config(token):
    """Update config/settings.py with new token"""
    config_file = Path("config/settings.py")
    
    if not config_file.exists():
        print(f"ERROR: Config file not found: {config_file}")
        return False
    
    content = config_file.read_text(encoding='utf-8')
    
    # Find and replace the token line
    lines = content.split('\n')
    updated = False
    
    for i, line in enumerate(lines):
        if line.startswith('FACEBOOK_GRAPH_TOKEN = '):
            lines[i] = f'FACEBOOK_GRAPH_TOKEN = "{token}"'
            updated = True
            break
    
    if updated:
        config_file.write_text('\n'.join(lines), encoding='utf-8')
        print(f"\nConfig updated: {config_file}")
        return True
    else:
        print("\nERROR: Could not find FACEBOOK_GRAPH_TOKEN in config")
        return False

def main():
    print("="*70)
    print("FACEBOOK LONG-LIVED TOKEN GENERATOR")
    print("="*70)
    print()
    print("STEP 1: Get a short-lived token from Facebook")
    print("Visit: https://developers.facebook.com/tools/explorer/")
    print()
    print("1. Select your app: 'MMA Adventures' (App ID: 1470899567366836)")
    print("2. Click 'Generate Access Token'")
    print("3. Grant permissions when prompted")
    print("4. Copy the token that appears")
    print()
    print("="*70)
    print()
    
    short_token = input("Paste your short-lived token here: ").strip()
    
    if not short_token:
        print("ERROR: No token provided")
        return
    
    print(f"\nShort token: {short_token[:30]}...")
    
    # Exchange for long-lived token
    long_token, expires_in = get_long_lived_token(short_token)
    
    if long_token:
        print(f"\nSUCCESS!")
        print(f"Long-lived token: {long_token[:30]}...")
        print(f"Expires in: {expires_in} seconds (~{int(expires_in)//86400} days)")
        
        # Update config
        if update_config(long_token):
            print("\nDONE! Your bot is ready to post to Facebook.")
            print("\nNext: Run 'python run_hourly_bot.py' to start the bot")
        else:
            print("\nManually update config/settings.py with this token:")
            print(long_token)
    else:
        print("\nFAILED to get long-lived token.")
        print("Check that your short-lived token is valid.")

if __name__ == "__main__":
    main()


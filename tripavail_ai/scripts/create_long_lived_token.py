#!/usr/bin/env python3
"""
Create Long-Lived Facebook Graph API Token
Exchanges short-lived token for long-lived token (60 days)
"""

import os
import requests
import json
from pathlib import Path
from loguru import logger

# Your Facebook App credentials — set via environment or .env file
APP_ID = os.getenv("FACEBOOK_APP_ID", "")
APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
SHORT_LIVED_TOKEN = os.getenv("FACEBOOK_SHORT_LIVED_TOKEN", "")

def get_long_lived_token():
    """
    Exchange short-lived token for long-lived token
    """
    try:
        print("="*70)
        print("CREATING LONG-LIVED FACEBOOK TOKEN")
        print("="*70 + "\n")
        
        print(f"App ID: {APP_ID}")
        print(f"App Secret: {APP_SECRET[:10]}...")
        print(f"Short Token: {SHORT_LIVED_TOKEN[:20]}...")
        print()
        
        # Facebook Graph API endpoint for long-lived tokens
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': APP_ID,
            'client_secret': APP_SECRET,
            'fb_exchange_token': SHORT_LIVED_TOKEN
        }
        
        print("Requesting long-lived token from Facebook...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'access_token' in data:
                long_lived_token = data['access_token']
                expires_in = data.get('expires_in', 'Unknown')
                
                print("SUCCESS: Long-lived token created!")
                print(f"Token: {long_lived_token}")
                print(f"Expires in: {expires_in} seconds ({int(expires_in/86400)} days)")
                print()
                
                # Save token to config
                save_token_to_config(long_lived_token)
                
                # Test the new token
                test_long_lived_token(long_lived_token)
                
                return long_lived_token
            else:
                print("ERROR: No access token in response")
                print(f"Response: {data}")
                return None
        else:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def save_token_to_config(token):
    """
    Save long-lived token to configuration
    """
    try:
        config_file = Path("config/settings.py")
        
        if config_file.exists():
            # Read current config
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace token
            old_token = os.getenv("FACEBOOK_SHORT_LIVED_TOKEN", "")
            new_content = content.replace(old_token, token) if old_token else content
            
            # Write updated config
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("SUCCESS: Token saved to config/settings.py")
        else:
            print("WARNING: Config file not found, please update manually")
            
    except Exception as e:
        print(f"WARNING: Could not save to config: {e}")

def test_long_lived_token(token):
    """
    Test the long-lived token by getting page info
    """
    try:
        print("Testing long-lived token...")
        
        url = f"https://graph.facebook.com/v18.0/me"
        params = {
            'access_token': token,
            'fields': 'id,name,category,fan_count'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("SUCCESS: Token test successful!")
            print(f"Page: {data.get('name', 'Unknown')}")
            print(f"Page ID: {data.get('id', 'Unknown')}")
            print(f"Category: {data.get('category', 'Unknown')}")
            print(f"Fan Count: {data.get('fan_count', 'Unknown')}")
        else:
            print(f"ERROR: Token test failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ERROR: Token test error: {e}")

def get_page_access_token():
    """
    Get page access token for posting (if needed)
    """
    try:
        print("\n" + "="*50)
        print("GETTING PAGE ACCESS TOKEN")
        print("="*50)
        
        # First get user's pages
        url = f"https://graph.facebook.com/v18.0/me/accounts"
        params = {
            'access_token': SHORT_LIVED_TOKEN
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get('data', [])
            
            if pages:
                print(f"Found {len(pages)} pages:")
                for page in pages:
                    print(f"  - {page.get('name')} (ID: {page.get('id')})")
                    print(f"    Access Token: {page.get('access_token', 'None')[:20]}...")
            else:
                print("No pages found")
        else:
            print(f"ERROR: Failed to get pages: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: Error getting pages: {e}")

def main():
    """Main function"""
    print("Facebook Long-Lived Token Generator")
    print("This will exchange your short-lived token for a 60-day token\n")
    
    # Create long-lived token
    long_token = get_long_lived_token()
    
    if long_token:
        # Get page access token info
        get_page_access_token()
        
        print("\n" + "="*70)
        print("LONG-LIVED TOKEN CREATION COMPLETE!")
        print("="*70)
        print("\nYour new long-lived token:")
        print(f"{long_token}")
        print("\nThis token will last for 60 days.")
        print("Save it securely and update your configuration.")
        print("="*70)
    else:
        print("\nERROR: Failed to create long-lived token")
        print("Please check your App ID, App Secret, and short-lived token")

if __name__ == "__main__":
    main()

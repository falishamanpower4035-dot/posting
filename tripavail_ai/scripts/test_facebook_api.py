#!/usr/bin/env python3
"""
Test Facebook API connection and permissions
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from config import settings

def test_facebook_connection():
    """Test Facebook API connection and get detailed error info"""
    print("Testing Facebook API connection...")
    
    # Test 1: Basic connection
    url = f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/me"
    params = {
        'access_token': settings.FACEBOOK_GRAPH_TOKEN,
        'fields': 'id,name,permissions'
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Connected to Facebook Page:")
            print(f"   ID: {data.get('id')}")
            print(f"   Name: {data.get('name')}")
            
            # Test permissions
            if 'permissions' in data:
                perms = data.get('permissions', {}).get('data', [])
                print(f"\n📋 Permissions:")
                for perm in perms:
                    status = "✅" if perm.get('status') == 'granted' else "❌"
                    print(f"   {status} {perm.get('permission')}: {perm.get('status')}")
        else:
            print(f"\n❌ Connection failed:")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Check if Reels endpoint is available
    print("\n\nTesting Reels endpoint...")
    url = f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/me/video_reels"
    data = {
        'access_token': settings.FACEBOOK_GRAPH_TOKEN,
        'upload_phase': 'start',
        'file_size': 1000  # Just testing, not actually uploading
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 400:
            print(f"\n✅ Reels endpoint accessible")
        else:
            error_data = response.json()
            print(f"\n❌ Reels endpoint error:")
            if 'error' in error_data:
                error = error_data['error']
                print(f"   Code: {error.get('code')}")
                print(f"   Message: {error.get('message')}")
                print(f"   Type: {error.get('type')}")
                if 'error_subcode' in error:
                    print(f"   Subcode: {error.get('error_subcode')}")
                if 'error_user_msg' in error:
                    print(f"   User Message: {error.get('error_user_msg')}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check regular video upload endpoint
    print("\n\nTesting regular video upload endpoint...")
    url = f"https://graph.facebook.com/{settings.FACEBOOK_API_VERSION}/me/videos"
    data = {
        'access_token': settings.FACEBOOK_GRAPH_TOKEN,
        'description': 'Test',
        'published': 'false'
    }
    
    try:
        # Just test the endpoint, don't actually upload
        response = requests.post(url, data=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 400:
            error_data = response.json()
            if 'error' in error_data:
                error = error_data['error']
                print(f"\n❌ Video upload error:")
                print(f"   Code: {error.get('code')}")
                print(f"   Message: {error.get('message')}")
                print(f"   Type: {error.get('type')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_facebook_connection()


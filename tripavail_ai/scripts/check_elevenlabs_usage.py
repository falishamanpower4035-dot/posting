#!/usr/bin/env python3
"""Check ElevenLabs API usage discrepancy"""

import requests
import os
from pathlib import Path

# Get API key
api_key = os.getenv("ELEVENLABS_API_KEY", "")

# Try to get user info and usage
headers = {"xi-api-key": api_key}

print("=== ELEVENLABS API USAGE CHECK ===\n")

# 1. Get user info
try:
    url = "https://api.elevenlabs.io/v1/user"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        user_data = resp.json()
        print("✅ User Account Info:")
        print(f"   Subscription: {user_data.get('subscription', {}).get('tier', 'Unknown')}")
        print(f"   Character count: {user_data.get('subscription', {}).get('character_count', 'N/A')}")
        print(f"   Character limit: {user_data.get('subscription', {}).get('character_limit', 'N/A')}")
        print()
    else:
        print(f"❌ Failed to get user info: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
except Exception as e:
    print(f"❌ Error getting user info: {e}")

# 2. Get usage history if available
try:
    url = "https://api.elevenlabs.io/v1/user/subscription"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        sub_data = resp.json()
        print("✅ Subscription Info:")
        for key, value in sub_data.items():
            print(f"   {key}: {value}")
        print()
except Exception as e:
    print(f"⚠️  Could not get subscription info: {e}")

# 3. Calculate expected vs actual
print("\n=== USAGE ANALYSIS ===")
print(f"Total Quota: 110,000 credits")
print(f"Remaining: 259 credits")
print(f"Used: 109,741 credits")
print(f"\nExpected Usage (23 posts):")
print(f"  TTS: 6,900 credits (23 × 300)")
print(f"  Music: 12,190 credits (23 × 530)")
print(f"  Total Expected: 19,090 credits")
print(f"\n⚠️  DISCREPANCY: 109,741 - 19,090 = 90,651 credits UNACCOUNTED FOR!")



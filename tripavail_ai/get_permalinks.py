#!/usr/bin/env python3
import sys, json
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))
from config import settings

api_version = getattr(settings, 'FACEBOOK_API_VERSION', 'v18.0')
base = 'https://graph.facebook.com/' + api_version
TOKEN = settings.FACEBOOK_GRAPH_TOKEN
IG_USER_ID = getattr(settings, 'INSTAGRAM_USER_ID', '')

out = {}

try:
    r = requests.get(base + '/' + IG_USER_ID + '/media', params={
        'access_token': TOKEN,
        'fields': 'id,permalink,caption,timestamp'
    }, timeout=30)
    out['ig_media'] = r.json()
except Exception as e:
    out['ig_error'] = str(e)

try:
    vid = '1744796712746709'
    r2 = requests.get(base + '/' + vid, params={
        'access_token': TOKEN,
        'fields': 'permalink_url,created_time,status'
    }, timeout=30)
    out['fb_video'] = r2.json()
except Exception as e:
    out['fb_error'] = str(e)

print(json.dumps(out, indent=2))

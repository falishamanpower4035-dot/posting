#!/usr/bin/env python3
"""Test duplicate detection"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

pm = PostManager()

# Test title
test_topic = {
    'title': 'Visa-free access to NZ via Australia for Chinese tourists',
    'link': '',
    'url': ''
}

print("Testing duplicate detection:")
print(f"Topic title: {test_topic['title']}")
print(f"Topic URL: {test_topic.get('link') or test_topic.get('url') or 'EMPTY'}")

result = pm.is_news_already_used(test_topic)
print(f"\nDuplicate check result: {result}")

# Check what titles are stored
print("\nChecking stored titles:")
used_titles = pm.get_used_news_titles()
normalized_test = ' '.join(test_topic['title'].lower().split())
print(f"Normalized test title: '{normalized_test}'")
print(f"\nFound {len(used_titles)} used titles")
for title in sorted(used_titles):
    if 'visa' in title.lower() or 'nz' in title.lower() or 'chinese' in title.lower():
        print(f"  '{title}'")
        if title == normalized_test:
            print(f"    ✅ MATCHES!")
        else:
            print(f"    ❌ Different (length: {len(title)} vs {len(normalized_test)})")


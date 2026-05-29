#!/usr/bin/env python3
"""Test duplicate detection"""
from core.content.post_manager import PostManager

pm = PostManager()
print(f"Used URLs: {len(pm.get_used_news_urls())}")
print(f"Used Titles: {len(pm.get_used_news_titles())}")

# Test with a sample topic
test_topic = {
    'title': 'Test News',
    'link': 'https://example.com/news'
}
print(f"\nTest topic already used: {pm.is_news_already_used(test_topic)}")


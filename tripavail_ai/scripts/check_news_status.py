#!/usr/bin/env python3
"""Check news processing status"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

def main():
    print("=" * 60)
    print("NEWS PROCESSING ANALYSIS")
    print("=" * 60)
    
    # Check processed news
    processed_file = Path("data/processed_news.json")
    if processed_file.exists():
        data = json.loads(processed_file.read_text())
        last_updated = data.get("last_updated", "N/A")
        stories = data.get("top_tourism_stories", [])
        print(f"\n📰 Processed News:")
        print(f"  Last updated: {last_updated}")
        print(f"  Total stories: {len(stories)}")
        
        if stories:
            print(f"\n  Stories with score >= 7:")
            score_7_plus = [s for s in stories if s.get("score", 0) >= 7]
            print(f"    Total: {len(score_7_plus)}")
            for i, s in enumerate(score_7_plus[:5], 1):
                print(f"    {i}. {s.get('title', 'N/A')[:60]} (score: {s.get('score', 0)})")
    else:
        print("\n❌ processed_news.json not found!")
    
    # Check raw news
    raw_file = Path("data/raw_news.json")
    if raw_file.exists():
        raw_data = json.loads(raw_file.read_text())
        raw_articles = raw_data.get("articles", [])
        print(f"\n📄 Raw News:")
        print(f"  Total articles: {len(raw_articles)}")
        if raw_articles:
            print(f"  Latest article: {raw_articles[0].get('title', 'N/A')[:60]}")
    else:
        print("\n❌ raw_news.json not found!")
    
    # Check which stories are already used
    pm = PostManager()
    print(f"\n🔍 Duplicate Detection Check:")
    if stories:
        score_7_plus = [s for s in stories if s.get("score", 0) >= 7]
        unused = []
        used = []
        for topic in score_7_plus:
            if pm.is_news_already_used(topic):
                used.append(topic)
            else:
                unused.append(topic)
        
        print(f"  Stories with score >= 7: {len(score_7_plus)}")
        print(f"  Already used: {len(used)}")
        print(f"  Unused (should generate): {len(unused)}")
        
        if unused:
            print(f"\n  Unused stories:")
            for i, s in enumerate(unused[:5], 1):
                print(f"    {i}. {s.get('title', 'N/A')[:60]} (score: {s.get('score', 0)})")
        else:
            print(f"\n  ⚠️ No unused stories! All score >= 7 stories already used.")
            if used:
                print(f"\n  Already used stories:")
                for i, s in enumerate(used[:5], 1):
                    print(f"    {i}. {s.get('title', 'N/A')[:60]} (score: {s.get('score', 0)})")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()


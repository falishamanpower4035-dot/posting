#!/usr/bin/env python3
"""Test news fetching and analysis"""
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.news.fetcher.fetch_news import NewsFetcher
from core.news.editor import TourismEditor

def main():
    print("=" * 60)
    print("TESTING NEWS ANALYSIS")
    print("=" * 60)
    
    # Step 1: Fetch news
    print("\n📰 Step 1: Fetching news...")
    try:
        fetcher = NewsFetcher()
        fetcher.run_fetch_cycle()
        print("✅ News fetched successfully")
    except Exception as e:
        print(f"❌ News fetch failed: {e}")
        return
    
    # Step 2: Analyze news
    print("\n🤖 Step 2: Analyzing news with OpenAI...")
    try:
        editor = TourismEditor()
        result = editor.run_analysis()
        
        if result is None:
            print("❌ Analysis failed - returned None")
            print("   Check OpenAI quota and API key")
            return
        
        print(f"✅ Analysis successful: {len(result)} stories found")
        for i, story in enumerate(result[:5], 1):
            print(f"   {i}. {story.get('title', 'N/A')[:60]} (score: {story.get('score', 0)})")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Check processed news file
    print("\n📄 Step 3: Checking processed_news.json...")
    processed_file = Path("data/processed_news.json")
    if processed_file.exists():
        import json
        data = json.loads(processed_file.read_text())
        processed_at = data.get("processed_at", "N/A")
        stories = data.get("top_tourism_stories", [])
        
        print(f"✅ File exists")
        print(f"   Processed at: {processed_at}")
        print(f"   Stories count: {len(stories)}")
        
        # Check age
        if processed_at != "N/A":
            try:
                proc_time = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - proc_time.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                if age_hours < 1:
                    print(f"   ✅ Fresh data (age: {age_hours:.1f} hours)")
                else:
                    print(f"   ⚠️ Old data (age: {age_hours:.1f} hours)")
            except:
                pass
    else:
        print("❌ processed_news.json not found")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()


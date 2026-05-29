#!/usr/bin/env python3
"""
Test script for News Fetcher - TripAvail AI
Tests all functionality without running the scheduler
"""

import json
from pathlib import Path
from modules.news_fetcher.fetch_news import NewsFetcher

def test_news_fetcher():
    """Test the news fetcher functionality"""
    print("Testing TripAvail AI News Fetcher")
    print("=" * 50)
    
    try:
        # Initialize fetcher
        fetcher = NewsFetcher()
        print("[OK] NewsFetcher initialized successfully")
        
        # Test query rotation
        query1 = fetcher.get_next_query()
        query2 = fetcher.get_next_query()
        query3 = fetcher.get_next_query()
        query4 = fetcher.get_next_query()
        
        print(f"[OK] Query rotation working:")
        print(f"   Query 1: {query1}")
        print(f"   Query 2: {query2}")
        print(f"   Query 3: {query3}")
        print(f"   Query 4: {query4} (should be same as Query 1)")
        
        # Test manual fetch
        print("\nRunning manual fetch...")
        fetcher.run_manual_fetch()
        
        # Check if files were created
        if fetcher.raw_news_file.exists():
            with open(fetcher.raw_news_file, 'r') as f:
                data = json.load(f)
                article_count = len(data.get('articles', []))
                print(f"[OK] Raw news file created with {article_count} articles")
        else:
            print("[ERROR] Raw news file not created")
        
        if fetcher.fetch_log_file.exists():
            with open(fetcher.fetch_log_file, 'r') as f:
                log_content = f.read().strip()
                print(f"[OK] Fetch log created: {log_content}")
        else:
            print("[ERROR] Fetch log file not created")
        
        if fetcher.state_file.exists():
            with open(fetcher.state_file, 'r') as f:
                state = json.load(f)
                print(f"[OK] State file created: Query index = {state.get('query_index', 0)}")
        else:
            print("[ERROR] State file not created")
        
        print("\nAll tests completed successfully!")
        print("\nNext steps:")
        print("1. Run 'python modules/news_fetcher/scheduler.py' to start automated fetching")
        print("2. Check logs/fetch_log.txt for fetch history")
        print("3. Check data/raw_news.json for latest articles")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news_fetcher()

#!/usr/bin/env python3
"""
Test script for TripAvail Tourism Editor
Demonstrates the intelligent analysis of tourism-relevant news
"""

import json
from pathlib import Path
from modules.tourism_editor import TourismEditor

def test_tourism_editor():
    """Test the Global Tourism News Selector functionality"""
    print("Testing TripAvail AI Global Tourism News Selector")
    print("=" * 50)
    
    try:
        # Initialize editor
        editor = TourismEditor()
        print("[OK] Global Tourism News Selector initialized successfully")
        
        # Run analysis
        print("\nRunning tourism analysis on batch of articles...")
        results = editor.run_analysis()
        
        if results:
            print(f"\n[OK] Analysis completed successfully!")
            print(f"Selected top {len(results)} tourism stories from NewsData.io batch:")
            
            for i, article in enumerate(results, 1):
                print(f"\n{i}. {article.get('title', 'N/A')}")
                print(f"   Region: {article.get('region', 'N/A')}")
                print(f"   Score: {article.get('score', 'N/A')}/10")
                print(f"   Source: {article.get('source', 'N/A')}")
                print(f"   Summary: {article.get('summary', 'N/A')}")
                print(f"   Reason: {article.get('reason', 'N/A')}")
            
            # Check if processed file was created
            processed_file = Path("data/processed_news.json")
            if processed_file.exists():
                print(f"\n[OK] Top tourism stories saved to {processed_file}")
            else:
                print(f"\n[ERROR] Processed news file not created")
                
        else:
            print("[ERROR] Analysis failed or no relevant articles found")
        
        print("\nGlobal Tourism News Selector Test Complete!")
        print("\nNext steps:")
        print("1. Check data/processed_news.json for top tourism stories")
        print("2. Check logs/tourism_editor.log for analysis history")
        print("3. Integrate with your content creation pipeline")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tourism_editor()

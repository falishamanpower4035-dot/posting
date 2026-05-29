#!/usr/bin/env python3
"""
Trend Detection Script for Long Videos
Runs every 12 hours (08:00 UTC and 20:00 UTC)
Detects trending destinations using OpenAI + pytrends
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

from datetime import datetime
from typing import List, Dict
from loguru import logger

from core.news.fetcher.fetch_news import NewsFetcher
from core.content.intelligence.trending_detector_long import TrendingDetectorLong


def fetch_news_articles() -> List[Dict]:
    """Fetch latest news articles"""
    try:
        logger.info("Fetching latest news articles...")
        news_fetcher = NewsFetcher()
        news_fetcher.run_fetch_cycle()
        
        # Load processed news
        import json
        news_file = Path("data/processed_news.json")
        if not news_file.exists():
            logger.warning("No processed_news.json found")
            return []
        
        with open(news_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('top_tourism_stories', [])
        logger.info(f"Loaded {len(articles)} news articles")
        return articles
        
    except Exception as e:
        logger.error(f"Failed to fetch news articles: {e}")
        return []


def detect_trending_destinations() -> Dict:
    """Detect trending destinations"""
    try:
        logger.info("=" * 60)
        logger.info("LONG VIDEO TREND DETECTION")
        logger.info("=" * 60)
        
        # Step 1: Fetch news articles
        articles = fetch_news_articles()
        
        if not articles:
            logger.warning("No news articles available for trend detection")
            return {
                "success": False,
                "error": "No news articles available"
            }
        
        # Step 2: Initialize trend detector
        detector = TrendingDetectorLong()
        
        # Step 3: Update trends
        logger.info("Updating trending destinations...")
        result = detector.update_trends(articles)
        
        if not result.get('updated'):
            logger.error("Failed to update trends")
            return {
                "success": False,
                "error": result.get('error', 'Unknown error')
            }
        
        # Step 4: Get results
        trending_destinations = result.get('trending_destinations', [])
        new_destinations = result.get('new_destinations', [])
        
        logger.info(f"✅ Trend detection completed:")
        logger.info(f"   - Total destinations: {len(trending_destinations)}")
        logger.info(f"   - New destinations: {len(new_destinations)}")
        
        # Step 5: Generate report
        report = detector.generate_trends_report()
        logger.info("\n" + report)
        
        # Step 6: Return results
        return {
            "success": True,
            "trending_destinations": trending_destinations,
            "new_destinations": new_destinations,
            "count": len(trending_destinations),
            "new_count": len(new_destinations),
            "last_updated": result.get('last_updated')
        }
        
    except Exception as e:
        logger.error(f"Trend detection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main function"""
    try:
        logger.info("Starting long video trend detection...")
        
        result = detect_trending_destinations()
        
        if result.get('success'):
            logger.info("✅ Trend detection completed successfully")
            logger.info(f"   Found {result.get('count', 0)} trending destinations")
            logger.info(f"   Found {result.get('new_count', 0)} new destinations")
            
            # Print new destinations
            new_destinations = result.get('new_destinations', [])
            if new_destinations:
                logger.info("\n🎯 NEW DESTINATIONS DETECTED:")
                for i, dest in enumerate(new_destinations, 1):
                    name = dest.get('name', 'Unknown')
                    score = dest.get('trend_score', 0)
                    logger.info(f"   {i}. {name} (Score: {score})")
        else:
            logger.error("❌ Trend detection failed")
            logger.error(f"   Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Trend detection script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Run Trend Detection and Generate Video
Detects trending destinations and generates video for the top trending destination
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger

# Import components
from core.content.intelligence.trending_detector_long import TrendingDetectorLong
from core.production.production_pipeline_long import ProductionPipelineLong


def fetch_news_articles() -> List[Dict]:
    """Fetch latest news articles or use existing processed news"""
    try:
        # Try to load existing processed news first
        news_file = Path("data/processed_news.json")
        if news_file.exists():
            logger.info("Loading existing processed news...")
            with open(news_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = data.get('top_tourism_stories', [])
            if articles:
                logger.info(f"Loaded {len(articles)} news articles from existing file")
                return articles
        
        # If no existing news, try to fetch new news
        logger.info("Attempting to fetch latest news articles...")
        try:
            from core.news.fetcher.fetch_news import NewsFetcher
            news_fetcher = NewsFetcher()
            news_fetcher.run_fetch_cycle()
            
            # Load processed news after fetching
            if news_file.exists():
                with open(news_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                articles = data.get('top_tourism_stories', [])
                logger.info(f"Loaded {len(articles)} news articles after fetching")
                return articles
        except ImportError:
            logger.warning("NewsFetcher not available (schedule module not installed), using existing news")
        except Exception as e:
            logger.warning(f"Failed to fetch news: {e}, using existing news if available")
        
        # If no articles found, return empty list
        logger.warning("No news articles available")
        return []
        
    except Exception as e:
        logger.error(f"Failed to load news articles: {e}")
        return []


def detect_trending_destinations() -> Dict:
    """Detect trending destinations using pytrends directly (NO NEWS REQUIRED)"""
    try:
        logger.info("=" * 60)
        logger.info("TRENDING DESTINATION DETECTION")
        logger.info("=" * 60)
        logger.info("Using DIRECT pytrends discovery (no news articles required)")
        
        # Step 1: Initialize trend detector
        detector = TrendingDetectorLong()
        
        # Step 2: Update trends using pytrends directly (news_articles=None)
        logger.info("Discovering trending destinations from Google Trends...")
        result = detector.update_trends(news_articles=None)  # No news required!
        
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
            "last_updated": result.get('last_updated'),
            "detector": detector
        }
        
    except Exception as e:
        logger.error(f"Trend detection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


def generate_video_for_trending_destination(destination_name: str, privacy_status: str = "private") -> Dict[str, Any]:
    """Generate video for a trending destination"""
    try:
        logger.info("=" * 60)
        logger.info("VIDEO GENERATION FOR TRENDING DESTINATION")
        logger.info("=" * 60)
        logger.info(f"Destination: {destination_name}")
        logger.info(f"Privacy Status: {privacy_status}")
        logger.info("=" * 60)
        
        # Initialize production pipeline
        production_pipeline = ProductionPipelineLong()
        
        # Generate video (with resume mode to reuse existing data)
        result = production_pipeline.generate_video_for_destination(
            destination=destination_name,
            max_duration_minutes=8,
            upload_to_youtube=False,  # Set to False for testing
            privacy_status=privacy_status,
            skip_cleanup=True,       # Resume: don't delete existing data
            reuse_existing=True      # Resume: reuse existing itinerary/script/voiceovers
        )
        
        # Print results
        logger.info("=" * 60)
        logger.info("GENERATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"Video Path: {result.get('video_path', 'N/A')}")
        logger.info(f"Thumbnail Path: {result.get('thumbnail_path', 'N/A')}")
        
        if result.get('errors'):
            logger.error(f"Errors: {result['errors']}")
        
        logger.info("=" * 60)
        
        return result
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "failed",
            "errors": [str(e)],
            "completed_at": datetime.now().isoformat()
        }


def main():
    """Main function"""
    try:
        logger.info("=" * 60)
        logger.info("TREND DETECTION AND VIDEO GENERATION")
        logger.info("=" * 60)
        
        # Step 1: Detect trending destinations
        logger.info("\n🔍 Step 1: Detecting trending destinations...")
        trend_result = detect_trending_destinations()
        
        if not trend_result.get('success'):
            logger.error("❌ Trend detection failed")
            logger.error(f"   Error: {trend_result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        trending_destinations = trend_result.get('trending_destinations', [])
        new_destinations = trend_result.get('new_destinations', [])
        
        if not trending_destinations:
            logger.warning("⚠️ No trending destinations found")
            sys.exit(1)
        
        # Step 2: Select destination (PRIORITIZE NEW over already-processed)
        # First, try to find a new destination that doesn't have a video yet
        selected_destination = None
        destination_name = None
        trend_score = 0
        
        # Check if video already exists for a destination
        def video_exists(dest_name: str) -> bool:
            """Check if video already exists for destination"""
            try:
                from pathlib import Path
                from config import settings_long
                safe_destination = dest_name.replace(",", "_").replace(" ", "_").replace("/", "_")
                videos_dir = Path(settings_long.VIDEOS_DIR)
                video_path = videos_dir / f"{safe_destination}_final.mp4"
                return video_path.exists()
            except:
                return False
        
        # Priority 1: New destinations (not yet processed) without videos
        if new_destinations:
            for dest in sorted(new_destinations, key=lambda x: x.get('trend_score', 0), reverse=True):
                name = dest.get('name', '')
                if name and not video_exists(name):
                    selected_destination = dest
                    destination_name = name
                    trend_score = dest.get('trend_score', 0)
                    logger.info("\n🎯 Selected NEW Destination (not yet processed):")
                    break
        
        # Priority 2: Any trending destination without a video (fallback)
        if not selected_destination:
            for dest in sorted(trending_destinations, key=lambda x: x.get('trend_score', 0), reverse=True):
                name = dest.get('name', '')
                if name and not video_exists(name):
                    selected_destination = dest
                    destination_name = name
                    trend_score = dest.get('trend_score', 0)
                    logger.info("\n🎯 Selected Destination (no existing video):")
                    break
        
        # Priority 3: Top trending destination (only if all have videos - shouldn't happen often)
        if not selected_destination:
            top_destination = trending_destinations[0]
            destination_name = top_destination.get('name', '')
            trend_score = top_destination.get('trend_score', 0)
            logger.warning("\n⚠️ All destinations have videos, selecting top trending:")
        
        if not destination_name:
            logger.error("❌ No destination name found in trending destinations")
            sys.exit(1)
        
        # Log selection details
        logger.info(f"   Name: {destination_name}")
        logger.info(f"   Trend Score: {trend_score}")
        if selected_destination:
            logger.info(f"   Reason: {selected_destination.get('reason', 'N/A')}")
        
        # Check if video already exists
        if video_exists(destination_name):
            logger.warning(f"\n⚠️ Video already exists for {destination_name}. Skipping generation.")
            logger.info("   To regenerate, delete the existing video first.")
            sys.exit(0)
        
        # Step 3: Generate video for selected destination
        logger.info(f"\n🎬 Step 2: Generating video for {destination_name}...")
        video_result = generate_video_for_trending_destination(
            destination_name=destination_name,
            privacy_status="private"  # Use "private" for testing
        )
        
        if video_result.get('status') == 'completed':
            logger.info("✅ Video generation completed successfully")
            logger.info(f"   Video Path: {video_result.get('video_path', 'N/A')}")
            logger.info(f"   Thumbnail Path: {video_result.get('thumbnail_path', 'N/A')}")
        else:
            logger.error("❌ Video generation failed")
            if video_result.get('errors'):
                for error in video_result['errors']:
                    logger.error(f"   Error: {error}")
            sys.exit(1)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ PROCESS COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
TripAvail AI - Main Application Entry Point
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa
from loguru import logger

def main():
    """Main application entry point."""
    logger.info("🚀 Starting TripAvail AI...")
    
    # Check if environment variables are loaded
    required_keys = [
        "OPENAI_API_KEY",
        "NEWSDATA_API_KEY", 
        "META_PAGE_TOKEN",
        "YOUTUBE_API_KEY"
    ]
    
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_keys)}")
        logger.info("Please check your .env file and ensure all API keys are set.")
        return
    
    logger.info("✅ All environment variables loaded successfully")
    logger.info("🎯 TripAvail AI is ready to run!")
    
    # Test news fetcher if NewsData.io key is available
    if os.getenv("NEWSDATA_API_KEY"):
        logger.info("📰 Testing news fetcher...")
        try:
            from modules.news_fetcher.fetch_news import NewsFetcher
            fetcher = NewsFetcher()
            fetcher.run_manual_fetch()
            logger.info("✅ News fetcher test completed successfully")
        except Exception as e:
            logger.error(f"❌ News fetcher test failed: {e}")
    
    # TODO: Add your main application logic here
    logger.info("📝 Application logic not yet implemented")

if __name__ == "__main__":
    main()

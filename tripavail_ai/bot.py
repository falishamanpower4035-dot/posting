#!/usr/bin/env python3
"""
TripAvail AI Bot - Single Entry Point
Professional, centralized automation bot for content generation and posting

Usage:
    python bot.py                    # Start hourly bot (default)
    python bot.py --test             # Test system
    python bot.py --generate-once    # Generate posts once and exit
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

# Now import logger
import logging
from loguru import logger as loguru_logger
# Use loguru logger instead of stdlib
logger = loguru_logger


def check_environment():
    """Check if environment is properly set up"""
    logger.info("Checking environment...")
    
    # Check virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.warning("Virtual environment not activated. Some imports may fail.")
        logger.info("Activate with: venv\\Scripts\\activate")
    
    # Check required directories
    required_dirs = ['core', 'data', 'config', 'logs']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            logger.error(f"Required directory missing: {dir_name}/")
            return False
    
    # Check config
    config_file = Path("config/settings.py")
    if not config_file.exists():
        logger.error("Config file missing: config/settings.py")
        return False
    
    logger.info("Environment check passed!")
    return True


def test_system():
    """Test the system with a single post generation"""
    logger.info("="*60)
    logger.info("TESTING TRIPAVAIL AI SYSTEM")
    logger.info("="*60)
    
    try:
        from core.content.post_manager import PostManager
        from production_pipeline import ProductionPipeline
        
        # Initialize
        pipeline = ProductionPipeline()
        post_manager = PostManager()
        
        # Load news
        topics = pipeline.load_news_topics()
        if not topics:
            logger.error("No news topics found. Run news fetcher first:")
            logger.info("  python scripts/test_news_fetcher.py")
            return False
        
        # Filter quality topics
        quality_topics = [t for t in topics if t.get('score', 0) >= 7]
        logger.info(f"Found {len(quality_topics)} quality topics (score >= 7)")
        
        if not quality_topics:
            logger.warning("No quality topics available for testing")
            return False
        
        # Get next post ID
        existing_posts = post_manager.get_all_posts()
        next_id = len(existing_posts) + 1
        
        logger.info(f"\nGenerating test post: post_{next_id:03d}")
        
        # Generate one post
        success = pipeline.process_single_post(quality_topics[0], next_id)
        
        if success:
            logger.info("\n" + "="*60)
            logger.info("[OK] TEST SUCCESSFUL!")
            logger.info("="*60)
            
            # Show summary
            post_id = f"{next_id:03d}"
            summary = post_manager.get_post_summary(post_id)
            
            logger.info(f"\nPost Directory: {summary['directory']}")
            logger.info(f"Images: {summary['images_count']}")
            logger.info(f"Voiceover: {'YES' if summary['has_voiceover'] else 'NO'}")
            logger.info(f"Final Video: {'YES' if summary['has_final_video'] else 'NO'}")
            
            if summary['metadata']:
                caption = summary['metadata'].get('caption', '')[:80]
                logger.info(f"\nCaption: {caption}...")
                hashtags = summary['metadata'].get('hashtags', [])[:5]
                logger.info(f"Hashtags: {', '.join(hashtags)}")
            
            logger.info("\n[OK] System is working correctly!")
            return True
        else:
            logger.error("\n[ERROR] TEST FAILED")
            logger.error("Check logs for details")
            return False
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure virtual environment is activated:")
        logger.info("  venv\\Scripts\\activate")
        return False
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_once():
    """Generate posts once and exit"""
    logger.info("="*60)
    logger.info("GENERATING POSTS (One-Time)")
    logger.info("="*60)
    
    try:
        from run_hourly_bot import fetch_and_process_news, generate_posts_from_news, post_to_platforms
        from core.content.post_manager import PostManager
        
        # Fetch news
        logger.info("\n1. Fetching news...")
        fetch_and_process_news()
        
        # Generate posts
        logger.info("\n2. Generating posts...")
        new_posts = generate_posts_from_news(max_posts=3)
        
        if not new_posts:
            logger.info("No new posts generated")
            return True
        
        # Post to platforms
        logger.info("\n3. Posting to platforms...")
        for post_id in new_posts:
            post_to_platforms(post_id)
        
        logger.info("\n[OK] Generation complete!")
        return True
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def start_hourly_bot():
    """Start the hourly automation bot"""
    logger.info("="*60)
    logger.info("STARTING HOURLY BOT")
    logger.info("="*60)
    
    try:
        # Import and run the hourly bot
        import run_hourly_bot
        run_hourly_bot.main()
        
    except KeyboardInterrupt:
        logger.info("\n\nBot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='TripAvail AI Bot - Automated Content Generation & Posting'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test the system with a single post generation'
    )
    parser.add_argument(
        '--generate-once',
        action='store_true',
        help='Generate posts once and exit (no continuous loop)'
    )
    parser.add_argument(
        '--skip-check',
        action='store_true',
        help='Skip environment check'
    )
    
    args = parser.parse_args()
    
    # Print header
    print("\n" + "="*60)
    print("TRIPAVAIL AI - Automated Content Bot")
    print("Professional Content Generation & Social Media Posting")
    print("="*60 + "\n")
    
    # Check environment
    if not args.skip_check:
        if not check_environment():
            logger.error("Environment check failed. Fix issues and try again.")
            sys.exit(1)
    
    # Run requested mode
    if args.test:
        success = test_system()
        sys.exit(0 if success else 1)
    
    elif args.generate_once:
        success = generate_once()
        sys.exit(0 if success else 1)
    
    else:
        # Default: Start hourly bot
        start_hourly_bot()


if __name__ == "__main__":
    main()


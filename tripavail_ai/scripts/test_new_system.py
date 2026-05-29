#!/usr/bin/env python3
"""
Test the new production pipeline system
Generates one post to verify everything works
"""

from pathlib import Path
from loguru import logger
from production_pipeline import ProductionPipeline
from modules.post_manager import PostManager

def main():
    logger.info("="*60)
    logger.info("TESTING NEW PRODUCTION PIPELINE")
    logger.info("="*60)
    
    # Initialize
    pipeline = ProductionPipeline()
    post_manager = PostManager()
    
    # Load news topics
    topics = pipeline.load_news_topics()
    
    if not topics:
        logger.error("No news topics found. Run news fetcher first.")
        return
    
    # Filter quality topics
    quality_topics = [t for t in topics if t.get('score', 0) >= 7]
    logger.info(f"Found {len(quality_topics)} quality topics (score >= 7)")
    
    if not quality_topics:
        logger.error("No quality topics available")
        return
    
    # Get next post ID
    existing_posts = post_manager.get_all_posts()
    next_id = len(existing_posts) + 1
    
    logger.info(f"\nGenerating test post: post_{next_id:03d}")
    
    # Generate one post
    success = pipeline.process_single_post(quality_topics[0], next_id)
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("✅ TEST SUCCESSFUL!")
        logger.info("="*60)
        
        # Show post summary
        post_id = f"{next_id:03d}"
        summary = post_manager.get_post_summary(post_id)
        
        logger.info(f"\nPost Directory: {summary['directory']}")
        logger.info(f"Images: {summary['images_count']}")
        logger.info(f"Voiceover: {'✅' if summary['has_voiceover'] else '❌'}")
        logger.info(f"Final Video: {'✅' if summary['has_final_video'] else '❌'}")
        
        if summary['metadata']:
            logger.info(f"\nCaption: {summary['metadata'].get('caption', '')[:100]}...")
            logger.info(f"Hashtags: {', '.join(summary['metadata'].get('hashtags', [])[:5])}")
        
        logger.info("\n" + "="*60)
        logger.info("New system is working! Ready to start the bot.")
        logger.info("="*60)
    else:
        logger.error("\n" + "="*60)
        logger.error("❌ TEST FAILED")
        logger.error("="*60)
        logger.error("Check the logs for details")


if __name__ == "__main__":
    main()


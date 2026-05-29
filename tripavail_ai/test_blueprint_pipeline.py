#!/usr/bin/env python3
"""
Test script to run the production pipeline with the new blueprint-based system
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.production.production_pipeline_long import ProductionPipelineLong
from loguru import logger

def main():
    """Test the production pipeline with Bali"""
    logger.info("=" * 60)
    logger.info("TESTING BLUEPRINT-BASED PRODUCTION PIPELINE")
    logger.info("=" * 60)
    
    pipeline = ProductionPipelineLong()
    
    # Use existing Bali itinerary and script
    result = pipeline.generate_video_for_destination(
        destination="Bali, Indonesia",
        max_duration_minutes=8,
        upload_to_youtube=False,  # Don't upload for testing
        reuse_existing=True,  # Reuse existing itinerary and script
        skip_cleanup=True  # Don't cleanup, just test the new image generation
    )
    
    logger.info("=" * 60)
    logger.info("GENERATION RESULT")
    logger.info("=" * 60)
    logger.info(f"Status: {result.get('status')}")
    logger.info(f"Video Path: {result.get('video_path')}")
    logger.info(f"Thumbnail Path: {result.get('thumbnail_path')}")
    
    if result.get('errors'):
        logger.error("Errors:")
        for error in result.get('errors', []):
            logger.error(f"  - {error}")
    
    return result

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Generate Karnataka Video with Voice
Fixes the previous issue where video was generated without voice
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

from loguru import logger
from core.production.production_pipeline_long import ProductionPipelineLong

def main():
    """Generate Karnataka video with proper voice integration"""
    destination = "Karnataka, India"
    
    logger.info("=" * 60)
    logger.info(f"GENERATING VIDEO FOR: {destination}")
    logger.info("=" * 60)
    logger.info("This will regenerate the video with proper voiceover integration")
    logger.info("")
    
    # Initialize pipeline
    pipeline = ProductionPipelineLong()
    
    # Generate video
    result = pipeline.generate_video_for_destination(
        destination=destination,
        max_duration_minutes=8,
        upload_to_youtube=False,  # Don't upload during regeneration
        privacy_status="private"
    )
    
    # Print results
    logger.info("=" * 60)
    logger.info("GENERATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Status: {result['status']}")
    logger.info(f"Video: {result.get('video_path', 'N/A')}")
    logger.info(f"Thumbnail: {result.get('thumbnail_path', 'N/A')}")
    if result.get('errors'):
        logger.error(f"Errors: {result['errors']}")
    
    if result['status'] == 'completed':
        logger.info("✅ Video generation completed successfully!")
        logger.info(f"Video saved at: {result.get('video_path')}")
    else:
        logger.error("❌ Video generation failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())


#!/usr/bin/env python3
"""
Reassemble video using existing images (no re-download)
Uses existing itinerary, script, voiceovers, and images
Only regenerates video assembly with the fix applied
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.production.production_pipeline_long import ProductionPipelineLong
from loguru import logger

def main():
    """Reassemble video for Bali using existing images"""
    logger.info("=" * 60)
    logger.info("REASSEMBLING VIDEO WITH EXISTING IMAGES")
    logger.info("=" * 60)
    
    destination = "Bali, Indonesia"
    
    pipeline = ProductionPipelineLong()
    
    # Reassemble video with:
    # - reuse_existing=True: Use existing itinerary, script, voiceovers
    # - Images will be reused automatically (image generator checks for existing images)
    # - Only video assembly will be regenerated with the fix
    result = pipeline.generate_video_for_destination(
        destination=destination,
        max_duration_minutes=8,
        upload_to_youtube=False,  # Don't upload
        reuse_existing=True,  # Use existing itinerary, script, voiceovers
        skip_cleanup=True  # Don't delete existing files
    )
    
    logger.info("=" * 60)
    logger.info("REASSEMBLY RESULT")
    logger.info("=" * 60)
    logger.info(f"Status: {result.get('status')}")
    logger.info(f"Video Path: {result.get('video_path')}")
    logger.info(f"Thumbnail Path: {result.get('thumbnail_path')}")
    
    if result.get('errors'):
        logger.error("Errors:")
        for error in result.get('errors', []):
            logger.error(f"  - {error}")
    
    if result.get('status') == 'completed':
        logger.info("✅ Video reassembled successfully with existing images!")
        logger.info(f"   Video: {result.get('video_path')}")
    else:
        logger.error(f"❌ Reassembly failed: {result.get('status')}")
    
    return result

if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""
Resume Generation for a Specific Destination
Skips trend detection, skips cleanup, and reuses existing itinerary/script/intro voiceover.
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
    try:
        destination = "Chiang Mai, Thailand"
        logger.info("=" * 60)
        logger.info("RESUME LONG VIDEO GENERATION")
        logger.info("=" * 60)
        logger.info(f"Destination: {destination}")
        logger.info("=" * 60)

        pipeline = ProductionPipelineLong()
        result = pipeline.generate_video_for_destination(
            destination=destination,
            max_duration_minutes=8,
            upload_to_youtube=False,
            privacy_status="private",
            skip_cleanup=True,
            reuse_existing=True
        )

        logger.info("=" * 60)
        logger.info("RESUME RESULTS")
        logger.info("=" * 60)
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info(f"Video Path: {result.get('video_path', 'N/A')}")
        logger.info(f"Thumbnail Path: {result.get('thumbnail_path', 'N/A')}")
        if result.get('errors'):
            logger.error(f"Errors: {result['errors']}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Resume run failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()



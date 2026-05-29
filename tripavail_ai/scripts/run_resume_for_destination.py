#!/usr/bin/env python3
"""
Resume generation for a specific destination (skip trend detection)
Skips cleanup and reuses existing itinerary/script/intro voiceover if present.
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
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_resume_for_destination.py \"Destination, Country\" [days_csv]")
        sys.exit(1)

    destination = sys.argv[1]
    days_csv = sys.argv[2] if len(sys.argv) > 2 else None
    process_days = None
    if days_csv:
        try:
            process_days = [int(x.strip()) for x in days_csv.split(',') if x.strip().isdigit()]
        except Exception:
            process_days = None

    logger.info("=" * 60)
    logger.info("RESUME GENERATION FOR DESTINATION")
    logger.info("=" * 60)
    logger.info(f"Destination: {destination}")
    logger.info("=" * 60)

    pipeline = ProductionPipelineLong()

    result = pipeline.generate_video_for_destination(
        destination=destination,
        max_duration_minutes=8,
        upload_to_youtube=False,
        privacy_status="private",
        skip_cleanup=True,       # resume: do not delete anything
        reuse_existing=True,     # resume: load existing itinerary/script/intro VO
        process_days=process_days
    )

    logger.info("=" * 60)
    logger.info("GENERATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Status: {result.get('status', 'unknown')}")
    logger.info(f"Video Path: {result.get('video_path', 'N/A')}")
    logger.info(f"Thumbnail Path: {result.get('thumbnail_path', 'N/A')}")
    if result.get('errors'):
        logger.error(f"Errors: {result['errors']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()



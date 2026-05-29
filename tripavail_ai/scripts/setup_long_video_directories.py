#!/usr/bin/env python3
"""
Setup Directory Structure for Long Video System
Creates all necessary directories for long video generation
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config import settings_long


def setup_directories():
    """Create all necessary directories for long video system"""
    try:
        logger.info("Setting up long video directory structure...")
        
        # Get directory paths from settings
        directories = [
            settings_long.DATA_DIR,
            settings_long.LONG_VIDEOS_DIR,
            settings_long.DESTINATIONS_DIR,
            settings_long.IMAGES_DIR,
            settings_long.SCRIPTS_DIR,
            settings_long.VOICEOVERS_DIR,
            settings_long.VIDEOS_DIR,
            settings_long.THUMBNAILS_DIR,
            settings_long.CACHE_DIR,
            settings_long.LOGS_DIR,
        ]
        
        # Create directories
        for directory in directories:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {dir_path}")
        
        # Create subdirectories for image cache
        cache_categories = ['attractions', 'activities', 'food_culture', 'local_life', 'scenic_views']
        for category in cache_categories:
            category_dir = Path(settings_long.CACHE_DIR) / category
            category_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created cache directory: {category_dir}")
        
        logger.info("✅ Directory structure setup completed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup directories: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main function"""
    try:
        logger.info("=" * 60)
        logger.info("LONG VIDEO DIRECTORY SETUP")
        logger.info("=" * 60)
        
        success = setup_directories()
        
        if success:
            logger.info("✅ Directory setup completed successfully")
        else:
            logger.error("❌ Directory setup failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Directory setup script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


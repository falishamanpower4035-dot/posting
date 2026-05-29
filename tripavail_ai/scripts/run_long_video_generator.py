#!/usr/bin/env python3
"""
Long Video Generator Scheduler
Runs during idle periods (end of day)
Detects trending destinations and generates long videos
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

import os
import json
import time
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Any
from loguru import logger
import schedule

# Import components
from core.content.intelligence.trending_detector_long import TrendingDetectorLong
from core.news.fetcher.fetch_news import NewsFetcher
from core.production.production_pipeline_long import ProductionPipelineLong
from config import settings_long


class LongVideoGeneratorScheduler:
    """
    Scheduler for long video generation
    Runs during idle periods (end of day)
    Detects trending destinations and generates long videos
    """
    
    def __init__(self):
        # Components
        self.trending_detector = TrendingDetectorLong()
        self.news_fetcher = NewsFetcher()
        self.production_pipeline = ProductionPipelineLong()
        
        # Settings
        self.enabled = settings_long.LONG_VIDEO_ENABLED
        self.trending_detection_time = settings_long.TRENDING_DETECTION_TIME  # "08:00,20:00"
        self.generation_time = settings_long.LONG_VIDEO_GENERATION_TIME  # "20:00"
        self.max_duration_minutes = 8
        
        # Resource management
        self.resource_check_enabled = settings_long.RESOURCE_CHECK_ENABLED
        self.resource_cpu_threshold = settings_long.RESOURCE_CPU_THRESHOLD
        self.resource_memory_threshold = settings_long.RESOURCE_MEMORY_THRESHOLD
        self.resource_disk_space_min_gb = settings_long.RESOURCE_DISK_SPACE_MIN_GB
        
        # Lock file
        self.lock_file = Path(settings_long.RESOURCE_LOCK_FILE)
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Long Video Generator Scheduler initialized")
        logger.info(f"Enabled: {self.enabled}")
        logger.info(f"Trending Detection Time: {self.trending_detection_time}")
        logger.info(f"Generation Time: {self.generation_time}")
    
    def check_resources(self) -> bool:
        """
        Check if system resources are available
        
        Returns:
            True if resources are available, False otherwise
        """
        try:
            if not self.resource_check_enabled:
                return True
            
            # Check CPU usage
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > (self.resource_cpu_threshold * 100):
                    logger.warning(f"CPU usage too high: {cpu_percent}%")
                    return False
            except ImportError:
                logger.warning("psutil not available, skipping CPU check")
            
            # Check memory usage
            try:
                import psutil
                memory = psutil.virtual_memory()
                memory_percent = memory.percent / 100
                if memory_percent > self.resource_memory_threshold:
                    logger.warning(f"Memory usage too high: {memory_percent * 100}%")
                    return False
            except ImportError:
                logger.warning("psutil not available, skipping memory check")
            
            # Check disk space
            try:
                import shutil
                disk_usage = shutil.disk_usage(Path.cwd())
                disk_free_gb = disk_usage.free / (1024 ** 3)
                if disk_free_gb < self.resource_disk_space_min_gb:
                    logger.warning(f"Disk space too low: {disk_free_gb:.2f} GB")
                    return False
            except Exception as e:
                logger.warning(f"Failed to check disk space: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
            return False
    
    def acquire_lock(self) -> bool:
        """
        Acquire lock file to prevent concurrent execution
        
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            if self.lock_file.exists():
                logger.warning("Lock file exists, another process may be running")
                return False
            
            # Create lock file
            self.lock_file.write_text(f"{datetime.now().isoformat()}\n")
            logger.info("Lock file acquired")
            return True
            
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
    
    def release_lock(self):
        """Release lock file"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                logger.info("Lock file released")
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
    
    def detect_trending_destinations(self) -> List[Dict[str, Any]]:
        """
        Detect trending destinations
        
        Returns:
            List of trending destinations
        """
        try:
            logger.info("Detecting trending destinations...")
            
            # Fetch news articles
            self.news_fetcher.run_fetch_cycle()
            
            # Load processed news
            news_file = Path("data/processed_news.json")
            if not news_file.exists():
                logger.warning("No processed news found")
                return []
            
            with open(news_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = data.get('top_tourism_stories', [])
            
            if not articles:
                logger.warning("No news articles available")
                return []
            
            # Update trends
            result = self.trending_detector.update_trends(articles)
            
            if not result.get('updated'):
                logger.error("Failed to update trends")
                return []
            
            # Get new destinations
            new_destinations = result.get('new_destinations', [])
            
            if new_destinations:
                logger.info(f"Found {len(new_destinations)} new trending destinations")
                for dest in new_destinations:
                    logger.info(f"  - {dest.get('name', 'Unknown')} (Score: {dest.get('trend_score', 0)})")
            
            return new_destinations
            
        except Exception as e:
            logger.error(f"Error detecting trending destinations: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def generate_video_for_destination(
        self,
        destination: str,
        upload_to_youtube: bool = True,
        privacy_status: str = "public"
    ) -> Dict[str, Any]:
        """
        Generate video for destination
        
        Args:
            destination: Destination name
            upload_to_youtube: Whether to upload to YouTube
            privacy_status: YouTube privacy status
            
        Returns:
            Dictionary with generation results
        """
        try:
            logger.info(f"Generating video for destination: {destination}")
            
            # Check resources
            if not self.check_resources():
                logger.warning("System resources not available, skipping video generation")
                return {
                    "destination": destination,
                    "status": "skipped",
                    "reason": "Insufficient resources"
                }
            
            # Acquire lock
            if not self.acquire_lock():
                logger.warning("Could not acquire lock, skipping video generation")
                return {
                    "destination": destination,
                    "status": "skipped",
                    "reason": "Lock file exists"
                }
            
            try:
                # Generate video
                result = self.production_pipeline.generate_video_for_destination(
                    destination=destination,
                    max_duration_minutes=self.max_duration_minutes,
                    upload_to_youtube=upload_to_youtube,
                    privacy_status=privacy_status
                )
                
                return result
                
            finally:
                # Release lock
                self.release_lock()
                
        except Exception as e:
            logger.error(f"Error generating video for destination: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Release lock
            self.release_lock()
            
            return {
                "destination": destination,
                "status": "failed",
                "errors": [str(e)]
            }
    
    def run_trending_detection(self):
        """Run trending destination detection"""
        try:
            logger.info("=" * 60)
            logger.info("TRENDING DESTINATION DETECTION")
            logger.info("=" * 60)
            
            # Detect trending destinations
            destinations = self.detect_trending_destinations()
            
            if destinations:
                logger.info(f"✅ Detected {len(destinations)} trending destinations")
            else:
                logger.info("No new trending destinations detected")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error running trending detection: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run_video_generation(self):
        """Run video generation for trending destinations"""
        try:
            logger.info("=" * 60)
            logger.info("LONG VIDEO GENERATION")
            logger.info("=" * 60)
            
            # Get trending destinations
            trending_destinations = self.trending_detector.get_trending_destinations(count=5)
            
            if not trending_destinations:
                logger.info("No trending destinations found")
                return
            
            logger.info(f"Found {len(trending_destinations)} trending destinations")
            
            # Generate videos for each destination
            results = []
            for dest in trending_destinations:
                destination_name = dest.get('name', '')
                if not destination_name:
                    continue
                
                logger.info(f"Generating video for: {destination_name}")
                
                # Generate video
                result = self.generate_video_for_destination(
                    destination=destination_name,
                    upload_to_youtube=True,
                    privacy_status="public"
                )
                
                results.append(result)
                
                # Wait between generations to avoid overload
                time.sleep(60)  # 1 minute between generations
            
            # Print summary
            logger.info("=" * 60)
            logger.info("GENERATION SUMMARY")
            logger.info("=" * 60)
            
            successful = [r for r in results if r.get('status') == 'completed']
            failed = [r for r in results if r.get('status') == 'failed']
            skipped = [r for r in results if r.get('status') == 'skipped']
            
            logger.info(f"Successful: {len(successful)}")
            logger.info(f"Failed: {len(failed)}")
            logger.info(f"Skipped: {len(skipped)}")
            
            if successful:
                logger.info("✅ Successful videos:")
                for r in successful:
                    logger.info(f"  - {r.get('destination', 'Unknown')}")
                    if r.get('youtube_url'):
                        logger.info(f"    YouTube: {r['youtube_url']}")
            
            if failed:
                logger.error("❌ Failed videos:")
                for r in failed:
                    logger.error(f"  - {r.get('destination', 'Unknown')}")
                    if r.get('errors'):
                        for error in r['errors']:
                            logger.error(f"    Error: {error}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error running video generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def schedule_jobs(self):
        """Schedule jobs for trending detection and video generation"""
        try:
            if not self.enabled:
                logger.warning("Long video generation is disabled")
                return
            
            # Parse trending detection times
            detection_times = self.trending_detection_time.split(',')
            for time_str in detection_times:
                time_str = time_str.strip()
                try:
                    hour, minute = map(int, time_str.split(':'))
                    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.run_trending_detection)
                    logger.info(f"Scheduled trending detection at {time_str} UTC")
                except Exception as e:
                    logger.error(f"Invalid time format: {time_str}")
            
            # Parse generation time
            try:
                hour, minute = map(int, self.generation_time.split(':'))
                schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.run_video_generation)
                logger.info(f"Scheduled video generation at {self.generation_time} UTC")
            except Exception as e:
                logger.error(f"Invalid generation time format: {self.generation_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling jobs: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def run(self):
        """Run scheduler"""
        try:
            if not self.enabled:
                logger.warning("Long video generation is disabled")
                return
            
            logger.info("=" * 60)
            logger.info("LONG VIDEO GENERATOR SCHEDULER")
            logger.info("=" * 60)
            logger.info("Starting scheduler...")
            logger.info(f"Trending Detection Time: {self.trending_detection_time}")
            logger.info(f"Generation Time: {self.generation_time}")
            logger.info("=" * 60)
            
            # Schedule jobs
            self.schedule_jobs()
            
            # Run scheduler
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Error running scheduler: {e}")
            import traceback
            logger.error(traceback.format_exc())


def main():
    """Main function"""
    try:
        logger.info("=" * 60)
        logger.info("LONG VIDEO GENERATOR SCHEDULER")
        logger.info("=" * 60)
        
        # Initialize scheduler
        scheduler = LongVideoGeneratorScheduler()
        
        # Run scheduler
        scheduler.run()
        
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


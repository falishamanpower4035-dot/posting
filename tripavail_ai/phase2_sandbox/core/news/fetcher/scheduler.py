#!/usr/bin/env python3
"""
News Scheduler for TripAvail AI
Handles automated scheduling of news fetching operations
"""

import time
import signal
import sys
from loguru import logger
from core.news.fetcher.fetch_news import NewsFetcher

class NewsScheduler:
    """Manages the automated news fetching schedule"""
    
    def __init__(self):
        self.fetcher = NewsFetcher()
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        sys.exit(0)
    
    def start(self):
        """Start the news scheduler"""
        logger.info("Starting TripAvail AI News Scheduler")
        logger.info("Fetching tourism news every 20 minutes")
        logger.info("Press Ctrl+C to stop")
        
        try:
            # Run initial fetch
            self.fetcher.run_fetch_cycle()
            
            # Main scheduling loop
            while self.running:
                # Check if it's time for next fetch (every 20 minutes)
                current_time = time.time()
                next_fetch_time = current_time + (20 * 60)  # 20 minutes
                
                logger.info(f"Next fetch scheduled in 20 minutes")
                
                # Sleep in 1-minute intervals to allow for graceful shutdown
                while self.running and time.time() < next_fetch_time:
                    time.sleep(60)  # Sleep for 1 minute
                
                if self.running:
                    logger.info("Starting scheduled news fetch")
                    self.fetcher.run_fetch_cycle()
                    
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            logger.info("News scheduler stopped")

def main():
    """Main function to start the scheduler"""
    scheduler = NewsScheduler()
    scheduler.start()

if __name__ == "__main__":
    main()

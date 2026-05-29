#!/usr/bin/env python3
"""
News Fetcher for TripAvail AI
Fetches tourism-related news from NewsData.io every 20-40 minutes
"""

import os
import json
import time
import requests
import schedule
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NewsFetcher:
    """Handles fetching and processing tourism news from NewsData.io"""
    
    def __init__(self):
        self.api_key = os.getenv('NEWSDATA_API_KEY')
        self.base_url = "https://newsdata.io/api/1/news"
        
        # Query rotation for different tourism topics
        self.queries = [
            "tourism OR travel OR destination",
            "visa OR tourist policy OR entry rules", 
            "eco-tourism OR sustainable travel OR digital nomad"
        ]
        self.current_query_index = 0
        
        # File paths
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.raw_news_file = self.data_dir / "raw_news.json"
        self.fetch_log_file = self.logs_dir / "fetch_log.txt"
        self.state_file = self.data_dir / "news_fetcher_state.json"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Enable debug logging
        logger.add("logs/news_fetcher_debug.log", level="DEBUG", rotation="1 day")
        
        # Load state for query rotation
        self.load_state()
        
        # Request tracking for quota control
        self.daily_requests = 0
        self.last_reset_date = datetime.now().date()
        
        if not self.api_key:
            raise ValueError("NEWSDATA_API_KEY not found in environment variables")
    
    def load_state(self):
        """Load the current state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.current_query_index = state.get('query_index', 0)
                    self.daily_requests = state.get('daily_requests', 0)
                    last_reset = state.get('last_reset_date')
                    if last_reset:
                        self.last_reset_date = datetime.fromisoformat(last_reset).date()
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self.current_query_index = 0
                self.daily_requests = 0
                self.last_reset_date = datetime.now().date()
    
    def save_state(self):
        """Save the current state to file"""
        try:
            state = {
                'query_index': self.current_query_index,
                'daily_requests': self.daily_requests,
                'last_reset_date': self.last_reset_date.isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def reset_daily_counter(self):
        """Reset daily request counter if it's a new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_requests = 0
            self.last_reset_date = today
            logger.info(f"Reset daily request counter for {today}")
    
    def get_next_query(self) -> str:
        """Get the next query in rotation"""
        query = self.queries[self.current_query_index]
        self.current_query_index = (self.current_query_index + 1) % len(self.queries)
        return query
    
    def fetch_news(self, query: str) -> Optional[Dict]:
        """Fetch news from NewsData.io API"""
        try:
            params = {
                'apikey': self.api_key,
                'q': query,
                'language': 'en'
                # Removed category parameter as it might be causing issues
            }
            
            logger.info(f"Fetching news for query: {query}")
            logger.debug(f"API URL: {self.base_url}")
            logger.debug(f"Params: {params}")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            
            # Log response details for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 422:
                logger.error(f"API returned 422 error. Response: {response.text}")
                return None
            
            response.raise_for_status()
            
            data = response.json()
            self.daily_requests += 1
            
            logger.info(f"Successfully fetched {len(data.get('results', []))} articles")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during fetch: {e}")
            return None
    
    def load_existing_news(self) -> List[Dict]:
        """Load existing news data to check for duplicates"""
        if not self.raw_news_file.exists():
            return []
        
        try:
            with open(self.raw_news_file, 'r') as f:
                data = json.load(f)
                return data.get('articles', [])
        except Exception as e:
            logger.warning(f"Failed to load existing news: {e}")
            return []
    
    def is_duplicate(self, article: Dict, existing_articles: List[Dict]) -> bool:
        """Check if an article is a duplicate based on URL and title"""
        article_url = article.get('link', '')
        article_title = article.get('title', '')
        
        for existing in existing_articles:
            if (existing.get('link') == article_url or 
                existing.get('title') == article_title):
                return True
        return False
    
    def process_and_save_news(self, api_data: Dict, query: str) -> int:
        """Process API response and save new articles"""
        if not api_data or 'results' not in api_data:
            logger.warning("No results in API response")
            return 0
        
        # Load existing articles
        existing_articles = self.load_existing_news()
        
        # Filter out duplicates
        new_articles = []
        for article in api_data['results']:
            if not self.is_duplicate(article, existing_articles):
                # Standardize article format
                standardized_article = {
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'link': article.get('link', ''),
                    'country': article.get('country', []),
                    'pubDate': article.get('pubDate', ''),
                    'source_id': article.get('source_id', ''),
                    'category': article.get('category', [])
                }
                new_articles.append(standardized_article)
        
        if not new_articles:
            logger.info("No new articles found")
            return 0
        
        # Create new data structure
        timestamp = datetime.now(timezone.utc).isoformat()
        news_data = {
            'timestamp': timestamp,
            'source': 'NewsData.io',
            'query': query,
            'articles': new_articles
        }
        
        # Save to file
        try:
            with open(self.raw_news_file, 'w') as f:
                json.dump(news_data, f, indent=2)
            
            logger.info(f"Saved {len(new_articles)} new articles to {self.raw_news_file}")
            return len(new_articles)
            
        except Exception as e:
            logger.error(f"Failed to save news data: {e}")
            return 0
    
    def log_fetch_operation(self, query: str, article_count: int):
        """Log the fetch operation to fetch_log.txt"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        log_entry = f"{timestamp} | Query: {query} | {article_count} articles\n"
        
        try:
            with open(self.fetch_log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Failed to write to fetch log: {e}")
    
    def run_fetch_cycle(self):
        """Run a complete fetch cycle"""
        logger.info("Starting news fetch cycle")
        
        # Reset daily counter if needed
        self.reset_daily_counter()
        
        # Check quota
        if self.daily_requests >= 144:  # Stay under 200/day limit
            logger.warning(f"Daily quota limit reached ({self.daily_requests} requests)")
            return
        
        # Get next query
        query = self.get_next_query()
        
        # Fetch news
        api_data = self.fetch_news(query)
        
        if api_data:
            # Process and save
            article_count = self.process_and_save_news(api_data, query)
            
            # Log operation
            self.log_fetch_operation(query, article_count)
            
            # Save state
            self.save_state()
            
            logger.info(f"Fetch cycle completed: {article_count} new articles")
        else:
            logger.error("Fetch cycle failed - no data received")
    
    def run_with_retry(self):
        """Run fetch cycle with retry logic"""
        try:
            self.run_fetch_cycle()
        except Exception as e:
            logger.error(f"Fetch cycle failed: {e}")
            
            # Retry once after 10 minutes
            logger.info("Scheduling retry in 10 minutes")
            schedule.every(10).minutes.do(self.run_fetch_cycle).tag('retry')
    
    def start_scheduler(self):
        """Start the scheduled news fetching"""
        logger.info("Starting news fetcher scheduler")
        
        # Schedule main fetch every 20 minutes
        schedule.every(20).minutes.do(self.run_with_retry).tag('main')
        
        # Run initial fetch
        self.run_fetch_cycle()
        
        # Keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_manual_fetch(self):
        """Run a manual fetch for testing"""
        logger.info("Running manual news fetch")
        self.run_fetch_cycle()
        logger.info("Manual fetch completed")

def main():
    """Main function for testing"""
    try:
        fetcher = NewsFetcher()
        fetcher.run_manual_fetch()
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()

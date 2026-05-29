#!/usr/bin/env python3
"""
Trending Destination Detector for Long Videos
Uses OpenAI + pytrends to detect trending travel destinations
Runs every 12 hours (08:00 UTC and 20:00 UTC)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

# Try to import pytrends
try:
    from pytrends.request import TrendReq
    import pandas as pd
    PTRENDS_AVAILABLE = True
except ImportError:
    PTRENDS_AVAILABLE = False
    pd = None
    logger.warning("pytrends not installed. Install with: pip install pytrends")

load_dotenv()


class TrendingDetectorLong:
    """
    Detects trending destinations for long videos using OpenAI + pytrends
    Combines news analysis with Google Trends data
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path("data")
        self.long_videos_dir = self.data_dir / "long_videos"
        self.destinations_dir = self.long_videos_dir / "destinations"
        self.trends_file = self.destinations_dir / "trending_destinations_long.json"
        
        # Initialize pytrends if available
        self.pytrends = None
        if PTRENDS_AVAILABLE:
            try:
                self.pytrends = TrendReq(hl='en-US', tz=360)
                logger.info("✅ pytrends initialized for Google Trends data")
            except Exception as e:
                logger.warning(f"Failed to initialize pytrends: {e}")
                self.pytrends = None
        
        # Ensure directories exist
        self.destinations_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing trends
        self.trends_cache = self.load_trends_cache()
        
        logger.info("Trending Detector Long initialized")
    
    def load_trends_cache(self) -> Dict:
        """Load cached trending destinations"""
        if self.trends_file.exists():
            try:
                with open(self.trends_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load trends cache: {e}")
        
        return {
            "last_updated": None,
            "trending_destinations": [],
            "last_check_time": None,
            "destinations_processed": []
        }
    
    def save_trends_cache(self, trends: Dict):
        """Save trending destinations to cache"""
        try:
            with open(self.trends_file, 'w', encoding='utf-8') as f:
                json.dump(trends, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved trends cache to {self.trends_file}")
        except Exception as e:
            logger.error(f"Failed to save trends cache: {e}")
    
    def analyze_news_with_openai(self, news_articles: List[Dict]) -> Dict[str, Any]:
        """
        Analyze news articles using OpenAI to identify trending destinations
        
        Args:
            news_articles: List of news article dictionaries
            
        Returns:
            Dictionary with trending destinations from OpenAI analysis
        """
        try:
            # Prepare news summary for AI analysis
            news_summary = self._prepare_news_summary(news_articles)
            
            prompt = f"""You are a travel industry trend analyst. Analyze these recent travel news articles and identify trending destinations.

NEWS ARTICLES SUMMARY:
{news_summary}

YOUR TASK:
Identify trending travel destinations from these news articles. Focus on destinations that are:
1. Mentioned frequently or getting significant attention
2. Have new developments, events, or attractions
3. Are experiencing increased interest or popularity
4. Have compelling stories that would make good long-format video content (3-4 minutes)

For each destination, provide:
- Destination name (be specific: "Bali, Indonesia" not just "Bali")
- Trend score (0-100): How trending is this destination?
- Reason: Why is it trending? What's the story?
- Keywords: Key search terms for this destination
- Category: Type of destination (beach, city, nature, cultural, etc.)

Respond in JSON format:
{{
    "trending_destinations": [
        {{
            "name": "Bali, Indonesia",
            "trend_score": 85,
            "reason": "New visa policies and cultural festivals attracting tourists",
            "keywords": ["Bali", "Indonesia", "tourism", "beach", "culture"],
            "category": "beach"
        }}
    ],
    "analyzed_at": "2025-01-15T20:00:00Z",
    "articles_analyzed": 20
}}
"""
            
            logger.info("Analyzing news for trending destinations with OpenAI...")
            
            # Use GPT-4o-mini directly (GPT-5 is unreliable/hanging)
            # TODO: Re-enable GPT-5 when it's more stable
            models_to_try = [
                ("gpt-4o-mini", {"temperature": 0.4, "max_tokens": 2000})
            ]
            
            response = None
            model_name = None
            last_error = None
            
            for model, params in models_to_try:
                try:
                    model_name = model
                    logger.info(f"Trying model: {model_name} for trend detection")
                    
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert travel industry trend analyst specializing in identifying trending destinations for long-format video content. You excel at finding destinations with compelling stories that would engage viewers for 3-4 minutes."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        **params
                    )
                    
                    if response.choices and response.choices[0].message.content:
                        logger.info(f"✅ Successfully got response from {model_name}")
                        break
                    else:
                        logger.warning(f"Empty response from {model_name}, trying fallback...")
                        last_error = f"Empty response from {model_name}"
                        response = None
                        
                except Exception as api_error:
                    logger.warning(f"Model {model_name} failed: {api_error}")
                    last_error = str(api_error)
                    response = None
                    continue
            
            if response is None or not response.choices:
                error_msg = f"All models failed for trend detection. Last error: {last_error}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            trends = json.loads(content)
            trends['analyzed_at'] = datetime.now().isoformat()
            trends['articles_analyzed'] = len(news_articles)
            
            logger.info(f"OpenAI identified {len(trends.get('trending_destinations', []))} trending destinations")
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze trends with OpenAI: {e}")
            return {"trending_destinations": [], "analyzed_at": datetime.now().isoformat(), "articles_analyzed": 0}
    
    def analyze_with_pytrends(self, destinations: List[str]) -> Dict[str, int]:
        """
        Analyze destinations using Google Trends (pytrends)
        
        Args:
            destinations: List of destination names to check
            
        Returns:
            Dictionary mapping destination names to trend scores (0-100)
        """
        if not self.pytrends or not PTRENDS_AVAILABLE:
            logger.warning("pytrends not available, skipping Google Trends analysis")
            return {}
        
        trend_scores = {}
        
        try:
            # Process destinations in batches (Google Trends limits)
            batch_size = 5
            for i in range(0, len(destinations), batch_size):
                batch = destinations[i:i + batch_size]
                
                # Build payload for this batch
                try:
                    # Add "travel" or "tourism" to each destination for better results
                    keywords = [f"{dest} travel" for dest in batch]
                    
                    self.pytrends.build_payload(
                        keywords,
                        timeframe='today 3-m',  # Last 3 months
                        geo='',  # Global
                        gprop=''  # Web search
                    )
                    
                    # Get interest over time
                    interest_data = self.pytrends.interest_over_time()
                    
                    if not interest_data.empty and len(interest_data) > 0:
                        # Calculate average interest for each destination
                        for j, dest in enumerate(batch):
                            keyword = keywords[j]
                            # Remove 'isPartial' column if present
                            if 'isPartial' in interest_data.columns:
                                interest_data_clean = interest_data.drop(columns=['isPartial'])
                            else:
                                interest_data_clean = interest_data
                            
                            if keyword in interest_data_clean.columns:
                                # Get average interest (0-100 scale)
                                avg_interest = interest_data_clean[keyword].mean()
                                # Check for NaN values
                                if pd and hasattr(pd, 'isna'):
                                    trend_scores[dest] = int(avg_interest) if not pd.isna(avg_interest) else 0
                                else:
                                    # Fallback if pandas not available
                                    import math
                                    trend_scores[dest] = int(avg_interest) if not math.isnan(avg_interest) else 0
                            else:
                                trend_scores[dest] = 0
                    else:
                        # No data, assign 0
                        for dest in batch:
                            trend_scores[dest] = 0
                    
                    # Rate limiting - wait between requests
                    import time
                    time.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"Failed to get trends for batch {batch}: {e}")
                    # Assign 0 for failed destinations
                    for dest in batch:
                        trend_scores[dest] = 0
            
            logger.info(f"Google Trends analysis completed for {len(trend_scores)} destinations")
            
        except Exception as e:
            logger.error(f"Failed to analyze trends with pytrends: {e}")
            return {}
        
        return trend_scores
    
    def combine_scores(self, openai_destinations: List[Dict], pytrends_scores: Dict[str, int]) -> List[Dict]:
        """
        Combine OpenAI and pytrends scores
        
        Formula: Final Score = (OpenAI Score × 0.6) + (pytrends Score × 0.4)
        
        Args:
            openai_destinations: List of destinations from OpenAI analysis
            pytrends_scores: Dictionary of pytrends scores
            
        Returns:
            List of destinations with combined scores
        """
        combined_destinations = []
        
        for dest in openai_destinations:
            name = dest.get('name', '')
            openai_score = dest.get('trend_score', 0)
            pytrends_score = pytrends_scores.get(name, 0)
            
            # Combine scores: 60% OpenAI, 40% pytrends
            combined_score = (openai_score * 0.6) + (pytrends_score * 0.4)
            
            combined_dest = {
                **dest,
                'trend_score': round(combined_score, 1),
                'openai_score': openai_score,
                'pytrends_score': pytrends_score,
                'combined_at': datetime.now().isoformat()
            }
            
            combined_destinations.append(combined_dest)
        
        # Sort by combined score (highest first)
        combined_destinations.sort(key=lambda x: x.get('trend_score', 0), reverse=True)
        
        return combined_destinations
    
    def detect_new_destinations(self, current_destinations: List[Dict]) -> List[Dict]:
        """
        Detect new destinations that weren't in the previous check
        
        Args:
            current_destinations: List of current trending destinations
            
        Returns:
            List of new destinations
        """
        # Get previously processed destinations
        processed = set(self.trends_cache.get('destinations_processed', []))
        
        # Find new destinations
        new_destinations = []
        for dest in current_destinations:
            name = dest.get('name', '')
            if name and name not in processed:
                new_destinations.append(dest)
        
        return new_destinations
    
    def discover_trending_destinations_with_pytrends(self) -> List[Dict[str, Any]]:
        """
        Discover trending destinations directly from Google Trends (pytrends)
        WITHOUT requiring news articles
        
        Uses a curated list of popular destinations and checks their trends
        
        Returns:
            List of trending destinations with scores
        """
        if not self.pytrends or not PTRENDS_AVAILABLE:
            logger.warning("pytrends not available, cannot discover trends")
            return []
        
        try:
            # Curated list of popular travel destinations to check
            # This list can be expanded or loaded from a file
            popular_destinations = [
                "Bali, Indonesia", "Paris, France", "Tokyo, Japan", "New York, USA",
                "London, UK", "Dubai, UAE", "Barcelona, Spain", "Rome, Italy",
                "Santorini, Greece", "Maldives", "Phuket, Thailand", "Mumbai, India",
                "Singapore", "Bangkok, Thailand", "Amsterdam, Netherlands", "Sydney, Australia",
                "Istanbul, Turkey", "Prague, Czech Republic", "Vienna, Austria", "Barcelona, Spain",
                "Lisbon, Portugal", "Budapest, Hungary", "Cairo, Egypt", "Marrakech, Morocco",
                "Jaipur, India", "Udaipur, India", "Goa, India", "Kerala, India",
                "Karnataka, India", "Rajasthan, India", "Himachal Pradesh, India",
                "Kyoto, Japan", "Seoul, South Korea", "Hong Kong", "Taipei, Taiwan",
                "Ho Chi Minh City, Vietnam", "Hanoi, Vietnam", "Luang Prabang, Laos",
                "Yangon, Myanmar", "Phnom Penh, Cambodia", "Manila, Philippines",
                "Cebu, Philippines", "Boracay, Philippines", "Nusa Penida, Indonesia",
                "Lombok, Indonesia", "Yogyakarta, Indonesia", "Kuala Lumpur, Malaysia",
                "Penang, Malaysia", "Langkawi, Malaysia", "Vientiane, Laos",
                "Chiang Mai, Thailand", "Pai, Thailand", "Krabi, Thailand",
                "Maui, Hawaii", "Cancun, Mexico", "Tulum, Mexico", "Cusco, Peru",
                "Machu Picchu, Peru", "Rio de Janeiro, Brazil", "São Paulo, Brazil",
                "Buenos Aires, Argentina", "Santiago, Chile", "Cartagena, Colombia",
                "Medellin, Colombia", "Quito, Ecuador", "Galapagos Islands, Ecuador",
                "Cape Town, South Africa", "Johannesburg, South Africa", "Nairobi, Kenya",
                "Zanzibar, Tanzania", "Seychelles", "Mauritius", "Reunion Island",
                "Casablanca, Morocco", "Fez, Morocco", "Alexandria, Egypt", "Luxor, Egypt",
                "Petra, Jordan", "Jerusalem, Israel", "Tel Aviv, Israel", "Beirut, Lebanon",
                "Baku, Azerbaijan", "Yerevan, Armenia", "Tbilisi, Georgia", "Almaty, Kazakhstan"
            ]
            
            logger.info(f"Checking trends for {len(popular_destinations)} popular destinations...")
            
            # Check trends for each destination
            trending_destinations = []
            
            # Process in smaller batches to avoid rate limits
            batch_size = 3
            for i in range(0, len(popular_destinations), batch_size):
                batch = popular_destinations[i:i + batch_size]
                logger.info(f"Checking batch {i//batch_size + 1}: {batch}")
                
                # Retry logic per batch to mitigate HTTP 429
                max_attempts = 3
                attempt = 1
                while attempt <= max_attempts:
                    try:
                        # Build payload with "travel" appended for better results
                        keywords = [f"{dest} travel" for dest in batch]
                        
                        self.pytrends.build_payload(
                            keywords,
                            timeframe='today 1-m',  # Last month (shorter timeframe for current trends)
                            geo='',  # Global
                            gprop=''  # Web search
                        )
                        
                        # Get interest over time
                        interest_data = self.pytrends.interest_over_time()
                        
                        if not interest_data.empty and len(interest_data) > 0:
                            # Calculate trend scores
                            for j, dest in enumerate(batch):
                                keyword = keywords[j]
                                
                                # Clean data
                                if 'isPartial' in interest_data.columns:
                                    interest_data_clean = interest_data.drop(columns=['isPartial'])
                                else:
                                    interest_data_clean = interest_data
                                
                                if keyword in interest_data_clean.columns:
                                    # Get recent average (last 2 weeks for current trends)
                                    recent_data = interest_data_clean[keyword].tail(14)
                                    avg_interest = recent_data.mean()
                                    
                                    # Calculate trend (is it increasing?)
                                    if len(recent_data) >= 7:
                                        first_half = recent_data.head(7).mean()
                                        second_half = recent_data.tail(7).mean()
                                        trend_increase = second_half - first_half
                                    else:
                                        trend_increase = 0
                                    
                                    # Only include if trending (interest > 20 and/or increasing)
                                    if avg_interest >= 20 or trend_increase > 10:
                                        score = int(avg_interest + (trend_increase * 2))  # Boost for increasing trends
                                        score = min(100, max(0, score))  # Clamp 0-100
                                        
                                        trending_destinations.append({
                                            "name": dest,
                                            "trend_score": score,
                                            "pytrends_score": int(avg_interest),
                                            "trend_increase": int(trend_increase),
                                            "reason": f"Google Trends interest: {int(avg_interest)}/100" + 
                                                     (f", trending up by {int(trend_increase)}" if trend_increase > 0 else ""),
                                            "keywords": [dest.split(',')[0].strip(), "travel", "tourism"],
                                            "category": "travel"
                                        })
                        
                        # Rate limiting between successful batches
                        import time
                        time.sleep(4)  # Slightly longer wait
                        break  # Success, exit retry loop
                    
                    except Exception as e:
                        message = str(e)
                        if "429" in message or "Rate limit" in message:
                            import random, time
                            backoff = 10 * attempt  # linear backoff
                            jitter = random.randint(0, 5)
                            wait_s = backoff + jitter
                            logger.warning(f"Rate limited for batch {batch} (attempt {attempt}/{max_attempts}). Waiting {wait_s}s...")
                            time.sleep(wait_s)
                            attempt += 1
                            continue
                        else:
                            logger.warning(f"Failed to check batch {batch}: {e}")
                            # Do not raise; continue with next batch
                            break
            
            # Sort by trend score
            trending_destinations = sorted(trending_destinations, key=lambda x: x.get('trend_score', 0), reverse=True)
            
            logger.info(f"✅ Discovered {len(trending_destinations)} trending destinations from Google Trends")
            # If none discovered, fallback to a static safe list to keep pipeline moving
            if not trending_destinations:
                logger.warning("No destinations discovered via pytrends; using fallback defaults")
                fallback = [
                    {"name": "Chiang Mai, Thailand", "trend_score": 60, "reason": "Fallback default", "keywords": ["Chiang Mai","travel","tourism"], "category": "travel", "pytrends_score": 60},
                    {"name": "Bali, Indonesia", "trend_score": 70, "reason": "Fallback default", "keywords": ["Bali","travel","tourism"], "category": "travel", "pytrends_score": 70},
                    {"name": "Tokyo, Japan", "trend_score": 65, "reason": "Fallback default", "keywords": ["Tokyo","travel","tourism"], "category": "travel", "pytrends_score": 65}
                ]
                return fallback
            return trending_destinations[:20]  # Return top 20
            
        except Exception as e:
            logger.error(f"Failed to discover trends with pytrends: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def update_trends(self, news_articles: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Update trending destinations cache
        
        NEW: Uses pytrends directly to discover trends (news articles optional/not required)
        
        Args:
            news_articles: Optional list of news articles (for backward compatibility, but not required)
            
        Returns:
            Dictionary with trending destinations and new destinations
        """
        try:
            # PRIMARY METHOD: Direct pytrends discovery (NO NEWS REQUIRED)
            if self.pytrends and PTRENDS_AVAILABLE:
                logger.info("Step 1: Discovering trending destinations directly from Google Trends (pytrends)...")
                pytrends_destinations = self.discover_trending_destinations_with_pytrends()
                
                if pytrends_destinations:
                    # Convert to standard format
                    trending_destinations = [
                        {
                            "name": dest.get("name", ""),
                            "trend_score": dest.get("trend_score", 0),
                            "reason": dest.get("reason", "Trending on Google Trends"),
                            "keywords": dest.get("keywords", []),
                            "category": dest.get("category", "travel"),
                            "openai_score": 0,  # Not using OpenAI news analysis
                            "pytrends_score": dest.get("pytrends_score", dest.get("trend_score", 0)),
                            "combined_at": datetime.now().isoformat()
                        }
                        for dest in pytrends_destinations
                    ]
                    
                    # Step 2: Detect new destinations
                    logger.info("Step 2: Detecting new destinations...")
                    new_destinations = self.detect_new_destinations(trending_destinations)
                    
                    # Step 3: Update cache
                    self.trends_cache = {
                        "last_updated": datetime.now().isoformat(),
                        "last_check_time": datetime.now().isoformat(),
                        "trending_destinations": trending_destinations,
                        "destinations_processed": list(set(
                            self.trends_cache.get('destinations_processed', []) +
                            [dest.get('name', '') for dest in trending_destinations]
                        )),
                        "articles_analyzed": 0,  # No news used
                        "openai_destinations_count": 0,  # No OpenAI news analysis
                        "pytrends_destinations_count": len(trending_destinations),
                        "new_destinations_count": len(new_destinations),
                        "method": "pytrends_direct"  # Mark as direct pytrends method
                    }
                    
                    # Save cache
                    self.save_trends_cache(self.trends_cache)
                    
                    logger.info(f"✅ Updated trends cache: {len(trending_destinations)} destinations, {len(new_destinations)} new (using direct pytrends)")
                    
                    return {
                        "trending_destinations": trending_destinations,
                        "new_destinations": new_destinations,
                        "updated": True,
                        "last_updated": self.trends_cache['last_updated'],
                        "method": "pytrends_direct"
                    }
                else:
                    # If pytrends returned nothing (e.g., due to 429), fallback to cache or defaults
                    cached = self.trends_cache.get("trending_destinations", [])
                    if cached:
                        logger.warning("Pytrends empty; falling back to cached trending destinations")
                        return {
                            "trending_destinations": cached,
                            "new_destinations": [],
                            "updated": False,
                            "last_updated": self.trends_cache.get('last_updated', datetime.now().isoformat()),
                            "method": "cache_fallback"
                        }
                    else:
                        logger.warning("Pytrends empty and cache empty; using hardcoded fallback destinations")
                        fallback = [
                            {"name": "Chiang Mai, Thailand", "trend_score": 60, "reason": "Fallback default", "keywords": ["Chiang Mai","travel","tourism"], "category": "travel", "pytrends_score": 60},
                            {"name": "Bali, Indonesia", "trend_score": 70, "reason": "Fallback default", "keywords": ["Bali","travel","tourism"], "category": "travel", "pytrends_score": 70},
                            {"name": "Tokyo, Japan", "trend_score": 65, "reason": "Fallback default", "keywords": ["Tokyo","travel","tourism"], "category": "travel", "pytrends_score": 65}
                        ]
                        self.trends_cache = {
                            "last_updated": datetime.now().isoformat(),
                            "last_check_time": datetime.now().isoformat(),
                            "trending_destinations": fallback,
                            "destinations_processed": list(set(
                                self.trends_cache.get('destinations_processed', [])
                            )),
                            "articles_analyzed": 0,
                            "openai_destinations_count": 0,
                            "pytrends_destinations_count": 0,
                            "new_destinations_count": 0,
                            "method": "fallback_defaults"
                        }
                        self.save_trends_cache(self.trends_cache)
                        return {
                            "trending_destinations": fallback,
                            "new_destinations": [],
                            "updated": True,
                            "last_updated": self.trends_cache['last_updated'],
                            "method": "fallback_defaults"
                        }
            
            # FALLBACK METHOD: News-based (for backward compatibility or if pytrends unavailable)
            if news_articles:
                logger.info("FALLBACK: Using news-based analysis (pytrends not available or failed)...")
                # Step 1: Analyze with OpenAI
                logger.info("Step 1: Analyzing news with OpenAI...")
                openai_results = self.analyze_news_with_openai(news_articles)
                openai_destinations = openai_results.get('trending_destinations', [])
                
                if not openai_destinations:
                    logger.warning("No destinations found by OpenAI analysis")
                    return {
                        "trending_destinations": [],
                        "new_destinations": [],
                        "updated": False
                    }
                
                # Step 2: Analyze with pytrends
                logger.info("Step 2: Analyzing with Google Trends (pytrends)...")
                destination_names = [dest.get('name', '') for dest in openai_destinations]
                pytrends_scores = self.analyze_with_pytrends(destination_names)
                
                # Step 3: Combine scores
                logger.info("Step 3: Combining OpenAI and pytrends scores...")
                combined_destinations = self.combine_scores(openai_destinations, pytrends_scores)
                
                # Step 4: Detect new destinations
                logger.info("Step 4: Detecting new destinations...")
                new_destinations = self.detect_new_destinations(combined_destinations)
                
                # Step 5: Update cache
                self.trends_cache = {
                    "last_updated": datetime.now().isoformat(),
                    "last_check_time": datetime.now().isoformat(),
                    "trending_destinations": combined_destinations,
                    "destinations_processed": list(set(
                        self.trends_cache.get('destinations_processed', []) +
                        [dest.get('name', '') for dest in combined_destinations]
                    )),
                    "articles_analyzed": len(news_articles),
                    "openai_destinations_count": len(openai_destinations),
                    "pytrends_destinations_count": len(pytrends_scores),
                    "new_destinations_count": len(new_destinations),
                    "method": "news_based"  # Mark as news-based method
                }
                
                # Save cache
                self.save_trends_cache(self.trends_cache)
                
                logger.info(f"✅ Updated trends cache: {len(combined_destinations)} destinations, {len(new_destinations)} new (using news)")
                
                return {
                    "trending_destinations": combined_destinations,
                    "new_destinations": new_destinations,
                    "updated": True,
                    "last_updated": self.trends_cache['last_updated'],
                    "method": "news_based"
                }
            else:
                logger.error("No news articles provided and pytrends direct discovery failed")
                return {
                    "trending_destinations": [],
                    "new_destinations": [],
                    "updated": False,
                    "error": "No news articles and pytrends unavailable"
                }
            
        except Exception as e:
            logger.error(f"Failed to update trends: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "trending_destinations": [],
                "new_destinations": [],
                "updated": False,
                "error": str(e)
            }
    
    def get_trending_destinations(self, count: int = 10) -> List[Dict]:
        """Get current trending destinations"""
        destinations = self.trends_cache.get('trending_destinations', [])
        return sorted(destinations, key=lambda x: x.get('trend_score', 0), reverse=True)[:count]
    
    def get_new_destinations(self) -> List[Dict]:
        """Get new destinations from last check"""
        # This will be populated when update_trends is called
        all_destinations = self.trends_cache.get('trending_destinations', [])
        processed = set(self.trends_cache.get('destinations_processed', []))
        
        new_destinations = [
            dest for dest in all_destinations
            if dest.get('name', '') not in processed
        ]
        
        return new_destinations
    
    def _prepare_news_summary(self, articles: List[Dict], max_articles: int = 20) -> str:
        """Prepare a summary of news articles for AI analysis"""
        if not articles:
            return "No news articles available"
        
        # Limit articles
        articles = articles[:max_articles]
        
        summary_parts = []
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'No title')
            summary = article.get('summary', article.get('description', 'No summary'))
            region = article.get('region', 'Unknown')
            
            summary_parts.append(f"{i}. Title: {title}\n   Region: {region}\n   Summary: {summary}\n")
        
        return "\n".join(summary_parts)
    
    def generate_trends_report(self) -> str:
        """Generate a human-readable trends report"""
        report = "\n=== Long Video Trending Destinations Report ===\n\n"
        
        last_updated = self.trends_cache.get('last_updated', 'Never')
        report += f"Last Updated: {last_updated}\n"
        report += f"Articles Analyzed: {self.trends_cache.get('articles_analyzed', 0)}\n\n"
        
        # Trending destinations
        destinations = self.get_trending_destinations(10)
        if destinations:
            report += "TRENDING DESTINATIONS:\n"
            for i, dest in enumerate(destinations, 1):
                name = dest.get('name', 'Unknown')
                score = dest.get('trend_score', 0)
                openai_score = dest.get('openai_score', 0)
                pytrends_score = dest.get('pytrends_score', 0)
                reason = dest.get('reason', 'N/A')
                
                report += f"  {i}. {name}\n"
                report += f"     Combined Score: {score}/100\n"
                report += f"     OpenAI: {openai_score}/100 | Google Trends: {pytrends_score}/100\n"
                report += f"     Reason: {reason}\n\n"
        
        # New destinations
        new_destinations = self.get_new_destinations()
        if new_destinations:
            report += f"\nNEW DESTINATIONS ({len(new_destinations)}):\n"
            for i, dest in enumerate(new_destinations, 1):
                name = dest.get('name', 'Unknown')
                score = dest.get('trend_score', 0)
                report += f"  {i}. {name} (Score: {score})\n"
        
        return report


def main():
    """Test trending destination detector"""
    detector = TrendingDetectorLong()
    
    # Load sample news articles
    news_file = Path("data/processed_news.json")
    if news_file.exists():
        with open(news_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('top_tourism_stories', [])
        
        if articles:
            print("Updating trends with news articles...")
            result = detector.update_trends(articles)
            
            if result.get('updated'):
                print(f"✅ Updated {len(result.get('trending_destinations', []))} destinations")
                print(f"✅ Found {len(result.get('new_destinations', []))} new destinations")
            else:
                print("❌ Failed to update trends")
        else:
            print("No news articles found")
    else:
        print("No processed_news.json found")
    
    # Generate report
    print("\n" + detector.generate_trends_report())


if __name__ == "__main__":
    main()


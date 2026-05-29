#!/usr/bin/env python3
"""
Trending Topic Detector for TripAvail AI
Uses AI to detect trending travel topics and viral content opportunities
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class TrendingTopicDetector:
    """
    Detects trending topics in travel and tourism using AI analysis
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path("data")
        self.trends_file = self.data_dir / "trending_topics.json"
        
        # Trend categories
        self.trend_categories = {
            "destinations": "Trending travel destinations",
            "activities": "Popular travel activities and experiences",
            "seasons": "Seasonal travel trends",
            "policies": "Travel policy changes and visa updates",
            "sustainability": "Eco-tourism and sustainable travel trends",
            "technology": "Travel technology and innovations",
            "events": "Upcoming events and festivals",
            "social_media": "Viral travel content on social platforms"
        }
        
        # Load existing trends
        self.trends_cache = self.load_trends_cache()
        
        logger.info("Trending Topic Detector initialized")
    
    def load_trends_cache(self) -> Dict:
        """Load cached trending topics"""
        if self.trends_file.exists():
            try:
                with open(self.trends_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load trends cache: {e}")
        
        return {
            "last_updated": None,
            "trending_topics": [],
            "trending_hashtags": [],
            "trending_regions": []
        }
    
    def save_trends_cache(self, trends: Dict):
        """Save trending topics to cache"""
        try:
            with open(self.trends_file, 'w', encoding='utf-8') as f:
                json.dump(trends, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved trends cache to {self.trends_file}")
        except Exception as e:
            logger.error(f"Failed to save trends cache: {e}")
    
    def analyze_news_for_trends(self, news_articles: List[Dict]) -> Dict[str, Any]:
        """
        Analyze news articles to identify trending topics
        
        Args:
            news_articles: List of news article dictionaries
            
        Returns:
            Dictionary with trending topics analysis
        """
        try:
            # Prepare news summary for AI analysis
            news_summary = self._prepare_news_summary(news_articles)
            
            prompt = f"""You are a travel industry trend analyst. Analyze these recent travel news articles and identify:

1. TRENDING DESTINATIONS: Which locations are mentioned most frequently or getting significant attention?
2. TRENDING TOPICS: What travel themes or subjects are gaining traction?
3. VIRAL POTENTIAL: Which stories have the highest potential to go viral on social media?
4. SEASONAL TRENDS: Any seasonal patterns or upcoming travel seasons?
5. HASHTAG OPPORTUNITIES: Suggest 10 trending hashtags for these topics

News Articles Summary:
{news_summary}

Respond in JSON format:
{{
    "trending_destinations": [
        {{"name": "Location", "trend_score": 0-100, "reason": "Why it's trending"}}
    ],
    "trending_topics": [
        {{"topic": "Topic name", "category": "Category", "virality_score": 0-100, "reason": "Why it's trending"}}
    ],
    "trending_hashtags": ["#hashtag1", "#hashtag2", ...],
    "seasonal_insights": "Brief analysis of seasonal trends",
    "viral_opportunities": [
        {{"title": "Story title", "viral_score": 0-100, "strategy": "How to leverage this"}}
    ]
}}"""

            logger.info("Analyzing news for trending topics with AI...")
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert travel industry trend analyst specializing in viral content and social media trends. You excel at identifying what will resonate with travel audiences."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
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
            
            logger.info(f"Identified {len(trends.get('trending_topics', []))} trending topics")
            return trends
            
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return {}
    
    def _prepare_news_summary(self, articles: List[Dict], max_articles: int = 20) -> str:
        """Prepare a summary of news articles for AI analysis"""
        summary = ""
        
        for i, article in enumerate(articles[:max_articles], 1):
            title = article.get('title', 'N/A')
            description = article.get('description', article.get('summary', 'N/A'))
            region = article.get('region', 'Unknown')
            
            summary += f"\n{i}. {title}\n"
            summary += f"   Region: {region}\n"
            summary += f"   Description: {description[:200]}...\n"
        
        return summary
    
    def score_content_trendiness(self, post_data: Dict[str, Any]) -> int:
        """
        Score how trendy a piece of content is (0-100)
        
        Args:
            post_data: Post data dictionary
            
        Returns:
            Trend score (0-100)
        """
        try:
            caption = post_data.get('caption', '')
            region = post_data.get('region', '')
            score = post_data.get('score', 5)
            
            # Get current trends
            trends = self.trends_cache.get('trending_topics', [])
            trending_regions = self.trends_cache.get('trending_regions', [])
            trending_hashtags = self.trends_cache.get('trending_hashtags', [])
            
            trend_score = 0
            
            # Base score from content quality
            trend_score += score * 5  # 5-10 points
            
            # Check if region is trending (+30 points)
            if any(region.lower() in tr.lower() for tr in trending_regions):
                trend_score += 30
                logger.info(f"Region '{region}' is trending +30")
            
            # Check if topic matches trends (+40 points)
            caption_lower = caption.lower()
            for trend in trends:
                topic = trend.get('topic', '').lower()
                if topic and topic in caption_lower:
                    trend_score += 40
                    logger.info(f"Topic '{topic}' is trending +40")
                    break
            
            # Check hashtag alignment (+20 points)
            post_hashtags = post_data.get('hashtags', [])
            matching_hashtags = [h for h in post_hashtags if h in trending_hashtags]
            if matching_hashtags:
                trend_score += min(20, len(matching_hashtags) * 5)
                logger.info(f"Matching trending hashtags: {matching_hashtags} +{min(20, len(matching_hashtags) * 5)}")
            
            # Recency bonus (+10 points if very recent news)
            # This would require timestamp comparison in production
            
            trend_score = min(100, trend_score)
            logger.info(f"Content trend score: {trend_score}/100")
            
            return trend_score
            
        except Exception as e:
            logger.error(f"Failed to score content trendiness: {e}")
            return 0
    
    def get_trending_hashtags(self, count: int = 30) -> List[str]:
        """Get current trending hashtags"""
        return self.trends_cache.get('trending_hashtags', [])[:count]
    
    def get_trending_destinations(self, count: int = 10) -> List[Dict]:
        """Get current trending destinations"""
        destinations = self.trends_cache.get('trending_destinations', [])
        return sorted(destinations, key=lambda x: x.get('trend_score', 0), reverse=True)[:count]
    
    def suggest_content_improvements(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest improvements to make content more trendy
        
        Args:
            post_data: Post data dictionary
            
        Returns:
            Dictionary with suggestions
        """
        try:
            caption = post_data.get('caption', '')
            region = post_data.get('region', '')
            hashtags = post_data.get('hashtags', [])
            
            trending_hashtags = self.get_trending_hashtags()
            trending_destinations = self.get_trending_destinations()
            
            suggestions = {
                "current_trend_score": self.score_content_trendiness(post_data),
                "suggested_hashtags": [],
                "suggested_improvements": [],
                "viral_opportunities": []
            }
            
            # Suggest trending hashtags not currently used
            current_hashtags_lower = [h.lower() for h in hashtags]
            suggested_hashtags = [
                h for h in trending_hashtags[:10]
                if h.lower() not in current_hashtags_lower
            ]
            suggestions["suggested_hashtags"] = suggested_hashtags[:5]
            
            # Check if destination is trending
            is_trending_destination = any(
                region.lower() in dest.get('name', '').lower()
                for dest in trending_destinations
            )
            
            if is_trending_destination:
                suggestions["suggested_improvements"].append(
                    f"✅ Great! {region} is currently trending. Emphasize this in the caption."
                )
            else:
                suggestions["suggested_improvements"].append(
                    f"💡 Consider connecting {region} to trending destinations or topics"
                )
            
            # Suggest viral angles
            suggestions["viral_opportunities"] = [
                "Use trending audio/music in video",
                "Create content around current travel challenges (sustainability, remote work)",
                "Leverage seasonal travel trends",
                "Highlight unique/unusual experiences for engagement"
            ]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return {}
    
    def update_trends(self, news_articles: List[Dict]) -> bool:
        """
        Update trending topics cache with new analysis
        
        Args:
            news_articles: List of recent news articles
            
        Returns:
            True if successful
        """
        try:
            # Analyze for trends
            trends = self.analyze_news_for_trends(news_articles)
            
            if not trends:
                return False
            
            # Update cache
            self.trends_cache = {
                "last_updated": datetime.now().isoformat(),
                "trending_topics": trends.get('trending_topics', []),
                "trending_hashtags": trends.get('trending_hashtags', []),
                "trending_destinations": trends.get('trending_destinations', []),
                "seasonal_insights": trends.get('seasonal_insights', ''),
                "viral_opportunities": trends.get('viral_opportunities', []),
                "articles_analyzed": trends.get('articles_analyzed', 0)
            }
            
            # Extract just region names for easy lookup
            self.trends_cache['trending_regions'] = [
                dest['name'] for dest in trends.get('trending_destinations', [])
            ]
            
            # Save to file
            self.save_trends_cache(self.trends_cache)
            
            logger.info("Successfully updated trends cache")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update trends: {e}")
            return False
    
    def generate_trends_report(self) -> str:
        """Generate a human-readable trends report"""
        report = "\n=== TripAvail AI Trending Topics Report ===\n\n"
        
        last_updated = self.trends_cache.get('last_updated', 'Never')
        report += f"Last Updated: {last_updated}\n"
        report += f"Articles Analyzed: {self.trends_cache.get('articles_analyzed', 0)}\n\n"
        
        # Trending destinations
        destinations = self.get_trending_destinations()
        if destinations:
            report += "\nTRENDING DESTINATIONS:\n"
            for i, dest in enumerate(destinations, 1):
                report += f"  {i}. {dest['name']} (Score: {dest.get('trend_score', 0)})\n"
                report += f"     Reason: {dest.get('reason', 'N/A')}\n"
        
        # Trending topics
        topics = self.trends_cache.get('trending_topics', [])
        if topics:
            report += "\nTRENDING TOPICS:\n"
            for i, topic in enumerate(topics[:10], 1):
                report += f"  {i}. {topic['topic']} (Virality: {topic.get('virality_score', 0)})\n"
                report += f"     Category: {topic.get('category', 'N/A')}\n"
        
        # Trending hashtags
        hashtags = self.get_trending_hashtags(15)
        if hashtags:
            report += "\nTRENDING HASHTAGS:\n"
            report += f"  {' '.join(hashtags[:15])}\n"
        
        # Seasonal insights
        seasonal = self.trends_cache.get('seasonal_insights', '')
        if seasonal:
            report += f"\nSEASONAL INSIGHTS:\n  {seasonal}\n"
        
        return report


def main():
    """Test trending topic detector"""
    detector = TrendingTopicDetector()
    
    # Test with sample news data
    sample_news = [
        {
            "title": "Bali Introduces New Sustainable Tourism Initiative",
            "description": "Bali launches eco-friendly travel program to protect environment",
            "region": "Bali, Indonesia"
        },
        {
            "title": "Digital Nomad Visas Expand to 50 Countries",
            "description": "Remote work visas become mainstream across Europe and Asia",
            "region": "Global"
        }
    ]
    
    print("\n=== Testing Trending Topic Detection ===")
    print("\nAnalyzing sample news...")
    
    # This would normally use real news data
    print("\nGenerate trends report:")
    print(detector.generate_trends_report())


if __name__ == "__main__":
    main()


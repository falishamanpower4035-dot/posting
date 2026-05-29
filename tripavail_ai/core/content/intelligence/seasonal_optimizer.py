#!/usr/bin/env python3
"""
Seasonal Content Optimizer for TripAvail AI
Optimizes content based on seasons, holidays, and travel trends
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


class SeasonalContentOptimizer:
    """
    Optimizes content based on seasonal trends, holidays, and travel patterns
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path("data")
        self.seasonal_file = self.data_dir / "seasonal_data.json"
        
        # Season definitions (Northern Hemisphere)
        self.seasons = {
            "winter": {"months": [12, 1, 2], "keywords": ["ski", "snow", "winter", "cold", "holiday"]},
            "spring": {"months": [3, 4, 5], "keywords": ["flowers", "spring", "fresh", "bloom", "mild"]},
            "summer": {"months": [6, 7, 8], "keywords": ["beach", "sun", "hot", "vacation", "summer"]},
            "autumn": {"months": [9, 10, 11], "keywords": ["fall", "autumn", "foliage", "harvest", "cool"]}
        }
        
        # Major travel holidays and events
        self.holidays = {
            "new_year": {"dates": "1/1", "travel_type": "party, celebration"},
            "valentines": {"dates": "2/14", "travel_type": "romantic, couples"},
            "spring_break": {"dates": "3/15-3/31", "travel_type": "beach, party"},
            "easter": {"dates": "variable", "travel_type": "family, cultural"},
            "summer_vacation": {"dates": "6/1-8/31", "travel_type": "beach, family, adventure"},
            "thanksgiving": {"dates": "11/24", "travel_type": "family, domestic"},
            "christmas": {"dates": "12/25", "travel_type": "family, ski, tropical escape"},
            "new_years_eve": {"dates": "12/31", "travel_type": "party, celebration, exotic"}
        }
        
        # Regional seasonal patterns
        self.regional_seasons = {
            "tropical": ["year-round destination", "dry season", "monsoon season"],
            "temperate": ["four distinct seasons", "summer peak", "winter sports"],
            "desert": ["extreme heat summer", "mild winter", "spring/fall ideal"],
            "polar": ["midnight sun summer", "aurora winter", "extreme cold"]
        }
        
        logger.info("Seasonal Content Optimizer initialized")
    
    def get_current_season(self, hemisphere: str = "northern") -> str:
        """Get current season based on hemisphere"""
        current_month = datetime.now().month
        
        for season, data in self.seasons.items():
            if current_month in data["months"]:
                return season
        
        return "summer"  # Default
    
    def get_upcoming_holidays(self, days_ahead: int = 90) -> List[Dict[str, str]]:
        """Get upcoming holidays within the specified timeframe"""
        # Simplified - in production, would calculate actual dates
        upcoming = []
        current_month = datetime.now().month
        
        holiday_months = {
            1: ["new_year"],
            2: ["valentines"],
            3: ["spring_break"],
            6: ["summer_vacation"],
            11: ["thanksgiving"],
            12: ["christmas", "new_years_eve"]
        }
        
        # Check next 3 months
        for i in range(3):
            check_month = (current_month + i) % 12 or 12
            if check_month in holiday_months:
                for holiday in holiday_months[check_month]:
                    holiday_data = self.holidays.get(holiday, {})
                    upcoming.append({
                        "name": holiday,
                        "dates": holiday_data.get("dates", "variable"),
                        "travel_type": holiday_data.get("travel_type", "general")
                    })
        
        return upcoming
    
    def analyze_seasonal_relevance(
        self,
        post_data: Dict[str, Any],
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Analyze how relevant content is for the current/target season
        
        Args:
            post_data: Post data dictionary
            target_date: Optional target date (uses current date if None)
            
        Returns:
            Dictionary with seasonal analysis
        """
        try:
            if target_date is None:
                target_date = datetime.now()
            
            caption = post_data.get('caption', '').lower()
            region = post_data.get('region', '').lower()
            
            # Determine season
            target_month = target_date.month
            current_season = None
            for season, data in self.seasons.items():
                if target_month in data["months"]:
                    current_season = season
                    break
            
            # Check seasonal keyword alignment
            season_keywords = self.seasons[current_season]["keywords"]
            matching_keywords = [kw for kw in season_keywords if kw in caption or kw in region]
            
            seasonal_score = len(matching_keywords) * 20  # 20 points per keyword
            
            # Check holiday alignment
            upcoming_holidays = self.get_upcoming_holidays()
            holiday_alignment = []
            for holiday in upcoming_holidays:
                travel_types = holiday['travel_type'].split(', ')
                if any(ttype in caption or ttype in region for ttype in travel_types):
                    holiday_alignment.append(holiday['name'])
                    seasonal_score += 30  # Bonus for holiday alignment
            
            seasonal_score = min(100, seasonal_score)
            
            analysis = {
                "target_season": current_season,
                "seasonal_score": seasonal_score,
                "matching_keywords": matching_keywords,
                "holiday_alignment": holiday_alignment,
                "is_timely": seasonal_score >= 60,
                "recommendations": self._generate_seasonal_recommendations(
                    current_season,
                    upcoming_holidays,
                    caption,
                    region
                )
            }
            
            logger.info(f"Seasonal relevance score: {seasonal_score}/100 for {current_season}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze seasonal relevance: {e}")
            return {}
    
    def _generate_seasonal_recommendations(
        self,
        season: str,
        holidays: List[Dict],
        caption: str,
        region: str
    ) -> List[str]:
        """Generate recommendations for seasonal optimization"""
        recommendations = []
        
        # Season-specific recommendations
        season_keywords = self.seasons[season]["keywords"]
        if not any(kw in caption for kw in season_keywords):
            recommendations.append(
                f"Add {season} keywords: {', '.join(season_keywords[:3])}"
            )
        
        # Holiday recommendations
        if holidays and not any(h['name'] in caption for h in holidays):
            next_holiday = holidays[0]
            recommendations.append(
                f"Align with upcoming {next_holiday['name']} ({next_holiday['travel_type']})"
            )
        
        # Regional season recommendations
        if "beach" in region or "tropical" in region:
            if season in ["winter"]:
                recommendations.append(
                    "Emphasize 'winter escape' and 'warm weather getaway' angles"
                )
        elif "ski" in region or "mountain" in region:
            if season in ["winter"]:
                recommendations.append(
                    "Highlight winter sports and snow activities"
                )
        
        return recommendations
    
    def prioritize_content_by_season(
        self,
        posts: List[Dict[str, Any]],
        target_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Prioritize posts based on seasonal relevance
        
        Args:
            posts: List of post dictionaries
            target_date: Optional target date
            
        Returns:
            List of posts sorted by seasonal priority
        """
        results = []
        
        for post in posts:
            analysis = self.analyze_seasonal_relevance(post, target_date)
            results.append({
                "post": post,
                "seasonal_analysis": analysis,
                "priority_score": analysis.get('seasonal_score', 0)
            })
        
        # Sort by priority score (descending)
        results.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info(f"Prioritized {len(results)} posts by seasonal relevance")
        return results
    
    def suggest_seasonal_content(
        self,
        target_date: Optional[datetime] = None,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        Suggest content ideas based on season and upcoming events
        
        Args:
            target_date: Optional target date
            count: Number of suggestions
            
        Returns:
            List of content suggestions
        """
        try:
            if target_date is None:
                target_date = datetime.now()
            
            current_season = self.get_current_season()
            upcoming_holidays = self.get_upcoming_holidays()
            
            prompt = f"""You are a travel content strategist. Suggest {count} engaging travel content ideas for {current_season} season.

Consider:
- Current season: {current_season}
- Upcoming holidays/events: {', '.join([h['name'] for h in upcoming_holidays])}
- Travel trends for this time of year
- Viral potential and engagement

For each suggestion, provide:
1. Content topic
2. Target region/destination
3. Why it's timely
4. Engagement potential (high/medium/low)

Respond in JSON format:
[
    {{
        "topic": "Content topic",
        "destination": "Destination/region",
        "reason": "Why it's timely",
        "engagement_potential": "high/medium/low",
        "suggested_hashtags": ["#hashtag1", "#hashtag2"]
    }}
]"""

            logger.info(f"Requesting seasonal content suggestions for {current_season}...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert travel content strategist specializing in seasonal and trending content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            suggestions = json.loads(content)
            logger.info(f"Generated {len(suggestions)} seasonal content suggestions")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate seasonal suggestions: {e}")
            return []
    
    def optimize_for_season(
        self,
        post_data: Dict[str, Any],
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Optimize post content for seasonal relevance
        
        Args:
            post_data: Post data dictionary
            target_date: Optional target date
            
        Returns:
            Optimized post data with seasonal enhancements
        """
        try:
            # Analyze current seasonal relevance
            analysis = self.analyze_seasonal_relevance(post_data, target_date)
            
            # If already highly seasonal, return as-is
            if analysis.get('seasonal_score', 0) >= 80:
                logger.info("Content already highly seasonal, no optimization needed")
                return post_data
            
            # Get AI-powered optimization
            caption = post_data.get('caption', '')
            region = post_data.get('region', '')
            hashtags = post_data.get('hashtags', [])
            current_season = analysis.get('target_season', 'summer')
            
            prompt = f"""Optimize this travel content for {current_season} season:

CURRENT CAPTION: {caption}
REGION: {region}
CURRENT HASHTAGS: {', '.join(hashtags)}
SEASON: {current_season}

Make it more seasonally relevant while maintaining the core message. Add seasonal keywords, adjust tone, and suggest better hashtags.

Respond in JSON:
{{
    "optimized_caption": "Enhanced caption",
    "seasonal_angle": "Main seasonal angle",
    "recommended_hashtags": ["#hashtag1", "#hashtag2", ...],
    "improvements_made": ["Improvement 1", "Improvement 2"]
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a travel content optimization expert specializing in seasonal content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            optimization = json.loads(content)
            
            # Create optimized post
            optimized_post = post_data.copy()
            optimized_post['caption'] = optimization.get('optimized_caption', caption)
            optimized_post['hashtags'] = optimization.get('recommended_hashtags', hashtags)
            optimized_post['seasonal_optimization'] = {
                "applied": True,
                "season": current_season,
                "improvements": optimization.get('improvements_made', []),
                "seasonal_angle": optimization.get('seasonal_angle', '')
            }
            
            logger.info("Successfully optimized content for seasonal relevance")
            return optimized_post
            
        except Exception as e:
            logger.error(f"Failed to optimize for season: {e}")
            return post_data
    
    def generate_seasonal_report(self) -> str:
        """Generate seasonal content strategy report"""
        report = "\n=== TripAvail AI Seasonal Content Report ===\n\n"
        
        current_date = datetime.now()
        current_season = self.get_current_season()
        upcoming_holidays = self.get_upcoming_holidays()
        
        report += f"Current Date: {current_date.strftime('%B %d, %Y')}\n"
        report += f"Current Season: {current_season.upper()}\n\n"
        
        # Season details
        season_data = self.seasons[current_season]
        report += f"SEASONAL KEYWORDS:\n"
        report += f"  {', '.join(season_data['keywords'])}\n\n"
        
        # Upcoming holidays
        if upcoming_holidays:
            report += "UPCOMING HOLIDAYS (Next 90 Days):\n"
            for holiday in upcoming_holidays:
                report += f"  - {holiday['name'].replace('_', ' ').title()}\n"
                report += f"    Travel Type: {holiday['travel_type']}\n"
        
        # Content suggestions
        report += "\n\nRECOMMENDED CONTENT FOCUS:\n"
        suggestions = self.suggest_seasonal_content(count=3)
        for i, suggestion in enumerate(suggestions, 1):
            report += f"\n{i}. {suggestion.get('topic', 'N/A')}\n"
            report += f"   Destination: {suggestion.get('destination', 'N/A')}\n"
            report += f"   Engagement Potential: {suggestion.get('engagement_potential', 'N/A')}\n"
        
        return report


def main():
    """Test seasonal optimizer"""
    optimizer = SeasonalContentOptimizer()
    
    print(optimizer.generate_seasonal_report())
    
    # Test seasonal analysis
    sample_post = {
        "caption": "Discover the beautiful beaches of Thailand! Perfect for your next vacation.",
        "region": "Thailand",
        "hashtags": ["#Thailand", "#Travel", "#Beach"]
    }
    
    print("\n=== Testing Seasonal Analysis ===")
    analysis = optimizer.analyze_seasonal_relevance(sample_post)
    print(f"\nSeasonal Score: {analysis.get('seasonal_score', 0)}/100")
    print(f"Target Season: {analysis.get('target_season', 'N/A')}")
    print(f"Is Timely: {analysis.get('is_timely', False)}")
    
    if analysis.get('recommendations'):
        print("\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"  - {rec}")


if __name__ == "__main__":
    main()


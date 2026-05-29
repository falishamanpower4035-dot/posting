#!/usr/bin/env python3
"""
Engagement Predictor for TripAvail AI
Predicts social media engagement using AI analysis
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class EngagementPredictor:
    """
    Predicts engagement for social media content using AI analysis
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path("data")
        self.history_file = self.data_dir / "engagement_history.json"
        
        # Engagement factors and their weights
        self.engagement_factors = {
            "visual_appeal": 25,      # Quality and appeal of visuals
            "caption_quality": 20,     # Caption engagement and storytelling
            "trending_alignment": 20,  # Alignment with trends
            "hashtag_strategy": 15,    # Hashtag effectiveness
            "timing": 10,              # Posting time optimization
            "platform_fit": 10         # Platform appropriateness
        }
        
        # Platform engagement benchmarks (average engagement rates)
        self.platform_benchmarks = {
            "instagram": {"low": 1.0, "medium": 3.0, "high": 6.0},
            "tiktok": {"low": 5.0, "medium": 10.0, "high": 20.0},
            "youtube": {"low": 2.0, "medium": 4.0, "high": 8.0},
            "facebook": {"low": 0.5, "medium": 1.5, "high": 3.0}
        }
        
        logger.info("Engagement Predictor initialized")
    
    def predict_engagement(
        self,
        post_data: Dict[str, Any],
        platform: str = "instagram"
    ) -> Dict[str, Any]:
        """
        Predict engagement metrics for a post
        
        Args:
            post_data: Post data dictionary
            platform: Target social media platform
            
        Returns:
            Dictionary with engagement predictions
        """
        try:
            caption = post_data.get('caption', '')
            region = post_data.get('region', 'Unknown')
            hashtags = post_data.get('hashtags', [])
            score = post_data.get('score', 5)
            
            logger.info(f"Predicting engagement for post on {platform}...")
            
            # Analyze with AI
            analysis = self._ai_engagement_analysis(caption, region, hashtags, platform)
            
            # Calculate engagement scores
            scores = self._calculate_engagement_scores(analysis, score, hashtags, platform)
            
            # Generate predictions
            predictions = {
                "platform": platform,
                "predicted_engagement_rate": scores['overall_score'],
                "engagement_level": self._classify_engagement(scores['overall_score'], platform),
                "factor_scores": scores['factors'],
                "estimated_metrics": self._estimate_metrics(scores['overall_score'], platform),
                "strengths": analysis.get('strengths', []),
                "weaknesses": analysis.get('weaknesses', []),
                "recommendations": analysis.get('recommendations', []),
                "viral_potential": scores['viral_potential'],
                "predicted_at": datetime.now().isoformat()
            }
            
            logger.info(f"Predicted engagement rate: {predictions['predicted_engagement_rate']:.2f}%")
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to predict engagement: {e}")
            return {}
    
    def _ai_engagement_analysis(
        self,
        caption: str,
        region: str,
        hashtags: List[str],
        platform: str
    ) -> Dict[str, Any]:
        """Use AI to analyze engagement potential"""
        try:
            prompt = f"""You are a social media engagement expert. Analyze this travel content for {platform}:

CAPTION: {caption}
REGION: {region}
HASHTAGS: {', '.join(hashtags[:10])}
PLATFORM: {platform}

Analyze the engagement potential considering:
1. Caption quality (hook, storytelling, call-to-action)
2. Visual appeal indicators from description
3. Hashtag strategy effectiveness
4. Platform-specific best practices
5. Viral potential

Respond in JSON format:
{{
    "strengths": ["Strength 1", "Strength 2", ...],
    "weaknesses": ["Weakness 1", "Weakness 2", ...],
    "recommendations": ["Recommendation 1", "Recommendation 2", ...],
    "caption_hook_score": 0-10,
    "hashtag_effectiveness": 0-10,
    "platform_optimization": 0-10,
    "viral_potential_score": 0-10,
    "overall_assessment": "Brief overall assessment"
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert in {platform} engagement optimization and viral content creation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            analysis = json.loads(content)
            return analysis
            
        except Exception as e:
            logger.error(f"AI engagement analysis failed: {e}")
            return {
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "caption_hook_score": 5,
                "hashtag_effectiveness": 5,
                "platform_optimization": 5,
                "viral_potential_score": 5
            }
    
    def _calculate_engagement_scores(
        self,
        ai_analysis: Dict[str, Any],
        content_score: int,
        hashtags: List[str],
        platform: str
    ) -> Dict[str, Any]:
        """Calculate detailed engagement scores"""
        
        # Factor scores (0-100)
        factors = {
            "visual_appeal": min(100, content_score * 10),  # Based on content quality score
            "caption_quality": ai_analysis.get('caption_hook_score', 5) * 10,
            "trending_alignment": ai_analysis.get('platform_optimization', 5) * 10,
            "hashtag_strategy": ai_analysis.get('hashtag_effectiveness', 5) * 10,
            "timing": 70,  # Would be calculated based on posting schedule
            "platform_fit": ai_analysis.get('platform_optimization', 5) * 10
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            factors[factor] * (weight / 100)
            for factor, weight in self.engagement_factors.items()
        ) / 100
        
        # Viral potential (0-100)
        viral_potential = ai_analysis.get('viral_potential_score', 5) * 10
        
        return {
            "overall_score": overall_score,
            "factors": factors,
            "viral_potential": viral_potential
        }
    
    def _classify_engagement(self, score: float, platform: str) -> str:
        """Classify engagement level based on score"""
        benchmarks = self.platform_benchmarks.get(platform, self.platform_benchmarks['instagram'])
        
        if score >= benchmarks['high']:
            return "HIGH"
        elif score >= benchmarks['medium']:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _estimate_metrics(self, engagement_rate: float, platform: str) -> Dict[str, str]:
        """Estimate engagement metrics"""
        # Simplified estimation (would use historical data in production)
        
        base_followers = 10000  # Assumed follower count
        estimated_engagement = int(base_followers * (engagement_rate / 100))
        
        metrics = {
            "estimated_likes": f"{int(estimated_engagement * 0.7):,}",
            "estimated_comments": f"{int(estimated_engagement * 0.1):,}",
            "estimated_shares": f"{int(estimated_engagement * 0.05):,}",
            "estimated_saves": f"{int(estimated_engagement * 0.15):,}"
        }
        
        if platform == "youtube":
            metrics["estimated_views"] = f"{int(estimated_engagement * 5):,}"
        elif platform == "tiktok":
            metrics["estimated_views"] = f"{int(estimated_engagement * 10):,}"
        
        return metrics
    
    def compare_posts(
        self,
        posts: List[Dict[str, Any]],
        platform: str = "instagram"
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple posts and rank by predicted engagement
        
        Args:
            posts: List of post data dictionaries
            platform: Target platform
            
        Returns:
            List of posts with predictions, sorted by engagement
        """
        results = []
        
        for post in posts:
            prediction = self.predict_engagement(post, platform)
            results.append({
                "post": post,
                "prediction": prediction,
                "ranking_score": prediction.get('predicted_engagement_rate', 0)
            })
        
        # Sort by ranking score (descending)
        results.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        logger.info(f"Ranked {len(results)} posts by predicted engagement")
        return results
    
    def optimize_posting_time(self, platform: str, target_audience: str = "global") -> Dict[str, Any]:
        """
        Suggest optimal posting times
        
        Args:
            platform: Social media platform
            target_audience: Target audience (global, us, europe, asia)
            
        Returns:
            Dictionary with optimal posting times
        """
        # Platform-specific optimal times (simplified)
        optimal_times = {
            "instagram": {
                "global": ["18:00-21:00", "11:00-13:00"],
                "us": ["19:00-21:00", "11:00-13:00"],
                "europe": ["18:00-20:00", "12:00-14:00"],
                "asia": ["20:00-22:00", "12:00-14:00"]
            },
            "tiktok": {
                "global": ["18:00-22:00", "06:00-09:00"],
                "us": ["19:00-23:00", "06:00-09:00"],
                "europe": ["17:00-21:00", "07:00-09:00"],
                "asia": ["19:00-23:00", "06:00-09:00"]
            },
            "youtube": {
                "global": ["14:00-16:00", "19:00-21:00"],
                "us": ["14:00-17:00", "20:00-22:00"],
                "europe": ["14:00-17:00", "19:00-21:00"],
                "asia": ["18:00-21:00", "12:00-14:00"]
            },
            "facebook": {
                "global": ["09:00-12:00", "13:00-15:00"],
                "us": ["09:00-11:00", "13:00-15:00"],
                "europe": ["09:00-12:00", "14:00-16:00"],
                "asia": ["10:00-12:00", "15:00-17:00"]
            }
        }
        
        times = optimal_times.get(platform, {}).get(target_audience, ["18:00-21:00"])
        
        return {
            "platform": platform,
            "target_audience": target_audience,
            "optimal_times": times,
            "best_days": ["Monday", "Wednesday", "Friday", "Sunday"],
            "avoid_days": ["Saturday"],
            "timezone_note": "All times in local audience timezone"
        }
    
    def generate_engagement_report(self, post_data: Dict[str, Any], platforms: List[str]) -> str:
        """Generate comprehensive engagement report for multiple platforms"""
        report = "\n=== TripAvail AI Engagement Prediction Report ===\n\n"
        
        caption = post_data.get('caption', '')[:100]
        region = post_data.get('region', 'Unknown')
        
        report += f"Content: {caption}...\n"
        report += f"Region: {region}\n\n"
        
        for platform in platforms:
            prediction = self.predict_engagement(post_data, platform)
            
            report += f"\n{platform.upper()} PREDICTIONS:\n"
            report += f"  Engagement Rate: {prediction.get('predicted_engagement_rate', 0):.2f}%\n"
            report += f"  Engagement Level: {prediction.get('engagement_level', 'N/A')}\n"
            report += f"  Viral Potential: {prediction.get('viral_potential', 0):.1f}/100\n"
            
            metrics = prediction.get('estimated_metrics', {})
            if metrics:
                report += f"  Estimated Metrics:\n"
                for metric, value in metrics.items():
                    report += f"    - {metric.replace('estimated_', '').title()}: {value}\n"
            
            strengths = prediction.get('strengths', [])
            if strengths:
                report += f"  Strengths: {', '.join(strengths[:3])}\n"
            
            recommendations = prediction.get('recommendations', [])
            if recommendations:
                report += f"  Top Recommendation: {recommendations[0]}\n"
        
        return report


def main():
    """Test engagement predictor"""
    predictor = EngagementPredictor()
    
    # Test prediction
    sample_post = {
        "caption": "Discover the stunning beaches of Maldives 🏝️ Crystal clear waters, white sand, and unforgettable sunsets await! Book your dream vacation today. #Maldives #TravelGoals #BeachLife",
        "region": "Maldives",
        "hashtags": ["#Maldives", "#TravelGoals", "#BeachLife", "#Paradise", "#TravelPhotography"],
        "score": 8
    }
    
    print("\n=== Testing Engagement Predictor ===")
    
    # Generate report for all platforms
    report = predictor.generate_engagement_report(
        sample_post,
        platforms=["instagram", "tiktok", "youtube", "facebook"]
    )
    print(report)
    
    # Test posting time optimization
    print("\n=== Optimal Posting Times ===")
    for platform in ["instagram", "tiktok"]:
        times = predictor.optimize_posting_time(platform, "global")
        print(f"\n{platform.upper()}:")
        print(f"  Best Times: {', '.join(times['optimal_times'])}")
        print(f"  Best Days: {', '.join(times['best_days'])}")


if __name__ == "__main__":
    main()


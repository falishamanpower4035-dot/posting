#!/usr/bin/env python3
"""
Story Analyzer - Analyzes news depth and determines optimal video parameters
Ensures each video tells a complete, coherent story
"""

import os
from typing import Dict, Any, Tuple
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class StoryAnalyzer:
    """
    Analyzes news content depth and determines:
    - Optimal video length (20-45 seconds)
    - Number of images needed (6-12)
    - Key story beats to visualize
    - Narrative structure for voiceover
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        logger.info("Story Analyzer initialized")
    
    def analyze_story(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep analysis of news story to determine video parameters
        
        Args:
            topic: News topic with title, summary, region, score
        
        Returns:
            Dict with:
            - duration: seconds (20-45)
            - image_count: number of images (6-12)
            - story_beats: list of visual moments to show
            - narrative_script: 60-150 word voiceover script
            - context_caption: explains what's happening (200-250 chars)
        """
        title = topic.get('title', '')
        summary = topic.get('summary', '')
        region = topic.get('region', 'Unknown')
        score = topic.get('score', 0)
        
        prompt = f"""
Analyze this tourism news story and create a VIDEO PRODUCTION PLAN.

NEWS STORY:
Title: {title}
Summary: {summary}
Region: {region}
Relevance Score: {score}/10

YOUR TASK:
You are a video producer. Analyze this story and determine:

1. VIDEO DURATION (20-45 seconds):
   - Simple announcement (new route, price change) = 20-25 sec
   - Moderate story (new attraction, event) = 25-35 sec
   - Complex story (cultural phenomenon, transformation) = 35-45 sec

2. IMAGE COUNT (AS MANY AS NEEDED):
   - Each image should represent a distinct "story beat"
   - NO LIMITS - use as many images as the story needs
   - Typical range: 6-20 images depending on story complexity
   - Each image should show ~3-4 seconds
   - Short video (20-25s) = 6-8 images
   - Medium video (25-35s) = 8-12 images
   - Long video (35-45s) = 12-20 images
   - Complex stories can use even more if needed

3. STORY BEATS:
   - List specific visual moments/scenes to show (NO ARTIFICIAL LIMITS)
   - Each beat = one image
   - Order them in narrative sequence (beginning → middle → end)
   - Use as many beats as needed to tell the complete story
   - Examples: "Ancient temple at sunrise", "Local artisan crafting pottery", "Tourist smiling with locals"

4. NARRATIVE SCRIPT (60-150 words):
   - Write a COMPLETE voiceover that EXPLAINS THE NEWS
   - Tell viewers WHAT is happening, WHERE, and WHY it matters
   - Use storytelling structure: Setup → Details → Payoff
   - NO vague language like "discover" or "explore"
   - YES specific details: names, numbers, facts
   - Example: "Bangkok's street food scene just changed forever. Starting this month, 500 vendors across Chinatown are launching late-night tasting menus. For just 300 baht, you'll experience five dishes crafted by third-generation cooks. This isn't your typical street food tour. Each vendor shares their family's story, from their grandmother's secret recipe to why they're still here after 60 years. The city's culinary heritage, served on a plastic stool."

5. CONTEXT CAPTION (200-250 characters):
   - Explain WHAT the news is about in 1-2 sentences
   - Give viewers context so they understand the story
   - Example: "Bangkok's Chinatown vendors are launching tasting menus that tell 60 years of family history. Street food just became storytelling."
   - NO generic travel hype
   - YES actual news explanation

6. KEYWORDS & LOCATIONS (for image and voiceover alignment):
   - keywords.primary: core nouns/entities (event, place, subject)
   - keywords.secondary: supporting terms (activities, objects)
   - keywords.visual: what should be visually shown (shots, scenes)
   - keywords.narrative: terms likely spoken in VO to align images
   - mood: one of [festive, calm, urgent, inspiring, luxurious, adventurous]
   - locations: {{ city, region, country, place_names: [...] }}

Return JSON format:
{{
  "duration": 35,
  "image_count": 14,
  "story_beats": [
    "Bangkok's Chinatown street at dusk",
    "Elderly vendor cooking at wok station",
    "Close-up of sizzling pad thai",
    "Tourist tasting food with chopsticks",
    "Vendor smiling and talking",
    "Family photo on vendor stall wall",
    "Multiple dishes laid out on table",
    "Crowded night market scene",
    "Vendor and tourist laughing together",
    "Wide shot of illuminated street",
    "Close-up of menu with prices",
    "Vendors preparing ingredients",
    "Tourists gathering around stall",
    "Sunset over Chinatown rooftops"
  ],
  "narrative_script": "Full 60-150 word voiceover that explains the news story...",
  "context_caption": "200-250 char explanation of what's happening",
  "complexity": "moderate",
  "keywords": {{
    "primary": ["Chinatown", "street food", "vendors"],
    "secondary": ["tasting menu", "family recipes", "night market"],
    "visual": ["wok flames", "crowds", "menu close-up"],
    "narrative": ["heritage", "generations", "affordable"],
    "mood": "inspiring"
  }},
  "locations": {{
    "city": "Bangkok",
    "region": "Chinatown",
    "country": "Thailand",
    "place_names": ["Yaowarat Road"]
  }}
}}

IMPORTANT: Use as many story beats as needed - NO LIMITS (6, 10, 15, 20+ images are all fine).
The example shows 14 images, but you can use MORE or LESS based on the story's needs.

COMPLEXITY LEVELS:
- simple: Basic announcement, straightforward info
- moderate: Interesting development, requires some context
- complex: Deep cultural story, transformation, significant impact
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a video producer analyzing tourism news to create coherent, story-driven short videos. Your job is to ensure each video tells a COMPLETE story that viewers can understand without reading additional context. Be specific, use real details, and create narrative arcs. Output strict JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1100
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Clean markdown formatting
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            analysis = json.loads(content)
            
            # Validate parameters (with expanded ranges)
            if not (20 <= analysis.get('duration', 0) <= 60):
                logger.warning(f"Invalid duration {analysis.get('duration')}, defaulting to 30s")
                analysis['duration'] = 30
            
            # NO upper limit on images! Only check minimum
            if analysis.get('image_count', 0) < 5:
                logger.warning(f"Image count too low {analysis.get('image_count')}, defaulting to 8")
                analysis['image_count'] = 8
            
            # Ensure keywords/locations exist
            analysis.setdefault('keywords', {
                'primary': [], 'secondary': [], 'visual': [], 'narrative': [], 'mood': 'inspiring'
            })
            analysis.setdefault('locations', {
                'city': '', 'region': topic.get('region', ''), 'country': '', 'place_names': []
            })
            
            logger.info(f"Story analysis complete: {analysis['duration']}s, {analysis['image_count']} images, {analysis['complexity']} complexity")
            return analysis
        
        except Exception as e:
            logger.error(f"Story analysis failed: {e}, using defaults")
            # Fallback to moderate defaults (expanded)
            return {
                "duration": 30,
                "image_count": 12,
                "story_beats": [
                    f"{region} landscape establishing shot",
                    "Main attraction or venue",
                    "Close-up of key element",
                    "People experiencing the attraction",
                    "Cultural or local element",
                    "Food or dining scene",
                    "People interacting with locals",
                    "Activity or event in progress",
                    "Scenic view or panorama",
                    "Detail shot capturing essence",
                    "Crowd or atmosphere",
                    "Signature moment or finale"
                ],
                "narrative_script": f"{title}. {summary}",
                "context_caption": f"Travel news from {region}: {title[:150]}",
                "complexity": "moderate",
                "keywords": {
                    "primary": [region],
                    "secondary": ["tourism", "travel"],
                    "visual": ["landmarks", "crowds"],
                    "narrative": ["update", "announcement"],
                    "mood": "informative"
                },
                "locations": {
                    "city": "",
                    "region": region,
                    "country": "",
                    "place_names": []
                }
            }


def main():
    """Test story analyzer"""
    analyzer = StoryAnalyzer()
    
    # Test with sample news
    test_topic = {
        "title": "Bangkok Street Food Vendors Launch Tasting Menus Showcasing 60 Years of Family Recipes",
        "summary": "Over 500 street food vendors in Bangkok's Chinatown are introducing curated tasting menus that highlight traditional family recipes passed down through generations. For 300 baht, visitors can experience five signature dishes while learning the personal stories behind each vendor's culinary heritage.",
        "region": "Bangkok, Thailand",
        "score": 8
    }
    
    print("\n=== Testing Story Analyzer ===\n")
    print(f"Input: {test_topic['title'][:60]}...")
    
    analysis = analyzer.analyze_story(test_topic)
    
    print(f"\n[ANALYSIS RESULTS]")
    print(f"Duration: {analysis['duration']} seconds")
    print(f"Image Count: {analysis['image_count']} images")
    print(f"Complexity: {analysis['complexity']}")
    
    print(f"\n[STORY BEATS]")
    for i, beat in enumerate(analysis['story_beats'], 1):
        print(f"  {i}. {beat}")
    
    print(f"\n[NARRATIVE SCRIPT] ({len(analysis['narrative_script'].split())} words)")
    print(f"  {analysis['narrative_script']}")
    
    print(f"\n[CONTEXT CAPTION] ({len(analysis['context_caption'])} chars)")
    print(f"  {analysis['context_caption']}")


if __name__ == "__main__":
    main()


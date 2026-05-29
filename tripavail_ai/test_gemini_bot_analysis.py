#!/usr/bin/env python3
"""
Gemini 2.5 Pro Analysis - TripAvail AI Bot Architecture Review
Tests the bot's design and provides intelligent recommendations
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from google import genai
from google.genai import types


def analyze_bot_architecture():
    """Use Gemini 2.5 Pro with thinking mode to analyze the bot's architecture"""
    
    # Set API key
    os.environ["GEMINI_API_KEY"] = "AIzaSyCFMtZlP_pSB7759iOjD4x4Pmj9qJ9E3Fw"
    
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-pro"
    
    # Comprehensive bot analysis prompt
    analysis_prompt = """
# TripAvail AI Bot - Architecture Analysis Request

I have an AI-powered travel content automation bot with the following features and architecture:

## CORE FEATURES:
1. **Automated News Fetching** - Fetches tourism news every hour using NewsData.io
2. **Story-Driven Content System** - AI analyzes story depth and determines:
   - Dynamic video duration (20-60 seconds based on complexity)
   - Intelligent image count (5-20+ images, no artificial limits)
   - Story beats for targeted visual search
   - Documentary-style narrative scripts
3. **Multi-Platform Posting** - Auto-posts to Facebook and YouTube (Shorts format)
4. **Auto-Deletion** - Removes posts after 8+ hours to maintain freshness
5. **Quality Filtering** - Only processes news with AI score >= 7

## MEDIA GENERATION PIPELINE:
- **Images**: 3-layer fallback system (Unsplash → Pexels → DALL-E HD)
- **Thumbnails**: Stability AI SDXL for 9:16 YouTube thumbnails
- **Voiceovers**: ElevenLabs Premium + OpenAI TTS (6 voice options, cinematic scripts)
- **Videos**: 9:16 vertical format, 60 FPS, HD quality, Ken Burns effects
- **Audio**: Background music with intelligent ducking during narration

## CONTENT INTELLIGENCE:
- **Story Analyzer**: Determines optimal video parameters from news content
- **Trending Detection**: AI-powered trending topic identification
- **Engagement Prediction**: Multi-platform engagement rate prediction
- **Seasonal Optimization**: Automatic seasonal content adjustment

## ARCHITECTURE:
```
core/
├── news/           # News fetching & tourism editing
├── content/        # Post manager, story analyzer, caption generation
├── media/          # Images, video, audio generation
│   ├── images/     # Hybrid generator, thumbnail generator
│   ├── video/      # Pro video generator, voiceover, audio mixing
│   └── audio/      # Music library, ducking, effects
├── social/         # Facebook & YouTube posting
└── pipeline/       # Orchestration & locking

data/posts/
└── post_XXX/       # Isolated directories per post
    ├── images/     # Story-beat matched images
    ├── audio/      # Voiceover + mixed audio
    ├── video/      # Draft + final videos
    └── metadata.json
```

## AUTOMATION WORKFLOW:
1. **Hourly Cycle**: Wait 1 hour → Fetch news → Process with AI tourism editor
2. **Content Generation**: Analyze story → Generate images → Create voiceover → Build video
3. **Auto-Posting**: Post to Facebook (landscape/square) & YouTube (9:16 Shorts)
4. **Cleanup**: Auto-delete posts 8+ hours old

## CURRENT STACK:
- Python 3.8+
- OpenAI GPT-4 (story analysis, captions, scripts)
- ElevenLabs Premium (high-quality voiceovers)
- Stability AI (SDXL thumbnails)
- Unsplash/Pexels/DALL-E (images)
- MoviePy (video editing)
- FFmpeg (video processing)
- Meta Graph API (Facebook)
- YouTube Data API v3

## QUALITY FEATURES:
- Ultra Premium: 100% JPEG, HD DALL-E, 60 FPS, 320k audio
- Story-driven: Each video tells complete story with context
- Professional: Documentary-quality narration and visuals
- Intelligent: Dynamic parameters based on content depth
- Isolated: Each post has own directory structure

---

## YOUR TASK:
As an expert AI system architect with deep knowledge of content automation, social media algorithms, and production pipelines, please analyze this system and provide:

1. **Architecture Assessment** (1-10 score with reasoning)
   - Is the modular structure optimal?
   - Are there architectural anti-patterns?
   - Is the story-driven approach sound?

2. **Scalability Analysis**
   - Can this handle 100+ posts/day?
   - What are the bottlenecks?
   - API rate limit concerns?

3. **Content Quality Evaluation**
   - Is the story-driven system better than fixed-parameter systems?
   - Are the AI-generated scripts truly "premium"?
   - Is 20-60 second dynamic duration optimal for Shorts?

4. **Cost Optimization Opportunities**
   - Where is money being wasted?
   - Better API choices available?
   - Caching opportunities?

5. **Security & Reliability Concerns**
   - What could break in production?
   - Error handling sufficient?
   - Data loss risks?

6. **Social Media Algorithm Optimization**
   - Does this content match YouTube Shorts algorithm preferences?
   - Facebook Reels algorithm considerations?
   - Optimal posting frequency?

7. **Top 5 Improvements** (Prioritized)
   - What would have the biggest impact?
   - Quick wins vs long-term investments?

8. **Competitive Analysis**
   - How does this compare to professional travel content automation?
   - Unique advantages?
   - Missing features?

Please be thorough, critical, and actionable. Focus on real-world production deployment.
"""
    
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=analysis_prompt),
            ],
        ),
    ]
    
    generate_content_config = types.GenerateContentConfig(
        thinking_config = types.ThinkingConfig(
            thinking_budget=-1,  # Unlimited thinking time
        ),
    )

    print("="*80)
    print("GEMINI 2.5 PRO - TRIPAVAIL AI BOT ANALYSIS")
    print("="*80)
    print("\n🤖 Analyzing bot architecture with deep thinking mode...\n")
    print("-"*80)
    print()

    try:
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        
        print("\n\n" + "="*80)
        print("✅ ANALYSIS COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_bot_architecture()


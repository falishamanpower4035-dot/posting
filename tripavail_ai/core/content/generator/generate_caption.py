"""
Caption & Hashtag Generator for TripAvail AI
Transforms AI-filtered tourism stories into engaging social media content
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CaptionGenerator:
    """Generates social media captions and hashtags from tourism news"""
    
    def __init__(self):
        """Initialize the caption generator"""
        self.openai_client = OpenAI()
        
        # File paths
        self.topics_file = "data/processed_news.json"
        self.posts_file = "data/posts.json"
        self.log_file = "logs/caption_log.txt"
        
        # Ensure directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Note: Logging configured centrally via core.utils.logging_setup
        # No need for logger.add() here - will use centralized app.log
        
    def load_topics(self) -> List[Dict[str, Any]]:
        """Load tourism topics from processed news"""
        try:
            if not os.path.exists(self.topics_file):
                logger.warning(f"Topics file {self.topics_file} not found")
                return []
                
            with open(self.topics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            topics = data.get('top_tourism_stories', [])
            logger.info(f"Loaded {len(topics)} tourism topics")
            return topics
            
        except Exception as e:
            logger.error(f"Error loading topics: {e}")
            return []
    
    def create_caption_prompt(self, topic: Dict[str, Any]) -> str:
        """Create prompt for caption generation"""
        title = topic.get('title', '')
        summary = topic.get('summary', '')
        region = topic.get('region', 'Global')
        score = topic.get('score', 0)
        
        prompt = f"""
You are TripAvail's luxury travel curator - crafting premium experiences for discerning travelers.

Create a SHORT, PREMIUM caption for high-end social media (Instagram/TikTok/YouTube Shorts).

Article Details:
- Title: {title}
- Summary: {summary}
- Region: {region}
- Relevance Score: {score}/10

PREMIUM CAPTION REQUIREMENTS:
✨ Length: 150-200 characters MAX (short & punchy)
✨ Tone: Exclusive, aspirational, sophisticated yet accessible
✨ Style: One powerful hook sentence that sells the dream
✨ NO generic phrases like "discover", "explore", "journey"
✨ USE: Sensory details, exclusive insights, curiosity gaps
✨ End with ONE power emoji that captures the vibe
✨ NO "Plan your journey" - too salesy

PREMIUM HASHTAG STRATEGY:
✨ 8-12 hashtags only (quality over quantity)
✨ Mix: 40% destination-specific, 30% luxury travel, 30% trending
✨ Include: #tripavail (brand), 2-3 location tags, 4-5 aspirational tags
✨ NO generic tags like #Travel #Tourism
✨ USE: Niche, premium tags that attract quality audience
✨ CRITICAL: All hashtags must be LOWERCASE (e.g., #naturelover not #NatureLover, #costalcharm not #CostalCharm)

EXAMPLES OF PREMIUM CAPTIONS:
❌ Bad: "Discover the beautiful beaches of Bali! Plan your journey ✈️"
✅ Good: "Sunrise over rice terraces that Instagram forgot existed 🌅"

❌ Bad: "Explore amazing food in Tokyo! Adventure awaits!"
✅ Good: "Where Michelin stars meet hole-in-the-wall magic ⭐"

❌ Bad: "Visit ancient temples and experience culture!"
✅ Good: "Monks chant at dawn. You're the only foreigner here 🕊️"

Return JSON format:
{{
  "caption": "One powerful sentence with sensory details and exclusivity",
  "hashtags": ["#tripavail", "#locationtag", "#premiumtag", ...],
  "region": "{region}",
  "score": {score}
}}
"""
        return prompt
    
    def generate_caption_with_openai(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Generate caption using OpenAI"""
        try:
            prompt = self.create_caption_prompt(topic)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a luxury travel curator for TripAvail. Create SHORT, PREMIUM captions (150-200 chars) that sell exclusive experiences through sensory details and curiosity gaps. Avoid generic travel clichés. Make readers FEEL like they're missing out on something extraordinary."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                # Clean up markdown formatting if present
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                result = json.loads(content)
                
                # Validate caption length (premium captions are shorter)
                caption = result.get('caption', '')
                if len(caption) > 200:
                    logger.warning(f"Caption too long ({len(caption)} chars), truncating for premium feel")
                    result['caption'] = caption[:197] + "..."
                elif len(caption) < 50:
                    logger.warning(f"Caption too short ({len(caption)} chars), might lack impact")

                
                # Validate hashtag count (premium = less is more)
                hashtags = result.get('hashtags', [])
                
                # CRITICAL: Normalize all hashtags to lowercase (preserve #, lowercase the rest)
                # Example: #NatureLover -> #naturelover, #CostalCharm -> #costalcharm
                normalized_hashtags = []
                for tag in hashtags:
                    if tag.startswith('#'):
                        # Keep #, lowercase everything after
                        normalized = '#' + tag[1:].lower()
                    else:
                        # Add # if missing, then lowercase
                        normalized = '#' + tag.lower()
                    normalized_hashtags.append(normalized)
                
                if len(normalized_hashtags) < 6:
                    logger.warning(f"Too few hashtags ({len(normalized_hashtags)}), adding premium defaults")
                    # Add premium default hashtags (already lowercase)
                    default_tags = ["#tripavail", "#luxurytravel", "#hiddengems", "#travelinstyle"]
                    result['hashtags'] = normalized_hashtags + default_tags[:8-len(normalized_hashtags)]
                elif len(normalized_hashtags) > 15:
                    logger.warning(f"Too many hashtags ({len(normalized_hashtags)}), keeping top 12")
                    result['hashtags'] = normalized_hashtags[:12]
                else:
                    result['hashtags'] = normalized_hashtags
                
                logger.info(f"Generated caption for: {topic.get('title', 'Unknown')[:50]}...")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {e}")
                logger.error(f"Response content: {content}")
                
                # Fallback response (all hashtags lowercase)
                return {
                    "caption": f"Discover amazing travel opportunities in {topic.get('region', 'the world')}! Plan your journey with TripAvail ✈️",
                    "hashtags": ["#travelgoals", "#tripavail", "#globaltravel", "#adventure", "#explore", "#wanderlust", "#travel", "#journey"],
                    "region": topic.get('region', 'Global'),
                    "score": topic.get('score', 0)
                }
                
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return {
                "caption": f"Explore incredible destinations! Plan your journey with TripAvail ✈️",
                "hashtags": ["#travelgoals", "#tripavail", "#globaltravel", "#adventure"],
                "region": topic.get('region', 'Global'),
                "score": topic.get('score', 0)
            }
    
    def batch_process_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple topics and generate captions"""
        generated_posts = []
        
        logger.info(f"Processing {len(topics)} topics for caption generation")
        
        for i, topic in enumerate(topics, 1):
            logger.info(f"Processing topic {i}/{len(topics)}: {topic.get('title', 'Unknown')[:50]}...")
            
            post = self.generate_caption_with_openai(topic)
            
            # Add metadata
            post['original_title'] = topic.get('title', '')
            post['original_summary'] = topic.get('summary', '')
            post['generated_at'] = datetime.now().isoformat()
            post['topic_id'] = i
            
            generated_posts.append(post)
        
        logger.info(f"Successfully generated {len(generated_posts)} social media posts")
        return generated_posts
    
    def save_posts(self, posts: List[Dict[str, Any]]) -> None:
        """Save generated posts to JSON file"""
        try:
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat(),
                "source": "TripAvail AI Caption Generator",
                "input_source": "Global Tourism News Selector",
                "total_posts": len(posts),
                "posts": posts
            }
            
            with open(self.posts_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(posts)} posts to {self.posts_file}")
            
        except Exception as e:
            logger.error(f"Error saving posts: {e}")
    
    def log_caption_activity(self, posts: List[Dict[str, Any]]) -> None:
        """Log caption generation activity"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{timestamp} | Generated {len(posts)} social media posts\n")
                
                for post in posts:
                    caption_length = len(post.get('caption', ''))
                    hashtag_count = len(post.get('hashtags', []))
                    region = post.get('region', 'Unknown')
                    score = post.get('score', 0)
                    
                    f.write(f"  - {post.get('original_title', 'Unknown')[:50]}... | "
                           f"Region: {region} | Score: {score} | "
                           f"Caption: {caption_length} chars | Hashtags: {hashtag_count}\n")
            
            logger.info(f"Logged caption activity to {self.log_file}")
            
        except Exception as e:
            logger.error(f"Error logging caption activity: {e}")
    
    def run_caption_generation(self) -> None:
        """Main method to run caption generation process"""
        logger.info("Starting caption generation process")
        
        # Load topics
        topics = self.load_topics()
        if not topics:
            logger.warning("No topics found to process")
            return
        
        # Generate captions
        posts = self.batch_process_topics(topics)
        
        # Save posts
        self.save_posts(posts)
        
        # Log activity
        self.log_caption_activity(posts)
        
        logger.info("Caption generation process completed successfully")
    
    def get_latest_posts(self) -> List[Dict[str, Any]]:
        """Get the latest generated posts"""
        try:
            if not os.path.exists(self.posts_file):
                return []
                
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return data.get('posts', [])
            
        except Exception as e:
            logger.error(f"Error loading latest posts: {e}")
            return []


def main():
    """Main function to run caption generation"""
    generator = CaptionGenerator()
    generator.run_caption_generation()
    
    # Display results
    posts = generator.get_latest_posts()
    print(f"\n[SUCCESS] Generated {len(posts)} social media posts!")
    
    for i, post in enumerate(posts, 1):
        print(f"\n[POST] Post {i}:")
        caption = post.get('caption', '').encode('ascii', 'ignore').decode('ascii')
        print(f"Caption: {caption}")
        hashtags = [tag.encode('ascii', 'ignore').decode('ascii') for tag in post.get('hashtags', [])]
        print(f"Hashtags: {', '.join(hashtags)}")
        print(f"Region: {post.get('region', 'Unknown')}")
        print(f"Score: {post.get('score', 0)}/10")


if __name__ == "__main__":
    main()

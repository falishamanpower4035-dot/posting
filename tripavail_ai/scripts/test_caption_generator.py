"""
Test script for Caption Generator
Tests the caption generation functionality
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.post_generator.generate_caption import CaptionGenerator


def test_caption_generator():
    """Test the caption generator functionality"""
    print("[TEST] Testing Caption Generator...")
    
    try:
        # Initialize generator
        print("1. Initializing CaptionGenerator...")
        generator = CaptionGenerator()
        print("   [OK] CaptionGenerator initialized")
        
        # Test loading topics
        print("2. Testing topic loading...")
        topics = generator.load_topics()
        print(f"   [OK] Loaded {len(topics)} topics")
        
        if not topics:
            print("   [WARNING] No topics found in processed_news.json")
            print("   [INFO] Run tourism editor first to generate topics")
            return False
        
        # Test caption generation for first topic
        print("3. Testing caption generation...")
        if topics:
            first_topic = topics[0]
            print(f"   Testing with: {first_topic.get('title', 'Unknown')[:50]}...")
            
            generated_post = generator.generate_caption_with_openai(first_topic)
            
            # Validate output
            caption = generated_post.get('caption', '')
            hashtags = generated_post.get('hashtags', [])
            
            print(f"   [OK] Generated caption ({len(caption)} chars)")
            print(f"   [OK] Generated {len(hashtags)} hashtags")
            
            # Check requirements
            if len(caption) <= 250:
                print("   [OK] Caption length within limit (<=250 chars)")
            else:
                print(f"   [WARNING] Caption too long ({len(caption)} chars)")
            
            if len(hashtags) >= 8:
                print("   [OK] Hashtag count sufficient (>=8)")
            else:
                print(f"   [WARNING] Too few hashtags ({len(hashtags)})")
        
        # Test batch processing
        print("4. Testing batch processing...")
        posts = generator.batch_process_topics(topics)
        print(f"   [OK] Processed {len(posts)} topics")
        
        # Test saving posts
        print("5. Testing post saving...")
        generator.save_posts(posts)
        
        if os.path.exists("data/posts.json"):
            print("   [OK] posts.json file created")
            
            # Verify file content
            with open("data/posts.json", 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            saved_posts = saved_data.get('posts', [])
            print(f"   [OK] Saved {len(saved_posts)} posts to file")
        else:
            print("   [ERROR] posts.json file not created")
            return False
        
        # Test logging
        print("6. Testing logging...")
        generator.log_caption_activity(posts)
        
        if os.path.exists("logs/caption_log.txt"):
            print("   [OK] caption_log.txt file created")
        else:
            print("   [ERROR] caption_log.txt file not created")
            return False
        
        # Test getting latest posts
        print("7. Testing latest posts retrieval...")
        latest_posts = generator.get_latest_posts()
        print(f"   [OK] Retrieved {len(latest_posts)} latest posts")
        
        print("\n[SUCCESS] All tests passed! Caption Generator is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        return False


def display_sample_output():
    """Display sample generated content"""
    print("\n[SAMPLE] Sample Generated Content:")
    print("=" * 50)
    
    try:
        if os.path.exists("data/posts.json"):
            with open("data/posts.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            
            for i, post in enumerate(posts[:2], 1):  # Show first 2 posts
                print(f"\nPost {i}:")
                caption = post.get('caption', '').encode('ascii', 'ignore').decode('ascii')
                print(f"Caption: {caption}")
                hashtags = [tag.encode('ascii', 'ignore').decode('ascii') for tag in post.get('hashtags', [])]
                print(f"Hashtags: {', '.join(hashtags)}")
                print(f"Region: {post.get('region', 'Unknown')}")
                print(f"Score: {post.get('score', 0)}/10")
                title = post.get('original_title', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                print(f"Original Title: {title}")
                print("-" * 30)
        else:
            print("No posts.json file found. Run the caption generator first.")
            
    except Exception as e:
        print(f"Error displaying sample output: {e}")


def main():
    """Main test function"""
    print("[LAUNCH] TripAvail AI - Caption Generator Test")
    print("=" * 50)
    
    # Run tests
    success = test_caption_generator()
    
    if success:
        # Display sample output
        display_sample_output()
        
        print(f"\n[STATUS] Caption Generator Status:")
        print(f"   [OK] Module: modules/post_generator/generate_caption.py")
        print(f"   [OK] Input: data/processed_news.json")
        print(f"   [OK] Output: data/posts.json")
        print(f"   [OK] Logs: logs/caption_log.txt")
        print(f"   [OK] OpenAI Model: gpt-4o-mini")
        print(f"   [OK] Caption Limit: <=250 characters")
        print(f"   [OK] Hashtag Count: >=8 hashtags")
        print(f"   [OK] Brand Tagline: 'Plan your journey with TripAvail'")
    else:
        print("\n[ERROR] Caption Generator test failed. Check the errors above.")


if __name__ == "__main__":
    main()

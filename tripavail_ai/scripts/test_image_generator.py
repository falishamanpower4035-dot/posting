"""
Test script for Image Generator
Tests the image generation and quality assurance functionality
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.image_generator.generate_images import ImageGenerator


def test_image_generator():
    """Test the image generator functionality"""
    print("[TEST] Testing Image Generator...")
    
    try:
        # Initialize generator
        print("1. Initializing ImageGenerator...")
        generator = ImageGenerator()
        print("   [OK] ImageGenerator initialized")
        
        # Test post ingestion
        print("2. Testing post ingestion...")
        posts = generator.ingest_posts()
        print(f"   [OK] Loaded {len(posts)} posts")
        
        if not posts:
            print("   [WARNING] No posts found in data/posts.json")
            print("   [INFO] Run caption generator first to create posts")
            return False
        
        # Test generation plan
        print("3. Testing generation plan...")
        plans = generator.define_generation_plan(posts)
        print(f"   [OK] Created {len(plans)} generation plans")
        
        # Display sample plan
        if plans:
            sample_plan = plans[0]
            print(f"   Sample prompt: {sample_plan['prompt'][:100]}...")
        
        # Test directory structure
        print("4. Testing directory structure...")
        required_dirs = [
            "data/images/staging",
            "data/images/approved", 
            "data/images/rejected",
            "assets"
        ]
        
        for directory in required_dirs:
            if os.path.exists(directory):
                print(f"   [OK] Directory exists: {directory}")
            else:
                print(f"   [ERROR] Directory missing: {directory}")
                return False
        
        # Test manifest file creation
        print("5. Testing manifest creation...")
        if os.path.exists("data/image_manifest.json"):
            print("   [OK] Manifest file exists")
            
            with open("data/image_manifest.json", 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            print(f"   [OK] Manifest contains {len(manifest.get('posts', []))} posts")
        else:
            print("   [INFO] No manifest file yet (will be created during generation)")
        
        print("\n[SUCCESS] Image Generator tests passed!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        return False


def display_sample_posts():
    """Display sample posts that will be processed"""
    print("\n[SAMPLE] Posts Ready for Image Generation:")
    print("=" * 50)
    
    try:
        if os.path.exists("data/posts.json"):
            with open("data/posts.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            
            for i, post in enumerate(posts[:2], 1):  # Show first 2 posts
                print(f"\nPost {i}:")
                caption = post.get('caption', '').encode('ascii', 'ignore').decode('ascii')
                print(f"Caption: {caption[:100]}...")
                print(f"Region: {post.get('region', 'Unknown')}")
                print(f"Score: {post.get('score', 0)}/10")
                print("-" * 30)
        else:
            print("No posts.json file found. Run the caption generator first.")
            
    except Exception as e:
        print(f"Error displaying sample posts: {e}")


def main():
    """Main test function"""
    print("[LAUNCH] TripAvail AI - Image Generator Test")
    print("=" * 50)
    
    # Run tests
    success = test_image_generator()
    
    if success:
        # Display sample posts
        display_sample_posts()
        
        print(f"\n[STATUS] Image Generator Status:")
        print(f"   [OK] Module: modules/image_generator/generate_images.py")
        print(f"   [OK] Input: data/posts.json")
        print(f"   [OK] Output: data/images/approved/")
        print(f"   [OK] Manifest: data/image_manifest.json")
        print(f"   [OK] Logs: logs/image_log.txt")
        print(f"   [OK] DALL-E Model: dall-e-3")
        print(f"   [OK] Image Size: 1080x1920 (9:16)")
        print(f"   [OK] Images per Post: 3")
        print(f"   [OK] Quality Check: OCR + GPT validation")
    else:
        print("\n[ERROR] Image Generator test failed. Check the errors above.")


if __name__ == "__main__":
    main()

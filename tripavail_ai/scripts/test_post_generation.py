#!/usr/bin/env python3
"""
Test Post Generation - Verify All Systems Working
Tests: Shutterstock + OpenAI optimization, image generation, voiceover, video
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from loguru import logger
from production_pipeline import ProductionPipeline
from core.content.post_manager import PostManager

def create_test_post():
    """Create a test post to verify all systems"""
    
    print("\n" + "="*60)
    print("TEST POST GENERATION")
    print("="*60)
    print()
    
    # Create test topic
    test_topic = {
        'title': 'Dubai Luxury Hotel Opens New Rooftop Infinity Pool',
        'summary': 'A new 5-star luxury hotel in Dubai has opened featuring a stunning rooftop infinity pool with panoramic views of the city skyline. The hotel offers world-class amenities including spa facilities, fine dining restaurants, and exclusive beach access.',
        'region': 'Dubai',
        'score': 8,
        'published_date': '2025-11-05'
    }
    
    print("📝 Test Topic:")
    print(f"   Title: {test_topic['title']}")
    print(f"   Region: {test_topic['region']}")
    print(f"   Score: {test_topic['score']}")
    print()
    
    # Initialize pipeline
    print("🔧 Initializing Production Pipeline...")
    pipeline = ProductionPipeline()
    post_manager = PostManager()
    
    print("✅ Pipeline initialized")
    print()
    
    # Step 1: Generate caption and story analysis
    print("="*60)
    print("STEP 1: Caption & Story Analysis")
    print("="*60)
    
    post_id = "test_001"
    post_data = pipeline.generate_caption_for_topic(test_topic, post_id)
    
    if not post_data:
        print("❌ Failed to generate caption")
        return False
    
    print(f"✅ Caption generated")
    print(f"   Caption: {post_data.get('caption', '')[:60]}...")
    print(f"   Story beats: {len(post_data.get('story_beats', []))}")
    print(f"   Duration: {post_data.get('duration', 0)}s")
    print()
    
    # Step 2: Generate images (with Shutterstock + OpenAI optimization)
    print("="*60)
    print("STEP 2: Image Generation (Shutterstock + OpenAI)")
    print("="*60)
    
    success = pipeline.generate_images_for_post(post_data)
    if not success:
        print("❌ Failed to generate images")
        return False
    
    images = post_manager.get_image_paths(post_id)
    print(f"✅ Generated {len(images)} images")
    for i, img in enumerate(images[:3], 1):
        print(f"   {i}. {Path(img).name}")
    print()
    
    # Step 3: Generate voiceover (ElevenLabs)
    print("="*60)
    print("STEP 3: Voiceover Generation (ElevenLabs)")
    print("="*60)
    
    success = pipeline.generate_voiceover_for_post(post_id)
    if not success:
        print("❌ Failed to generate voiceover")
        return False
    
    voiceover_path = post_manager.get_voiceover_path(post_id)
    if voiceover_path.exists():
        print(f"✅ Voiceover generated: {voiceover_path.name}")
        print(f"   Size: {voiceover_path.stat().st_size / 1024:.1f} KB")
    else:
        print("⚠️ Voiceover file not found")
    print()
    
    # Step 4: Get background music
    print("="*60)
    print("STEP 4: Background Music (Archive)")
    print("="*60)
    
    success = pipeline.generate_music_for_post(post_id)
    music_path = post_manager.get_post_directory(post_id) / "audio" / "background_music.mp3"
    if music_path.exists():
        print(f"✅ Background music: {music_path.name}")
    else:
        print("⚠️ No background music (proceeding without)")
    print()
    
    # Step 5: Generate thumbnail
    print("="*60)
    print("STEP 5: Thumbnail Generation (Gemini)")
    print("="*60)
    
    success = pipeline.generate_thumbnails_for_post(post_id)
    if success:
        metadata = post_manager.get_metadata(post_id)
        thumbnails = metadata.get('thumbnails', {})
        if thumbnails:
            print(f"✅ Thumbnail generated")
            for platform, path in thumbnails.items():
                if platform != 'hook_text':
                    print(f"   {platform}: {Path(path).name}")
    else:
        print("⚠️ Thumbnail generation failed (continuing...)")
    print()
    
    # Step 6: Generate video
    print("="*60)
    print("STEP 6: Video Generation")
    print("="*60)
    
    if not images:
        print("❌ No images available for video")
        return False
    
    success = pipeline.generate_video_for_post(post_id)
    if not success:
        print("❌ Failed to generate video")
        return False
    
    draft_path = post_manager.get_draft_video_path(post_id)
    final_path = post_manager.get_final_video_path(post_id)
    
    if draft_path.exists():
        print(f"✅ Draft video: {draft_path.name}")
        print(f"   Size: {draft_path.stat().st_size / (1024*1024):.1f} MB")
    if final_path.exists():
        print(f"✅ Final video: {final_path.name}")
        print(f"   Size: {final_path.stat().st_size / (1024*1024):.1f} MB")
    print()
    
    # Summary
    print("="*60)
    print("✅ TEST POST GENERATION COMPLETE!")
    print("="*60)
    print()
    print("📊 Summary:")
    print(f"   Post ID: {post_id}")
    print(f"   Images: {len(images)}")
    print(f"   Voiceover: {'✅' if voiceover_path.exists() else '❌'}")
    print(f"   Music: {'✅' if music_path.exists() else '❌'}")
    print(f"   Thumbnail: {'✅' if thumbnails else '❌'}")
    print(f"   Draft Video: {'✅' if draft_path.exists() else '❌'}")
    print(f"   Final Video: {'✅' if final_path.exists() else '❌'}")
    print()
    print(f"📁 Post directory: {post_manager.get_post_directory(post_id)}")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = create_test_post()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


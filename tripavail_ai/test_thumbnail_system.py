#!/usr/bin/env python3
"""
Test the complete thumbnail generation and posting system
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.media.images.generator.thumbnail_generator import ThumbnailGenerator
from core.social.platforms.youtube_uploader import YouTubeUploader
import json

def test_thumbnail_generation():
    """Test thumbnail generation for a sample post"""
    print("Testing Thumbnail Generation System")
    print("=" * 60)
    
    # Create test metadata
    test_metadata = {
        'original_title': 'Amazing Travel Destination in Europe - Lisbon City Guide',
        'caption': 'Discover the beauty of European cities with our comprehensive travel guide',
        'region': 'Europe',
        'hashtags': ['#travel', '#europe', '#lisbon', '#tourism', '#cityguide']
    }
    
    # Initialize thumbnail generator
    generator = ThumbnailGenerator()
    print(f"Stability AI Status: {'SET' if generator.stability_api_key else 'NOT SET'}")
    
    if not generator.stability_api_key:
        print("Cannot test without Stability AI API key")
        return False
    
    # Generate thumbnails
    print("\nGenerating thumbnails...")
    thumbnails = generator.generate_thumbnail_for_post("test_thumb_001", test_metadata)
    
    if thumbnails:
        print("Thumbnails generated successfully!")
        for platform, path in thumbnails.items():
            print(f"  {platform}: {path}")
            if Path(path).exists():
                print(f"     File exists ({Path(path).stat().st_size} bytes)")
            else:
                print(f"     File not found")
        return True
    else:
        print("Failed to generate thumbnails")
        return False

def test_youtube_thumbnail_upload():
    """Test YouTube thumbnail upload (without actually uploading)"""
    print("\nTesting YouTube Thumbnail Upload")
    print("=" * 60)
    
    try:
        uploader = YouTubeUploader()
        print(f"YouTube API Status: {'Ready' if uploader.youtube else 'Not initialized'}")
        
        # Test thumbnail path
        test_thumbnail = Path("data/posts/post_test_thumb_001/video/youtube_thumbnail.jpg")
        if test_thumbnail.exists():
            print(f"Test thumbnail found: {test_thumbnail}")
            print(f"   Size: {test_thumbnail.stat().st_size} bytes")
            return True
        else:
            print(f"Test thumbnail not found: {test_thumbnail}")
            return False
            
    except Exception as e:
        print(f"YouTube test error: {e}")
        return False

def test_complete_pipeline():
    """Test the complete pipeline with thumbnail generation"""
    print("\nTesting Complete Pipeline with Thumbnails")
    print("=" * 60)
    
    try:
        from production_pipeline import ProductionPipeline
        
        # Create a test topic
        test_topic = {
            'topic_id': 'test_thumb_002',
            'title': 'Beautiful Travel Destination in Asia',
            'summary': 'Discover amazing places in Asia with our travel guide',
            'region': 'Asia',
            'score': 8.5
        }
        
        # Initialize pipeline
        pipeline = ProductionPipeline()
        print("Pipeline initialized")
        
        # Process the test topic
        print("Processing test topic...")
        success = pipeline.process_single_post(test_topic, 2)
        
        if success:
            print("Complete pipeline test successful!")
            
            # Check if thumbnails were generated
            metadata = pipeline.post_manager.get_metadata("002")
            if metadata and 'thumbnails' in metadata:
                print("Thumbnails found in metadata:")
                for platform, path in metadata['thumbnails'].items():
                    print(f"  {platform}: {path}")
            else:
                print("No thumbnails found in metadata")
            
            return True
        else:
            print("Pipeline test failed")
            return False
            
    except Exception as e:
        print(f"Pipeline test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("THUMBNAIL SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Thumbnail Generation", test_thumbnail_generation),
        ("YouTube Upload Test", test_youtube_thumbnail_upload),
        ("Complete Pipeline", test_complete_pipeline)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All tests passed! Thumbnail system is ready!")
    else:
        print("Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()

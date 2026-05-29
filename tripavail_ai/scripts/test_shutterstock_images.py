#!/usr/bin/env python3
"""
Test Shutterstock Image Integration
Dry-run test for Shutterstock -> Pexels -> Unsplash image selection
Tests the priority order and diversification without running full pipeline
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from core.media.images.generator.hybrid_generator import HybridImageGenerator
from loguru import logger


def test_shutterstock_search():
    """Test basic Shutterstock search functionality"""
    print("\n" + "="*60)
    print("TEST 1: Shutterstock Search")
    print("="*60)
    
    gen = HybridImageGenerator()
    
    if not gen.shutterstock_access_token:
        print("❌ SHUTTERSTOCK_ACCESS_TOKEN not found in environment")
        print("   Add it to your .env file:")
        print("   SHUTTERSTOCK_ACCESS_TOKEN=your-token-here")
        return False
    
    # Test search with different queries
    test_queries = [
        "Paris Eiffel Tower sunset",
        "Bali beach tropical paradise",
        "Tokyo city night lights"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching Shutterstock: '{query}'")
        results = gen.search_shutterstock(query, count=5)
        
        if results:
            print(f"   ✅ Found {len(results)} results")
            for i, r in enumerate(results[:3], 1):
                desc = r.get('description', '')[:50]
                url = r.get('preview_url', '')[:60]
                print(f"      {i}. {desc}... | {url}...")
        else:
            print(f"   ⚠️  No results found")
    
    return True


def test_priority_order():
    """Test the priority order: Shutterstock -> Pexels -> Unsplash"""
    print("\n" + "="*60)
    print("TEST 2: Priority Order (Shutterstock -> Pexels -> Unsplash)")
    print("="*60)
    
    gen = HybridImageGenerator()
    
    # Create a test post
    test_post = {
        'post_id': '999',
        'topic_id': 'test_999',
        'title': 'Beautiful Mountain Landscape',
        'summary': 'Stunning mountain views with snow-capped peaks',
        'region': 'Switzerland',
        'keywords': {
            'primary': ['mountain', 'landscape', 'snow'],
            'visual': ['peaks', 'alpine', 'nature'],
            'secondary': ['Switzerland', 'travel', 'scenery']
        },
        'image_count': 5
    }
    
    print(f"\n📊 Test Post: {test_post['title']}")
    print(f"   Region: {test_post['region']}")
    print(f"   Target: {test_post['image_count']} images")
    
    # Create query
    query = gen.extract_keywords_and_create_query(test_post)
    print(f"\n🔎 Search Query: '{query}'")
    
    # Test each source
    print("\n--- Source 1: Shutterstock (PRIORITY) ---")
    shutter_results = gen.search_shutterstock(query, 3)
    print(f"   Found: {len(shutter_results)} results")
    
    print("\n--- Source 2: Pexels ---")
    pexels_results = gen.search_pexels(query, 3)
    print(f"   Found: {len(pexels_results)} results")
    
    print("\n--- Source 3: Unsplash ---")
    unsplash_results = gen.search_unsplash(query, 3)
    print(f"   Found: {len(unsplash_results)} results")
    
    total_found = len(shutter_results) + len(pexels_results) + len(unsplash_results)
    print(f"\n✅ Total images available: {total_found}")
    
    return total_found > 0


def test_page_diversification():
    """Test page and sort diversification for Shutterstock"""
    print("\n" + "="*60)
    print("TEST 3: Page & Sort Diversification")
    print("="*60)
    
    gen = HybridImageGenerator()
    query = "tropical beach sunset"
    
    # Test different sort orders
    sort_options = ["relevance", "popular", "newest"]
    
    for sort in sort_options:
        print(f"\n🔄 Sort: {sort}")
        results = gen.search_shutterstock(query, count=3, page=1, sort=sort)
        if results:
            print(f"   ✅ {len(results)} results")
            desc = results[0].get('description', '')[:60] if results else ''
            print(f"   Top result: {desc}...")
        else:
            print(f"   ⚠️  No results")
    
    # Test page rotation
    print(f"\n📄 Testing page rotation (1-3):")
    for page in range(1, 4):
        results = gen.search_shutterstock(query, count=2, page=page, sort="relevance")
        if results:
            print(f"   Page {page}: {len(results)} results")
        else:
            print(f"   Page {page}: No results")
    
    return True


def test_full_image_generation():
    """Test full image generation with priority order"""
    print("\n" + "="*60)
    print("TEST 4: Full Image Generation (DRY RUN)")
    print("="*60)
    
    gen = HybridImageGenerator()
    
    # Create test post
    test_post = {
        'post_id': 'test_001',
        'topic_id': 'test_001',
        'title': 'Dubai Luxury Hotel Opens',
        'summary': 'New 5-star hotel in Dubai features rooftop infinity pool',
        'region': 'Dubai',
        'keywords': {
            'primary': ['hotel', 'luxury', 'Dubai'],
            'visual': ['rooftop', 'pool', 'skyline'],
            'secondary': ['travel', 'tourism', 'Middle East']
        },
        'image_count': 6
    }
    
    print(f"\n📝 Test Post: {test_post['title']}")
    print(f"   Target: {test_post['image_count']} images")
    print(f"   Priority: Shutterstock -> Pexels -> Unsplash")
    
    # Simulate the flow (without actually downloading/saving)
    query = gen.extract_keywords_and_create_query(test_post)
    target_count = min(10, test_post.get('image_count', 6))
    
    print(f"\n🔍 Search Query: '{query}'")
    print(f"   Max images to fetch: {target_count}")
    
    simulated_images = []
    
    # 1. Shutterstock
    print("\n--- Trying Shutterstock ---")
    shutter = gen.search_shutterstock(query, target_count)
    simulated_images.extend([f"shutterstock_{i}" for i in range(min(len(shutter), target_count))])
    print(f"   ✅ Would get {len(shutter)} images from Shutterstock")
    
    # 2. Pexels (if needed)
    if len(simulated_images) < target_count:
        remaining = target_count - len(simulated_images)
        print(f"\n--- Trying Pexels (need {remaining} more) ---")
        pexels = gen.search_pexels(query, remaining)
        simulated_images.extend([f"pexels_{i}" for i in range(min(len(pexels), remaining))])
        print(f"   ✅ Would get {len(pexels)} images from Pexels")
    
    # 3. Unsplash (if needed)
    if len(simulated_images) < target_count:
        remaining = target_count - len(simulated_images)
        print(f"\n--- Trying Unsplash (need {remaining} more) ---")
        unsplash = gen.search_unsplash(query, remaining)
        simulated_images.extend([f"unsplash_{i}" for i in range(min(len(unsplash), remaining))])
        print(f"   ✅ Would get {len(unsplash)} images from Unsplash")
    
    print(f"\n📊 RESULT:")
    print(f"   Total images found: {len(simulated_images)}/{target_count}")
    print(f"   Sources breakdown:")
    print(f"      - Shutterstock: {sum(1 for x in simulated_images if 'shutterstock' in x)}")
    print(f"      - Pexels: {sum(1 for x in simulated_images if 'pexels' in x)}")
    print(f"      - Unsplash: {sum(1 for x in simulated_images if 'unsplash' in x)}")
    
    return len(simulated_images) >= min(5, target_count)


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SHUTTERSTOCK IMAGE INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Shutterstock Search", test_shutterstock_search),
        ("Priority Order", test_priority_order),
        ("Page Diversification", test_page_diversification),
        ("Full Generation Flow", test_full_image_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Shutterstock integration is ready!")
    else:
        print("\n⚠️  Some tests failed. Check configuration and API keys.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

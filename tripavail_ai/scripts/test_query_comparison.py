#!/usr/bin/env python3
"""Compare optimized vs original queries"""

import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from core.media.images.generator.hybrid_generator import HybridImageGenerator

def main():
    print(f"\n{'='*60}")
    print(f"Comparing Query Optimization Results")
    print(f"{'='*60}\n")
    
    gen = HybridImageGenerator()
    
    test_post = {
        'post_id': 'test_001',
        'original_title': 'Dubai Luxury Hotel Opens New Rooftop Infinity Pool',
        'original_summary': 'A new 5-star luxury hotel in Dubai has opened featuring a stunning rooftop infinity pool with panoramic views of the city skyline.',
        'caption': 'Experience luxury at its finest in Dubai',
        'region': 'Dubai',
        'keywords': {
            'primary': ['hotel', 'luxury', 'Dubai'],
            'visual': ['rooftop', 'pool', 'skyline'],
            'secondary': ['travel', 'tourism']
        }
    }
    
    # Test 1: Original query (what we had before)
    print("📊 Test 1: Original Query (without OpenAI)")
    original_query = "dubai luxury hotel"
    print(f"   Query: '{original_query}'")
    results1 = gen.search_shutterstock(original_query, count=5)
    print(f"   Results: {len(results1)} images found\n")
    
    # Test 2: Optimized query (with OpenAI)
    print("📊 Test 2: OpenAI Optimized Query")
    optimized_query = gen.extract_keywords_and_create_query(test_post)
    print(f"   Query: '{optimized_query}'")
    results2 = gen.search_shutterstock(optimized_query, count=5)
    print(f"   Results: {len(results2)} images found\n")
    
    # Test 3: Alternative simpler optimized query
    print("📊 Test 3: Testing Simpler Query")
    simpler_query = "Dubai luxury hotel rooftop"
    print(f"   Query: '{simpler_query}'")
    results3 = gen.search_shutterstock(simpler_query, count=5)
    print(f"   Results: {len(results3)} images found\n")
    
    print(f"{'='*60}")
    print(f"Summary:")
    print(f"   Original: {len(results1)} results")
    print(f"   OpenAI Optimized: {len(results2)} results")
    print(f"   Simpler Alternative: {len(results3)} results")
    print(f"{'='*60}\n")
    
    # Show best results
    best_query = original_query if len(results1) > 0 else (simpler_query if len(results3) > 0 else optimized_query)
    best_results = results1 if len(results1) > 0 else (results3 if len(results3) > 0 else results2)
    
    if best_results:
        print(f"✅ Best performing query: '{best_query}'")
        print(f"   Top 3 results:")
        for i, r in enumerate(best_results[:3], 1):
            desc = r.get('description', 'N/A')[:70]
            print(f"   {i}. {desc}...")

if __name__ == "__main__":
    main()


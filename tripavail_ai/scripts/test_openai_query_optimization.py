#!/usr/bin/env python3
"""Test OpenAI query optimization for Shutterstock"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from core.media.images.generator.hybrid_generator import HybridImageGenerator

def main():
    print(f"\n{'='*60}")
    print(f"Testing OpenAI Query Optimization for Shutterstock")
    print(f"{'='*60}\n")
    
    gen = HybridImageGenerator()
    
    # Create a test post (like "Dubai luxury hotel opens")
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
    
    print("📝 Test Post:")
    print(f"   Title: {test_post['original_title']}")
    print(f"   Region: {test_post['region']}\n")
    
    # Generate query (will use OpenAI optimization)
    print("🔍 Generating optimized query with OpenAI...\n")
    optimized_query = gen.extract_keywords_and_create_query(test_post)
    
    print(f"✅ Optimized Query: '{optimized_query}'\n")
    
    # Now search Shutterstock with the optimized query
    print(f"🔎 Searching Shutterstock with optimized query...\n")
    results = gen.search_shutterstock(optimized_query, count=5)
    
    print(f"✅ Found {len(results)} results\n")
    
    if results:
        for i, r in enumerate(results[:5], 1):
            desc = r.get('description', 'N/A')[:80]
            print(f"{i}. {desc}...")
        print()
    else:
        print("⚠️  No results found")
    
    print(f"\n{'='*60}")
    print(f"Optimization complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()


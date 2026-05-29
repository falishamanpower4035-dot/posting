#!/usr/bin/env python3
"""Quick test script to search Shutterstock for a specific query"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from core.media.images.generator.hybrid_generator import HybridImageGenerator

def main():
    query = "dubai luxury hotel"
    print(f"\n{'='*60}")
    print(f"Searching Shutterstock for: '{query}'")
    print(f"{'='*60}\n")
    
    gen = HybridImageGenerator()
    
    if not gen.shutterstock_access_token:
        print("❌ SHUTTERSTOCK_ACCESS_TOKEN not found")
        return
    
    results = gen.search_shutterstock(query, count=10)
    
    print(f"✅ Found {len(results)} results\n")
    
    if results:
        for i, r in enumerate(results, 1):
            desc = r.get('description', 'N/A')[:100]
            url = r.get('preview_url', 'N/A')
            width = r.get('width', '?')
            height = r.get('height', '?')
            
            print(f"{i}. {desc}...")
            print(f"   URL: {url[:80]}...")
            print(f"   Size: {width}x{height}")
            print()
    else:
        print("⚠️  No results found")
    
    print(f"\n{'='*60}")
    print(f"Total: {len(results)} results")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()


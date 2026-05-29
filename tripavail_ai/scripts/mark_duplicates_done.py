#!/usr/bin/env python3
"""Mark duplicate posts as done to prevent reposting"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled, mark_done

def main():
    pm = PostManager()
    posts = pm.get_all_posts()
    
    print("=" * 60)
    print("MARKING DUPLICATE POSTS AS DONE")
    print("=" * 60)
    
    # Group by normalized title
    by_title = defaultdict(list)
    
    for post_id in posts:
        meta = pm.get_metadata(post_id)
        if not meta:
            continue
            
        title = meta.get('original_title', '').strip()
        if not title:
            continue
            
        normalized_title = ' '.join(title.lower().split())
        by_title[normalized_title].append(post_id)
    
    # Find duplicates and mark extras as done
    duplicates_marked = 0
    scheduled = list_scheduled("pending")
    scheduled_post_ids = {item.post_id for item in scheduled}
    
    for title, post_ids in by_title.items():
        if len(post_ids) <= 1:
            continue
        
        # Find which posts are already posted
        posted_posts = []
        unposted_posts = []
        
        for pid in post_ids:
            ig = pm.is_posted(pid, "instagram")
            fb = pm.is_posted(pid, "facebook")
            if ig or fb:
                posted_posts.append(pid)
            else:
                unposted_posts.append(pid)
        
        if posted_posts:
            print(f"\n📋 Title: {title[:70]}")
            print(f"   Already posted: {posted_posts}")
            print(f"   Not posted yet: {unposted_posts}")
            
            # Mark unposted duplicates as done
            for pid in unposted_posts:
                if pid in scheduled_post_ids:
                    print(f"   ✅ Marking Post {pid} as done (duplicate)")
                    mark_done(pid)
                    duplicates_marked += 1
    
    print(f"\n\n✅ Marked {duplicates_marked} duplicate posts as done")
    print("=" * 60)

if __name__ == "__main__":
    main()


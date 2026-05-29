#!/usr/bin/env python3
"""Find duplicate posts with same news article"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager

def main():
    pm = PostManager()
    posts = pm.get_all_posts()
    
    print("=" * 60)
    print("DUPLICATE POST ANALYSIS")
    print("=" * 60)
    
    # Group by title and URL
    by_title = defaultdict(list)
    by_url = defaultdict(list)
    
    for post_id in posts:
        meta = pm.get_metadata(post_id)
        if not meta:
            continue
            
        title = meta.get('original_title', '').strip()
        url = meta.get('original_url', '') or meta.get('link', '')
        
        if title:
            by_title[title.lower()].append(post_id)
        if url:
            by_url[url].append(post_id)
    
    # Find duplicates
    print("\n📋 Posts with same TITLE:")
    title_dupes = {k: v for k, v in by_title.items() if len(v) > 1}
    for title, post_ids in sorted(title_dupes.items())[:10]:
        print(f"\n  Title: {title[:70]}")
        for pid in post_ids:
            meta = pm.get_metadata(pid)
            ig = pm.is_posted(pid, "instagram")
            fb = pm.is_posted(pid, "facebook")
            yt = pm.is_posted(pid, "youtube")
            url = meta.get('original_url', '') if meta else 'N/A'
            print(f"    Post {pid}: IG={ig}, FB={fb}, YT={yt}, URL={url[:50]}")
    
    print("\n\n📋 Posts with same URL:")
    url_dupes = {k: v for k, v in by_url.items() if len(v) > 1}
    for url, post_ids in sorted(url_dupes.items())[:10]:
        print(f"\n  URL: {url[:70]}")
        for pid in post_ids:
            meta = pm.get_metadata(pid)
            title = meta.get('original_title', 'N/A')[:60] if meta else 'N/A'
            ig = pm.is_posted(pid, "instagram")
            fb = pm.is_posted(pid, "facebook")
            yt = pm.is_posted(pid, "youtube")
            print(f"    Post {pid}: {title}")
            print(f"      IG={ig}, FB={fb}, YT={yt}")
    
    # Check scheduled posts
    print("\n\n📅 Checking scheduled_posts.json:")
    from core.scheduling.scheduler import list_scheduled
    scheduled = list_scheduled("pending")
    print(f"  Total pending: {len(scheduled)}")
    
    # Group by post_id
    scheduled_by_post = defaultdict(list)
    for item in scheduled:
        scheduled_by_post[item.post_id].append(item)
    
    print(f"\n  Posts scheduled multiple times:")
    for post_id, items in scheduled_by_post.items():
        if len(items) > 1:
            print(f"    Post {post_id}: {len(items)} schedules")
            for item in items:
                print(f"      - {item.scheduled_at} (priority: {item.priority})")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()


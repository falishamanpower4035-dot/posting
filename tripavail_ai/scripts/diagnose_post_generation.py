#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

print("=== POST GENERATION DIAGNOSTIC ===\n")

# 1. Check scheduled posts
scheduled_file = Path("data/scheduled_posts.json")
if scheduled_file.exists():
    with open(scheduled_file) as f:
        scheduled = json.load(f)
    
    pending = [p for p in scheduled if p.get('status') == 'pending']
    done = [p for p in scheduled if p.get('status') == 'done']
    
    print(f"1. SCHEDULED POSTS:")
    print(f"   Total: {len(scheduled)}")
    print(f"   Pending: {len(pending)}")
    print(f"   Done: {len(done)}")
    
    if pending:
        print(f"\n   Pending posts:")
        now = datetime.now(timezone.utc)
        for p in pending[-10:]:
            scheduled_at = datetime.fromisoformat(p['scheduled_at'].replace('Z', '+00:00'))
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            status = "OVERDUE" if scheduled_at < now else "FUTURE"
            print(f"     Post {p['post_id']}: {scheduled_at} ({status})")
    
    recent = [p for p in scheduled if p['post_id'] in ['056','057','058','059','060','061']]
    print(f"\n   Recent posts (056-061):")
    for p in recent:
        print(f"     Post {p['post_id']}: status={p.get('status')}, scheduled={p.get('scheduled_at', 'N/A')}")
else:
    print("❌ scheduled_posts.json not found!")

# 2. Check generated posts
posts_dir = Path("data/posts")
if posts_dir.exists():
    post_dirs = sorted([d.name for d in posts_dir.iterdir() if d.is_dir() and d.name.startswith('post_')])
    print(f"\n2. GENERATED POSTS:")
    print(f"   Total posts: {len(post_dirs)}")
    if post_dirs:
        print(f"   Latest: {post_dirs[-5:]}")
        
        # Check if post_061 has video
        post_061_dir = posts_dir / "post_061"
        if post_061_dir.exists():
            video_dir = post_061_dir / "video"
            if video_dir.exists():
                videos = list(video_dir.glob("*.mp4"))
                print(f"\n   Post 061 video files: {len(videos)}")
                if videos:
                    for v in videos:
                        print(f"     {v.name}")
                else:
                    print(f"     ❌ NO VIDEO FILES (generation failed)")
else:
    print("\n❌ data/posts directory not found!")

# 3. Check processed news
news_file = Path("data/processed_news.json")
if news_file.exists():
    with open(news_file) as f:
        news_data = json.load(f)
    
    processed_at = news_data.get('processed_at')
    stories = news_data.get('top_tourism_stories', [])
    
    print(f"\n3. PROCESSED NEWS:")
    print(f"   Stories: {len(stories)}")
    if processed_at:
        try:
            proc_time = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
            if proc_time.tzinfo is None:
                proc_time = proc_time.replace(tzinfo=timezone.utc)
            age_hours = (datetime.now(timezone.utc) - proc_time).total_seconds() / 3600
            print(f"   Last processed: {proc_time} ({age_hours:.1f} hours ago)")
            if age_hours > 6:
                print(f"   ⚠️  WARNING: Stale data (>6 hours old)")
        except Exception as e:
            print(f"   Last processed: {processed_at} (parse error: {e})")
    
    if stories:
        scores = [s.get('score', 0) for s in stories]
        print(f"   Score range: {min(scores)} - {max(scores)}")
        high_score = [s for s in stories if (s.get('score', 0) or 0) >= 7]
        print(f"   Score >=7: {len(high_score)}")
        
        # Check which ones are already used
        from core.content.post_manager import PostManager
        pm = PostManager()
        unused = [s for s in high_score if not pm.is_news_already_used(s)]
        print(f"   Score >=7 UNUSED: {len(unused)}")
        
        if len(unused) == 0:
            print(f"   ❌ NO UNUSED ARTICLES AVAILABLE - This is why no posts are being generated!")
else:
    print("\n❌ processed_news.json not found!")

print("\n=== END DIAGNOSTIC ===")



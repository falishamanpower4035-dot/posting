#!/usr/bin/env python3
"""Check recent bot activity and posting status"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

def check_recent_activity():
    from core.content.post_manager import PostManager
    
    pm = PostManager()
    posts_dir = Path("data/posts")
    
    print("="*80)
    print("RECENT POSTING ACTIVITY ANALYSIS")
    print("="*80)
    
    now = datetime.now(timezone.utc)
    print(f"\nCurrent time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"8 hours ago: {(now - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    if not posts_dir.exists():
        print("❌ No posts directory found")
        return
    
    posts = sorted([d.name for d in posts_dir.iterdir() if d.is_dir() and d.name.startswith("post_")])
    
    print(f"Total posts found: {len(posts)}")
    
    # Check last 10 posts
    recent_posts = []
    for post_id in posts[-10:]:
        meta_file = posts_dir / post_id / "metadata.json"
        if not meta_file.exists():
            continue
            
        try:
            meta = json.loads(meta_file.read_text())
            
            # Get posting times
            ig_posted = meta.get("instagram_posted_at")
            fb_posted = meta.get("facebook_posted_at")
            yt_posted = meta.get("youtube_posted_at")
            
            # Get status
            ig = meta.get("posted_to_instagram", False)
            fb = meta.get("posted_to_facebook", False)
            yt = meta.get("posted_to_youtube", False)
            
            scheduled_time = meta.get("scheduled_time")
            created_at = meta.get("created_at")
            status = meta.get("status", "unknown")
            
            recent_posts.append({
                'id': post_id,
                'status': status,
                'ig': ig,
                'fb': fb,
                'yt': yt,
                'ig_time': ig_posted,
                'fb_time': fb_posted,
                'yt_time': yt_posted,
                'scheduled': scheduled_time,
                'created': created_at
            })
        except Exception as e:
            print(f"⚠️ Error reading {post_id}: {e}")
    
    print(f"\nAnalyzing last {len(recent_posts)} posts...\n")
    
    # Find last posting time
    last_post_times = []
    for p in recent_posts:
        times = []
        if p['ig_time']:
            try:
                times.append(datetime.fromisoformat(p['ig_time'].replace('Z', '+00:00')))
            except:
                pass
        if p['fb_time']:
            try:
                times.append(datetime.fromisoformat(p['fb_time'].replace('Z', '+00:00')))
            except:
                pass
        if p['yt_time']:
            try:
                times.append(datetime.fromisoformat(p['yt_time'].replace('Z', '+00:00')))
            except:
                pass
        if times:
            last_post_times.append((p['id'], max(times)))
    
    if last_post_times:
        last_post_times.sort(key=lambda x: x[1], reverse=True)
        last_post_id, last_post_time = last_post_times[0]
        hours_ago = (now - last_post_time).total_seconds() / 3600
        
        print(f"📅 LAST POST ACTIVITY:")
        print(f"   Post ID: {last_post_id}")
        print(f"   Posted at: {last_post_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   Hours ago: {hours_ago:.1f} hours")
        
        if hours_ago > 8:
            print(f"   ⚠️ WARNING: No posts in last 8 hours!")
    else:
        print("⚠️ No posting timestamps found in recent posts")
    
    # Check for unposted posts
    print(f"\n📊 POST STATUS BREAKDOWN:")
    print("-"*80)
    print(f"{'Post ID':<12} {'Status':<12} {'IG':<5} {'FB':<5} {'YT':<5} {'Scheduled':<20} {'Last Posted':<20}")
    print("-"*80)
    
    unposted = []
    for p in sorted(recent_posts, key=lambda x: x['id']):
        latest_time = None
        latest_str = "Never"
        
        times = []
        if p['ig_time']:
            try:
                times.append(datetime.fromisoformat(p['ig_time'].replace('Z', '+00:00')))
            except:
                pass
        if p['fb_time']:
            try:
                times.append(datetime.fromisoformat(p['fb_time'].replace('Z', '+00:00')))
            except:
                pass
        if p['yt_time']:
            try:
                times.append(datetime.fromisoformat(p['yt_time'].replace('Z', '+00:00')))
            except:
                pass
        
        if times:
            latest_time = max(times)
            latest_str = latest_time.strftime('%Y-%m-%d %H:%M:%S')
        
        all_done = p['ig'] and p['fb'] and p['yt']
        if not all_done:
            unposted.append(p)
        
        print(f"{p['id']:<12} {p['status']:<12} {str(p['ig']):<5} {str(p['fb']):<5} {str(p['yt']):<5} {str(p['scheduled']):<20} {latest_str:<20}")
    
    # Check for posts ready to post
    print(f"\n🚀 POSTS READY TO POST:")
    print("-"*80)
    
    ready_now = []
    for p in unposted:
        scheduled = p['scheduled']
        if scheduled:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
                if scheduled_dt <= now:
                    ready_now.append(p)
            except:
                pass
    
    if ready_now:
        print(f"⚠️ Found {len(ready_now)} posts that should have been posted already:\n")
        for p in ready_now:
            print(f"   {p['id']}: scheduled for {p['scheduled']}")
            print(f"      Status: {p['status']}, IG={p['ig']}, FB={p['fb']}, YT={p['yt']}")
    else:
        print("✅ No overdue posts found")
    
    # Check if there are any posts scheduled in the future
    future_posts = []
    for p in recent_posts:
        scheduled = p['scheduled']
        if scheduled:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
                if scheduled_dt > now:
                    future_posts.append((p['id'], scheduled_dt))
            except:
                pass
    
    if future_posts:
        future_posts.sort(key=lambda x: x[1])
        print(f"\n📅 UPCOMING POSTS:")
        print("-"*80)
        for post_id, scheduled_dt in future_posts[:5]:
            hours_until = (scheduled_dt - now).total_seconds() / 3600
            print(f"   {post_id}: {scheduled_dt.strftime('%Y-%m-%d %H:%M:%S UTC')} ({hours_until:.1f}h)")
    else:
        print(f"\n⚠️ No future posts scheduled")
    
    return {
        'last_post_time': last_post_time if last_post_times else None,
        'unposted': unposted,
        'ready_now': ready_now,
        'future_posts': future_posts
    }

if __name__ == "__main__":
    check_recent_activity()


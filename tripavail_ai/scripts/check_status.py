#!/usr/bin/env python3
"""Quick status check for TripAvail bot"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytz

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled

def main():
    print("=" * 60)
    print("TRIPAVAIL BOT STATUS CHECK")
    print("=" * 60)
    
    # Check scheduled posts
    print("\n📅 SCHEDULED POSTS:")
    scheduled = list_scheduled(status="pending")
    now_utc = datetime.now(timezone.utc)
    
    print(f"Total pending: {len(scheduled)}")
    
    # Filter posts scheduled for today or past
    today_posts = []
    future_posts = []
    
    for item in scheduled:
        when = datetime.fromisoformat(item.scheduled_at)
        if when.tzinfo is None:
            when = pytz.utc.localize(when)
        
        if when <= now_utc:
            today_posts.append((item.post_id, item.scheduled_at, item.priority))
        elif when.date() == now_utc.date():
            today_posts.append((item.post_id, item.scheduled_at, item.priority))
        else:
            future_posts.append((item.post_id, item.scheduled_at, item.priority))
    
    print(f"\n📌 Ready to post NOW (overdue): {len([p for p in today_posts if datetime.fromisoformat(p[1]).replace(tzinfo=timezone.utc) <= now_utc])}")
    print(f"📌 Scheduled for TODAY: {len(today_posts)}")
    print(f"📌 Scheduled for FUTURE: {len(future_posts)}")
    
    if today_posts:
        print("\nToday's scheduled posts:")
        for post_id, scheduled_at, priority in sorted(today_posts, key=lambda x: x[1])[:10]:
            when = datetime.fromisoformat(scheduled_at)
            if when.tzinfo is None:
                when = pytz.utc.localize(when)
            time_str = when.strftime("%H:%M UTC")
            print(f"  • Post {post_id}: {time_str} (priority: {priority})")
    
    # Check post status
    print("\n📊 POST STATUS:")
    pm = PostManager()
    all_posts = pm.get_all_posts()
    print(f"Total posts generated: {len(all_posts)}")
    
    # Count posting status
    fully_posted = 0
    partially_posted = 0
    unposted = 0
    
    posting_status = []
    
    for post_id in all_posts:
        ig = pm.is_posted(post_id, "instagram")
        fb = pm.is_posted(post_id, "facebook")
        yt = pm.is_posted(post_id, "youtube")
        
        if ig and fb and yt:
            fully_posted += 1
        elif ig or fb or yt:
            partially_posted += 1
            posting_status.append((post_id, ig, fb, yt))
        else:
            unposted += 1
            posting_status.append((post_id, ig, fb, yt))
    
    print(f"✅ Fully posted (all platforms): {fully_posted}")
    print(f"⚠️  Partially posted: {partially_posted}")
    print(f"❌ Not posted: {unposted}")
    
    if posting_status:
        print("\nPosts needing attention:")
        for post_id, ig, fb, yt in posting_status[:10]:
            status = []
            if ig: status.append("IG")
            if fb: status.append("FB")
            if yt: status.append("YT")
            missing = []
            if not ig: missing.append("IG")
            if not fb: missing.append("FB")
            if not yt: missing.append("YT")
            print(f"  • Post {post_id}: {'✅' if status else '❌'} {', '.join(status) if status else 'None'} | Missing: {', '.join(missing) if missing else 'None'}")
    
    # Check latest posts
    print("\n📝 LATEST POSTS:")
    latest = sorted(all_posts)[-5:] if all_posts else []
    for post_id in latest:
        meta = pm.get_metadata(post_id)
        title = meta.get('original_title', 'N/A')[:60] if meta else 'No metadata'
        print(f"  • Post {post_id}: {title}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()


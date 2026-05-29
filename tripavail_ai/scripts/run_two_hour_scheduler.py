#!/usr/bin/env python3
from __future__ import annotations

import time
from dotenv import load_dotenv
load_dotenv()

# Initialize centralized logging FIRST
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.utils import logging_setup  # noqa

from datetime import datetime
from typing import List, Dict

import pytz

from core.news.fetcher.fetch_news import NewsFetcher
from core.news.editor import TourismEditor
from production_pipeline import ProductionPipeline
from core.content.post_manager import PostManager
from core.scheduling.scheduler import schedule_after_minutes, schedule_peak, schedule_smart_peak


PK_TZ = pytz.timezone("Asia/Karachi")


def fetch_and_analyze() -> List[Dict]:
    # Fetch latest news
    NewsFetcher().run_fetch_cycle()
    # Analyze and score
    editor = TourismEditor()
    analyzed = editor.run_analysis()
    
    # Check if analysis failed (returns None on OpenAI quota error)
    if analyzed is None:
        print("⚠️ WARNING: News analysis failed (likely OpenAI quota exceeded)")
        print("   The system will use existing processed news if available")
        print("   Check OpenAI billing and quota limits!")
    
    # Load processed news
    import json, pathlib
    data_file = pathlib.Path("data/processed_news.json")
    if not data_file.exists():
        print("❌ No processed_news.json found - cannot generate posts")
        return []
    
    data = json.loads(data_file.read_text(encoding="utf-8"))
    stories = data.get("top_tourism_stories", [])
    
    # Warn if using stale data
    from datetime import datetime, timezone
    processed_at = data.get("processed_at")
    if processed_at:
        try:
            proc_time = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
            age_hours = (datetime.now(timezone.utc) - proc_time.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            if age_hours > 6:
                print(f"⚠️ WARNING: Using stale processed news (age: {age_hours:.1f} hours)")
                print(f"   Last processed: {processed_at}")
                print(f"   Analysis may have failed - check OpenAI quota!")
        except:
            pass
    
    return stories


def generate_and_schedule(topics: List[Dict]) -> None:
    if not topics:
        return
    pipeline = ProductionPipeline()
    pm = PostManager()

    # Determine top score
    top_score = max([t.get("score", 0) for t in topics] or [0])

    # Only consider score >=7 for normal scheduling
    selected = [t for t in topics if (t.get("score", 0) or 0) >= 7]
    
    # CRITICAL: Filter out topics that have already been used to create posts
    # This prevents generating duplicate posts from the same news article
    # This is a SECONDARY check - primary filtering happens in TourismEditor
    unused_topics = []
    for topic in selected:
        if not pm.is_news_already_used(topic):
            unused_topics.append(topic)
        else:
            # Log which topic was skipped (should be rare if filtering at source works)
            title = topic.get('title', 'Unknown')[:60]
            url = topic.get('link', topic.get('url', 'N/A'))
            print(f"⚠️ Skipping already-used topic (secondary check): {title} ({url})")
    
    if not unused_topics:
        print("✅ No new topics to generate (all score >= 7 topics already used)")
        return
    
    print(f"📝 Generating posts for {len(unused_topics)} new topics (filtered from {len(selected)} total)")

    # Generate posts and schedule
    # CRITICAL: Use max ID instead of count to handle gaps from failed posts
    all_posts = pm.get_all_posts()
    if all_posts:
        # Get the maximum post ID number (handle gaps correctly)
        # Skip non-numeric post IDs (like test_001, etc.)
        numeric_ids = []
        for pid in all_posts:
            try:
                numeric_ids.append(int(pid))
            except ValueError:
                # Skip non-numeric post IDs (test posts, etc.)
                print(f"⚠️ Skipping non-numeric post ID: {pid}")
        max_id = max(numeric_ids) if numeric_ids else 0
        start_index = max_id + 1
    else:
        start_index = 1
    post_idx = start_index

    for topic in unused_topics:
        ok = pipeline.process_single_post(topic, post_idx)
        if not ok:
            # On failure, still increment to avoid overwriting
            # But directory might be created, so this is intentional
            post_idx += 1
            continue
        post_id = f"{post_idx:03d}"

        score = topic.get("score", 0) or 0
        # High priority: max score or score >= 10 -> peak schedule
        if score >= 10 or score == top_score:
            # Learning-based peak scheduling for rank-10/top posts
            schedule_smart_peak(post_id)
        else:
            # Normal: 20 minutes after ready
            schedule_after_minutes(post_id, minutes=20)

        post_idx += 1


def main() -> None:
    print("Four-hour scheduler started.")
    try:
        topics = fetch_and_analyze()
        generate_and_schedule(topics)
    except Exception as e:
        print("Scheduler error:", e)


if __name__ == "__main__":
    main()

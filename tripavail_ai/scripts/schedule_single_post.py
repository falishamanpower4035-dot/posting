#!/usr/bin/env python3
"""
Generate one post (15s) and schedule posting to Instagram, Facebook, and YouTube
at a specified local time in a given timezone (default: Asia/Karachi).

Usage examples:
  python scripts/schedule_single_post.py --time 01:25 --tz Asia/Karachi
  python scripts/schedule_single_post.py --time 13:10 --tz Asia/Karachi --title "Skardu opens new scenic route" --summary "15-second teaser"
"""
from __future__ import annotations

import argparse
from dotenv import load_dotenv
load_dotenv()
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict

import pytz

from core.content.post_manager import PostManager
from production_pipeline import ProductionPipeline
from core.social.platforms.facebook_poster import FacebookPoster
from core.social.platforms.youtube_uploader import YouTubeUploader
from core.social.platforms.instagram_poster import InstagramPoster


def next_run_at(local_time_str: str, tz_name: str) -> datetime:
    tz = pytz.timezone(tz_name)
    now_tz = datetime.now(tz)
    hour, minute = map(int, local_time_str.split(":"))
    run = now_tz.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if run <= now_tz:
        run = run + timedelta(days=1)
    return run


def generate_one_post_15s(title: str, summary: str, region: str = "Pakistan") -> str:
    # Ensure target duration override is respected by the pipeline
    os.environ["TARGET_DURATION_SEC"] = "15"

    pipeline = ProductionPipeline()
    pm = PostManager()

    # Determine next post id index
    existing = pm.get_all_posts()
    next_index = len(existing) + 1

    topic: Dict[str, object] = {
        "title": title or "New scenic route opens in Pakistan",
        "summary": summary or "A short 15-second teaser highlighting a new travel update.",
        "region": region,
        "score": 9,
    }

    ok = pipeline.process_single_post(topic, next_index)
    if not ok:
        raise RuntimeError("Post generation failed")

    return f"{next_index:03d}"


def post_everywhere(post_id: str) -> None:
    pm = PostManager()

    # Metadata and video
    meta = pm.get_metadata(post_id)
    if not meta:
        raise RuntimeError(f"No metadata for post {post_id}")
    video = pm.get_final_video_path(post_id)
    if not video.exists():
        raise RuntimeError(f"No final video for post {post_id}")

    title = meta.get("original_title", "")[:70]
    caption = meta.get("caption", meta.get("context_caption", ""))
    hashtags = meta.get("hashtags", [])

    # Instagram
    if not pm.is_posted(post_id, "instagram"):
        ig = InstagramPoster()
        ig_caption = caption
        if hashtags:
            ig_caption = f"{ig_caption}\n\n{' '.join(hashtags[:30])}"
        if ig.post_reel(video, ig_caption):
            pm.mark_as_posted(post_id, "instagram")

    # Facebook
    if not pm.is_posted(post_id, "facebook"):
        fb = FacebookPoster()
        fb_caption = caption
        if hashtags:
            fb_caption = f"{fb_caption}\n\n{' '.join(hashtags[:30])}"
        if fb.post_video(video, fb_caption, hashtags):
            pm.mark_as_posted(post_id, "facebook")

    # YouTube (Shorts)
    if not pm.is_posted(post_id, "youtube"):
        yt = YouTubeUploader()
        yt.authenticate()
        tags = [t.replace('#','') for t in hashtags[:10]] + ['TripAvail','Travel','Shorts']
        # Use truncate_title to ensure max 60 characters (will be truncated in upload_video too)
        yt_title = yt.truncate_title(title, " | TripAvail")
        yt_description = f"{caption}\n\n#Shorts\n\n" + " ".join(hashtags[:10])
        vid = yt.upload_video(video, title=yt_title, description=yt_description, tags=tags)
        if vid:
            pm.mark_as_posted(post_id, "youtube", f"https://youtube.com/shorts/{vid}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--time", required=True, help="HH:MM in local timezone (e.g., 01:25)")
    parser.add_argument("--tz", default="Asia/Karachi", help="Timezone name (default Asia/Karachi)")
    parser.add_argument("--title", default="")
    parser.add_argument("--summary", default="")
    args = parser.parse_args()

    post_id = generate_one_post_15s(args.title, args.summary)
    run_dt = next_run_at(args.time, args.tz)

    # Sleep until scheduled time
    now_utc = datetime.now(timezone.utc)
    run_utc = run_dt.astimezone(pytz.utc)
    wait_s = (run_utc - now_utc).total_seconds()
    if wait_s < 0:
        wait_s = 0
    print(f"Post {post_id} scheduled for {run_dt.isoformat()} ({args.tz}), waiting {int(wait_s)}s...")
    time.sleep(wait_s)

    print(f"Posting post_{post_id} to all platforms...")
    post_everywhere(post_id)
    print("DONE")


if __name__ == "__main__":
    main()

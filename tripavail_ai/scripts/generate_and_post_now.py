#!/usr/bin/env python3
"""
Generate a single post now and immediately post it to Instagram, Facebook, and YouTube.

Usage:
  python scripts/generate_and_post_now.py --duration 15 --title "Pakistan tourism update" --summary "Systems check"
"""
from __future__ import annotations

import argparse
from dotenv import load_dotenv
load_dotenv()
import os
from typing import Dict

from core.content.post_manager import PostManager
from production_pipeline import ProductionPipeline
from core.social.platforms.facebook_poster import FacebookPoster
from core.social.platforms.youtube_uploader import YouTubeUploader
from core.social.platforms.instagram_poster import InstagramPoster


def generate_one(duration_sec: int, title: str, summary: str, region: str = "Pakistan") -> str:
    os.environ["TARGET_DURATION_SEC"] = str(duration_sec)

    pipeline = ProductionPipeline()
    pm = PostManager()

    next_index = len(pm.get_all_posts()) + 1
    topic: Dict[str, object] = {
        "title": title or "Pakistan tourism update",
        "summary": summary or "15s systems check post",
        "region": region,
        "score": 9,
    }

    ok = pipeline.process_single_post(topic, next_index)
    if not ok:
        raise RuntimeError("Post generation failed")
    return f"{next_index:03d}"


def post_everywhere(post_id: str) -> None:
    pm = PostManager()
    meta = pm.get_metadata(post_id)
    video = pm.get_final_video_path(post_id)

    title = (meta or {}).get("original_title", "")[:70]
    caption = (meta or {}).get("caption", (meta or {}).get("context_caption", ""))
    hashtags = (meta or {}).get("hashtags", [])

    # Instagram
    ig = InstagramPoster()
    ig_caption = caption
    if hashtags:
        ig_caption = f"{ig_caption}\n\n{' '.join(hashtags[:30])}"
    ig.post_reel(video, ig_caption)

    # Facebook
    fb = FacebookPoster()
    fb_caption = caption
    if hashtags:
        fb_caption = f"{fb_caption}\n\n{' '.join(hashtags[:30])}"
    fb.post_video(video, fb_caption, hashtags)

    # YouTube
    yt = YouTubeUploader()
    yt.authenticate()
    tags = [t.replace('#','') for t in hashtags[:10]] + ['TripAvail','Travel','Shorts']
    # Use truncate_title to ensure max 60 characters (will be truncated in upload_video too)
    yt_title = yt.truncate_title(title, " | TripAvail")
    yt_description = f"{caption}\n\n#Shorts\n\n" + " ".join(hashtags[:10])
    yt.upload_video(video, title=yt_title, description=yt_description, tags=tags)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--title", default="Pakistan tourism update")
    parser.add_argument("--summary", default="15s systems check post")
    args = parser.parse_args()

    post_id = generate_one(args.duration, args.title, args.summary)
    print(f"Generated post {post_id}. Posting now...")
    post_everywhere(post_id)
    print("DONE")


if __name__ == "__main__":
    main()

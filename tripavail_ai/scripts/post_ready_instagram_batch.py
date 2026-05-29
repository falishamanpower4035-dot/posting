#!/usr/bin/env python3
"""
Post all unposted ready posts from data/posts to Instagram.
- Scans data/posts/post_*/video/final*.mp4
- Builds caption from metadata (caption + up to 30 hashtags)
- Uses InstagramPoster to post as Reel
- Marks as posted on success

Usage:
  python scripts/post_ready_instagram_batch.py [--limit N] [--only POST_ID,POST_ID]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from core.content.post_manager import PostManager
from core.social.platforms.instagram_poster import InstagramPoster


def pick_video_path(pm: PostManager, post_id: str) -> Optional[Path]:
    video_dir = pm.get_video_dir(post_id)
    # Preference order
    candidates = [
        video_dir / "final_with_overlays.mp4",
        video_dir / "final.mp4",
        video_dir / "final_9x16.mp4",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def build_caption(meta: dict) -> str:
    base = (meta.get("caption") or meta.get("context_caption") or "").strip()
    hashtags = meta.get("hashtags") or []
    if hashtags:
        base = f"{base}\n\n" + " ".join(hashtags[:30])
    # Instagram captions limit is large (~2,200 chars); we keep it modest
    return base[:2000]


def main() -> None:
    parser = argparse.ArgumentParser(description="Post ready posts to Instagram")
    parser.add_argument("--limit", type=int, default=10, help="Max number of posts to publish")
    parser.add_argument("--only", type=str, default="", help="Comma-separated list of post IDs to publish (e.g., 001,002)")
    args = parser.parse_args()

    pm = PostManager()
    poster = InstagramPoster()

    if args.only:
        targets: List[str] = [pid.strip() for pid in args.only.split(",") if pid.strip()]
    else:
        targets = pm.get_unposted_posts(platform="instagram")

    published = 0

    for post_id in targets:
        if published >= args.limit:
            break

        meta = pm.get_metadata(post_id) or {}
        video_path = pick_video_path(pm, post_id)
        if not video_path:
            print(f"SKIP post_{post_id}: no video found")
            continue

        caption = build_caption(meta)
        print(f"Posting post_{post_id} → Instagram: {video_path}")
        ok = poster.post_reel(video_path, caption)
        if ok:
            pm.mark_as_posted(post_id, "instagram")
            print(f"OK post_{post_id}")
            published += 1
        else:
            print(f"FAIL post_{post_id}")

    print(f"Done. Published: {published}")


if __name__ == "__main__":
    main()

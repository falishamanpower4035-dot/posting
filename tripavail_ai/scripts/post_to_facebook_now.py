#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.social.platforms.facebook_poster import FacebookPoster
from core.content.post_manager import PostManager

if __name__ == "__main__":
    pm = PostManager()
    post_id = "001"
    meta = pm.get_metadata(post_id)
    video_dir = pm.get_video_dir(post_id)
    overlaid = video_dir / "final_with_overlays.mp4"
    final = video_dir / "final.mp4"

    video_path = overlaid if overlaid.exists() else final
    if not video_path.exists():
        print(f"No video found to post at {video_dir}")
        sys.exit(1)

    caption = meta.get("caption", meta.get("context_caption", ""))
    hashtags = meta.get("hashtags", [])

    fb = FacebookPoster()
    ok = fb.post_video(video_path, caption, hashtags)
    print("Posted:" if ok else "Failed:", video_path)

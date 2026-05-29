#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.content.post_manager import PostManager
from core.social.platforms.instagram_poster import InstagramPoster
from core.social.platforms.facebook_poster import FacebookPoster

def main():
    if len(sys.argv) < 2:
        print("Usage: post_now_one.py <post_id>")
        sys.exit(1)
    post_id = sys.argv[1]
    pm = PostManager()
    meta = pm.get_metadata(post_id) or {}
    video = pm.get_final_video_path(post_id)
    if not video.exists():
        print(f"No final video: {video}")
        sys.exit(2)
    caption = meta.get("caption", meta.get("context_caption", ""))
    hashtags = meta.get("hashtags", [])

    # Instagram
    if not pm.is_posted(post_id, "instagram"):
        try:
            ig = InstagramPoster()
            ig_caption = caption
            if hashtags:
                ig_caption = f"{ig_caption}\n\n" + " ".join(hashtags[:30])
            ok = ig.post_reel(video, ig_caption)
            print("Instagram:", ok)
            if ok:
                pm.mark_as_posted(post_id, "instagram")
        except Exception as e:
            print("Instagram error:", e)

    # Facebook
    if not pm.is_posted(post_id, "facebook"):
        try:
            fb = FacebookPoster()
            fb_caption = caption
            if hashtags:
                fb_caption = f"{fb_caption}\n\n" + " ".join(hashtags)
            ok = fb.post_video(video, fb_caption, hashtags)
            print("Facebook:", ok)
            if ok:
                pm.mark_as_posted(post_id, "facebook")
        except Exception as e:
            print("Facebook error:", e)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Post a Reel to Instagram now using the first ready post in data/posts/* that has video/final.mp4.
"""
from pathlib import Path
from core.content.post_manager import PostManager
from core.social.platforms.instagram_poster import InstagramPoster


def pick_ready_post(pm: PostManager) -> tuple[str, Path, dict] | tuple[None, None, None]:
    posts = pm.get_all_posts()
    for post_id in posts:
        final = pm.get_final_video_path(post_id)
        if final.exists():
            meta = pm.get_metadata(post_id) or {}
            return post_id, final, meta
    return None, None, None


def build_caption(meta: dict) -> str:
    caption = (meta.get("caption") or "").strip()
    hashtags = meta.get("hashtags") or []
    if hashtags:
        caption = f"{caption}\n\n" + " ".join(hashtags[:30])
    return caption


def main() -> None:
    pm = PostManager()
    post_id, video_path, meta = pick_ready_post(pm)
    if not post_id:
        print("NO_READY_POST")
        return

    caption = build_caption(meta)

    poster = InstagramPoster()
    print(f"Posting post_{post_id} → Instagram: {video_path}")
    ok = poster.post_reel(video_path, caption)
    print("RESULT:", ok)


if __name__ == "__main__":
    main()

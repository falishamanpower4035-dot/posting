#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from core.social.platforms.instagram_poster import InstagramPoster
from core.content.post_manager import PostManager
from core.social.platforms.google_drive_uploader import GoogleDriveUploader


if __name__ == "__main__":
    # Usage: python post_to_instagram_now.py <post_id|gdrive_file_id> [--drive]
    import sys
    use_drive = '--drive' in sys.argv
    arg = sys.argv[1] if len(sys.argv) > 1 else "001"

    if use_drive:
        # arg is Google Drive file ID
        gdrive_file_id = arg
        temp_path = Path("temp_instagram_video.mp4")
        drive = GoogleDriveUploader()
        if not drive.download_file(gdrive_file_id, temp_path):
            print(f"Failed to download video from Google Drive: {gdrive_file_id}")
            sys.exit(1)
        video_path = temp_path
        caption = "Posted from Google Drive"
    else:
        # arg is post_id
        pm = PostManager()
        post_id = arg
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
        if hashtags:
            caption = f"{caption}\n\n{' '.join(hashtags[:30])}"

    poster = InstagramPoster()
    ok = poster.post_reel(video_path, caption)
    print("Posted to Instagram" if ok else "Failed to post to Instagram")



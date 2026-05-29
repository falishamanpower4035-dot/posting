#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.content.post_manager import PostManager
from core.social.platforms.google_drive_uploader import GoogleDriveUploader
from datetime import datetime, timezone

if __name__ == "__main__":
    pm = PostManager()
    post_id = "001"
    video_dir = pm.get_video_dir(post_id)
    overlaid = video_dir / "final_with_overlays.mp4"
    final = video_dir / "final.mp4"
    video_path = overlaid if overlaid.exists() else final

    if not video_path.exists():
        print(f"No video found at {video_dir}")
        sys.exit(1)

    uploader = GoogleDriveUploader()
    # Build dated folder name like 2025-10-29_post_001
    meta = pm.get_metadata(post_id)
    created_at = meta.get("created_at")
    try:
        date_str = datetime.fromisoformat(created_at).strftime("%Y-%m-%d") if created_at else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder_base = uploader._ensure_folder()
    if folder_base:
        sub_name = f"{date_str}_post_{post_id}"
        sub_folder = uploader._ensure_child_folder(folder_base, sub_name)
    else:
        sub_folder = None
    file_id = uploader.upload_video(video_path, folder_id=sub_folder)
    print("Drive file id:", file_id, "in folder:", sub_name if folder_base else "(root)")



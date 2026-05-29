#!/usr/bin/env python3
"""
Upload a final.mp4 to Google Drive (user token preferred), make it public, then post as an Instagram Reel.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from core.content.post_manager import PostManager
from core.social.platforms.instagram_poster import InstagramPoster

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
]
SERVICE_ACCOUNT_FILE = Path("nanobnana-1fa87a66cc0f.json")
USER_TOKEN_FILE = Path("drive_token.json")


def find_ready_post(pm: PostManager) -> tuple[Optional[str], Optional[Path], dict]:
    for post_id in pm.get_all_posts():
        final = pm.get_final_video_path(post_id)
        if final.exists():
            meta = pm.get_metadata(post_id) or {}
            return post_id, final, meta
    return None, None, {}


def build_caption(meta: dict) -> str:
    caption = (meta.get("caption") or "").strip()
    hashtags = meta.get("hashtags") or []
    if hashtags:
        caption = f"{caption}\n\n" + " ".join(hashtags[:30])
    return caption


def get_drive_service():
    # Prefer user OAuth token if present (has storage quota)
    if USER_TOKEN_FILE.exists():
        # Do NOT pass scopes here; use token's existing scopes to avoid invalid_scope
        creds = UserCredentials.from_authorized_user_file(str(USER_TOKEN_FILE))
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    # Fallback to service account (may lack storage quota)
    if SERVICE_ACCOUNT_FILE.exists():
        creds = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE), scopes=DRIVE_SCOPES
        )
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    raise FileNotFoundError("No Drive credentials found (drive_token.json or service account json)")


def upload_to_drive_public(service, file_path: Path) -> str:
    file_metadata = {
        "name": file_path.name,
    }
    media = MediaFileUpload(str(file_path), resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")

    # Make file public
    service.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"},
    ).execute()

    # Direct download link
    public_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    return public_url


def main() -> None:
    pm = PostManager()
    post_id, video_path, meta = find_ready_post(pm)
    if not post_id:
        print("NO_READY_POST")
        return

    print(f"Using post_{post_id}: {video_path}")

    # Upload to Google Drive
    service = get_drive_service()
    public_link = upload_to_drive_public(service, video_path)
    print(f"Public link: {public_link}")

    # Build caption and post to Instagram
    caption = build_caption(meta)
    ig = InstagramPoster()
    creation_id = ig.create_media_container(public_link, caption)
    print("creation_id:", creation_id)
    if not creation_id:
        print("FAILED_AT_CREATE_CONTAINER")
        return

    # Wait for processing to finish before publishing
    ready = ig.wait_until_processed(creation_id)
    print("processed:", ready)
    if not ready:
        print("FAILED_WAITING_FOR_PROCESSING")
        return

    post_id_resp = ig.publish_media(creation_id)
    print("publish_id:", post_id_resp)
    print("OK" if post_id_resp else "FAILED_AT_PUBLISH")


if __name__ == "__main__":
    main()

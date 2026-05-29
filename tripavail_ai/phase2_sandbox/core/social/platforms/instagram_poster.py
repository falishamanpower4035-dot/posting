#!/usr/bin/env python3
"""
Instagram Graph API Integration for TripAvail AI
- Posts Reels using the media -> media_publish flow
- Requires: INSTAGRAM_USER_ID and a long-lived access token with scopes:
  instagram_basic, instagram_content_publish, pages_show_list
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from loguru import logger
import dropbox

# Ensure project root on path for config import
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import settings


class InstagramPoster:
    def __init__(self):
        self.access_token = settings.FACEBOOK_GRAPH_TOKEN
        self.api_version = getattr(settings, "FACEBOOK_API_VERSION", "v18.0")
        # Prefer explicit INSTAGRAM_USER_ID if present; else env var
        self.ig_user_id = getattr(settings, "INSTAGRAM_USER_ID", "") or os.getenv("INSTAGRAM_USER_ID", "")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        if not self.access_token:
            raise ValueError("Instagram access token missing (FACEBOOK_GRAPH_TOKEN)")
        if not self.ig_user_id:
            raise ValueError("INSTAGRAM_USER_ID not configured in config/settings.py or env")

        logger.info("Instagram Poster initialized")

    def _upload_temp(self, file_path: Path) -> Optional[str]:
        """Upload file to a temporary host to get a public HTTPS URL.
        Tries multiple providers for reliability. Falls back to Google Drive if needed."""
        # Provider 0: Dropbox (recommended - temporary direct link)
        try:
            dbx_token = getattr(settings, "DROPBOX_ACCESS_TOKEN", "") or os.getenv("DROPBOX_ACCESS_TOKEN", "")
            dbx_refresh = getattr(settings, "DROPBOX_REFRESH_TOKEN", "") or os.getenv("DROPBOX_REFRESH_TOKEN", "")
            dbx_app_key = getattr(settings, "DROPBOX_APP_KEY", "") or os.getenv("DROPBOX_APP_KEY", "")
            dbx_app_secret = getattr(settings, "DROPBOX_APP_SECRET", "") or os.getenv("DROPBOX_APP_SECRET", "")

            dbx = None
            if dbx_refresh and dbx_app_key and dbx_app_secret:
                dbx = dropbox.Dropbox(oauth2_refresh_token=dbx_refresh, app_key=dbx_app_key, app_secret=dbx_app_secret)
            elif dbx_token:
                dbx = dropbox.Dropbox(dbx_token)

            if dbx:
                target = f"/tripavail_instagram/{file_path.name}"
                with open(file_path, "rb") as f:
                    dbx.files_upload(f.read(), target, mode=dropbox.files.WriteMode.overwrite)
                link = dbx.files_get_temporary_link(target).link
                if link and link.startswith("http"):
                    logger.info(f"Temporary video URL (Dropbox): {link}")
                    return link
        except Exception as e:
            logger.warning(f"Dropbox upload failed: {e}")
        # Provider 1: 0x0.st
        try:
            with open(file_path, "rb") as f:
                resp = requests.post("https://0x0.st", files={"file": (file_path.name, f)}, timeout=300)
            resp.raise_for_status()
            link = resp.text.strip()
            if link.startswith("http"):
                logger.info(f"Temporary video URL (0x0.st): {link}")
                return link
        except Exception as e:
            logger.warning(f"0x0.st upload failed: {e}")

        # Provider 2: file.io
        try:
            with open(file_path, "rb") as f:
                resp = requests.post("https://file.io", files={"file": (file_path.name, f)}, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            link = data.get("link")
            if link:
                logger.info(f"Temporary video URL (file.io): {link}")
                return link
        except Exception as e:
            logger.warning(f"file.io upload failed: {e}")

        # Provider 3: transfer.sh
        try:
            with open(file_path, "rb") as f:
                resp = requests.put(f"https://transfer.sh/{file_path.name}", data=f, timeout=300)
            resp.raise_for_status()
            link = resp.text.strip()
            if link.startswith("http"):
                logger.info(f"Temporary video URL (transfer.sh): {link}")
                return link
        except Exception as e:
            logger.warning(f"transfer.sh upload failed: {e}")

        # Provider 4: Google Drive (fallback)
        try:
            from core.social.platforms.google_drive_uploader import GoogleDriveUploader
            drive = GoogleDriveUploader()
            file_id = drive.upload_video(file_path)
            if not file_id:
                logger.error("Google Drive upload failed")
                return None
            # Build a shareable link
            service = drive.service
            # Set file to anyone with the link can view
            service.permissions().create(
                fileId=file_id,
                body={"role": "reader", "type": "anyone"},
            ).execute()
            file = service.files().get(fileId=file_id, fields="webContentLink,webViewLink").execute()
            link = file.get("webContentLink") or file.get("webViewLink")
            if link:
                logger.info(f"Temporary video URL (Google Drive): {link}")
                return link
        except Exception as e:
            logger.error(f"Google Drive upload failed: {e}")

        logger.error("All temporary upload providers failed")
        return None

    def create_media_container(self, video_url: str, caption: str) -> Optional[str]:
        try:
            endpoint = f"{self.base_url}/{self.ig_user_id}/media"
            data = {
                "access_token": self.access_token,
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                # Optional: share_to_feed true/false
            }
            r = requests.post(endpoint, data=data, timeout=60)
            r.raise_for_status()
            creation_id = r.json().get("id")
            logger.info(f"Created IG media container: {creation_id}")
            return creation_id
        except Exception as e:
            logger.error(f"Failed to create IG media container: {e} | {getattr(e, 'response', None) and e.response.text}")
            return None

    def publish_media(self, creation_id: str) -> Optional[str]:
        try:
            endpoint = f"{self.base_url}/{self.ig_user_id}/media_publish"
            data = {"access_token": self.access_token, "creation_id": creation_id}
            r = requests.post(endpoint, data=data, timeout=60)
            r.raise_for_status()
            id_ = r.json().get("id")
            logger.info(f"Published IG media: {id_}")
            return id_
        except Exception as e:
            logger.error(f"Failed to publish IG media: {e} | {getattr(e, 'response', None) and e.response.text}")
            return None

    def wait_until_processed(self, creation_id: str, timeout_sec: int = 180, interval_sec: int = 5) -> bool:
        """Poll media container status until FINISHED or ERROR/timeout."""
        import time as _t
        status_endpoint = f"{self.base_url}/{creation_id}"
        params = {"access_token": self.access_token, "fields": "status_code"}
        deadline = _t.time() + timeout_sec
        last = None
        while _t.time() < deadline:
            try:
                resp = requests.get(status_endpoint, params=params, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                status = data.get("status_code")
                if status != last:
                    logger.info(f"IG media status: {status}")
                    last = status
                if status == "FINISHED":
                    return True
                if status in ("ERROR", "ERRORS"):
                    return False
            except Exception as e:
                logger.warning(f"Status poll failed: {e}")
            _t.sleep(interval_sec)
        logger.error("Timed out waiting for IG media processing")
        return False

    def post_reel(self, video_path: Path, caption: str) -> bool:
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return False
        url = self._upload_temp(video_path)
        if not url:
            return False
        creation_id = self.create_media_container(url, caption)
        if not creation_id:
            return False
        # Wait for processing to finish
        if not self.wait_until_processed(creation_id):
            logger.error("IG media not ready to publish")
            return False
        post_id = self.publish_media(creation_id)
        return post_id is not None


def main():
    print("\nIG quick test not intended for direct run.")


if __name__ == "__main__":
    main()



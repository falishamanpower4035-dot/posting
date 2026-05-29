#!/usr/bin/env python3
"""
Google Drive Uploader for TripAvail AI

Supports:
- Service Account (recommended for headless/droplet). Share the destination folder
  with the service account email, then set env GDRIVE_SERVICE_ACCOUNT_FILE or
  GDRIVE_SERVICE_ACCOUNT_JSON.
- OAuth Installed App (fallback): requires client_secret.json in project root.
  A token file drive_token.json will be created after first auth.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from loguru import logger

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials as SA_Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# project config
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import settings


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDriveUploader:

    def download_file(self, file_id: str, dest_path: Path) -> bool:
        """Download a file from Google Drive by file_id to dest_path."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            with open(dest_path, "wb") as f:
                from googleapiclient.http import MediaIoBaseDownload
                import io
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            logger.info(f"Downloaded file {file_id} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file {file_id} from Drive: {e}")
            return False
    def __init__(self):
        self.service = self._init_service()

    def _init_service(self):
        # Try service account first
        if settings.GDRIVE_SERVICE_ACCOUNT_FILE or settings.GDRIVE_SERVICE_ACCOUNT_JSON:
            try:
                if settings.GDRIVE_SERVICE_ACCOUNT_JSON:
                    info = json.loads(settings.GDRIVE_SERVICE_ACCOUNT_JSON)
                    creds = SA_Credentials.from_service_account_info(info, scopes=SCOPES)
                else:
                    creds = SA_Credentials.from_service_account_file(
                        settings.GDRIVE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
                    )
                logger.info("Google Drive: using Service Account credentials")
                return build("drive", "v3", credentials=creds)
            except Exception as e:
                logger.warning(f"Service Account init failed: {e}")

        # Fallback to OAuth Installed App
        token_path = Path("drive_token.json")
        creds: Optional[UserCredentials] = None
        if token_path.exists():
            creds = UserCredentials.from_authorized_user_file(str(token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                # Try new file name first, fallback to standard name
                secret_file = "client_secret_1055967706845-fsq2hnofrsrjvd78rgi0dg82p4hjh7es.apps.googleusercontent.com.json"
                if not Path(secret_file).exists():
                    secret_file = "client_secret.json"
                flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
                creds = flow.run_local_server(port=0)
                token_path.write_text(creds.to_json())
        logger.info("Google Drive: using OAuth Installed App credentials")
        return build("drive", "v3", credentials=creds)

    def _ensure_folder(self, name: str = "TripAvail Videos") -> Optional[str]:
        if settings.GDRIVE_FOLDER_ID:
            return settings.GDRIVE_FOLDER_ID
        # Search for folder by name
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
            resp = self.service.files().list(q=query, fields="files(id,name)").execute()
            items = resp.get("files", [])
            if items:
                return items[0]["id"]
            # create folder
            meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
            folder = self.service.files().create(body=meta, fields="id").execute()
            return folder.get("id")
        except Exception as e:
            logger.error(f"Drive: folder ensure failed: {e}")
            return None

    def _ensure_child_folder(self, parent_id: str, name: str) -> Optional[str]:
        """Ensure a child folder exists with given name under parent_id."""
        try:
            query = (
                f"mimeType='application/vnd.google-apps.folder' and name='{name}' "
                f"and '{parent_id}' in parents and trashed=false"
            )
            resp = self.service.files().list(q=query, fields="files(id,name)").execute()
            items = resp.get("files", [])
            if items:
                return items[0]["id"]
            meta = {"name": name, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
            folder = self.service.files().create(body=meta, fields="id").execute()
            return folder.get("id")
        except Exception as e:
            logger.error(f"Drive: child folder ensure failed: {e}")
            return None

    def upload_video(self, file_path: Path, folder_id: Optional[str] = None) -> Optional[str]:
        if not file_path.exists():
            logger.error(f"Drive: file not found: {file_path}")
            return None
        try:
            folder_id = folder_id or self._ensure_folder()
            if not folder_id:
                return None
            metadata = {"name": file_path.name, "parents": [folder_id]}
            media = MediaFileUpload(str(file_path), mimetype="video/mp4", resumable=True)
            file = self.service.files().create(body=metadata, media_body=media, fields="id,webViewLink,webContentLink").execute()
            file_id = file.get("id")
            logger.info(f"Drive upload complete: id={file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Drive upload failed: {e}")
            return None


def main():
    pm_root = Path("data/posts/post_001/video")
    candidate = pm_root / "final_with_overlays.mp4"
    if not candidate.exists():
        candidate = pm_root / "final.mp4"
    uploader = GoogleDriveUploader()
    uploader.upload_video(candidate)


if __name__ == "__main__":
    main()



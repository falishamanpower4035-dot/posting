#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Optional

# Google API imports
try:
	from google.oauth2.credentials import Credentials
	from googleapiclient.discovery import build
	from googleapiclient.errors import HttpError
	exists_google = True
except Exception:
	exists_google = False


class GmailNotifier:
	"""Send emails using Gmail API (users.messages.send)."""
	def __init__(self, client_secret_file: Path, token_file: Path):
		if not exists_google:
			raise RuntimeError("Google API libraries missing: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
		self.client_secret_file = Path(client_secret_file)
		self.token_file = Path(token_file)
		self.service = None
		self._init_service()

	def _init_service(self):
		"""Initialize Gmail API service with stored token (refreshable)."""
		if not self.token_file.exists():
			raise RuntimeError(f"Gmail token not found: {self.token_file}. Run authorize_gmail_api.py to create it.")
		creds = Credentials.from_authorized_user_file(str(self.token_file), scopes=[
			"https://www.googleapis.com/auth/gmail.send"
		])
		self.service = build("gmail", "v1", credentials=creds)

	@staticmethod
	def _build_message(sender: str, to: str, subject: str, body: str) -> dict:
		import base64
		from email.mime.text import MIMEText
		message = MIMEText(body)
		message["to"] = to
		message["from"] = sender
		message["subject"] = subject
		raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
		return {"raw": raw}

	def send_email(self, sender: str, to: str, subject: str, body: str) -> Optional[str]:
		try:
			msg = self._build_message(sender, to, subject, body)
			resp = self.service.users().messages().send(userId="me", body=msg).execute()
			return resp.get("id")
		except HttpError as e:
			raise RuntimeError(f"Gmail API error: {e}")

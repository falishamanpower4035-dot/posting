#!/usr/bin/env python3
"""
Authorize Gmail API and save gmail_token.json
- Use on your local machine (opens a browser) OR run with --console for code flow.
- Requires client_secret.json in the current directory (or set GMAIL_CLIENT_SECRET_FILE).
"""
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main(console: bool = False):
	root = Path('.').resolve()
	client_secret = Path(sys.argv[2]) if len(sys.argv) > 2 else root / (sys.argv[1] if len(sys.argv) > 1 else 'client_secret.json')
	token_path = root / 'gmail_token.json'
	if not client_secret.exists():
		print(f"❌ client_secret file not found: {client_secret}")
		print("Place your OAuth client file as client_secret.json or pass a path.")
		return 1
	flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
	if console:
		creds = flow.run_console()
	else:
		creds = flow.run_local_server(port=8081, prompt='consent', authorization_prompt_message='Opening browser for Gmail authorization...')
	token_path.write_text(creds.to_json(), encoding='utf-8')
	print(f"✅ Saved token to {token_path}")
	return 0


if __name__ == '__main__':
	# Usage:
	#   python scripts/authorize_gmail_api.py                  # local server browser flow
	#   python scripts/authorize_gmail_api.py --console        # console code flow
	console = ('--console' in sys.argv)
	sys.exit(main(console))

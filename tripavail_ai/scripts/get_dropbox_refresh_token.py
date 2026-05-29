#!/usr/bin/env python3
"""
Generate a Dropbox OAuth2 refresh token with offline access.
Steps:
1) It will print an authorization URL.
2) Open it, log in, approve scopes, copy the code.
3) Paste the code back; it will print the refresh token.

Usage:
  python scripts/get_dropbox_refresh_token.py --app-key <APP_KEY> --app-secret <APP_SECRET>
"""
import argparse
from dropbox import DropboxOAuth2FlowNoRedirect


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-key", required=True)
    parser.add_argument("--app-secret", required=True)
    args = parser.parse_args()

    auth_flow = DropboxOAuth2FlowNoRedirect(
        consumer_key=args.app_key,
        consumer_secret=args.app_secret,
        token_access_type="offline",
        scope=[
            "files.content.write",
            "files.content.read",
            "sharing.read",
        ],
    )

    authorize_url = auth_flow.start()
    print("\nAuthorize this app:")
    print(authorize_url)
    print("\nAfter approval, paste the code here and press Enter.")
    code = input("Authorization code: ").strip()

    oauth_result = auth_flow.finish(code)
    print("\nSUCCESS. Store these securely:")
    print("REFRESH_TOKEN=", oauth_result.refresh_token)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
from instagrapi import Client


def main() -> None:
    username = os.getenv("IG_USERNAME", "").strip()
    password = os.getenv("IG_PASSWORD", "").strip()
    code = os.getenv("IG_2FA_CODE", "").strip()
    if not username or not password:
        print("MISSING_CREDENTIALS")
        sys.exit(2)

    cl = Client()
    cl.delay_range = [1, 3]

    try:
        # Try direct login; recent versions accept verification_code arg
        if code:
            cl.login(username, password, verification_code=code)
        else:
            cl.login(username, password)
    except Exception as e:
        # Try fallback two_factor_login when code supplied
        if code:
            try:
                cl.two_factor_login(code)
            except Exception as e2:
                print(f"ERROR_TWO_FACTOR {e2}")
                sys.exit(1)
        else:
            print(f"ERROR_LOGIN {e}")
            sys.exit(1)

    try:
        info = cl.user_info_by_username(username)
        print(f"OK {info.username} {info.pk}")
        cl.dump_settings("ig_session.json")
        print("SESSION_SAVED ig_session.json")
    except Exception as e:
        print(f"ERROR_POST_LOGIN {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

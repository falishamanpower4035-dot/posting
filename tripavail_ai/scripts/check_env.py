#!/usr/bin/env python3
import os
from dotenv import load_dotenv

REQUIRED = [
    "OPENAI_API_KEY",
    "NEWSDATA_API_KEY",
]
OPTIONAL = [
    "DROPBOX_APP_KEY",
    "DROPBOX_APP_SECRET",
    "DROPBOX_REFRESH_TOKEN",
    "PEXELS_API_KEY",
    "UNSPLASH_ACCESS_KEY",
]

def mask(v: str) -> str:
    if not v:
        return ""
    if len(v) <= 6:
        return "*" * len(v)
    return v[:3] + "*" * (len(v) - 6) + v[-3:]


def main() -> None:
    load_dotenv()
    print("[REQUIRED]")
    ok = True
    for k in REQUIRED:
        v = os.getenv(k, "")
        present = bool(v)
        print(f"{k:20} present={present} value={mask(v)}")
        if not present:
            ok = False
    print("\n[OPTIONAL]")
    for k in OPTIONAL:
        v = os.getenv(k, "")
        print(f"{k:20} present={bool(v)} value={mask(v)}")
    print("\nStatus:", "OK" if ok else "MISSING_REQUIRED_KEYS")

if __name__ == "__main__":
    main()

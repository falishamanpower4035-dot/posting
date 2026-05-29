#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import argparse

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "data" / "posts"
ARCHIVE_DIR = ROOT / "data" / "music_archive"


def dir_age_hours(path: Path) -> float:
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime)
    return (datetime.now() - mtime).total_seconds() / 3600.0


def find_background_music(post_dir: Path) -> Optional[Path]:
    audio_dir = post_dir / "audio"
    candidates = [
        audio_dir / "background_music.mp3",
        audio_dir / "background_music.wav",
        audio_dir / "music.mp3",
        audio_dir / "music.wav",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def cleanup_posts(older_than_hours: float = 24.0) -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    removed = 0
    archived = 0

    for child in POSTS_DIR.iterdir():
        if not child.is_dir():
            continue
        # Only operate on directories like post_XXX
        if not child.name.startswith("post_"):
            continue
        try:
            age_h = dir_age_hours(child)
            if age_h < older_than_hours:
                continue

            # Archive ElevenLabs background music if present
            music = find_background_music(child)
            if music and music.exists():
                target = ARCHIVE_DIR / f"{child.name}_{music.name}"
                try:
                    shutil.copy2(music, target)
                    archived += 1
                except Exception:
                    pass

            # Remove the post directory
            shutil.rmtree(child)
            removed += 1
            print(f"Deleted {child} (age {age_h:.1f}h)")
        except Exception as e:
            print(f"Skip {child}: {e}")

    print(f"Cleanup complete. Removed={removed}, Archived music files={archived}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup posts older than N hours")
    env_default = os.getenv("AUTO_DELETION_HOURS")
    default_hours = float(env_default) if env_default else 24.0
    parser.add_argument("--hours", type=float, default=default_hours, help="Delete posts older than this many hours (default from env AUTO_DELETION_HOURS or 24)")
    args = parser.parse_args()
    cleanup_posts(older_than_hours=args.hours)

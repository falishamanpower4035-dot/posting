#!/usr/bin/env python3
"""
Idempotent orchestrator: generate new content, validate outputs, and auto-post
Safeguards:
- Global file lock (prevents concurrent runs)
- State machine per post (skips completed stages)
- Guards to ensure Shorts vertical, single audio, duration
"""

import json
import subprocess
import sys
from pathlib import Path
from loguru import logger

from modules.orchestrator.lock import FileLock
from modules.orchestrator import state
from modules.orchestrator.guard import validate_final


DATA = Path("data")
VIDEOS = DATA / "videos"


def run(cmd):
    res = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error(res.stderr[:4000])
    else:
        logger.info(res.stdout[:4000])
    return res.returncode == 0


def main():
    lock = FileLock(Path(".run_lock"), timeout_sec=600)
    if not lock.acquire():
        print("Another run is in progress. Skipping.")
        return
    try:
        # Ensure posts
        posts_file = DATA / "posts.json"
        if not posts_file.exists():
            run(["regenerate_premium_captions.py"])  # creates posts.json

        posts = json.loads(posts_file.read_text(encoding="utf-8")).get("posts", [])

        # Ensure images and voiceovers and videos per post
        for post in posts:
            pid = str(post.get("topic_id"))

            if state.get_stage(pid) in ("posted", "uploaded"):
                continue

            # Voiceover + video + mix: idempotent via file existence
            state.set_stage(pid, "generating")
            run(["modules/image_generator/hybrid_generator.py"])  # safe re-run
            run(["regenerate_premium_voiceovers.py"])  # per-post safe; regenerates

            final = VIDEOS / f"reel_{pid}_final.mp4"
            ok, reason = validate_final(final)
            if not ok:
                logger.error(f"Validation failed for post {pid}: {reason}")
                state.set_stage(pid, f"invalid:{reason}")
                continue

            state.set_stage(pid, "ready")

        # Upload to YouTube (idempotent: uploader skips if file missing; we track published id)
        for post in posts:
            pid = str(post.get("topic_id"))
            if state.get_published_id(pid, "youtube"):
                continue
            if state.get_stage(pid) != "ready":
                continue
            if run(["upload_to_youtube.py"]):
                # Best-effort: marking uploaded to prevent immediate re-upload in next cycle
                state.set_stage(pid, "uploaded")

        # Facebook posting can be added similarly if required
        # run(["post_to_facebook.py"])  # optional

    finally:
        lock.release()


if __name__ == "__main__":
    main()



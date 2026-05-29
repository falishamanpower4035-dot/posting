#!/usr/bin/env python3
from __future__ import annotations

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from production_pipeline import ProductionPipeline
from core.content.post_manager import PostManager
from core.scheduling import scheduler


def main() -> None:
    # Force 15s target duration
    os.environ["TARGET_DURATION_SEC"] = "15"

    pipeline = ProductionPipeline()
    pm = PostManager()

    existing = pm.get_all_posts()
    next_index = len(existing) + 1

    topic = {
        "title": "TripAvail test post",
        "summary": "15-second scheduled test",
        "region": "Pakistan",
        "score": 9,
    }

    ok = pipeline.process_single_post(topic, next_index)
    if not ok:
        raise SystemExit("generation failed")

    post_id = f"{next_index:03d}"
    scheduler.schedule_after_minutes(post_id, minutes=10, priority="normal")
    print(f"Generated post_{post_id}. Scheduled for ~10 minutes from now (UTC basis). Daemon will post to all platforms.")


if __name__ == "__main__":
    main()

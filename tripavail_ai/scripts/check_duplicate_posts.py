#!/usr/bin/env python3
"""Check for duplicate posts in scheduled_posts.json"""
import json
from pathlib import Path
from collections import Counter

schedule_file = Path("data/scheduled_posts.json")
if not schedule_file.exists():
    print("No scheduled_posts.json found")
    exit(1)

data = json.load(open(schedule_file))
pending = [x for x in data if x.get("status") == "pending"]
print(f"Total pending: {len(pending)}")

ids = [x["post_id"] for x in pending]
dupes = {k: v for k, v in Counter(ids).items() if v > 1}
if dupes:
    print(f"⚠️ Duplicate post_ids found: {dupes}")
    for post_id, count in dupes.items():
        print(f"  Post {post_id}: {count} scheduled entries")
else:
    print("✅ No duplicate post_ids")


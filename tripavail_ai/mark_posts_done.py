#!/usr/bin/env python3
"""Mark stuck posts as done by directly editing scheduled_posts.json"""
import json
from pathlib import Path

SCHEDULE_FILE = Path("data/scheduled_posts.json")
STUCK_POSTS = ['288', '289', '301', '303']

print(f"Reading {SCHEDULE_FILE}...")
if not SCHEDULE_FILE.exists():
    print("❌ Schedule file not found!")
    exit(1)

with open(SCHEDULE_FILE, 'r') as f:
    items = json.load(f)

print(f"Found {len(items)} scheduled items")

# Mark stuck posts as done
marked_count = 0
for item in items:
    if item.get('post_id') in STUCK_POSTS and item.get('status') == 'pending':
        print(f"  Marking post {item['post_id']} as done (was pending)")
        item['status'] = 'done'
        marked_count += 1

if marked_count > 0:
    # Save back
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(items, f, indent=2)
    print(f"\n✅ Marked {marked_count} posts as done")
else:
    print("\n⚠️ No stuck posts found in pending status")

# Show remaining pending posts
print("\nRemaining pending posts:")
pending = [item for item in items if item.get('status') == 'pending']
for item in pending[:10]:
    print(f"  - Post {item.get('post_id')}: scheduled at {item.get('scheduled_at')}")
print(f"Total pending: {len(pending)}")


#!/usr/bin/env python3
"""Execute remote commands via SSH and fix stuck posts"""
import subprocess
import sys

SSH_KEY = r"C:\Users\hp\.ssh\id_ed25519_do"
HOST = "root@138.68.141.3"

def ssh_exec(command):
    """Execute SSH command and return output"""
    cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        HOST,
        command
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

print("=" * 60)
print("Step 1: Check if scheduler is running")
print("=" * 60)
ssh_exec("ps aux | grep scheduler_daemon | grep -v grep")

print("\n" + "=" * 60)
print("Step 2: Stop scheduler")
print("=" * 60)
ssh_exec("pkill -f scheduler_daemon.py")

print("\n" + "=" * 60)
print("Step 3: Download scheduled_posts.json")
print("=" * 60)
scp_cmd = [
    "scp",
    "-i", SSH_KEY,
    "-o", "StrictHostKeyChecking=no",
    f"{HOST}:/opt/tripavail_ai/data/scheduled_posts.json",
    "scheduled_posts_remote.json"
]
result = subprocess.run(scp_cmd, capture_output=True, text=True)
print(f"SCP download result: {result.returncode}")
if result.stderr:
    print(f"STDERR: {result.stderr}")

print("\n" + "=" * 60)
print("Step 4: Fix the file locally")
print("=" * 60)
try:
    import json
    with open("scheduled_posts_remote.json", "r") as f:
        items = json.load(f)
    
    print(f"Loaded {len(items)} items")
    
    stuck_posts = ['288', '289', '301', '303']
    marked = 0
    for item in items:
        if item.get('post_id') in stuck_posts and item.get('status') == 'pending':
            print(f"  Marking post {item['post_id']} as done")
            item['status'] = 'done'
            marked += 1
    
    if marked > 0:
        with open("scheduled_posts_fixed.json", "w") as f:
            json.dump(items, f, indent=2)
        print(f"✅ Marked {marked} posts as done")
    else:
        print("⚠️ No stuck posts found")
        
except Exception as e:
    print(f"Error fixing file: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("Step 5: Upload fixed file")
print("=" * 60)
scp_cmd = [
    "scp",
    "-i", SSH_KEY,
    "-o", "StrictHostKeyChecking=no",
    "scheduled_posts_fixed.json",
    f"{HOST}:/opt/tripavail_ai/data/scheduled_posts.json"
]
result = subprocess.run(scp_cmd, capture_output=True, text=True)
print(f"SCP upload result: {result.returncode}")

print("\n" + "=" * 60)
print("Step 6: Remove lock file and restart scheduler")
print("=" * 60)
ssh_exec("cd /opt/tripavail_ai && rm -f .scheduler_daemon.lock && PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 &")

print("\n" + "=" * 60)
print("Step 7: Verify scheduler is running")
print("=" * 60)
import time
time.sleep(3)
ssh_exec("ps aux | grep scheduler_daemon | grep -v grep")

print("\n" + "=" * 60)
print("Step 8: Check recent logs")
print("=" * 60)
ssh_exec("tail -30 /opt/tripavail_ai/logs/scheduler.log")

print("\n✅ Done!")


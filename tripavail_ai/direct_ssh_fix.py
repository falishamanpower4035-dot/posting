#!/usr/bin/env python3
"""Direct SSH execution with output capture"""
import subprocess
import sys
from pathlib import Path

SSH_KEY = r"C:\Users\hp\.ssh\id_ed25519_do"
HOST = "root@138.68.141.3"

def run_ssh(command, description):
    """Run SSH command and capture output"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    
    cmd = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", HOST, command]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        output_file = Path("ssh_output_log.txt")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"{description}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Exit Code: {result.returncode}\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")
        
        print(f"Exit Code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# Clear previous log
Path("ssh_output_log.txt").write_text("SSH Execution Log\n" + "="*60 + "\n", encoding="utf-8")

print("Starting SSH diagnostics and fix...")

# Step 1: Check connection
run_ssh("hostname && date", "Step 1: Test Connection")

# Step 2: Check scheduler status
run_ssh("ps aux | grep scheduler_daemon | grep -v grep", "Step 2: Check Scheduler Status")

# Step 3: Check recent logs
run_ssh("tail -50 /opt/tripavail_ai/logs/scheduler.log", "Step 3: Check Recent Logs")

# Step 4: Check for error posts
run_ssh("tail -100 /opt/tripavail_ai/logs/scheduler.log | grep -E '(288|289|301|303)' | tail -20", "Step 4: Check Error Posts")

# Step 5: Stop scheduler
run_ssh("pkill -f scheduler_daemon.py && sleep 2 && echo 'Scheduler stopped'", "Step 5: Stop Scheduler")

# Step 6: Download schedule file
print("\n" + "="*60)
print("Step 6: Download Schedule File")
print("="*60)
scp_cmd = ["scp", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", 
           f"{HOST}:/opt/tripavail_ai/data/scheduled_posts.json", "scheduled_posts_remote.json"]
result = subprocess.run(scp_cmd, capture_output=True, text=True)
print(f"SCP Exit Code: {result.returncode}")
if result.returncode == 0:
    print("✅ File downloaded successfully")
    
    # Step 7: Fix the file
    print("\n" + "="*60)
    print("Step 7: Fix Schedule File")
    print("="*60)
    
    import json
    try:
        with open("scheduled_posts_remote.json", "r") as f:
            items = json.load(f)
        
        print(f"Loaded {len(items)} scheduled items")
        
        stuck_posts = ['288', '289', '301', '303']
        marked = 0
        for item in items:
            if item.get('post_id') in stuck_posts and item.get('status') == 'pending':
                print(f"  ✅ Marking post {item['post_id']} as done")
                item['status'] = 'done'
                marked += 1
        
        if marked > 0:
            with open("scheduled_posts_fixed.json", "w") as f:
                json.dump(items, f, indent=2)
            print(f"\n✅ Marked {marked} posts as done")
            
            # Step 8: Upload fixed file
            print("\n" + "="*60)
            print("Step 8: Upload Fixed File")
            print("="*60)
            scp_cmd = ["scp", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
                       "scheduled_posts_fixed.json", f"{HOST}:/opt/tripavail_ai/data/scheduled_posts.json"]
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            print(f"SCP Upload Exit Code: {result.returncode}")
            if result.returncode == 0:
                print("✅ Fixed file uploaded successfully")
        else:
            print("⚠️ No stuck posts found in pending status")
    except Exception as e:
        print(f"ERROR fixing file: {e}")
else:
    print(f"ERROR downloading file: {result.stderr}")

# Step 9: Restart scheduler
run_ssh("cd /opt/tripavail_ai && rm -f .scheduler_daemon.lock && PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 & sleep 3 && echo 'Scheduler restarted'", "Step 9: Restart Scheduler")

# Step 10: Verify scheduler is running
run_ssh("ps aux | grep scheduler_daemon | grep -v grep", "Step 10: Verify Scheduler Running")

# Step 11: Check logs after restart
run_ssh("tail -30 /opt/tripavail_ai/logs/scheduler.log", "Step 11: Check Logs After Restart")

print("\n" + "="*60)
print("COMPLETE! Check ssh_output_log.txt for full details")
print("="*60)


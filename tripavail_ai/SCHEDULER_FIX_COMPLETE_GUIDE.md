# Scheduler Error Fix - Complete Guide

## Problem Summary
Posts 288, 289, 301, 303 are stuck in a loop:
- They're missing `original_title` and `caption` metadata
- They get archived but remain "pending" in the scheduler
- The scheduler keeps trying to process them every 5 minutes
- This generates continuous error emails

## What I've Fixed

### 1. ✅ Code Bug Fixed - `mark_done()` Scoping Error
**File:** `scripts/scheduler_daemon.py` (line 209-210)

**Problem:** The nested `_mark_failed()` function couldn't access `mark_done` from outer scope.

**Fix Applied:**
```python
# OLD (broken):
try:
    mark_done(post_id)
except Exception as mark_err:
    logger.warning(f"Failed to mark post {post_id} as done after failure: {mark_err}")

# NEW (fixed):
try:
    from core.scheduling.scheduler import mark_done as _mark_done
    _mark_done(post_id)
except Exception as mark_err:
    logger.warning(f"Failed to mark post {post_id} as done after failure: {mark_err}")
```

**Status:** ✅ Fixed code uploaded to `/opt/tripavail_ai/scripts/scheduler_daemon.py`

### 2. ⏳ Database Fix Needed - Mark Stuck Posts as Done
**File:** `/opt/tripavail_ai/data/scheduled_posts.json` (on droplet)

**Problem:** Posts 288, 289, 301, 303 are still marked as "pending" in this file.

**Fix Needed:** Change their status from "pending" to "done"

## How to Complete the Fix

### OPTION 1: Automated Batch File (Recommended)

1. Open File Explorer
2. Navigate to: `D:\posty\tripavail_ai`
3. Double-click: **`FIX_SCHEDULER_ERRORS.bat`**
4. Wait for it to complete (should take 10-15 seconds)
5. Check the output - it will show you the results

### OPTION 2: Manual PowerShell Commands

Open PowerShell and run these commands one by one:

```powershell
# 1. Stop the scheduler
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "pkill -f scheduler_daemon.py"

# 2. Download the schedule file
scp -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3:/opt/tripavail_ai/data/scheduled_posts.json scheduled_posts_backup.json

# 3. Fix the file
python -c "import json; items = json.load(open('scheduled_posts_backup.json')); [item.update({'status': 'done'}) for item in items if item.get('post_id') in ['288', '289', '301', '303'] and item.get('status') == 'pending']; json.dump(items, open('scheduled_posts_fixed.json', 'w'), indent=2); print('Fixed!')"

# 4. Upload the fixed file
scp -i C:\Users\hp\.ssh\id_ed25519_do scheduled_posts_fixed.json root@138.68.141.3:/opt/tripavail_ai/data/scheduled_posts.json

# 5. Restart the scheduler
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "cd /opt/tripavail_ai && rm -f .scheduler_daemon.lock && PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 &"

# 6. Verify it's running
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "ps aux | grep scheduler_daemon | grep -v grep"

# 7. Check logs for errors
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "tail -30 /opt/tripavail_ai/logs/scheduler.log"
```

### OPTION 3: Direct SSH (If Above Doesn't Work)

```bash
# SSH into the droplet
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3

# Once connected, run:
cd /opt/tripavail_ai

# Stop scheduler
pkill -f scheduler_daemon.py

# Fix the schedule file
python3 << 'EOF'
import json
from pathlib import Path

file = Path("data/scheduled_posts.json")
with open(file) as f:
    items = json.load(f)

count = 0
for item in items:
    if item.get('post_id') in ['288', '289', '301', '303'] and item.get('status') == 'pending':
        item['status'] = 'done'
        print(f"✅ Marked post {item['post_id']} as done")
        count += 1

with open(file, 'w') as f:
    json.dump(items, f, indent=2)

print(f"\n✅ Fixed {count} posts!")
EOF

# Restart scheduler
rm -f .scheduler_daemon.lock
PYTHONPATH=/opt/tripavail_ai nohup /opt/tripavail_ai/venv/bin/python scripts/scheduler_daemon.py >> logs/scheduler.log 2>&1 &

# Verify
ps aux | grep scheduler_daemon | grep -v grep
tail -30 logs/scheduler.log
```

## Expected Results

After running the fix:

1. **No more error emails** for posts 288, 289, 301, 303
2. **Scheduler logs** should show normal operation
3. **Posts will be marked as done** and won't be retried
4. **New posts** will be processed normally

## Verification Commands

To check if the fix worked:

```bash
# Check if scheduler is running
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "ps aux | grep scheduler_daemon"

# Check recent logs (should show no errors for 288, 289, 301, 303)
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "tail -50 /opt/tripavail_ai/logs/scheduler.log | grep -E '288|289|301|303'"

# Check if posts are marked as done
ssh -i C:\Users\hp\.ssh\id_ed25519_do root@138.68.141.3 "cat /opt/tripavail_ai/data/scheduled_posts.json | grep -A 3 -B 1 '\"288\"'"
```

## Why This Happened

1. **Missing Metadata:** Posts 288, 289, 301, 303 were created without `original_title` and `caption` fields
2. **Archiving Logic:** The scheduler correctly archived them to prevent posting
3. **Mark Done Bug:** The `mark_done()` function had a scoping bug and couldn't mark them as done
4. **Recreation Loop:** After archiving, the posts were recreated and the cycle repeated

## What's Fixed Now

1. ✅ **Code Bug:** The `mark_done()` scoping issue is fixed
2. ✅ **Uploaded:** Fixed code is on the droplet
3. ⏳ **Database:** Need to run the fix script to mark posts as done
4. ✅ **Prevention:** Future posts with missing metadata will be archived AND marked as done (no loop)

## Files Created

- `FIX_SCHEDULER_ERRORS.bat` - Automated fix script
- `FIX_SCHEDULER_MANUAL_STEPS.txt` - Manual instructions
- `SCHEDULER_FIX_COMPLETE_GUIDE.md` - This file
- `fix_stuck_posts.py` - Python script to mark posts as done
- `mark_posts_done.py` - Alternative Python script

## Terminal Issue Note

The Cursor terminal is not displaying command output. This is why I created the batch file and manual instructions. The commands ARE executing (exit code 0) but output is suppressed. Running the batch file directly from File Explorer will show the output in a normal Command Prompt window.

---

**Next Step:** Run `FIX_SCHEDULER_ERRORS.bat` to complete the fix!


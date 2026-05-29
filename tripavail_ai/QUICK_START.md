# TripAvail AI Bot - Quick Start Guide 🚀

## Current Status: ✅ FULLY OPERATIONAL

All systems tested and working on production server (138.68.141.3)

---

## What the Bot Does

### Automated Workflow

1. **Every 2 Hours:**
   - Fetches latest tourism news from NewsData.io
   - Analyzes and scores each story (1-10 scale)
   - Generates videos for stories scoring 7+
   - Schedules posts automatically

2. **Scheduling Rules:**
   - **Score 7-9:** Post 20 minutes after generation
   - **Score 10+:** Post at peak times (6 PM, 8 PM, 9 PM Pakistan Time)
   - **Smart Scheduling:** Learns optimal patterns for high-ranking content
   - **Peak Time Logic:** Only highest-ranked news during 7-11 PM window

3. **Every 60 Seconds:**
   - Daemon checks for due posts
   - Posts to Instagram, Facebook, YouTube automatically
   - Marks completed posts as "done"

4. **Cleanup:**
   - Deletes posts older than 24 hours
   - Archives ElevenLabs background music

---

## Local Development

### Run Single Test Post (15 seconds)
```bash
cd D:\posty\tripavail_ai
$env:PYTHONPATH = (Get-Location).Path
.\venv\Scripts\python scripts\schedule_single_post.py
```

### Generate and Post Immediately
```bash
cd D:\posty\tripavail_ai
$env:PYTHONPATH = (Get-Location).Path
.\venv\Scripts\python scripts\generate_and_post_now.py
```

### Check Environment Variables
```bash
cd D:\posty\tripavail_ai
$env:PYTHONPATH = (Get-Location).Path
.\venv\Scripts\python scripts\check_env.py
```

### Run Two-Hour Scheduler Once
```bash
cd D:\posty\tripavail_ai
$env:PYTHONPATH = (Get-Location).Path
.\venv\Scripts\python scripts\run_two_hour_scheduler.py
```

---

## Production Server Commands

### SSH Access
```powershell
$KEY="C:\Users\$env:USERNAME\.ssh\id_ed25519"
ssh -i $KEY root@138.68.141.3
```

### Check Service Status
```bash
systemctl status tripavail-daemon.service
systemctl status tripavail-twohour.service
systemctl status tripavail-twohour.timer
```

### View Live Logs
```bash
# Daemon logs (posting)
journalctl -u tripavail-daemon.service -f

# Scheduler logs (generation)
journalctl -u tripavail-twohour.service -f

# Application logs
tail -f /opt/tripavail_ai/logs/scheduler_daemon.log
tail -f /opt/tripavail_ai/logs/two_hour_scheduler.log
```

### Restart Services
```bash
systemctl restart tripavail-daemon.service
systemctl restart tripavail-twohour.timer
```

### View Scheduled Posts
```bash
cat /opt/tripavail_ai/data/scheduled_posts.json
```

### Manual Test Post
```bash
cd /opt/tripavail_ai
venv/bin/python scripts/schedule_single_post.py
```

---

## Deployment Process

### Package Local Changes
```powershell
cd D:\posty
tar -czf update.tar.gz -C tripavail_ai --exclude=venv --exclude=__pycache__ --exclude="*.pyc" --exclude=data/posts --exclude=logs .
```

### Upload to Server
```powershell
$KEY="C:\Users\$env:USERNAME\.ssh\id_ed25519"
scp -i $KEY update.tar.gz root@138.68.141.3:/tmp/
```

### Apply on Server
```bash
ssh -i $KEY root@138.68.141.3
cd /opt/tripavail_ai
tar -xzf /tmp/update.tar.gz
systemctl restart tripavail-daemon.service
systemctl restart tripavail-twohour.timer
```

---

## Troubleshooting

### Bot Not Posting
1. Check daemon status: `systemctl status tripavail-daemon.service`
2. View logs: `journalctl -u tripavail-daemon.service -f`
3. Check scheduled posts: `cat data/scheduled_posts.json`
4. Restart daemon: `systemctl restart tripavail-daemon.service`

### YouTube Not Working
1. Check token: `venv/bin/python scripts/test_youtube_now.py`
2. If expired, generate new token from OAuth Playground
3. Update `config/settings.py` with new `YOUTUBE_REFRESH_TOKEN`
4. Redeploy and restart services

### No New Posts Being Generated
1. Check timer status: `systemctl status tripavail-twohour.timer`
2. View scheduler logs: `journalctl -u tripavail-twohour.service -f`
3. Manually trigger: `systemctl start tripavail-twohour.service`
4. Check API keys: `venv/bin/python scripts/check_env.py`

### FFmpeg Errors
1. Verify ffmpeg installed: `which ffmpeg`
2. Check PATH in service files: `cat /etc/systemd/system/tripavail-daemon.service`
3. Ensure PATH includes `/usr/bin`

---

## File Structure

```
tripavail_ai/
├── config/
│   └── settings.py              # All API keys and configuration
├── core/
│   ├── content/                 # Post management, story analysis
│   ├── media/                   # Image, video, audio generation
│   ├── news/                    # News fetching and editing
│   ├── scheduling/              # Scheduling logic and learning
│   └── social/                  # Instagram, Facebook, YouTube posters
├── scripts/
│   ├── run_two_hour_scheduler.py    # Main scheduler (runs every 2h)
│   ├── scheduler_daemon.py          # Posting daemon (runs continuously)
│   ├── schedule_single_post.py      # Manual single post
│   ├── generate_and_post_now.py     # Immediate post
│   ├── check_env.py                 # Environment checker
│   └── cleanup_posts.py             # Delete old posts
├── deploy/
│   ├── tripavail-daemon.service     # Systemd service for daemon
│   ├── tripavail-twohour.service    # Systemd service for scheduler
│   └── tripavail-twohour.timer      # Systemd timer (every 2h)
├── data/
│   ├── posts/                       # Generated videos and assets
│   └── scheduled_posts.json         # Scheduling queue
├── logs/                            # Application logs
├── production_pipeline.py           # Main content generation pipeline
└── .env                             # Environment variables (DO NOT COMMIT)
```

---

## Important Notes

### API Costs
- **OpenAI:** ~$0.10-0.30 per video (GPT-4, DALL-E, TTS)
- **NewsData.io:** Free tier (200 requests/day)
- **ElevenLabs:** Free tier (10,000 chars/month)
- **Pexels/Unsplash:** Free (no cost)
- **Social Media APIs:** Free

**Estimated Cost:** ~$5-15/day depending on posting frequency

### Storage Management
- Posts auto-delete after 24 hours
- Background music archived before deletion
- Logs rotate automatically (logrotate)
- Keep ~10GB free space for video generation

### Peak Times (Pakistan Time)
- 6:00 PM (13:00 UTC)
- 8:00 PM (15:00 UTC)
- 9:00 PM (16:00 UTC)

### Posting Platforms
- **Instagram:** Reels (15-90 seconds)
- **Facebook:** Reels (15-90 seconds, fallback to regular video)
- **YouTube:** Shorts (15-60 seconds)

---

## Contact & Support

**Project:** TripAvail AI Tourism Content Bot  
**Email:** tripavail92@gmail.com  
**Server:** 138.68.141.3 (DigitalOcean London)

---

*Last Updated: November 1, 2025*  
*All systems operational ✅*


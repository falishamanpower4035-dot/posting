#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

import pytz

SCHEDULE_FILE = Path("data/scheduled_posts.json")
PK_TZ = pytz.timezone("Asia/Karachi")

PEAK_SLOTS = [18, 20, 21]  # 6pm, 8pm, 9pm
PEAK_WINDOW_START = 19  # inclusive
PEAK_WINDOW_END = 23    # exclusive; 19:00-23:00 means 19,20,21,22 hours available for spacing


@dataclass
class ScheduledPost:
    post_id: str
    scheduled_at: str  # ISO time in UTC
    priority: str      # normal | peak
    platforms: List[str]
    status: str = "pending"  # pending | done | cancelled


def _now_utc() -> datetime:
    # Use timezone-aware datetime (fix deprecated utcnow)
    return datetime.now(timezone.utc)


def _load_all() -> List[Dict[str, Any]]:
    """Load all scheduled posts with error handling"""
    if not SCHEDULE_FILE.exists():
        return []
    try:
        content = SCHEDULE_FILE.read_text(encoding="utf-8")
        if not content.strip():
            return []
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Log error but don't crash - return empty list
        import logging
        logging.error(f"Failed to parse scheduled_posts.json: {e}")
        return []
    except Exception as e:
        import logging
        logging.error(f"Error loading scheduled_posts.json: {e}")
        return []


def _save_all(items: List[Dict[str, Any]]) -> None:
    """Save all scheduled posts with error handling"""
    try:
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Write to temporary file first, then rename (atomic operation)
        temp_file = SCHEDULE_FILE.with_suffix('.json.tmp')
        temp_file.write_text(json.dumps(items, indent=2), encoding="utf-8")
        temp_file.replace(SCHEDULE_FILE)  # Atomic rename
    except Exception as e:
        import logging
        logging.error(f"Error saving scheduled_posts.json: {e}")
        raise


def list_scheduled(status: Optional[str] = None) -> List[ScheduledPost]:
    raw = _load_all()
    out: List[ScheduledPost] = []
    for r in raw:
        try:
            if status and r.get("status") != status:
                continue
            out.append(ScheduledPost(**r))
        except Exception:
            continue
    return out


def add_schedule(post_id: str, when_dt_utc: datetime, priority: str = "normal", platforms: Optional[List[str]] = None) -> bool:
    """
    Add a post to the schedule
    
    Args:
        post_id: Post identifier
        when_dt_utc: When to post (timezone-aware datetime)
        priority: Priority level (normal | peak)
        platforms: List of platforms to post to
        
    Returns:
        True if added successfully, False if duplicate or error
    """
    platforms = platforms or ["instagram", "facebook", "youtube"]
    items = _load_all()
    
    # CRITICAL: Check if this post is already scheduled OR already posted
    # Prevent duplicate schedules entirely - if post is already scheduled pending, skip
    # Also check if post is already posted to any platform (prevent re-scheduling)
    from core.content.post_manager import PostManager
    pm = PostManager()
    
    # Check if already posted to any platform - if so, don't schedule
    if pm.is_posted(post_id, "instagram") or pm.is_posted(post_id, "facebook") or pm.is_posted(post_id, "youtube"):
        # Already posted, don't schedule
        return False
    
    # Check for duplicate: same post_id with pending status at ANY time
    # This prevents the same post from being scheduled multiple times
    for existing in items:
        if existing.get("post_id") == post_id and existing.get("status") == "pending":
            # Duplicate pending schedule found - skip to prevent duplicate posting
            return False
    
    when_iso = when_dt_utc.astimezone(pytz.utc).isoformat()
    
    items.append(asdict(ScheduledPost(
        post_id=post_id,
        scheduled_at=when_iso,
        priority=priority,
        platforms=platforms,
        status="pending",
    )))
    _save_all(items)
    return True


def mark_done(post_id: str) -> None:
    items = _load_all()
    for r in items:
        if r.get("post_id") == post_id and r.get("status") == "pending":
            r["status"] = "done"
    _save_all(items)


def next_peak_slot_utc(preferred_hours: List[int] = PEAK_SLOTS) -> datetime:
    now_pk = datetime.now(PK_TZ)
    # Build candidate times for today and tomorrow
    candidates: List[datetime] = []
    for day_offset in (0, 1):
        base = (now_pk + timedelta(days=day_offset)).replace(minute=0, second=0, microsecond=0)
        # Strict preferred slots first (e.g., 18,20,21)
        for h in preferred_hours:
            candidates.append(base.replace(hour=h))
        # Then fill the window 19-22 for spacing backup
        for h in range(PEAK_WINDOW_START, PEAK_WINDOW_END):
            if h not in preferred_hours:
                candidates.append(base.replace(hour=h))
    # Filter future only
    candidates = [c for c in candidates if c > now_pk]

    # Avoid collisions: ensure no two posts are within the same hour
    scheduled = list_scheduled(status="pending")
    scheduled_hours = set()
    for s in scheduled:
        t = datetime.fromisoformat(s.scheduled_at).astimezone(PK_TZ)
        scheduled_hours.add((t.year, t.month, t.day, t.hour))

    for c in candidates:
        key = (c.year, c.month, c.day, c.hour)
        if key not in scheduled_hours:
            return c.astimezone(pytz.utc)

    # Fallback: 2 hours from now
    return (now_pk + timedelta(hours=2)).astimezone(pytz.utc)


def schedule_after_minutes(post_id: str, minutes: int, priority: str = "normal", platforms: Optional[List[str]] = None) -> None:
    when_utc = (_now_utc() + timedelta(minutes=minutes)).astimezone(pytz.utc)
    add_schedule(post_id, when_utc, priority=priority, platforms=platforms)


def schedule_peak(post_id: str, platforms: Optional[List[str]] = None) -> None:
    when_utc = next_peak_slot_utc()
    add_schedule(post_id, when_utc, priority="peak", platforms=platforms)


def schedule_smart_peak(post_id: str, platforms: Optional[List[str]] = None) -> None:
    """Use learning-based hour recommendations; fallback to static peak slots.
    Ensures hour-level spacing across pending items.
    """
    try:
        from core.scheduling.learning import LearningScheduler  # lazy import
        ls = LearningScheduler()
        hours = ls.recommend_hours(k=3)
        when_utc = next_peak_slot_utc(preferred_hours=hours)
    except Exception:
        when_utc = next_peak_slot_utc()
    add_schedule(post_id, when_utc, priority="peak", platforms=platforms)

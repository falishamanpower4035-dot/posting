"""APScheduler-based worker process.

Run locally:
    python -m sma.worker.main

On Railway / Render this is the entry-point for the `worker` service.
Three jobs run in-process:
  - process_scheduled_posts:  every 60 seconds
  - discover_topics:          every 30 minutes
  - refresh_oauth_tokens:     every hour
"""

from __future__ import annotations

import signal
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from sma import __version__
from sma.config import get_settings
from sma.worker.jobs.discover_topics import discover_topics_for_all_tenants
from sma.worker.jobs.process_schedules import process_due_schedules
from sma.worker.jobs.refresh_tokens import refresh_due_tokens


def _build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        process_due_schedules,
        IntervalTrigger(seconds=60),
        id="process_scheduled_posts",
        max_instances=1,         # never overlap with itself
        coalesce=True,           # if we fall behind, just run once when we catch up
        misfire_grace_time=300,
    )
    scheduler.add_job(
        discover_topics_for_all_tenants,
        IntervalTrigger(minutes=30),
        id="discover_topics",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=600,
    )
    scheduler.add_job(
        refresh_due_tokens,
        IntervalTrigger(hours=1),
        id="refresh_oauth_tokens",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
    )
    return scheduler


def main() -> int:
    settings = get_settings()
    logger.info(
        f"Starting Social Media Automation worker v{__version__} "
        f"(mode={settings.deployment_mode.value})"
    )

    scheduler = _build_scheduler()

    def _graceful_shutdown(signum, frame):  # type: ignore[no-untyped-def]
        logger.info(f"Received signal {signum}; shutting down scheduler")
        scheduler.shutdown(wait=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, _graceful_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _graceful_shutdown)

    # Run jobs once at startup so a fresh deploy doesn't wait up to 30 min
    # for the first topic discovery cycle.
    logger.info("Running initial jobs at startup...")
    try:
        process_due_schedules()
    except Exception as e:
        logger.error(f"initial process_due_schedules failed: {e}")
    # Don't run discover_topics at startup — it makes API calls and could be
    # expensive on every restart. Let the schedule pick it up.

    logger.info("Scheduler started. Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  {job.id} → {job.trigger}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

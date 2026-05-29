#!/usr/bin/env python3
from __future__ import annotations

import time
import atexit
from pathlib import Path
import signal
import sys
import ssl
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()
import pytz
from loguru import logger

from core.content.post_manager import PostManager
from core.scheduling.scheduler import list_scheduled, mark_done
from core.social.platforms.facebook_poster import FacebookPoster
from core.social.platforms.instagram_poster import InstagramPoster
from core.social.platforms.youtube_uploader import YouTubeUploader
from core.pipeline.orchestrator.lock import FileLock
from config import settings

# File lock for Facebook posting to prevent race conditions across processes
_facebook_post_lock_file = Path(".facebook_post.lock")
_scheduler_lock_file = Path(".scheduler_daemon.lock")
_STALE_LOCK_MAX_AGE = timedelta(minutes=10)

# Email notification helper
def send_email_notification(message: str, level: str = "info"):
    """Send email notification when posts are published"""
    try:
        if not getattr(settings, 'EMAIL_ENABLED', False):
            return
        
        from core.utils.gmail_notifier import GmailNotifier
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        receiver_email = getattr(settings, 'NOTIFY_EMAIL', 'holywolf92@gmail.com')
        sender_email = getattr(settings, 'SMTP_FROM_EMAIL', getattr(settings, 'SMTP_USER', 'tripavail92@gmail.com'))
        login_user = getattr(settings, 'SMTP_USER', sender_email)
        subject = f"TripAvail - Post {level.upper()}"
        body = f"""
TripAvail Post Notification

{message}

Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        # Try Gmail API first (recommended)
        if getattr(settings, 'EMAIL_METHOD', 'gmail_api').lower() == 'gmail_api':
            try:
                client_secret = Path(getattr(settings, 'GMAIL_CLIENT_SECRET_FILE', 'client_secret.json'))
                token_file = Path(getattr(settings, 'GMAIL_TOKEN_FILE', 'gmail_token.json'))
                
                if client_secret.exists() and token_file.exists():
                    notifier = GmailNotifier(client_secret, token_file)
                    msg_id = notifier.send_email(sender_email, receiver_email, subject, body)
                    logger.info(f"📧 Email sent via Gmail API to {receiver_email} (id={msg_id})")
                    return
            except Exception as e:
                logger.warning(f"Gmail API email failed: {e}, trying SMTP...")
        
        # Fallback to SMTP
        password = getattr(settings, 'SMTP_PASSWORD', '')
        if not password:
            logger.warning("SMTP_PASSWORD not set, skipping email notification")
            return
        
        host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
        port = int(getattr(settings, 'SMTP_PORT', 465))
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        use_ssl = getattr(settings, 'SMTP_USE_SSL', None)
        if use_ssl is None:
            use_ssl = (port == 465)
        use_tls = getattr(settings, 'SMTP_USE_TLS', None)
        if use_tls is None:
            use_tls = not use_ssl

        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(login_user, password)
                server.send_message(msg)
        else:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(login_user, password)
                server.send_message(msg)
        
        logger.info(f"📧 Email sent via SMTP to {receiver_email}")
    except Exception as e:
        logger.error(f"Email notification error: {e}")


def post_now(post_id: str) -> bool:
    """
    Post to all platforms (Instagram, Facebook, YouTube)
    
    Args:
        post_id: Post identifier
        
    Returns:
        True if posted to at least one platform, False otherwise
    """
    pm = PostManager()

    def voiceover_summary(metadata):
        if not metadata:
            return ""
        voice_name = (metadata.get('voiceover_voice') or '').strip()
        voice_id = (metadata.get('voiceover_voice_id') or '').strip()
        provider = (metadata.get('voiceover_provider') or '').strip()
        if not voice_name and not voice_id and not provider:
            return ""
        parts = []
        if voice_name:
            parts.append(voice_name)
        if voice_id and voice_id not in parts:
            parts.append(voice_id)
        summary = " | ".join(parts) if parts else "Unknown"
        if provider:
            summary += f" [{provider}]"
        return f"\nVoiceover: {summary}"
    
    # CRITICAL: Check if already posted to ALL platforms - if so, skip entirely
    # This prevents the same post from being posted multiple times if scheduled multiple times
    # IMPORTANT: Only skip if ALL platforms are posted - allow partial posting to continue
    ig_posted = pm.is_posted(post_id, "instagram")
    fb_posted = pm.is_posted(post_id, "facebook")
    yt_posted = pm.is_posted(post_id, "youtube")
    
    # Double-check after a tiny delay to catch race conditions
    if ig_posted or fb_posted or yt_posted:
        time.sleep(0.1)
        ig_posted2 = pm.is_posted(post_id, "instagram")
        fb_posted2 = pm.is_posted(post_id, "facebook")
        yt_posted2 = pm.is_posted(post_id, "youtube")
        
        # Use the most recent check result
        ig_final = ig_posted or ig_posted2
        fb_final = fb_posted or fb_posted2
        yt_final = yt_posted or yt_posted2
        
        # Only skip if ALL platforms are already posted
        if ig_final and fb_final and yt_final:
            logger.info(f"Post {post_id} already posted to all platforms (IG={ig_final}, FB={fb_final}, YT={yt_final}), skipping")
            return True
        else:
            # Partially posted - log which platforms are already posted, but continue to post to others
            logger.info(f"Post {post_id} partially posted (IG={ig_final}, FB={fb_final}, YT={yt_final}) - will post to remaining platforms")
    
    # Check if post is archived before processing
    # IMPORTANT: Use base_dir directly, NOT get_post_directory() which creates the directory!
    post_dir = pm.base_dir / f"post_{post_id}"
    if not post_dir.exists():
        # Post directory doesn't exist - check if it's archived
        archive_base = pm.base_dir.parent / "posts_archive"
        if archive_base.exists():
            for reason_dir in archive_base.iterdir():
                if reason_dir.is_dir():
                    archived_post = reason_dir / f"post_{post_id}"
                    if archived_post.exists() or any(archived_post.name.startswith(f"post_{post_id}_") for archived_post in reason_dir.iterdir()):
                        logger.info(f"Post {post_id} is archived (reason: {reason_dir.name}), skipping")
                        try:
                            from core.scheduling.scheduler import mark_done
                            mark_done(post_id)
                        except Exception as e:
                            logger.warning(f"Failed to mark archived post {post_id} as done: {e}")
                        return False
        # Post directory doesn't exist and not archived - treat as missing
        logger.warning(f"Post {post_id} directory not found and not archived, skipping")
        try:
            from core.scheduling.scheduler import mark_done
            mark_done(post_id)
        except Exception as e:
            logger.warning(f"Failed to mark missing post {post_id} as done: {e}")
        return False

    meta = pm.get_metadata(post_id)

    def _mark_failed(reason: str, details: str, notify_level: str = "error") -> bool:
        logger.error(details)
        try:
            failure_meta = meta.copy() if isinstance(meta, dict) else {}
            status = failure_meta.get('post_status', {})
            status['youtube'] = reason
            failure_meta['post_status'] = status
            failure_meta['last_failure_reason'] = reason
            failure_meta['last_failure_at'] = datetime.now(timezone.utc).isoformat()
            pm.save_metadata(post_id, failure_meta)
        except Exception as meta_err:
            logger.warning(f"Unable to persist failure metadata for post {post_id}: {meta_err}")

        try:
            from core.scheduling.scheduler import mark_done as _mark_done
            _mark_done(post_id)
        except Exception as mark_err:
            logger.warning(f"Failed to mark post {post_id} as done after failure: {mark_err}")

        send_email_notification(
            f"⚠️ Post {post_id} skipped for YouTube\n\nReason: {reason}\nDetails: {details}{voiceover_summary(meta)}",
            notify_level
        )
        return False

    if not meta:
        # Archive immediately - don't retry for missing metadata
        logger.warning(f"Post {post_id}: No metadata found. Archiving post.")
        try:
            pm.archive_post(post_id, reason="missing_metadata")
        except Exception as archive_err:
            logger.error(f"Failed to archive post {post_id}: {archive_err}")
        return _mark_failed(
            "missing_metadata",
            f"Post {post_id}: No metadata found. Post archived."
        )
    if not isinstance(meta, dict):
        # Archive immediately - don't retry for invalid metadata format
        logger.warning(f"Post {post_id}: Metadata is not a dict ({type(meta)}). Archiving post.")
        try:
            pm.archive_post(post_id, reason="invalid_metadata_format")
        except Exception as archive_err:
            logger.error(f"Failed to archive post {post_id}: {archive_err}")
        return _mark_failed(
            "invalid_metadata_format",
            f"Post {post_id}: Metadata is not a dict ({type(meta)}). Post archived."
        )

    required_meta_fields = ("original_title", "caption")
    missing_fields = [field for field in required_meta_fields if not meta.get(field)]
    if missing_fields:
        # Archive immediately - don't retry for missing fields
        logger.warning(f"Post {post_id}: Missing required metadata fields: {', '.join(missing_fields)}. Archiving post.")
        try:
            pm.archive_post(post_id, reason="missing_required_fields")
        except Exception as archive_err:
            logger.error(f"Failed to archive post {post_id}: {archive_err}")
        return _mark_failed(
            "missing_required_fields",
            f"Post {post_id}: Missing required metadata fields: {', '.join(missing_fields)}. Post archived."
        )
        
    video = pm.get_final_video_path(post_id)
    if not video.exists():
        return _mark_failed(
            "video_missing",
            f"Post {post_id}: Video file not found at {video}.",
        )

    title = meta.get("original_title", "")[:70]
    caption = meta.get("caption", meta.get("context_caption", ""))
    hashtags = meta.get("hashtags", [])
    
    # CRITICAL: Normalize hashtags to lowercase (preserve #, lowercase the rest)
    # Example: #NatureLover -> #naturelover, #CostalCharm -> #costalcharm
    normalized_hashtags = []
    for tag in hashtags:
        if isinstance(tag, str):
            if tag.startswith('#'):
                # Keep #, lowercase everything after
                normalized = '#' + tag[1:].lower()
            else:
                # Add # if missing, then lowercase
                normalized = '#' + tag.lower()
            normalized_hashtags.append(normalized)
    hashtags = normalized_hashtags
    
    # CRITICAL: Check if another post with the same title was already posted recently
    # This prevents posting duplicate content even if duplicate detection failed during generation
    if title:
        normalized_title = ' '.join(title.lower().strip().split())
        all_posts = pm.get_all_posts()
        for other_post_id in all_posts:
            if other_post_id == post_id:
                continue
            other_meta = pm.get_metadata(other_post_id)
            if not other_meta:
                continue
            other_title = other_meta.get('original_title', '').strip()
            if not other_title:
                continue
            other_normalized = ' '.join(other_title.lower().split())
            if normalized_title == other_normalized:
                # Check if the other post was already posted to Instagram or Facebook
                other_ig_posted = pm.is_posted(other_post_id, "instagram")
                other_fb_posted = pm.is_posted(other_post_id, "facebook")
                if other_ig_posted or other_fb_posted:
                    logger.warning(f"⚠️ Post {post_id} is duplicate of Post {other_post_id} (same title: '{title[:50]}...')")
                    logger.warning(f"   Post {other_post_id} already posted: IG={other_ig_posted}, FB={other_fb_posted}")
                    logger.warning(f"   Skipping Post {post_id} to prevent duplicate posting")
                    # Mark this post as done to prevent retries
                    from core.scheduling.scheduler import mark_done
                    mark_done(post_id)
                    return False
    
    posted_any = False
    
    # Track retry attempts for YouTube
    youtube_retry_count = meta.get('youtube_retry_count', 0)
    last_youtube_attempt = meta.get('last_youtube_attempt')

    # Instagram
    if not pm.is_posted(post_id, "instagram"):
        try:
            ig = InstagramPoster()
            ig_caption = caption
            if hashtags:
                # CRITICAL: Preserve exact hashtag casing - hashtags are case-sensitive
                hashtag_text = " ".join(hashtags[:30])  # Join with space, preserve exact case
                ig_caption = f"{ig_caption}\n\n{hashtag_text}"
                logger.debug(f"Post {post_id} Instagram hashtags: {hashtags[:5]}")
            if ig.post_reel(video, ig_caption):
                pm.mark_as_posted(post_id, "instagram")
                posted_any = True
                logger.info(f"✅ Post {post_id} posted to Instagram")
                # Send email notification
                send_email_notification(
                    f"✅ Posted to Instagram\n\nPost ID: {post_id}\nTitle: {title}\nPlatform: Instagram{voiceover_summary(meta)}",
                    "success"
                )
            else:
                logger.warning(f"⚠️ Post {post_id} failed to post to Instagram")
                send_email_notification(
                    f"❌ Failed to post to Instagram\n\nPost ID: {post_id}\nTitle: {title}\nPlatform: Instagram{voiceover_summary(meta)}",
                    "error"
                )
        except Exception as e:
            logger.error(f"❌ Post {post_id} Instagram error: {e}")
            send_email_notification(
                f"❌ Instagram Error\n\nPost ID: {post_id}\nTitle: {title}\nError: {str(e)}{voiceover_summary(meta)}",
                "error"
            )
        
        # Delay before next platform to prevent rate limiting (only if we attempted posting)
        time.sleep(30)

    # Facebook (with longer delay due to rate limiting)
    if not pm.is_posted(post_id, "facebook"):
        # Use file lock to prevent race conditions with Smart Scheduler (cross-process)
        fb_lock = FileLock(_facebook_post_lock_file, timeout_sec=30)
        if fb_lock.acquire():
            try:
                # Double-check inside lock to prevent race conditions
                if pm.is_posted(post_id, "facebook"):
                    logger.info(f"Post {post_id} already posted to Facebook (race condition prevented)")
                else:
                    try:
                        fb = FacebookPoster()
                        fb_caption = caption
                        if hashtags:
                            # CRITICAL: Preserve exact hashtag casing - hashtags are case-sensitive
                            hashtag_text = " ".join(hashtags[:30])  # Join with space, preserve exact case
                            fb_caption = f"{fb_caption}\n\n{hashtag_text}"
                            logger.debug(f"Post {post_id} Facebook hashtags: {hashtags[:5]}")

                        # Attempt to post
                        # Note: Facebook poster also receives hashtags list for internal use
                        success = fb.post_video(video, fb_caption, hashtags)

                        # Mark as posted ONLY if successful
                        if success:
                            pm.mark_as_posted(post_id, "facebook")
                            posted_any = True
                            logger.info(f"✅ Post {post_id} posted to Facebook")
                            # Send email notification
                            send_email_notification(
                                f"✅ Posted to Facebook\n\nPost ID: {post_id}\nTitle: {title}\nPlatform: Facebook{voiceover_summary(meta)}",
                                "success"
                            )
                        else:
                            # Check again - maybe it posted but returned False due to API response format
                            # Wait a moment for Facebook API to process
                            time.sleep(2)
                            # Re-check if somehow posted (Facebook API might be slow)
                            if not pm.is_posted(post_id, "facebook"):
                                logger.warning(f"⚠️ Post {post_id} failed to post to Facebook (likely rate limited)")
                                send_email_notification(
                                    f"❌ Failed to post to Facebook\n\nPost ID: {post_id}\nTitle: {title}\nPlatform: Facebook\nReason: Likely rate limited{voiceover_summary(meta)}",
                                    "error"
                                )
                    except Exception as e:
                        logger.error(f"❌ Post {post_id} Facebook error: {e}")
                        send_email_notification(
                            f"❌ Facebook Error\n\nPost ID: {post_id}\nTitle: {title}\nError: {str(e)}{voiceover_summary(meta)}",
                            "error"
                        )
            finally:
                fb_lock.release()
        else:
            logger.warning(f"⚠️ Could not acquire Facebook lock for post {post_id}, skipping (another process is posting)")

        # Delay before next platform to prevent rate limiting (60 seconds for Facebook)
        time.sleep(60)

    # YouTube - with retry limit and cooldown
    if not pm.is_posted(post_id, "youtube"):
        # Check retry limit (max 3 retries)
        if youtube_retry_count >= 3:
            logger.warning(f"⚠️ Post {post_id} YouTube retry limit reached (3 attempts). Archiving post.")
            # Archive post after 3 failed attempts
            try:
                pm.archive_post(post_id, reason="youtube_retry_limit")
            except Exception as archive_err:
                logger.error(f"Failed to archive post {post_id}: {archive_err}")
            # Don't mark as done here - let the main loop handle it
            return posted_any
        
        # Check cooldown period (wait at least 1 hour between retries)
        if last_youtube_attempt:
            try:
                last_attempt_time = datetime.fromisoformat(last_youtube_attempt)
                time_since_attempt = (datetime.now(timezone.utc) - last_attempt_time.replace(tzinfo=timezone.utc)).total_seconds()
                if time_since_attempt < 3600:  # 1 hour cooldown
                    remaining_minutes = int((3600 - time_since_attempt) / 60)
                    logger.info(f"Post {post_id} YouTube retry cooldown active ({remaining_minutes} min remaining), skipping")
                    return posted_any
            except Exception as e:
                logger.warning(f"Error checking YouTube cooldown: {e}")
        
        try:
            # Update retry attempt tracking
            meta['youtube_retry_count'] = youtube_retry_count + 1
            meta['last_youtube_attempt'] = datetime.now(timezone.utc).isoformat()
            pm.save_metadata(post_id, meta)

            yt = YouTubeUploader()
            yt.authenticate()
            # CRITICAL: Preserve exact hashtag casing
            # YouTube tags (API) don't use #, but description hashtags should preserve case
            tags = [t.replace('#', '') for t in hashtags[:10]] + ['TripAvail', 'Travel', 'Shorts']  # Remove # for tags API only
            # Use truncate_title to ensure max 60 characters (will be truncated in upload_video too)
            yt_title = yt.truncate_title(title, " | TripAvail")
            # YouTube description: preserve exact hashtag casing with #
            hashtag_text = " ".join(hashtags[:10])  # Preserve exact case
            yt_description = f"{caption}\n\n#Shorts\n\n{hashtag_text}"
            logger.debug(f"Post {post_id} YouTube hashtags: {hashtags[:5]}")
            vid = yt.upload_video(video, title=yt_title, description=yt_description, tags=tags)
            if vid:
                pm.mark_as_posted(post_id, "youtube", f"https://youtube.com/shorts/{vid}")
                posted_any = True
                logger.info(f"✅ Post {post_id} posted to YouTube: {vid}")
                # Refresh metadata so posted_platforms includes YouTube before saving updates
                meta = pm.get_metadata(post_id) or meta
                # Clear retry count on success
                meta['youtube_retry_count'] = 0
                meta.pop('last_youtube_attempt', None)
                pm.save_metadata(post_id, meta)
                # Send email notification
                send_email_notification(
                    f"✅ Posted to YouTube\n\nPost ID: {post_id}\nTitle: {title}\nPlatform: YouTube\nVideo ID: {vid}\nURL: https://youtube.com/shorts/{vid}{voiceover_summary(meta)}",
                    "success"
                )
            else:
                logger.warning(f"⚠️ Post {post_id} failed to post to YouTube (attempt {youtube_retry_count + 1}/3)")
                # Update post_status to track failure
                failure_meta = pm.get_metadata(post_id) or meta
                post_status = failure_meta.get('post_status', {})
                post_status['youtube'] = 'upload_failed'
                failure_meta['post_status'] = post_status
                failure_meta['last_failure_reason'] = 'youtube_upload_failed'
                failure_meta['last_failure_at'] = datetime.now(timezone.utc).isoformat()
                pm.save_metadata(post_id, failure_meta)
                send_email_notification(
                    f"❌ Failed to post to YouTube\n\nPost ID: {post_id}\nTitle: {title}\nPlatform: YouTube\nAttempt: {youtube_retry_count + 1}/3{voiceover_summary(meta)}",
                    "error"
                )
        except Exception as e:
            logger.error(f"❌ Post {post_id} YouTube error: {e}")
            # Update post_status to track error
            failure_meta = pm.get_metadata(post_id) or meta
            post_status = failure_meta.get('post_status', {})
            post_status['youtube'] = f'error: {str(e)[:50]}'
            failure_meta['post_status'] = post_status
            failure_meta['last_failure_reason'] = f'youtube_error: {str(e)[:100]}'
            failure_meta['last_failure_at'] = datetime.now(timezone.utc).isoformat()
            failure_meta['youtube_retry_count'] = youtube_retry_count + 1
            failure_meta['last_youtube_attempt'] = datetime.now(timezone.utc).isoformat()
            pm.save_metadata(post_id, failure_meta)
            send_email_notification(
                f"❌ YouTube Error\n\nPost ID: {post_id}\nTitle: {title}\nError: {str(e)}{voiceover_summary(meta)}",
                "error"
            )
    
    return posted_any


def main() -> None:
    logger.info("Scheduler daemon started. Checking every 60s...")
    
    # File lock to prevent concurrent execution (longer timeout to prevent restart loops)
    # Proactively remove stale locks (e.g., left after crash)
    try:
        if _scheduler_lock_file.exists():
            age = datetime.now(timezone.utc) - datetime.fromtimestamp(
                _scheduler_lock_file.stat().st_mtime, timezone.utc
            )
            if age > _STALE_LOCK_MAX_AGE:
                logger.warning(f"🧹 Removing stale scheduler lock (age={age})")
                _scheduler_lock_file.unlink(missing_ok=True)
    except Exception as stale_err:
        logger.warning(f"Failed to evaluate/remove stale scheduler lock: {stale_err}")

    lock = FileLock(_scheduler_lock_file, timeout_sec=30)
    if not lock.acquire():
        logger.error("Scheduler daemon already running. Exiting.")
        return

    def _release_lock_and_exit(signum=None, frame=None):
        try:
            lock.release()
            logger.info("Scheduler daemon lock released (signal cleanup)")
        finally:
            if signum is not None:
                sys.exit(0)

    # Always release the lock on shutdown
    atexit.register(lock.release)
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _release_lock_and_exit)
        except Exception as sig_err:
            logger.debug(f"Unable to register handler for {sig}: {sig_err}")
    
    try:
        pm = PostManager()  # Reuse PostManager instance

        while True:
            try:
                pending = list_scheduled(status="pending")
                # Use timezone-aware datetime (fix deprecated utcnow)
                now_utc = datetime.now(timezone.utc)

                if not pending:
                    time.sleep(60)
                    continue

                posts_processed = 0
                for item in pending:
                    try:
                        when = datetime.fromisoformat(item.scheduled_at)
                        # Ensure timezone-aware comparison
                        if when.tzinfo is None:
                            when = pytz.utc.localize(when)

                        if now_utc < when:
                            # Not yet time to post, skip
                            continue

                        # CRITICAL: Check if already posted to ALL platforms before attempting
                        # Only skip if ALL platforms are posted - allow partial posting to continue
                        ig_posted = pm.is_posted(item.post_id, "instagram")
                        fb_posted = pm.is_posted(item.post_id, "facebook")
                        yt_posted = pm.is_posted(item.post_id, "youtube")

                        if ig_posted and fb_posted and yt_posted:
                            # Already posted to ALL platforms - mark as done
                            logger.info(
                                f"Post {item.post_id} already posted to all platforms (IG={ig_posted}, FB={fb_posted}, YT={yt_posted}), marking as done"
                            )
                            mark_done(item.post_id)
                            continue
                        if ig_posted or fb_posted or yt_posted:
                            # Partially posted - log but continue to post to remaining platforms
                            logger.info(
                                f"Post {item.post_id} partially posted (IG={ig_posted}, FB={fb_posted}, YT={yt_posted}) - will post to remaining platforms"
                            )

                        # CRITICAL: Check for duplicate posts BEFORE attempting to post
                        # This prevents posting the same news article multiple times
                        meta = pm.get_metadata(item.post_id)
                        if meta:
                            title = meta.get('original_title', '').strip()
                            if title:
                                normalized_title = ' '.join(title.lower().split())
                                all_posts = pm.get_all_posts()
                                duplicate_found = False
                                for other_post_id in all_posts:
                                    if other_post_id == item.post_id:
                                        continue
                                    other_meta = pm.get_metadata(other_post_id)
                                    if not other_meta:
                                        continue
                                    other_title = other_meta.get('original_title', '').strip()
                                    if not other_title:
                                        continue
                                    other_normalized = ' '.join(other_title.lower().split())
                                    if normalized_title == other_normalized:
                                        # Check if the other post was already posted
                                        other_ig = pm.is_posted(other_post_id, "instagram")
                                        other_fb = pm.is_posted(other_post_id, "facebook")
                                        if other_ig or other_fb:
                                            logger.warning(
                                                f"⚠️ Post {item.post_id} is duplicate of Post {other_post_id} (already posted)"
                                            )
                                            logger.warning(f"   Skipping Post {item.post_id} and marking as done")
                                            mark_done(item.post_id)
                                            duplicate_found = True
                                            break
                                if duplicate_found:
                                    continue

                        # CRITICAL: Check each platform individually before posting
                        # This prevents race conditions where multiple instances try to post
                        # Also check if Smart Scheduler already posted this
                        already_posted_fb = pm.is_posted(item.post_id, "facebook")
                        if already_posted_fb:
                            logger.info(
                                f"Post {item.post_id} already posted to Facebook, skipping Facebook posting"
                            )
                            # Still post to other platforms if needed

                        logger.info(f"Posting scheduled post {item.post_id} (priority={item.priority})")
                        posted_any = post_now(item.post_id)

                        # CRITICAL: Small delay to ensure metadata file writes are flushed to disk
                        # This prevents race condition where is_posted() checks before file is written
                        time.sleep(0.5)

                        # Check if now fully posted after attempt
                        insta_posted = pm.is_posted(item.post_id, "instagram")
                        fb_posted = pm.is_posted(item.post_id, "facebook")
                        yt_posted = pm.is_posted(item.post_id, "youtube")

                        logger.info(
                            f"Post {item.post_id} status after posting: IG={insta_posted}, FB={fb_posted}, YT={yt_posted}"
                        )

                        if insta_posted and fb_posted and yt_posted:
                            # Fully posted, mark as done
                            mark_done(item.post_id)
                            logger.info(f"✅ Post {item.post_id} fully posted to all platforms, marked as done")
                            # Send summary email
                            meta = pm.get_metadata(item.post_id)
                            title = meta.get('original_title', 'N/A')[:60] if meta else 'N/A'
                            send_email_notification(
                                "🎉 Post Fully Published!\n\n"
                                f"Post ID: {item.post_id}\nTitle: {title}\n\n"
                                "✅ Instagram: Posted\n"
                                "✅ Facebook: Posted\n"
                                "✅ YouTube: Posted\n\n"
                                "All platforms completed successfully!",
                                "success",
                            )
                        else:
                            # Partially posted - handle based on what's missing
                            # Check if YouTube retry limit reached (handled in post_now)
                            meta = pm.get_metadata(item.post_id)
                            youtube_retry_count = meta.get('youtube_retry_count', 0) if meta else 0

                            if youtube_retry_count >= 3:
                                # Retry limit reached, archive and mark as done
                                logger.warning(
                                    f"Post {item.post_id} YouTube retry limit reached (3 attempts). Archiving post."
                                )
                                try:
                                    pm.archive_post(item.post_id, reason="youtube_retry_limit")
                                except Exception as archive_err:
                                    logger.error(f"Failed to archive post {item.post_id}: {archive_err}")
                                mark_done(item.post_id)
                            elif not yt_posted:
                                # YouTube not posted but under retry limit - keep schedule active
                                logger.info(
                                    f"Post {item.post_id} YouTube not posted - keeping schedule active (retry {youtube_retry_count}/3)"
                                )
                                # Don't mark as done - will retry after cooldown
                            elif not fb_posted and insta_posted:
                                # Facebook rate limited but Instagram posted - mark as done to prevent retries
                                mark_done(item.post_id)
                                logger.warning(
                                    f"Post {item.post_id} Facebook rate limited, marked as done to prevent retries"
                                )
                            else:
                                # Other partial posting scenarios - keep active
                                logger.info(
                                    f"Post {item.post_id} partially posted - keeping schedule active"
                                )

                        posts_processed += 1

                        # Delay between multiple posts to prevent rate limiting (5 minutes minimum)
                        # Only delay if we actually processed a post
                        if posts_processed > 0:
                            logger.info("Waiting 5 minutes before next post to prevent rate limiting...")
                            time.sleep(300)  # 5 minutes between posts
                            posts_processed = 0  # Reset counter after delay
                    except Exception as e:
                        logger.error(f"Error processing post {item.post_id}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                import traceback

                logger.error(traceback.format_exc())

            time.sleep(60)
    finally:
        lock.release()
        logger.info("Scheduler daemon stopped")


if __name__ == "__main__":
    main()

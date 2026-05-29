#!/usr/bin/env python3
"""
Smart Scheduler for TripAvail AI
- Ranks ALL posts using multiple metrics
- Selects top 10 highest-quality posts
- Posts at global peak times across Instagram, Facebook, YouTube
- Intelligent scheduling with timezone optimization
- Performance tracking and analytics
- Smart retry logic with notifications
"""

import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import schedule

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa
from loguru import logger

# Import platform posters
from core.content.post_manager import PostManager
from core.social.platforms.instagram_poster import InstagramPoster
from core.social.platforms.facebook_poster import FacebookPoster
from core.social.platforms.youtube_uploader import YouTubeUploader
from config import settings
from core.utils.gmail_notifier import GmailNotifier
from core.pipeline.orchestrator.lock import FileLock


class SmartScheduler:
    """
    Intelligent scheduler that ranks posts and schedules top 10 at peak times
    """
    
    def __init__(self):
        self.post_manager = PostManager()
        self.data_dir = Path("data")
        
        # Global Peak Times (UTC) - covers major markets
        # These times reach peak audiences across USA, Europe, Asia
        self.peak_times = [
            "06:00",  # 2am EST, 7am London, 2pm China - Asia morning
            "09:00",  # 5am EST, 10am London, 5pm China - Asia evening  
            "14:00",  # 10am EST, 3pm London, 10pm China - USA morning + Europe afternoon
            "18:00",  # 2pm EST, 7pm London, 2am China - USA afternoon + Europe evening
            "21:00",  # 5pm EST, 10pm London, 5am China - USA peak + Europe night
            "23:00",  # 7pm EST, 12am London, 7am China - USA evening
        ]
        
        # Platform posting preferences
        # Each peak time can have multiple platforms
        # Spacing (30-40 min) only applies if multiple posts at SAME peak time
        self.platform_schedule = {
            "instagram": ["06:00", "14:00", "18:00", "21:00"],  # 4 posts/day
            "facebook": ["09:00", "18:00", "23:00"],            # 3 posts/day
            "youtube": ["14:00", "18:00", "21:00"],             # 3 posts/day
        }
        
        # Note: Spacing only used when 2+ platforms post at same time
        # Example: At 18:00, if Instagram+Facebook+YouTube all post,
        # they'll be spaced 30-40 min apart (18:00, 18:35, 19:10)
        
        # Performance tracking
        self.performance_file = self.data_dir / "scheduler_performance.json"
        self.daily_stats_file = self.data_dir / "scheduler_daily_stats.json"
        
        # Configuration
        self.retry_attempts = 3
        self.retry_delay = 15  # minutes
        self.notification_email = getattr(settings, 'NOTIFY_EMAIL', 'tripavail92@gmail.com')
        
        # Daily stats (reset each day)
        self.today_stats = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'posts_attempted': 0,
            'posts_successful': 0,
            'posts_failed': 0,
            'by_platform': {
                'instagram': {'attempted': 0, 'successful': 0, 'failed': 0},
                'facebook': {'attempted': 0, 'successful': 0, 'failed': 0},
                'youtube': {'attempted': 0, 'successful': 0, 'failed': 0}
            }
        }
        
        self._load_today_stats()
        
        logger.info("Smart Scheduler initialized with performance tracking & notifications")
    
    def calculate_post_rank_score(self, post_id: str, metadata: Dict[str, Any]) -> float:
        """
        Calculate comprehensive ranking score for a post
        
        Combines multiple factors:
        - AI score (0-10) - 40% weight
        - Priority score (0-100) - 30% weight  
        - Viral potential (0-100) - 20% weight
        - Freshness (newer = better) - 10% weight
        
        Returns:
            Float score (0-100)
        """
        # Factor 1: AI Score (0-10) → normalize to 0-100
        ai_score = metadata.get('score', 0) * 10  # 0-100
        
        # Factor 2: Priority Score (may not exist in all posts)
        priority_score = metadata.get('priority_score', metadata.get('score', 0) * 10)
        
        # Factor 3: Viral Potential (from intelligence modules)
        viral_potential = metadata.get('viral_potential', 50)  # Default 50
        
        # Factor 4: Freshness (newer posts score higher)
        created_at = metadata.get('created_at')
        freshness_score = 50  # Default
        
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at)
                age_hours = (datetime.now() - created_time).total_seconds() / 3600
                # Newer = higher score (100 for 0 hours, decreases over time)
                freshness_score = max(0, 100 - (age_hours / 24 * 50))  # Decays over days
            except:
                pass
        
        # Weighted combination
        rank_score = (
            ai_score * 0.40 +
            priority_score * 0.30 +
            viral_potential * 0.20 +
            freshness_score * 0.10
        )
        
        return round(rank_score, 2)
    
    def get_top_posts(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N posts ranked by comprehensive metrics
        
        Args:
            count: Number of top posts to return
            
        Returns:
            List of post dictionaries with rank scores
        """
        logger.info(f"Ranking all posts to find top {count}...")
        
        all_posts = self.post_manager.get_all_posts()
        
        if not all_posts:
            logger.warning("No posts found")
            return []
        
        # Score all posts
        ranked_posts = []
        
        for post_id in all_posts:
            metadata = self.post_manager.get_metadata(post_id)
            
            if not metadata:
                continue
            
            # Check if final video exists
            final_video = self.post_manager.get_final_video_path(post_id)
            if not final_video.exists():
                logger.debug(f"Post {post_id} has no final video, skipping")
                continue
            
            # Calculate rank score
            rank_score = self.calculate_post_rank_score(post_id, metadata)
            
            ranked_posts.append({
                'post_id': post_id,
                'rank_score': rank_score,
                'ai_score': metadata.get('score', 0),
                'title': metadata.get('original_title', '')[:50],
                'caption': metadata.get('caption', '')[:100],
                'hashtags': metadata.get('hashtags', []),
                'region': metadata.get('region', 'Unknown'),
                'video_path': str(final_video),
                'created_at': metadata.get('created_at', ''),
                'metadata': metadata
            })
        
        # Sort by rank score (descending)
        ranked_posts.sort(key=lambda x: x['rank_score'], reverse=True)
        
        # Get top N
        top_posts = ranked_posts[:count]
        
        logger.info(f"Top {len(top_posts)} posts selected:")
        for i, post in enumerate(top_posts, 1):
            logger.info(f"  #{i} - Post {post['post_id']}: {post['rank_score']}/100 - {post['title']}")
        
        return top_posts
    
    def get_posts_to_post_today(self, platform: str = None) -> List[Dict[str, Any]]:
        """
        Get top posts that haven't been posted yet today
        
        Args:
            platform: Optional platform filter
            
        Returns:
            List of posts to post
        """
        top_posts = self.get_top_posts(count=10)
        
        # Filter out already posted
        posts_to_post = []
        
        for post in top_posts:
            post_id = post['post_id']
            
            if platform:
                # Check specific platform
                if not self.post_manager.is_posted(post_id, platform):
                    posts_to_post.append(post)
            else:
                # Check if posted to any platform today
                metadata = self.post_manager.get_metadata(post_id)
                posted_platforms = metadata.get('posted_platforms', {})
                
                # Check if posted today
                posted_today = False
                for plat, info in posted_platforms.items():
                    posted_at = info.get('posted_at', '')
                    if posted_at:
                        try:
                            posted_time = datetime.fromisoformat(posted_at)
                            if posted_time.date() == datetime.now().date():
                                posted_today = True
                                break
                        except:
                            pass
                
                if not posted_today:
                    posts_to_post.append(post)
        
        return posts_to_post
    
    def post_to_instagram(self, post_data: Dict[str, Any], retry_count: int = 0) -> bool:
        """Post to Instagram with retry logic"""
        post_id = post_data['post_id']
        logger.info(f"📱 Posting {post_id} to Instagram... (Attempt {retry_count + 1}/{self.retry_attempts})")
        
        self.today_stats['by_platform']['instagram']['attempted'] += 1
        self.today_stats['posts_attempted'] += 1
        
        try:
            # Check if already posted
            if self.post_manager.is_posted(post_id, "instagram"):
                logger.info(f"  Already posted to Instagram")
                return True
            
            poster = InstagramPoster()
            video_path = Path(post_data['video_path'])
            
            # Build caption
            caption = post_data['caption']
            hashtags = post_data.get('hashtags', [])
            if hashtags:
                caption = f"{caption}\n\n{' '.join(hashtags[:30])}"
            
            success = poster.post_reel(video_path, caption)
            
            if success:
                self.post_manager.mark_as_posted(post_id, "instagram")
                self.today_stats['by_platform']['instagram']['successful'] += 1
                self.today_stats['posts_successful'] += 1
                self._save_today_stats()
                
                # Track performance
                self._track_post_performance(post_id, 'instagram', datetime.now())
                
                logger.info(f"  ✅ Posted to Instagram!")
                self._send_notification(f"✅ SUCCESS: Posted {post_id} to Instagram", "success")
                return True
            else:
                logger.error(f"  ❌ Instagram posting failed")
                
                # Retry logic
                if retry_count < self.retry_attempts - 1:
                    wait_time = self.retry_delay * (retry_count + 1)
                    logger.info(f"  🔄 Retrying in {wait_time} minutes...")
                    time.sleep(wait_time * 60)
                    return self.post_to_instagram(post_data, retry_count + 1)
                else:
                    self.today_stats['by_platform']['instagram']['failed'] += 1
                    self.today_stats['posts_failed'] += 1
                    self._save_today_stats()
                    self._send_notification(f"❌ FAILED: Instagram posting failed for {post_id} after {self.retry_attempts} attempts", "error")
                    return False
                
        except Exception as e:
            logger.error(f"  ❌ Instagram error: {e}")
            
            # Retry logic
            if retry_count < self.retry_attempts - 1:
                wait_time = self.retry_delay * (retry_count + 1)
                logger.info(f"  🔄 Retrying in {wait_time} minutes...")
                time.sleep(wait_time * 60)
                return self.post_to_instagram(post_data, retry_count + 1)
            else:
                self.today_stats['by_platform']['instagram']['failed'] += 1
                self.today_stats['posts_failed'] += 1
                self._save_today_stats()
                self._send_notification(f"❌ ERROR: Instagram error for {post_id}: {str(e)}", "error")
                return False
    
    def post_to_facebook(self, post_data: Dict[str, Any]) -> bool:
        """Post to Facebook"""
        post_id = post_data['post_id']
        logger.info(f"📘 Posting {post_id} to Facebook...")
        
        try:
            # CRITICAL: Check if already posted BEFORE attempting
            if self.post_manager.is_posted(post_id, "facebook"):
                logger.info(f"  Already posted to Facebook - skipping to prevent duplicate")
                return True
            
            # Use file lock to prevent race conditions with scheduler daemon (cross-process)
            fb_lock = FileLock(Path(".facebook_post.lock"), timeout_sec=30)
            if not fb_lock.acquire():
                logger.warning(f"  Could not acquire Facebook lock for post {post_id}, skipping (another process is posting)")
                return False
            
            try:
                # Double-check right before posting (race condition prevention)
                if self.post_manager.is_posted(post_id, "facebook"):
                    logger.info(f"  Already posted to Facebook (race condition prevented)")
                return True
            
            poster = FacebookPoster()
            video_path = Path(post_data['video_path'])
            caption = post_data['caption']
            hashtags = post_data.get('hashtags', [])
            
            success = poster.post_video(video_path, caption, hashtags)
            
            if success:
                    # Mark as posted ONLY if successful
                self.post_manager.mark_as_posted(post_id, "facebook")
                logger.info(f"  ✅ Posted to Facebook!")
                return True
            else:
                logger.error(f"  ❌ Facebook posting failed")
                return False
            finally:
                fb_lock.release()
                
        except Exception as e:
            logger.error(f"  ❌ Facebook error: {e}")
            return False
    
    def post_to_youtube(self, post_data: Dict[str, Any]) -> bool:
        """Post to YouTube"""
        post_id = post_data['post_id']
        logger.info(f"📺 Posting {post_id} to YouTube...")
        
        try:
            # Check if already posted
            if self.post_manager.is_posted(post_id, "youtube"):
                logger.info(f"  Already posted to YouTube")
                return True
            
            uploader = YouTubeUploader()
            uploader.authenticate()
            
            video_path = Path(post_data['video_path'])
            metadata = post_data['metadata']
            
            # Build title and description
            # Use truncate_title to ensure max 60 characters
            original_title = metadata.get('original_title', '')
            title = uploader.truncate_title(original_title, " | TripAvail")
            caption = post_data['caption']
            hashtags = post_data.get('hashtags', [])
            
            description = f"{caption}\n\n#Shorts\n\n" + " ".join(hashtags[:10])
            tags = [t.replace('#','') for t in hashtags[:10]] + ['TripAvail','Travel','Shorts']
            
            # Get thumbnail if available
            thumbnail_path = None
            if 'thumbnails' in metadata and 'vertical' in metadata['thumbnails']:
                thumbnail_path = Path(metadata['thumbnails']['vertical'])
            
            video_id = uploader.upload_video(
                video_path,
                title=title,
                description=description,
                tags=tags,
                thumbnail_path=thumbnail_path
            )
            
            if video_id:
                post_url = f"https://youtube.com/shorts/{video_id}"
                self.post_manager.mark_as_posted(post_id, "youtube", post_url)
                logger.info(f"  ✅ Posted to YouTube: {post_url}")
                return True
            else:
                logger.error(f"  ❌ YouTube upload failed")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ YouTube error: {e}")
            return False
    
    def _execute_single_post(self, post_data: Dict[str, Any], platform: str):
        """
        Execute a single scheduled post
        
        Args:
            post_data: Post data dictionary
            platform: Platform to post to
        """
        post_id = post_data['post_id']
        
        logger.info(f"\n🚀 Executing scheduled post: {post_id} → {platform}")
        
        # Check if already posted
        if self.post_manager.is_posted(post_id, platform):
            logger.info(f"   Already posted, skipping")
            return schedule.CancelJob  # Remove this scheduled job
        
        # Post to platform
        success = False
        
        if platform == "instagram":
            success = self.post_to_instagram(post_data)
        elif platform == "facebook":
            success = self.post_to_facebook(post_data)
        elif platform == "youtube":
            success = self.post_to_youtube(post_data)
        
        if success:
            logger.info(f"   ✅ Posted successfully!")
        else:
            logger.error(f"   ❌ Posting failed")
        
        # Remove this one-time job
        return schedule.CancelJob
    
    def post_at_time(self, time_str: str):
        """
        Scheduled job: Schedule posts for this peak time
        Spacing only applied when multiple posts go to SAME platform
        
        Args:
            time_str: Time string (e.g., "14:00")
        """
        logger.info("\n" + "="*70)
        logger.info(f"🕐 SCHEDULING POSTS FOR {time_str} UTC")
        logger.info("="*70)
        
        # Determine which platforms post at this time
        platforms_to_post = []
        for platform, times in self.platform_schedule.items():
            if time_str in times:
                platforms_to_post.append(platform)
        
        if not platforms_to_post:
            logger.info(f"No platforms scheduled for {time_str}")
            return
        
        logger.info(f"Platforms: {', '.join(platforms_to_post)}")
        
        # Get top posts
        top_posts = self.get_top_posts(count=10)
        
        if not top_posts:
            logger.warning("No posts available to schedule")
            return
        
        # Organize posts by platform
        # Key: platform name, Value: list of posts for that platform
        platform_posts = {platform: [] for platform in platforms_to_post}
        
        # Collect ALL available posts for each platform
        for platform in platforms_to_post:
            for post in top_posts:
                post_id = post['post_id']
                
                if self.post_manager.is_posted(post_id, platform):
                    continue
                
                # Add this post as available for this platform
                platform_posts[platform].append(post)
        
        # Now schedule posts with spacing ONLY if multiple posts per platform
        total_scheduled = 0
        
        for platform, posts in platform_posts.items():
            if not posts:
                logger.info(f"  {platform}: No unposted content available")
                continue
            
            if len(posts) == 1:
                # Only 1 post for this platform - post immediately at base time
                logger.info(f"  {platform}: 1 post available")
                self._schedule_single_post(posts[0], platform, time_str)
                total_scheduled += 1
            else:
                # Multiple posts for same platform - use spacing!
                logger.info(f"  {platform}: {len(posts)} posts available - applying spacing")
                self._schedule_multiple_posts_with_spacing(posts, platform, time_str)
                total_scheduled += len(posts)
        
        logger.info(f"\n✅ Scheduled {total_scheduled} posts total")
        logger.info("="*70 + "\n")
    
    def _schedule_single_post(self, post_data: Dict[str, Any], platform: str, time_str: str):
        """
        Schedule a single post (no spacing needed)
        
        Args:
            post_data: Post data
            platform: Platform name
            time_str: Time to post (e.g., "18:00")
        """
        post_id = post_data['post_id']
        logger.info(f"     {time_str} → Post {post_id} to {platform.upper()}")
        
        # Schedule immediately at base time
        schedule.every().day.at(time_str).do(
            self._execute_single_post,
            post_data=post_data,
            platform=platform
        ).tag(f'scheduled_{post_id}_{platform}')
    
    def _schedule_multiple_posts_with_spacing(self, posts: List[Dict[str, Any]], platform: str, base_time: str):
        """
        Schedule multiple posts to SAME platform with 30-40 min spacing
        
        Args:
            posts: List of posts to schedule
            platform: Platform name
            base_time: Base time string (e.g., "18:00")
        """
        import random
        from datetime import datetime, timedelta
        
        logger.info(f"     📅 Spacing timeline for {platform.upper()}:")
        
        cumulative_delay = 0
        
        for i, post_data in enumerate(posts[:5]):  # Max 5 posts per platform per time slot
            post_id = post_data['post_id']
            
            # Calculate posting time
            if i == 0:
                delay_minutes = 0  # First post at base time
            else:
                delay_minutes = random.randint(30, 40)  # Random 30-40 min spacing
                cumulative_delay += delay_minutes
            
            # Parse base time and add delay
            base_dt = datetime.strptime(base_time, "%H:%M")
            post_time = base_dt + timedelta(minutes=cumulative_delay)
            post_time_str = post_time.strftime("%H:%M")
            
            logger.info(f"        {post_time_str} → Post {post_id} (+{cumulative_delay}m)")
            
            # Schedule the job
            schedule.every().day.at(post_time_str).do(
                self._execute_single_post,
                post_data=post_data,
                platform=platform
            ).tag(f'scheduled_{post_id}_{platform}')
    
    def _load_today_stats(self):
        """Load today's statistics"""
        if self.daily_stats_file.exists():
            try:
                with open(self.daily_stats_file, 'r') as f:
                    stats = json.load(f)
                
                # Check if it's today's stats
                if stats.get('date') == datetime.now().strftime('%Y-%m-%d'):
                    self.today_stats = stats
                    logger.info(f"Loaded today's stats: {stats['posts_successful']}/{stats['posts_attempted']} successful")
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
    
    def _save_today_stats(self):
        """Save today's statistics"""
        try:
            with open(self.daily_stats_file, 'w') as f:
                json.dump(self.today_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def _track_post_performance(self, post_id: str, platform: str, posted_time: datetime):
        """Track post performance for analytics"""
        try:
            # Load existing performance data
            if self.performance_file.exists():
                with open(self.performance_file, 'r') as f:
                    performance = json.load(f)
            else:
                performance = {'posts': []}
            
            # Add this post
            performance['posts'].append({
                'post_id': post_id,
                'platform': platform,
                'posted_at': posted_time.isoformat(),
                'time_slot': posted_time.strftime('%H:%M'),
                'day_of_week': posted_time.strftime('%A'),
                'date': posted_time.strftime('%Y-%m-%d')
            })
            
            # Save
            with open(self.performance_file, 'w') as f:
                json.dump(performance, f, indent=2)
            
            logger.debug(f"Tracked performance: {post_id} on {platform}")
            
        except Exception as e:
            logger.error(f"Error tracking performance: {e}")
    
    def _send_notification(self, message: str, level: str = "info"):
        """Send email notification"""
        try:
            # Log the notification
            if level == "success":
                logger.info(f"📧 {message}")
            elif level == "error":
                logger.error(f"📧 {message}")
            else:
                logger.info(f"📧 {message}")
            
            # Send email notification
            self._send_email(message, level)
            
        except Exception as e:
            logger.error(f"Notification error: {e}")
    
    def _send_email(self, message: str, level: str = "info"):
        """Send email via SMTP using config settings"""
        try:
            # Always log
            logger.info(f"📧 Email notification: {message}")
            
            # Build common content
            subject = f"TripAvail - {level.upper()}"
            body = f"""
TripAvail Notification
            
            {message}
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
            """
            
            receiver_email = self.notification_email

            # Gmail API path (HTTPS, no SMTP port needed)
            if getattr(settings, 'EMAIL_METHOD', 'smtp') == 'gmail_api':
                notifier = GmailNotifier(
                    Path(getattr(settings, 'GMAIL_CLIENT_SECRET_FILE', 'client_secret.json')),
                    Path(getattr(settings, 'GMAIL_TOKEN_FILE', 'gmail_token.json')),
                )
                sender_email = getattr(settings, 'SMTP_USER', 'tripavail92@gmail.com')
                msg_id = notifier.send_email(sender_email, receiver_email, subject, body)
                logger.info(f"📧 Gmail API sent to {receiver_email} (id={msg_id})")
                return

            # SMTP path
            if not getattr(settings, 'EMAIL_ENABLED', False):
                return

            sender_email = getattr(settings, 'SMTP_USER', 'tripavail92@gmail.com')
            password = getattr(settings, 'SMTP_PASSWORD', '')
            host = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
            port = int(getattr(settings, 'SMTP_PORT', 465))
            if not password:
                logger.warning("EMAIL_ENABLED is true but SMTP_PASSWORD is empty; skipping SMTP send")
                return

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(sender_email, password)
                server.send_message(msg)
            logger.info(f"📧 SMTP sent to {receiver_email}")
            
        except Exception as e:
            logger.error(f"Email error: {e}")
    
    def generate_daily_summary(self):
        """Generate and send daily summary"""
        try:
            stats = self.today_stats
            
            summary = f"""
            ═══════════════════════════════════════════════════════════
            📊 DAILY SUMMARY - {stats['date']}
            ═══════════════════════════════════════════════════════════
            
            Overall Performance:
            • Total Posts Attempted: {stats['posts_attempted']}
            • Successful: {stats['posts_successful']} ✅
            • Failed: {stats['posts_failed']} ❌
            • Success Rate: {(stats['posts_successful']/stats['posts_attempted']*100) if stats['posts_attempted'] > 0 else 0:.1f}%
            
            By Platform:
            
            Instagram:
            • Attempted: {stats['by_platform']['instagram']['attempted']}
            • Successful: {stats['by_platform']['instagram']['successful']} ✅
            • Failed: {stats['by_platform']['instagram']['failed']} ❌
            
            Facebook:
            • Attempted: {stats['by_platform']['facebook']['attempted']}
            • Successful: {stats['by_platform']['facebook']['successful']} ✅
            • Failed: {stats['by_platform']['facebook']['failed']} ❌
            
            YouTube:
            • Attempted: {stats['by_platform']['youtube']['attempted']}
            • Successful: {stats['by_platform']['youtube']['successful']} ✅
            • Failed: {stats['by_platform']['youtube']['failed']} ❌
            
            ═══════════════════════════════════════════════════════════
            """
            
            logger.info(summary)
            
            # Send email notification
            self._send_notification(f"Daily Summary: {stats['posts_successful']}/{stats['posts_attempted']} posts successful", "info")
            
            # Save summary to file
            summary_file = self.data_dir / f"daily_summary_{stats['date']}.txt"
            with open(summary_file, 'w') as f:
                f.write(summary)
            
            logger.info(f"Daily summary saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights from historical data"""
        try:
            if not self.performance_file.exists():
                return {'message': 'No performance data yet'}
            
            with open(self.performance_file, 'r') as f:
                performance = json.load(f)
            
            posts = performance.get('posts', [])
            
            if not posts:
                return {'message': 'No posts tracked yet'}
            
            # Analyze by time slot
            time_slots = {}
            platforms = {}
            days = {}
            
            for post in posts:
                time_slot = post.get('time_slot', 'Unknown')
                platform = post.get('platform', 'Unknown')
                day = post.get('day_of_week', 'Unknown')
                
                time_slots[time_slot] = time_slots.get(time_slot, 0) + 1
                platforms[platform] = platforms.get(platform, 0) + 1
                days[day] = days.get(day, 0) + 1
            
            insights = {
                'total_posts_tracked': len(posts),
                'most_active_time': max(time_slots, key=time_slots.get) if time_slots else 'N/A',
                'most_used_platform': max(platforms, key=platforms.get) if platforms else 'N/A',
                'most_active_day': max(days, key=days.get) if days else 'N/A',
                'by_time_slot': time_slots,
                'by_platform': platforms,
                'by_day': days
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return {'error': str(e)}
    
    def show_schedule(self):
        """Display the posting schedule"""
        logger.info("\n" + "="*70)
        logger.info("SMART SCHEDULER - Posting Schedule")
        logger.info("="*70)
        logger.info("\nGlobal Peak Times (UTC):")
        for time_str in self.peak_times:
            logger.info(f"  {time_str}")
        
        logger.info("\nPlatform Schedule:")
        for platform, times in self.platform_schedule.items():
            logger.info(f"\n  {platform.upper()}:")
            for time_str in times:
                logger.info(f"    - {time_str} UTC")
        
        logger.info("\nDaily Totals:")
        logger.info(f"  Instagram: {len(self.platform_schedule['instagram'])} posts/day")
        logger.info(f"  Facebook: {len(self.platform_schedule['facebook'])} posts/day")
        logger.info(f"  YouTube: {len(self.platform_schedule['youtube'])} posts/day")
        logger.info(f"  TOTAL: {sum(len(t) for t in self.platform_schedule.values())} posts/day across all platforms")
        logger.info("="*70 + "\n")
    
    def setup_schedule(self):
        """Setup the schedule jobs"""
        logger.info("Setting up schedule...")
        
        # Schedule posts at peak times
        for time_str in self.peak_times:
            schedule.every().day.at(time_str).do(self.post_at_time, time_str)
            logger.info(f"  ✓ Scheduled posting at {time_str} UTC")
        
        # Schedule daily summary at 23:59 UTC
        schedule.every().day.at("23:59").do(self.generate_daily_summary)
        logger.info(f"  ✓ Scheduled daily summary at 23:59 UTC")
        
        logger.info(f"\n✅ Schedule configured with {len(self.peak_times)} daily posting times + daily summary")
        
        self.show_schedule()
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("\n" + "="*70)
        logger.info("🚀 SMART SCHEDULER STARTED")
        logger.info("="*70)
        logger.info("Posts top 10 ranked videos at global peak times")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*70 + "\n")
        
        self.setup_schedule()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Scheduler stopped by user")
    
    def post_now(self, platforms: List[str] = None):
        """
        Post immediately to specified platforms (for testing)
        
        Args:
            platforms: List of platforms ['instagram', 'facebook', 'youtube']
                      If None, posts to all platforms
        """
        if platforms is None:
            platforms = ['instagram', 'facebook', 'youtube']
        
        logger.info("\n" + "="*70)
        logger.info("📤 IMMEDIATE POSTING (Test Mode)")
        logger.info("="*70)
        
        top_posts = self.get_top_posts(count=10)
        
        if not top_posts:
            logger.error("No posts available")
            return
        
        for platform in platforms:
            logger.info(f"\n--- Posting to {platform.upper()} ---")
            
            # Get next unposted post
            for post in top_posts:
                post_id = post['post_id']
                
                if self.post_manager.is_posted(post_id, platform):
                    continue
                
                # Post
                if platform == "instagram":
                    self.post_to_instagram(post)
                elif platform == "facebook":
                    self.post_to_facebook(post)
                elif platform == "youtube":
                    self.post_to_youtube(post)
                
                break  # One post per platform
                
            time.sleep(5)
        
        logger.info("\n" + "="*70)
        logger.info("✅ Immediate posting complete!")
        logger.info("="*70 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Scheduler - Post top 10 videos at peak times')
    parser.add_argument('--run', action='store_true', help='Run the scheduler loop')
    parser.add_argument('--show-top', action='store_true', help='Show top 10 ranked posts')
    parser.add_argument('--post-now', action='store_true', help='Post immediately (test mode)')
    parser.add_argument('--schedule', action='store_true', help='Show posting schedule')
    parser.add_argument('--stats', action='store_true', help='Show today\'s statistics')
    parser.add_argument('--summary', action='store_true', help='Generate daily summary now')
    parser.add_argument('--insights', action='store_true', help='Show performance insights')
    
    args = parser.parse_args()
    
    scheduler = SmartScheduler()
    
    if args.show_top:
        # Show top posts
        top_posts = scheduler.get_top_posts(count=10)
        print("\n" + "="*70)
        print("TOP 10 RANKED POSTS")
        print("="*70)
        for i, post in enumerate(top_posts, 1):
            print(f"\n#{i} - Post {post['post_id']}")
            print(f"  Rank Score: {post['rank_score']}/100")
            print(f"  AI Score: {post['ai_score']}/10")
            print(f"  Title: {post['title']}")
            print(f"  Region: {post['region']}")
        print("="*70 + "\n")
    
    elif args.schedule:
        # Show schedule
        scheduler.show_schedule()
    
    elif args.stats:
        # Show today's stats
        stats = scheduler.today_stats
        print("\n" + "="*70)
        print(f"📊 TODAY'S STATISTICS - {stats['date']}")
        print("="*70)
        print(f"\nOverall: {stats['posts_successful']}/{stats['posts_attempted']} successful")
        print(f"Success Rate: {(stats['posts_successful']/stats['posts_attempted']*100) if stats['posts_attempted'] > 0 else 0:.1f}%")
        print("\nBy Platform:")
        for platform, data in stats['by_platform'].items():
            print(f"  {platform.capitalize()}: {data['successful']}/{data['attempted']} successful")
        print("="*70 + "\n")
    
    elif args.summary:
        # Generate daily summary
        scheduler.generate_daily_summary()
    
    elif args.insights:
        # Show performance insights
        insights = scheduler.get_performance_insights()
        print("\n" + "="*70)
        print("📈 PERFORMANCE INSIGHTS")
        print("="*70)
        if 'error' in insights:
            print(f"\nError: {insights['error']}")
        elif 'message' in insights:
            print(f"\n{insights['message']}")
        else:
            print(f"\nTotal Posts Tracked: {insights['total_posts_tracked']}")
            print(f"Most Active Time: {insights['most_active_time']}")
            print(f"Most Used Platform: {insights['most_used_platform']}")
            print(f"Most Active Day: {insights['most_active_day']}")
            print("\nPosts by Time Slot:")
            for time, count in insights['by_time_slot'].items():
                print(f"  {time}: {count} posts")
            print("\nPosts by Platform:")
            for platform, count in insights['by_platform'].items():
                print(f"  {platform}: {count} posts")
            print("\nPosts by Day:")
            for day, count in insights['by_day'].items():
                print(f"  {day}: {count} posts")
        print("="*70 + "\n")
    
    elif args.post_now:
        # Post immediately
        scheduler.post_now()
    
    elif args.run:
        # Run scheduler
        scheduler.run_scheduler()
    
    else:
        # Default: show help
        parser.print_help()
        print("\nExamples:")
        print("  python smart_scheduler.py --show-top    # View top 10 posts")
        print("  python smart_scheduler.py --schedule    # View posting schedule")
        print("  python smart_scheduler.py --stats       # View today's statistics")
        print("  python smart_scheduler.py --summary     # Generate daily summary")
        print("  python smart_scheduler.py --insights    # View performance insights")
        print("  python smart_scheduler.py --post-now    # Post immediately (test)")
        print("  python smart_scheduler.py --run         # Run scheduler loop")


if __name__ == "__main__":
    main()


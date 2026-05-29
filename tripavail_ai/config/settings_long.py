# TripAvail AI Long Video Configuration File
# Separate configuration for long-format videos (3-4 minutes, 16:9 horizontal)
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ========================================
# Long Video Settings
# ========================================
LONG_VIDEO_ENABLED = os.getenv("LONG_VIDEO_ENABLED", "true").lower() == "true"
LONG_VIDEO_DURATION_MIN = 180  # 3 minutes (180 seconds)
LONG_VIDEO_DURATION_MAX = 240  # 4 minutes (240 seconds)
LONG_VIDEO_IMAGE_COUNT_MIN = 60  # Minimum images required
LONG_VIDEO_IMAGE_COUNT_MAX = 85  # Maximum images target
LONG_VIDEO_GENERATION_TIME = os.getenv("LONG_VIDEO_GENERATION_TIME", "20:00")  # UTC

# Video Format
LONG_VIDEO_FORMAT = "16:9"  # Horizontal format
LONG_VIDEO_RESOLUTION = (1920, 1080)  # Full HD
LONG_VIDEO_FPS = 30  # 30 FPS
LONG_VIDEO_ASPECT_RATIO = 1.78  # 16:9 aspect ratio

# Image Settings
LONG_VIDEO_IMAGE_ORIENTATION = "horizontal"  # Horizontal/landscape only
LONG_VIDEO_IMAGE_ASPECT_RATIO_MIN = 1.6  # Minimum aspect ratio
LONG_VIDEO_IMAGE_ASPECT_RATIO_MAX = 1.8  # Maximum aspect ratio
LONG_VIDEO_IMAGE_MIN_RESOLUTION = (1920, 1080)  # Minimum resolution

# Image Duration Settings
LONG_VIDEO_IMAGE_DURATION_HERO = 5.0  # Hero shots (seconds)
LONG_VIDEO_IMAGE_DURATION_STANDARD = 3.5  # Standard shots (seconds)
LONG_VIDEO_IMAGE_DURATION_QUICK = 2.5  # Quick transitions (seconds)
LONG_VIDEO_FADE_DURATION = 0.8  # Crossfade duration (seconds)

# ========================================
# Trend Detection Settings
# ========================================
TRENDING_DETECTION_ENABLED = True
TRENDING_DETECTION_INTERVAL_HOURS = 12  # Every 12 hours (not 4 hours)
TRENDING_DETECTION_MIN_SCORE = 7.0  # Minimum trend score
TRENDING_DETECTION_TIME = os.getenv("TRENDING_DETECTION_TIME", "08:00,20:00")  # UTC times (comma-separated)

# ========================================
# Image Search API Keys (Long Videos Only)
# ========================================

# Pixabay API Key (HIGHEST PRIORITY - Long Videos Only)
PIXABAY_API_KEY_LONG = os.getenv("PIXABAY_API_KEY_LONG", "53072265-2fee715e77bd6709a2ad84b3f")
# NOTE: Pixabay is the highest priority image source for long videos

# Pexels API Key (LONG VIDEOS ONLY - Separate from short videos)
PEXELS_API_KEY_LONG = os.getenv("PEXELS_API_KEY_LONG", "WaaZwYKSLwrBEnvVNXcWLBvWZS48auiNghb34tQE2sufUGa5GQ9bpg4X")
# NOTE: This key is ONLY used for long videos. Short videos use the regular PEXELS_API_KEY.

# Unsplash API Credentials (Long Videos)
UNSPLASH_APP_ID_LONG = os.getenv("UNSPLASH_APP_ID_LONG", "829529")
UNSPLASH_ACCESS_KEY_LONG = os.getenv("UNSPLASH_ACCESS_KEY_LONG", "OSlM5giq8LVThEDf1HcTsLvo59tZl0BywfUpXxkcksI")
UNSPLASH_SECRET_KEY_LONG = os.getenv("UNSPLASH_SECRET_KEY_LONG", "4_T4Wem3tnqyE6DIRMZnk2pKxcHV-0mc5OvIiQgyCRI")
# NOTE: Unsplash uses Access Key for API requests (not App ID)

# Shutterstock API Key (Long Videos - if different from short videos)
SHUTTERSTOCK_ACCESS_TOKEN_LONG = os.getenv("SHUTTERSTOCK_ACCESS_TOKEN_LONG", "")
SHUTTERSTOCK_CLIENT_ID_LONG = os.getenv("SHUTTERSTOCK_CLIENT_ID_LONG", "")
SHUTTERSTOCK_CLIENT_SECRET_LONG = os.getenv("SHUTTERSTOCK_CLIENT_SECRET_LONG", "")
# If not set, falls back to regular SHUTTERSTOCK_ACCESS_TOKEN from settings.py

# ========================================
# Image Search Distribution Strategy
# ========================================
# Distribute searches across services to avoid duplicates
IMAGE_SEARCH_DISTRIBUTION = {
    "attractions": "pixabay",      # Pixabay for attractions (highest priority)
    "activities": "pixabay",      # Pixabay for activities (highest priority)
    "food_culture": "pixabay",    # Pixabay for food & culture (highest priority)
    "local_life": "pixabay",      # Pixabay for local life (highest priority)
    "scenic_views": "pixabay",    # Pixabay for scenic views (highest priority)
}

# Service Priority (for fallback) - Pixabay has highest priority
IMAGE_SEARCH_PRIORITY = ["pixabay", "pexels", "unsplash", "shutterstock"]

# Image Search Settings
IMAGE_SEARCH_ORIENTATION = "horizontal"  # Horizontal/landscape only
IMAGE_SEARCH_PER_PAGE = 20  # Images per API request
IMAGE_SEARCH_MAX_PAGES = 5  # Maximum pages to search
IMAGE_SEARCH_RATE_LIMIT_DELAY = 10  # Seconds between searches

# ========================================
# Image Caching Settings
# ========================================
IMAGE_CACHE_ENABLED = True
IMAGE_CACHE_EXPIRY_DAYS = 30  # Cache expires after 30 days
IMAGE_CACHE_BASE_DIR = "data/long_videos/image_cache"
IMAGE_CACHE_CLEANUP_ENABLED = True
IMAGE_CACHE_CLEANUP_INTERVAL_DAYS = 7  # Cleanup every 7 days

# ========================================
# Voiceover Settings (ElevenLabs)
# ========================================
ELEVENLABS_API_KEY_LONG = os.getenv("ELEVENLABS_API_KEY_LONG", "e810fca85dcb11ced48b326eddc86415f0c0ef992a587c8e5bcd86c3425b4dc9")
ELEVENLABS_VOICE_ID_LONG = os.getenv("ELEVENLABS_VOICE_ID_LONG", "lxYfHSkYm1EzQzGhdbfc")  # Nova voice
ELEVENLABS_MODEL_LONG = "eleven_turbo_v2_5"  # Premium model

# Voiceover Quality Settings
ELEVENLABS_TTS_LONG = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.4,
    "use_speaker_boost": True,
}

# Voice Selection (consistent voice for all long videos)
ELEVENLABS_VOICE_CONSISTENT = True  # Use same voice for all videos
ELEVENLABS_VOICE_NAME_LONG = "Jessica Anne Bogart - Narration"  # Voice name (Nova - Professional narration voice)

# ========================================
# Script Generation Settings
# ========================================
SCRIPT_GENERATION_ENABLED = True
SCRIPT_WORD_COUNT_MIN = 300  # Minimum words for 3-minute video
SCRIPT_WORD_COUNT_MAX = 400  # Maximum words for 4-minute video
SCRIPT_STRUCTURE = {
    "introduction": 0.15,  # 15% of script
    "main_content": 0.70,  # 70% of script
    "conclusion": 0.15,    # 15% of script
}

# ========================================
# Caption Settings
# ========================================
CAPTION_GENERATION_ENABLED = True
CAPTION_STYLE = "professional"  # Professional, readable style
CAPTION_POSITION = "bottom_center"  # Bottom center position
CAPTION_FONT_SIZE = 48  # Font size
CAPTION_COLOR = "white"  # Text color
CAPTION_OUTLINE_COLOR = "black"  # Outline color
CAPTION_OUTLINE_WIDTH = 2  # Outline width

# ========================================
# Hook Generation Settings
# ========================================
HOOK_GENERATION_ENABLED = True
HOOK_MAX_LENGTH = 70  # Maximum characters
HOOK_MIN_LENGTH = 60  # Minimum characters
HOOK_WORD_BOUNDARY_TRUNCATION = True  # Truncate at word boundaries
HOOK_SEO_OPTIMIZED = True  # Optimize for YouTube SEO

# ========================================
# Thumbnail Settings
# ========================================
THUMBNAIL_GENERATION_ENABLED = True
THUMBNAIL_FORMAT = "16:9"  # Horizontal format
THUMBNAIL_RESOLUTION = (1920, 1080)  # Full HD
THUMBNAIL_INCLUDE_CHARACTER = True  # Include consistent character
THUMBNAIL_CHARACTER_DESCRIPTION = ""  # Character description (will be set)
THUMBNAIL_CHARACTER_REFERENCE = ""  # Character reference image path (will be set)

# ========================================
# Video Generation Settings
# ========================================
VIDEO_GENERATION_ENABLED = True
VIDEO_CODEC = "libx264"  # H.264 codec
VIDEO_PRESET = "medium"  # Encoding preset (medium for faster processing)
VIDEO_CRF = 20  # Quality setting (18-23, lower = higher quality)
VIDEO_PIX_FMT = "yuv420p"  # Pixel format

# Video Effects
VIDEO_KEN_BURNS_ENABLED = True  # Ken Burns effect
VIDEO_CROSSFADE_ENABLED = True  # Crossfade transitions
VIDEO_TRANSITION_DURATION = 0.8  # Transition duration (seconds)

# ========================================
# Audio Mixing Settings
# ========================================
AUDIO_MIXING_ENABLED = True
AUDIO_VOICEOVER_VOLUME = 1.0  # Voiceover volume (0.0-1.0)
AUDIO_MUSIC_VOLUME = 0.3  # Background music volume (0.0-1.0)
AUDIO_MUSIC_FADE_IN = 1.0  # Music fade-in duration (seconds)
AUDIO_MUSIC_FADE_OUT = 2.0  # Music fade-out duration (seconds)
AUDIO_CODEC = "aac"  # Audio codec
AUDIO_BITRATE = "320k"  # Audio bitrate

# ========================================
# YouTube Upload Settings
# ========================================
YOUTUBE_UPLOAD_ENABLED = True
YOUTUBE_CATEGORY = "Travel & Events"  # Video category
YOUTUBE_PRIVACY = "public"  # Privacy setting (public, unlisted, private)
YOUTUBE_AUTO_PUBLISH = False  # Auto-publish or schedule
YOUTUBE_SCHEDULE_DELAY_HOURS = 24  # Delay before publishing (hours)

# ========================================
# Error Handling & Retry Settings
# ========================================
ERROR_RETRY_ENABLED = True
ERROR_RETRY_ATTEMPTS = 3  # Maximum retry attempts
ERROR_RETRY_DELAY_SECONDS = 60  # Delay between retries (seconds)
ERROR_WAIT_FOR_NEXT_DAY = True  # Wait for next day if all retries fail
ERROR_NO_AI_FALLBACK = True  # Never use AI generation as fallback

# ========================================
# Resource Management Settings
# ========================================
RESOURCE_CHECK_ENABLED = True
RESOURCE_CPU_THRESHOLD = 0.70  # Maximum CPU usage (0.0-1.0)
RESOURCE_MEMORY_THRESHOLD = 0.80  # Maximum memory usage (0.0-1.0)
RESOURCE_DISK_SPACE_MIN_GB = 5  # Minimum disk space required (GB)
RESOURCE_LOCK_FILE = "data/long_videos/.generation_lock"  # Lock file path

# ========================================
# Logging Settings
# ========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/long_video_generation.log"
LOG_ROTATION = "1 day"
LOG_RETENTION = "30 days"

# ========================================
# Directory Paths
# ========================================
DATA_DIR = "data"
LONG_VIDEOS_DIR = f"{DATA_DIR}/long_videos"
DESTINATIONS_DIR = f"{LONG_VIDEOS_DIR}/destinations"
IMAGES_DIR = f"{LONG_VIDEOS_DIR}/images"
SCRIPTS_DIR = f"{LONG_VIDEOS_DIR}/scripts"
VOICEOVERS_DIR = f"{LONG_VIDEOS_DIR}/voiceovers"
VIDEOS_DIR = f"{LONG_VIDEOS_DIR}/videos"
THUMBNAILS_DIR = f"{LONG_VIDEOS_DIR}/thumbnails"
CACHE_DIR = f"{LONG_VIDEOS_DIR}/image_cache"
LOGS_DIR = "logs"

# ========================================
# Validation
# ========================================
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check required API keys
    if not PIXABAY_API_KEY_LONG:
        errors.append("PIXABAY_API_KEY_LONG is required for long videos")
    
    if not PEXELS_API_KEY_LONG:
        errors.append("PEXELS_API_KEY_LONG is required for long videos")
    
    if not UNSPLASH_ACCESS_KEY_LONG:
        errors.append("UNSPLASH_ACCESS_KEY_LONG is required for long videos")
    
    if not ELEVENLABS_API_KEY_LONG:
        errors.append("ELEVENLABS_API_KEY_LONG is required for long videos")
    
    # Check directory paths
    import os
    for dir_path in [DATA_DIR, LONG_VIDEOS_DIR, LOGS_DIR]:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                errors.append(f"Failed to create directory {dir_path}: {e}")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
    
    return True

# Validate configuration on import
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        import logging
        logging.warning(f"Configuration validation warning: {e}")


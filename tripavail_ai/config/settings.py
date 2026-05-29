# TripAvail AI Configuration File
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Application Settings
APP_NAME = "TripAvail AI"
APP_VERSION = "1.0.0"
DEBUG = False

# API Settings
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 2000
OPENAI_TEMPERATURE = 0.7

# Shutterstock (Stock images - third priority fallback in Hybrid image pipeline)
# Prefer setting SHUTTERSTOCK_ACCESS_TOKEN via environment for OAuth2 Bearer auth
SHUTTERSTOCK_ACCESS_TOKEN = os.getenv("SHUTTERSTOCK_ACCESS_TOKEN", "")
# Optional (not required if ACCESS_TOKEN provided). Keep empty unless you implement token exchange flow.
SHUTTERSTOCK_CLIENT_ID = os.getenv("SHUTTERSTOCK_CLIENT_ID", "")
SHUTTERSTOCK_CLIENT_SECRET = os.getenv("SHUTTERSTOCK_CLIENT_SECRET", "")

# News Settings
NEWS_LIMIT = 50
NEWS_LANGUAGE = "en"
NEWS_COUNTRY = "US"

# Social Media Settings - Facebook
FACEBOOK_API_VERSION = "v18.0"
FACEBOOK_GRAPH_TOKEN = os.getenv("FACEBOOK_GRAPH_TOKEN", "")

# Instagram (requires IG Business account connected to your Facebook Page)
# Set this to your Instagram Business Account ID (numeric). You can also set ENV INSTAGRAM_USER_ID.
INSTAGRAM_USER_ID = "17841476246421683"

# Social Media Settings - YouTube
YOUTUBE_API_VERSION = "v3"
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
YOUTUBE_EMAIL = "tripavail92@gmail.com"
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube"
]
# YouTube title max length (configurable via environment variable YOUTUBE_TITLE_MAX_LENGTH, default: 70)
# The truncation function will try to find word boundaries between 60-70 chars to avoid cutting words
YOUTUBE_TITLE_MAX_LENGTH = int(os.getenv("YOUTUBE_TITLE_MAX_LENGTH", "70"))

# File Paths
DATA_DIR = "data"
LOGS_DIR = "logs"
CONFIG_DIR = "config"

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
LOG_ROTATION = "1 day"
LOG_RETENTION = "30 days"

# Rate Limiting
API_RATE_LIMIT = 100  # requests per minute
REQUEST_TIMEOUT = 30  # seconds

# Data Processing
BATCH_SIZE = 10
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Auto-deletion retention window (in hours). Set via env AUTO_DELETION_HOURS, default 24
AUTO_DELETION_HOURS = int(os.getenv("AUTO_DELETION_HOURS", "24"))

# ========================================
# Stability AI (9:16 Thumbnail Generation)
# ========================================
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")

# ========================================
# ElevenLabs (PREMIUM Creator Plan)
# ========================================
# Features: Turbo v2.5 (3x quality), Sound Effects, Premium Voices
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# TTS Model: eleven_turbo_v2_5 (PREMIUM - 3x quality, 2x speed)
ELEVENLABS_MODEL = "eleven_turbo_v2_5"

# Default Premium Voice (Default for all unclassified content)
# Get more voices: https://elevenlabs.io/voice-library (filter: Turbo v2.5)
ELEVENLABS_VOICE_ID = "kPzsL2i3teMYv0FxEYQ6"  # Default Voice

# Premium Turbo v2.5 Settings (Optimized for Travel Content)
ELEVENLABS_TTS = {
    "stability": 0.5,           # 0.5 = balanced (expressive yet consistent)
    "similarity_boost": 0.75,   # 0.75 = natural but authentic
    "style": 0.4,               # 0.4 = moderate emotion (Turbo v2.5 only)
    "use_speaker_boost": True,  # Always True for clarity
}

# ========================================
# SMART VOICE SELECTION SYSTEM
# ========================================
# Map content types to PREMIUM Turbo v2.5 Voice IDs
# Each content type gets its own unique voice for personality
ELEVENLABS_VOICE_MAP = {
    # Primary content types (specified by user)
    "hotel": "lxYfHSkYm1EzQzGhdbfc",           # Hotel news (professional, hospitality)
    "government": "GzE4TcXfh9rYCU9gVgPp",       # Government announcements (authoritative)
    "good_news": "tnSpp4vdxKPjI9w0GnoV",        # Good news (upbeat, positive)
    "motivational": "84Fal4DSXWfp7nJ8emqQ",     # Motivational content (inspiring)
    
    # Secondary content types (using voice1, voice2, voice3)
    "luxury": "19STyYD15bswVz51nqLf",          # Voice1 (sophisticated)
    "adventure": "wyWA56cQNU2KqUW4eCsI",       # Voice2 (energetic)
    "cultural": "ZF6FPAbjXT4488VcRRnw",        # Voice3 (respectful)
    
    # Additional content types (using available voices)
    "beach": "tnSpp4vdxKPjI9w0GnoV",           # Good news voice (relaxed, positive)
    "wellness": "tnSpp4vdxKPjI9w0GnoV",         # Good news voice (calming)
    "family": "tnSpp4vdxKPjI9w0GnoV",           # Good news voice (friendly)
    "city": "wyWA56cQNU2KqUW4eCsI",            # Voice2 (dynamic)
    "nature": "ZF6FPAbjXT4488VcRRnw",          # Voice3 (serene)
    "resort": "lxYfHSkYm1EzQzGhdbfc",          # Hotel voice (hospitality)
    "announcement": "GzE4TcXfh9rYCU9gVgPp",     # Government voice (official)
    
    # Default fallback
    "default": "kPzsL2i3teMYv0FxEYQ6",         # Default Voice
}

# Sound Effects Settings (PREMIUM Creator Plan Feature)
ELEVENLABS_SOUND_EFFECTS = {
    "enabled": True,                    # Enable ElevenLabs Sound Generation
    "duration": 3.0,                    # Default duration in seconds (0.5-22)
    "prompt_influence": 0.3,            # How closely to follow prompt (0.0-1.0)
}

# Sound Effect Prompts for Different Content Types
ELEVENLABS_SOUND_PROMPTS = {
    "adventure": "Exciting outdoor adventure ambiance with wind and distant nature sounds",
    "luxury": "Elegant upscale hotel lobby with subtle sophisticated ambiance",
    "beach": "Gentle ocean waves lapping on tropical beach shore",
    "cultural": "Traditional cultural market ambiance with distant voices",
    "family": "Happy family vacation atmosphere with light background chatter",
    "wellness": "Peaceful spa ambiance with gentle water sounds",
    "city": "Vibrant city street ambiance with distant traffic",
    "nature": "Peaceful forest with birds chirping and gentle breeze",
    "default": "Subtle ambient background suitable for travel content",
}

# ========================================
# ElevenLabs Music API (NEW!)
# ========================================
# Features: AI-generated background music (20 seconds)
# Format: MP3, 44.1kHz, 128-192kbps
# Usage: Commercial use cleared
ELEVENLABS_MUSIC_API_KEY = os.getenv("ELEVENLABS_MUSIC_API_KEY", "")

# Music Generation Settings
ELEVENLABS_MUSIC_DURATION = 20000  # 20 seconds (API limit)
ELEVENLABS_MUSIC_VOLUME = -18      # dB reduction (so voiceover is clear)

# ========================================
# Google Drive (Archive videos instead of posting)
# ========================================
# Preferred method: Service Account JSON file path or JSON string in env
# If not provided, falls back to OAuth using client_secret.json and drive_token.json
GDRIVE_FOLDER_ID = "1PPR4bXQtg8kzoiCRdnux210airStuhpL"  # insta folder (shared with service account)
GDRIVE_SERVICE_ACCOUNT_FILE = os.getenv("GDRIVE_SERVICE_ACCOUNT_FILE", "")
GDRIVE_SERVICE_ACCOUNT_JSON = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "")  # inline JSON

# ========================================
# Dropbox (Temporary public links for Instagram)
# ========================================
# Prefer OAuth2 refresh token flow for long-lived operation
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN", "")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN", "")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY", "")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET", "")

# ========================================
# Email / Notifications
# ========================================
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "1") in ("1", "true", "True")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
SMTP_USER = os.getenv("SMTP_USER", "9a982c001@smtp-brevo.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "1") in ("1", "true", "True")
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "0") in ("1", "true", "True")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "tripavail92@gmail.com")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "holywolf92@gmail.com")

# Email method: 'smtp' or 'gmail_api'
EMAIL_METHOD = os.getenv("EMAIL_METHOD", "smtp").lower()
# Gmail API files (used when EMAIL_METHOD=gmail_api)
GMAIL_CLIENT_SECRET_FILE = os.getenv("GMAIL_CLIENT_SECRET_FILE", "client_secret.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "gmail_token.json")

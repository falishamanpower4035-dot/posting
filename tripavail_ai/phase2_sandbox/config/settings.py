"""
Phase 2 Sandbox Settings
========================
Sandbox-specific configuration for Phase 2 development.
This file loads from .env_sandbox instead of .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load sandbox environment variables
sandbox_env = Path(__file__).parent.parent / ".env_sandbox"
if sandbox_env.exists():
    load_dotenv(sandbox_env)
    print(f"✓ Loaded sandbox environment from: {sandbox_env}")
else:
    print(f"⚠️  WARNING: {sandbox_env} not found!")
    print("   Please copy .env_sandbox_template to .env_sandbox")

# Sandbox Mode Flag
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "false").lower() == "true"
SANDBOX_VERSION = os.getenv("SANDBOX_VERSION", "2.0")

if SANDBOX_MODE:
    print(f"✓ Sandbox Mode: ACTIVE (v{SANDBOX_VERSION})")
else:
    print("⚠️  WARNING: SANDBOX_MODE not enabled!")

# Application Settings
APP_NAME = "TripAvail AI - Phase 2 Sandbox"
APP_VERSION = SANDBOX_VERSION
DEBUG = os.getenv("DEBUG_MODE", "true").lower() == "true"

# Feature Flags (Phase 2 Experiments)
EXPERIMENTAL_GPT4O = os.getenv("EXPERIMENTAL_GPT4O", "false").lower() == "true"
EXPERIMENTAL_CLAUDE = os.getenv("EXPERIMENTAL_CLAUDE", "false").lower() == "true"
EXPERIMENTAL_TIKTOK = os.getenv("EXPERIMENTAL_TIKTOK", "false").lower() == "true"
EXPERIMENTAL_ADVANCED_SCORING = os.getenv("EXPERIMENTAL_ADVANCED_SCORING", "false").lower() == "true"
EXPERIMENTAL_MULTI_LANGUAGE = os.getenv("EXPERIMENTAL_MULTI_LANGUAGE", "false").lower() == "true"

# API Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

# Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "kPzsL2i3teMYv0FxEYQ6")

# Stock Photos (Shutterstock Priority)
SHUTTERSTOCK_ACCESS_TOKEN = os.getenv("SHUTTERSTOCK_ACCESS_TOKEN", "")
SHUTTERSTOCK_CLIENT_ID = os.getenv("SHUTTERSTOCK_CLIENT_ID", "")
SHUTTERSTOCK_CLIENT_SECRET = os.getenv("SHUTTERSTOCK_CLIENT_SECRET", "")

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

# Stability AI
STABILITY_KEY = os.getenv("STABILITY_KEY", "")

# Social Media (TEST ACCOUNTS ONLY!)
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")

# File Paths (Sandbox-specific)
SANDBOX_ROOT = Path(__file__).parent.parent
DATA_DIR = str(SANDBOX_ROOT / "data")
LOGS_DIR = str(SANDBOX_ROOT / "logs")
CONFIG_DIR = str(SANDBOX_ROOT / "config")

# Logging Settings
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | [SANDBOX] {message}"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "7 days"

# Rate Limiting (Lower for testing)
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "50"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_POSTS_PER_DAY = int(os.getenv("MAX_POSTS_PER_DAY", "5"))

# Safety Features
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"  # Prevent actual posting
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"

# Print configuration summary
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PHASE 2 SANDBOX CONFIGURATION")
    print("=" * 60)
    print(f"Sandbox Mode: {SANDBOX_MODE}")
    print(f"Debug Mode: {DEBUG}")
    print(f"Dry Run: {DRY_RUN}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Logs Directory: {LOGS_DIR}")
    print("\nExperimental Features:")
    print(f"  GPT-4o: {EXPERIMENTAL_GPT4O}")
    print(f"  Claude: {EXPERIMENTAL_CLAUDE}")
    print(f"  TikTok: {EXPERIMENTAL_TIKTOK}")
    print(f"  Advanced Scoring: {EXPERIMENTAL_ADVANCED_SCORING}")
    print(f"  Multi-Language: {EXPERIMENTAL_MULTI_LANGUAGE}")
    print("\nAPI Keys Configured:")
    print(f"  OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
    print(f"  Google Gemini: {'✓' if GOOGLE_API_KEY else '✗'}")
    print(f"  ElevenLabs: {'✓' if ELEVENLABS_API_KEY else '✗'}")
    print(f"  Shutterstock: {'✓' if SHUTTERSTOCK_ACCESS_TOKEN else '✗'}")
    print(f"  Pexels: {'✓' if PEXELS_API_KEY else '✗'}")
    print(f"  Unsplash: {'✓' if UNSPLASH_ACCESS_KEY else '✗'}")
    print("=" * 60 + "\n")

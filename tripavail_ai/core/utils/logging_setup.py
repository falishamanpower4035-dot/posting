"""
Centralized Logging Setup for TripAvail AI

This module provides a single point of configuration for all logging across the application.
It uses Loguru for rich, structured logging and intercepts stdlib logging to ensure consistency.

Features:
- Unified log format with timestamps, levels, module names
- Automatic rotation and retention from config.settings
- Human-readable text logs + optional JSON for machine parsing
- stdlib logging interception (so logging.getLogger() works seamlessly)
- Environment-based overrides for log level and JSON mode

Usage:
    Import this module once at the top of your entry point (main.py, bot.py, etc.):
    
    from core.utils import logging_setup  # noqa
    
    Then use loguru's logger or stdlib logging anywhere:
    
    from loguru import logger
    logger.info("Hello from centralized logging!")
    
    import logging
    logging.getLogger(__name__).info("This also flows through Loguru!")

Environment Variables:
    LOG_LEVEL: Override config.settings.LOG_LEVEL (e.g., DEBUG, INFO, WARNING)
    LOG_JSON: Set to "true" to enable JSON-formatted logs (default: false)
    LOG_DIR: Override config.settings.LOGS_DIR
"""

import sys
import os
import logging
from pathlib import Path
from loguru import logger

# Remove default logger to avoid duplicates
logger.remove()

# Import settings (with fallback for missing config)
try:
    from config import settings
    LOGS_DIR = Path(os.getenv("LOG_DIR", settings.LOGS_DIR))
    LOG_LEVEL = os.getenv("LOG_LEVEL", settings.LOG_LEVEL)
    LOG_ROTATION = getattr(settings, "LOG_ROTATION", "1 day")
    LOG_RETENTION = getattr(settings, "LOG_RETENTION", "30 days")
except ImportError:
    # Fallback if settings is unavailable
    LOGS_DIR = Path(os.getenv("LOG_DIR", "logs"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_ROTATION = "1 day"
    LOG_RETENTION = "30 days"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Determine if JSON logging is enabled
LOG_JSON = os.getenv("LOG_JSON", "false").lower() in ("true", "1", "yes")

# ========================================
# SINK 1: Console (human-readable, color)
# ========================================
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# ========================================
# SINK 2: All logs (text file, rotated)
# ========================================
logger.add(
    LOGS_DIR / "app.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level=LOG_LEVEL,
    rotation=LOG_ROTATION,
    retention=LOG_RETENTION,
    compression="zip",
    backtrace=True,
    diagnose=True,
)

# ========================================
# SINK 3: Error-only logs (text file, rotated)
# ========================================
logger.add(
    LOGS_DIR / "app_error.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation=LOG_ROTATION,
    retention=LOG_RETENTION,
    compression="zip",
    backtrace=True,
    diagnose=True,
)

# ========================================
# SINK 4: JSON logs (optional, machine-readable)
# ========================================
if LOG_JSON:
    logger.add(
        LOGS_DIR / "app.jsonl",
        format="{message}",
        level=LOG_LEVEL,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",
        serialize=True,  # Output as JSON
    )

# ========================================
# Intercept stdlib logging into Loguru
# ========================================
class InterceptHandler(logging.Handler):
    """
    Intercepts standard logging calls and routes them through Loguru.
    This ensures all logging.getLogger() calls use the same sinks/format.
    """
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Install the intercept handler for stdlib logging
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Intercept all existing loggers
for name in logging.root.manager.loggerDict.keys():
    logging_logger = logging.getLogger(name)
    logging_logger.handlers = [InterceptHandler()]
    logging_logger.propagate = False

# Log setup completion
logger.info(f"✅ Centralized logging initialized: level={LOG_LEVEL}, dir={LOGS_DIR}, json={LOG_JSON}")

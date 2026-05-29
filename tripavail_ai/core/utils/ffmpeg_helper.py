#!/usr/bin/env python3
"""
FFmpeg Helper Utility
Provides FFmpeg and FFprobe paths with fallback to imageio-ffmpeg
"""

import shutil
from pathlib import Path
from typing import Optional
from loguru import logger

# Cache for FFmpeg paths
_ffmpeg_path: Optional[str] = None
_ffprobe_path: Optional[str] = None


def get_ffmpeg_path() -> str:
    """
    Get FFmpeg executable path with fallback to imageio-ffmpeg
    
    Returns:
        Path to FFmpeg executable
        
    Raises:
        RuntimeError: If FFmpeg cannot be found
    """
    global _ffmpeg_path
    
    if _ffmpeg_path is not None:
        return _ffmpeg_path
    
    # First, try to find FFmpeg in PATH
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        _ffmpeg_path = ffmpeg_path
        logger.debug(f"Found FFmpeg in PATH: {ffmpeg_path}")
        return _ffmpeg_path
    
    # Fallback to imageio-ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and Path(ffmpeg_path).exists():
            _ffmpeg_path = ffmpeg_path
            logger.info(f"Using imageio-ffmpeg FFmpeg: {ffmpeg_path}")
            return _ffmpeg_path
    except ImportError:
        logger.warning("imageio-ffmpeg not available")
    except Exception as e:
        logger.warning(f"Error getting FFmpeg from imageio-ffmpeg: {e}")
    
    # If we get here, FFmpeg was not found
    raise RuntimeError(
        "FFmpeg not found. Please install FFmpeg and add it to PATH, "
        "or ensure imageio-ffmpeg is installed (it comes with moviepy)."
    )


def get_ffprobe_path() -> str:
    """
    Get FFprobe executable path with fallback to imageio-ffmpeg
    
    Returns:
        Path to FFprobe executable
        
    Raises:
        RuntimeError: If FFprobe cannot be found
    """
    global _ffprobe_path
    
    if _ffprobe_path is not None:
        return _ffprobe_path
    
    # First, try to find FFprobe in PATH
    ffprobe_path = shutil.which('ffprobe')
    if ffprobe_path:
        _ffprobe_path = ffprobe_path
        logger.debug(f"Found FFprobe in PATH: {ffprobe_path}")
        return _ffprobe_path
    
    # Fallback: try to derive from FFmpeg path
    try:
        ffmpeg_path = get_ffmpeg_path()
        # If FFmpeg is from imageio-ffmpeg, FFprobe should be in the same directory
        if 'imageio_ffmpeg' in ffmpeg_path:
            ffprobe_path = str(Path(ffmpeg_path).parent / 'ffprobe.exe')
            if Path(ffprobe_path).exists():
                _ffprobe_path = ffprobe_path
                logger.info(f"Using imageio-ffmpeg FFprobe: {ffprobe_path}")
                return _ffprobe_path
            
            # Try without .exe extension (Linux/Mac)
            ffprobe_path_no_ext = str(Path(ffmpeg_path).parent / 'ffprobe')
            if Path(ffprobe_path_no_ext).exists():
                _ffprobe_path = ffprobe_path_no_ext
                logger.info(f"Using imageio-ffmpeg FFprobe: {ffprobe_path_no_ext}")
                return _ffprobe_path
    except RuntimeError:
        pass
    
    # If we get here, FFprobe was not found
    # For FFprobe, we can also try using FFmpeg with -probe_size and -analyzeduration
    # But for simplicity, we'll require FFprobe or use FFmpeg as fallback
    logger.warning("FFprobe not found, will try to use FFmpeg as fallback")
    try:
        ffmpeg_path = get_ffmpeg_path()
        _ffprobe_path = ffmpeg_path  # Use FFmpeg as FFprobe fallback
        logger.info(f"Using FFmpeg as FFprobe fallback: {ffmpeg_path}")
        return _ffprobe_path
    except RuntimeError:
        raise RuntimeError(
            "FFprobe not found and FFmpeg is also unavailable. "
            "Please install FFmpeg and add it to PATH, "
            "or ensure imageio-ffmpeg is installed."
        )


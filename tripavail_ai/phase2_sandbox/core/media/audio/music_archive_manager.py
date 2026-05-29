#!/usr/bin/env python3
"""
Music Archive Manager - Reuse archived background music files
Saves 530 credits per post by reusing existing music instead of generating new
"""

from pathlib import Path
from typing import Optional
import random
import shutil
from loguru import logger


class MusicArchiveManager:
    """
    Manages archived background music files for reuse
    Saves ElevenLabs API credits by reusing existing music
    """
    
    def __init__(self, archive_dir: Optional[Path] = None):
        """
        Initialize Music Archive Manager
        
        Args:
            archive_dir: Path to music archive directory (default: data/music_archive)
        """
        if archive_dir is None:
            archive_dir = Path("data/music_archive")
        
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache available music files
        self._available_music = None
        self._refresh_cache()
        
        logger.info(f"🎵 Music Archive Manager initialized: {len(self._available_music)} files available")
    
    def _refresh_cache(self):
        """Refresh the cache of available music files"""
        if self.archive_dir.exists():
            all_files = list(self.archive_dir.glob("*.mp3"))
            # Filter out empty files (0 bytes) and validate with ffprobe
            valid_files = []
            for f in all_files:
                size = f.stat().st_size
                if size < 1000:  # Skip files smaller than 1KB (likely empty or corrupted)
                    logger.warning(f"⚠️ Skipping small/corrupted file: {f.name} ({size} bytes)")
                    continue
                
                # Quick validation with ffprobe
                import subprocess
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', str(f)],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    valid_files.append(f)
                else:
                    logger.warning(f"⚠️ Skipping invalid file: {f.name} ({result.stderr[:50]})")
            
            self._available_music = valid_files
        else:
            self._available_music = []
    
    def get_available_count(self) -> int:
        """Get count of available archived music files"""
        return len(self._available_music)
    
    def select_random_music(self) -> Optional[Path]:
        """
        Select a random music file from archive
        
        Returns:
            Path to selected music file, or None if no files available
        """
        if not self._available_music:
            self._refresh_cache()
        
        if not self._available_music:
            logger.warning("⚠️ No archived music files available")
            return None
        
        selected = random.choice(self._available_music)
        logger.info(f"🎵 Selected archived music: {selected.name}")
        return selected
    
    def copy_to_post(self, source_music: Path, target_path: Path) -> bool:
        """
        Copy archived music file to post directory
        
        Args:
            source_music: Path to archived music file
            target_path: Target path in post directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_music, target_path)
            logger.info(f"✅ Copied archived music to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy archived music: {e}")
            return False
    
    def use_archived_music(self, output_path: Path) -> bool:
        """
        Select and copy archived music to output path
        
        Args:
            output_path: Where to save the music file
            
        Returns:
            True if successful, False otherwise
        """
        selected = self.select_random_music()
        if not selected:
            return False
        
        return self.copy_to_post(selected, output_path)


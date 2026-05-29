#!/usr/bin/env python3
"""Test music archive manager"""
from core.media.audio.music_archive_manager import MusicArchiveManager

m = MusicArchiveManager()
print(f"Available music files: {m.get_available_count()}")

# Test selection
selected = m.select_random_music()
if selected:
    print(f"Selected: {selected.name}")
else:
    print("No music files available")


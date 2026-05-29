"""
Audio Manager Module for TripAvail AI
Handles background music, audio ducking, and sound effects
"""

from .music_library import MusicLibrary
from .audio_ducking import AudioDucker
from .sound_effects import SoundEffectsManager

__all__ = ['MusicLibrary', 'AudioDucker', 'SoundEffectsManager']


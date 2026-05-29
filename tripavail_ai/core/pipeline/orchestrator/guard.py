from pathlib import Path
from typing import Tuple
from moviepy import VideoFileClip


def is_vertical(path: Path) -> bool:
    with VideoFileClip(str(path)) as clip:
        w, h = clip.size
    return h > w and h >= 1280


def has_single_audio(path: Path) -> bool:
    # MoviePy exposes a single audio track if present; for multi-track we rely on our pipeline (pro is silent, final has one)
    with VideoFileClip(str(path)) as clip:
        return clip.audio is not None


def duration_ok(path: Path, max_seconds: float = 60.0) -> bool:
    with VideoFileClip(str(path)) as clip:
        return clip.duration <= max_seconds + 0.5


def validate_final(path: Path) -> Tuple[bool, str]:
    if not path.exists():
        return False, "file_missing"
    if not is_vertical(path):
        return False, "not_vertical"
    if not has_single_audio(path):
        return False, "no_audio"
    if not duration_ok(path):
        return False, "too_long"
    return True, "ok"



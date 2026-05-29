#!/usr/bin/env python3
"""
Integration test for the simplified long-video assembly pipeline.

This utility fabricates a deterministic set of assets (itinerary, script, images,
voiceovers, mixed audio) for N consecutive days, assembles per-day videos, and
then compiles them into a cumulative video. It is designed to surface FFmpeg /
assembly errors quickly without relying on external APIs.

Usage:
    python scripts/test_day_video_assembly.py --destination "Testville, Wonderland" --days 4
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger
from PIL import Image

# Ensure project root on path when running as a script
import sys

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings_long
from core.media.audio.audio_mixer_long import AudioMixerLong
from core.media.video.generator.day_video_assembler_long import DayVideoAssemblerLong
from core.media.video.generator.final_video_assembler_long import FinalVideoAssemblerLong
from core.utils.ffmpeg_helper import get_ffmpeg_path


IMAGES_PER_DAY = 12
VOICEOVER_DURATION = 30.0  # seconds
IMAGE_RESOLUTION = (1920, 1080)


def build_test_itinerary(destination: str, num_days: int) -> Dict:
    itinerary_days = []
    for day in range(1, num_days + 1):
        scenes = []
        for idx in range(1, 5):
            scenes.append(
                {
                    "scene_number": idx,
                    "order": idx,
                    "category": "attraction",
                    "title": f"Scene {idx}",
                    "description": f"Test scene {idx} for Day {day}",
                }
            )
        itinerary_days.append(
            {
                "day_number": day,
                "title": f"DAY {day} – Testville Explorations",
                "scenes": scenes,
            }
        )
    return {"destination": destination, "itinerary": itinerary_days}


def build_test_script(num_days: int) -> Dict:
    script_days = []
    for day in range(1, num_days + 1):
        scenes = []
        for idx in range(1, 5):
            scenes.append(
                {
                    "scene_number": idx,
                    "order": idx,
                    "category": "attraction",
                    "narration": f"Scene {idx} narration for day {day}.",
                    "image_keywords": [f"Day {day}", f"Scene {idx}", "Test"],
                }
            )
        script_days.append(
            {
                "day_number": day,
                "title": f"DAY {day} – Testville Explorations",
                "narration": f"This is the narration for day {day} in our integration test.",
                "image_keywords": [f"Day {day}", "Testville", "Travel"],
                "estimated_voiceover_seconds": VOICEOVER_DURATION,
                "specific_locations": [f"Test Location {day}"],
                "specific_dishes": [f"Test Dish {day}"],
                "scenes": scenes,
            }
        )
    return {"days": script_days}


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_placeholder_images(destination: str, num_days: int) -> None:
    base_dir = Path(settings_long.IMAGES_DIR) / destination
    for day in range(1, num_days + 1):
        day_dir = ensure_directory(base_dir / f"day_{day}" / "all")
        for idx in range(1, IMAGES_PER_DAY + 1):
            image_path = day_dir / f"test_day{day:02d}_{idx:02d}.jpg"
            if image_path.exists():
                continue
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
            img = Image.new("RGB", IMAGE_RESOLUTION, color=color)
            img.save(image_path, quality=90)
            logger.debug(f"Created placeholder image: {image_path}")


def generate_synthetic_audio(output_path: Path, duration: float) -> None:
    ffmpeg_path = get_ffmpeg_path()
    cmd = [
        ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=44100:cl=stereo",
        "-t",
        str(duration),
        "-q:a",
        "4",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def ensure_background_track(min_duration: float = 120.0) -> Path:
    music_dir = ensure_directory(Path("assets") / "audio")
    track_path = music_dir / "test_background.mp3"
    if track_path.exists():
        return track_path
    ffmpeg_path = get_ffmpeg_path()
    cmd = [
        ffmpeg_path,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=432:sample_rate=44100:duration={min_duration}",
        "-q:a",
        "4",
        str(track_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    logger.info(f"Created test background track: {track_path}")
    return track_path


def prepare_voiceovers(destination: str, num_days: int) -> Dict[int, Path]:
    voiceover_dir = ensure_directory(Path(settings_long.VOICEOVERS_DIR))
    voiceovers = {}
    safe_destination = destination.replace(",", "__").replace(" ", "_")
    for day in range(1, num_days + 1):
        vo_path = voiceover_dir / f"{safe_destination}_day_{day}_voiceover.mp3"
        generate_synthetic_audio(vo_path, VOICEOVER_DURATION)
        voiceovers[day] = vo_path
    return voiceovers


def run_day_assembly_test(destination: str, num_days: int) -> Tuple[Dict[int, Path], Path]:
    logger.info(f"Preparing placeholder assets for {num_days} day(s) in {destination}...")
    generate_placeholder_images(destination, num_days)
    voiceovers = prepare_voiceovers(destination, num_days)
    background_track = ensure_background_track()

    itinerary = build_test_itinerary(destination, num_days)
    script = build_test_script(num_days)

    audio_mixer = AudioMixerLong()
    day_assembler = DayVideoAssemblerLong()
    final_assembler = FinalVideoAssemblerLong()

    mixed_audio_paths: Dict[int, Path] = {}
    for day in range(1, num_days + 1):
        mixed_audio = audio_mixer.mix_audio_for_day(
            voiceover_path=voiceovers[day],
            day_number=day,
            destination=destination,
            music_path=background_track,
        )
        if not mixed_audio:
            raise RuntimeError(f"Failed to mix audio for day {day}")
        mixed_audio_paths[day] = mixed_audio

    day_videos: Dict[int, Path] = {}
    images_root = Path(settings_long.IMAGES_DIR)
    for day_data in itinerary["itinerary"]:
        day_number = day_data["day_number"]
        video_path = day_assembler.assemble_day_video(
            day_data=day_data,
            script_data=script,
            destination=destination,
            images_dir=images_root,
            voiceover_path=mixed_audio_paths[day_number],
        )
        if not video_path:
            raise RuntimeError(f"Day {day_number} assembly failed")
        day_videos[day_number] = video_path

    final_video = final_assembler.combine_day_videos(
        day_video_paths=day_videos,
        destination=destination,
    )
    if not final_video:
        raise RuntimeError("Final video assembly failed")

    return day_videos, final_video


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Integration test for long video day assembly"
    )
    parser.add_argument(
        "--destination",
        default="Testville, Wonderland",
        help="Destination name to namespace assets",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=4,
        help="Number of synthetic days to generate (default: 4)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary as JSON for CI integration",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    destination = args.destination
    num_days = args.days

    if num_days < 1:
        raise ValueError("Number of days must be >= 1")

    logger.info("===============================================")
    logger.info(" LONG VIDEO ASSEMBLY INTEGRATION TEST (SIMPLIFIED)")
    logger.info("===============================================")
    logger.info(f"Destination: {destination}")
    logger.info(f"Days: {num_days}")

    day_videos, final_video = run_day_assembly_test(destination, num_days)

    summary = {
        "destination": destination,
        "days": num_days,
        "day_videos": {day: str(path) for day, path in day_videos.items()},
        "final_video": str(final_video),
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        logger.info("===============================================")
        logger.info(" TEST SUMMARY")
        logger.info("===============================================")
        for day, path in sorted(day_videos.items()):
            logger.info(f"Day {day} video: {path}")
        logger.info(f"Final video: {final_video}")
        logger.info("✅ Assembly test completed successfully")


if __name__ == "__main__":
    main()


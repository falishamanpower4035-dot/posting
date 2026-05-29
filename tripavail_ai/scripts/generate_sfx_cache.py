#!/usr/bin/env python3
"""
Batch-generate sound effects variants (whoosh/swipe/ambient) using ElevenLabs
Adds entries to the SFX manifest and caches MP3 files under data/audio/sound_effects
"""

from pathlib import Path
from loguru import logger
from modules.audio_manager.sound_effects import SoundEffectsManager
from modules.audio_manager.elevenlabs_tts import synthesize
from importlib import import_module


def main():
    sfx_mgr = SoundEffectsManager()

    try:
        settings = import_module('config.settings')
        api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
        voice_id = getattr(settings, 'ELEVENLABS_VOICE_ID', None)
    except Exception:
        api_key = None
        voice_id = None

    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not configured.")
        return

    out_dir = Path("data/audio/sound_effects")
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [
        ("whoosh", 4),
        ("swipe", 3),
        ("fade", 2),
        ("waves", 2),
        ("city", 2),
        ("birds", 2),
        ("pop", 3),
    ]

    created = 0
    for effect_type, count in targets:
        for i in range(1, count + 1):
            file_name = f"{effect_type}_{i:02d}.mp3"
            out_path = out_dir / file_name
            if out_path.exists():
                continue
            prompt = sfx_mgr._prompt_for_type(effect_type)  # reuse prompt
            ok = synthesize(
                text=prompt,
                output_path=out_path,
                api_key=api_key,
                voice_id=voice_id,
            )
            if ok:
                created += 1
                sfx_mgr.add_sound_effect({
                    "id": f"{effect_type}_{i:02d}",
                    "name": f"{effect_type.capitalize()} Variant {i}",
                    "category": "ambient" if effect_type in ["waves", "city", "birds"] else ("impact" if effect_type == "pop" else "transition"),
                    "type": effect_type,
                    "duration": 0.6,
                    "file_path": str(out_path),
                    "volume": 0.25,
                    "license": "Generated via ElevenLabs"
                })

    print(f"SFX generation complete. New files: {created}")


if __name__ == "__main__":
    main()



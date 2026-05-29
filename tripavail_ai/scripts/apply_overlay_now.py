#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from production_pipeline import ProductionPipeline

if __name__ == "__main__":
    pp = ProductionPipeline()
    post_id = "001"
    meta = pp.post_manager.get_metadata(post_id)
    final_path = pp.post_manager.get_final_video_path(post_id)
    voiceover_path = pp.post_manager.get_voiceover_path(post_id)
    out = pp._apply_text_overlays_ffmpeg(final_path, meta, voiceover_path)
    if out:
        print(f"Overlay applied -> {out}")
    else:
        print("Overlay step returned None")

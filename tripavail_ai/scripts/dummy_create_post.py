#!/usr/bin/env python3
import json, shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.content.post_manager import PostManager

def main(src_id: str = '008') -> None:
    pm = PostManager()
    all_ids = [int(p) for p in pm.get_all_posts()] or [0]
    new = f"{max(all_ids)+1:03d}"
    post_dir = pm.get_post_directory(new)
    meta = {
        'post_id': new,
        'topic_id': new,
        'original_title': 'Dummy Email Test Post',
        'caption': 'Dummy test post for email notification',
        'hashtags': ['#TripAvail','#Test']
    }
    pm.save_metadata(new, meta)
    # Copy one image from src to ensure quick render
    src_images = list((pm.get_images_dir(src_id)).glob('img_*'))
    if src_images:
        dst_img = pm.get_images_dir(new)/src_images[0].name
        dst_img.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_images[0], dst_img)
    print(json.dumps({'new_post_id': new}, indent=2))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '008')

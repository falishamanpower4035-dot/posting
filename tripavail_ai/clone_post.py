#!/usr/bin/env python3
import sys, json, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.content.post_manager import PostManager

def main():
    src_id = sys.argv[1] if len(sys.argv) > 1 else '008'
    pm = PostManager()
    all_posts = pm.get_all_posts()
    next_idx = (max([int(p) for p in all_posts] + [0]) + 1)
    new_id = f"{next_idx:03d}"

    src_dir = pm.get_post_directory(src_id)
    dst_dir = pm.get_post_directory(new_id)

    # Copy metadata
    meta = pm.get_metadata(src_id) or {}
    meta['post_id'] = new_id
    meta['topic_id'] = new_id
    pm.save_metadata(new_id, meta)

    # Ensure video dir exists and copy full multi-image final
    (dst_dir / 'video').mkdir(parents=True, exist_ok=True)
    pro = Path('data/videos') / f'reel_{src_id}_pro.mp4'
    src_final = src_dir / 'video' / 'final.mp4'
    dst_final = dst_dir / 'video' / 'final.mp4'

    if pro.exists():
        shutil.copy2(pro, dst_final)
    elif src_final.exists():
        shutil.copy2(src_final, dst_final)
    else:
        print(json.dumps({'error': 'No source video found'}, indent=2))
        sys.exit(2)

    print(json.dumps({'new_post_id': new_id, 'dst_final': str(dst_final)}, indent=2))

if __name__ == '__main__':
    main()

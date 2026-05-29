#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.content.post_manager import PostManager
from core.social.platforms.instagram_poster import InstagramPoster
from core.social.platforms.facebook_poster import FacebookPoster
from core.social.platforms.youtube_uploader import YouTubeUploader

def main():
    pm=PostManager()
    targets = ['013','048']
    for pid in targets:
        meta = pm.get_metadata(pid) or {}
        video = pm.get_final_video_path(pid)
        if not video.exists():
            print('SKIP', pid, 'no final')
            continue
        title = (meta.get('original_title') or f'TripAvail Post {pid}')[:70]
        caption = meta.get('caption', meta.get('context_caption',''))
        hashtags = meta.get('hashtags', [])
        print('POST', pid, 'video', video)
        if not pm.is_posted(pid,'instagram'):
            try:
                ig = InstagramPoster()
                ig_caption = caption + ('\n\n' + ' '.join(hashtags[:30]) if hashtags else '')
                ok = ig.post_reel(video, ig_caption)
                print('IG', pid, ok)
                if ok: pm.mark_as_posted(pid,'instagram')
            except Exception as e:
                print('IG error', pid, e)
        if not pm.is_posted(pid,'facebook'):
            try:
                fb = FacebookPoster()
                fb_caption = caption + ('\n\n' + ' '.join(hashtags) if hashtags else '')
                ok = fb.post_video(video, fb_caption, hashtags)
                print('FB', pid, ok)
                if ok: pm.mark_as_posted(pid,'facebook')
            except Exception as e:
                print('FB error', pid, e)
        if not pm.is_posted(pid,'youtube'):
            try:
                yt = YouTubeUploader()
                yt.authenticate()
                desc = caption + ('\n\n' + ' '.join(hashtags[:10]) if hashtags else '')
                vid = yt.upload_video(video, title=f"{title} | TripAvail", description=desc, tags=['TripAvail','Shorts'] )
                print('YT', pid, vid)
                if vid: pm.mark_as_posted(pid,'youtube', f'https://youtube.com/watch?v={vid}')
            except Exception as e:
                print('YT error', pid, e)
    print('DONE')

if __name__ == '__main__':
    main()

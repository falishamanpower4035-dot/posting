from moviepy import VideoFileClip
import os

files = [f for f in os.listdir("data/videos") if f.endswith(".mp4")]
for f in files:
    try:
        clip = VideoFileClip(os.path.join("data/videos", f))
        print(f"{f}: {clip.duration:.1f}s")
        clip.close()
    except Exception as e:
        print(f"{f}: Error - {e}")

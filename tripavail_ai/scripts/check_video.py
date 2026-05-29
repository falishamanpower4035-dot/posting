from moviepy import VideoFileClip
import os

files = [f for f in os.listdir('data/videos') if f.endswith('_final.mp4')]
for f in files:
    clip = VideoFileClip(f"data/videos/{f}")
    print(f"{f}: {clip.duration:.1f}s")
    clip.close()

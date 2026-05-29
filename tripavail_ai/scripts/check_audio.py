from moviepy import AudioFileClip
import os

files = [f for f in os.listdir('data/audio/voiceovers') if f.endswith('.mp3')]
for f in files:
    clip = AudioFileClip(f"data/audio/voiceovers/{f}")
    print(f"{f}: {clip.duration:.1f}s")
    clip.close()

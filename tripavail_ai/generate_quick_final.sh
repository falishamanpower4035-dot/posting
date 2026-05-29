#!/bin/bash
# Quick render of final.mp4 for a given post ID
# Usage: ./generate_quick_final.sh 008

set -euo pipefail

POST_ID=${1:-}
if [ -z "$POST_ID" ]; then
  echo "Usage: $0 <post_id_three_digits>" >&2
  exit 1
fi

BASE="data/posts/post_${POST_ID}"
IMG=$(ls -1 "$BASE/images"/img_* 2>/dev/null | head -1 || true)
VO="$BASE/audio/voiceover.mp3"
OUT="$BASE/video/final.mp4"

if [ -z "$IMG" ] || [ ! -f "$IMG" ]; then
  echo "No images found in $BASE/images" >&2
  exit 2
fi

mkdir -p "$BASE/video"

if [ -f "$VO" ]; then
  ffmpeg -y -loglevel error -loop 1 -t 20 -i "$IMG" -i "$VO" \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1" \
    -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT"
else
  ffmpeg -y -loglevel error -loop 1 -t 12 -i "$IMG" \
    -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1" \
    -c:v libx264 -pix_fmt yuv420p "$OUT"
fi

ls -lh "$OUT"

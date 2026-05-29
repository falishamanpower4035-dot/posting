"""
Pro Video Generator (FFmpeg)
Creates professional reels with Ken-Burns, crossfades, hook text, branding, and music.
"""

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class ProVideoGenerator:
	def __init__(self):
		self.data_dir = Path("data")
		self.videos_dir = self.data_dir / "videos"
		self.manifest_file = self.data_dir / "image_manifest.json"
		self.posts_file = self.data_dir / "posts.json"
		self.logs_dir = Path("logs")
		self.run_summary_file = self.logs_dir / "video_run_summary.txt"
		self.font_candidates = [
			str(Path("C:/Windows/Fonts/arial.ttf")),
			str(Path("C:/Windows/Fonts/Segoeui.ttf")),
		]
		self.logo_path = Path("assets") / "tripavail_logo.png"
		self.audio_dir = Path("assets") / "audio"
		# ULTRA PREMIUM VIDEO SETTINGS
		self.target_w, self.target_h = 1080, 1920  # 9:16 aspect ratio
		self.fps = 30  # 30 FPS for lower CPU/memory usage and platform stability
		self.image_sec = 3.5
		self.fade_sec = 0.8
		self.total_sec = 22.0
		# Premium video encoding settings
		self.video_codec = "libx264"
		self.video_preset = "slow"  # Best quality encoding
		self.video_crf = 18  # Lower CRF = higher quality (18 is visually lossless)
		self.audio_codec = "aac"
		self.audio_bitrate = "320k"  # High quality audio
		self._ensure_dirs()
		logger.info("ProVideoGenerator initialized")

	def _ensure_dirs(self):
		self.videos_dir.mkdir(parents=True, exist_ok=True)
		self.logs_dir.mkdir(parents=True, exist_ok=True)

	def _pick_font(self) -> Optional[str]:
		for p in self.font_candidates:
			if os.path.exists(p):
				return p
		return None

	def _pick_audio(self) -> Optional[str]:
		if self.audio_dir.exists():
			for name in ["travel_upbeat.mp3", "adventure_theme.mp3", "nature_ambient.mp3", "city_exploration.mp3"]:
				p = self.audio_dir / name
				if p.exists():
					return str(p)
		return None

	def _load_posts_and_images(self) -> List[Dict[str, Any]]:
		if not self.manifest_file.exists() or not self.posts_file.exists():
			logger.error("Required data files not found")
			return []
		manifest = json.loads(Path(self.manifest_file).read_text(encoding="utf-8"))
		posts = json.loads(Path(self.posts_file).read_text(encoding="utf-8"))
		posts_by_id = {}
		for idx, post in enumerate(posts.get("posts", []), start=1):
			pid = post.get("post_id") or f"{idx:03d}"
			post["post_id"] = pid
			posts_by_id[pid] = post
		processed = []
		for mpost in manifest.get("posts", []):
			pid = mpost.get("post_id")
			imgs = mpost.get("image_paths", [])
			if pid in posts_by_id and len(imgs) >= 3:
				item = posts_by_id[pid]
				item["image_paths"] = imgs[:3]
				processed.append(item)
		return processed

	def _build_ffmpeg_cmd(self, images: List[str], output: str, hook_text: str, post_id: str = None, duration: Optional[float] = None) -> List[str]:
		"""Build enhanced FFmpeg command with crossfade transitions and dynamic duration"""
		num_images = len(images)
		
		# Inputs: images with loop and duration
		# CRITICAL: First image duration is 1.5s (freeze for YouTube thumbnail), others are normal (3.5s)
		freeze_duration = 1.5  # Freeze first image for YouTube thumbnail selection
		inputs = []
		for i, img in enumerate(images):
			if i == 0:
				# First image: freeze duration (1.5s) for YouTube thumbnail
				inputs += ["-loop", "1", "-t", str(freeze_duration), "-i", img]
			else:
				# Other images: normal duration (3.5s)
				inputs += ["-loop", "1", "-t", str(self.image_sec), "-i", img]
		
		# NOTE: Do not include audio inputs here. Audio is mixed in a separate
		# step (see modules/video_generator/mix_audio.py) to avoid double audio.
		vo_exists = False
		
		# Build filtergraph: scale each image, then crossfade
		filters = []
		
		# Scale and pad each image with Ken Burns zoom effect
		# CRITICAL: First image (index 0) gets NO zoom - frozen for YouTube thumbnail selection
		freeze_duration = 1.5  # Freeze first image for YouTube thumbnail
		for i in range(num_images):
			if i == 0:
				# First image: NO zoom effect - freeze frame for YouTube thumbnail (1.5 seconds)
				# This ensures YouTube picks the first frame as thumbnail automatically
				# Static image (no zoom, no motion) for 1.5 seconds
				filters.append(f"[{i}:v]scale={self.target_w}:{self.target_h}:force_original_aspect_ratio=decrease,pad={self.target_w}:{self.target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={self.fps}[v{i}]")
			else:
				# Other images: Subtle zoom for dynamic feel
				zoom_filter = f"zoompan=z='min(zoom+0.001,1.2)':d={int(self.image_sec * self.fps)}:s={self.target_w}x{self.target_h}:fps={self.fps}"
				filters.append(f"[{i}:v]scale={self.target_w}:{self.target_h}:force_original_aspect_ratio=decrease,pad={self.target_w}:{self.target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,{zoom_filter}[v{i}]")
		
		# Apply crossfade transitions between images
		if num_images == 1:
			# Single image, no transition needed
			filters.append("[v0]copy[vout]")
		else:
			# Start with first image (frozen for 1.5s for YouTube thumbnail selection)
			current_label = "[v0]"
			
			# Freeze duration for first image (YouTube thumbnail)
			freeze_duration = 1.5
			
			for i in range(1, num_images):
				next_label = f"[v{i}]"
				output_label = f"[vt{i}]" if i < num_images - 1 else "[vout]"
				
				# Calculate offset for crossfade
				if i == 1:
					# First transition: starts after freeze duration (1.5s)
					offset = freeze_duration
				else:
					# Subsequent transitions: normal spacing
					offset = freeze_duration + (self.image_sec - self.fade_sec) * (i - 1)
				
				# Apply crossfade transition
				filters.append(
					f"{current_label}{next_label}xfade=transition=smoothleft:duration={self.fade_sec}:offset={offset}{output_label}"
				)
				
				current_label = output_label
		
		# Add animated hook text (from frame 2 onwards, first 4.5 seconds)
		# Frame 2 at 30 FPS ≈ 0.0667 seconds (skip frame 1 which has thumbnail)
		hook_sanitized = hook_text.encode('ascii', 'ignore').decode('ascii')
		# Escape special characters for FFmpeg drawtext
		hook_sanitized = hook_sanitized.replace('\\', '\\\\').replace(':', '\\:').replace("'", "'\\\\\\''")
		logger.info(f"Hook text: '{hook_sanitized}'")
		
		# Hook text starting from frame 2 (0.0167s) to avoid thumbnail overlap
		filters.append(
			f"[vout]drawtext=text='{hook_sanitized}'"
			f":fontsize=70"  # Large font
			f":fontcolor=white"
			f":bordercolor=black"
			f":borderw=4"  # Thick black outline
			f":box=1"
			f":boxcolor=black@0.7"  # Semi-transparent black box
			f":boxborderw=25"  # Padding around text
			f":x=(w-text_w)/2"  # Center horizontally
			f":y=h-th-120"  # Position near bottom (lower third)
			f":enable='between(t,0.0667,4.5)'"  # Start from frame 2 (skip frame 1 thumbnail)
			f"[vt]"
		)
		
		# Add logo if present
		if self.logo_path.exists():
			inputs += ["-i", str(self.logo_path)]
			logo_idx = num_images + (1 if vo_exists else 0)
			filters.append(f"[vt][{logo_idx}:v]scale2ref=w=iw*0.18:h=ow/mdar[logo][base];[base][logo]overlay=x=W-w-40:y=H-h-40:format=auto[vfinal]")
		else:
			filters.append("[vt]copy[vfinal]")
		
		# Audio handling: always output silent pro video; audio is added later
		amap = ["-map", "[vfinal]"]
		
		# Join all filters
		filter_complex = ";".join(filters)
		
		# Output options
		# Use dynamic duration if provided, otherwise use default
		video_duration = duration if duration is not None else self.total_sec
		
		out_opts = [
			"-t", str(video_duration),
			"-c:v", self.video_codec,
			"-preset", self.video_preset,  # Use premium "slow" preset
			"-crf", str(self.video_crf),   # Use premium CRF 18
			"-pix_fmt", "yuv420p",
			"-r", str(self.fps),  # Set frame rate to configured FPS (30)
			"-shortest",
		]
		
		# No audio stream in pro render
		
		cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filter_complex] + amap + out_opts + [output]
		return cmd

	def _load_manifest(self) -> Dict[str, Any]:
		"""Load image manifest"""
		try:
			with open(self.manifest_file, 'r', encoding='utf-8') as f:
				return json.load(f)
		except Exception as e:
			logger.error(f"Error loading manifest: {e}")
			return {"posts": []}

	def generate_for_post(self, post: Dict[str, Any]) -> Optional[str]:
		# Get post ID
		pid_raw = post.get("post_id", post.get("topic_id", "1"))
		pid_str = str(pid_raw).replace("post_", "")  # Remove prefix if present
		pid_padded = pid_str.zfill(3)
		
		# NEW: Try to load images from post-centric directory first
		from pathlib import Path as P
		post_images_dir = P(f"data/posts/post_{pid_padded}/images")
		
		images = []
		if post_images_dir.exists():
			# Use post-centric structure
			image_paths = sorted(post_images_dir.glob("*.jpg"))
			if image_paths:
				images = [str(p) for p in image_paths]
				logger.info(f"Using {len(images)} images from post directory: {post_images_dir}")
			else:
				logger.error(f"No images found in post directory: {post_images_dir}")
				return None
		else:
			# Fallback to old manifest-based approach
			logger.warning(f"Post directory not found: {post_images_dir}, trying manifest...")
			manifest_data = self._load_manifest()
			post_images = None
			for p in manifest_data.get("posts", []):
				mid = str(p.get("post_id"))
				if mid == pid_str or mid == pid_padded:
					post_images = p.get("image_paths", [])
					break
			
			if not post_images:
				logger.error(f"Post {pid_str}: no images found in manifest")
				return None
			
			images = [str(Path(p)) for p in post_images]
		
		if len(images) < 2:
			logger.error(f"Post {pid_str}: needs at least 2 images, found {len(images)}")
			return None
		
		# Calculate video duration from image count (fixed 3s per image)
		# Duration = (images × image_sec) - ((images-1) × fade_sec)
		# This accounts for overlapping crossfades
		# Allow explicit override via metadata key 'target_duration_sec'
		override_duration = None
		try:
			override_val = post.get("target_duration_sec") or post.get("duration_override")
			if override_val is not None:
				override_duration = float(override_val)
		except Exception:
			override_duration = None

		target_duration = (len(images) * self.image_sec) - ((len(images) - 1) * self.fade_sec)
		logger.info(f"📊 Video duration: {target_duration:.1f}s ({len(images)} images × {self.image_sec}s)")
		
		hook = self._make_hook(post)
		out = str(self.videos_dir / f"reel_{pid_str}_pro.mp4")
		cmd = self._build_ffmpeg_cmd(images, out, hook, pid_str, override_duration if override_duration is not None else target_duration)
		logger.info(f"Generating pro reel for post {pid_str} with {len(images)} images ({target_duration:.1f}s)")
		res = subprocess.run(cmd, capture_output=True, text=True)
		if res.returncode != 0:
			logger.error(f"FFmpeg error for {pid_str}:\n{res.stderr}")
			return None
		logger.info(f"Generated: {out}")
		return out

	def _make_hook(self, post: Dict[str, Any]) -> str:
		# Use a short hook from caption or original_title
		cap = (post.get("caption") or "").strip()
		if cap:
			words = cap.split()
			return " ".join(words[:8])
		title = (post.get("original_title") or "").strip()
		return title[:60] if title else "Explore more with TripAvail"

	def run(self) -> Dict[str, str]:
		posts = self._load_posts_and_images()
		results: Dict[str, str] = {}
		for post in posts:
			path = self.generate_for_post(post)
			if path:
				results[post["post_id"]] = path
		self._log_summary(results)
		return results

	def _log_summary(self, results: Dict[str, str]):
		summary = [
			f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
			f"Generated: {len(results)} reels",
		]
		for pid, p in results.items():
			summary.append(f"{pid}: {p}")
		Path(self.run_summary_file).write_text("\n".join(summary), encoding="utf-8")
		logger.info("Pro video run summary logged")


def main():
	gen = ProVideoGenerator()
	res = gen.run()
	print(f"[OK] Pro reels: {len(res)}")
	for k, v in res.items():
		print(f"{k}: {v}")


if __name__ == "__main__":
	main()

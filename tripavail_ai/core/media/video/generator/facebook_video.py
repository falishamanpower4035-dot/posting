"""
Facebook-Optimized Video Generator
Creates videos in Facebook's preferred aspect ratios: 16:9 (landscape) or 1:1 (square)
"""

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class FacebookVideoGenerator:
    def __init__(self, aspect_ratio: str = "16:9"):
        """
        Initialize Facebook video generator
        
        Args:
            aspect_ratio: "16:9" (landscape), "1:1" (square), or "9:16" (portrait)
        """
        self.data_dir = Path("data")
        self.videos_dir = self.data_dir / "videos"
        self.manifest_file = self.data_dir / "image_manifest.json"
        self.posts_file = self.data_dir / "posts.json"
        self.logs_dir = Path("logs")
        self.run_summary_file = self.logs_dir / "facebook_video_run_summary.txt"
        
        # Facebook-optimized dimensions
        self.aspect_ratio = aspect_ratio
        if aspect_ratio == "16:9":
            self.target_w, self.target_h = 1920, 1080  # Landscape - BEST for Facebook
        elif aspect_ratio == "1:1":
            self.target_w, self.target_h = 1080, 1080  # Square - Good for Facebook
        elif aspect_ratio == "9:16":
            self.target_w, self.target_h = 1080, 1920  # Portrait - Instagram/TikTok
        else:
            self.target_w, self.target_h = 1920, 1080  # Default to landscape
        
        self.fps = 30
        self.image_sec = 4.0  # Longer per image for landscape
        self.fade_sec = 1.0   # Longer fade for smoother transitions
        self.total_sec = 30.0  # Longer total duration for Facebook
        
        # Font and branding
        self.font_candidates = [
            str(Path("C:/Windows/Fonts/arial.ttf")),
            str(Path("C:/Windows/Fonts/Segoeui.ttf")),
        ]
        self.logo_path = Path("assets") / "tripavail_logo.png"
        self.audio_dir = Path("assets") / "audio"
        
        self._ensure_dirs()
        logger.info(f"FacebookVideoGenerator initialized - {aspect_ratio} ({self.target_w}x{self.target_h})")
    
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
                audio_path = self.audio_dir / name
                if audio_path.exists():
                    return str(audio_path)
        return None
    
    def _build_ffmpeg_cmd(self, post_id: str, images: List[str], hook_text: str) -> List[str]:
        """Build FFmpeg command for Facebook-optimized video"""
        num_images = len(images)
        if num_images == 0:
            raise ValueError("No images provided")
        
        # Input files
        inputs = []
        for img in images:
            inputs += ["-loop", "1", "-t", str(self.image_sec), "-i", img]
        
        # Optional voiceover
        vo_exists = False
        if post_id:
            vo_path = self.data_dir / "audio" / "voiceovers" / f"{post_id}.mp3"
            vo_exists = vo_path.exists()
            logger.info(f"Voiceover path: {vo_path}, exists: {vo_exists}")
            if vo_exists:
                inputs += ["-i", str(vo_path)]
        
        # Build filtergraph: scale each image, then crossfade
        filters = []
        
        # Scale and add Ken Burns effect for each image
        for i in range(num_images):
            # Ken Burns zoom effect - more subtle for landscape
            zoom_factor = 1.1 if self.aspect_ratio == "16:9" else 1.2
            zoom_filter = f"zoompan=z='min(zoom+0.0005,{zoom_factor})':d={int(self.image_sec * self.fps)}:s={self.target_w}x{self.target_h}:fps={self.fps}"
            filters.append(f"[{i}:v]scale={self.target_w}:{self.target_h}:force_original_aspect_ratio=decrease,pad={self.target_w}:{self.target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,{zoom_filter}[v{i}]")
        
        # Apply crossfade transitions between images
        if num_images == 1:
            filters.append("[v0]copy[vout]")
        else:
            current_label = "[v0]"
            for i in range(1, num_images):
                next_label = f"[v{i}]"
                output_label = f"[vt{i}]" if i < num_images - 1 else "[vout]"
                offset = self.image_sec - self.fade_sec
                filters.append(
                    f"{current_label}{next_label}xfade=transition=smoothleft:duration={self.fade_sec}:offset={offset * i}{output_label}"
                )
                current_label = output_label
        
        # Add hook text overlay (positioned for landscape/square)
        if hook_text:
            hook_sanitized = hook_text.encode('ascii', 'ignore').decode('ascii')
            hook_sanitized = hook_sanitized.replace('\\', '\\\\').replace(':', '\\:').replace("'", "'\\\\\\''")
            logger.info(f"Hook text: '{hook_sanitized}'")
            
            # Position text based on aspect ratio
            if self.aspect_ratio == "16:9":
                # Landscape: position at bottom third
                text_y = f"h-th-80"
                font_size = "60"
            elif self.aspect_ratio == "1:1":
                # Square: position at bottom
                text_y = f"h-th-60"
                font_size = "50"
            else:
                # Portrait: position at bottom
                text_y = f"h-th-120"
                font_size = "70"
            
            filters.append(
                f"[vout]drawtext=text='{hook_sanitized}'"
                f":fontsize={font_size}"
                f":fontcolor=white"
                f":bordercolor=black"
                f":borderw=3"
                f":box=1"
                f":boxcolor=black@0.7"
                f":boxborderw=15"
                f":x=(w-text_w)/2"
                f":y={text_y}"
                f":enable='between(t,0,5.0)'"
                f"[vt]"
            )
            final_output = "[vt]"
        else:
            final_output = "[vout]"
        
        # Audio mixing
        audio_filters = []
        if vo_exists:
            audio_filters.append(f"[{num_images}:a]volume=1.0[vo]")
            audio_filters.append(f"{final_output}[vo]amix=inputs=1:duration=first[aout]")
            final_audio = "[aout]"
        else:
            final_audio = "anull"
        
        # Combine all filters
        all_filters = filters + audio_filters
        
        # Output file
        output_file = self.videos_dir / f"facebook_{post_id}_{self.aspect_ratio.replace(':', 'x')}.mp4"
        
        # Build complete command
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(all_filters),
            "-map", final_output,
            "-map", final_audio,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-r", str(self.fps),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_file)
        ]
        
        return cmd
    
    def generate_for_post(self, post: Dict[str, Any]) -> Optional[Path]:
        """Generate Facebook-optimized video for a post"""
        try:
            post_id = post.get('topic_id', 'unknown')
            title = post.get('original_title', '')
            caption = post.get('caption', '')
            
            logger.info(f"Generating Facebook video for post {post_id} ({self.aspect_ratio})")
            
            # Load image manifest
            if not self.manifest_file.exists():
                logger.error("Image manifest not found")
                return None
            
            with open(self.manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Get images for this post - try both topic_id and post_id
            post_images = []
            if 'posts' in manifest:
                # New format: array of post objects
                for post_data in manifest['posts']:
                    if post_data.get('post_id') == int(post_id) or post_data.get('topic_id') == post_id:
                        post_images = post_data.get('image_paths', [])
                        break
            else:
                # Old format: direct mapping
                post_images = manifest.get(post_id, [])
            
            if not post_images:
                logger.error(f"Post {post_id}: no images found in manifest")
                return None
            
            # Limit images for Facebook (longer duration per image)
            max_images = 6 if self.aspect_ratio == "16:9" else 8
            images = post_images[:max_images]
            
            logger.info(f"Generating Facebook video for post {post_id} with {len(images)} images")
            
            # Create hook text from caption
            hook_text = caption.split('.')[0] if '.' in caption else caption[:50]
            
            # Build and run FFmpeg command
            cmd = self._build_ffmpeg_cmd(post_id, images, hook_text)
            
            logger.info(f"Running FFmpeg command for Facebook video...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return None
            
            # Find output file
            output_file = self.videos_dir / f"facebook_{post_id}_{self.aspect_ratio.replace(':', 'x')}.mp4"
            
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                logger.info(f"Generated Facebook video: {output_file.name} ({size_mb:.2f} MB)")
                return output_file
            else:
                logger.error("Output file not found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate Facebook video: {e}")
            return None
    
    def generate_all_formats(self, post: Dict[str, Any]) -> Dict[str, Path]:
        """Generate video in all Facebook-optimized formats"""
        formats = {}
        
        for aspect_ratio in ["16:9", "1:1"]:
            try:
                # Create generator for this aspect ratio
                generator = FacebookVideoGenerator(aspect_ratio)
                video_path = generator.generate_for_post(post)
                if video_path:
                    formats[aspect_ratio] = video_path
            except Exception as e:
                logger.error(f"Failed to generate {aspect_ratio} format: {e}")
        
        return formats


def main():
    """Test Facebook video generator"""
    print("\n" + "="*60)
    print("FACEBOOK VIDEO GENERATOR TEST")
    print("="*60 + "\n")
    
    # Load posts
    posts_file = Path("data/posts.json")
    if not posts_file.exists():
        print("ERROR: No posts.json found")
        return
    
    with open(posts_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    posts = data['posts']
    if not posts:
        print("ERROR: No posts found")
        return
    
    # Test with first post
    post = posts[0]
    post_id = post.get('topic_id')
    title = post.get('original_title', '')[:60]
    
    print(f"Testing with Post #{post_id}: {title}...")
    
    # Generate in different formats
    for aspect_ratio in ["16:9", "1:1"]:
        print(f"\nGenerating {aspect_ratio} format...")
        generator = FacebookVideoGenerator(aspect_ratio)
        video_path = generator.generate_for_post(post)
        
        if video_path:
            size_mb = video_path.stat().st_size / (1024 * 1024)
            print(f"SUCCESS: {video_path.name} ({size_mb:.2f} MB)")
        else:
            print(f"ERROR: Failed to generate {aspect_ratio} video")
    
    print("\n" + "="*60)
    print("FACEBOOK VIDEO TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()

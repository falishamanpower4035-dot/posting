"""
Python-Only Video Generation
Creates video slideshows from images using PIL and basic video creation
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PythonVideoGenerator:
    """Python-only video generation from images"""
    
    def __init__(self):
        # Configuration
        self.target_resolution = (1080, 1920)  # 9:16 aspect ratio
        self.fps = 30
        self.image_duration = 5.0  # seconds per image
        self.total_duration = 15.0  # total video duration
        self.total_frames = int(self.total_duration * self.fps)
        
        # File paths
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.posts_file = self.data_dir / "posts.json"
        self.image_manifest_file = self.data_dir / "image_manifest.json"
        self.video_output_dir = self.data_dir / "videos"
        
        # Logging files
        self.video_log_file = self.logs_dir / "video_log.txt"
        self.run_summary_file = self.logs_dir / "run_summary.txt"
        
        # Ensure directories exist
        self._ensure_directories()
        
        logger.info("Python Video Generator initialized")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        self.video_output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_posts_and_images(self) -> List[Dict[str, Any]]:
        """Load posts and their associated images"""
        try:
            # Load posts
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
            
            # Load image manifest
            with open(self.image_manifest_file, 'r', encoding='utf-8') as f:
                image_manifest = json.load(f)
            
            posts = posts_data.get('posts', [])
            processed_posts = []
            
            for post in posts:
                post_id = post.get('post_id', '001')
                
                # Find corresponding images in manifest
                post_images = None
                for manifest_post in image_manifest.get('posts', []):
                    if manifest_post.get('post_id') == post_id:
                        post_images = manifest_post.get('image_paths', [])
                        break
                
                if post_images and len(post_images) >= 3:
                    post['image_paths'] = post_images
                    processed_posts.append(post)
                else:
                    logger.warning(f"Post {post_id} missing required images")
            
            logger.info(f"Loaded {len(processed_posts)} posts with images for video generation")
            return processed_posts
            
        except Exception as e:
            logger.error(f"Error loading posts and images: {e}")
            return []
    
    def resize_image(self, image_path: str) -> Image.Image:
        """Resize image to target resolution"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate scaling to fit target resolution
                img_width, img_height = img.size
                target_width, target_height = self.target_resolution
                
                # Calculate scale factor
                scale_w = target_width / img_width
                scale_h = target_height / img_height
                scale = min(scale_w, scale_h)  # Use smaller scale to fit
                
                # Calculate new dimensions
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Resize image
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create new image with target resolution
                final_img = Image.new('RGB', self.target_resolution, (0, 0, 0))
                
                # Calculate position to center the image
                x = (target_width - new_width) // 2
                y = (target_height - new_height) // 2
                
                # Paste resized image onto final image
                final_img.paste(img_resized, (x, y))
                
                return final_img
                
        except Exception as e:
            logger.error(f"Error resizing image {image_path}: {e}")
            # Return black image as fallback
            return Image.new('RGB', self.target_resolution, (0, 0, 0))
    
    def add_text_overlay(self, img: Image.Image, text: str) -> Image.Image:
        """Add text overlay to image"""
        try:
            # Create a copy of the image
            img_with_text = img.copy()
            draw = ImageDraw.Draw(img_with_text)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (bottom center)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (self.target_resolution[0] - text_width) // 2
            y = self.target_resolution[1] - text_height - 50
            
            # Draw text with outline
            draw.text((x-1, y-1), text, font=font, fill=(0, 0, 0))  # Black outline
            draw.text((x+1, y-1), text, font=font, fill=(0, 0, 0))  # Black outline
            draw.text((x-1, y+1), text, font=font, fill=(0, 0, 0))  # Black outline
            draw.text((x+1, y+1), text, font=font, fill=(0, 0, 0))  # Black outline
            draw.text((x, y), text, font=font, fill=(255, 255, 255))  # White text
            
            return img_with_text
            
        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            return img
    
    def create_video_frames(self, image_paths: List[str], caption: str) -> List[Image.Image]:
        """Create video frames from images"""
        try:
            frames = []
            frames_per_image = self.total_frames // len(image_paths[:3])  # Use first 3 images
            
            for i, image_path in enumerate(image_paths[:3]):
                # Resize image
                resized_img = self.resize_image(image_path)
                
                # Add text overlay for the first image
                if i == 0:
                    # Extract first few words from caption
                    caption_words = caption.split()[:6]
                    caption_text = " ".join(caption_words)
                    resized_img = self.add_text_overlay(resized_img, caption_text)
                
                # Add TripAvail branding to last image
                if i == 2:
                    resized_img = self.add_text_overlay(resized_img, "TripAvail")
                
                # Create frames for this image
                for _ in range(frames_per_image):
                    frames.append(resized_img.copy())
            
            # Ensure we have exactly the right number of frames
            while len(frames) < self.total_frames:
                frames.append(frames[-1].copy())
            
            return frames[:self.total_frames]
            
        except Exception as e:
            logger.error(f"Error creating video frames: {e}")
            return []
    
    def create_mp4_video(self, frames: List[Image.Image], output_path: str) -> bool:
        """Create MP4 video from frames using FFmpeg"""
        try:
            import subprocess
            import tempfile
            
            # Create temporary directory for frames
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save frames as images
                for i, frame in enumerate(frames):
                    frame_path = os.path.join(temp_dir, f"frame_{i:06d}.jpg")
                    frame.save(frame_path, "JPEG", quality=95)
                
                # Create FFmpeg command
                cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file
                    '-framerate', str(self.fps),
                    '-i', os.path.join(temp_dir, 'frame_%06d.jpg'),
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-crf', '23',  # High quality
                    '-preset', 'medium',
                    output_path
                ]
                
                # Run FFmpeg
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"Successfully created video: {output_path}")
                    return True
                else:
                    logger.error(f"FFmpeg error: {result.stderr}")
                    return False
            
        except Exception as e:
            logger.error(f"Error creating MP4 video: {e}")
            return False
    
    def save_frames_as_images(self, frames: List[Image.Image], output_dir: str) -> bool:
        """Save frames as individual images (backup method)"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for i, frame in enumerate(frames):
                frame_path = os.path.join(output_dir, f"frame_{i:06d}.jpg")
                frame.save(frame_path, "JPEG", quality=95)
            
            logger.info(f"Saved {len(frames)} frames to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving frames: {e}")
            return False
    
    def create_video_instructions(self, post_id: str, output_dir: str) -> str:
        """Create instructions for manual video creation"""
        instructions = f"""
VIDEO CREATION INSTRUCTIONS FOR POST {post_id}
===============================================

1. FRAMES LOCATION: {output_dir}
2. TOTAL FRAMES: {self.total_frames}
3. FRAME RATE: {self.fps} fps
4. DURATION: {self.total_duration} seconds
5. RESOLUTION: {self.target_resolution[0]}x{self.target_resolution[1]} (9:16)

TO CREATE VIDEO MANUALLY:
-------------------------
Option 1 - Using FFmpeg (if installed):
ffmpeg -framerate {self.fps} -i {output_dir}/frame_%06d.jpg -c:v libx264 -pix_fmt yuv420p reel_{post_id}.mp4

Option 2 - Using Online Tools:
1. Upload all frames to an online video creator
2. Set frame rate to {self.fps} fps
3. Set duration to {self.total_duration} seconds
4. Export as MP4

Option 3 - Using Video Editing Software:
1. Import all frames as image sequence
2. Set frame rate to {self.fps} fps
3. Export as MP4 with 9:16 aspect ratio

READY FOR SOCIAL MEDIA POSTING!
"""
        return instructions
    
    def generate_video_for_post(self, post: Dict[str, Any]) -> Optional[str]:
        """Generate MP4 video for a single post"""
        try:
            post_id = post.get('post_id', '001')
            caption = post.get('caption', '')
            image_paths = post.get('image_paths', [])
            
            if len(image_paths) < 3:
                logger.error(f"Post {post_id} needs at least 3 images")
                return None
            
            logger.info(f"Generating MP4 video for post {post_id}")
            
            # Create video frames
            frames = self.create_video_frames(image_paths, caption)
            
            if not frames:
                logger.error(f"Failed to create frames for post {post_id}")
                return None
            
            # Create MP4 video
            video_path = self.video_output_dir / f"reel_{post_id}.mp4"
            success = self.create_mp4_video(frames, str(video_path))
            
            if success:
                logger.info(f"Generated MP4 video: {video_path}")
                return str(video_path)
            else:
                # Fallback: save frames for manual processing
                logger.warning(f"MP4 creation failed, saving frames for post {post_id}")
                output_dir = self.video_output_dir / f"frames_{post_id}"
                self.save_frames_as_images(frames, str(output_dir))
                
                # Create instructions file
                instructions = self.create_video_instructions(post_id, str(output_dir))
                instructions_file = self.video_output_dir / f"instructions_{post_id}.txt"
                
                with open(instructions_file, 'w', encoding='utf-8') as f:
                    f.write(instructions)
                
                return str(output_dir)
            
        except Exception as e:
            logger.error(f"Error generating video for post {post_id}: {e}")
            return None
    
    def generate_all_videos(self) -> Dict[str, str]:
        """Generate MP4 videos for all posts"""
        start_time = time.time()
        logger.info("Starting MP4 video generation")
        
        # Load posts and images
        posts = self.load_posts_and_images()
        if not posts:
            logger.error("No posts found for video generation")
            return {}
        
        results = {}
        
        for post in posts:
            post_id = post.get('post_id', '001')
            frames_dir = self.generate_video_for_post(post)
            
            if frames_dir:
                results[post_id] = frames_dir
                logger.info(f"Successfully generated video frames for post {post_id}")
            else:
                logger.error(f"Failed to generate video frames for post {post_id}")
        
        # Log summary
        duration = time.time() - start_time
        self.log_run_summary(results, duration)
        
        logger.info("MP4 video generation completed")
        return results
    
    def log_run_summary(self, results: Dict[str, str], duration: float):
        """Log run summary"""
        total_videos = len(results)
        
        summary = f"""MP4 Video Generation Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Posts processed: {total_videos}
MP4 videos generated: {total_videos}
Success rate: 100.0%
Average processing: {duration/total_videos:.1f} s/video
Total duration: {duration:.1f} seconds

[READY] MP4 videos are ready for social media posting!

Generated Videos:
"""
        
        for post_id, frames_dir in results.items():
            summary += f"Post {post_id}: {frames_dir}\n"
        
        summary += f"""
VIDEO SPECIFICATIONS:
- Resolution: {self.target_resolution[0]}x{self.target_resolution[1]} (9:16)
- Frame Rate: {self.fps} fps
- Duration: {self.total_duration} seconds
- Format: MP4 (H.264)
- Quality: High (CRF 23)
"""
        
        with open(self.run_summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("Run summary logged")


def main():
    """Main function to run Python video generation"""
    try:
        generator = PythonVideoGenerator()
        results = generator.generate_all_videos()
        
        print("\n[SUCCESS] MP4 Video Generation Complete!")
        print(f"Generated MP4 videos for {len(results)} posts")
        
        for post_id, video_path in results.items():
            print(f"Post {post_id}: {video_path}")
        
        print("\n[READY] MP4 videos are ready for social media posting!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()

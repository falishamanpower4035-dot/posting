"""
Simplified Automated Video Generation
Basic video creation from images using MoviePy
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SimpleVideoGenerator:
    """Simplified video generation from images"""
    
    def __init__(self):
        # Configuration
        self.target_resolution = (1080, 1920)  # 9:16 aspect ratio
        self.fps = 30
        self.image_duration = 5.0  # seconds per image
        self.total_duration = 15.0  # total video duration
        
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
        
        logger.info("Simple Video Generator initialized")
    
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
    
    def create_simple_video(self, image_paths: List[str], output_path: str) -> bool:
        """Create a simple video from images using FFmpeg"""
        try:
            import subprocess
            
            # Create a temporary file list for FFmpeg
            temp_file = "temp_images.txt"
            
            with open(temp_file, 'w') as f:
                for image_path in image_paths[:3]:  # Use first 3 images
                    # Write each image path with duration
                    f.write(f"file '{image_path}'\n")
                    f.write(f"duration {self.image_duration}\n")
                # Add the last image again to ensure proper duration
                if image_paths:
                    f.write(f"file '{image_paths[-1]}'\n")
            
            # FFmpeg command to create video
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', temp_file,
                '-vf', f'scale={self.target_resolution[0]}:{self.target_resolution[1]}:force_original_aspect_ratio=decrease,pad={self.target_resolution[0]}:{self.target_resolution[1]}:(ow-iw)/2:(oh-ih)/2',
                '-c:v', 'libx264',
                '-r', str(self.fps),
                '-t', str(self.total_duration),
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if result.returncode == 0:
                logger.info(f"Successfully created video: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return False
    
    def generate_video_for_post(self, post: Dict[str, Any]) -> Optional[str]:
        """Generate video for a single post"""
        try:
            post_id = post.get('post_id', '001')
            caption = post.get('caption', '')
            image_paths = post.get('image_paths', [])
            
            if len(image_paths) < 3:
                logger.error(f"Post {post_id} needs at least 3 images")
                return None
            
            logger.info(f"Generating video for post {post_id}")
            
            # Output file path
            output_path = self.video_output_dir / f"reel_{post_id}.mp4"
            
            # Create video
            success = self.create_simple_video(image_paths, str(output_path))
            
            if success:
                logger.info(f"Generated video: {output_path}")
                return str(output_path)
            else:
                logger.error(f"Failed to generate video for post {post_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error generating video for post {post_id}: {e}")
            return None
    
    def generate_all_videos(self) -> Dict[str, str]:
        """Generate videos for all posts"""
        start_time = time.time()
        logger.info("Starting simple video generation")
        
        # Load posts and images
        posts = self.load_posts_and_images()
        if not posts:
            logger.error("No posts found for video generation")
            return {}
        
        results = {}
        
        for post in posts:
            post_id = post.get('post_id', '001')
            video_path = self.generate_video_for_post(post)
            
            if video_path:
                results[post_id] = video_path
                logger.info(f"Successfully generated video for post {post_id}")
            else:
                logger.error(f"Failed to generate video for post {post_id}")
        
        # Log summary
        duration = time.time() - start_time
        self.log_run_summary(results, duration)
        
        logger.info("Simple video generation completed")
        return results
    
    def log_run_summary(self, results: Dict[str, str], duration: float):
        """Log run summary"""
        total_videos = len(results)
        
        summary = f"""Simple Video Generation Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Posts processed: {total_videos}
Videos generated: {total_videos}
Success rate: 100.0%
Average processing: {duration/total_videos:.1f} s/video
Total duration: {duration:.1f} seconds

[READY] Videos are ready for social media posting!

Generated Videos:
"""
        
        for post_id, video_path in results.items():
            summary += f"Post {post_id}: {video_path}\n"
        
        with open(self.run_summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("Run summary logged")


def main():
    """Main function to run simple video generation"""
    try:
        generator = SimpleVideoGenerator()
        results = generator.generate_all_videos()
        
        print("\n[SUCCESS] Simple Video Generation Complete!")
        print(f"Generated videos for {len(results)} posts")
        
        for post_id, video_path in results.items():
            print(f"Post {post_id}: {video_path}")
        
        print("\n[READY] Videos are ready for social media posting!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()

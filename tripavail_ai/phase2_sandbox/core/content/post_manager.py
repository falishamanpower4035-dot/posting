#!/usr/bin/env python3
"""
Post Manager - Organizes each post in its own isolated directory
Prevents content mixing and makes tracking easier
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class PostManager:
    """
    Manages individual post directories with isolated assets
    Each post gets its own folder with subfolders for images, audio, video
    """
    
    def __init__(self, base_dir: Path = Path("data/posts")):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"PostManager initialized: {self.base_dir}")
    
    def create_post_directory(self, post_id: str) -> Path:
        """
        Create a dedicated directory structure for a post
        
        Args:
            post_id: Unique post identifier (e.g., "001", "002")
        
        Returns:
            Path to the post directory
        """
        post_dir = self.base_dir / f"post_{post_id}"
        
        # Create directory structure
        (post_dir / "images").mkdir(parents=True, exist_ok=True)
        (post_dir / "audio").mkdir(parents=True, exist_ok=True)
        (post_dir / "video").mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created post directory: {post_dir}")
        return post_dir
    
    def get_post_directory(self, post_id: str) -> Path:
        """Get the directory for a post (create if doesn't exist)"""
        post_dir = self.base_dir / f"post_{post_id}"
        if not post_dir.exists():
            return self.create_post_directory(post_id)
        return post_dir
    
    def save_metadata(self, post_id: str, metadata: Dict[str, Any]) -> Path:
        """
        Save post metadata (caption, hashtags, score, etc.)
        
        CRITICAL: This method MERGES with existing metadata to preserve fields like 'posted_platforms'
        that may be updated by other processes (e.g., marking posts as posted)
        
        Args:
            post_id: Post identifier
            metadata: Dictionary with post data (will be merged with existing metadata)
        
        Returns:
            Path to metadata file
        """
        post_dir = self.get_post_directory(post_id)
        metadata_file = post_dir / "metadata.json"
        
        # CRITICAL: Load existing metadata first to preserve fields like 'posted_platforms'
        existing_metadata = self.get_metadata(post_id) or {}
        
        # Merge new metadata with existing (new values override existing ones)
        merged_metadata = {**existing_metadata, **metadata}
        
        # Add/update timestamps
        if 'created_at' not in merged_metadata:
            merged_metadata['created_at'] = datetime.now().isoformat()
        merged_metadata['updated_at'] = datetime.now().isoformat()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(merged_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata for post {post_id}")
        return metadata_file
    
    def get_metadata(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Load post metadata"""
        metadata_file = self.get_post_directory(post_id) / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata for post {post_id}: {e}")
            return None
    
    def get_images_dir(self, post_id: str) -> Path:
        """Get the images directory for a post"""
        return self.get_post_directory(post_id) / "images"
    
    def get_audio_dir(self, post_id: str) -> Path:
        """Get the audio directory for a post"""
        return self.get_post_directory(post_id) / "audio"
    
    def get_video_dir(self, post_id: str) -> Path:
        """Get the video directory for a post"""
        return self.get_post_directory(post_id) / "video"
    
    def get_voiceover_path(self, post_id: str) -> Path:
        """Get the voiceover file path"""
        return self.get_audio_dir(post_id) / "voiceover.mp3"
    
    def get_background_music_path(self, post_id: str) -> Path:
        """Get the background music file path"""
        return self.get_audio_dir(post_id) / "music.mp3"
    
    def get_draft_video_path(self, post_id: str) -> Path:
        """Get the draft video path (video-only, no audio)"""
        return self.get_video_dir(post_id) / "draft.mp4"
    
    def get_final_video_path(self, post_id: str) -> Path:
        """Get the final video path (video + mixed audio)"""
        return self.get_video_dir(post_id) / "final.mp4"
    
    def get_image_paths(self, post_id: str) -> List[Path]:
        """Get all image paths for a post"""
        images_dir = self.get_images_dir(post_id)
        
        if not images_dir.exists():
            return []
        
        # Get all image files
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
            images.extend(images_dir.glob(ext))
        
        return sorted(images)
    
    def add_image(self, post_id: str, source_image: Path, index: int = None) -> Path:
        """
        Add an image to the post's image directory
        
        Args:
            post_id: Post identifier
            source_image: Source image file path
            index: Optional index for naming (img_001.jpg)
        
        Returns:
            Path to the copied image
        """
        images_dir = self.get_images_dir(post_id)
        
        if index is not None:
            dest_name = f"img_{index:03d}{source_image.suffix}"
        else:
            # Auto-increment based on existing images
            existing = len(list(images_dir.glob("img_*")))
            dest_name = f"img_{existing+1:03d}{source_image.suffix}"
        
        dest_path = images_dir / dest_name
        shutil.copy2(source_image, dest_path)
        
        logger.debug(f"Added image to post {post_id}: {dest_name}")
        return dest_path
    
    def mark_as_posted(self, post_id: str, platform: str, post_url: str = None):
        """
        Mark a post as posted to a platform
        
        Args:
            post_id: Post identifier
            platform: Platform name (facebook, youtube, etc.)
            post_url: Optional URL of the post
        """
        metadata = self.get_metadata(post_id) or {}
        
        if 'posted_platforms' not in metadata:
            metadata['posted_platforms'] = {}
        
        metadata['posted_platforms'][platform] = {
            'posted_at': datetime.now().isoformat(),
            'url': post_url
        }
        
        self.save_metadata(post_id, metadata)
        logger.info(f"Marked post {post_id} as posted to {platform}")
    
    def is_posted(self, post_id: str, platform: str = None) -> bool:
        """
        Check if a post has been posted
        
        Args:
            post_id: Post identifier
            platform: Optional platform to check. If None, checks if posted to any platform
        
        Returns:
            True if posted, False otherwise
        """
        metadata = self.get_metadata(post_id)
        
        if not metadata or 'posted_platforms' not in metadata:
            return False
        
        if platform:
            return platform in metadata['posted_platforms']
        
        return len(metadata['posted_platforms']) > 0
    
    def get_all_posts(self) -> List[str]:
        """Get list of all post IDs"""
        if not self.base_dir.exists():
            return []
        
        posts = []
        for post_dir in self.base_dir.glob("post_*"):
            if post_dir.is_dir():
                post_id = post_dir.name.replace("post_", "")
                posts.append(post_id)
        
        return sorted(posts)
    
    def get_unposted_posts(self, platform: str = None) -> List[str]:
        """
        Get list of post IDs that haven't been posted yet
        
        Args:
            platform: Optional platform filter
        
        Returns:
            List of post IDs
        """
        all_posts = self.get_all_posts()
        return [pid for pid in all_posts if not self.is_posted(pid, platform)]
    
    def delete_post(self, post_id: str):
        """Delete a post directory and all its contents"""
        post_dir = self.base_dir / f"post_{post_id}"
        
        if post_dir.exists():
            shutil.rmtree(post_dir)
            logger.info(f"Deleted post directory: {post_dir}")
    
    def get_all_posts(self) -> List[str]:
        """Get list of all post IDs"""
        if not self.base_dir.exists():
            return []
        
        posts = []
        for post_dir in self.base_dir.glob("post_*"):
            if post_dir.is_dir():
                post_id = post_dir.name.replace("post_", "")
                posts.append(post_id)
        
        return sorted(posts)
    
    def get_used_news_urls(self) -> set:
        """
        Get set of all news URLs that have already been used to create posts
        
        Returns:
            Set of news URLs
        """
        used_urls = set()
        for post_id in self.get_all_posts():
            meta = self.get_metadata(post_id)
            if meta:
                url = meta.get('original_url') or meta.get('link')
                if url:
                    used_urls.add(url)
        return used_urls
    
    def get_used_news_titles(self) -> set:
        """
        Get set of all news titles that have already been used to create posts
        
        Returns:
            Set of news titles (normalized)
        """
        used_titles = set()
        for post_id in self.get_all_posts():
            meta = self.get_metadata(post_id)
            if meta:
                title = meta.get('original_title', '').strip()
                if title:
                    # Normalize title for comparison (lowercase, remove extra spaces)
                    normalized = ' '.join(title.lower().split())
                    used_titles.add(normalized)
        return used_titles
    
    def is_news_already_used(self, topic: Dict[str, Any]) -> bool:
        """
        Check if a news topic has already been used to create a post
        
        Args:
            topic: News topic dictionary with 'link' and/or 'title'
            
        Returns:
            True if already used, False otherwise
        """
        # Check by URL first (most reliable)
        url = topic.get('link') or topic.get('url')
        if url:
            used_urls = self.get_used_news_urls()
            if url in used_urls:
                return True
        
        # Check by title (normalized)
        title = topic.get('title', '').strip()
        if title:
            normalized_title = ' '.join(title.lower().split())
            used_titles = self.get_used_news_titles()
            if normalized_title in used_titles:
                return True
        
        return False
    
    def get_post_summary(self, post_id: str) -> Dict[str, Any]:
        """Get a summary of post assets"""
        post_dir = self.get_post_directory(post_id)
        metadata = self.get_metadata(post_id)
        images = self.get_image_paths(post_id)
        
        voiceover = self.get_voiceover_path(post_id)
        final_video = self.get_final_video_path(post_id)
        
        return {
            'post_id': post_id,
            'directory': str(post_dir),
            'metadata': metadata,
            'images_count': len(images),
            'has_voiceover': voiceover.exists(),
            'has_final_video': final_video.exists(),
            'is_posted': self.is_posted(post_id),
            'posted_platforms': metadata.get('posted_platforms', {}) if metadata else {}
        }


def main():
    """Test the PostManager"""
    logger.info("Testing PostManager...")
    
    pm = PostManager(Path("data/posts_test"))
    
    # Create a test post
    post_id = "001"
    pm.create_post_directory(post_id)
    
    # Save metadata
    metadata = {
        'topic_id': '001',
        'title': 'Test Travel Post',
        'caption': 'Amazing destination awaits!',
        'hashtags': ['#Travel', '#Adventure'],
        'score': 8
    }
    pm.save_metadata(post_id, metadata)
    
    # Display paths
    print(f"\nPost Directory: {pm.get_post_directory(post_id)}")
    print(f"Images Dir: {pm.get_images_dir(post_id)}")
    print(f"Voiceover Path: {pm.get_voiceover_path(post_id)}")
    print(f"Final Video Path: {pm.get_final_video_path(post_id)}")
    
    # Get summary
    summary = pm.get_post_summary(post_id)
    print(f"\nPost Summary:")
    print(json.dumps(summary, indent=2, default=str))
    
    # Clean up
    pm.delete_post(post_id)
    logger.info("Test complete!")


if __name__ == "__main__":
    main()


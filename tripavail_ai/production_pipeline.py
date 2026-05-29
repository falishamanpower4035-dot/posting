#!/usr/bin/env python3
"""
Production Pipeline - Clean, Organized Content Generation
Each post gets its own isolated directory structure
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import ffmpeg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa
from loguru import logger

from core.content.post_manager import PostManager
from core.content.story_analyzer import StoryAnalyzer
from core.content.generator.generate_caption import CaptionGenerator
from core.media.images.generator.hybrid_generator import HybridImageGenerator
# ElevenLabs music generation disabled - using archived music only
# from core.media.audio.elevenlabs_music import ElevenLabsMusicGenerator
from core.media.images.generator.gemini_thumbnail_generator import GeminiThumbnailGenerator
from core.media.video.generator.enhanced_voiceover import EnhancedVoiceoverGenerator
from core.media.video.generator.pro_video import ProVideoGenerator
from core.media.video.generator.mix_audio import AudioMixer
from core.media.video.generator.caption_generator import CaptionGenerator as VideoCaptionGenerator


class ProductionPipeline:
    """
    Production pipeline with isolated post directories
    Each post: data/posts/post_XXX/ with subfolders for images, audio, video
    """
    
    def __init__(self):
        self.post_manager = PostManager()
        self.story_analyzer = StoryAnalyzer()
        self.caption_gen = CaptionGenerator()
        self.image_gen = HybridImageGenerator()
        self.thumbnail_gen = GeminiThumbnailGenerator()  # ENHANCED: AI-powered thumbnails
        self.voiceover_gen = EnhancedVoiceoverGenerator()
        self.video_gen = ProVideoGenerator()
        self.audio_mixer = AudioMixer()
        # NOTE: ElevenLabs music generation disabled - using archived music only
        # self.music_gen = ElevenLabsMusicGenerator()  # DISABLED: Using archived music instead
        self.caption_gen_video = VideoCaptionGenerator()  # NEW: Caption generator for final videos
        
        # Configure for ULTRA PREMIUM QUALITY
        self.image_gen.set_image_quality("ultra")  # 100% JPEG, HD DALL-E, Ultra resolution
        logger.info("🚀 ULTRA PREMIUM QUALITY ENABLED: 100% JPEG, HD DALL-E, 60 FPS, 320k Audio")
        logger.info("🎨 ENHANCED THUMBNAILS: AI-powered prompts + multi-layer text + OCR validation")
        logger.info("🎵 BACKGROUND MUSIC: Using archived music only (saves 530 credits/post, no ElevenLabs generation)")
        logger.info("📝 TEXT OVERLAYS: Hook text (from frame 2) + Captions synced with voiceover")
        
        self.data_dir = Path("data")
        self.processed_news_file = self.data_dir / "processed_news.json"
        
        logger.info("Production Pipeline initialized with STORY-DRIVEN content system")
    
    def load_news_topics(self) -> List[Dict[str, Any]]:
        """Load processed news topics"""
        if not self.processed_news_file.exists():
            logger.error(f"Processed news file not found: {self.processed_news_file}")
            return []
        
        try:
            with open(self.processed_news_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            topics = data.get('top_tourism_stories', [])
            logger.info(f"Loaded {len(topics)} news topics")
            return topics
        
        except Exception as e:
            logger.error(f"Failed to load news topics: {e}")
            return []
    
    def generate_caption_for_topic(self, topic: Dict[str, Any], post_id: str) -> Dict[str, Any]:
        """
        Generate STORY-DRIVEN content for a news topic
        
        Args:
            topic: News topic dictionary
            post_id: Post identifier
        
        Returns:
            Post data with story analysis, caption, hashtags, and video parameters
        """
        logger.info(f"Analyzing story depth for post {post_id}...")
        
        try:
            # STEP 1: Analyze story to determine video parameters
            story_analysis = self.story_analyzer.analyze_story(topic)
            
            # STEP 2: Generate social media caption (for hashtags)
            social_result = self.caption_gen.generate_caption_with_openai(topic)
            
            # STEP 3: Combine into complete post data
            post_data = {
                'post_id': post_id,
                'topic_id': topic.get('topic_id', post_id),
                'original_title': topic.get('title', ''),
                'original_summary': topic.get('summary', ''),
                'original_url': topic.get('link') or topic.get('url', ''),  # CRITICAL: Save URL for duplicate detection
                'region': topic.get('region', 'Unknown'),
                'created_at': datetime.now().isoformat(),  # Add creation timestamp for auto-deletion
                'score': topic.get('score', 0),
                
                # IMPORTANT: Save voiceover_script for captions
                'voiceover_script': story_analysis.get('narrative_script', ''),
                
                # Story-driven content
                'duration': story_analysis.get('duration', 30),
                'image_count': story_analysis.get('image_count', 8),
                'story_beats': story_analysis.get('story_beats', []),
                'narrative_script': story_analysis.get('narrative_script', ''),
                'context_caption': story_analysis.get('context_caption', ''),
                'complexity': story_analysis.get('complexity', 'moderate'),
                'keywords': story_analysis.get('keywords', {}),
                'locations': story_analysis.get('locations', {}),
                
                # Social media elements
                'caption': story_analysis.get('context_caption', social_result.get('caption', '')),
                'hashtags': social_result.get('hashtags', []),
                'content_type': social_result.get('content_type', 'general')
            }
            
            # Save metadata to post directory
            self.post_manager.save_metadata(post_id, post_data)
            
            logger.info(f"Story-driven content generated for post {post_id}: {post_data['duration']}s, {post_data['image_count']} images")
            return post_data
        
        except Exception as e:
            logger.error(f"Failed to generate story content for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_images_for_post(self, post_data: Dict[str, Any]) -> bool:
        """
        Generate images based on STORY BEATS for a post
        
        Args:
            post_data: Post metadata
        
        Returns:
            True if successful, False otherwise
        """
        post_id = post_data['post_id']
        logger.info(f"Generating images for post {post_id}...")
        
        try:
            images_dir = self.post_manager.get_images_dir(post_id)
            
            # Use STORY-DRIVEN image generation
            has_story_beats = 'story_beats' in post_data and post_data['story_beats']
            
            if has_story_beats:
                logger.info(f"Using story beats for targeted image search (post {post_id})")
                success = self.image_gen.generate_for_post_with_story_beats(post_data, images_dir)
            else:
                logger.warning(f"No story beats available, using generic image search (post {post_id})")
                success = self.image_gen.generate_for_post(post_data)

            if not success:
                logger.error(f"Image generation failed for post {post_id}")
                return False

            # Verify images exist in the post directory
            generated_images = sorted(images_dir.glob("*.jpg"))
            
            if len(generated_images) == 0:
                logger.error(f"No images found in post directory for post {post_id}: {images_dir}")
                return False
            
            logger.info(f"Generated {len(generated_images)} images for post {post_id}")
            
            # Update metadata with actual image count
            metadata = self.post_manager.get_metadata(post_id)
            metadata['actual_image_count'] = len(generated_images)
            self.post_manager.save_metadata(post_id, metadata)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to generate images for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def adjust_image_count_for_voiceover(self, post_id: str) -> bool:
        """
        Intelligently adjust image count to match voiceover duration
        Adds more images if voiceover is longer than video would be
        
        Args:
            post_id: Post identifier
        
        Returns:
            True if adjustment successful, False otherwise
        """
        try:
            voiceover_path = self.post_manager.get_voiceover_path(post_id)
            if not voiceover_path.exists():
                logger.warning(f"Voiceover not found for post {post_id}, skipping adjustment")
                return False
            
            # Get voiceover duration
            from moviepy import AudioFileClip
            audio = AudioFileClip(str(voiceover_path))
            voiceover_duration = audio.duration
            audio.close()
            
            # Get current image count
            images = self.post_manager.get_image_paths(post_id)
            current_image_count = len(images)
            
            # Calculate optimal image count
            # Target: 3 seconds per image (comfortable viewing pace)
            target_image_sec = 3.0
            fade_sec = 0.8
            
            # Calculate how many images we need for this voiceover duration
            # Formula: duration = (images × target_sec) - ((images-1) × fade_sec)
            # Solving for images: images = (duration + fade_sec) / (target_sec - fade_sec)
            needed_images = int((voiceover_duration + fade_sec) / (target_image_sec - fade_sec))
            
            # Ensure minimum of 5 images
            needed_images = max(5, needed_images)
            
            logger.info(f"🎙️ Voiceover: {voiceover_duration:.1f}s | Current: {current_image_count} images | Needed: {needed_images} images")
            
            if current_image_count > needed_images:
                extra_images = current_image_count - needed_images
                logger.info(f"✂️ Voiceover shorter than image set. Trimming {extra_images} images so video matches narration.")

                keep_images = images[:needed_images]
                remove_images = images[needed_images:]

                for img_path in remove_images:
                    try:
                        img_path.unlink(missing_ok=False)
                        logger.debug(f"Removed extra image {img_path.name}")
                    except FileNotFoundError:
                        logger.debug(f"Extra image already removed: {img_path}")
                    except Exception as trim_err:
                        logger.warning(f"Failed to remove extra image {img_path}: {trim_err}")

                # Update metadata counts after trimming
                metadata = self.post_manager.get_metadata(post_id) or {}
                metadata['actual_image_count'] = len(keep_images)
                metadata['image_count'] = len(keep_images)
                self.post_manager.save_metadata(post_id, metadata)

                # Refresh image list for consistency logging
                images = self.post_manager.get_image_paths(post_id)
                current_image_count = len(images)
                logger.info(f"✅ Trimmed image set to {current_image_count} frames to match {voiceover_duration:.1f}s voiceover")
                return True

            if current_image_count == needed_images:
                logger.info(f"✅ Perfect image count ({current_image_count} images for {voiceover_duration:.1f}s voiceover)")
                return True
            
            # Need more images!
            additional_images = needed_images - current_image_count
            logger.warning(f"⚠️ Need {additional_images} more images to match voiceover duration!")
            
            # Generate additional images using story beats
            metadata = self.post_manager.get_metadata(post_id)
            story_beats = metadata.get('story_beats', [])
            
            if not story_beats:
                logger.error(f"No story beats available to generate more images for post {post_id}")
                return False
            
            # Expand story beats if needed
            if len(story_beats) < needed_images:
                logger.info(f"📝 Expanding story beats from {len(story_beats)} to {needed_images}")
                # Use StoryAnalyzer to request more beats
                from core.content.story_analyzer import StoryAnalyzer
                analyzer = StoryAnalyzer()
                
                # Re-analyze with desired image count
                topic = {
                    'title': metadata.get('original_title', ''),
                    'summary': metadata.get('original_summary', ''),
                    'region': metadata.get('region', 'Global')
                }
                
                # Force the analyzer to generate more images
                expanded_analysis = analyzer.analyze_story(topic)
                
                # If expanded analysis has more beats, use them
                if len(expanded_analysis.get('story_beats', [])) >= needed_images:
                    story_beats = expanded_analysis['story_beats'][:needed_images]
                    metadata['story_beats'] = story_beats
                    metadata['image_count'] = needed_images
                    self.post_manager.save_metadata(post_id, metadata)
                    logger.info(f"✅ Expanded to {len(story_beats)} story beats")
                else:
                    # Fallback: duplicate last few beats with variations
                    logger.info(f"📸 Generating additional image variations")
                    while len(story_beats) < needed_images:
                        # Add variations of existing beats
                        base_beat = story_beats[len(story_beats) % len(story_beats)]
                        story_beats.append(f"Alternative view: {base_beat}")
            
            # Generate the additional images
            logger.info(f"🎨 Generating {additional_images} additional images...")
            
            # Use only the additional beats we need
            additional_beats = story_beats[current_image_count:needed_images]
            
            success = self.image_gen.generate_additional_images_for_post(
                post_data=metadata,
                additional_beats=additional_beats,
                start_index=current_image_count
            )
            
            if success:
                logger.info(f"✅ Successfully generated {additional_images} additional images")
                # Update metadata
                metadata['actual_image_count'] = needed_images
                self.post_manager.save_metadata(post_id, metadata)
                return True
            else:
                logger.error(f"❌ Failed to generate additional images")
                return False
                
        except Exception as e:
            logger.error(f"Failed to adjust image count for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def generate_voiceover_for_post(self, post_id: str) -> bool:
        """
        Generate voiceover for a post
        
        Args:
            post_id: Post identifier
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating voiceover for post {post_id}...")
        
        try:
            metadata = self.post_manager.get_metadata(post_id)
            if not metadata:
                logger.error(f"No metadata found for post {post_id}")
                return False
            
            voiceover_path = self.post_manager.get_voiceover_path(post_id)
            
            # Use NARRATIVE SCRIPT from story analysis (not the caption!)
            narrative_script = metadata.get('narrative_script', '')
            
            selected_voice = None
            eleven_voice_id = None

            if narrative_script:
                logger.info(f"Using narrative script for voiceover (post {post_id})")
                
                # Determine content type for voice selection
                content_type = self.voiceover_gen._content_type_from_text(
                    narrative_script,
                    metadata.get('region', '')
                )
                logger.info(f"🎙️ Content type detected: {content_type} (post {post_id})")
                
                # Determine ElevenLabs voice if available
                if self.voiceover_gen.eleven_api_key:
                    if self.voiceover_gen.eleven_voice_map and content_type in self.voiceover_gen.eleven_voice_map:
                        eleven_voice_id = self.voiceover_gen.eleven_voice_map.get(content_type) or self.voiceover_gen.eleven_voice_id
                        logger.info(f"🎙️ Selected premium voice for '{content_type}': {eleven_voice_id[:8]}...")
                    else:
                        eleven_voice_id = self.voiceover_gen.eleven_voice_id
                        logger.info(f"🎙️ Using default voice (content_type '{content_type}' not in voice_map): {eleven_voice_id[:8]}...")
                else:
                    logger.warning("⚠️ ElevenLabs API key not configured - cannot use premium voices")
                
                # Select voice based on content analysis
                selected_voice = self.voiceover_gen.select_voice_for_content(
                    caption=narrative_script,
                    region=metadata.get('region', 'Unknown')
                )
                
                success = self.voiceover_gen.generate_voiceover(
                    text=narrative_script,
                    output_path=voiceover_path,
                    voice=selected_voice,  # Use AI-selected voice
                    speed=1.05,
                    eleven_voice_id=eleven_voice_id,
                    content_type=content_type  # Pass content type for voice selection
                )
            else:
                logger.warning(f"No narrative script, using caption (post {post_id})")
                # Fallback to old method
                fallback_caption = metadata.get('caption') or metadata.get('context_caption', '')
                if not fallback_caption:
                    logger.error(f"No caption available for fallback voiceover (post {post_id})")
                    return False

                content_type = self.voiceover_gen._content_type_from_text(
                    fallback_caption,
                    metadata.get('region', '')
                )
                if self.voiceover_gen.eleven_api_key:
                    if self.voiceover_gen.eleven_voice_map and content_type in self.voiceover_gen.eleven_voice_map:
                        eleven_voice_id = self.voiceover_gen.eleven_voice_map.get(content_type) or self.voiceover_gen.eleven_voice_id
                        logger.info(f"🎙️ Selected premium voice for fallback '{content_type}': {eleven_voice_id[:8]}...")
                    else:
                        eleven_voice_id = self.voiceover_gen.eleven_voice_id
                        logger.info(f"🎙️ Using default premium voice for fallback: {eleven_voice_id[:8]}...")
                else:
                    logger.warning("⚠️ ElevenLabs API key not configured - cannot use premium voices (fallback)")

                selected_voice = self.voiceover_gen.select_voice_for_content(
                    caption=fallback_caption,
                    region=metadata.get('region', 'Unknown')
                )

                script = self.voiceover_gen._create_voiceover_script(fallback_caption) or fallback_caption

                success = self.voiceover_gen.generate_voiceover(
                    text=script,
                    output_path=voiceover_path,
                    voice=selected_voice,
                    speed=1.05,
                    eleven_voice_id=eleven_voice_id,
                    content_type=content_type
                )
            
            if success:
                metadata['voiceover_voice'] = selected_voice or metadata.get('voiceover_voice')
                if eleven_voice_id:
                    metadata['voiceover_voice_id'] = eleven_voice_id
                    metadata['voiceover_provider'] = 'elevenlabs'
                else:
                    if selected_voice:
                        metadata['voiceover_voice_id'] = selected_voice
                    metadata['voiceover_provider'] = 'openai'
                self.post_manager.save_metadata(post_id, metadata)
                logger.info(f"Voiceover saved to {voiceover_path}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to generate voiceover for post {post_id}: {e}")
            return False
    
    def generate_music_for_post(self, post_id: str) -> bool:
        """
        Get background music for a post using archived music ONLY
        
        CRITICAL: This method ONLY uses archived music from MusicArchiveManager.
        ElevenLabs music generation is DISABLED to save API credits (530 credits per post).
        
        Args:
            post_id: Post identifier
            
        Returns:
            True if successful, False otherwise (proceeds without music if archive empty)
        """
        logger.info(f"🎵 Getting background music for post {post_id} from archive...")
        
        try:
            metadata = self.post_manager.get_metadata(post_id)
            if not metadata:
                logger.error(f"No metadata found for post {post_id}")
                return False
            
            # Get music output path
            music_path = self.post_manager.get_post_directory(post_id) / "audio" / "background_music.mp3"
            
            # CRITICAL: Use archived music ONLY (ElevenLabs generation disabled)
            from core.media.audio.music_archive_manager import MusicArchiveManager
            archive_manager = MusicArchiveManager()
            
            available_count = archive_manager.get_available_count()
            logger.info(f"📦 Archived music available: {available_count} files")
            
            if available_count > 0:
                # Use archived music (saves 530 credits per post!)
                logger.info(f"💰 Using archived music (saves 530 credits per post)")
                success = archive_manager.use_archived_music(music_path)
                if success:
                    logger.info(f"✅ Background music copied from archive for post {post_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Failed to copy archived music, proceeding without music")
                    return False
            else:
                logger.warning(f"⚠️ No archived music available in archive, proceeding WITHOUT background music")
                logger.warning(f"   (ElevenLabs generation is disabled - only archived music is used)")
                return False
        
        except Exception as e:
            logger.error(f"Failed to get music for post {post_id}: {e}")
            return False
    
    def _mix_audio_with_music(
        self, 
        draft_path: Path, 
        voiceover_path: Path, 
        music_path: Path, 
        final_path: Path,
        post_id: str
    ) -> bool:
        """
        Mix video with voiceover and background music
        
        Background music:
        - Plays for first 20 seconds only
        - Volume lowered to -18dB (so voiceover is clear)
        - Smooth fade out at 19-20 seconds
        
        Args:
            draft_path: Path to draft video (no audio)
            voiceover_path: Path to voiceover audio
            music_path: Path to background music (20 seconds)
            final_path: Output path for final video
            post_id: Post ID for logging
            
        Returns:
            True if successful, False otherwise
        """
        import subprocess
        
        try:
            # Check if music exists
            if music_path.exists():
                logger.info(f"🎵 Mixing with background music (first 20 seconds)")
                
                # Complex FFmpeg command with music
                # Filter: 
                # - [1:a] = voiceover (full length, normal volume)
                # - [2:a] = music (20 sec, -18dB, fade out at 19s)
                # - amix = mix them together
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(draft_path),          # [0] video
                    "-i", str(voiceover_path),      # [1] voiceover
                    "-i", str(music_path),          # [2] music
                    "-filter_complex",
                    "[2:a]volume=-18dB,afade=t=out:st=19:d=1[music];"  # Lower music volume, fade out
                    "[1:a][music]amix=inputs=2:duration=first[audio]",  # Mix voiceover + music
                    "-map", "0:v",                  # Use video from input 0
                    "-map", "[audio]",              # Use mixed audio
                    "-c:v", "copy",                 # Copy video codec
                    "-c:a", "aac",                  # AAC audio codec
                    "-b:a", "192k",                 # Audio bitrate
                    "-shortest",                    # End when shortest stream ends
                    str(final_path)
                ]
                
            else:
                logger.info(f"⚠️ No background music found, mixing with voiceover only")
                
                # Simple mix: video + voiceover
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(draft_path),
                    "-i", str(voiceover_path),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-shortest",
                    str(final_path)
                ]
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and final_path.exists():
                if music_path.exists():
                    logger.info(f"✅ Audio mixed: voiceover + background music (20s)")
                else:
                    logger.info(f"✅ Audio mixed: voiceover only")
                return True
            else:
                logger.error(f"FFmpeg mixing failed: {result.stderr[:200]}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to mix audio: {e}")
            return False
    
    def _add_captions_to_final_video(
        self, 
        video_path: Path, 
        post_id: str, 
        voiceover_path: Path
    ) -> Optional[Path]:
        """
        Add captions to final video synced with voiceover
        
        Args:
            video_path: Path to final video (with audio)
            post_id: Post identifier
            voiceover_path: Path to voiceover audio file
            
        Returns:
            Path to captioned video or None if failed
        """
        try:
            # Load post data to get voiceover script
            posts_file = self.data_dir / "posts.json"
            voiceover_script = None
            
            if posts_file.exists():
                with open(posts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for post in data.get("posts", []):
                    if str(post.get("topic_id")) == str(post_id):
                        voiceover_script = post.get("voiceover_script") or post.get("caption", "")
                        break
            
            if not voiceover_script:
                logger.warning(f"No voiceover script found for post {post_id}")
                return None
            
            # Get voiceover duration
            from moviepy import AudioFileClip
            with AudioFileClip(str(voiceover_path)) as audio:
                duration = audio.duration
            
            # Generate captions
            captioned_path = self.caption_gen_video.add_captions_to_video(
                video_path=video_path,
                voiceover_text=voiceover_script,
                voiceover_duration=duration
            )
            
            if captioned_path and captioned_path.exists():
                # Replace original with captioned version
                if captioned_path != video_path:
                    try:
                        video_path.unlink()  # Remove non-captioned
                        captioned_path.rename(video_path)  # Rename captioned to original name
                        logger.info(f"Replaced video with captioned version: {video_path}")
                    except Exception as e:
                        logger.error(f"Error replacing video: {e}")
                        return captioned_path
                
                return video_path
            
            logger.warning("Caption generation returned None")
            return None
            
        except Exception as e:
            logger.error(f"Failed to add captions: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_hook_text_overlay(self, video_path: Path, metadata: Dict[str, Any], post_id: str) -> Optional[Path]:
        """
        Add hook text overlay to video (same style as thumbnail)
        
        Hook text appears for first 8 seconds:
        - Large yellow text at top
        - Same font style as thumbnail
        - Eye-catching and retention-boosting
        
        Args:
            video_path: Path to video file
            metadata: Post metadata containing hook_text
            post_id: Post ID
            
        Returns:
            Path to video with text overlay, or None if failed
        """
        try:
            import subprocess
            
            # Get hook text from metadata
            hook_text = metadata.get('hook_text', '')
            
            if not hook_text:
                logger.warning(f"⚠️ No hook text found in metadata, skipping overlay")
                return video_path
            
            logger.info(f"📝 Adding hook text overlay: '{hook_text}'")
            
            # Output path
            output_path = video_path.parent / f"final_with_text_{post_id}.mp4"
            
            # Escape special characters for FFmpeg
            hook_text_escaped = hook_text.replace("'", "'\\\\\\''").replace(":", "\\:")
            
            # FFmpeg drawtext filter for large, bold, yellow text at top
            # Same styling as thumbnail: large font, yellow color, positioned at top
            drawtext_filter = (
                f"drawtext="
                f"text='{hook_text_escaped}':"
                f"fontfile=C\\:/Windows/Fonts/arialbd.ttf:"  # Bold Arial
                f"fontsize=80:"  # Large font
                f"fontcolor=yellow:"  # Same yellow as thumbnail
                f"borderw=4:"  # Thick border for readability
                f"bordercolor=black:"
                f"x=(w-text_w)/2:"  # Center horizontally
                f"y=100:"  # Position at top (same as thumbnail)
                f"enable='between(t,0,8)'"  # Show for first 8 seconds
            )
            
            # FFmpeg command with text overlay
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", drawtext_filter,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",  # High quality
                "-c:a", "copy",  # Copy audio
                str(output_path)
            ]
            
            logger.info(f"🎬 Applying text overlay with FFmpeg...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0 or not output_path.exists():
                logger.error(f"FFmpeg text overlay failed: {result.stderr[:300]}")
                return video_path  # Return original if overlay fails
            
            logger.info(f"✅ Hook text overlay added (visible for 8 seconds)")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to add text overlay: {e}")
            return video_path  # Return original on error

    def _apply_text_overlays_ffmpeg(self, video_path: Path, metadata: Dict[str, Any], voiceover_path: Path) -> Optional[Path]:
        """
        Apply hook (two centered lines) and captions using FFmpeg-Python.
        Returns path to overlaid video; returns original on failure.
        """
        try:
            # Determine hook text (prefer metadata.hook_text, fallback to thumbnails.hook_text)
            hook_text = metadata.get('hook_text') or metadata.get('thumbnails', {}).get('hook_text')
            if not hook_text:
                logger.warning("No hook text found; skipping overlay step")
                return video_path

            # Split hook into two lines: all but last word, then last word
            words = hook_text.split()
            if len(words) <= 1:
                line1 = hook_text
                line2 = ""
            else:
                line1 = " ".join(words[:-1])
                line2 = words[-1]

            # Probe voiceover duration for caption timing
            try:
                probe = ffmpeg.probe(str(voiceover_path))
                vo_duration = float(probe.get('format', {}).get('duration', 0))
            except Exception:
                vo_duration = 0

            voiceover_script = metadata.get('voiceover_script') or metadata.get('narrative_script', '')

            font_path = "C:/Windows/Fonts/arialbd.ttf"

            inp = ffmpeg.input(str(video_path))

            # Hook line 1
            hook1_opts = {
                'fontfile': font_path,
                'text': line1.replace("\\", "\\\\").replace(":", "\\:").replace("'", r"\'"),
                'fontsize': 68,
                'fontcolor': 'yellow',
                'borderw': 5,
                'bordercolor': 'black',
                'x': '(w-text_w)/2',
                'y': 'h*0.14',
                'enable': 'between(t,3,1e9)'
            }
            video_chain = inp.video.filter('drawtext', **hook1_opts)

            # Hook line 2
            if line2:
                hook2_opts = {
                    'fontfile': font_path,
                    'text': line2.replace("\\", "\\\\").replace(":", "\\:").replace("'", r"\'"),
                    'fontsize': 68,
                    'fontcolor': 'yellow',
                    'borderw': 5,
                    'bordercolor': 'black',
                    'x': '(w-text_w)/2',
                    'y': 'h*0.21',
                    'enable': 'between(t,3,1e9)'
                }
                video_chain = video_chain.filter('drawtext', **hook2_opts)

            # Captions (3 words per caption) if script and duration are present
            if voiceover_script and vo_duration > 0:
                words = voiceover_script.split()
                if words:
                    time_per_word = vo_duration / len(words)
                    for i in range(0, len(words), 3):
                        start = i * time_per_word
                        end = min((i + 3) * time_per_word, 1e9)
                        cap_text = " ".join(words[i:i+3]).upper()
                        cap_opts = {
                            'fontfile': font_path,
                            'text': cap_text.replace("\\", "\\\\").replace(":", "\\:").replace("'", r"\'"),
                            'fontsize': 54,
                            'fontcolor': 'white',
                            'borderw': 4,
                            'bordercolor': 'black',
                            'x': '(w-text_w)/2',
                            'y': 'h-220',
                            'enable': f"between(t,{start:.3f},{end:.3f})"
                        }
                        video_chain = video_chain.filter('drawtext', **cap_opts)

            output_path = video_path.parent / 'final_with_overlays.mp4'
            out = ffmpeg.output(
                video_chain, inp.audio,
                str(output_path), vcodec='libx264', acodec='aac', preset='medium', pix_fmt='yuv420p'
            )
            ffmpeg.run(out, overwrite_output=True)

            if output_path.exists():
                return output_path
            return video_path
        except Exception as e:
            logger.error(f"Failed to apply text overlays via FFmpeg-Python: {e}")
            return video_path
    
    def _add_thumbnail_intro(self, draft_path: Path, thumbnail_path: Path, post_id: str) -> Optional[Path]:
        """
        Add thumbnail as a 2-second intro to the video
        
        Args:
            draft_path: Path to draft video
            thumbnail_path: Path to thumbnail image
            post_id: Post ID
            
        Returns:
            Path to new video with thumbnail intro, or None if failed
        """
        try:
            import subprocess
            
            # Output path for video with thumbnail intro
            output_path = draft_path.parent / f"draft_with_thumb_{post_id}.mp4"
            
            # Step 1: Create 2-second video from thumbnail
            thumb_video = draft_path.parent / f"thumb_intro_{post_id}.mp4"
            
            cmd_thumb = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(thumbnail_path),
                "-c:v", "libx264",
                "-t", "1.5",  # 1.5 seconds freeze (matches video generator)
                "-pix_fmt", "yuv420p",
                "-r", "30",  # Match 30 FPS (same as video generator)
                "-vf", "scale=1080:1920",  # 9:16 format
                str(thumb_video)
            ]
            
            result = subprocess.run(cmd_thumb, capture_output=True, text=True)
            if result.returncode != 0 or not thumb_video.exists():
                logger.error(f"Failed to create thumbnail video: {result.stderr[:200]}")
                return None
            
            logger.info(f"✅ Created 2-second thumbnail video")
            
            # Step 2: Create concat file for ffmpeg
            concat_file = draft_path.parent / f"concat_{post_id}.txt"
            with open(concat_file, 'w') as f:
                f.write(f"file '{thumb_video.absolute()}'\n")
                f.write(f"file '{draft_path.absolute()}'\n")
            
            # Step 3: Concatenate thumbnail video + draft video
            cmd_concat = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path)
            ]
            
            result = subprocess.run(cmd_concat, capture_output=True, text=True)
            
            # Cleanup temp files
            if thumb_video.exists():
                thumb_video.unlink()
            if concat_file.exists():
                concat_file.unlink()
            
            if result.returncode != 0 or not output_path.exists():
                logger.error(f"Failed to concatenate videos: {result.stderr[:200]}")
                return None
            
            logger.info(f"✅ Concatenated thumbnail intro + video")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to add thumbnail intro: {e}")
            return None
    
    def generate_video_for_post(self, post_id: str) -> bool:
        """
        Generate video for a post (draft + final with audio)
        
        Args:
            post_id: Post identifier
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating video for post {post_id}...")
        
        try:
            metadata = self.post_manager.get_metadata(post_id)
            if not metadata:
                logger.error(f"No metadata found for post {post_id}")
                return False
            
            # Get image paths
            images = self.post_manager.get_image_paths(post_id)
            if not images:
                logger.error(f"No images found for post {post_id}")
                return False
            
            # Generate draft video (video-only)
            hook_text = metadata.get('caption', '')[:100]  # First 100 chars as hook
            draft_path = self.post_manager.get_draft_video_path(post_id)
            
            # TODO: Update pro_video.py to use custom paths
            # For now, use existing video generator
            # Optional: allow target duration override for special runs
            target_override_env = os.getenv("TARGET_DURATION_SEC")
            if target_override_env:
                try:
                    metadata["target_duration_sec"] = float(target_override_env)
                except Exception:
                    pass

            success = self.video_gen.generate_for_post(metadata)
            
            if success:
                # Move generated video
                default_video_path = Path(f"data/videos/reel_{post_id}_pro.mp4")
                if default_video_path.exists():
                    import shutil
                    shutil.move(str(default_video_path), str(draft_path))
                    logger.info(f"Draft video saved to {draft_path}")
                    
                    # NOTE: First frame freeze is now handled in pro_video.py
                    # The first image is frozen for 1.5 seconds (no zoom) to ensure YouTube picks it as thumbnail
                    # This happens automatically during video generation - no additional processing needed
                    logger.info(f"📸 First frame freeze active (first image frozen for 1.5s for YouTube thumbnail)")
                    
                    # Mix audio with background music and voiceover
                    final_path = self.post_manager.get_final_video_path(post_id)
                    voiceover_path = self.post_manager.get_voiceover_path(post_id)
                    music_path = self.post_manager.get_post_directory(post_id) / "audio" / "background_music.mp3"
                    
                    if voiceover_path.exists() and draft_path.exists():
                        # Mix with background music (if available)
                        success = self._mix_audio_with_music(
                            draft_path, voiceover_path, music_path, final_path, post_id
                        )
                        
                        if success:
                            logger.info(f"Final video saved to {final_path}")
                            
                            # Apply hook (two-line centered) + captions using FFmpeg-Python
                            logger.info(f"\n📝 Applying hook + captions overlays...")
                            overlaid_path = self._apply_text_overlays_ffmpeg(
                                final_path, metadata, voiceover_path
                            )
                            if overlaid_path and overlaid_path != final_path:
                                import shutil
                                shutil.move(str(overlaid_path), str(final_path))
                                logger.info("✅ Hook + captions overlays applied")
                            
                            # Skip platform renditions - only generate 9:16 videos
                            logger.info("Skipping platform renditions - only 9:16 format needed")
                            return True
                        else:
                            logger.error(f"Audio mixing failed")
                            return False
                    else:
                        logger.error(f"Missing assets: draft={draft_path.exists()}, voiceover={voiceover_path.exists()}")
                        return False
            
            return False
        
        except Exception as e:
            logger.error(f"Failed to generate video for post {post_id}: {e}")
            return False

    def _derive_platform_renditions(self, source_path: Path, post_id: str):
        """Create 1:1 and 16:9 renditions from the 9:16 source for platforms."""
        import subprocess
        video_dir = self.post_manager.get_video_dir(post_id)
        out_square = video_dir / "final_1x1.mp4"
        out_land = video_dir / "final_16x9.mp4"

        # 1:1 square 1080x1080: scale to height 1080 then pad width to 1080
        cmd_square = [
            "ffmpeg", "-y", "-i", str(source_path),
            "-vf", "scale=-2:1080,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            str(out_square)
        ]
        res1 = subprocess.run(cmd_square, capture_output=True, text=True)
        if res1.returncode == 0 and out_square.exists():
            logger.info(f"Derived square rendition: {out_square}")
        else:
            logger.error(f"Square rendition failed: {res1.stderr[:200]}")

        # 16:9 landscape 1920x1080: scale to height 1080 then pad width to 1920
        cmd_land = [
            "ffmpeg", "-y", "-i", str(source_path),
            "-vf", "scale=-2:1080,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            str(out_land)
        ]
        res2 = subprocess.run(cmd_land, capture_output=True, text=True)
        if res2.returncode == 0 and out_land.exists():
            logger.info(f"Derived landscape rendition: {out_land}")
        else:
            logger.error(f"Landscape rendition failed: {res2.stderr[:200]}")
    
    def process_single_post(self, topic: Dict[str, Any], post_index: int) -> bool:
        """
        Process a single news topic into a complete post
        
        Args:
            topic: News topic data
            post_index: Index for post ID (1, 2, 3...)
        
        Returns:
            True if successful, False otherwise
        """
        post_id = f"{post_index:03d}"
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Post {post_id}")
        logger.info(f"{'='*60}")
        
        # Step 1: Generate caption
        post_data = self.generate_caption_for_topic(topic, post_id)
        if not post_data:
            logger.error(f"Failed to generate caption for post {post_id}")
            return False
        
        # Step 2: Generate initial images
        if not self.generate_images_for_post(post_data):
            logger.error(f"Failed to generate images for post {post_id}")
            return False
        
        # Step 3: Generate voiceover
        if not self.generate_voiceover_for_post(post_id):
            logger.error(f"Failed to generate voiceover for post {post_id}")
            return False
        
        # Step 3.5: Get background music from archive (ARCHIVED MUSIC ONLY - ElevenLabs disabled)
        logger.info(f"\n🎵 Step 3.5: Getting background music from archive...")
        self.generate_music_for_post(post_id)  # Uses archived music only - saves 530 credits
        
        # Step 3.6: INTELLIGENT IMAGE ADJUSTMENT
        # Check if we need more images to match voiceover duration
        logger.info(f"\n🎯 Step 3.6: Intelligent image count adjustment...")
        self.adjust_image_count_for_voiceover(post_id)
        
        # Step 4: Generate thumbnails (MOVED HERE - before video!)
        # This ensures hook_text is available for video overlay
        logger.info(f"\n🎨 Step 4: Generating thumbnails...")
        if not self.generate_thumbnails_for_post(post_id):
            logger.warning(f"Failed to generate thumbnails for post {post_id} (continuing...)")
        
        # Step 5: Generate video (NOW hook_text is available!)
        logger.info(f"\n🎬 Step 5: Generating video with all features...")
        if not self.generate_video_for_post(post_id):
            logger.error(f"Failed to generate video for post {post_id}")
            return False
        
        logger.info(f"✅ Post {post_id} completed successfully!")
        return True
    
    def generate_thumbnails_for_post(self, post_id: str) -> bool:
        """Generate thumbnails for YouTube and Facebook using Stability AI SDXL"""
        logger.info(f"🎨 Generating thumbnails for post {post_id}...")
        
        try:
            # Get post metadata
            metadata = self.post_manager.get_metadata(post_id)
            if not metadata:
                logger.error(f"No metadata found for post {post_id}")
                return False
            
            # Generate thumbnails
            thumbnails = self.thumbnail_gen.generate_thumbnail_for_post(post_id, metadata)
            
            if thumbnails:
                # Update metadata with thumbnail paths
                metadata['thumbnails'] = thumbnails
                self.post_manager.save_metadata(post_id, metadata)
                
                logger.info(f"✅ Generated {len(thumbnails)} thumbnails for post {post_id}")
                for platform, path in thumbnails.items():
                    logger.info(f"  {platform}: {path}")
                
                # CRITICAL: Copy thumbnail as first image so YouTube picks it automatically
                # The thumbnail becomes the first frame (frozen for 1.5s in pro_video.py)
                thumbnail_path = thumbnails.get('vertical')
                if thumbnail_path:
                    thumbnail_path = Path(thumbnail_path)
                    if thumbnail_path.exists():
                        images_dir = self.post_manager.get_images_dir(post_id)
                        images_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Copy thumbnail as img_000.jpg (sorts first, becomes first frame)
                        first_image_path = images_dir / "img_000.jpg"
                        import shutil
                        shutil.copy2(thumbnail_path, first_image_path)
                        logger.info(f"📸 Copied thumbnail as first image: {first_image_path.name}")
                        logger.info(f"   YouTube will automatically pick this as thumbnail (first frame freeze)")
                
                return True
            else:
                logger.error(f"Failed to generate thumbnails for post {post_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating thumbnails for post {post_id}: {e}")
            return False
    
    def run(self, max_posts: int = 5):
        """
        Run the complete production pipeline
        
        Args:
            max_posts: Maximum number of posts to generate
        """
        logger.info("Starting Production Pipeline...")
        
        # Load news topics
        topics = self.load_news_topics()
        if not topics:
            logger.error("No topics to process")
            return
        
        # Filter by score >= 7
        quality_topics = [t for t in topics if t.get('score', 0) >= 7]
        logger.info(f"Found {len(quality_topics)} quality topics (score >= 7)")
        
        # Process each topic
        successful_posts = []
        failed_posts = []
        
        for i, topic in enumerate(quality_topics[:max_posts], start=1):
            success = self.process_single_post(topic, i)
            
            if success:
                successful_posts.append(f"{i:03d}")
            else:
                failed_posts.append(f"{i:03d}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("PRODUCTION PIPELINE SUMMARY")
        logger.info("="*60)
        logger.info(f"Successful Posts: {len(successful_posts)} - {successful_posts}")
        logger.info(f"Failed Posts: {len(failed_posts)} - {failed_posts}")
        logger.info("="*60)


def main():
    """Run the production pipeline"""
    pipeline = ProductionPipeline()
    pipeline.run(max_posts=3)  # Generate 3 posts


if __name__ == "__main__":
    main()


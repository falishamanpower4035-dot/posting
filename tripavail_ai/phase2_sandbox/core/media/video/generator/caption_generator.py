#!/usr/bin/env python3
"""
Caption Generator for TripAvail AI Videos
Generates word-level captions synced with voiceover audio
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import re


class CaptionGenerator:
    """
    Generates captions for videos synced with voiceover
    """
    
    def __init__(self):
        self.data_dir = Path("data")
        self.audio_dir = self.data_dir / "audio" / "voiceovers"
        
        # Caption styling
        # Use Windows font file path directly for compatibility
        self.font = r'C:\Windows\Fonts\arial.ttf'
        self.fontsize = 60
        self.fontcolor = "yellow"
        self.stroke_color = "black"
        self.stroke_width = 3
        self.bg_color = "rgba(0, 0, 0, 0.7)"  # Semi-transparent black background
        
        # Caption positioning
        self.position = "bottom"  # top, center, or bottom
        self.y_offset = 200  # Distance from bottom
        
        # Caption timing (words per caption)
        self.words_per_caption = 3  # Show 3 words at a time
        
        logger.info("Caption Generator initialized")
    
    def estimate_word_timings(
        self, 
        text: str, 
        duration: float
    ) -> List[Dict[str, Any]]:
        """
        Estimate word-level timings from text and duration
        
        Args:
            text: Voiceover text
            duration: Total audio duration
            
        Returns:
            List of word timing dicts with 'word', 'start', 'end'
        """
        # Split text into words
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        # Calculate average time per word
        time_per_word = duration / total_words
        
        word_timings = []
        for i, word in enumerate(words):
            start_time = i * time_per_word
            end_time = (i + 1) * time_per_word
            
            word_timings.append({
                'word': word,
                'start': start_time,
                'end': end_time,
                'index': i
            })
        
        logger.info(f"Generated {len(word_timings)} word timings for {duration:.2f}s audio")
        return word_timings
    
    def create_caption_groups(
        self, 
        word_timings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group words into caption segments
        
        Args:
            word_timings: List of word timing dicts
            
        Returns:
            List of caption group dicts with 'text', 'start', 'end'
        """
        caption_groups = []
        
        for i in range(0, len(word_timings), self.words_per_caption):
            # Get words for this caption
            group_words = word_timings[i:i + self.words_per_caption]
            
            if not group_words:
                continue
            
            # Combine words
            caption_text = ' '.join([w['word'] for w in group_words])
            start_time = group_words[0]['start']
            end_time = group_words[-1]['end']
            
            caption_groups.append({
                'text': caption_text,
                'start': start_time,
                'end': end_time
            })
        
        logger.info(f"Created {len(caption_groups)} caption groups")
        return caption_groups
    
    def create_caption_clip(
        self,
        text: str,
        start_time: float,
        end_time: float,
        video_size: Tuple[int, int]
    ) -> Optional[TextClip]:
        """
        Create a single caption clip
        
        Args:
            text: Caption text
            start_time: Start time in seconds
            end_time: End time in seconds
            video_size: Video dimensions (width, height)
            
        Returns:
            TextClip or None if failed
        """
        try:
            duration = end_time - start_time
            
            # Create text clip
            txt_clip = TextClip(
                text=text,
                font=self.font,
                font_size=self.fontsize,
                color=self.fontcolor,
                stroke_color=self.stroke_color,
                stroke_width=self.stroke_width,
                method='caption',
                size=(video_size[0] - 100, None),
                text_align='center'
            ).with_duration(duration).with_start(start_time)
            
            # Position based on setting
            if self.position == "top":
                txt_clip = txt_clip.with_position(("center", 100))
            elif self.position == "center":
                txt_clip = txt_clip.with_position("center")
            else:  # bottom
                txt_clip = txt_clip.with_position(("center", video_size[1] - self.y_offset))
            
            return txt_clip
            
        except Exception as e:
            logger.error(f"Failed to create caption clip: {e}")
            return None
    
    def add_captions_to_video(
        self,
        video_path: Path,
        voiceover_text: str,
        voiceover_duration: float,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Add captions to a video based on voiceover
        
        Args:
            video_path: Path to input video
            voiceover_text: Voiceover script text
            voiceover_duration: Duration of voiceover audio
            output_path: Optional output path (defaults to video_path with _captioned suffix)
            
        Returns:
            Path to captioned video or None if failed
        """
        try:
            # Load video
            video = VideoFileClip(str(video_path))
            video_size = video.size
            
            # Generate word timings
            word_timings = self.estimate_word_timings(voiceover_text, voiceover_duration)
            
            if not word_timings:
                logger.warning("No word timings generated, returning original video")
                return video_path
            
            # Create caption groups
            caption_groups = self.create_caption_groups(word_timings)
            
            # Create caption clips
            caption_clips = []
            for group in caption_groups:
                clip = self.create_caption_clip(
                    text=group['text'],
                    start_time=group['start'],
                    end_time=group['end'],
                    video_size=video_size
                )
                if clip:
                    caption_clips.append(clip)
            
            if not caption_clips:
                logger.warning("No caption clips created, returning original video")
                video.close()
                return video_path
            
            # Composite video with captions
            logger.info(f"Compositing {len(caption_clips)} caption clips...")
            final_video = CompositeVideoClip([video] + caption_clips)
            
            # Determine output path
            if output_path is None:
                output_path = video_path.with_name(
                    video_path.name.replace('.mp4', '_captioned.mp4')
                )
            
            # Write video
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                fps=video.fps,
                preset='medium',
                bitrate='8000k'
            )
            
            # Clean up
            video.close()
            final_video.close()
            
            logger.info(f"✅ Captions added: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to add captions to video: {e}")
            return None
    
    def generate_for_post(
        self,
        post_id: str,
        video_path: Path,
        voiceover_script: str,
        voiceover_duration: float
    ) -> Optional[Path]:
        """
        Generate captions for a specific post
        
        Args:
            post_id: Post identifier
            video_path: Path to video file
            voiceover_script: Voiceover script text
            voiceover_duration: Duration of voiceover
            
        Returns:
            Path to captioned video or None
        """
        logger.info(f"Generating captions for post {post_id}...")
        
        output_path = video_path.with_name(f"reel_{post_id}_captioned.mp4")
        
        return self.add_captions_to_video(
            video_path=video_path,
            voiceover_text=voiceover_script,
            voiceover_duration=voiceover_duration,
            output_path=output_path
        )


def main():
    """Test caption generator"""
    generator = CaptionGenerator()
    
    print("\n=== Caption Generator Test ===")
    
    # Test word timing estimation
    test_text = "Discover the stunning beaches of Maldives where crystal clear waters and pristine white sand await your arrival"
    duration = 12.0
    
    word_timings = generator.estimate_word_timings(test_text, duration)
    print(f"\nGenerated {len(word_timings)} word timings:")
    for timing in word_timings[:5]:
        print(f"  {timing['word']}: {timing['start']:.2f}s - {timing['end']:.2f}s")
    
    # Test caption grouping
    caption_groups = generator.create_caption_groups(word_timings)
    print(f"\nGenerated {len(caption_groups)} caption groups:")
    for i, group in enumerate(caption_groups[:3], 1):
        print(f"  {i}. [{group['start']:.2f}s - {group['end']:.2f}s]: {group['text']}")
    
    print("\n✅ Caption generator test complete")


if __name__ == "__main__":
    main()


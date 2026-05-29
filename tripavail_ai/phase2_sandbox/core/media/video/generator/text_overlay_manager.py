#!/usr/bin/env python3
"""
Advanced Text Overlay Manager for TripAvail AI
Handles animated text, subtitles, keyword highlighting, and CTAs
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from loguru import logger
from moviepy import TextClip, CompositeVideoClip, VideoClip
import re


class TextOverlayManager:
    """
    Manages advanced text overlays for videos including:
    - Animated text with motion graphics
    - Subtitle generation with timing
    - Keyword highlighting
    - Call-to-action overlays
    """
    
    def __init__(self):
        self.default_font = "Arial-Bold"
        self.default_fontsize = 60
        self.default_color = "white"
        self.default_stroke_color = "black"
        self.default_stroke_width = 2
        
        # CTA templates
        self.cta_templates = {
            "book_now": "BOOK NOW ✈️",
            "learn_more": "Learn More 👆",
            "swipe_up": "Swipe Up ⬆️",
            "visit_website": "Visit TripAvail.com 🌍",
            "plan_trip": "Plan Your Trip 🗺️",
            "discover": "Discover More ✨",
            "follow": "Follow for More 📱"
        }
        
        logger.info("Text Overlay Manager initialized")
    
    def create_title_overlay(
        self,
        text: str,
        duration: float,
        video_size: Tuple[int, int],
        position: str = "top",
        fontsize: int = 70,
        animation: str = "fade_in"
    ) -> TextClip:
        """
        Create animated title overlay
        
        Args:
            text: Title text
            duration: Duration in seconds
            video_size: Video dimensions (width, height)
            position: Position on screen (top, center, bottom)
            fontsize: Font size
            animation: Animation type (fade_in, slide_in, zoom_in)
            
        Returns:
            TextClip with animation
        """
        try:
            # Create text clip
            txt_clip = TextClip(
                text=text,
                font=self.default_font,
                font_size=fontsize,
                color=self.default_color,
                stroke_color=self.default_stroke_color,
                stroke_width=self.default_stroke_width,
                method='caption',
                size=(video_size[0] - 100, None),
                text_align='center'
            ).with_duration(duration)
            
            # Set position
            if position == "top":
                txt_clip = txt_clip.with_position(("center", 100))
            elif position == "center":
                txt_clip = txt_clip.with_position("center")
            elif position == "bottom":
                txt_clip = txt_clip.with_position(("center", video_size[1] - 200))
            
            # Apply animation
            if animation == "fade_in":
                txt_clip = txt_clip.with_effects([
                    lambda clip: clip.with_effects([
                        ("fadein", 0.5)
                    ])
                ])
            elif animation == "slide_in":
                # Slide in from left
                txt_clip = txt_clip.with_position(
                    lambda t: (min(video_size[0]/2, -video_size[0] + video_size[0] * t * 2), 100)
                    if t < 0.5 else ("center", 100)
                )
            
            return txt_clip
            
        except Exception as e:
            logger.error(f"Failed to create title overlay: {e}")
            return None
    
    def create_subtitle_overlays(
        self,
        subtitle_data: List[Dict[str, Any]],
        video_size: Tuple[int, int],
        fontsize: int = 50
    ) -> List[TextClip]:
        """
        Create subtitle overlays with timing
        
        Args:
            subtitle_data: List of subtitle dicts with 'text', 'start', 'end'
            video_size: Video dimensions
            fontsize: Font size for subtitles
            
        Returns:
            List of positioned TextClips
        """
        subtitle_clips = []
        
        try:
            for subtitle in subtitle_data:
                text = subtitle['text']
                start_time = subtitle['start']
                end_time = subtitle['end']
                duration = end_time - start_time
                
                # Create subtitle clip
                txt_clip = TextClip(
                    text=text,
                    font=self.default_font,
                    font_size=fontsize,
                    color=self.default_color,
                    stroke_color=self.default_stroke_color,
                    stroke_width=2,
                    method='caption',
                    size=(video_size[0] - 100, None),
                    text_align='center'
                ).with_duration(duration).with_start(start_time)
                
                # Position at bottom center
                txt_clip = txt_clip.with_position(("center", video_size[1] - 150))
                
                subtitle_clips.append(txt_clip)
            
            logger.info(f"Created {len(subtitle_clips)} subtitle overlays")
            return subtitle_clips
            
        except Exception as e:
            logger.error(f"Failed to create subtitle overlays: {e}")
            return []
    
    def create_keyword_highlight(
        self,
        text: str,
        keywords: List[str],
        duration: float,
        video_size: Tuple[int, int],
        start_time: float = 0
    ) -> List[TextClip]:
        """
        Create text overlay with highlighted keywords
        
        Args:
            text: Full text
            keywords: List of keywords to highlight
            duration: Duration in seconds
            video_size: Video dimensions
            start_time: Start time in video
            
        Returns:
            List of TextClips (base text + highlighted keywords)
        """
        clips = []
        
        try:
            # Create base text clip
            base_clip = TextClip(
                text=text,
                font=self.default_font,
                font_size=55,
                color=self.default_color,
                stroke_color=self.default_stroke_color,
                stroke_width=2,
                method='caption',
                size=(video_size[0] - 100, None),
                text_align='center'
            ).with_duration(duration).with_start(start_time).with_position("center")
            
            clips.append(base_clip)
            
            # For each keyword, create a highlighted version
            # This is a simplified approach - in production, you'd want to
            # calculate exact positions for each word
            for i, keyword in enumerate(keywords):
                if keyword.lower() in text.lower():
                    # Create highlighted keyword clip
                    keyword_clip = TextClip(
                        text=keyword.upper(),
                        font=self.default_font,
                        font_size=65,
                        color='yellow',
                        stroke_color='orange',
                        stroke_width=3
                    ).with_duration(0.5).with_start(start_time + i * 0.5)
                    
                    # Position keywords at different locations
                    keyword_clip = keyword_clip.with_position(("center", 200 + i * 100))
                    clips.append(keyword_clip)
            
            return clips
            
        except Exception as e:
            logger.error(f"Failed to create keyword highlights: {e}")
            return []
    
    def create_cta_overlay(
        self,
        cta_type: str,
        duration: float,
        video_size: Tuple[int, int],
        start_time: float,
        custom_text: Optional[str] = None,
        animation: str = "pulse"
    ) -> Optional[TextClip]:
        """
        Create call-to-action overlay
        
        Args:
            cta_type: Type of CTA (book_now, learn_more, etc.)
            duration: Duration in seconds
            video_size: Video dimensions
            start_time: Start time in video
            custom_text: Optional custom CTA text
            animation: Animation style
            
        Returns:
            TextClip with CTA
        """
        try:
            # Get CTA text
            cta_text = custom_text if custom_text else self.cta_templates.get(cta_type, "Learn More")
            
            # Create CTA clip with background box effect
            txt_clip = TextClip(
                text=cta_text,
                font=self.default_font,
                font_size=50,
                color='white',
                stroke_color='black',
                stroke_width=3,
                bg_color='rgba(255, 100, 100, 0.8)',  # Semi-transparent red background
                method='caption',
                size=(video_size[0] - 200, None),
                text_align='center'
            ).with_duration(duration).with_start(start_time)
            
            # Position at bottom
            txt_clip = txt_clip.with_position(("center", video_size[1] - 100))
            
            # Apply pulse animation (simulated with fade in/out)
            if animation == "pulse":
                txt_clip = txt_clip.with_effects([
                    lambda clip: clip.with_effects([
                        ("fadein", 0.3),
                        ("fadeout", 0.3)
                    ])
                ])
            
            logger.info(f"Created CTA overlay: {cta_text}")
            return txt_clip
            
        except Exception as e:
            logger.error(f"Failed to create CTA overlay: {e}")
            return None
    
    def generate_subtitles_from_text(
        self,
        text: str,
        duration: float,
        words_per_subtitle: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate subtitle timing from text
        
        Args:
            text: Full text to convert to subtitles
            duration: Total video duration
            words_per_subtitle: Number of words per subtitle
            
        Returns:
            List of subtitle dicts with timing
        """
        # Split text into words
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        # Calculate timing
        time_per_word = duration / total_words
        subtitles = []
        
        for i in range(0, total_words, words_per_subtitle):
            chunk = words[i:i + words_per_subtitle]
            subtitle_text = ' '.join(chunk)
            
            start_time = i * time_per_word
            end_time = min((i + words_per_subtitle) * time_per_word, duration)
            
            subtitles.append({
                'text': subtitle_text,
                'start': start_time,
                'end': end_time
            })
        
        logger.info(f"Generated {len(subtitles)} subtitles from text")
        return subtitles
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract important keywords from text
        
        Args:
            text: Text to analyze
            top_n: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction (in production, use NLP)
        # Remove common words and extract capitalized words or hashtags
        
        keywords = []
        
        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        keywords.extend(hashtags[:top_n])
        
        # Extract capitalized words (likely important)
        words = text.split()
        capitalized = [word.strip('.,!?') for word in words if word and word[0].isupper() and len(word) > 3]
        keywords.extend(capitalized[:top_n - len(keywords)])
        
        # Remove duplicates and limit
        keywords = list(dict.fromkeys(keywords))[:top_n]
        
        logger.info(f"Extracted keywords: {keywords}")
        return keywords
    
    def create_location_tag(
        self,
        location: str,
        duration: float,
        video_size: Tuple[int, int],
        start_time: float = 0
    ) -> Optional[TextClip]:
        """
        Create location tag overlay (like Instagram)
        
        Args:
            location: Location name
            duration: Duration in seconds
            video_size: Video dimensions
            start_time: Start time
            
        Returns:
            TextClip with location tag
        """
        try:
            # Create location tag with pin emoji
            location_text = f"📍 {location}"
            
            txt_clip = TextClip(
                text=location_text,
                font=self.default_font,
                font_size=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                bg_color='rgba(0, 0, 0, 0.6)'
            ).with_duration(duration).with_start(start_time)
            
            # Position at top left
            txt_clip = txt_clip.with_position((50, 50))
            
            logger.info(f"Created location tag: {location}")
            return txt_clip
            
        except Exception as e:
            logger.error(f"Failed to create location tag: {e}")
            return None
    
    def apply_text_overlays_to_video(
        self,
        video_clip: VideoClip,
        post_data: Dict[str, Any],
        include_subtitles: bool = True,
        include_cta: bool = True,
        include_location: bool = True
    ) -> VideoClip:
        """
        Apply all text overlays to a video
        
        Args:
            video_clip: Base video clip
            post_data: Post data with caption, region, etc.
            include_subtitles: Whether to add subtitles
            include_cta: Whether to add CTA
            include_location: Whether to add location tag
            
        Returns:
            Video clip with overlays
        """
        try:
            video_size = video_clip.size
            duration = video_clip.duration
            caption = post_data.get('caption', '')
            region = post_data.get('region', 'Unknown')
            
            overlay_clips = [video_clip]
            
            # Add location tag
            if include_location and region:
                location_tag = self.create_location_tag(
                    location=region,
                    duration=duration,
                    video_size=video_size
                )
                if location_tag:
                    overlay_clips.append(location_tag)
            
            # Add subtitles
            if include_subtitles and caption:
                # Generate subtitle timing
                subtitle_data = self.generate_subtitles_from_text(caption, duration)
                subtitle_clips = self.create_subtitle_overlays(subtitle_data, video_size)
                overlay_clips.extend(subtitle_clips)
            
            # Add CTA at the end
            if include_cta:
                cta_start = max(0, duration - 3)  # Last 3 seconds
                cta = self.create_cta_overlay(
                    cta_type="visit_website",
                    duration=3,
                    video_size=video_size,
                    start_time=cta_start
                )
                if cta:
                    overlay_clips.append(cta)
            
            # Composite all clips
            final_video = CompositeVideoClip(overlay_clips)
            
            logger.info(f"Applied {len(overlay_clips) - 1} text overlays to video")
            return final_video
            
        except Exception as e:
            logger.error(f"Failed to apply text overlays: {e}")
            return video_clip


def main():
    """Test text overlay manager"""
    manager = TextOverlayManager()
    
    print("\n=== Text Overlay Manager Test ===")
    
    # Test subtitle generation
    test_text = "Discover the stunning beaches of Maldives. Crystal clear waters and white sand await you. Book your dream vacation today!"
    subtitles = manager.generate_subtitles_from_text(test_text, duration=15.0)
    
    print(f"\nGenerated {len(subtitles)} subtitles:")
    for i, sub in enumerate(subtitles, 1):
        print(f"{i}. [{sub['start']:.1f}s - {sub['end']:.1f}s]: {sub['text']}")
    
    # Test keyword extraction
    keywords = manager.extract_keywords(test_text)
    print(f"\nExtracted keywords: {keywords}")
    
    # List CTA templates
    print("\nAvailable CTA templates:")
    for cta_type, text in manager.cta_templates.items():
        print(f"  {cta_type}: {text}")


if __name__ == "__main__":
    main()


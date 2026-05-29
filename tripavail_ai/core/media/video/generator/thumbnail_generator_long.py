#!/usr/bin/env python3
"""
Thumbnail Generator for Long Videos
Creates 16:9 YouTube thumbnails with overlay text, accent tags, and destination imagery
Bright, colorful, high-contrast design
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise


class ThumbnailGeneratorLong:
    """
    Generates 16:9 YouTube thumbnails for long videos
    Creates bright, colorful, high-contrast thumbnails with overlay text and accent tags
    """
    
    def __init__(self):
        # Thumbnail settings
        self.resolution = settings_long.THUMBNAIL_RESOLUTION  # (1920, 1080)
        self.aspect_ratio = 16 / 9  # 16:9
        self.width, self.height = self.resolution
        
        # Text settings
        self.title_font_size_min = 60  # Minimum font size (pt)
        self.title_font_size_max = 80  # Maximum font size (pt)
        self.tag_font_size = 40  # Tag font size (pt)
        self.max_title_words = 4  # Maximum words in title
        
        # Color settings
        self.title_colors = ['white', 'yellow', '#FFD700']  # Title colors (contrasting)
        self.tag_colors = ['white', '#FFD700', '#FFA500']  # Tag colors
        self.overlay_opacity = 0.7  # Overlay opacity (0-1)
        self.text_shadow = True  # Text shadow
        
        # Output directory
        self.thumbnails_dir = Path(settings_long.THUMBNAILS_DIR)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        # Images directory (for main image)
        self.images_dir = Path(settings_long.IMAGES_DIR)
        
        logger.info("Thumbnail Generator Long initialized")
        logger.info(f"Resolution: {self.width}x{self.height}")
        logger.info(f"Aspect Ratio: {self.aspect_ratio}")
    
    def generate_thumbnail(
        self,
        destination: str,
        itinerary_data: Dict[str, Any],
        output_path: Optional[Path] = None,
        script_data: Optional[Dict[str, Any]] = None  # PHASE 2.2: Story-based thumbnail
    ) -> Optional[Path]:
        """
        Generate thumbnail for destination
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            itinerary_data: Itinerary data with days and scenes
            output_path: Output thumbnail path (optional)
            
        Returns:
            Path to generated thumbnail or None if failed
        """
        try:
            logger.info(f"Generating thumbnail for {destination}...")
            
            # Get destination info
            ideal_days = itinerary_data.get('ideal_days', 0)
            itinerary = itinerary_data.get('itinerary', [])
            
            # PHASE 2.2: Generate story-based title from script_data
            if script_data and script_data.get('itinerary_introduction'):
                # Extract story theme from introduction
                intro_text = script_data.get('itinerary_introduction', '')
                # Generate title that captures story essence
                title = self._generate_story_title(destination, ideal_days, intro_text)
            else:
                # Fallback to basic title
                title = self._generate_title(destination, ideal_days)
            
            # PHASE 2.2: Generate story-based tags from script_data
            if script_data:
                # Extract journey arc highlights
                tags = self._generate_story_tags(script_data, itinerary)
            else:
                # Fallback to basic tags
                tags = self._generate_tags(itinerary)
            
            # PHASE 2.2: Get main image - try to extract from introduction video or use best scene
            main_image = self._get_story_image(destination, itinerary, script_data)
            
            if not main_image:
                logger.warning("No main image found, using placeholder")
                main_image = self._create_placeholder_image()
            
            # Create thumbnail
            thumbnail = self._create_thumbnail(main_image, title, tags, destination)
            
            # Save thumbnail
            if output_path is None:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                output_path = self.thumbnails_dir / f"{safe_destination}_thumbnail.jpg"
            
            thumbnail.save(output_path, 'JPEG', quality=95)
            logger.info(f"✅ Generated thumbnail: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _generate_title(self, destination: str, ideal_days: int) -> str:
        """
        Generate title (max 4 words)
        
        Args:
            destination: Destination name
            ideal_days: Number of days
            
        Returns:
            Title string (max 4 words)
        """
        try:
            # Extract destination name (remove country if present)
            dest_name = destination.split(',')[0].strip()
            
            # Generate title based on destination and days
            if ideal_days > 0:
                title = f"{dest_name} {ideal_days}-Day"
            else:
                title = f"{dest_name} Guide"
            
            # Add emoji based on destination
            emoji = self._get_destination_emoji(dest_name)
            if emoji:
                title = f"{title} {emoji}"
            
            # Ensure max 4 words
            words = title.split()
            if len(words) > self.max_title_words:
                title = " ".join(words[:self.max_title_words])
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return destination.split(',')[0].strip()
    
    def _generate_tags(self, itinerary: List[Dict[str, Any]]) -> List[str]:
        """
        Generate accent tags (highlights)
        
        Args:
            itinerary: Itinerary data with days and scenes
            
        Returns:
            List of tag strings
        """
        try:
            tags = []
            categories = set()
            
            # Collect categories from itinerary
            for day in itinerary:
                scenes = day.get('scenes', [])
                for scene in scenes:
                    category = scene.get('category', '')
                    if category in ['attraction', 'food', 'scenic', 'stay']:
                        categories.add(category)
            
            # Map categories to tags
            category_map = {
                'attraction': 'Attractions',
                'food': 'Food',
                'scenic': 'Views',
                'stay': 'Hotels',
                'nightlife': 'Nightlife',
                'local_life': 'Culture',
            }
            
            # Convert categories to tags
            for category in categories:
                if category in category_map:
                    tags.append(category_map[category])
            
            # Limit to 3-4 tags
            if len(tags) > 4:
                tags = tags[:4]
            
            # Add default tags if none found
            if not tags:
                tags = ['Food', 'Culture', 'Views']
            
            return tags
            
        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            return ['Food', 'Culture', 'Views']
    
    def _generate_story_title(self, destination: str, ideal_days: int, intro_text: str) -> str:
        """
        PHASE 2.2: Generate story-based title from introduction text
        
        Args:
            destination: Destination name
            ideal_days: Number of days
            intro_text: Introduction text from script
            
        Returns:
            Story-based title string (max 4 words)
        """
        try:
            # Extract destination name
            dest_name = destination.split(',')[0].strip()
            
            # Extract key words from introduction that capture story theme
            import re
            # Look for words that suggest journey arc (discovery, journey, transformation, ancient, modern, etc.)
            story_keywords = ['journey', 'discovery', 'transformation', 'ancient', 'modern', 'vibrant', 'palace', 'city', 'coast', 'mountain', 'culture', 'heritage']
            
            intro_lower = intro_text.lower()
            found_keywords = [kw for kw in story_keywords if kw in intro_lower]
            
            # Build title with story theme
            if ideal_days > 0:
                if found_keywords:
                    # Use first found keyword to add story flavor
                    theme_word = found_keywords[0].capitalize()
                    title = f"{dest_name} {theme_word}"
                else:
                    title = f"{dest_name} {ideal_days}-Day"
            else:
                if found_keywords:
                    theme_word = found_keywords[0].capitalize()
                    title = f"{dest_name} {theme_word}"
                else:
                    title = f"{dest_name} Guide"
            
            # Add emoji based on destination
            emoji = self._get_destination_emoji(dest_name)
            if emoji:
                title = f"{title} {emoji}"
            
            # Ensure max 4 words
            words = title.split()
            if len(words) > self.max_title_words:
                title = " ".join(words[:self.max_title_words])
            
            logger.info(f"Generated story-based title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating story title: {e}")
            return self._generate_title(destination, ideal_days)
    
    def _generate_story_tags(self, script_data: Dict[str, Any], itinerary: List[Dict[str, Any]]) -> List[str]:
        """
        PHASE 2.2: Generate story-based tags from script_data journey arc
        
        Args:
            script_data: Script data with days and introduction
            itinerary: Itinerary data with days and scenes
            
        Returns:
            List of story-based tag strings
        """
        try:
            tags = []
            script_days = script_data.get('days', [])
            
            # Extract journey arc from days
            # Look for themes like: arrival → discovery → culture → reflection
            day_themes = []
            for script_day in script_days[:4]:  # First 4 days
                day_title = script_day.get('day_title', '')
                day_narration = script_day.get('narration', '')
                
                # Extract theme words from day title/narration
                theme_words = {
                    'arrival': 'Arrival',
                    'city': 'Urban',
                    'palace': 'Heritage',
                    'culture': 'Culture',
                    'food': 'Cuisine',
                    'scenic': 'Scenery',
                    'temple': 'Spiritual',
                    'beach': 'Coastal',
                    'mountain': 'Nature'
                }
                
                day_text = (day_title + ' ' + day_narration).lower()
                for keyword, tag in theme_words.items():
                    if keyword in day_text and tag not in tags:
                        day_themes.append(tag)
                        break
            
            tags.extend(day_themes[:3])  # Limit to 3 story tags
            
            # Add default tags if needed
            if len(tags) < 2:
                tags.extend(['Culture', 'Discovery'])
            
            # Limit to 4 tags total
            if len(tags) > 4:
                tags = tags[:4]
            
            logger.info(f"Generated story-based tags: {tags}")
            return tags
            
        except Exception as e:
            logger.error(f"Error generating story tags: {e}")
            return self._generate_tags(itinerary)
    
    def _get_story_image(self, destination: str, itinerary: List[Dict[str, Any]], script_data: Optional[Dict[str, Any]] = None) -> Optional[Image.Image]:
        """
        PHASE 2.2: Get story-based image - try to extract from introduction video or use best scene
        
        Args:
            destination: Destination name
            itinerary: Itinerary data with days and scenes
            script_data: Script data with introduction (optional)
            
        Returns:
            Story-based main image (PIL Image) or None if not found
        """
        try:
            # First, try to extract frame from introduction video if available
            if script_data and script_data.get('itinerary_introduction'):
                intro_image = self._extract_intro_video_frame(destination)
                if intro_image:
                    logger.info("Using extracted frame from introduction video")
                    return intro_image
            
            # Fallback: Use best scene image that represents journey arc
            # Try to find an image from Day 1 (arrival/introduction scene)
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            
            # Look for Day 1 arrival or scenic images
            if itinerary:
                first_day = itinerary[0]
                scenes = first_day.get('scenes', [])
                
                # Try arrival scene first
                for scene in scenes:
                    scene_order = scene.get('order', 0)
                    category = scene.get('category', '')
                    
                    if category in ['arrival', 'scenic']:
                        scene_dir = self.images_dir / safe_destination / f"day_1" / f"scene_{scene_order}"
                        if scene_dir.exists():
                            scene_images = list(scene_dir.glob("*.jpg"))
                            if scene_images:
                                logger.info(f"Using Day 1 {category} image: {scene_images[0]}")
                                return Image.open(scene_images[0])
            
            # Fallback to regular main image selection
            return self._get_main_image(destination, itinerary)
            
        except Exception as e:
            logger.error(f"Error getting story image: {e}")
            # Fallback to regular main image selection
            return self._get_main_image(destination, itinerary)
    
    def _extract_intro_video_frame(self, destination: str) -> Optional[Image.Image]:
        """
        PHASE 2.2: Extract best frame from introduction video (if exists)
        
        Args:
            destination: Destination name
            
        Returns:
            Extracted frame (PIL Image) or None if not found
        """
        try:
            from core.utils.ffmpeg_helper import get_ffmpeg_path
            import subprocess
            from pathlib import Path
            import tempfile
            
            # Look for introduction video in videos directory
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            videos_dir = Path(settings_long.VIDEOS_DIR)
            intro_video_path = videos_dir / "temp_days" / f"{safe_destination}_introduction.mp4"
            
            # Also check main videos directory
            if not intro_video_path.exists():
                intro_video_path = videos_dir / f"{safe_destination}_introduction.mp4"
            
            if not intro_video_path.exists():
                logger.debug(f"Introduction video not found: {intro_video_path}")
                return None
            
            # Extract frame at 1 second (good thumbnail timing)
            ffmpeg_path = get_ffmpeg_path()
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                output_frame = Path(tmp_file.name)
            
            cmd = [
                ffmpeg_path,
                '-i', str(intro_video_path),
                '-ss', '1',  # Extract frame at 1 second
                '-vframes', '1',
                '-q:v', '2',  # High quality
                '-y',
                str(output_frame)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and output_frame.exists():
                logger.info(f"Extracted frame from introduction video: {output_frame}")
                frame_image = Image.open(output_frame)
                # Clean up temp file after loading
                try:
                    output_frame.unlink()
                except:
                    pass
                return frame_image
            else:
                logger.warning(f"Failed to extract frame from introduction video: {result.stderr[:200]}")
                # Clean up temp file on error
                try:
                    if output_frame.exists():
                        output_frame.unlink()
                except:
                    pass
                return None
                
        except Exception as e:
            logger.warning(f"Error extracting intro video frame: {e}")
            return None
    
    def _get_destination_emoji(self, destination: str) -> str:
        """
        Get emoji for destination
        
        Args:
            destination: Destination name
            
        Returns:
            Emoji string
        """
        try:
            destination_lower = destination.lower()
            
            # Destination emoji map
            emoji_map = {
                'bali': '🌴',
                'thailand': '🏖️',
                'japan': '🗾',
                'switzerland': '🏔️',
                'france': '🗼',
                'italy': '🏛️',
                'spain': '🏖️',
                'greece': '🏛️',
                'turkey': '🕌',
                'india': '🕌',
                'china': '🏮',
                'south korea': '🏮',
                'singapore': '🏙️',
                'malaysia': '🌴',
                'philippines': '🏖️',
                'vietnam': '🏛️',
                'cambodia': '🏛️',
                'laos': '🏛️',
                'myanmar': '🏛️',
                'indonesia': '🌴',
                'maldives': '🏖️',
                'sri lanka': '🏖️',
                'nepal': '🏔️',
                'bhutan': '🏔️',
                'tibet': '🏔️',
            }
            
            # Check for exact match
            if destination_lower in emoji_map:
                return emoji_map[destination_lower]
            
            # Check for partial match
            for key, emoji in emoji_map.items():
                if key in destination_lower:
                    return emoji
            
            # Default emoji
            return '🌴'
            
        except Exception as e:
            logger.error(f"Error getting destination emoji: {e}")
            return '🌴'
    
    def _get_main_image(self, destination: str, itinerary: List[Dict[str, Any]]) -> Optional[Image.Image]:
        """
        Get main image (scenic photo) for thumbnail
        
        Args:
            destination: Destination name
            itinerary: Itinerary data with days and scenes
            
        Returns:
            Main image (PIL Image) or None if not found
        """
        try:
            # Look for scenic images in images directory
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            
            # Try scenic_views category first
            scenic_dir = self.images_dir / safe_destination / "scenic_views"
            if scenic_dir.exists():
                scenic_images = list(scenic_dir.glob("*.jpg"))
                if scenic_images:
                    # Use first scenic image
                    main_image_path = scenic_images[0]
                    logger.info(f"Using scenic image: {main_image_path}")
                    return Image.open(main_image_path)
            
            # Try attractions category
            attractions_dir = self.images_dir / safe_destination / "attractions"
            if attractions_dir.exists():
                attraction_images = list(attractions_dir.glob("*.jpg"))
                if attraction_images:
                    # Use first attraction image
                    main_image_path = attraction_images[0]
                    logger.info(f"Using attraction image: {main_image_path}")
                    return Image.open(main_image_path)
            
            # Try any category
            for category in ['scenic_views', 'attractions', 'activities', 'food_culture', 'local_life']:
                category_dir = self.images_dir / safe_destination / category
                if category_dir.exists():
                    category_images = list(category_dir.glob("*.jpg"))
                    if category_images:
                        # Use first image
                        main_image_path = category_images[0]
                        logger.info(f"Using image from {category}: {main_image_path}")
                        return Image.open(main_image_path)
            
            logger.warning("No images found for thumbnail")
            return None
            
        except Exception as e:
            logger.error(f"Error getting main image: {e}")
            return None
    
    def _create_placeholder_image(self) -> Image.Image:
        """
        Create placeholder image if no main image found
        
        Returns:
            Placeholder image (PIL Image)
        """
        try:
            # Create gradient placeholder
            img = Image.new('RGB', self.resolution, color=(100, 150, 200))
            draw = ImageDraw.Draw(img)
            
            # Draw gradient
            for y in range(self.height):
                color_value = int(100 + (150 - 100) * (y / self.height))
                draw.rectangle([(0, y), (self.width, y + 1)], fill=(color_value, color_value + 50, color_value + 100))
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            return Image.new('RGB', self.resolution, color=(100, 150, 200))
    
    def _create_thumbnail(
        self,
        main_image: Image.Image,
        title: str,
        tags: List[str],
        destination: str
    ) -> Image.Image:
        """
        Create thumbnail from main image, title, and tags
        
        Args:
            main_image: Main image (PIL Image)
            title: Title text
            tags: List of tag strings
            destination: Destination name
            
        Returns:
            Thumbnail image (PIL Image)
        """
        try:
            # Resize main image to thumbnail resolution
            main_image = main_image.resize(self.resolution, Image.LANCZOS)
            
            # Enhance image (brightness, contrast, saturation)
            enhancer = ImageEnhance.Brightness(main_image)
            main_image = enhancer.enhance(1.2)  # Increase brightness
            
            enhancer = ImageEnhance.Contrast(main_image)
            main_image = enhancer.enhance(1.3)  # Increase contrast
            
            enhancer = ImageEnhance.Color(main_image)
            main_image = enhancer.enhance(1.2)  # Increase saturation
            
            # Create thumbnail with overlay
            thumbnail = main_image.copy()
            draw = ImageDraw.Draw(thumbnail)
            
            # Add dark overlay for text readability
            overlay = Image.new('RGBA', self.resolution, (0, 0, 0, int(255 * (1 - self.overlay_opacity))))
            thumbnail = Image.alpha_composite(thumbnail.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(thumbnail)
            
            # Get font
            try:
                # Try to use system font
                title_font = ImageFont.truetype("arial.ttf", self.title_font_size_min)
                tag_font = ImageFont.truetype("arial.ttf", self.tag_font_size)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                tag_font = ImageFont.load_default()
            
            # Draw title (bottom center)
            title_color = random.choice(self.title_colors)
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            title_y = self.height - title_height - 100  # Bottom with margin
            
            # Draw title with shadow
            if self.text_shadow:
                # Shadow
                draw.text((title_x + 3, title_y + 3), title, font=title_font, fill='black')
            
            # Title
            draw.text((title_x, title_y), title, font=title_font, fill=title_color)
            
            # Draw tags (small banners, top right)
            tag_x = self.width - 20  # Right margin
            tag_y = 20  # Top margin
            
            # Reverse tags for bottom-to-top display
            tags_reversed = list(reversed(tags))
            
            for i, tag in enumerate(tags_reversed):
                tag_text = tag
                tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
                tag_width = tag_bbox[2] - tag_bbox[0]
                tag_height = tag_bbox[3] - tag_bbox[1]
                
                # Calculate tag position
                tag_x_pos = tag_x - tag_width - 10
                tag_y_pos = tag_y + (tag_height + 10) * i
                
                # Draw tag background (semi-transparent)
                tag_bg = Image.new('RGBA', (tag_width + 20, tag_height + 10), (0, 0, 0, 180))
                thumbnail.paste(tag_bg, (tag_x_pos - 10, tag_y_pos - 5), tag_bg)
                draw = ImageDraw.Draw(thumbnail)
                
                # Draw tag text
                tag_color = random.choice(self.tag_colors)
                if self.text_shadow:
                    # Shadow
                    draw.text((tag_x_pos + 1, tag_y_pos + 1), tag_text, font=tag_font, fill='black')
                
                # Tag
                draw.text((tag_x_pos, tag_y_pos), tag_text, font=tag_font, fill=tag_color)
            
            return thumbnail
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return main_image
    
    def generate_thumbnail_from_prompt(
        self,
        destination: str,
        ideal_days: int,
        tags: List[str],
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Generate thumbnail from prompt (for testing)
        
        Args:
            destination: Destination name
            ideal_days: Number of days
            tags: List of tag strings
            output_path: Output thumbnail path (optional)
            
        Returns:
            Path to generated thumbnail or None if failed
        """
        try:
            # Generate title
            title = self._generate_title(destination, ideal_days)
            
            # Get main image
            main_image = self._get_main_image(destination, [])
            
            if not main_image:
                logger.warning("No main image found, using placeholder")
                main_image = self._create_placeholder_image()
            
            # Create thumbnail
            thumbnail = self._create_thumbnail(main_image, title, tags, destination)
            
            # Save thumbnail
            if output_path is None:
                safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                output_path = self.thumbnails_dir / f"{safe_destination}_thumbnail.jpg"
            
            thumbnail.save(output_path, 'JPEG', quality=95)
            logger.info(f"✅ Generated thumbnail: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating thumbnail from prompt: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


def main():
    """Test thumbnail generator"""
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    
    # Generate itinerary
    itinerary_generator = ItineraryGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing thumbnail generator for {test_destination}")
    
    # Load or generate itinerary
    itinerary_data = itinerary_generator.load_itinerary(test_destination)
    
    if not itinerary_data:
        logger.info("Generating itinerary first...")
        itinerary_data = itinerary_generator.generate_itinerary(test_destination, max_duration_minutes=8)
        itinerary_generator.save_itinerary(itinerary_data, test_destination)
    
    # Generate thumbnail
    thumbnail_generator = ThumbnailGeneratorLong()
    thumbnail_path = thumbnail_generator.generate_thumbnail(
        test_destination,
        itinerary_data
    )
    
    if thumbnail_path:
        logger.info(f"✅ Generated thumbnail: {thumbnail_path}")
    else:
        logger.error("Failed to generate thumbnail")


if __name__ == "__main__":
    main()


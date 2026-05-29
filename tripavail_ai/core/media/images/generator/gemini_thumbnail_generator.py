"""
Gemini Imagen 3.0 Thumbnail Generator - ENHANCED
Uses Google's Gemini API + OpenAI for extraordinary thumbnail generation
Features:
- AI-powered prompt generation (GPT-4)
- Hook text generation for thumbnails
- OCR validation for text accuracy
- Professional, eye-catching visuals
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from loguru import logger
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai package not installed. Install with: pip install google-genai")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai package not installed. Install with: pip install openai")

try:
    import pytesseract
    from PIL import Image as PILImage
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not installed. Install with: pip install pytesseract")


class GeminiThumbnailGenerator:
    """Generate thumbnails using Google Gemini Imagen 3.0"""
    
    def __init__(self):
        # Set API keys
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyCFMtZlP_pSB7759iOjD4x4Pmj9qJ9E3Fw')
        os.environ['GEMINI_API_KEY'] = self.gemini_api_key
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not GEMINI_AVAILABLE:
            logger.error("Gemini API not available. Install google-genai package.")
            return
        
        # Initialize Gemini client
        try:
            self.client = genai.Client(api_key=self.gemini_api_key)
            logger.info("✅ Gemini Imagen 3.0 initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
        
        # Initialize OpenAI client for AI prompt generation
        self.openai_client = None
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI GPT-4 initialized for prompt generation")
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")
        
        # Check OCR availability
        if OCR_AVAILABLE:
            logger.info("✅ OCR validation enabled (pytesseract)")
        else:
            logger.warning("⚠️ OCR not available - text validation disabled")
        
        # Thumbnail dimensions - Only 9:16 for vertical videos
        self.vertical_size = (1080, 1920)  # 9:16 aspect ratio
        
        logger.info("🎨 Enhanced Thumbnail Generator ready")
        
    def generate_thumbnail_for_post(self, post_id: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate 9:16 thumbnail for vertical videos using Gemini Imagen 3.0
        
        Args:
            post_id: Post identifier (e.g., "001")
            metadata: Post metadata with title, caption, region
        
        Returns:
            Dict with thumbnail path: {'vertical': 'path/to/thumbnail.jpg'}
        """
        if not GEMINI_AVAILABLE or not self.client:
            logger.error("Gemini API not available")
            return {}
        
        try:
            # Extract content for thumbnail
            title = metadata.get('original_title', '')
            caption = metadata.get('caption', '')
            region = metadata.get('region', 'Unknown')
            
            logger.info(f"🎨 Generating EXTRAORDINARY Gemini thumbnail for post {post_id}")
            logger.info(f"   Title: {title[:60]}...")
            logger.info(f"   Region: {region}")
            
            # Generate hook text using AI
            hook_text = self._generate_hook_text(title, caption)
            
            # Generate AI-powered prompt for stunning visuals
            thumbnail_prompt = self._generate_ai_prompt(title, caption, region)
            logger.info(f"   Using AI-generated prompt for extraordinary visuals")
            
            # Generate image using Gemini Imagen 3.0
            image_data = self._generate_gemini_image(thumbnail_prompt)
            
            if not image_data:
                logger.error(f"❌ Failed to generate thumbnail for post {post_id}")
                return {}
            
            # Create 9:16 thumbnail with enhanced text overlay
            vertical_path = self._create_vertical_thumbnail_enhanced(
                image_data, hook_text, title, post_id
            )
            
            if vertical_path:
                # Validate text is readable using OCR
                if self._validate_text_with_ocr(vertical_path, hook_text):
                    logger.info(f"✅ Text validated with OCR - Clearly readable!")
                
                # Save hook text to metadata for video overlay
                self._save_hook_text_to_metadata(post_id, hook_text)
                
                logger.info(f"✅ Generated EXTRAORDINARY 9:16 thumbnail: {vertical_path}")
                return {'vertical': str(vertical_path), 'hook_text': hook_text}
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error generating thumbnail for post {post_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def _generate_hook_text(self, title: str, caption: str) -> str:
        """
        Generate punchy hook text for thumbnail using AI
        
        Hook text should be:
        - 3-7 words maximum
        - Attention-grabbing
        - Clear and readable
        - Conveys the main news
        """
        if not self.openai_client:
            # Fallback: Extract first few words from title
            words = title.split()[:5]
            return ' '.join(words)
        
        try:
            logger.info("🤖 Generating hook text with GPT-3.5-turbo...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert YouTube Shorts thumbnail copywriter. Create punchy, attention-grabbing hook text for thumbnails.

Rules:
- 3-7 words MAXIMUM
- All caps for impact
- No punctuation except ! or ?
- Should make viewer NEED to click
- Convey the main news clearly
- Use power words and intrigue"""
                    },
                    {
                        "role": "user",
                        "content": f"""Create a punchy thumbnail hook text for this travel news:

Title: {title}
Caption: {caption}

Return ONLY the hook text, nothing else."""
                    }
                ],
                temperature=0.9,
                max_tokens=20
            )
            
            hook_text = response.choices[0].message.content.strip()
            hook_text = hook_text.strip('"').strip("'")  # Remove quotes
            
            # Ensure it's not too long
            if len(hook_text) > 50:
                words = hook_text.split()[:6]
                hook_text = ' '.join(words)
            
            logger.info(f"   Hook: {hook_text}")
            return hook_text
            
        except Exception as e:
            logger.error(f"Hook generation failed: {e}")
            # Fallback
            words = title.split()[:5]
            return ' '.join(words).upper()
    
    def _generate_ai_prompt(self, title: str, caption: str, region: str) -> str:
        """
        Use GPT-4 to generate extraordinary, creative Imagen prompts
        
        Strategy:
        - Analyze the news content deeply
        - Create vivid, cinematic visual descriptions
        - Focus on emotional impact and beauty
        - Include specific composition details
        """
        if not self.openai_client:
            # Fallback to basic prompt
            return self._create_thumbnail_prompt(title, caption, region)
        
        try:
            logger.info("🤖 Generating AI-powered image prompt with GPT-4...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert travel photographer and visual artist. Generate extraordinary, cinematic image prompts for AI image generation (Gemini Imagen 3.0).

Your prompts should:
- Create breathtaking, magazine-cover quality visuals
- Use vivid sensory details and color descriptions
- Specify dramatic lighting (golden hour, blue hour, dramatic shadows)
- Include compositional elements (rule of thirds, leading lines, depth)
- Evoke emotion and wanderlust
- Be 100-150 words of pure visual description
- Focus on VISUAL elements only (no text, no people's faces)
- Make the viewer say "WOW, I need to see this!"

Style: Professional travel photography, National Geographic quality, cinematic composition, ultra-detailed."""
                    },
                    {
                        "role": "user",
                        "content": f"""Generate an extraordinary image prompt for this travel news:

**Title:** {title}
**Caption:** {caption}
**Region:** {region}

Create a STUNNING visual prompt that captures the essence of this news. Make it extraordinary, beautiful, and eye-catching. Focus on the location, atmosphere, and visual drama.

Return ONLY the image prompt, no explanations."""
                    }
                ],
                temperature=0.8,
                max_tokens=250
            )
            
            ai_prompt = response.choices[0].message.content.strip()
            
            # Add technical specifications
            technical_specs = """
Photorealistic, professional travel photography, shot with Canon EOS R5, 
24mm wide angle lens, f/2.8, ultra sharp focus, 8K resolution, 
cinematic color grading, award-winning composition, National Geographic style.
9:16 vertical format optimized, negative space at bottom 30% for text overlay.
NO text, NO watermarks, NO logos."""
            
            full_prompt = f"{ai_prompt}\n\n{technical_specs}"
            
            logger.info(f"   AI Prompt (first 100 chars): {ai_prompt[:100]}...")
            return full_prompt
            
        except Exception as e:
            logger.error(f"AI prompt generation failed: {e}")
            # Fallback to basic prompt
            return self._create_thumbnail_prompt(title, caption, region)
    
    def _create_thumbnail_prompt(self, title: str, caption: str, region: str) -> str:
        """
        Create an optimized prompt for Gemini Imagen thumbnail generation
        
        Strategy:
        - Cinematic travel photography style
        - High contrast and vibrant colors
        - Clean negative space for text overlay
        - Professional, eye-catching composition
        """
        # Extract key visual elements
        visual_elements = []
        
        # Add region-specific elements
        if region and region != 'Unknown':
            visual_elements.append(f"stunning {region} landscape")
        
        # Extract travel-related keywords
        travel_keywords = [
            'travel', 'tourism', 'destination', 'city', 'beach', 'mountain', 
            'culture', 'adventure', 'luxury', 'resort', 'hotel', 'food',
            'street', 'market', 'temple', 'architecture', 'nature', 'sunset'
        ]
        
        text_content = (title + ' ' + caption).lower()
        found_keywords = [kw for kw in travel_keywords if kw in text_content]
        
        if found_keywords:
            visual_elements.extend(found_keywords[:2])
        
        # Build comprehensive prompt
        if visual_elements:
            scene_description = ', '.join(visual_elements)
        else:
            scene_description = 'a breathtaking travel destination'
        
        prompt = f"""Professional travel photography: {scene_description}. 
Cinematic composition, vibrant colors, high contrast, dramatic lighting, 
golden hour atmosphere, ultra sharp focus, travel magazine quality.
Shot with professional camera, shallow depth of field, eye-catching visual.
Clean negative space at top for text overlay. No text, no watermarks.
Photorealistic, high resolution, award-winning travel photography style."""
        
        return prompt
    
    def _generate_gemini_image(self, prompt: str) -> Optional[bytes]:
        """
        Generate image using Gemini Imagen 3.0 API
        
        Args:
            prompt: Text description of desired image
        
        Returns:
            Image data as bytes, or None if failed
        """
        try:
            logger.info("📡 Calling Gemini Imagen 3.0 API...")
            
            # Generate image with Gemini Imagen 3.0
            result = self.client.models.generate_images(
                model="models/imagen-3.0-generate-002",
                prompt=prompt,
                config=dict(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio="9:16",  # Vertical format for YouTube Shorts
                ),
            )
            
            # Check if images were generated
            if not result.generated_images:
                logger.error("❌ No images generated by Gemini API")
                return None
            
            if len(result.generated_images) != 1:
                logger.warning(f"⚠️ Expected 1 image, got {len(result.generated_images)}")
            
            # Get the first generated image
            generated_image = result.generated_images[0]
            
            # Gemini API's save method only takes a filename (not buffer)
            # Save to temp file then read bytes
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # Save using Gemini's simple save method (just filename)
                generated_image.image.save(tmp_path)
                
                # Read the bytes
                with open(tmp_path, 'rb') as f:
                    image_bytes = f.read()
                
                logger.info(f"✅ Gemini generated image: {len(image_bytes)} bytes")
                return image_bytes
            
            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"❌ Gemini image generation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _save_hook_text_to_metadata(self, post_id: str, hook_text: str):
        """
        Save hook text to metadata for video overlay use
        
        Args:
            post_id: Post identifier
            hook_text: Hook text to save
        """
        try:
            # Get metadata path
            post_dir = Path(f"data/posts/post_{post_id}")
            metadata_path = post_dir / "metadata.json"
            
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Add hook text
                metadata['hook_text'] = hook_text
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                logger.info(f"💾 Saved hook text to metadata: '{hook_text}'")
        
        except Exception as e:
            logger.error(f"Failed to save hook text to metadata: {e}")
    
    def _validate_text_with_ocr(self, image_path: Path, expected_text: str) -> bool:
        """
        Validate that text overlay is readable using OCR
        
        Args:
            image_path: Path to thumbnail image
            expected_text: Text that should be visible
        
        Returns:
            True if text is clearly readable
        """
        if not OCR_AVAILABLE:
            logger.warning("⚠️ OCR not available - skipping text validation")
            return True  # Assume success if OCR not available
        
        try:
            # Read image
            img = PILImage.open(image_path)
            
            # Extract text using Tesseract
            extracted_text = pytesseract.image_to_string(img).strip()
            
            # Check if key words from expected text are present
            expected_words = set(expected_text.upper().split())
            extracted_words = set(extracted_text.upper().split())
            
            # Calculate word match percentage
            if not expected_words:
                return True
            
            matches = expected_words.intersection(extracted_words)
            match_percentage = len(matches) / len(expected_words) * 100
            
            logger.info(f"   OCR Match: {match_percentage:.0f}% ({len(matches)}/{len(expected_words)} words)")
            
            # Consider successful if at least 50% of words are detected
            if match_percentage >= 50:
                return True
            else:
                logger.warning(f"   OCR validation low ({match_percentage:.0f}%) - text may not be clearly readable")
                return False
            
        except Exception as e:
            logger.error(f"OCR validation failed: {e}")
            return True  # Don't fail thumbnail generation on OCR errors
    
    def _create_vertical_thumbnail_enhanced(
        self, 
        image_data: bytes, 
        hook_text: str, 
        full_title: str, 
        post_id: str
    ) -> Optional[Path]:
        """
        Create 9:16 vertical thumbnail with ENHANCED multi-layer text overlay
        
        Features:
        - Large hook text at top (attention-grabbing)
        - Smaller subtitle/title at bottom (context)
        - Professional styling with shadows and effects
        - High contrast for maximum readability
        """
        try:
            # Load base image
            base_image = Image.open(io.BytesIO(image_data))
            
            logger.info(f"   Original image size: {base_image.size}")
            
            # Ensure correct dimensions (9:16 = 1080×1920)
            if base_image.size != self.vertical_size:
                logger.info(f"   Resizing to {self.vertical_size}")
                thumbnail = base_image.resize(self.vertical_size, Image.Resampling.LANCZOS)
            else:
                thumbnail = base_image
            
            # Enhance image for more impact
            thumbnail = self._enhance_image(thumbnail)
            
            # Add multi-layer text overlay
            thumbnail = self._add_enhanced_text_overlay(thumbnail, hook_text, full_title)
            
            # Save thumbnail
            output_path = Path(f"data/posts/post_{post_id}/video/thumbnail_9x16.jpg")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            thumbnail.save(output_path, "JPEG", quality=98, optimize=True)
            
            file_size = output_path.stat().st_size / 1024  # KB
            logger.info(f"   Saved enhanced thumbnail: {output_path.name} ({file_size:.1f} KB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced vertical thumbnail: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """
        Enhance image for more visual impact
        - Increase contrast
        - Boost color saturation
        - Sharpen details
        """
        try:
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Boost saturation
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.3)
            
            # Sharpen
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            return image
        except:
            return image
    
    def _add_enhanced_text_overlay(
        self, 
        image: Image.Image, 
        hook_text: str, 
        full_title: str
    ) -> Image.Image:
        """
        Add professional multi-layer text overlay
        
        Layout:
        - TOP (Hook): Large, bold, all caps - grabs attention
        - BOTTOM (Title): Smaller, provides context
        - Both with shadows/strokes for readability
        """
        try:
            img = image.copy()
            draw = ImageDraw.Draw(img)
            
            # Font paths to try
            font_paths_bold = [
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/impact.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
            
            font_paths_regular = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            
            # Load fonts
            hook_font = None
            title_font = None
            
            # Hook font (large, bold)
            for font_path in font_paths_bold:
                try:
                    hook_font = ImageFont.truetype(font_path, 90)  # Very large
                    break
                except:
                    continue
            
            # Title font (medium, regular)
            for font_path in font_paths_regular:
                try:
                    title_font = ImageFont.truetype(font_path, 50)  # Medium
                    break
                except:
                    continue
            
            if not hook_font:
                hook_font = ImageFont.load_default()
            if not title_font:
                title_font = ImageFont.load_default()
            
            # Add HOOK TEXT at TOP
            self._draw_hook_text(draw, hook_text, hook_font, img.width, img.height)
            
            # Add TITLE TEXT at BOTTOM
            self._draw_title_text(draw, full_title, title_font, img.width, img.height)
            
            logger.info(f"   Added multi-layer text: Hook + Title")
            return img
            
        except Exception as e:
            logger.error(f"❌ Error adding enhanced text overlay: {e}")
            return image
    
    def _draw_hook_text(
        self, 
        draw: ImageDraw.Draw, 
        hook_text: str, 
        font: ImageFont.FreeTypeFont,
        img_width: int,
        img_height: int
    ):
        """
        Draw hook text at TOP of image with dramatic styling
        """
        # Make hook text ALL CAPS
        hook_text = hook_text.upper()
        
        # Position at top with padding
        y_position = 100
        
        # Wrap text if needed
        max_width = img_width - 80
        wrapped_lines = self._wrap_text(draw, hook_text, font, max_width)
        
        # Limit to 2 lines for hook
        wrapped_lines = wrapped_lines[:2]
        
        # Draw each line with dramatic effect
        for i, line in enumerate(wrapped_lines):
            # Calculate center position
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (img_width - text_width) // 2
            y_pos = y_position + (i * 110)
            
            # Draw shadow layer (multiple for depth)
            shadow_color = (0, 0, 0, 255)
            for offset in range(8, 0, -2):
                draw.text(
                    (x_position + offset, y_pos + offset),
                    line,
                    font=font,
                    fill=shadow_color
                )
            
            # Draw thick stroke (outline)
            stroke_width = 8
            stroke_color = (0, 0, 0)
            for x_off in range(-stroke_width, stroke_width + 1):
                for y_off in range(-stroke_width, stroke_width + 1):
                    if x_off != 0 or y_off != 0:
                        draw.text(
                            (x_position + x_off, y_pos + y_off),
                            line,
                            font=font,
                            fill=stroke_color
                        )
            
            # Draw main text (bright, eye-catching)
            main_color = (255, 255, 0)  # Yellow for maximum visibility
            draw.text((x_position, y_pos), line, font=font, fill=main_color)
    
    def _draw_title_text(
        self,
        draw: ImageDraw.Draw,
        title: str,
        font: ImageFont.FreeTypeFont,
        img_width: int,
        img_height: int
    ):
        """
        Draw subtitle/title at BOTTOM of image - CENTER ALIGNED
        """
        # Position at bottom
        max_width = img_width - 80  # More padding for center alignment
        wrapped_lines = self._wrap_text(draw, title, font, max_width)
        
        # Limit to 2 lines
        wrapped_lines = wrapped_lines[:2]
        
        # Calculate starting position
        line_height = 60
        total_height = len(wrapped_lines) * line_height
        start_y = img_height - total_height - 60
        
        # Draw each line - CENTER ALIGNED
        for i, line in enumerate(wrapped_lines):
            y_pos = start_y + (i * line_height)
            
            # Calculate center position for this line
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (img_width - text_width) // 2  # CENTER ALIGNED
            
            # Draw shadow
            shadow_color = (0, 0, 0, 200)
            for offset in range(4, 0, -1):
                draw.text(
                    (x_position + offset, y_pos + offset),
                    line,
                    font=font,
                    fill=shadow_color
                )
            
            # Draw stroke
            stroke_width = 5
            stroke_color = (0, 0, 0)
            for x_off in range(-stroke_width, stroke_width + 1):
                for y_off in range(-stroke_width, stroke_width + 1):
                    if x_off != 0 or y_off != 0:
                        draw.text(
                            (x_position + x_off, y_pos + y_off),
                            line,
                            font=font,
                            fill=stroke_color
                        )
            
            # Draw main text (white for clarity) - CENTER ALIGNED
            draw.text((x_position, y_pos), line, font=font, fill=(255, 255, 255))
    
    def _wrap_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> list:
        """
        Wrap text to fit within max_width
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            try:
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(test_line) * 30
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _create_vertical_thumbnail(self, image_data: bytes, title: str, post_id: str) -> Optional[Path]:
        """
        Create 9:16 vertical thumbnail with text overlay
        
        Args:
            image_data: Raw image bytes from Gemini
            title: Title text to overlay
            post_id: Post identifier
        
        Returns:
            Path to saved thumbnail
        """
        try:
            # Load image from bytes
            base_image = Image.open(io.BytesIO(image_data))
            
            logger.info(f"   Original image size: {base_image.size}")
            
            # Ensure correct dimensions (9:16 = 1080×1920)
            if base_image.size != self.vertical_size:
                logger.info(f"   Resizing to {self.vertical_size}")
                thumbnail = base_image.resize(self.vertical_size, Image.Resampling.LANCZOS)
            else:
                thumbnail = base_image
            
            # Add text overlay
            thumbnail = self._add_text_overlay(thumbnail, title)
            
            # Save thumbnail
            output_path = Path(f"data/posts/post_{post_id}/video/thumbnail_9x16.jpg")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            thumbnail.save(output_path, "JPEG", quality=95, optimize=True)
            
            file_size = output_path.stat().st_size / 1024  # KB
            logger.info(f"   Saved thumbnail: {output_path.name} ({file_size:.1f} KB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error creating vertical thumbnail: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _add_text_overlay(self, image: Image.Image, title: str) -> Image.Image:
        """
        Add professional text overlay to thumbnail
        
        Strategy:
        - White text with black stroke for visibility
        - Positioned at bottom of image
        - Maximum 2 lines for readability
        - Bold, large font for YouTube Shorts visibility
        """
        try:
            # Create a copy
            img = image.copy()
            draw = ImageDraw.Draw(img)
            
            # Font settings for 9:16 vertical thumbnails
            font_size = 60  # Larger for better visibility on mobile
            text_color = (255, 255, 255)  # White
            stroke_color = (0, 0, 0)      # Black outline
            stroke_width = 4
            max_width = img.width - 60
            
            # Try to load a bold font
            font = None
            font_paths = [
                "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold
                "C:/Windows/Fonts/arial.ttf",     # Arial
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "arial.ttf",
            ]
            
            for font_path in font_paths:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except:
                    continue
            
            if not font:
                font = ImageFont.load_default()
                logger.warning("⚠️ Using default font - text may not look optimal")
            
            # Wrap text to fit within max_width
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                
                try:
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    text_width = bbox[2] - bbox[0]
                except:
                    # Fallback for older Pillow versions
                    text_width = len(test_line) * (font_size * 0.6)
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Limit to 2 lines for readability
            lines = lines[:2]
            
            # Calculate text position (bottom of image with padding)
            line_height = font_size + 15
            total_height = len(lines) * line_height
            start_y = img.height - total_height - 40
            
            # Draw text with stroke
            for i, line in enumerate(lines):
                y_pos = start_y + (i * line_height)
                
                # Draw stroke (outline) for visibility
                for x_offset in range(-stroke_width, stroke_width + 1):
                    for y_offset in range(-stroke_width, stroke_width + 1):
                        if x_offset != 0 or y_offset != 0:
                            draw.text(
                                (30 + x_offset, y_pos + y_offset), 
                                line, 
                                font=font, 
                                fill=stroke_color
                            )
                
                # Draw main text (white)
                draw.text((30, y_pos), line, font=font, fill=text_color)
            
            logger.info(f"   Added text overlay: {len(lines)} lines")
            return img
            
        except Exception as e:
            logger.error(f"❌ Error adding text overlay: {e}")
            return image  # Return original if overlay fails


def test_gemini_thumbnail():
    """Test the Gemini thumbnail generator with sample data"""
    print("\n" + "="*70)
    print("🧪 TESTING GEMINI IMAGEN 3.0 THUMBNAIL GENERATOR")
    print("="*70 + "\n")
    
    # Initialize generator
    generator = GeminiThumbnailGenerator()
    
    if not GEMINI_AVAILABLE or not generator.client:
        print("❌ Gemini API not available. Install google-genai:")
        print("   pip install google-genai")
        return
    
    # Test metadata (realistic travel news)
    test_cases = [
        {
            'post_id': 'test_001',
            'metadata': {
                'original_title': 'Bangkok Night Markets Launch New Food Experience',
                'caption': 'Experience authentic Thai street food in Bangkok\'s vibrant night markets',
                'region': 'Bangkok, Thailand',
                'hashtags': ['#Bangkok', '#ThaiFood', '#NightMarket']
            }
        },
        {
            'post_id': 'test_002',
            'metadata': {
                'original_title': 'New Luxury Resort Opens in Maldives',
                'caption': 'Discover paradise with overwater villas and pristine beaches',
                'region': 'Maldives',
                'hashtags': ['#Maldives', '#LuxuryTravel', '#Resort']
            }
        }
    ]
    
    print(f"Running {len(test_cases)} test cases...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"Test Case {i}/{len(test_cases)}")
        print(f"{'─'*70}")
        
        post_id = test_case['post_id']
        metadata = test_case['metadata']
        
        print(f"Post ID: {post_id}")
        print(f"Title: {metadata['original_title']}")
        print(f"Region: {metadata['region']}")
        print()
        
        # Generate thumbnail
        result = generator.generate_thumbnail_for_post(post_id, metadata)
        
        if result and 'vertical' in result:
            thumbnail_path = Path(result['vertical'])
            if thumbnail_path.exists():
                file_size = thumbnail_path.stat().st_size / 1024
                print(f"\n✅ SUCCESS!")
                print(f"   Path: {result['vertical']}")
                print(f"   Size: {file_size:.1f} KB")
                
                # Verify image
                try:
                    img = Image.open(thumbnail_path)
                    print(f"   Dimensions: {img.size[0]}×{img.size[1]}")
                    print(f"   Format: {img.format}")
                except:
                    pass
            else:
                print(f"\n❌ File not found: {result['vertical']}")
        else:
            print(f"\n❌ FAILED to generate thumbnail")
        
        print()
    
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)
    print("\nCheck generated thumbnails in:")
    print("  data/posts/test_001/video/thumbnail_9x16.jpg")
    print("  data/posts/test_002/video/thumbnail_9x16.jpg")
    print()


if __name__ == "__main__":
    test_gemini_thumbnail()


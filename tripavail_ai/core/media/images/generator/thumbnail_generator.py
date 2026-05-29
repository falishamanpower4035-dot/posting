"""
Thumbnail Generator using Stability AI SDXL
Creates consistent, high-quality thumbnails for YouTube and Facebook
"""

import os
import base64
import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
import io

class ThumbnailGenerator:
    """Generate thumbnails using NanoBanana (AI Studio) with Stability fallback, plus text overlays"""
    
    def __init__(self):
        # API Keys (NanoBanana primary, Stability fallback)
        self.nanonob_api_key = os.getenv('NANOBNANA_API_KEY') or os.getenv('NANONOB_API_KEY')
        self.stability_api_key = os.getenv('STABILITY_API_KEY')
        try:
            from config import settings
            if not self.nanonob_api_key:
                self.nanonob_api_key = (
                    getattr(settings, 'NANOBNANA_API_KEY', None)
                    or getattr(settings, 'NANONOB_API_KEY', None)
                )
            if not self.stability_api_key:
                self.stability_api_key = getattr(settings, 'STABILITY_API_KEY', None)
        except ImportError:
            pass
        if self.nanonob_api_key:
            logger.info("NanoBanana API key loaded for thumbnails (primary)")
        if self.stability_api_key:
            logger.info("Stability AI API key loaded for thumbnails (fallback)")
        
        # Thumbnail dimensions - Only 9:16 for vertical videos
        self.vertical_size = (1080, 1920)  # 9:16 aspect ratio for YouTube Shorts, Instagram Reels, TikTok
        
        logger.info("Thumbnail Generator initialized (9:16 only; NanoBanana primary, Stability fallback)")
    
    def generate_thumbnail_for_post(self, post_id: str, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate 9:16 thumbnail for vertical videos
        Returns dict with path to generated thumbnail
        """
        try:
            # Extract content for thumbnail
            title = metadata.get('original_title', '')
            caption = metadata.get('caption', '')
            region = metadata.get('region', 'Unknown')
            hashtags = metadata.get('hashtags', [])
            
            # Create thumbnail prompt
            thumbnail_prompt = self._create_thumbnail_prompt(title, caption, region)
            
            # Try NanoBanana (Gemini) first
            base_image_data = self._generate_nanonob_thumbnail(thumbnail_prompt)
            if not base_image_data:
                # Fallback to Stability if NanoBanana not available
                base_image_data = self._generate_stability_thumbnail(thumbnail_prompt)
            if not base_image_data:
                logger.error(f"Failed to generate base thumbnail for post {post_id}")
                return {}
            
            # Create 9:16 thumbnail only
            thumbnails = {}
            
            # 9:16 thumbnail for vertical videos
            vertical_path = self._create_vertical_thumbnail(base_image_data, title, post_id)
            if vertical_path:
                thumbnails['vertical'] = str(vertical_path)
            
            logger.info(f"Generated 9:16 thumbnail for post {post_id}")
            return thumbnails
            
        except Exception as e:
            logger.error(f"Error generating thumbnail for post {post_id}: {e}")
            return {}
    
    def _create_thumbnail_prompt(self, title: str, caption: str, region: str) -> str:
        """Create an optimized prompt for thumbnail generation"""
        # Extract key visual elements
        visual_elements = []
        
        # Add region-specific elements
        if region and region != 'Unknown':
            visual_elements.append(f"beautiful {region} landscape")
        
        # Extract travel-related keywords from title/caption
        travel_keywords = ['travel', 'tourism', 'destination', 'city', 'beach', 'mountain', 'culture', 'adventure']
        found_keywords = [kw for kw in travel_keywords if kw.lower() in (title + caption).lower()]
        
        if found_keywords:
            visual_elements.extend(found_keywords[:2])  # Take top 2 keywords
        
        # Create the prompt (explicit 9:16 framing for NanoBanana)
        base_prompt = f"""Generate a cinematic travel thumbnail in vertical 9:16 format showing {', '.join(visual_elements) if visual_elements else 'a beautiful travel destination'}. 
        High contrast, vibrant colors, cinematic lighting, professional travel photography style, 
        eye-catching composition with clean negative space at the top for text, no actual text overlays,
        high resolution, detailed, realistic."""
        
        return base_prompt
    
    def _generate_stability_thumbnail(self, prompt: str) -> Optional[bytes]:
        """Generate base thumbnail using Stability AI SDXL (9:16 format)"""
        try:
            if not self.stability_api_key:
                logger.warning("Stability AI API key not found for thumbnail generation")
                return None
            
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            headers = {
                "Authorization": f"Bearer {self.stability_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": 8,  # Higher for more creative thumbnails
                "height": 1024,  # Square format (supported by SDXL)
                "width": 1024,   # Will be resized to 9:16 later
                "samples": 1,
                "steps": 25,  # Higher quality for thumbnails
                "style_preset": "photographic"
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            for artifact in result.get('artifacts', []):
                if artifact.get('finishReason') == 'SUCCESS':
                    image_data = base64.b64decode(artifact['base64'])
                    logger.info("Generated base thumbnail using Stability AI SDXL (9:16)")
                    return image_data
            
            return None
            
        except Exception as e:
            logger.error(f"Stability AI thumbnail generation error: {e}")
            return None

    def _generate_nanonob_thumbnail(self, prompt: str) -> Optional[bytes]:
        """Generate base thumbnail using NanoBanana (AI Studio) Imagen 3 with 9:16 aspect ratio.
        Returns raw image bytes if successful."""
        try:
            if not self.nanonob_api_key:
                logger.warning("NanoBanana API key not found for thumbnail generation")
                return None

            result = None
            using_nanobanana = False
            try:
                from nanobanana import Banana  # type: ignore
                using_nanobanana = True
            except Exception:
                using_nanobanana = False

            try:
                if using_nanobanana:
                    client = Banana(api_key=self.nanonob_api_key)  # type: ignore[name-defined]
                    result = client.images.generate(
                        model="imagen-3.0-generate",
                        prompt={"text": prompt + " | vertical 9:16 aspect ratio"}
                    )
                else:
                    url = f"https://generativelanguage.googleapis.com/v1beta/images:generate?key={self.nanonob_api_key}"
                    payload = {
                        "model": "imagen-3.0-generate",
                        "prompt": {"text": prompt},
                        "aspectRatio": "9:16"
                    }
                    headers = {"Content-Type": "application/json"}
                    resp = requests.post(url, headers=headers, json=payload, timeout=60)
                    resp.raise_for_status()
                    result = resp.json()

                # Extract image bytes from various possible shapes
                # 1) result.image or result["image"] with base64
                def _b64_to_bytes(val: Optional[str]) -> Optional[bytes]:
                    if not val:
                        return None
                    try:
                        return base64.b64decode(val)
                    except Exception:
                        return None

                # Common patterns
                if isinstance(result, dict):
                    # images: [{"b64": "..."}] or data: [{"b64_json": "..."}]
                    images = result.get("images") or result.get("data") or []  # type: ignore[assignment]
                    if isinstance(images, list) and images:
                        first = images[0]
                        if isinstance(first, dict):
                            return (
                                _b64_to_bytes(first.get("b64"))
                                or _b64_to_bytes(first.get("base64"))
                                or _b64_to_bytes(first.get("b64_json"))
                                or _b64_to_bytes(first.get("image_base64"))
                            )
                    # Google Images API style
                    preds = result.get("predictions") or result.get("candidates") or []
                    if isinstance(preds, list) and preds:
                        cand = preds[0]
                        if isinstance(cand, dict):
                            maybe = (
                                _b64_to_bytes(cand.get("bytes_base64"))
                                or _b64_to_bytes(cand.get("image"))
                                or _b64_to_bytes(cand.get("inline_data"))
                            )
                            if maybe:
                                return maybe
                    # direct field
                    direct = (
                        result.get("image_base64") or result.get("b64") or result.get("base64")
                    )
                    if direct:
                        maybe = _b64_to_bytes(direct)  # type: ignore[arg-type]
                        if maybe:
                            return maybe

                # If SDK returns an object with attributes
                try:
                    attr_img = getattr(result, "image", None)
                    if isinstance(attr_img, (bytes, bytearray)):
                        return bytes(attr_img)
                    if isinstance(attr_img, str):
                        maybe = _b64_to_bytes(attr_img)
                        if maybe:
                            return maybe
                except Exception:
                    pass

                logger.error("NanoBanana call succeeded but no image data found in response")
                # Try Vertex OAuth fallback if configured
                vertex_bytes = self._generate_vertex_imagen_thumbnail(prompt)
                if vertex_bytes:
                    return vertex_bytes
                return None

            except Exception as sdk_err:
                logger.error(f"NanoBanana SDK error: {sdk_err}")
                # Try Vertex OAuth fallback if configured
                vertex_bytes = self._generate_vertex_imagen_thumbnail(prompt)
                if vertex_bytes:
                    return vertex_bytes
                return None

        except Exception as e:
            logger.error(f"NanoBanana thumbnail generation error: {e}")
            return None

    def _generate_vertex_imagen_thumbnail(self, prompt: str) -> Optional[bytes]:
        """Fallback: Use Vertex AI Imagen 3 with OAuth (service account)."""
        try:
            project_id = os.getenv("GOOGLE_PROJECT_ID")
            location = os.getenv("GOOGLE_LOCATION", "us-central1")
            creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not (project_id and creds):
                return None

            try:
                import vertexai  # type: ignore
                from vertexai.preview.vision_models import ImageGenerationModel  # type: ignore
            except Exception as imp_err:
                logger.error(f"Vertex AI SDK not installed or unavailable: {imp_err}")
                return None

            try:
                vertexai.init(project=project_id, location=location)
                model = ImageGenerationModel.from_pretrained("imagen-3.0-generate")
                result = model.generate_images(
                    prompt=prompt + " | vertical 9:16 aspect ratio",
                    number_of_images=1,
                    aspect_ratio="9:16",
                )

                # Extract first image
                image_obj = None
                try:
                    images = getattr(result, "images", None) or []
                    image_obj = images[0] if images else None
                except Exception:
                    image_obj = None

                if image_obj is None:
                    return None

                # Convert to bytes
                try:
                    # Some SDK versions expose a PIL Image
                    from io import BytesIO
                    buf = BytesIO()
                    image_obj.save(buf, format="JPEG")  # type: ignore[attr-defined]
                    return buf.getvalue()
                except Exception:
                    pass

                try:
                    raw = getattr(image_obj, "_image_bytes", None)
                    if isinstance(raw, (bytes, bytearray)):
                        return bytes(raw)
                except Exception:
                    pass

                return None
            except Exception as gen_err:
                logger.error(f"Vertex Imagen generation error: {gen_err}")
                return None
        except Exception:
            return None
    
    def _create_vertical_thumbnail(self, base_image_data: bytes, title: str, post_id: str) -> Optional[Path]:
        """Create 9:16 vertical thumbnail with text overlay"""
        try:
            # Load base image
            base_image = Image.open(io.BytesIO(base_image_data))
            
            # Resize to 9:16 dimensions
            thumbnail = base_image.resize(self.vertical_size, Image.Resampling.LANCZOS)
            
            # Add text overlay
            thumbnail = self._add_text_overlay(thumbnail, title, "vertical")
            
            # Save thumbnail
            output_path = Path(f"data/posts/post_{post_id}/video/thumbnail_9x16.jpg")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            thumbnail.save(output_path, "JPEG", quality=95)
            logger.info(f"Created 9:16 thumbnail: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating 9:16 thumbnail: {e}")
            return None
    
    def _add_text_overlay(self, image: Image.Image, title: str, platform: str) -> Image.Image:
        """Add text overlay to thumbnail"""
        try:
            # Create a copy to avoid modifying original
            img = image.copy()
            draw = ImageDraw.Draw(img)
            
            # Font settings for 9:16 vertical thumbnails
            font_size = 50
            text_color = (255, 255, 255)  # White
            stroke_color = (0, 0, 0)      # Black outline
            stroke_width = 3
            max_width = img.width - 40
            
            # Try to load a bold font, fallback to default
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
            
            # Wrap text to fit within max_width
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
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
            
            # Calculate text position (bottom of image)
            line_height = font_size + 10
            total_height = len(lines) * line_height
            start_y = img.height - total_height - 20
            
            # Draw text with stroke
            for i, line in enumerate(lines):
                y_pos = start_y + (i * line_height)
                
                # Draw stroke (outline)
                for x_offset in range(-stroke_width, stroke_width + 1):
                    for y_offset in range(-stroke_width, stroke_width + 1):
                        if x_offset != 0 or y_offset != 0:
                            draw.text((20 + x_offset, y_pos + y_offset), line, 
                                    font=font, fill=stroke_color)
                
                # Draw main text
                draw.text((20, y_pos), line, font=font, fill=text_color)
            
            return img
            
        except Exception as e:
            logger.error(f"Error adding text overlay: {e}")
            return image  # Return original image if text overlay fails


def test_thumbnail_generator():
    """Test the thumbnail generator"""
    generator = ThumbnailGenerator()
    
    # Test metadata
    test_metadata = {
        'original_title': 'Amazing Travel Destination in Europe',
        'caption': 'Discover the beauty of European cities',
        'region': 'Europe',
        'hashtags': ['#travel', '#europe', '#tourism']
    }
    
    print("Testing Thumbnail Generator...")
    print("=" * 50)
    
    thumbnails = generator.generate_thumbnail_for_post("test_001", test_metadata)
    
    if thumbnails:
        print("✅ Thumbnails generated successfully!")
        for platform, path in thumbnails.items():
            print(f"  {platform}: {path}")
    else:
        print("❌ Failed to generate thumbnails")


if __name__ == "__main__":
    test_thumbnail_generator()

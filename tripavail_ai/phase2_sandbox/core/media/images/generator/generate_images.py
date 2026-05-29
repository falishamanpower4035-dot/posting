"""
Image Generation & Quality Assurance for TripAvail AI
Creates 9:16 cinematic travel images with OCR validation and branding
"""

import json
import os
import time
import base64
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
import requests
import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ImageGenerator:
    """Generates 9:16 cinematic travel images with quality assurance"""
    
    def __init__(self):
        """Initialize the image generator"""
        self.openai_client = OpenAI()
        
        # File paths
        self.posts_file = "data/posts.json"
        self.manifest_file = "data/image_manifest.json"
        self.image_log_file = "logs/image_log.txt"
        self.run_summary_file = "logs/run_summary.txt"
        
        # Directory paths
        self.staging_dir = "data/images/staging"
        self.approved_dir = "data/images/approved"
        self.rejected_dir = "data/images/rejected"
        self.assets_dir = "assets"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Setup logging
        logger.add(self.image_log_file, rotation="1 day", retention="7 days")
        
        # Image configuration
        self.image_size = "1024x1792"  # 9:16 aspect ratio (closest to 1080x1920)
        self.images_per_post = 3
        self.max_retries = 2
        
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.staging_dir,
            self.approved_dir,
            self.rejected_dir,
            self.assets_dir,
            "logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def ingest_posts(self) -> List[Dict[str, Any]]:
        """Step 1: Ingest posts from data/posts.json"""
        try:
            if not os.path.exists(self.posts_file):
                logger.error(f"Posts file {self.posts_file} not found")
                return []
            
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            
            # Validate schema and filter posts
            valid_posts = []
            for i, post in enumerate(posts):
                if self._validate_post_schema(post, i):
                    valid_posts.append(post)
            
            logger.info(f"Loaded {len(valid_posts)} valid posts for image generation")
            return valid_posts
            
        except Exception as e:
            logger.error(f"Error ingesting posts: {e}")
            return []
    
    def _validate_post_schema(self, post: Dict[str, Any], index: int) -> bool:
        """Validate post schema and check for required fields"""
        required_fields = ['caption', 'region', 'score']
        
        for field in required_fields:
            if field not in post:
                logger.warning(f"Post {index} missing required field: {field}")
                return False
        
        if not post.get('caption', '').strip():
            logger.warning(f"Post {index} has empty caption")
            return False
        
        return True
    
    def define_generation_plan(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Step 2: Define image generation plan for each post"""
        generation_plans = []
        
        for i, post in enumerate(posts):
            post_id = f"{i+1:03d}"
            caption = post.get('caption', '')
            region = post.get('region', 'Global')
            
            # Create cinematic prompt with news content
            prompt = self._create_cinematic_prompt(
                caption, 
                region,
                post.get('original_title', ''),
                post.get('original_summary', '')
            )
            
            plan = {
                'post_id': post_id,
                'original_post': post,
                'prompt': prompt,
                'images_to_generate': self.images_per_post,
                'target_size': self.image_size,
                'style_intent': 'cinematic photography, professional lighting, soft natural color grading, immersive travel mood'
            }
            
            generation_plans.append(plan)
        
        logger.info(f"Created generation plans for {len(generation_plans)} posts")
        return generation_plans
    
    def _create_cinematic_prompt(self, caption: str, region: str, original_title: str = "", original_summary: str = "") -> str:
        """Create a realistic photographic prompt for image generation based on actual news content"""
        # Clean caption for prompt (remove hashtags and TripAvail tagline)
        clean_caption = caption.replace('Plan your journey with TripAvail ✈️', '').strip()
        
        # Extract specific location/destination from the news content
        location_hint = self._extract_location_from_news(original_title, original_summary, clean_caption)
        
        prompt = f"""Create a vertical (9:16) high-resolution photograph of a REAL, AUTHENTIC travel destination. This must look like a genuine photograph taken by a professional travel photographer.

SPECIFIC REQUIREMENTS:
- Photograph the actual location mentioned in this news story: {location_hint}
- This is about: {original_title}
- News context: {original_summary}

PHOTOGRAPHIC STYLE (MANDATORY):
- Shot with professional DSLR camera (Canon EOS R5, Sony A7R IV, or Nikon D850)
- Natural daylight only - golden hour or blue hour lighting
- Authentic shadows and realistic depth of field
- True-to-life colors with natural saturation (NO over-saturation)
- Realistic textures: stone, sand, water, vegetation, architecture
- Natural perspective as if taken by a human photographer
- Include environmental context: sky, horizon, natural surroundings

ABSOLUTELY FORBIDDEN:
- NO digital art, AI art, or fantasy elements
- NO glowing effects, neon colors, or artificial lighting
- NO circuit board patterns, digital overlays, or futuristic elements
- NO cartoon-like or stylized appearance
- NO text, letters, signs, logos, or watermarks
- NO artificial or unrealistic colors
- NO composite or manipulated elements

REALISM REQUIREMENTS:
- Must look like a genuine travel photograph from a real camera
- Natural composition and framing
- Authentic travel destination that actually exists
- Realistic weather and lighting conditions
- Believable human perspective and scale

This should look like a photograph you would see in National Geographic or a professional travel magazine."""
        
        return prompt
    
    def _extract_location_from_news(self, title: str, summary: str, caption: str) -> str:
        """Extract specific location information from news content"""
        # Combine all text to find location clues
        full_text = f"{title} {summary} {caption}".lower()
        
        # Define location mappings based on the news content
        location_mappings = {
            "tulum": "Tulum, Mexico - Mayan ruins and beaches",
            "kotka": "Kotka, Finland - coastal city with light festival",
            "new hampshire": "New Hampshire, USA - mountains and lakes",
            "louvre": "Paris, France - Louvre Museum exterior",
            "finland": "Finland - Nordic landscape",
            "mexico": "Mexico - authentic Mexican destination",
            "americas": "North or South America - authentic regional landscape",
            "europe": "Europe - authentic European destination"
        }
        
        # Find the most specific location mentioned
        for keyword, location in location_mappings.items():
            if keyword in full_text:
                return location
        
        # Default based on region
        if "americas" in full_text:
            return "North America - authentic regional landscape"
        elif "europe" in full_text:
            return "Europe - authentic European destination"
        else:
            return "authentic travel destination"
    
    def generate_images(self, generation_plans: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Step 3: Generate images using DALL-E 3"""
        generated_images = {}
        
        for plan in generation_plans:
            post_id = plan['post_id']
            prompt = plan['prompt']
            
            logger.info(f"Generating {self.images_per_post} images for post {post_id}")
            
            # Create staging directory for this post
            post_staging_dir = os.path.join(self.staging_dir, post_id)
            os.makedirs(post_staging_dir, exist_ok=True)
            
            image_paths = []
            
            for i in range(self.images_per_post):
                try:
                    # Generate image with DALL-E 3
                    response = self.openai_client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size=self.image_size,
                        quality="standard",
                        n=1
                    )
                    
                    # Download and save image
                    image_url = response.data[0].url
                    image_path = os.path.join(post_staging_dir, f"image_{i+1}.png")
                    
                    self._download_image(image_url, image_path)
                    image_paths.append(image_path)
                    
                    logger.info(f"Generated image {i+1} for post {post_id}")
                    
                    # Rate limiting - wait between requests
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error generating image {i+1} for post {post_id}: {e}")
                    # Continue with other images even if one fails
            
            generated_images[post_id] = image_paths
        
        logger.info(f"Generated images for {len(generated_images)} posts")
        return generated_images
    
    def _download_image(self, url: str, filepath: str):
        """Download image from URL and save to file"""
        response = requests.get(url)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
    
    def quality_check(self, generated_images: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """Step 4: Quality check with OCR and GPT validation"""
        quality_results = {}
        
        for post_id, image_paths in generated_images.items():
            logger.info(f"Quality checking {len(image_paths)} images for post {post_id}")
            
            post_results = {
                'accepted': [],
                'rejected': [],
                'total_processed': len(image_paths)
            }
            
            for image_path in image_paths:
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found: {image_path}")
                    continue
                
                # Check image dimensions
                if not self._check_image_dimensions(image_path):
                    logger.warning(f"Image {image_path} has incorrect dimensions")
                    post_results['rejected'].append({
                        'path': image_path,
                        'reason': 'Incorrect dimensions'
                    })
                    continue
                
                # OCR text detection
                detected_text = self._detect_text_ocr(image_path)
                
                if not detected_text:
                    # No text found - accept immediately
                    post_results['accepted'].append({
                        'path': image_path,
                        'reason': 'No text detected'
                    })
                    logger.info(f"Image {image_path} accepted - no text detected")
                else:
                    # Text found - validate with GPT
                    is_valid = self._validate_text_with_gpt(detected_text)
                    
                    if is_valid:
                        post_results['accepted'].append({
                            'path': image_path,
                            'reason': f'Text validated: {detected_text}'
                        })
                        logger.info(f"Image {image_path} accepted - text validated")
                    else:
                        post_results['rejected'].append({
                            'path': image_path,
                            'reason': f'Invalid text detected: {detected_text}'
                        })
                        logger.warning(f"Image {image_path} rejected - invalid text")
            
            quality_results[post_id] = post_results
        
        return quality_results
    
    def _check_image_dimensions(self, image_path: str) -> bool:
        """Check if image has correct 1024x1792 dimensions"""
        try:
            with Image.open(image_path) as img:
                return img.size == (1024, 1792)
        except Exception as e:
            logger.error(f"Error checking dimensions for {image_path}: {e}")
            return False
    
    def _detect_text_ocr(self, image_path: str) -> str:
        """Enhanced text detection with multiple methods and higher sensitivity"""
        try:
            # Load image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return ""
            
            # Method 1: Try Tesseract OCR if available
            detected_text_ocr = self._try_tesseract_ocr(image_path)
            
            # Method 2: Visual pattern detection for suspicious text-like areas
            suspicious_patterns = self._detect_suspicious_patterns(image)
            
            # Method 3: Edge and contour analysis for text-like structures
            text_structures = self._detect_text_structures(image)
            
            # Combine all detections
            all_detections = []
            if detected_text_ocr.strip():
                all_detections.append(f"OCR: {detected_text_ocr}")
            if suspicious_patterns:
                all_detections.append(f"Suspicious patterns: {suspicious_patterns}")
            if text_structures:
                all_detections.append(f"Text structures: {text_structures}")
            
            combined_text = " | ".join(all_detections)
            
            if combined_text.strip():
                logger.warning(f"Text/patterns detected in {image_path}: {combined_text}")
                return combined_text
            else:
                logger.info(f"No text/patterns detected in {image_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Error in enhanced text detection for {image_path}: {e}")
            return ""
    
    def _try_tesseract_ocr(self, image_path: str) -> str:
        """Try Tesseract OCR if available, fallback to empty string"""
        try:
            import pytesseract
            pil_image = Image.open(image_path)
            
            # Configure tesseract for high sensitivity
            config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?;:()[]{}"\''
            
            # Try multiple image preprocessing
            text_results = []
            
            # Original image
            text = pytesseract.image_to_string(pil_image, config=config).strip()
            if text:
                text_results.append(text)
            
            # Convert to grayscale
            gray_image = pil_image.convert('L')
            text = pytesseract.image_to_string(gray_image, config=config).strip()
            if text and text not in text_results:
                text_results.append(text)
            
            # Increase contrast
            contrast_image = Image.eval(gray_image, lambda x: min(255, x * 1.5))
            text = pytesseract.image_to_string(contrast_image, config=config).strip()
            if text and text not in text_results:
                text_results.append(text)
            
            return " | ".join(text_results)
            
        except Exception as e:
            logger.debug(f"Tesseract OCR not available: {e}")
            return ""
    
    def _detect_text_structures(self, image: np.ndarray) -> str:
        """Detect text-like structures using computer vision"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_like_structures = []
            
            for contour in contours:
                # Calculate contour properties
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                if area < 100:  # Skip tiny contours
                    continue
                
                # Calculate aspect ratio
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Calculate rectangularity
                rect_area = w * h
                rectangularity = area / rect_area if rect_area > 0 else 0
                
                # Detect horizontal text-like structures
                if 2 < aspect_ratio < 10 and rectangularity > 0.6:
                    text_like_structures.append(f"Horizontal structure (AR:{aspect_ratio:.1f})")
                
                # Detect vertical text-like structures
                elif 0.1 < aspect_ratio < 0.5 and rectangularity > 0.6:
                    text_like_structures.append(f"Vertical structure (AR:{aspect_ratio:.1f})")
                
                # Detect square-like structures (could be letters)
                elif 0.7 < aspect_ratio < 1.4 and rectangularity > 0.7:
                    text_like_structures.append(f"Square structure (AR:{aspect_ratio:.1f})")
            
            # Detect regular patterns (common in text)
            # Use template matching to find repeated patterns
            pattern_count = self._detect_repeated_patterns(gray)
            if pattern_count > 3:
                text_like_structures.append(f"Repeated patterns ({pattern_count})")
            
            return " | ".join(text_like_structures) if text_like_structures else ""
            
        except Exception as e:
            logger.error(f"Error in text structure detection: {e}")
            return ""
    
    def _detect_repeated_patterns(self, gray_image: np.ndarray) -> int:
        """Detect repeated patterns that might indicate text"""
        try:
            # Resize image for faster processing
            small = cv2.resize(gray_image, (200, 200))
            
            # Use template matching to find repeated patterns
            pattern_count = 0
            
            # Define small template sizes (typical letter sizes)
            template_sizes = [(8, 8), (12, 12), (16, 16)]
            
            for template_size in template_sizes:
                # Create a template from a small region
                template = small[50:50+template_size[1], 50:50+template_size[0]]
                
                # Perform template matching
                result = cv2.matchTemplate(small, template, cv2.TM_CCOEFF_NORMED)
                
                # Find matches above threshold
                locations = np.where(result >= 0.7)
                matches = len(locations[0])
                
                if matches > 2:  # More than 2 matches suggests repeated pattern
                    pattern_count += matches
            
            return pattern_count
            
        except Exception as e:
            logger.debug(f"Error in pattern detection: {e}")
            return 0
    
    def _detect_suspicious_patterns(self, image: np.ndarray) -> str:
        """Detect suspicious text-like patterns using computer vision"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect horizontal lines (common in text)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Detect vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # Detect rectangular shapes (text boxes)
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rectangular_shapes = 0
            
            for contour in contours:
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular
                if len(approx) >= 4:
                    area = cv2.contourArea(contour)
                    if area > 100:  # Filter out tiny shapes
                        rectangular_shapes += 1
            
            # Detect edge density (text areas have high edge density)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Compile suspicious indicators
            suspicious_indicators = []
            
            if np.sum(horizontal_lines > 0) > 1000:
                suspicious_indicators.append("High horizontal line density")
            
            if np.sum(vertical_lines > 0) > 1000:
                suspicious_indicators.append("High vertical line density")
            
            if rectangular_shapes > 5:
                suspicious_indicators.append(f"Multiple rectangular shapes ({rectangular_shapes})")
            
            if edge_density > 0.1:  # More than 10% edge pixels
                suspicious_indicators.append(f"High edge density ({edge_density:.2f})")
            
            return " | ".join(suspicious_indicators) if suspicious_indicators else ""
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return ""
    
    def _validate_text_with_gpt(self, text: str) -> bool:
        """Enhanced GPT validation for detected text and suspicious patterns"""
        try:
            prompt = f"""You are analyzing a computer vision detection report from a travel photograph. The report describes what the system detected in the image.

Detection Report: "{text}"

IMPORTANT: This is a SYSTEM REPORT describing what was found, NOT actual text visible in the image.

Analyze if the detection report indicates:
1. Actual readable text/words visible in the image itself
2. Suspicious patterns that look like text (but aren't readable)
3. Technical analysis results (which are NOT text in the image)

Answer format: YES/NO - [reason]

YES = The image contains actual readable text/words that should be rejected
NO = No actual readable text found in the image (only technical analysis)

Examples:
- "OCR: Hello World" = YES (actual readable text)
- "Suspicious patterns: High line density" = NO (technical analysis, not text in image)
- "Text structures: Repeated patterns" = NO (technical analysis, not text in image)"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are analyzing computer vision detection reports. Distinguish between actual text in images vs technical analysis reports."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            
            answer = response.choices[0].message.content.strip().upper()
            logger.info(f"GPT validation result: {answer}")
            
            # Return True if GPT says NO (no actual text in image)
            return answer.startswith("NO")
            
        except Exception as e:
            logger.error(f"Error validating text with GPT: {e}")
            # If GPT validation fails, err on the side of caution and reject
            return False
    
    def organize_outputs(self, quality_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Step 6: Organize outputs and create manifest"""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "source": "TripAvail AI Image Generator",
            "total_posts": len(quality_results),
            "posts": []
        }
        
        for post_id, results in quality_results.items():
            # Create approved directory for this post
            post_approved_dir = os.path.join(self.approved_dir, post_id)
            post_rejected_dir = os.path.join(self.rejected_dir, post_id)
            os.makedirs(post_approved_dir, exist_ok=True)
            os.makedirs(post_rejected_dir, exist_ok=True)
            
            # Move accepted images
            accepted_paths = []
            for i, accepted in enumerate(results['accepted']):
                old_path = accepted['path']
                new_path = os.path.join(post_approved_dir, f"img{i+1:02d}.png")
                
                try:
                    os.rename(old_path, new_path)
                    accepted_paths.append(new_path)
                except Exception as e:
                    logger.error(f"Error moving accepted image: {e}")
            
            # Move rejected images
            rejected_paths = []
            for rejected in results['rejected']:
                old_path = rejected['path']
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"bad_{timestamp}.png"
                new_path = os.path.join(post_rejected_dir, filename)
                
                try:
                    os.rename(old_path, new_path)
                    rejected_paths.append(new_path)
                except Exception as e:
                    logger.error(f"Error moving rejected image: {e}")
            
            # Determine if ready for video
            ready_for_video = len(accepted_paths) >= 2
            
            post_manifest = {
                "post_id": post_id,
                "aspect_ratio": "9:16",
                "accepted": len(accepted_paths),
                "rejected": len(rejected_paths),
                "ready_for_video": ready_for_video,
                "image_paths": accepted_paths,
                "rejected_paths": rejected_paths
            }
            
            manifest["posts"].append(post_manifest)
        
        # Save manifest
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created manifest with {len(manifest['posts'])} posts")
        return manifest
    
    def log_run_summary(self, manifest: Dict[str, Any], start_time: float):
        """Step 7: Log run summary"""
        end_time = time.time()
        duration = end_time - start_time
        
        total_images = sum(post['accepted'] + post['rejected'] for post in manifest['posts'])
        total_accepted = sum(post['accepted'] for post in manifest['posts'])
        total_rejected = sum(post['rejected'] for post in manifest['posts'])
        
        acceptance_rate = (total_accepted / total_images * 100) if total_images > 0 else 0
        avg_processing_time = duration / total_images if total_images > 0 else 0
        
        summary = f"""Run: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Posts processed: {manifest['total_posts']}
Images generated: {total_images}
Accepted: {total_accepted} ({acceptance_rate:.1f}%)
Rejected: {total_rejected} ({100-acceptance_rate:.1f}%)
Average processing: {avg_processing_time:.1f} s/image
Total duration: {duration:.1f} seconds"""
        
        with open(self.run_summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("Run summary logged")
        return summary
    
    def run_image_generation(self) -> bool:
        """Main method to run the complete image generation pipeline"""
        start_time = time.time()
        logger.info("Starting TripAvail AI Image Generation Pipeline")
        
        try:
            # Step 1: Ingest posts
            posts = self.ingest_posts()
            if not posts:
                logger.error("No valid posts found for image generation")
                return False
            
            # Step 2: Define generation plan
            generation_plans = self.define_generation_plan(posts)
            
            # Step 3: Generate images
            generated_images = self.generate_images(generation_plans)
            
            # Step 4: Quality check
            quality_results = self.quality_check(generated_images)
            
            # Step 6: Organize outputs
            manifest = self.organize_outputs(quality_results)
            
            # Step 7: Log summary
            summary = self.log_run_summary(manifest, start_time)
            
            logger.info("Image generation pipeline completed successfully")
            print(f"\n[SUCCESS] Image Generation Complete!")
            print(summary)
            
            return True
            
        except Exception as e:
            logger.error(f"Image generation pipeline failed: {e}")
            return False


def main():
    """Main function to run image generation"""
    generator = ImageGenerator()
    success = generator.run_image_generation()
    
    if success:
        print("\n[READY] Images are ready for Day 6 video assembly!")
    else:
        print("\n[ERROR] Image generation failed. Check logs for details.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Destination Image Generator for Long Videos
Searches for horizontal (16:9) images from Pixabay → Pexels → Unsplash → Shutterstock
NO AI fallback - waits for next day if all services fail
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from PIL import Image
import io
from loguru import logger
from dotenv import load_dotenv

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

load_dotenv()


class DestinationImageGeneratorLong:
    """
    Generates horizontal (16:9) images for long videos
    Priority: Pixabay → Pexels → Unsplash → Shutterstock
    """
    
    def __init__(self):
        # API Keys (from settings_long)
        self.pixabay_api_key = settings_long.PIXABAY_API_KEY_LONG
        self.pexels_api_key = settings_long.PEXELS_API_KEY_LONG
        self.unsplash_access_key = settings_long.UNSPLASH_ACCESS_KEY_LONG
        self.shutterstock_access_token = settings_long.SHUTTERSTOCK_ACCESS_TOKEN_LONG or os.getenv('SHUTTERSTOCK_ACCESS_TOKEN')
        
        # Image settings - RELAXED to get more images (preprocessing handles conversion)
        self.orientation = "horizontal"  # Horizontal only (preprocessing will convert to 16:9)
        self.image_type = "photo"  # Photos only (no illustrations/vectors)
        # RELAXED validation: Accept wider range, preprocessing will handle conversion
        # Preprocessing can handle 1.5-2.0 aspect ratios and resize/crop to 16:9
        self.min_resolution = (1280, 720)  # Minimum 1280x720 (can be upscaled to 1920x1080)
        self.target_resolution = (1920, 1080)  # Target resolution (exact 16:9 after preprocessing)
        self.aspect_ratio_min = 1.5  # Relaxed minimum (3:2, can be cropped to 16:9)
        self.aspect_ratio_max = 2.0  # Relaxed maximum (21:9, can be cropped to 16:9)
        # STRICT mode for final validation (used after preprocessing)
        self.strict_aspect_ratio_min = 1.75  # Strict 16:9 minimum for already-processed images
        self.strict_aspect_ratio_max = 1.80  # Strict 16:9 maximum for already-processed images
        
        # Cache settings
        self.cache_dir = Path(settings_long.CACHE_DIR)
        self.cache_expiry_days = settings_long.IMAGE_CACHE_EXPIRY_DAYS  # 30 days
        
        # Search settings
        self.per_page = settings_long.IMAGE_SEARCH_PER_PAGE  # 20
        self.max_pages = settings_long.IMAGE_SEARCH_MAX_PAGES  # 5
        self.rate_limit_delay = settings_long.IMAGE_SEARCH_RATE_LIMIT_DELAY  # 10 seconds
        
        # Priority order
        self.service_priority = settings_long.IMAGE_SEARCH_PRIORITY  # ["pixabay", "pexels", "unsplash", "shutterstock"]
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.pixabay_requests = 0
        self.pexels_requests = 0
        self.unsplash_requests = 0
        self.shutterstock_requests = 0
        self.last_reset_date = datetime.now().date()
        
        logger.info("Destination Image Generator Long initialized")
        logger.info(f"Service priority: {' → '.join(self.service_priority)}")
    
    def search_pixabay(self, query: str, count: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search Pixabay (HIGHEST PRIORITY) for horizontal photos
        
        Args:
            query: Search query
            count: Number of results (max 200 per page)
            page: Page number
            
        Returns:
            List of image dictionaries
        """
        try:
            if not self.pixabay_api_key:
                logger.warning("Pixabay API key not found")
                return []
            
            url = "https://pixabay.com/api/"
            params = {
                "key": self.pixabay_api_key,
                "q": query,
                "image_type": "photo",  # Photos only
                "orientation": "horizontal",  # Horizontal only
                "per_page": min(count, 200),  # Max 200 per page
                "page": page,
                "order": "popular",  # Popular images first
                "safesearch": "true",  # Safe search enabled
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('hits', [])
            
            # Normalize results - RELAXED to accept wider range
            normalized: List[Dict[str, Any]] = []
            for hit in hits:
                # Validate aspect ratio (RELAXED: accepts 1.5-2.0, preprocessing will fix)
                width = hit.get('imageWidth', 0)
                height = hit.get('imageHeight', 0)
                
                if width and height:
                    aspect_ratio = width / height
                    # RELAXED: Accept wider aspect ratio range (preprocessing handles conversion)
                    if self.aspect_ratio_min <= aspect_ratio <= self.aspect_ratio_max:
                        # RELAXED: Accept lower resolution (can be upscaled)
                        if width >= self.min_resolution[0] and height >= self.min_resolution[1]:
                            normalized.append({
                                "preview_url": hit.get('webformatURL', ''),  # Preview URL
                                "full_url": hit.get('largeImageURL', ''),  # Full size URL
                                "width": width,
                                "height": height,
                                "aspect_ratio": aspect_ratio,
                                "tags": hit.get('tags', ''),
                                "description": hit.get('tags', ''),  # Use tags as description
                                "service": "pixabay",
                                "_raw": hit,
                            })
            
            self.pixabay_requests += 1
            logger.info(f"Pixabay search returned {len(normalized)} valid horizontal images for query: '{query}' (page {page})")
            return normalized
            
        except Exception as e:
            logger.error(f"Pixabay API error: {e}")
            return []
    
    def search_pexels(self, query: str, count: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search Pexels for horizontal photos
        
        Args:
            query: Search query
            count: Number of results (max 80 per page)
            page: Page number
            
        Returns:
            List of image dictionaries
        """
        try:
            if not self.pexels_api_key:
                logger.warning("Pexels API key not found")
                return []
            
            url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": self.pexels_api_key
            }
            params = {
                "query": query,
                "per_page": min(count, 80),  # Max 80 per page
                "page": page,
                "orientation": "landscape",  # Horizontal/landscape only
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            photos = data.get('photos', [])
            
            # Normalize results
            normalized: List[Dict[str, Any]] = []
            for photo in photos:
                width = photo.get('width', 0)
                height = photo.get('height', 0)
                
                if width and height:
                    aspect_ratio = width / height
                    if self.aspect_ratio_min <= aspect_ratio <= self.aspect_ratio_max:
                        if width >= self.min_resolution[0] and height >= self.min_resolution[1]:
                            # Get largest available size
                            src = photo.get('src', {})
                            normalized.append({
                                "preview_url": src.get('large', src.get('medium', '')),
                                "full_url": src.get('original', src.get('large', '')),
                                "width": width,
                                "height": height,
                                "aspect_ratio": aspect_ratio,
                                "description": photo.get('alt', ''),
                                "photographer": photo.get('photographer', ''),
                                "service": "pexels",
                                "_raw": photo,
                            })
            
            self.pexels_requests += 1
            logger.info(f"Pexels search returned {len(normalized)} valid horizontal images for query: '{query}' (page {page})")
            return normalized
            
        except Exception as e:
            logger.error(f"Pexels API error: {e}")
            return []
    
    def search_unsplash(self, query: str, count: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search Unsplash for horizontal photos
        
        Args:
            query: Search query
            count: Number of results (max 30 per page)
            page: Page number
            
        Returns:
            List of image dictionaries
        """
        try:
            if not self.unsplash_access_key:
                logger.warning("Unsplash API key not found")
                return []
            
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}"
            }
            params = {
                "query": query,
                "per_page": min(count, 30),  # Max 30 per page
                "page": page,
                "orientation": "landscape",  # Horizontal/landscape only
                "content_filter": "high",
                "order_by": "relevant",
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # Normalize results
            normalized: List[Dict[str, Any]] = []
            for result in results:
                width = result.get('width', 0)
                height = result.get('height', 0)
                
                if width and height:
                    aspect_ratio = width / height
                    if self.aspect_ratio_min <= aspect_ratio <= self.aspect_ratio_max:
                        if width >= self.min_resolution[0] and height >= self.min_resolution[1]:
                            urls = result.get('urls', {})
                            normalized.append({
                                "preview_url": urls.get('regular', urls.get('small', '')),
                                "full_url": urls.get('full', urls.get('regular', '')),
                                "width": width,
                                "height": height,
                                "aspect_ratio": aspect_ratio,
                                "description": result.get('description', result.get('alt_description', '')),
                                "service": "unsplash",
                                "_raw": result,
                            })
            
            self.unsplash_requests += 1
            logger.info(f"Unsplash search returned {len(normalized)} valid horizontal images for query: '{query}' (page {page})")
            return normalized
            
        except Exception as e:
            logger.error(f"Unsplash API error: {e}")
            return []
    
    def search_shutterstock(self, query: str, count: int = 20, page: int = 1) -> List[Dict[str, Any]]:
        """
        Search Shutterstock for horizontal photos
        
        Args:
            query: Search query
            count: Number of results (max 20 per page)
            page: Page number
            
        Returns:
            List of image dictionaries
        """
        try:
            if not self.shutterstock_access_token:
                logger.warning("Shutterstock access token not found")
                return []
            
            url = "https://api.shutterstock.com/v2/images/search"
            headers = {
                "Authorization": f"Bearer {self.shutterstock_access_token}",
            }
            params = {
                "query": query,
                "image_type": "photo",
                "orientation": "horizontal",  # Horizontal only
                "page": page,
                "per_page": min(count, 20),  # Max 20 per page
                "sort": "relevance",
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("data", [])
            
            # Normalize results
            normalized: List[Dict[str, Any]] = []
            for item in results:
                assets = item.get("assets", {})
                preview = (assets.get("preview_1000") or {}).get("url") or (assets.get("preview") or {}).get("url")
                
                width = item.get("width", 0)
                height = item.get("height", 0)
                
                if width and height and preview:
                    aspect_ratio = width / height
                    if self.aspect_ratio_min <= aspect_ratio <= self.aspect_ratio_max:
                        if width >= self.min_resolution[0] and height >= self.min_resolution[1]:
                            normalized.append({
                                "preview_url": preview,
                                "full_url": preview,  # Shutterstock preview is usually sufficient
                                "width": width,
                                "height": height,
                                "aspect_ratio": aspect_ratio,
                                "description": item.get("description", ""),
                                "service": "shutterstock",
                                "_raw": item,
                            })
            
            self.shutterstock_requests += 1
            logger.info(f"Shutterstock search returned {len(normalized)} valid horizontal images for query: '{query}' (page {page})")
            return normalized
            
        except Exception as e:
            logger.error(f"Shutterstock API error: {e}")
            return []
    
    def search_all_services(self, query: str, category: str = None, total_needed: int = 60) -> List[Dict[str, Any]]:
        """
        Search all services in priority order until we have enough images
        
        Args:
            query: Search query
            category: Image category (attractions, activities, etc.)
            total_needed: Total number of images needed
            
        Returns:
            List of unique images from all services
        """
        all_images = []
        seen_urls = set()
        
        # Determine service order based on category or use default priority
        if category and category in settings_long.IMAGE_SEARCH_DISTRIBUTION:
            preferred_service = settings_long.IMAGE_SEARCH_DISTRIBUTION[category]
            # Start with preferred service, then follow priority
            service_order = [preferred_service] + [s for s in self.service_priority if s != preferred_service]
        else:
            service_order = self.service_priority
        
        logger.info(f"Searching for {total_needed} images with query: '{query}' (category: {category})")
        logger.info(f"Service order: {' → '.join(service_order)}")
        
        # Track failed services to skip quickly on repeated failures
        failed_services = set()
        
        # Search each service
        for service in service_order:
            if len(all_images) >= total_needed:
                break
            
            # Skip if service has already failed
            if service in failed_services:
                logger.debug(f"Skipping {service} (already failed for this query)")
                continue
            
            logger.info(f"Searching {service}...")
            
            service_failed = False
            consecutive_400_errors = 0
            
            # Search multiple pages if needed
            for page in range(1, self.max_pages + 1):
                if len(all_images) >= total_needed or service_failed:
                    break
                
                try:
                    # Call appropriate search method
                    if service == "pixabay":
                        results = self.search_pixabay(query, count=self.per_page, page=page)
                    elif service == "pexels":
                        results = self.search_pexels(query, count=self.per_page, page=page)
                    elif service == "unsplash":
                        results = self.search_unsplash(query, count=self.per_page, page=page)
                    elif service == "shutterstock":
                        results = self.search_shutterstock(query, count=self.per_page, page=page)
                    else:
                        logger.warning(f"Unknown service: {service}")
                        continue
                    
                    # Reset consecutive errors on success
                    consecutive_400_errors = 0
                    
                    # Add unique images
                    for img in results:
                        img_url = img.get('full_url') or img.get('preview_url', '')
                        if img_url and img_url not in seen_urls:
                            seen_urls.add(img_url)
                            all_images.append(img)
                            
                            if len(all_images) >= total_needed:
                                break
                    
                    # Rate limiting
                    if page < self.max_pages:
                        time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    error_msg = str(e)
                    # Check if it's a 400 Bad Request (query too long/complex)
                    if "400" in error_msg or "Bad Request" in error_msg:
                        consecutive_400_errors += 1
                        # FAIL FAST: After 2 consecutive 400 errors, skip this service entirely
                        if consecutive_400_errors >= 2:
                            logger.warning(f"{service} API: Multiple 400 Bad Request errors. Skipping {service} for this query.")
                            failed_services.add(service)
                            service_failed = True
                            break
                        else:
                            logger.debug(f"{service} API error (400 Bad Request) on page {page}, continuing...")
                    elif "NameResolutionError" in error_msg or "Failed to resolve" in error_msg:
                        # Network DNS errors - skip this service
                        logger.warning(f"{service} API: Network DNS error. Skipping {service} for this query.")
                        failed_services.add(service)
                        service_failed = True
                        break
                    else:
                        logger.error(f"Error searching {service} page {page}: {e}")
                    continue
        
        # FALLBACK: If we don't have enough images, retry with even more relaxed criteria
        if len(all_images) < total_needed * 0.5:  # If we got less than 50% of needed
            logger.warning(f"Initial search returned only {len(all_images)}/{total_needed} images. Retrying with more relaxed criteria...")
            
            # Store current criteria
            original_aspect_min = self.aspect_ratio_min
            original_aspect_max = self.aspect_ratio_max
            original_min_res = self.min_resolution
            
            # Apply more relaxed criteria (accept even wider range)
            self.aspect_ratio_min = 1.3  # Even more relaxed (allows 4:3 = 1.33, etc.)
            self.aspect_ratio_max = 2.5  # Even more relaxed (allows ultrawide)
            self.min_resolution = (1024, 576)  # Lower minimum (720p-ish)
            
            logger.info(f"Retrying with relaxed criteria: AR {self.aspect_ratio_min}-{self.aspect_ratio_max}, min {self.min_resolution[0]}x{self.min_resolution[1]}")
            
            # Retry search with relaxed criteria
            for service in service_order:
                if len(all_images) >= total_needed:
                    break
                
                try:
                    for page in range(1, self.max_pages + 1):
                        if len(all_images) >= total_needed:
                            break
                        
                        try:
                            if service == "pixabay":
                                results = self.search_pixabay(query, count=self.per_page, page=page)
                            elif service == "pexels":
                                results = self.search_pexels(query, count=self.per_page, page=page)
                            elif service == "unsplash":
                                results = self.search_unsplash(query, count=self.per_page, page=page)
                            elif service == "shutterstock":
                                results = self.search_shutterstock(query, count=self.per_page, page=page)
                            else:
                                continue
                            
                            # Add unique images
                            for img in results:
                                img_url = img.get('full_url') or img.get('preview_url', '')
                                if img_url and img_url not in seen_urls:
                                    seen_urls.add(img_url)
                                    all_images.append(img)
                                    if len(all_images) >= total_needed:
                                        break
                            
                            if page < self.max_pages:
                                time.sleep(self.rate_limit_delay)
                        except Exception as e:
                            logger.debug(f"Error in fallback search {service} page {page}: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error in fallback search {service}: {e}")
                    continue
            
            # Restore original criteria
            self.aspect_ratio_min = original_aspect_min
            self.aspect_ratio_max = original_aspect_max
            self.min_resolution = original_min_res
            
            logger.info(f"Fallback search completed. Total images: {len(all_images)}/{total_needed}")
        
        logger.info(f"Found {len(all_images)} unique horizontal images from all services")
        return all_images[:total_needed]
    
    def validate_image(self, image_path: Path) -> bool:
        """
        Validate image can be processed to 16:9 (RELAXED - accepts wider range)
        
        Args:
            image_path: Path to image file
            
        Returns:
            True if valid (can be processed), False otherwise
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # RELAXED validation: Accept images that can be processed to 16:9
                
                # Minimum resolution: Accept 1280x720 or larger (can be upscaled/cropped)
                min_width = 1280
                min_height = 720
                if width < min_width or height < min_height:
                    logger.debug(f"Image too small: {width}x{height} (min: {min_width}x{min_height})")
                    return False
                
                # RELAXED aspect ratio: Accept 1.5-2.0 (can be cropped/resized to 16:9)
                # This includes: 3:2 (1.5), 16:9 (1.78), 21:9 (2.33), etc.
                aspect_ratio = width / height
                relaxed_min = 1.5  # Accept wider range
                relaxed_max = 2.0
                
                if aspect_ratio < relaxed_min or aspect_ratio > relaxed_max:
                    logger.debug(f"Image aspect ratio too extreme: {aspect_ratio:.2f} (acceptable: {relaxed_min:.2f}-{relaxed_max:.2f})")
                    return False
                
                # Image can be processed to 16:9
                logger.debug(f"✅ Image validated (can be processed): {width}x{height} (AR: {aspect_ratio:.2f})")
                return True
                
        except Exception as e:
            logger.error(f"Error validating image {image_path}: {e}")
            return False
    
    def preprocess_image_to_1920x1080(self, image_path: Path) -> bool:
        """
        Pre-process image to exactly 1920x1080 (16:9) - IMPROVED to handle wider range
        
        Strategy:
        1. If image is larger than 1920x1080: Resize down to 1920x1080 (maintains aspect ratio)
        2. If image is smaller than 1920x1080: Scale up to 1920x1080 (maintains aspect ratio)
        3. If aspect ratio is not exactly 16:9: Crop to 16:9 (centered crop)
        4. IMPROVED: Handle edge cases (very wide/tall images, small images)
        
        Args:
            image_path: Path to image file (will be modified in-place)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            target_width, target_height = self.target_resolution
            target_aspect = target_width / target_height  # 1.777... (16:9)
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (handle RGBA, P, etc.)
                if img.mode != 'RGB':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    else:
                        rgb_img.paste(img)
                    img = rgb_img
                
                original_width, original_height = img.size
                original_aspect = original_width / original_height
                
                # If image is already exactly 1920x1080 with correct aspect ratio, skip
                if original_width == target_width and original_height == target_height and abs(original_aspect - target_aspect) < 0.01:
                    logger.debug(f"Image already {target_width}x{target_height}, skipping preprocessing")
                    return True
                
                # IMPROVED: Handle very small images by upscaling first
                if original_width < target_width or original_height < target_height:
                    # Upscale to at least target size while maintaining aspect ratio
                    scale_factor = max(target_width / original_width, target_height / original_height)
                    new_width = int(original_width * scale_factor)
                    new_height = int(original_height * scale_factor)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    original_width, original_height = new_width, new_height
                    original_aspect = original_width / original_height
                
                # Step 1: Resize to fit within 1920x1080 (maintain aspect ratio)
                # Use LANCZOS for high-quality resampling
                if original_aspect > target_aspect:
                    # Image is wider than 16:9 - fit to height, crop width
                    new_height = target_height
                    new_width = int(original_width * (target_height / original_height))
                    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Crop width to exactly 1920 (centered)
                    left = (new_width - target_width) // 2
                    right = left + target_width
                    img_cropped = img_resized.crop((left, 0, right, target_height))
                elif original_aspect < target_aspect:
                    # Image is taller than 16:9 - fit to width, crop height
                    new_width = target_width
                    new_height = int(original_height * (target_width / original_width))
                    img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Crop height to exactly 1080 (centered)
                    top = (new_height - target_height) // 2
                    bottom = top + target_height
                    img_cropped = img_resized.crop((0, top, target_width, bottom))
                else:
                    # Aspect ratio is exactly 16:9 - just resize to 1920x1080
                    img_cropped = img.resize((target_width, target_height), Image.LANCZOS)
                
                # Verify final size
                if img_cropped.size != (target_width, target_height):
                    # Final safety check - resize if needed
                    img_cropped = img_cropped.resize((target_width, target_height), Image.LANCZOS)
                
                # Save processed image (overwrite original)
                img_cropped.save(image_path, 'JPEG', quality=95, optimize=True)
                
                logger.info(f"✅ Preprocessed image to {target_width}x{target_height}: {image_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def download_image(self, image_url: str, destination: Path) -> bool:
        """
        Download image from URL and save to destination
        
        Args:
            image_url: URL of image to download
            destination: Path to save image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save image
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # RELAXED: Validate image (accepts wider range, will be processed)
            if self.validate_image(destination):
                # Pre-process to exactly 1920x1080 (handles wider range of images)
                if self.preprocess_image_to_1920x1080(destination):
                    logger.info(f"✅ Downloaded, validated, and preprocessed image: {destination.name}")
                    return True
                else:
                    logger.warning(f"Image validation passed but preprocessing failed: {destination.name}")
                    destination.unlink()
                    return False
            else:
                logger.debug(f"Downloaded image failed validation (too small or extreme aspect ratio): {destination.name}")
                destination.unlink()  # Delete invalid image
                return False
                
        except Exception as e:
            logger.error(f"Error downloading image from {image_url}: {e}")
            if destination.exists():
                destination.unlink()
            return False
    
    def get_cached_images(self, destination: str, category: str, day_number: Optional[int] = None) -> List[Path]:
        """
        Get cached images for a destination and category
        
        Args:
            destination: Destination name
            category: Image category
            day_number: Optional day number for per-day caching
            
        Returns:
            List of cached image paths
        """
        cache_category_dir = self.cache_dir / category
        if not cache_category_dir.exists():
            return []
        
        # Find images for this destination
        cached_images = []
        
        # Build search pattern
        if day_number is not None:
            # Search for day-specific cached images
            pattern = f"{destination}_day_{day_number}_{category}_*.jpg"
        else:
            # Search for general cached images (legacy)
            pattern = f"{destination}_{category}_*.jpg"
        
        for img_file in cache_category_dir.glob(pattern):
            # Check if cache is still valid (30 days)
            if img_file.stat().st_mtime > (datetime.now() - timedelta(days=self.cache_expiry_days)).timestamp():
                cached_images.append(img_file)
        
        # Also check day-specific directory if day_number is provided
        if day_number is not None:
            # Check in per-day image directory (not cache)
            images_dir = Path(settings_long.IMAGES_DIR) / destination / f"day_{day_number}" / category
            if images_dir.exists():
                for img_file in images_dir.glob("*.jpg"):
                    cached_images.append(img_file)
        
        return sorted(cached_images)
    
    def cache_image(self, image_path: Path, destination: str, category: str, image_data: Dict[str, Any], day_number: Optional[int] = None) -> Path:
        """
        Cache image for future use
        
        Args:
            image_path: Path to image file
            destination: Destination name
            category: Image category
            image_data: Image metadata
            day_number: Optional day number for per-day caching
            
        Returns:
            Path to cached image
        """
        cache_category_dir = self.cache_dir / category
        cache_category_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate cache filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if day_number is not None:
            cache_filename = f"{destination}_day_{day_number}_{category}_{timestamp}.jpg"
        else:
            cache_filename = f"{destination}_{category}_{timestamp}.jpg"
        cache_path = cache_category_dir / cache_filename
        
        # Copy image to cache
        import shutil
        shutil.copy2(image_path, cache_path)
        
        # Save metadata
        metadata_path = cache_path.with_suffix('.json')
        metadata = {
            "destination": destination,
            "category": category,
            "day_number": day_number,
            "cached_at": datetime.now().isoformat(),
            "image_data": image_data,
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Cached image: {cache_path}")
        return cache_path
    
    def generate_images_for_destination(
        self,
        destination: str,
        categories: List[str] = None,
        images_per_category: int = 12,
        use_cache: bool = True,
        day_number: Optional[int] = None
    ) -> Dict[str, List[Path]]:
        """
        Generate images for a destination across multiple categories
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            categories: List of categories (default: all categories)
            images_per_category: Number of images per category
            use_cache: Whether to use cached images
            day_number: Optional day number for per-day organization (e.g., 1, 2, 3)
            
        Returns:
            Dictionary mapping categories to lists of image paths
        """
        if categories is None:
            categories = ["attractions", "activities", "food_culture", "local_life", "scenic_views", "hotel_stay"]
        
        result = {}
        
        for category in categories:
            logger.info(f"Generating images for {destination} - {category}" + (f" (Day {day_number})" if day_number else "") + "...")
            
            # Determine image directory based on day_number
            if day_number is not None:
                # Per-day organization: data/long_videos/images/Bali/day_1/attractions/
                images_dir = Path(settings_long.IMAGES_DIR) / destination / f"day_{day_number}" / category
            else:
                # Legacy organization: data/long_videos/images/Bali/attractions/
                images_dir = Path(settings_long.IMAGES_DIR) / destination / category
            
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Check cache first (day-specific if day_number provided)
            if use_cache:
                cached_images = self.get_cached_images(destination, category, day_number=day_number)
                if len(cached_images) >= images_per_category:
                    logger.info(f"Using {len(cached_images)} cached images for {destination} - {category}" + (f" (Day {day_number})" if day_number else ""))
                    result[category] = cached_images[:images_per_category]
                    continue
            
            # Build search query
            query = f"{category} in {destination}"
            
            # Search for images
            images = self.search_all_services(query, category=category, total_needed=images_per_category)
            
            if not images:
                logger.warning(f"No images found for {destination} - {category}" + (f" (Day {day_number})" if day_number else ""))
                result[category] = []
                continue
            
            # Download images
            downloaded_images = []
            
            for i, img_data in enumerate(images):
                if len(downloaded_images) >= images_per_category:
                    break
                
                image_url = img_data.get('full_url') or img_data.get('preview_url', '')
                if not image_url:
                    continue
                
                # Generate filename with day number if provided
                if day_number is not None:
                    image_filename = f"{destination}_day_{day_number}_{category}_{i+1:03d}.jpg"
                else:
                    image_filename = f"{destination}_{category}_{i+1:03d}.jpg"
                
                image_path = images_dir / image_filename
                
                if self.download_image(image_url, image_path):
                    downloaded_images.append(image_path)
                    # Cache the image (with day_number in cache key if provided)
                    self.cache_image(image_path, destination, category, img_data, day_number=day_number)
            
            result[category] = downloaded_images
            logger.info(f"Generated {len(downloaded_images)} images for {destination} - {category}" + (f" (Day {day_number})" if day_number else ""))
        
        return result
    
    def generate_images_for_day_with_scenes(
        self,
        destination: str,
        day_number: int,
        voiceover_duration_seconds: float,
        scenes: List[Dict[str, Any]],
        day_location: Optional[str] = None,
        specific_locations: Optional[List[str]] = None,
        specific_dishes: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        """
        Generate images for a day using scene-level image prompts from blueprint segments
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            day_number: Day number (e.g., 1, 2, 3)
            voiceover_duration_seconds: Total voiceover duration in seconds
            scenes: List of scene dictionaries with image_prompt, order, experience_focus, etc.
            day_location: Day-specific city (e.g., "Kuta", "Ubud")
            specific_locations: List of exact locations/landmarks (for fallback)
            specific_dishes: List of exact dish names (for fallback)
            
        Returns:
            Dictionary mapping scene order to lists of image paths
        """
        logger.info(f"Generating images for Day {day_number} of {destination} (SCENE-BASED - voiceover: {voiceover_duration_seconds:.2f}s, {len(scenes)} scenes)")
        
        # Estimate total image count based on voiceover duration
        target_seconds_per_image = 2.5  # 2.5 seconds per image
        total_images_needed = int(voiceover_duration_seconds / target_seconds_per_image)
        
        # Distribute images across scenes (proportional to scene duration or evenly)
        # For now, distribute evenly across scenes
        images_per_scene = max(2, int(total_images_needed / len(scenes))) if scenes else total_images_needed
        
        # Check if images already exist (reuse existing if available)
        images_dir = Path(settings_long.IMAGES_DIR) / destination / f"day_{day_number}"
        
        if images_dir.exists():
            existing_images = list(images_dir.rglob("*.jpg"))
            if len(existing_images) >= total_images_needed * 0.8:  # If we have at least 80% of needed images
                logger.info(f"✅ Found {len(existing_images)} existing images for Day {day_number} (need ~{total_images_needed}), reusing them")
                # Group existing images by scene (if scene folders exist)
                scene_images = {}
                for scene in scenes:
                    scene_order = scene.get('order', 0)
                    scene_dir = images_dir / f"scene_{scene_order}"
                    if scene_dir.exists():
                        scene_images[scene_order] = list(scene_dir.glob("*.jpg"))[:images_per_scene]
                    else:
                        scene_images[scene_order] = []
                # Fill missing scenes from "all" folder
                all_dir = images_dir / "all"
                if all_dir.exists():
                    all_images = list(all_dir.glob("*.jpg"))
                    for scene_order in scene_images:
                        if len(scene_images[scene_order]) < images_per_scene:
                            needed = images_per_scene - len(scene_images[scene_order])
                            scene_images[scene_order].extend(all_images[:needed])
                            all_images = all_images[needed:]
                return scene_images
        
        # Ensure day-specific directory exists
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Simplify destination name
        dest_name = destination.split(',')[0].strip() if ',' in destination else destination
        
        # Global deduplication (track URLs to avoid downloading duplicates)
        seen_image_urls = set()
        seen_image_hashes = set()
        
        # Store images per scene
        scene_images = {}
        
        # Search for images per scene using scene-specific image_prompt
        for scene in scenes:
            scene_order = scene.get('order', 0)
            image_prompt = scene.get('image_prompt', '')
            experience_focus = scene.get('experience_focus', 'scenic_views')
            
            if not image_prompt:
                logger.warning(f"Scene {scene_order} has no image_prompt, skipping")
                scene_images[scene_order] = []
                continue
            
            logger.info(f"Scene {scene_order}: Searching images using prompt: '{image_prompt[:60]}...'")
            
            # Map experience_focus to image category
            category_map = {
                'transit': 'scenic_views',
                'arrival': 'scenic_views',
                'lodging_checkin': 'hotel_stay',
                'relaxation': 'hotel_stay',
                'food': 'food_culture',
                'nature': 'attractions',
                'culture': 'attractions',
                'adventure': 'attractions',
                'nightlife': 'local_life',
                'shopping': 'local_life'
            }
            category = category_map.get(experience_focus, 'scenic_views')
            
            # Build search query from image_prompt
            # Use search multiplier to account for validation failures
            search_multiplier = 2.5
            images_to_search = int(images_per_scene * search_multiplier)
            
            # Enhance query with destination and location if available
            # IMPORTANT: Simplify query to avoid API 400 errors
            # Extract key words from image_prompt (first 3-4 words + location)
            prompt_words = image_prompt.split()[:4]  # Take first 4 words max
            simplified_prompt = " ".join(prompt_words)
            
            query_parts = [simplified_prompt]
            if day_location:
                query_parts.append(day_location)
            query_parts.append(dest_name)
            query = " ".join(query_parts)[:100]  # Reduced to 100 chars for API compatibility
            
            # Search for images
            scene_image_results = self.search_all_services(
                query,
                category=category,
                total_needed=images_to_search
            )
            
            if scene_image_results:
                # Deduplicate by URL
                scene_images_list = []
                for img in scene_image_results:
                    img_url = img.get('full_url') or img.get('preview_url') or img.get('url', '')
                    if img_url and img_url not in seen_image_urls:
                        seen_image_urls.add(img_url)
                        scene_images_list.append(img)
                        if len(scene_images_list) >= images_to_search:
                            break
                
                scene_images[scene_order] = scene_images_list
                logger.info(f"  Scene {scene_order}: Found {len(scene_images_list)} images")
            else:
                logger.warning(f"  Scene {scene_order}: No images found, will use fallback")
                scene_images[scene_order] = []
        
        # Fallback: If some scenes have no images, use generic search with day keywords
        scenes_without_images = [s for s in scenes if len(scene_images.get(s.get('order', 0), [])) == 0]
        if scenes_without_images and (specific_locations or specific_dishes):
            logger.info(f"Fallback: Searching for {len(scenes_without_images)} scenes without images using specific locations/dishes")
            
            # Use specific locations/dishes as fallback
            fallback_queries = []
            if specific_locations:
                fallback_queries.extend(specific_locations[:3])
            if specific_dishes:
                fallback_queries.extend(specific_dishes[:2])
            
            for scene in scenes_without_images:
                scene_order = scene.get('order', 0)
                if fallback_queries:
                    query = f"{fallback_queries[0]} {dest_name}" if day_location else f"{fallback_queries[0]} {dest_name}"
                    fallback_images = self.search_all_services(
                        query,
                        category='scenic_views',
                        total_needed=images_per_scene * 2
                    )
                    if fallback_images:
                        scene_images[scene_order] = fallback_images[:images_per_scene]
                        logger.info(f"  Scene {scene_order}: Found {len(scene_images[scene_order])} fallback images")
        
        # Download and validate images per scene
        final_scene_images = {}
        for scene in scenes:
            scene_order = scene.get('order', 0)
            scene_image_list = scene_images.get(scene_order, [])
            
            if not scene_image_list:
                logger.warning(f"Scene {scene_order} has no images after search")
                final_scene_images[scene_order] = []
                continue
            
            # Create scene-specific directory
            scene_dir = images_dir / f"scene_{scene_order}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            # Download and validate images
            downloaded_images = []
            for i, img_data in enumerate(scene_image_list, 1):
                if len(downloaded_images) >= images_per_scene:
                    break
                
                # Extract image URL
                image_url = img_data.get('full_url') or img_data.get('preview_url') or img_data.get('url', '')
                if not image_url:
                    logger.warning(f"  Skipping image {i} for scene {scene_order}: No URL found")
                    continue
                
                # Generate filename
                safe_dest = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
                image_filename = f"{safe_dest}_day_{day_number}_scene_{scene_order}_{i:03d}.jpg"
                image_path = scene_dir / image_filename
                
                # Download image
                logger.debug(f"  Downloading scene {scene_order} image {i}/{len(scene_image_list)}: {image_url[:60]}...")
                if self.download_image(image_url, image_path):
                    # Content-based deduplication: Check image hash
                    try:
                        import hashlib
                        with open(image_path, 'rb') as f:
                            image_hash = hashlib.md5(f.read()).hexdigest()
                        
                        if image_hash in seen_image_hashes:
                            logger.debug(f"  Skipping duplicate image content (hash: {image_hash[:8]}...): {image_path.name}")
                            image_path.unlink()  # Delete duplicate
                            continue
                        
                        # Mark as seen (both URL and hash)
                        seen_image_urls.add(image_url)
                        seen_image_hashes.add(image_hash)
                    except Exception as e:
                        logger.warning(f"Failed to compute image hash for {image_path.name}: {e}")
                        # Still mark URL as seen even if hash fails
                        seen_image_urls.add(image_url)
                    
                    downloaded_images.append(image_path)
                    logger.info(f"  ✅ Downloaded scene {scene_order} image {i}: {image_path.name}")
                else:
                    logger.warning(f"  ❌ Failed to download scene {scene_order} image {i}: {image_url[:60]}...")
            
            final_scene_images[scene_order] = downloaded_images
            logger.info(f"✅ Scene {scene_order}: Downloaded {len(downloaded_images)}/{images_per_scene} images")
        
        # Also save to "all" folder for backward compatibility
        all_dir = images_dir / "all"
        all_dir.mkdir(parents=True, exist_ok=True)
        all_images = []
        for scene_order in sorted(final_scene_images.keys()):
            all_images.extend(final_scene_images[scene_order])
        
        # Copy images to "all" folder
        for i, img_path in enumerate(all_images[:total_images_needed]):
            import shutil
            dest_path = all_dir / f"image_{i+1}.jpg"
            if not dest_path.exists():
                shutil.copy2(img_path, dest_path)
        
        logger.info(f"✅ Generated images for Day {day_number}: {sum(len(imgs) for imgs in final_scene_images.values())} total images across {len(scenes)} scenes")
        
        # Return in format compatible with existing code (also include "all" key)
        result = {"all": all_images[:total_images_needed]}
        result.update({f"scene_{order}": imgs for order, imgs in final_scene_images.items()})
        
        return result
    
    def generate_images_for_day_simple(
        self,
        destination: str,
        day_number: int,
        voiceover_duration_seconds: float,
        day_keywords: List[str],
        day_location: Optional[str] = None,
        specific_locations: Optional[List[str]] = None,
        specific_dishes: Optional[List[str]] = None,
        specific_restaurants: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        """
        SIMPLIFIED: Generate images for a day using day-level keywords (no scene breakdown)
        
        Args:
            destination: Destination name (e.g., "Chiang Mai, Thailand")
            day_number: Day number (e.g., 1, 2, 3)
            voiceover_duration_seconds: Voiceover duration in seconds
            day_keywords: List of day-level keywords for image search
            day_location: Day-specific city (e.g., "Bengaluru", "Chiang Mai")
            specific_locations: List of exact locations/landmarks
            specific_dishes: List of exact dish names
            specific_restaurants: List of restaurant names (optional)
            
        Returns:
            Dictionary mapping categories to lists of image paths
        """
        logger.info(f"Generating images for Day {day_number} of {destination} (SIMPLIFIED - voiceover: {voiceover_duration_seconds:.2f}s)")
        
        # Estimate image count based on voiceover duration
        target_seconds_per_image = 2.5  # 2.5 seconds per image
        estimated_images_needed = int(voiceover_duration_seconds / target_seconds_per_image)
        
        # Check if images already exist (reuse existing if available)
        images_dir = Path(settings_long.IMAGES_DIR) / destination / f"day_{day_number}"
        category_dir = images_dir / "all"
        
        if category_dir.exists():
            existing_images = list(category_dir.glob("*.jpg"))
            if len(existing_images) >= estimated_images_needed * 0.8:  # If we have at least 80% of needed images
                logger.info(f"✅ Found {len(existing_images)} existing images for Day {day_number} (need ~{estimated_images_needed}), reusing them")
                # Return existing images
                return {"all": existing_images[:estimated_images_needed]}
            elif len(existing_images) > 0:
                logger.info(f"Found {len(existing_images)} existing images for Day {day_number}, but need {estimated_images_needed}. Will download more.")
        
        # Adjust for multi-search if we have specific locations/dishes
        total_specific_items = 0
        if specific_locations:
            total_specific_items += len(specific_locations)
        if specific_dishes:
            total_specific_items += len(specific_dishes)
        
        if total_specific_items > 0:
            # Add extra images for multi-search (1-2 per specific item)
            adjustment = min(int(total_specific_items * 0.5), 15)  # Max +15 images
            estimated_images_needed = estimated_images_needed + adjustment
            logger.info(f"Multi-search adjustment: +{adjustment} images for {total_specific_items} specific items")
        
        # SOLUTION 2: Increase search count to account for validation failures
        # Search 2.5x more images than needed (many will fail validation)
        search_multiplier = 2.5
        images_to_search = int(estimated_images_needed * search_multiplier)
        logger.info(f"Search multiplier: {search_multiplier}x (searching {images_to_search} images to get ~{estimated_images_needed} valid ones)")
        
        logger.info(f"Voiceover duration: {voiceover_duration_seconds:.2f}s")
        logger.info(f"Target: {target_seconds_per_image}s per image")
        logger.info(f"Estimated images needed: {estimated_images_needed}")
        
        # Simplify destination name
        dest_name = destination.split(',')[0].strip() if ',' in destination else destination
        
        # Global deduplication (track URLs to avoid downloading duplicates)
        seen_image_urls = set()  # Track URLs we've already processed
        seen_image_hashes = set()  # Track image content hashes
        
        # Ensure day-specific directory exists (already created above if checking for existing images)
        images_dir.mkdir(parents=True, exist_ok=True)
        
        all_images = []  # Store all images for the day
        
        # 1. Multi-search for specific locations (if provided)
        if specific_locations:
            logger.info(f"Multi-search: Searching for {len(specific_locations)} specific locations")
            # Use search multiplier for location searches too
            images_per_location = max(3, int((images_to_search // (len(specific_locations) + 2)) * 0.4))  # Reserve some for generic
            
            for location in specific_locations[:8]:  # Limit to top 8 locations
                query_parts = [location.strip()]
                if day_location:
                    query_parts.append(day_location)
                query_parts.append(dest_name)
                query = " ".join(query_parts)[:100]
                
                location_images = self.search_all_services(
                    query, 
                    category="attractions", 
                    total_needed=images_per_location
                )
                
                if location_images:
                    # Deduplicate by URL (only add if not seen before)
                    new_count = 0
                    for img in location_images:
                        img_url = img.get('full_url') or img.get('preview_url') or img.get('url', '')
                        if img_url and img_url not in seen_image_urls:
                            seen_image_urls.add(img_url)
                            all_images.append(img)
                            new_count += 1
                    logger.debug(f"  Location '{location}': Found {new_count} new images")
        
        # 2. Multi-search for specific dishes (if provided)
        if specific_dishes:
            logger.info(f"Multi-search: Searching for {len(specific_dishes)} specific dishes")
            # Use search multiplier for dish searches too
            images_per_dish = max(3, int((images_to_search // (len(specific_dishes) + 2)) * 0.4))
            
            for dish in specific_dishes[:5]:  # Limit to top 5 dishes
                query_parts = [dish.strip()]
                if day_location:
                    query_parts.append(day_location)
                query_parts.append(dest_name)
                query = " ".join(query_parts)[:100]
                
                dish_images = self.search_all_services(
                    query, 
                    category="food_culture", 
                    total_needed=images_per_dish
                )
                
                if dish_images:
                    # Deduplicate by URL (only add if not seen before)
                    new_count = 0
                    for img in dish_images:
                        img_url = img.get('full_url') or img.get('preview_url') or img.get('url', '')
                        if img_url and img_url not in seen_image_urls:
                            seen_image_urls.add(img_url)
                            all_images.append(img)
                            new_count += 1
                    logger.debug(f"  Dish '{dish}': Found {new_count} new images")
        
        # 3. Generic search using day-level keywords (fill remaining)
        remaining_needed = max(0, images_to_search - len(all_images))
        if remaining_needed > 0 and day_keywords:
            logger.info(f"Generic search: Filling remaining {remaining_needed} images using day keywords")
            
            # Build query from day keywords (top 2-3 keywords)
            top_keywords = day_keywords[:3] if len(day_keywords) >= 3 else day_keywords
            keyword_query = " ".join(top_keywords[:2])  # Use top 2 keywords
            
            query_parts = []
            if day_location:
                query_parts.append(day_location)
            if keyword_query:
                query_parts.append(keyword_query)
            query_parts.append(dest_name)
            query = " ".join(query_parts)[:100]
            
            generic_images = self.search_all_services(
                query, 
                category="scenic_views", 
                total_needed=remaining_needed
            )
            
            if generic_images:
                # Deduplicate by URL (only add if not seen before)
                new_count = 0
                for img in generic_images:
                    img_url = img.get('full_url') or img.get('preview_url') or img.get('url', '')
                    if img_url and img_url not in seen_image_urls:
                        seen_image_urls.add(img_url)
                        all_images.append(img)
                        new_count += 1
                logger.debug(f"  Generic search: Found {new_count} new images")
        
        # 4. If still not enough, try one more generic search
        if len(all_images) < images_to_search * 0.7:  # If we have less than 70%
            logger.info(f"Fallback search: Still need more images ({len(all_images)}/{images_to_search})")
            fallback_query = f"{day_location} {dest_name}" if day_location else dest_name
            fallback_images = self.search_all_services(
                fallback_query, 
                category="scenic_views", 
                total_needed=images_to_search - len(all_images)
            )
            if fallback_images:
                # Deduplicate by URL (only add if not seen before)
                new_count = 0
                for img in fallback_images:
                    img_url = img.get('full_url') or img.get('preview_url') or img.get('url', '')
                    if img_url and img_url not in seen_image_urls:
                        seen_image_urls.add(img_url)
                        all_images.append(img)
                        new_count += 1
                logger.info(f"  Fallback search: Added {new_count} new images (total: {len(all_images)})")
        
        # Limit to images_to_search (we'll filter during download)
        all_images = all_images[:images_to_search]
        
        logger.info(f"Total images collected for download: {len(all_images)} (target: {estimated_images_needed} valid images from {images_to_search} searched)")
        
        # Download images to day directory (all in one folder, no category subfolders)
        downloaded_images = []
        category_dir = images_dir / "all"  # Single "all" category folder
        category_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting download of {len(all_images)} images to {category_dir}...")
        for idx, img_data in enumerate(all_images, 1):
            if len(downloaded_images) >= estimated_images_needed:
                break
            
            # Extract image URL from img_data dict
            image_url = img_data.get('full_url') or img_data.get('preview_url') or img_data.get('url', '')
            if not image_url:
                logger.warning(f"  Skipping image {idx}: No URL found in image data")
                continue
            
            # NOTE: seen_image_urls already contains URLs from search phase
            # We check here to avoid re-downloading, but we should still try to download
            # The real deduplication happens after download via content hash
            
            # Generate filename
            safe_dest = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            image_filename = f"{safe_dest}_day_{day_number}_all_{idx:03d}.jpg"
            image_path = category_dir / image_filename
            
            # Download and validate image
            logger.debug(f"  Downloading image {idx}/{len(all_images)}: {image_url[:60]}...")
            if self.download_image(image_url, image_path):
                # Content-based deduplication: Check image hash
                try:
                    import hashlib
                    with open(image_path, 'rb') as f:
                        image_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if image_hash in seen_image_hashes:
                        logger.debug(f"  Skipping duplicate image content (hash: {image_hash[:8]}...): {image_path.name}")
                        image_path.unlink()  # Delete duplicate
                        continue
                    
                    # Mark as seen (both URL and hash)
                    seen_image_urls.add(image_url)
                    seen_image_hashes.add(image_hash)
                except Exception as e:
                    logger.warning(f"Failed to compute image hash for {image_path.name}: {e}")
                    # Still mark URL as seen even if hash fails
                    seen_image_urls.add(image_url)
                
                downloaded_images.append(image_path)
                logger.info(f"  ✅ Downloaded image {idx}/{len(all_images)}: {image_path.name}")
            else:
                logger.warning(f"  ❌ Failed to download image {idx}: {image_url[:60]}...")
        
        logger.info(f"✅ Day {day_number}: Generated {len(downloaded_images)} images (simplified)")
        
        # Return simple structure: all images in one category
        return {"all": downloaded_images}
    
    def generate_images_for_day(
        self,
        destination: str,
        day_number: int,
        scenes: List[Dict[str, Any]],
        voiceover_duration_seconds: float,
        keywords_from_script: Optional[Dict[int, List[str]]] = None,
        day_location: Optional[str] = None,  # Day-specific city (e.g., "Bengaluru", "Mysuru")
        specific_locations: Optional[List[str]] = None,  # NEW: List of exact locations/landmarks (e.g., ["Shahi Killa", "Fortress"])
        specific_dishes: Optional[List[str]] = None,  # NEW: List of exact dish names (e.g., ["dosa", "idli", "biryani"])
        specific_restaurants: Optional[List[str]] = None  # NEW: List of restaurant names (optional)
    ) -> Dict[str, List[Path]]:
        """
        Generate images for a specific day based on scenes and voiceover duration
        NEW: Scene-based generation - each scene gets images based on its specific keywords
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            day_number: Day number (e.g., 1, 2, 3)
            scenes: List of scenes with categories and keywords (ordered by scene order)
            voiceover_duration_seconds: Voiceover duration in seconds
            keywords_from_script: Optional dictionary mapping scene order to keywords from script
            
        Returns:
            Dictionary mapping categories to lists of image paths
        """
        logger.info(f"Generating images for Day {day_number} of {destination} (voiceover: {voiceover_duration_seconds:.2f}s, {len(scenes)} scenes)")
        
        # Estimate image count based on voiceover duration
        # Target: 2.5 seconds per image (as specified by user)
        # Formula: images_needed = voiceover_duration_seconds / 2.5
        target_seconds_per_image = 2.5  # 2.5 seconds per image
        estimated_images_needed = int(voiceover_duration_seconds / target_seconds_per_image)
        
        # DYNAMIC ADJUSTMENT: Account for multi-search (multiple locations/dishes per scene)
        # If we have many specific locations or dishes, we might need more images
        # Adjust based on average locations/dishes per scene
        total_specific_items = 0
        if specific_locations:
            total_specific_items += len(specific_locations)
        if specific_dishes:
            total_specific_items += len(specific_dishes)
        
        # If we have many specific items, slightly increase image count to ensure good coverage
        # Formula: base_images + (specific_items_count * adjustment_factor)
        if total_specific_items > 0 and scenes:
            avg_items_per_scene = total_specific_items / len(scenes)
            # Add 1-2 images per additional specific item (capped at reasonable limit)
            adjustment = min(int(avg_items_per_scene * 0.5), 10)  # Max +10 images adjustment
            estimated_images_needed = estimated_images_needed + adjustment
            logger.info(f"Multi-search adjustment: +{adjustment} images for {total_specific_items} specific items ({avg_items_per_scene:.1f} avg per scene)")
        
        # Distribute images across scenes
        # Ensure minimum 3 images per scene for visual variety
        images_per_scene = max(3, estimated_images_needed // len(scenes)) if scenes else max(3, estimated_images_needed)
        
        logger.info(f"Voiceover duration: {voiceover_duration_seconds:.2f}s")
        logger.info(f"Target: {target_seconds_per_image}s per image")
        logger.info(f"Estimated images needed: {estimated_images_needed} ({images_per_scene} per scene, {len(scenes)} scenes)")
        if specific_locations:
            logger.info(f"  Specific locations: {len(specific_locations)}")
        if specific_dishes:
            logger.info(f"  Specific dishes: {len(specific_dishes)}")
        
        # Map scene categories to image generator categories
        # FIXED: Separate attractions from scenic_views
        category_mapping = {
            "arrival": "scenic_views",
            "attraction": "attractions",  # FIXED: Attractions should map to "attractions" not "scenic_views"
            "food": "food_culture",
            "stay": "hotel_stay",
            "scenic": "scenic_views",  # FIXED: Keep scenic separate from attractions
            "nightlife": "local_life",
            "transit": "scenic_views",
        }
        
        # Category-specific keyword boosters (to ensure category-specific results)
        category_keyword_boosters = {
            "attractions": ["monument", "landmark", "tourist attraction", "heritage site", "architecture", "historical site"],
            "food_culture": ["food", "dish", "cuisine", "restaurant", "meal", "local food", "traditional food", "culinary", "dining"],
            "scenic_views": ["landscape", "scenery", "panoramic view", "nature", "vista", "panorama", "beautiful view"],
            "hotel_stay": ["hotel", "resort", "accommodation", "luxury hotel", "resort", "lodge"],
            "local_life": ["local", "street", "people", "culture", "local life", "community"],
        }
        
        # Sort scenes by order
        sorted_scenes = sorted(scenes, key=lambda x: x.get('order', 0))
        
        # Generate images per scene (not per category)
        result = {}  # category -> list of image paths
        scene_keyword_map = keywords_from_script or {}
        
        # Global deduplication: Track all downloaded image URLs/hashes across all scenes
        seen_image_urls = set()
        seen_image_hashes = set()  # For content-based deduplication
        
        for scene in sorted_scenes:
            scene_order = scene.get('order', 0)
            scene_category = scene.get('category', 'unknown')
            
            # Get image category for this scene
            image_category = category_mapping.get(scene_category, "scenic_views")
            
            # Extract scene-specific keywords
            scene_keywords = []
            
            # 1. Get keywords from itinerary scene
            itinerary_keywords = scene.get('image_search_keywords', [])
            scene_keywords.extend(itinerary_keywords)
            
            # 2. Get keywords from script scene (if available)
            if scene_order in scene_keyword_map:
                script_keywords = scene_keyword_map[scene_order]
                scene_keywords.extend(script_keywords)
            
            # 3. Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for kw in scene_keywords:
                if kw and kw.lower() not in seen:
                    unique_keywords.append(kw)
                    seen.add(kw.lower())
            
            # Simplify destination name (remove comma and country if present)
            # "Karnataka, India" -> "Karnataka"
            dest_name = destination.split(',')[0].strip() if ',' in destination else destination
            
            # 4. Add category-specific keyword boosters to ensure category-specific results
            # IMPORTANT: Location is ALWAYS included in the query for better results
            if image_category in category_keyword_boosters:
                boosters = category_keyword_boosters[image_category]
                # Add 1-2 boosters if not already present in keywords
                for booster in boosters[:2]:
                    booster_lower = booster.lower()
                    # Skip if already in keywords
                    if booster_lower not in [kw.lower() for kw in unique_keywords]:
                        unique_keywords.append(booster)
            
            # MULTI-SEARCH STRATEGY: Create multiple targeted queries for better results
            # For food scenes: Search per dish (e.g., "dosa Bengaluru Karnataka")
            # For attraction/scenic scenes: Search per location (e.g., "Shahi Killa Lahore Pakistan")
            
            search_queries = []
            
            # FOOD SCENES: Multi-search per dish
            if scene_category == "food" and specific_dishes:
                logger.info(f"Food scene: Using multi-search for {len(specific_dishes)} dishes")
                for dish in specific_dishes[:5]:  # Limit to top 5 dishes
                    # Query format: "dish + day_location + destination"
                    # Example: "dosa Bengaluru Karnataka"
                    query_parts = [dish.strip()]
                    if day_location:
                        query_parts.append(day_location)
                    query_parts.append(dest_name)
                    query = " ".join(query_parts)
                    
                    # Limit query length
                    if len(query) > 100:
                        query = query[:100].rsplit(' ', 1)[0]
                    
                    search_queries.append((query, f"dish:{dish}"))
                    logger.debug(f"  Food query: '{query}'")
            
            # ATTRACTION/SCENIC SCENES: Multi-search per location
            elif scene_category in ["attraction", "scenic"] and specific_locations:
                logger.info(f"{scene_category} scene: Using multi-search for {len(specific_locations)} locations")
                for location in specific_locations[:5]:  # Limit to top 5 locations
                    # Query format: "location + day_location + destination"
                    # Example: "Shahi Killa Lahore Pakistan"
                    query_parts = [location.strip()]
                    if day_location:
                        query_parts.append(day_location)
                    query_parts.append(dest_name)
                    query = " ".join(query_parts)
                    
                    # Limit query length
                    if len(query) > 100:
                        query = query[:100].rsplit(' ', 1)[0]
                    
                    search_queries.append((query, f"location:{location}"))
                    logger.debug(f"  Location query: '{query}'")
            
            # FALLBACK: Generic search (if no specific dishes/locations or as supplement)
            if not search_queries:
                # Build generic query with priority: day_location > category boosters > keywords > destination
                if unique_keywords:
                    # Use top 2-3 keywords for search query (prefer shorter, more specific keywords)
                    filtered_keywords = [kw for kw in unique_keywords if len(kw) <= 30][:3]
                    if not filtered_keywords:
                        filtered_keywords = unique_keywords[:2]
                        filtered_keywords = [kw[:30] for kw in filtered_keywords]
                    
                    keyword_query = " ".join(filtered_keywords)
                    query_parts = []
                    
                    # 1. Day-specific location FIRST (most specific)
                    if day_location:
                        query_parts.append(day_location)
                    
                    # 2. Other keywords (category boosters are already in unique_keywords)
                    if keyword_query:
                        query_parts.append(keyword_query)
                    
                    # 3. Overall destination LAST (broader context)
                    query_parts.append(dest_name)
                    
                    query = " ".join(query_parts)
                    
                    # Limit query length
                    if len(query) > 100:
                        if day_location:
                            remaining_length = 100 - len(day_location) - 1
                            if remaining_length > len(dest_name) + 5:
                                keyword_space = remaining_length - len(dest_name) - 1
                                if keyword_space > 0 and keyword_query:
                                    keyword_query_truncated = keyword_query[:keyword_space].rsplit(' ', 1)[0]
                                    query = f"{day_location} {keyword_query_truncated} {dest_name}"
                                else:
                                    query = f"{day_location} {dest_name}"
                            else:
                                category_booster = category_keyword_boosters.get(image_category, [""])[0] if image_category in category_keyword_boosters else scene_category
                                query = f"{day_location} {category_booster}"[:100]
                        else:
                            max_keyword_length = 100 - len(dest_name) - 1
                            if max_keyword_length > 0 and keyword_query:
                                keyword_query_truncated = keyword_query[:max_keyword_length].rsplit(' ', 1)[0]
                                query = f"{keyword_query_truncated} {dest_name}"
                            else:
                                query = dest_name[:100]
                    
                    search_queries.append((query, "generic"))
                else:
                    # Last resort: day_location + category + destination
                    if day_location:
                        query = f"{day_location} {scene_category} {dest_name}"
                    else:
                        query = f"{dest_name} {scene_category}"
                    if len(query) > 100:
                        query = query[:100].rsplit(' ', 1)[0]
                    search_queries.append((query, "generic"))
            
            # DISTRIBUTE images across multiple queries
            # If we have multiple queries, distribute images_per_scene across them
            # Example: 12 images needed, 4 locations = 3 images per location
            images_per_query = max(2, images_per_scene // len(search_queries)) if search_queries else images_per_scene
            min_images_per_query = 2  # Minimum images per query
            
            logger.info(f"Scene {scene_order} ({scene_category}): {len(search_queries)} search query(ies), {images_per_query} images per query")
            if search_queries:
                logger.debug(f"  Queries: {[q[0] for q in search_queries[:3]]}")
            
            # Collect images from all queries
            all_images = []
            for query, query_type in search_queries:
                # Search for images using this specific query
                query_images = self.search_all_services(query, category=image_category, total_needed=images_per_query)
                
                if query_images:
                    all_images.extend(query_images)
                    logger.debug(f"  {query_type}: Found {len(query_images)} images with query '{query}'")
                else:
                    logger.warning(f"  {query_type}: No images found for query '{query}'")
                
                # If we have enough images, break early
                if len(all_images) >= images_per_scene:
                    break
            
            # If multi-search didn't yield enough images, try generic fallback
            if len(all_images) < min_images_per_query and search_queries and search_queries[0][1] != "generic":
                logger.info(f"Multi-search found only {len(all_images)} images, trying generic fallback...")
                fallback_query_parts = []
                if day_location:
                    fallback_query_parts.append(day_location)
                if image_category in category_keyword_boosters:
                    fallback_query_parts.append(category_keyword_boosters[image_category][0])
                fallback_query_parts.append(dest_name)
                fallback_query = " ".join(fallback_query_parts)[:100]
                
                fallback_images = self.search_all_services(fallback_query, category=image_category, total_needed=images_per_scene - len(all_images))
                if fallback_images:
                    all_images.extend(fallback_images)
                    logger.info(f"Generic fallback found {len(fallback_images)} additional images")
            
            images = all_images[:images_per_scene]  # Limit to images_per_scene
            
            if not images:
                query_summary = ", ".join([q[0] for q in search_queries[:3]]) if search_queries else "no queries"
                logger.warning(f"No images found for Scene {scene_order} ({scene_category}) with queries: {query_summary}")
                # Initialize category list if not exists
                if image_category not in result:
                    result[image_category] = []
                continue
            
            # Download images to day-specific category directory
            images_dir = Path(settings_long.IMAGES_DIR) / destination / f"day_{day_number}" / image_category
            images_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize category list if not exists
            if image_category not in result:
                result[image_category] = []
            
            downloaded_images = []
            for i, img_data in enumerate(images):
                if len(downloaded_images) >= images_per_scene:
                    break
                
                image_url = img_data.get('full_url') or img_data.get('preview_url', '')
                if not image_url:
                    continue
                
                # DEDUPLICATION: Skip if we've already downloaded this URL (cross-scene deduplication)
                if image_url in seen_image_urls:
                    logger.debug(f"  Skipping duplicate URL: {image_url[:60]}...")
                    continue
                
                # Generate filename with scene number for tracking
                image_filename = f"{destination}_day_{day_number}_scene_{scene_order:02d}_{image_category}_{i+1:03d}.jpg"
                image_path = images_dir / image_filename
                
                # Download and validate image
                if self.download_image(image_url, image_path):
                    # Content-based deduplication: Check image hash
                    try:
                        import hashlib
                        with open(image_path, 'rb') as f:
                            image_hash = hashlib.md5(f.read()).hexdigest()
                        
                        if image_hash in seen_image_hashes:
                            logger.debug(f"  Skipping duplicate image content (hash: {image_hash[:8]}...): {image_path.name}")
                            image_path.unlink()  # Delete duplicate
                            continue
                        
                        # Mark as seen (both URL and hash)
                        seen_image_urls.add(image_url)
                        seen_image_hashes.add(image_hash)
                    except Exception as e:
                        logger.warning(f"Failed to compute image hash for {image_path.name}: {e}")
                        # Still mark URL as seen even if hash fails
                        seen_image_urls.add(image_url)
                    
                    downloaded_images.append(image_path)
                    result[image_category].append(image_path)
                    # Cache the image
                    self.cache_image(image_path, destination, image_category, img_data, day_number=day_number)
            
            logger.info(f"✅ Scene {scene_order} ({scene_category}): Generated {len(downloaded_images)} images for {image_category}")
            if unique_keywords:
                logger.debug(f"  Used keywords: {', '.join(unique_keywords[:5])}")
            if image_category in category_keyword_boosters:
                logger.debug(f"  Added category boosters: {', '.join(category_keyword_boosters[image_category][:2])}")
        
        # Log summary with deduplication stats
        total_images = sum(len(images) for images in result.values())
        total_duplicates_skipped = len(seen_image_urls) - total_images  # Rough estimate
        logger.info(f"✅ Day {day_number}: Generated {total_images} unique images across {len(result)} categories")
        if total_duplicates_skipped > 0:
            logger.info(f"  Skipped {total_duplicates_skipped} duplicate images (cross-scene deduplication)")
        for category, images in result.items():
            logger.info(f"  {category}: {len(images)} images")
        
        return result


def main():
    """Test the destination image generator"""
    generator = DestinationImageGeneratorLong()
    
    # Test search
    test_destination = "Bali, Indonesia"
    test_category = "attractions"
    
    logger.info(f"Testing image generation for {test_destination} - {test_category}")
    
    result = generator.generate_images_for_destination(
        destination=test_destination,
        categories=[test_category],
        images_per_category=5,
        use_cache=False
    )
    
    logger.info(f"Generated {len(result.get(test_category, []))} images")
    for img_path in result.get(test_category, []):
        logger.info(f"  - {img_path}")


if __name__ == "__main__":
    main()


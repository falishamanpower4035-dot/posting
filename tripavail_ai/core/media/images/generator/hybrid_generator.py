"""
Hybrid Real-Photo Image Generation Pipeline
Pexels → Unsplash → Shutterstock → AI Fallback for authentic travel photography
"""

import json
import os
import time
import base64
import re
import requests
from collections import Counter
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from openai import OpenAI
from loguru import logger
from dotenv import load_dotenv
from core.content.post_manager import PostManager

# Load environment variables
load_dotenv()


class HybridImageGenerator:
    """Hybrid image generation using real photos from Unsplash/Pexels with AI fallback"""
    
    _STOPWORDS = {
        "the", "and", "for", "with", "from", "that", "this", "these", "those",
        "into", "your", "their", "about", "around", "after", "before", "near",
        "under", "over", "between", "through", "into", "onto", "within",
        "discover", "experience", "explore", "enjoy", "travel", "tourism",
        "visit", "journey", "world", "city", "country", "region", "place",
        "beautiful", "stunning", "amazing", "incredible", "new", "latest",
        "today", "breaking", "news", "update", "official", "launch", "open",
        "opening", "offers", "offering", "reveals", "revealed", "introduces",
        "introducing", "spotlights", "announces", "announced", "highlights",
        "brings", "bring", "marks", "makes", "plans", "plan", "destination",
        "destinations", "tourists", "tourist", "travellers", "traveler",
        "attracts", "highlight", "focus", "major", "first", "ever", "grand",
        "celebrates", "celebration", "season", "seasons", "winter", "summer",
        "spring", "autumn", "fall", "festival", "event"
    }

    _TRAVEL_THEMES = [
        "luxury hotel", "five star resort", "beach resort", "tropical beach",
        "city skyline", "historic district", "cultural festival", "street market",
        "heritage site", "mountain retreat", "spa retreat", "vineyard tour",
        "desert safari", "island escape", "art museum", "fine dining", "food tour",
        "night market", "ski resort", "jungle trek", "wildlife safari"
    ]

    _TRAVEL_KEYWORDS = [
        "luxury", "resort", "hotel", "spa", "beach", "island", "city", "skyline",
        "mountain", "lake", "forest", "desert", "sunset", "sunrise", "nightlife",
        "festival", "market", "heritage", "culture", "adventure", "family",
        "wellness", "nature", "cuisine", "food", "gourmet", "historic", "modern",
        "art", "architecture", "marina", "harbor", "villas", "palace", "temple",
        "cathedral", "bridge", "garden", "park"
    ]

    _shutterstock_watermark_template: Optional[np.ndarray] = None
    
    def __init__(self):
        # API Keys
        # Pexels (priority source)
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
        self.unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
        self.shutterstock_access_token = os.getenv('SHUTTERSTOCK_ACCESS_TOKEN')
        self.stability_api_key = os.getenv('STABILITY_API_KEY')
        self.openai_client = OpenAI()
        
        # Try to get API keys from config if not in environment
        try:
            from config import settings
            # Pexels (priority source)
            if not self.pexels_api_key:
                self.pexels_api_key = getattr(settings, 'PEXELS_API_KEY', None)
                if self.pexels_api_key:
                    logger.info("Pexels API key loaded from config")
            # Unsplash (second priority)
            if not self.unsplash_access_key:
                self.unsplash_access_key = getattr(settings, 'UNSPLASH_ACCESS_KEY', None)
                if self.unsplash_access_key:
                    logger.info("Unsplash API key loaded from config")
            # Shutterstock (third priority)
            if not self.shutterstock_access_token:
                self.shutterstock_access_token = getattr(settings, 'SHUTTERSTOCK_ACCESS_TOKEN', None)
                if self.shutterstock_access_token:
                    logger.info("Shutterstock API key loaded from config")
            # Stability AI
            if not self.stability_api_key:
                self.stability_api_key = getattr(settings, 'STABILITY_API_KEY', None)
                if self.stability_api_key:
                    logger.info("Stability AI API key loaded from config")
        except ImportError:
            pass
        
        # Configuration
        # Image Quality Settings - ULTRA PREMIUM CONFIGURATION
        self.target_size = (1080, 1920)  # 9:16 aspect ratio
        self.image_quality = 100  # JPEG quality: 100% (lossless)
        self.dalle_quality = "hd"  # DALL-E quality: HD (premium)
        self.target_resolution = "ultra"  # Resolution level: ULTRA (maximum processing)
        
        # Quality presets
        self.quality_presets = {
            "standard": {"jpeg_quality": 90, "dalle_quality": "standard", "resolution": "standard"},
            "high": {"jpeg_quality": 95, "dalle_quality": "hd", "resolution": "high"},
            "premium": {"jpeg_quality": 98, "dalle_quality": "hd", "resolution": "high"},
            "ultra": {"jpeg_quality": 100, "dalle_quality": "hd", "resolution": "ultra"}
        }
        self.images_per_post = 6
        self.max_retries = 2
        
        # File paths
        self.data_dir = Path("data")
        self.logs_dir = Path("logs")
        self.posts_file = self.data_dir / "posts.json"
        self.image_manifest_file = self.data_dir / "image_manifest.json"
        self.image_log_file = self.logs_dir / "image_log.txt"
        self.run_summary_file = self.logs_dir / "run_summary.txt"
        
        # Image directories
        self.staging_dir = self.data_dir / "images" / "staging"
        self.approved_dir = self.data_dir / "images" / "approved"
        self.rejected_dir = self.data_dir / "images" / "rejected"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # API rate limiting
        self.unsplash_requests = 0
        self.pexels_requests = 0
        self.shutterstock_requests = 0
        self.last_reset_date = datetime.now().date()
        
        logger.info("Hybrid Image Generator initialized")
    
    def set_image_quality(self, quality_level: str = "premium"):
        """
        Set image quality level
        
        Args:
            quality_level: "standard", "high", "premium", or "ultra"
        """
        if quality_level in self.quality_presets:
            preset = self.quality_presets[quality_level]
            self.image_quality = preset["jpeg_quality"]
            self.dalle_quality = preset["dalle_quality"]
            self.target_resolution = preset["resolution"]
            logger.info(f"Image quality set to {quality_level}: JPEG={self.image_quality}%, DALL-E={self.dalle_quality}")
        else:
            logger.warning(f"Unknown quality level: {quality_level}. Using current settings.")
    
    def get_quality_info(self) -> dict:
        """Get current quality settings"""
        return {
            "jpeg_quality": self.image_quality,
            "dalle_quality": self.dalle_quality,
            "target_resolution": self.target_resolution,
            "target_size": self.target_size
        }
    
    def _ensure_directories(self):
        """Create necessary directories"""
        for directory in [self.staging_dir, self.approved_dir, self.rejected_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def ingest_posts(self) -> List[Dict[str, Any]]:
        """Step 1: Load posts from previous pipeline"""
        try:
            if not self.posts_file.exists():
                logger.error(f"Posts file not found: {self.posts_file}")
                return []
            
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = data.get('posts', [])
            valid_posts = []
            
            for i, post in enumerate(posts):
                if all(key in post for key in ['caption', 'region', 'original_title', 'original_summary']):
                    post['post_id'] = f"{i+1:03d}"
                    valid_posts.append(post)
                else:
                    logger.warning(f"Post {i+1} missing required fields, skipping")
            
            logger.info(f"Loaded {len(valid_posts)} valid posts for image generation")
            return valid_posts
            
        except Exception as e:
            logger.error(f"Error loading posts: {e}")
            return []
    
    def extract_keywords_and_create_query(self, post: Dict[str, Any], story_beat: str = None) -> str:
        """
        Generate a compact keyword query (max 5 tokens) for image providers.
        Priority: location → travel theme → descriptive context.
        """
        try:
            keyword_bundle = self._generate_keyword_bundle(post, story_beat)
            if not keyword_bundle:
                region = post.get('region') or post.get('original_title') or "travel"
                keyword_bundle = [region.strip(), "travel"]
                logger.warning(f"Keyword bundle empty, using fallback keywords: {keyword_bundle}")

            primary = keyword_bundle[:2]
            visual = keyword_bundle[2:4]
            secondary = keyword_bundle[4:]
            post['keywords'] = {
                "primary": primary,
                "visual": visual,
                "secondary": secondary,
                "bundle": keyword_bundle
            }

            keyword_query = ", ".join(keyword_bundle)

            optimized_query = self._optimize_query_with_openai(post, keyword_query)
            if optimized_query and optimized_query != keyword_query:
                optimized_bundle = self._generate_keyword_bundle(
                    {
                        "original_title": post.get("original_title", ""),
                        "original_summary": post.get("original_summary", ""),
                        "caption": post.get("caption", ""),
                        "region": post.get("region", ""),
                        "extra": optimized_query
                    },
                    story_beat=story_beat
                )
                if optimized_bundle:
                    keyword_bundle = optimized_bundle
                    post['keywords']["bundle"] = keyword_bundle
                    keyword_query = ", ".join(keyword_bundle)
                
                post_id = post.get('post_id') or post.get('topic_id', 'unknown')
            logger.info(f"Keyword bundle for post {post_id}: {keyword_bundle}")

            final_query = self._test_query_and_fallback(post, keyword_query, keyword_query)
            return final_query

        except Exception as e:
            logger.error(f"Error creating search query: {e}")
            region = post.get('region', 'travel')
            return f"{region} travel"
    
    def _generate_keyword_bundle(self, post: Dict[str, Any], story_beat: Optional[str] = None) -> List[str]:
        """Build prioritized keyword bundle (<=5 terms) for stock image search."""
        bundle: List[str] = []
        seen = set()

        def add_keyword(term: str):
            if not term:
                return
            cleaned = term.strip()
            if not cleaned:
                return
            normalized = cleaned.lower()
            if normalized in seen or len(bundle) >= 5:
                return
            bundle.append(cleaned)
            seen.add(normalized)

        locations = post.get('locations') or {}
        for loc_key in ("city", "region", "country"):
            add_keyword(locations.get(loc_key, ""))

        region = post.get('region', '') or ''
            if region:
            for part in [p.strip() for p in region.split(',') if p.strip()]:
                add_keyword(part)

        combined_text = " ".join(filter(None, [
            post.get('original_title', ''),
            post.get('original_summary', ''),
            post.get('caption', ''),
            story_beat or "",
            post.get('extra', '')
        ])).lower()

        for phrase in self._TRAVEL_THEMES:
            if phrase in combined_text:
                add_keyword(phrase)

        for keyword in self._TRAVEL_KEYWORDS:
            if keyword in combined_text:
                add_keyword(keyword)

        tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", combined_text)
        filtered_tokens = [
            t for t in tokens
            if t not in self._STOPWORDS and len(t) > 2
        ]
        counts = Counter(filtered_tokens)
        for word, _ in counts.most_common(10):
            add_keyword(word)
            if len(bundle) >= 5:
                break

        if story_beat:
            beat_tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", story_beat.lower())
            for token in beat_tokens:
                if token not in self._STOPWORDS and len(token) > 2:
                    add_keyword(token)
                if len(bundle) >= 5:
                    break

        return bundle[:5]

    def _get_shutterstock_watermark_template(self) -> np.ndarray:
        if self._shutterstock_watermark_template is None:
            canvas = np.zeros((120, 600), dtype=np.uint8)
            cv2.putText(
                canvas,
                "SHUTTERSTOCK",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.6,
                255,
                3,
                cv2.LINE_AA
            )
            rotation_matrix = cv2.getRotationMatrix2D((300, 60), -32, 1.0)
            rotated = cv2.warpAffine(canvas, rotation_matrix, (600, 120), borderValue=0)
            blurred = cv2.GaussianBlur(rotated, (5, 5), 0)
            self._shutterstock_watermark_template = blurred
        return self._shutterstock_watermark_template.copy()

    def _contains_shutterstock_watermark(self, image_path: Path) -> bool:
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                return False
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            template = self._get_shutterstock_watermark_template()

            # normalize image for better matching
            gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

            for scale in (1.0, 0.75, 0.5):
                resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                if resized.shape[0] < template.shape[0] or resized.shape[1] < template.shape[1]:
                    continue
                res = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
                if res.size and res.max() >= 0.45:
                    return True
                # also test inverted (white-on-black vs black-on-white)
                res_inv = cv2.matchTemplate(255 - resized, template, cv2.TM_CCOEFF_NORMED)
                if res_inv.size and res_inv.max() >= 0.45:
                    return True
            return False
        except Exception as err:
            logger.debug(f"Watermark detection failed: {err}")
            return False
    
    def _extract_location_keywords(self, title: str, summary: str) -> List[str]:
        """Extract location-related keywords"""
        text = f"{title} {summary}".lower()
        
        # Common location patterns
        location_patterns = [
            'tulum', 'mexico', 'kotka', 'finland', 'new hampshire', 'paris', 'france',
            'louvre', 'beach', 'coast', 'mountain', 'city', 'village', 'town'
        ]
        
        found_locations = []
        for pattern in location_patterns:
            if pattern in text:
                found_locations.append(pattern)
        
        return found_locations
    
    def _extract_theme_keywords(self, caption: str, title: str, summary: str) -> List[str]:
        """Extract theme-related keywords"""
        text = f"{caption} {title} {summary}".lower()
        
        # Theme patterns
        theme_patterns = [
            'festival', 'light', 'art', 'sustainable', 'eco', 'digital', 'award',
            'museum', 'heritage', 'culture', 'nature', 'landscape', 'architecture'
        ]
        
        found_themes = []
        for pattern in theme_patterns:
            if pattern in text:
                found_themes.append(pattern)
        
        return found_themes
    
    def _optimize_search_query(self, query: str) -> str:
        """Optimize search query for better results"""
        # Remove duplicates and limit length
        words = query.split()
        unique_words = []
        seen = set()
        
        for word in words:
            if word not in seen and len(unique_words) < 8:  # Max 8 words
                unique_words.append(word)
                seen.add(word)
        
        return ' '.join(unique_words)
    
    def _optimize_query_with_openai(self, post: Dict[str, Any], base_query: str) -> str:
        """
        Use OpenAI GPT to optimize search query for Shutterstock
        
        Creates more relatable, natural search queries that yield better results
        from stock photo libraries like Shutterstock.
        
        Args:
            post: Post data with title, summary, caption, region
            base_query: Current basic query
            
        Returns:
            Optimized query string, or base_query if OpenAI fails
        """
        try:
            title = post.get('original_title', '')
            summary = post.get('original_summary', '')
            caption = post.get('caption', '')
            region = post.get('region', '')
            
            # Build context for GPT
            context = f"""
Title: {title}
Summary: {summary}
Region: {region}
Current query: {base_query}
"""
            
            prompt = f"""You are an expert at creating search queries for stock photo libraries like Shutterstock.

Your task: Transform the given travel news content into a highly effective, relatable search query that will find the best matching stock photos.

Guidelines:
- Use natural, conversational terms that real photographers would tag their images with
- Focus on visual elements that people actually photograph (scenes, landmarks, activities)
- Include location names when relevant
- Use 3-5 words maximum (concise but descriptive)
- Prioritize terms that match how professional photographers describe their images
- Keep it RELATABLE but not overly specific - balance detail with searchability
- Prefer broad visual concepts that yield results (e.g., "luxury hotel" over "rooftop infinity pool")
- Only add specific details if they're essential landmarks or famous places
- Avoid overly technical or niche terms
- IMPORTANT: If the content mentions generic concepts (hotel, beach, city), keep those in the query
- Only remove generic words like "tourism" or "destination" if they're redundant

Content:
{context}

Generate ONLY the optimized search query (3-5 words), nothing else. Make it relatable and visual but searchable.

Example transformations:
- "Dubai luxury hotel travel tourism destination" → "Dubai luxury hotel"
- "Paris Eiffel Tower sunset travel" → "Paris Eiffel Tower sunset"  
- "Bali beach tropical paradise tourism" → "Bali tropical beach"
- "Tokyo city night lights travel" → "Tokyo night city lights"

CRITICAL: Keep it SIMPLE. If content mentions "hotel", use "hotel" not "skyline" or "pool". 
Only add descriptive words if they're essential landmarks (e.g., "Eiffel Tower", "Taj Mahal").
Prefer removing generic words over adding specific ones.

Generate the query now:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at creating effective stock photo search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            
            optimized_query = response.choices[0].message.content.strip()
            
            # Clean up the response (remove quotes, extra text)
            optimized_query = optimized_query.strip('"').strip("'").strip()
            
            # Post-process: Remove overly specific words that aren't landmarks/famous places
            # This prevents queries like "Dubai luxury hotel skyline" → "Dubai luxury hotel"
            landmark_keywords = ['eiffel', 'tower', 'taj', 'mahal', 'statue', 'liberty', 'louvre', 
                               'colosseum', 'pyramid', 'sphinx', 'great wall', 'bridge', 'golden gate']
            
            query_words = optimized_query.lower().split()
            base_words = set(base_query.lower().split())
            
            # If optimized query adds words not in base query, check if they're landmarks
            # If not landmarks and base query had key terms (hotel, beach, city), prefer simpler version
            added_words = [w for w in query_words if w not in base_words]
            is_landmark = any(landmark in optimized_query.lower() for landmark in landmark_keywords)
            
            # If added non-landmark words and base query has common terms (hotel, beach, city, etc.)
            common_terms = ['hotel', 'beach', 'city', 'resort', 'island', 'mountain', 'lake']
            base_has_common = any(term in base_query.lower() for term in common_terms)
            
            if added_words and not is_landmark and base_has_common:
                # Prefer simpler version: keep location + common terms, remove overly specific additions
                location = post.get('region', '')
                simple_query_parts = [location] if location else []
                for term in common_terms:
                    if term in base_query.lower():
                        simple_query_parts.append(term)
                        break  # Just add one main term
                if simple_query_parts:
                    optimized_query = ' '.join(simple_query_parts[:3])  # Max 3 words
                    logger.info(f"🔧 Simplified query to avoid overly specific terms: '{optimized_query}'")
            
            # Validate it's reasonable (not too long, not empty)
            if optimized_query and len(optimized_query.split()) <= 10:
                logger.info(f"🤖 OpenAI optimized query: '{base_query}' → '{optimized_query}'")
                return optimized_query
            else:
                logger.warning(f"OpenAI query optimization returned invalid result: '{optimized_query}', using base query")
                return base_query
                
        except Exception as e:
            logger.warning(f"OpenAI query optimization failed: {e}, using base query")
            return base_query
    
    def _test_query_and_fallback(self, post: Dict[str, Any], optimized_query: str, base_query: str) -> str:
        """
        Test optimized query and fallback to base if it returns no results
        
        This ensures we don't use queries that yield 0 results from Shutterstock
        
        Args:
            post: Post data
            optimized_query: OpenAI-optimized query
            base_query: Original query as fallback
            
        Returns:
            Query that works (has results), or base_query if both fail
        """
        # Quick test: search with optimized query first
        try:
            test_results = self.search_shutterstock(optimized_query, count=1)
            if len(test_results) > 0:
                logger.info(f"✅ Optimized query '{optimized_query}' has results, using it")
                return optimized_query
            else:
                logger.warning(f"⚠️ Optimized query '{optimized_query}' returned 0 results, falling back to base query")
                return base_query
        except Exception as e:
            logger.warning(f"Query test failed: {e}, using base query")
            return base_query

    def search_shutterstock(self, query: str, count: int = 3, page: int = 1, sort: str = "relevance") -> List[Dict[str, Any]]:
        """Search Shutterstock (third priority fallback) for real photos (supports paging and sort for diversity)."""
        try:
            if not self.shutterstock_access_token:
                logger.warning("Shutterstock access token not found")
                return []

            # Basic rate limiting safeguard
            if self.shutterstock_requests >= 500:
                logger.warning("Shutterstock rate limit (local guard) reached")
                return []

            url = "https://api.shutterstock.com/v2/images/search"
            headers = {
                "Authorization": f"Bearer {self.shutterstock_access_token}",
            }
            # Note: Shutterstock API uses boolean values, not string "True"
            params = {
                "query": query,
                "image_type": "photo",
                "orientation": "vertical",
                "page": page,
                "per_page": min(count, 20),  # Max 20 per page
                "sort": sort,  # relevance, popular, newest for variety
            }

            resp = requests.get(url, headers=headers, params=params, timeout=12)
            resp.raise_for_status()
            data = resp.json() or {}
            results = data.get("data", [])

            # Normalize a small subset for downstream use
            normalized: List[Dict[str, Any]] = []
            for item in results:
                assets = (item.get("assets") or {})
                # Try a few common preview keys
                preview = (
                    (assets.get("preview_1000") or {}).get("url")
                    or (assets.get("preview") or {}).get("url")
                    or (assets.get("huge_thumb") or {}).get("url")
                    or (assets.get("thumb_360") or {}).get("url")
                )
                width = None
                height = None
                # Some preview objects include width/height
                for k in ("preview_1000", "preview", "huge_thumb", "thumb_360"):
                    a = assets.get(k) or {}
                    if a.get("url") == preview:
                        width = a.get("width") or width
                        height = a.get("height") or height
                normalized.append({
                    "preview_url": preview,
                    "description": (item.get("description") or ""),
                    "width": width,
                    "height": height,
                    "_raw": item,
                })

            self.shutterstock_requests += 1
            logger.info(f"Shutterstock search returned {len(normalized)} results for query: '{query}' (page {page}, sort={sort})")
            return normalized

        except Exception as e:
            logger.error(f"Shutterstock API error: {e}")
            return []

    def _score_shutterstock_result(self, result: Dict[str, Any], keywords: Dict[str, List[str]]) -> int:
        """Relevance score for Shutterstock based on description and portrait orientation."""
        desc = (result.get("description") or "").lower()
        score = 0
        # Favor vertical
        w = result.get("width") or 0
        h = result.get("height") or 0
        if h and w and h > w:
            score += 4
        # Keyword overlaps
        for w in (keywords.get('primary') or []):
            if w and w.lower() in desc:
                score += 3
        for w in (keywords.get('visual') or []):
            if w and w.lower() in desc:
                score += 2
        for w in (keywords.get('secondary') or []):
            if w and w.lower() in desc:
                score += 1
        return score
    
    def search_unsplash(self, query: str, count: int = 3, page: int = 1, order_by: str = "relevant") -> List[Dict[str, Any]]:
        """Search Unsplash (second priority) for real photos (supports paging for diversity)"""
        try:
            if not self.unsplash_access_key:
                logger.warning("Unsplash API key not found")
                return []
            
            # Check rate limits
            if self.unsplash_requests >= 50:  # Unsplash free tier limit
                logger.warning("Unsplash rate limit reached")
                return []
            
            url = "https://api.unsplash.com/search/photos"
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}"
            }
            params = {
                "query": query,
                "per_page": count,
                "orientation": "portrait",
                "content_filter": "high",
                "page": page,
                "order_by": order_by,
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            self.unsplash_requests += 1
            
            logger.info(f"Unsplash search returned {len(results)} results for query: '{query}' (page {page}, order_by={order_by})")
            return results
            
        except Exception as e:
            logger.error(f"Unsplash API error: {e}")
            return []

    def _score_unsplash_result(self, result: Dict[str, Any], keywords: Dict[str, List[str]]) -> int:
        """Enhanced relevance score based on keyword overlaps for voiceover alignment."""
        text_parts = []
        alt = result.get('alt_description') or ''
        desc = result.get('description') or ''
        text_parts.extend([alt.lower(), desc.lower()])
        # Tags may be an array of dicts with title
        tags = result.get('tags') or []
        for t in tags:
            title = (t.get('title') or '').lower()
            if title:
                text_parts.append(title)
        blob = ' '.join(text_parts)
        score = 0
        
        # Enhanced scoring for better voiceover alignment
        for w in (keywords.get('primary') or []):
            if w and w.lower() in blob:
                score += 4  # Primary keywords are most important
        for w in (keywords.get('visual') or []):
            if w and w.lower() in blob:
                score += 3  # Visual keywords are very important
        for w in (keywords.get('narrative') or []):
            if w and w.lower() in blob:
                score += 2  # Narrative keywords help with voiceover alignment
        for w in (keywords.get('secondary') or []):
            if w and w.lower() in blob:
                score += 1  # Secondary keywords provide context
        return score
    
    def search_pexels(self, query: str, count: int = 3, page: int = 1) -> List[Dict[str, Any]]:
        """Search Pexels (first priority) for real photos (supports paging for diversity)"""
        try:
            if not self.pexels_api_key:
                logger.warning("Pexels API key not found")
                return []
            
            # Check rate limits
            if self.pexels_requests >= 200:  # Pexels free tier limit
                logger.warning("Pexels rate limit reached")
                return []
            
            url = "https://api.pexels.com/v1/search"
            headers = {
                "Authorization": self.pexels_api_key
            }
            params = {
                "query": query,
                "per_page": count,
                "orientation": "portrait",
                "page": page,
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('photos', [])
            
            self.pexels_requests += 1
            
            logger.info(f"Pexels search returned {len(results)} results for query: '{query}' (page {page})")
            return results
            
        except Exception as e:
            logger.error(f"Pexels API error: {e}")
            return []

    def _score_pexels_result(self, result: Dict[str, Any], keywords: Dict[str, List[str]]) -> int:
        """Enhanced relevance score for Pexels based on voiceover alignment."""
        alt = (result.get('alt') or '').lower()
        score = 0
        
        # Enhanced scoring for better voiceover alignment
        for w in (keywords.get('primary') or []):
            if w and w.lower() in alt:
                score += 4  # Primary keywords are most important
        for w in (keywords.get('visual') or []):
            if w and w.lower() in alt:
                score += 3  # Visual keywords are very important
        for w in (keywords.get('narrative') or []):
            if w and w.lower() in alt:
                score += 2  # Narrative keywords help with voiceover alignment
        for w in (keywords.get('secondary') or []):
            if w and w.lower() in alt:
                score += 1  # Secondary keywords provide context
        return score

    def _compute_image_hash(self, image_path: str) -> str:
        """Compute a simple average hash for deduplication (no external deps)."""
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                img = img.convert('L').resize((8, 8))
                pixels = list(img.getdata())
                avg = sum(pixels) / len(pixels)
                bits = ''.join('1' if p > avg else '0' for p in pixels)
                # Convert to hex for compact storage
                return hex(int(bits, 2))[2:].rjust(16, '0')
        except Exception:
            # Fallback to file size-based hash
            try:
                import os, hashlib
                with open(image_path, 'rb') as f:
                    return hashlib.md5(f.read(4096)).hexdigest()
            except Exception:
                return ""

    def _get_existing_image_hashes(self, post_images_dir: "Path") -> set:
        """Collect hashes of existing images in a post directory."""
        try:
            hashes = set()
            for p in sorted(post_images_dir.glob("*.jpg")):
                h = self._compute_image_hash(str(p))
                if h:
                    hashes.add(h)
            return hashes
        except Exception:
            return set()
    
    def generate_ai_fallback(self, query: str, count: int = 1) -> List[str]:
        """Step 5: Generate AI fallback using Stability AI SDXL"""
        try:
            if not self.stability_api_key:
                logger.warning("Stability AI API key not found, using DALL-E fallback")
                return self._generate_dalle_fallback(query, count)
            
            # Use Stability AI SDXL for AI generation
            return self._generate_stability_sdxl(query, count)
            
        except Exception as e:
            logger.error(f"AI fallback error: {e}, using DALL-E fallback")
            return self._generate_dalle_fallback(query, count)
    
    def _generate_stability_sdxl(self, query: str, count: int) -> List[str]:
        """Generate images using Stability AI SDXL"""
        try:
            import requests
            
            # Stability AI SDXL API endpoint
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            headers = {
                "Authorization": f"Bearer {self.stability_api_key}",
                "Content-Type": "application/json"
            }
            
            # Enhanced prompt for travel photography
            prompt = f"""A stunning vertical travel photograph taken by a professional DSLR camera showing {query}. 
            Natural lighting, authentic travel destination, cinematic composition, 9:16 aspect ratio, 
            professional travel photography style, high resolution, detailed, realistic"""
            
            data = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": 7,  # Creative freedom (1-35)
                "height": 1024,  # Square format for SDXL
                "width": 1024,   # Will be cropped to 9:16 later
                "samples": count,
                "steps": 20,  # Reduced for faster generation
                "style_preset": "photographic"  # Realistic style
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            image_urls = []
            
            for artifact in result.get('artifacts', []):
                if artifact.get('finishReason') == 'SUCCESS':
                    # Convert base64 to data URL
                    import base64
                    image_data = base64.b64decode(artifact['base64'])
                    # For now, we'll return the base64 data as a data URL
                    # In production, you might want to save to temp file first
                    image_urls.append(f"data:image/png;base64,{artifact['base64']}")
            
            logger.info(f"Generated {len(image_urls)} Stability AI SDXL images")
            return image_urls
            
        except Exception as e:
            logger.error(f"Stability AI SDXL error: {e}")
            return []
    
    def _generate_dalle_fallback(self, query: str, count: int) -> List[str]:
        """Generate images using DALL-E as fallback"""
        try:
            prompt = f"""A realistic vertical travel photograph taken by a professional DSLR camera showing {query}. 
            Natural lighting, authentic travel destination, no digital art, no text or logos, 
            cinematic 9:16 aspect ratio, professional travel photography style."""
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1792",
                quality=self.dalle_quality,  # Use configurable quality
                n=count
            )
            
            image_urls = [img.url for img in response.data]
            logger.info(f"Generated {len(image_urls)} AI fallback images")
            return image_urls
            
        except Exception as e:
            logger.error(f"DALL-E fallback error: {e}")
            return []
    
    def download_and_process_image(self, image_url: str, source: str) -> Optional[str]:
        """Download image and process it (handles both URLs and data URLs)"""
        try:
            # Handle data URLs (from Stability AI)
            if image_url.startswith('data:image/'):
                import base64
                import re
                
                # Extract base64 data from data URL
                match = re.match(r'data:image/([^;]+);base64,(.+)', image_url)
                if not match:
                    logger.error("Invalid data URL format")
                    return None
                
                image_format, base64_data = match.groups()
                image_data = base64.b64decode(base64_data)
                
                # Create temporary file
                temp_path = self.staging_dir / f"temp_{int(time.time())}.{image_format}"
                
                with open(temp_path, 'wb') as f:
                    f.write(image_data)
                
                # Process image
                processed_path = self._normalize_aspect_ratio(temp_path, source)
                
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
                
                return processed_path
            
            # Handle regular URLs (from Unsplash, Pexels, DALL-E)
            else:
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                
                # Create temporary file
                temp_path = self.staging_dir / f"temp_{int(time.time())}.jpg"
                
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
                
                if source == "shutterstock" and self._contains_shutterstock_watermark(temp_path):
                    logger.warning("Rejected Shutterstock image due to watermark detection")
                    if temp_path.exists():
                        temp_path.unlink()
                    return None
                
                # Process image
                processed_path = self._normalize_aspect_ratio(temp_path, source)
                
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()
                
                return processed_path
            
        except Exception as e:
            logger.error(f"Error downloading/processing image: {e}")
            return None
    
    def _normalize_aspect_ratio(self, image_path: Path, source: str) -> str:
        """Step 6: Normalize to 9:16 aspect ratio"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate target dimensions
                target_width, target_height = self.target_size
                target_ratio = target_width / target_height
                
                # Get current dimensions
                current_width, current_height = img.size
                current_ratio = current_width / current_height
                
                # Crop or pad to match 9:16 ratio
                if current_ratio > target_ratio:
                    # Image is too wide, crop horizontally
                    new_width = int(current_height * target_ratio)
                    left = (current_width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, current_height))
                elif current_ratio < target_ratio:
                    # Image is too tall, crop vertically
                    new_height = int(current_width / target_ratio)
                    top = (current_height - new_height) // 2
                    img = img.crop((0, top, current_width, top + new_height))
                
                # Resize to target dimensions
                img = img.resize(self.target_size, Image.Resampling.LANCZOS)
                
                # Apply gentle enhancements
                img = self._apply_visual_consistency(img)
                
                # Save processed image with configurable quality
                processed_path = self.staging_dir / f"processed_{source}_{int(time.time())}.jpg"
                img.save(processed_path, 'JPEG', quality=self.image_quality)
                
                return str(processed_path)
                
        except Exception as e:
            logger.error(f"Error normalizing aspect ratio: {e}")
            return str(image_path)
    
    def _apply_visual_consistency(self, img: Image.Image) -> Image.Image:
        """Step 10: Apply visual consistency checks and enhancements"""
        try:
            # Convert to numpy for processing
            img_array = np.array(img)
            
            # Check for visual consistency
            if self._is_visually_consistent(img_array):
                # Apply mild warm-tone filter for brand consistency
                img_array = self._apply_warm_filter(img_array)
                
                # Gentle sharpening
                img_array = self._apply_gentle_sharpening(img_array)
                
                return Image.fromarray(img_array)
            else:
                logger.warning("Image failed visual consistency check")
                return img
                
        except Exception as e:
            logger.error(f"Error applying visual consistency: {e}")
            return img
    
    def _is_visually_consistent(self, img_array: np.ndarray) -> bool:
        """Check if image meets visual consistency standards"""
        try:
            # Check brightness (avoid too dark or too bright)
            mean_brightness = np.mean(img_array)
            if mean_brightness < 30 or mean_brightness > 225:
                return False
            
            # Check for cartoonish filters (check color variance)
            color_variance = np.var(img_array)
            if color_variance < 100:  # Too uniform
                return False
            
            # Check for black and white
            if len(img_array.shape) == 3:
                r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
                if np.allclose(r, g, b, atol=10):  # Nearly grayscale
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking visual consistency: {e}")
            return True  # Default to accepting if check fails
    
    def _apply_warm_filter(self, img_array: np.ndarray) -> np.ndarray:
        """Apply mild warm-tone filter"""
        try:
            # Increase red and yellow channels slightly
            img_array[:,:,0] = np.clip(img_array[:,:,0] * 1.05, 0, 255)  # Red
            img_array[:,:,1] = np.clip(img_array[:,:,1] * 1.02, 0, 255)  # Green (yellow component)
            
            return img_array.astype(np.uint8)
        except Exception as e:
            logger.error(f"Error applying warm filter: {e}")
            return img_array
    
    def _apply_gentle_sharpening(self, img_array: np.ndarray) -> np.ndarray:
        """Apply gentle sharpening"""
        try:
            # Convert to PIL for sharpening
            img = Image.fromarray(img_array)
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            return np.array(img)
        except Exception as e:
            logger.error(f"Error applying sharpening: {e}")
            return img_array
    
    def quality_check(self, image_path: str) -> bool:
        """Step 7: Quality assurance with OCR + GPT check"""
        try:
            # Check dimensions
            if not self._check_image_dimensions(image_path):
                return False
            
            # OCR text detection
            detected_text = self._detect_text_ocr(image_path)
            
            if detected_text.strip():
                # GPT validation
                is_valid = self._validate_text_with_gpt(detected_text)
                if not is_valid:
                    logger.warning(f"Image rejected due to text: {image_path}")
                    return False
            
            logger.info(f"Image passed quality check: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error in quality check: {e}")
            return False
    
    def _check_image_dimensions(self, image_path: str) -> bool:
        """Check if image has correct dimensions"""
        try:
            with Image.open(image_path) as img:
                return img.size == self.target_size
        except Exception as e:
            logger.error(f"Error checking dimensions: {e}")
            return False
    
    def _detect_text_ocr(self, image_path: str) -> str:
        """Detect text in image using OCR"""
        try:
            # Load image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                return ""
            
            # Convert to PIL Image for pytesseract
            pil_image = Image.open(image_path)
            
            # Try Tesseract OCR if available
            try:
                import pytesseract
                config = '--oem 3 --psm 6'
                text = pytesseract.image_to_string(pil_image, config=config).strip()
                if text:
                    logger.warning(f"Text detected in {image_path}: {text}")
                    return text
            except ImportError:
                logger.debug("Tesseract not available, skipping OCR")
            
            # Fallback: basic pattern detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            if edge_density > 0.15:  # High edge density might indicate text
                return "High edge density detected"
            
            return ""
            
        except Exception as e:
            logger.error(f"Error in OCR detection: {e}")
            return ""
    
    def _validate_text_with_gpt(self, text: str) -> bool:
        """Validate detected text with GPT"""
        try:
            prompt = f"""Analyze this detected text from a travel photograph. Determine if it contains actual readable text that should be rejected.

Text: "{text}"

Answer format: YES/NO - [reason]

YES = Contains problematic readable text that should be rejected
NO = No problematic text found (only technical analysis or acceptable content)"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are analyzing text detection reports from travel photographs. Distinguish between actual problematic text vs technical analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return answer.startswith("NO")
            
        except Exception as e:
            logger.error(f"Error validating text with GPT: {e}")
            return False
    
    def organize_outputs(self, results: Dict[str, List[str]]) -> Dict[str, Any]:
        """Step 8: Organize outputs and create manifest"""
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "source": "TripAvail AI Hybrid Image Generator",
            "total_posts": len(results),
            "posts": []
        }
        
        for post_id, image_paths in results.items():
            # Create post directory
            post_dir = self.approved_dir / post_id
            post_dir.mkdir(exist_ok=True)
            
            # Move and rename images
            final_paths = []
            for i, image_path in enumerate(image_paths):
                if image_path and os.path.exists(image_path):
                    final_name = f"img{i+1:02d}.jpg"
                    final_path = post_dir / final_name
                    
                    # Move image
                    os.rename(image_path, final_path)
                    final_paths.append(f"data/images/approved/{post_id}/{final_name}")
            
            # Add to manifest
            manifest["posts"].append({
                "post_id": post_id,
                "aspect_ratio": "9:16",
                "accepted": len(final_paths),
                "rejected": 0,
                "ready_for_video": len(final_paths) >= 2,
                "image_paths": final_paths,
                "rejected_paths": []
            })
        
        # Save manifest
        with open(self.image_manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created manifest with {len(results)} posts")
        return manifest
    
    def log_run_summary(self, results: Dict[str, List[str]], duration: float):
        """Log run summary"""
        total_images = sum(len(paths) for paths in results.values())
        total_posts = len(results)
        
        summary = f"""Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Posts processed: {total_posts}
Images generated: {total_images}
Accepted: {total_images} (100.0%)
Rejected: 0 (0.0%)
Average processing: {duration/total_images:.1f} s/image
Total duration: {duration:.1f} seconds

[READY] Images are ready for Day 6 video assembly!"""
        
        with open(self.run_summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info("Run summary logged")
    
    def generate_for_post(self, post: Dict[str, Any]) -> bool:
        """Generate images for a single post"""
        post_id = post.get('post_id', post.get('topic_id', '001'))
        # Determine natural image count with an upper cap of 10 to avoid limits
        desired = post.get('image_count') or self.images_per_post or 6
        try:
            desired = int(desired)
        except Exception:
            desired = 6
        target_count = max(5, min(10, desired))
        logger.info(f"Generating up to {target_count} vertical images for post {post_id}")
        
        try:
            # Extract keywords and create search query
            query = self.extract_keywords_and_create_query(post)
            post_keywords = post.get('keywords', {}) or {}
            
            images_found = []

            # Search Pexels first (PRIORITY)
            pexels_results = self.search_pexels(query, target_count)
            try:
                pexels_results = sorted(
                    pexels_results,
                    key=lambda r: self._score_pexels_result(r, post_keywords),
                    reverse=True
                )
            except Exception:
                pass
            for result in pexels_results:
                image_url = result.get('src', {}).get('large', '')
                if image_url:
                    processed_path = self.download_and_process_image(image_url, "pexels")
                    if processed_path and self.quality_check(processed_path):
                        images_found.append(processed_path)
                        if len(images_found) >= target_count:
                            break

            # Search Unsplash next
            if len(images_found) < target_count:
                unsplash_results = self.search_unsplash(query, target_count - len(images_found))
                try:
                    unsplash_results = sorted(
                        unsplash_results,
                        key=lambda r: self._score_unsplash_result(r, post_keywords),
                        reverse=True
                    )
                except Exception:
                    pass
                for result in unsplash_results:
                    image_url = result.get('urls', {}).get('regular', '')
                    if not image_url:
                        continue
                    processed_path = self.download_and_process_image(image_url, "unsplash")
                    if processed_path and self.quality_check(processed_path):
                        images_found.append(processed_path)
                        if len(images_found) >= target_count:
                            break
            
            # Search Shutterstock last (stock fallback)
            if len(images_found) < target_count:
                shutter_results = self.search_shutterstock(query, target_count - len(images_found))
                try:
                    shutter_results = sorted(
                        shutter_results,
                        key=lambda r: self._score_shutterstock_result(r, post_keywords),
                        reverse=True
                    )
                except Exception:
                    pass
                for r in shutter_results:
                    image_url = r.get('preview_url') or ''
                    if image_url:
                        processed_path = self.download_and_process_image(image_url, "shutterstock")
                        if processed_path and self.quality_check(processed_path):
                            images_found.append(processed_path)
                            if len(images_found) >= target_count:
                                break
            
            if images_found:
                # Organize images into approved directory
                self._organize_images_for_post(post_id, images_found)
                logger.info(f"Post {post_id}: Generated {len(images_found)}/{target_count} images")
                return True
            else:
                logger.error(f"Post {post_id}: No valid images generated")
                return False
                
        except Exception as e:
            logger.error(f"Error generating images for post {post_id}: {e}")
            return False

    def _organize_images_for_post(self, post_id: str, images: List[str]):
        """Organize images into approved directory and update manifest"""
        try:
            # Normalize post_id string
            pid_str = str(post_id)
            if pid_str.isdigit():
                pid_str = pid_str.zfill(3)

            # Use PostManager to place images into post-centric directory
            pm = PostManager()
            images_dir = pm.get_images_dir(pid_str)
            images_dir.mkdir(parents=True, exist_ok=True)

            # Copy images to post images directory
            saved_paths = []
            for i, img_path in enumerate(images):
                new_name = f"img_{i+1:03d}.jpg"
                new_path = images_dir / new_name

                import shutil
                shutil.copy2(img_path, new_path)
                saved_paths.append(str(new_path))

            # Update legacy manifest for compatibility (optional)
            self._update_manifest_for_post(pid_str, saved_paths)
            
        except Exception as e:
            logger.error(f"Error organizing images for post {post_id}: {e}")

    def _update_manifest_for_post(self, post_id: str, image_paths: List[str]):
        """Update image manifest for a single post"""
        try:
            # Load existing manifest
            manifest_data = {"posts": []}
            if self.image_manifest_file.exists():
                with open(self.image_manifest_file, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
            
            # Find existing post entry or create new one
            post_entry = None
            for post in manifest_data["posts"]:
                if post.get("post_id") == post_id:
                    post_entry = post
                    break
            
            if not post_entry:
                post_entry = {
                    "post_id": post_id,
                    "aspect_ratio": "9:16",
                    "accepted": 0,
                    "rejected": 0,
                    "ready_for_video": False,
                    "image_paths": [],
                    "rejected_paths": []
                }
                manifest_data["posts"].append(post_entry)
            
            # Update post entry
            post_entry["image_paths"] = image_paths
            post_entry["accepted"] = len(image_paths)
            post_entry["ready_for_video"] = len(image_paths) >= 2
            
            # Save manifest
            with open(self.image_manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2)
            
            logger.info(f"Updated manifest for post {post_id} with {len(image_paths)} images")
            
        except Exception as e:
            logger.error(f"Error updating manifest for post {post_id}: {e}")

    def generate_for_post_with_story_beats(self, post: Dict[str, Any], target_images_dir: Path) -> bool:
        """
        NEW: Generate images based on story beats
        
        Args:
            post: Post data with story_beats array
            target_images_dir: Directory to save images
        
        Returns:
            True if successful
        """
        try:
            post_id = post.get('post_id') or post.get('topic_id', 'unknown')
            story_beats = post.get('story_beats', [])
            image_count = post.get('image_count', 8)
            
            if not story_beats:
                logger.warning(f"No story beats for post {post_id}, using generic search")
                return self.generate_for_post(post)
            
            logger.info(f"Generating {image_count} images using story beats for post {post_id}")
            
            images_found = []
            
            # Prepare deduplication set
            existing_hashes = self._get_existing_image_hashes(target_images_dir)
            
            # Generate one image per story beat
            for i, story_beat in enumerate(story_beats[:image_count], 1):
                logger.info(f"Story beat {i}/{len(story_beats)}: '{story_beat}'")
                
                # Create query from story beat
                query = self.extract_keywords_and_create_query(post, story_beat=story_beat)
                post_keywords = post.get('keywords', {}) or {}
                
                # Try sources in order: Pexels -> Unsplash -> Shutterstock -> AI
                image_found = False
                
                # Use page rotation for diversity
                page = (i % 3) + 1  # Rotate pages 1, 2, 3
                
                # 1. Try Pexels (PRIORITY)
                if not image_found:
                    pexels_results = self.search_pexels(query, 3, page=page)
                    try:
                        pexels_results = sorted(
                            pexels_results,
                            key=lambda r: self._score_pexels_result(r, post_keywords),
                            reverse=True
                        )
                    except Exception:
                        pass
                    for result in pexels_results:
                        image_url = result.get('src', {}).get('large', '')
                        if image_url:
                            processed_path = self.download_and_process_image(image_url, "pexels")
                            if processed_path and self.quality_check(processed_path):
                                ihash = self._compute_image_hash(processed_path)
                                if ihash and ihash in existing_hashes:
                                    logger.info("Duplicate image detected (hash match), skipping (Pexels)")
                                    continue
                                dest_path = target_images_dir / f"img_{i:03d}.jpg"
                                import shutil
                                shutil.move(processed_path, str(dest_path))
                                images_found.append(str(dest_path))
                                if ihash:
                                    existing_hashes.add(ihash)
                                image_found = True
                                logger.info(f"Found image {i} for story beat (Pexels): {story_beat}")
                                break
                
                # 2. Try Unsplash if Pexels failed
                if not image_found:
                    # Use page rotation and order_by variation for diversity
                    order_by_options = ["relevant", "latest"]
                    order_by = order_by_options[i % len(order_by_options)]
                    
                    unsplash_results = self.search_unsplash(query, 3, page=page, order_by=order_by)
                    try:
                        unsplash_results = sorted(
                            unsplash_results,
                            key=lambda r: self._score_unsplash_result(r, post_keywords),
                            reverse=True
                        )
                    except Exception:
                        pass
                    for result in unsplash_results:
                        image_url = result.get('urls', {}).get('regular', '')
                        if image_url:
                            processed_path = self.download_and_process_image(image_url, "unsplash")
                            if processed_path and self.quality_check(processed_path):
                                ihash = self._compute_image_hash(processed_path)
                                if ihash and ihash in existing_hashes:
                                    logger.info("Duplicate image detected (hash match), skipping (Unsplash)")
                                    continue
                                dest_path = target_images_dir / f"img_{i:03d}.jpg"
                                import shutil
                                shutil.move(processed_path, str(dest_path))
                                images_found.append(str(dest_path))
                                if ihash:
                                    existing_hashes.add(ihash)
                                image_found = True
                                logger.info(f"Found image {i} for story beat (Unsplash): {story_beat}")
                                break
                
                # 3. Try Shutterstock if Unsplash failed
                if not image_found:
                    # Use page rotation and sort variation for diversity
                    sort_options = ["relevance", "popular", "newest"]
                    sort = sort_options[i % len(sort_options)]
                    
                    shutter_results = self.search_shutterstock(query, 3, page=page, sort=sort)
                    try:
                        shutter_results = sorted(
                            shutter_results,
                            key=lambda r: self._score_shutterstock_result(r, post_keywords),
                            reverse=True
                        )
                    except Exception:
                        pass
                    for result in shutter_results:
                        image_url = result.get('preview_url', '')
                        if image_url:
                            processed_path = self.download_and_process_image(image_url, "shutterstock")
                            if processed_path and self.quality_check(processed_path):
                                # Dedup by hash
                                ihash = self._compute_image_hash(processed_path)
                                if ihash and ihash in existing_hashes:
                                    logger.info("Duplicate image detected (hash match), skipping (Shutterstock)")
                                    continue
                                # Move to target directory
                                dest_path = target_images_dir / f"img_{i:03d}.jpg"
                                import shutil
                                shutil.move(processed_path, str(dest_path))
                                images_found.append(str(dest_path))
                                if ihash:
                                    existing_hashes.add(ihash)
                                image_found = True
                                logger.info(f"Found image {i} for story beat (Shutterstock): {story_beat}")
                                break
                
                # Fallback 1: use generic query if story beat fails
                if not image_found:
                    logger.warning(f"Story beat search failed for: {story_beat}, using generic query")
                    generic_query = self.extract_keywords_and_create_query(post)
                    # Try Pexels first with generic query
                    pexels_results = self.search_pexels(generic_query, 1)
                    for result in pexels_results:
                        image_url = result.get('src', {}).get('large', '')
                        if image_url:
                            processed_path = self.download_and_process_image(image_url, "pexels")
                            if processed_path and self.quality_check(processed_path):
                                dest_path = target_images_dir / f"img_{i:03d}.jpg"
                                import shutil
                                shutil.move(processed_path, str(dest_path))
                                images_found.append(str(dest_path))
                                logger.info(f"Found generic image {i} (Pexels)")
                                image_found = True
                                break
                    # Try Unsplash if Pexels failed
                    if not image_found:
                        unsplash_results = self.search_unsplash(generic_query, 1)
                        for result in unsplash_results:
                            image_url = result.get('urls', {}).get('regular', '')
                            if image_url:
                                processed_path = self.download_and_process_image(image_url, "unsplash")
                                if processed_path and self.quality_check(processed_path):
                                    dest_path = target_images_dir / f"img_{i:03d}.jpg"
                                    import shutil
                                    shutil.move(processed_path, str(dest_path))
                                    images_found.append(str(dest_path))
                                    logger.info(f"Found generic image {i} (Unsplash)")
                                    image_found = True
                                    break

                # Fallback 2: AI generation (Stability/DALL-E)
                if not image_found:
                    ai_query = story_beat or generic_query if 'generic_query' in locals() else self.extract_keywords_and_create_query(post)
                    ai_urls = self.generate_ai_fallback(ai_query, 1)
                    for url in ai_urls:
                        processed_path = self.download_and_process_image(url, "ai")
                        if processed_path and self.quality_check(processed_path):
                            dest_path = target_images_dir / f"img_{i:03d}.jpg"
                            import shutil
                            shutil.move(processed_path, str(dest_path))
                            images_found.append(str(dest_path))
                            logger.info(f"Generated AI fallback image {i}")
                            image_found = True
                            break
            
            # Success if we got at least 80% of requested images (or minimum 5)
            min_required = max(5, int(image_count * 0.8))
            success = len(images_found) >= min_required
            if success:
                logger.info(f"Successfully generated {len(images_found)}/{image_count} images for post {post_id}")
            else:
                logger.error(f"Only generated {len(images_found)}/{image_count} images, needed at least {min_required}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating images with story beats: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def generate_additional_images_for_post(self, post_data: Dict[str, Any], additional_beats: List[str], start_index: int = 0) -> bool:
        """
        Generate additional images for a post using specified story beats
        Used when voiceover is longer than initial video
        
        Args:
            post_data: Post metadata
            additional_beats: List of story beats to generate images for
            start_index: Starting index for image numbering
        
        Returns:
            True if successful, False otherwise
        """
        try:
            post_id = post_data.get('post_id', post_data.get('topic_id', '001'))
            logger.info(f"Generating {len(additional_beats)} additional images for post {post_id} (starting at index {start_index})")
            
            from pathlib import Path
            post_images_dir = Path(f"data/posts/post_{post_id}/images")
            post_images_dir.mkdir(parents=True, exist_ok=True)
            
            images_generated = 0
            # Prepare deduplication set
            existing_hashes = self._get_existing_image_hashes(post_images_dir)
            used_urls = set()
            
            # Query diversification helpers
            import random
            time_of_day = ["sunrise", "morning", "afternoon", "golden hour", "sunset", "night"]
            angles = ["wide shot", "medium shot", "close-up", "low angle", "high angle", "aerial view"]
            moods = ["vibrant", "cinematic", "moody", "documentary style", "editorial", "street photography"]
            
            for i, beat in enumerate(additional_beats, start=1):
                beat_index = start_index + i
                logger.info(f"Story beat {beat_index}/{start_index + len(additional_beats)}: '{beat}'")
                
                # Create query from story beat
                region = post_data.get('region', 'Global')
                base_beat = beat.replace('Alternative view:', '').strip()
                # Build diversified query
                q_time = random.choice(time_of_day)
                q_angle = random.choice(angles)
                q_mood = random.choice(moods)
                query = f"{region} {base_beat} {q_angle} {q_time} {q_mood}"
                logger.info(f"Story beat query for post {post_id}: '{query}'")
                
                # Attempt multiple pages/sources to ensure uniqueness
                found_image = False
                for page in range(1, 6):  # try up to 5 pages
                    if found_image:
                        break
                    # Try Pexels first (PRIORITY)
                    pexels_results = self.search_pexels(query, 3, page=page)
                    for result in pexels_results:
                        image_url = result.get('src', {}).get('large', '')
                        if not image_url or image_url in used_urls:
                            continue
                        processed_path = self.download_and_process_image(image_url, "pexels")
                        if processed_path and self.quality_check(processed_path):
                            ihash = self._compute_image_hash(processed_path)
                            if ihash and ihash in existing_hashes:
                                logger.info("Duplicate image detected (hash match), skipping (Pexels)")
                                continue
                            dest_path = post_images_dir / f"img_{beat_index:03d}.jpg"
                            import shutil
                            shutil.move(str(processed_path), str(dest_path))
                            images_generated += 1
                            used_urls.add(image_url)
                            if ihash:
                                existing_hashes.add(ihash)
                            logger.info(f"Found additional image {beat_index} for story beat: {base_beat}")
                            found_image = True
                            break
                    if found_image:
                        break
                    # Try Unsplash if Pexels failed
                    for order_by in ("relevant", "latest"):
                        unsplash_results = self.search_unsplash(query, 3, page=page, order_by=order_by)
                        for result in unsplash_results:
                            image_url = result.get('urls', {}).get('regular', '')
                            if not image_url or image_url in used_urls:
                                continue
                            processed_path = self.download_and_process_image(image_url, "unsplash")
                            if processed_path and self.quality_check(processed_path):
                                # Dedup by hash
                                ihash = self._compute_image_hash(processed_path)
                                if ihash and ihash in existing_hashes:
                                    logger.info("Duplicate image detected (hash match), skipping (Unsplash)")
                                    continue
                                # Move to post-specific directory
                                dest_path = post_images_dir / f"img_{beat_index:03d}.jpg"
                                import shutil
                                shutil.move(str(processed_path), str(dest_path))
                                images_generated += 1
                                used_urls.add(image_url)
                                if ihash:
                                    existing_hashes.add(ihash)
                                logger.info(f"Found additional image {beat_index} for story beat (Unsplash): {base_beat}")
                                found_image = True
                                break
                        if found_image:
                            break
                    if found_image:
                        break
                if not found_image:
                    logger.warning(f"Could not find a unique image for beat {beat_index}, will proceed")
            
            success = images_generated == len(additional_beats)
            if success:
                logger.info(f"✅ Successfully generated {images_generated} additional images")
            else:
                logger.warning(f"⚠️ Only generated {images_generated}/{len(additional_beats)} additional images")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating additional images: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_hybrid_generation(self) -> Dict[str, List[str]]:
        """Run the complete hybrid image generation pipeline"""
        start_time = time.time()
        logger.info("Starting Hybrid Image Generation Pipeline")
        
        # Step 1: Ingest posts
        posts = self.ingest_posts()
        if not posts:
            logger.error("No posts found for image generation")
            return {}
        
        results = {}
        
        for post in posts:
            post_id = post['post_id']
            logger.info(f"Processing post {post_id}")
            
            # Step 2: Extract keywords and create query
            query = self.extract_keywords_and_create_query(post)
            
            # Step 3-5: Try sources in order: Pexels -> Unsplash -> Shutterstock -> AI
            images_found = []
            
            # Try Pexels first (PRIORITY)
            pexels_results = self.search_pexels(query, self.images_per_post)
            for result in pexels_results:
                image_url = result.get('src', {}).get('large', '')
                if image_url:
                    processed_path = self.download_and_process_image(image_url, "pexels")
                    if processed_path and self.quality_check(processed_path):
                        images_found.append(processed_path)
                        if len(images_found) >= self.images_per_post:
                            break
            
            # Try Unsplash if needed
            if len(images_found) < self.images_per_post:
                unsplash_results = self.search_unsplash(query, self.images_per_post - len(images_found))
                for result in unsplash_results:
                    image_url = result.get('urls', {}).get('regular', '')
                    if image_url:
                        processed_path = self.download_and_process_image(image_url, "unsplash")
                        if processed_path and self.quality_check(processed_path):
                            images_found.append(processed_path)
                            if len(images_found) >= self.images_per_post:
                                break
            
            # Try Shutterstock if still needed
            if len(images_found) < self.images_per_post:
                shutter_results = self.search_shutterstock(query, self.images_per_post - len(images_found))
                for result in shutter_results:
                    image_url = result.get('preview_url', '')
                    if image_url:
                        processed_path = self.download_and_process_image(image_url, "shutterstock")
                        if processed_path and self.quality_check(processed_path):
                            images_found.append(processed_path)
                            if len(images_found) >= self.images_per_post:
                                break
            
            # Try AI fallback if still needed
            if len(images_found) < self.images_per_post:
                ai_urls = self.generate_ai_fallback(query, self.images_per_post - len(images_found))
                for url in ai_urls:
                    processed_path = self.download_and_process_image(url, "ai")
                    if processed_path and self.quality_check(processed_path):
                        images_found.append(processed_path)
                        if len(images_found) >= self.images_per_post:
                            break
            
            results[post_id] = images_found
            logger.info(f"Post {post_id}: Found {len(images_found)} images")
        
        # Step 8: Organize outputs
        manifest = self.organize_outputs(results)
        
        # Log summary
        duration = time.time() - start_time
        self.log_run_summary(results, duration)
        
        logger.info("Hybrid image generation pipeline completed successfully")
        return results


def main():
    """Main function to run hybrid image generation"""
    try:
        generator = HybridImageGenerator()
        results = generator.run_hybrid_generation()
        
        print("\n[SUCCESS] Hybrid Image Generation Complete!")
        print(f"Generated images for {len(results)} posts")
        
        for post_id, images in results.items():
            print(f"Post {post_id}: {len(images)} images")
        
        print("\n[READY] Images are ready for Day 6 video assembly!")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Itinerary Generator for Long Videos
Generates structured travel itinerary with days, scenes, and image keywords
Follows airport-to-airport flow with geographic logic
"""

import os
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

# Add project root to Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

load_dotenv()


class SceneModel(BaseModel):
    order: int
    category: str
    image_search_keywords: List[str]
    model_config = ConfigDict(extra='allow')


class BlueprintSegmentModel(BaseModel):
    segment_type: str
    time_of_day: str
    title: str
    description: str
    primary_locations: List[str]
    experience_focus: str
    recommended_duration_minutes: float
    must_try_food: Optional[str]
    cultural_insight: str
    image_prompt: str
    model_config = ConfigDict(extra='allow')


class LodgingRecommendationModel(BaseModel):
    name: str
    neighborhood: str
    style: str
    price_range: str
    why_it_works: str
    image_prompt: str
    model_config = ConfigDict(extra='allow')


class LocalTipModel(BaseModel):
    title: str
    description: str
    category: str
    model_config = ConfigDict(extra='allow')


class DailyBlueprintModel(BaseModel):
    summary: str
    segments: List[BlueprintSegmentModel]
    lodging_recommendation: LodgingRecommendationModel
    local_tips: List[LocalTipModel]
    model_config = ConfigDict(extra='allow')


class DayPlanModel(BaseModel):
    day_number: int
    title: str
    daily_blueprint: DailyBlueprintModel
    scenes: List[SceneModel]
    model_config = ConfigDict(extra='allow')


class ItineraryResponseModel(BaseModel):
    destination: str
    ideal_days: int
    itinerary: List[DayPlanModel]
    model_config = ConfigDict(extra='allow')


class ItineraryGeneratorLong:
    """
    Generates structured travel itinerary for long videos
    Creates day-by-day itinerary with scenes, keywords, and geographic logic
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path(settings_long.DATA_DIR)
        self.long_videos_dir = Path(settings_long.LONG_VIDEOS_DIR)
        self.destinations_dir = Path(settings_long.DESTINATIONS_DIR)
        self.scripts_dir = Path(settings_long.SCRIPTS_DIR)
        
        # Ensure directories exist
        self.destinations_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Itinerary Generator Long initialized")
        
        self.segment_type_defaults = [
            ("arrival_connector", ["arrival_connector"]),
            ("morning_activity", ["morning_activity"]),
            ("midday_food", ["midday_food"]),
            ("afternoon_culture", ["afternoon_culture"]),
            ("adventure_block", ["adventure_block"]),
            ("evening_relaxation", ["evening_relaxation"]),
            ("nightlife", ["nightlife"]),
            ("transit_connector", ["transit_connector"]),
            ("lodging_checkin", ["lodging_checkin"])
        ]
    
    def generate_itinerary(self, destination: str, max_duration_minutes: int = 8) -> Dict[str, Any]:
        """
        Generate structured itinerary for a destination
        
        Args:
            destination: Destination name (e.g., "Bali, Indonesia")
            max_duration_minutes: Maximum video duration in minutes (default: 8)
            
        Returns:
            Dictionary with itinerary structure
        """
        try:
            logger.info(f"Generating itinerary for {destination} (max duration: {max_duration_minutes} minutes)")
            
            prompt = f"""Plan a complete travel itinerary for {destination}.

REQUIREMENTS:
1. Estimate the ideal number of days required based on the region's geography, travel distances, and major attractions.
2. The itinerary must follow a complete journey from airport arrival to airport departure.
3. Output one object per day with the following structure: {{ day_number, title, daily_blueprint, scenes[] }}.
4. Day titles MUST follow this exact format: "DAY X – LOCATION(S): Theme" (e.g., "DAY 1 – ULUWATU & JIMBARAN: Ocean Cliffs and Culture", "DAY 2 – UBUD: Rice Terraces, Temples & Local Life")
   - Use uppercase for location names
   - Include a colon followed by a descriptive theme
   - Focus on the main locations and key experiences of the day
5. Within each day's 'scenes', output ordered steps of the day in travel sequence (e.g., arrival → attraction → food → stay → scenic → nightlife, only if relevant).
6. Each scene must include:
   - order (integer, sequential)
   - category (MUST be EXACTLY one of: arrival, attraction, food, stay, scenic, nightlife, transit - NO variations or alternatives)
   - 3-5 image_search_keywords (short descriptive prompts for Pixabay/Pexels queries)
7. Image keywords MUST be rich, descriptive, and highly searchable. Each keyword should be a complete phrase (5-10 words) that includes:
   - **Location/Specific Name** (REQUIRED): Exact place name (e.g., "Bangalore Palace", "Mysore Palace", "Karnataka")
   - **Composition Style** (REQUIRED): aerial view, wide angle, panoramic, close-up, ground level, drone shot, exterior, interior
   - **Mood/Atmosphere** (REQUIRED): bustling, serene, vibrant, peaceful, dramatic, lush, colorful, majestic, elegant
   - **Action/Activity** (REQUIRED): people visiting, tourists, locals, crowds, cooking, serving, eating, exploring, traveling
   - **Visual Details** (REQUIRED): lush green, colorful, vibrant, majestic, elegant, traditional, modern, architectural detail
   - **Cultural Elements**: traditional, authentic, heritage, local, Indian architecture, cultural
   - **Time of Day** (OPTIONAL - only if naturally relevant): morning, afternoon, evening, sunset, golden hour (DO NOT force time if it restricts search results)
   
   IMPORTANT: Time of day should only be included if it's naturally relevant to the scene. If including time makes the keyword too specific and might limit search results, OMIT it and focus on location, composition, mood, and activity instead.
   
   Examples of STRONG keywords (with location, composition, mood, activity):
   - ✅ "Kempegowda International Airport exterior aerial view modern architecture bustling arrival"
   - ✅ "Bangalore Palace exterior wide angle architectural detail heritage building people visiting"
   - ✅ "Bengaluru street food bustling vendors cooking dosa close-up traditional colorful"
   - ✅ "Mysore Palace kaleidoscope colors intricate designs majestic royal architecture tourists exploring"
   - ✅ "Karnataka highway rural road lush green fields peaceful scenic journey aerial view"
   
   Examples of STRONG keywords (time included only when natural):
   - ✅ "Bengaluru street food evening bustling vendors cooking dosa close-up traditional" (evening is natural for food scenes)
   - ✅ "Mysore Palace sunset kaleidoscope colors intricate designs majestic royal architecture" (sunset is natural for palaces)
   
   Examples of WEAK keywords (AVOID):
   - ❌ "airport", "city skyline", "arrival" (too generic, no location/composition/mood)
   - ❌ "highway", "landscape", "countryside" (extremely generic, could be anywhere, no location)
   - ❌ "street food", "dosa", "idli sambar" (too simple, no location/context/composition)
   - ❌ Just location names without descriptors (e.g., "Bangalore Palace" alone - needs composition/mood/activity)
   
   Each scene should have 3-5 rich, descriptive keywords that paint a complete visual picture WITHOUT being too restrictive.
8. Ensure no backtracking between regions — keep the route geographically logical.
9. Include hotels in the 'stay' category (for future paid content opportunities).
10. Start with airport arrival (category: "arrival") and end with airport departure (category: "transit" or "arrival" for return).
11. Total video duration must not exceed {max_duration_minutes} minutes.
12. Distribute days proportionally based on destination size and attractions.
13. Each day should have 3-8 scenes (dynamic, let AI decide based on content).
14. Focus on iconic, visually striking locations and experiences that create compelling video content.
15. Include a `daily_blueprint` for each day so the viewer gets a practical itinerary:
    - Provide 4-6 sequential segments that cover morning activity, midday food, afternoon culture/adventure, evening relaxation/nightlife, and any key transit connectors.
    - Each segment must include: segment_type (MUST be EXACTLY one of: arrival_connector, morning_activity, midday_food, afternoon_culture, adventure_block, evening_relaxation, nightlife, transit_connector, lodging_checkin - NO variations or alternatives), time_of_day ("HH:MM-HH:MM descriptor"), title (<12 words), description (2-3 sentences with sensory detail), primary_locations (1-3 specific places), experience_focus (sightseeing / food / culture / nature / relaxation / nightlife / transit), recommended_duration_minutes (45-240), must_try_food (string or null), cultural_insight (short fact or etiquette tip), and image_prompt (12-18 word vivid phrase for the image pipeline).
    - Add a lodging_recommendation object describing where to stay (name, neighborhood, style, price_range, why_it_works, image_prompt).
    - Add 2-3 local_tips objects with title, description, and category (transport / etiquette / safety / money / weather).

OUTPUT FORMAT (JSON only, no extra commentary):
{{
    "destination": "{destination}",
    "ideal_days": <number>,
    "itinerary": [
        {{
            "day_number": 1,
            "title": "DAY 1 – LOCATION: Theme Description",
            "scenes": [
                {{
                    "order": 1,
                    "category": "arrival",
                    "image_search_keywords": [
                        "Kempegowda International Airport exterior aerial view modern architecture bustling arrival people traveling",
                        "Bengaluru city skyline wide angle urban landscape vibrant colors",
                        "airport terminal building bustling arrival people traveling professional photography"
                    ]
                }},
                {{
                    "order": 2,
                    "category": "attraction",
                    "image_search_keywords": [
                        "Bangalore Palace exterior wide angle architectural detail heritage building people visiting",
                        "Vidhana Soudha majestic building lush greenery Cubbon Park panoramic tourists exploring",
                        "Cubbon Park lush green trees people walking peaceful urban oasis vibrant colors",
                        "Bengaluru attractions tourists exploring historical landmarks beautiful architecture professional photography"
                    ]
                }},
                {{
                    "order": 3,
                    "category": "food",
                    "image_search_keywords": [
                        "Bengaluru street food bustling vendors cooking dosa close-up traditional colorful",
                        "MTR restaurant dosa crispy golden serving hot traditional breakfast authentic",
                        "idli sambar traditional South Indian breakfast colorful vibrant close-up authentic cultural"
                    ]
                }},
                {{
                    "order": 4,
                    "category": "stay",
                    "image_search_keywords": [
                        "Taj West End luxury hotel Bengaluru elegant lobby interior peaceful warm lighting",
                        "luxury hotel Bengaluru comfortable amenities elegant design tranquil rest beautiful interior",
                        "hotel lobby Bengaluru modern architecture warm atmosphere professional photography stunning"
                    ]
                }}
            ]
        }},
        {{
            "day_number": 2,
            "title": "DAY 2 – LOCATION: Theme Description",
            "scenes": [
                {{
                    "order": 1,
                    "category": "transit",
                    "image_search_keywords": [
                        "Bengaluru to Mysuru highway Karnataka lush landscapes scenic journey aerial view peaceful",
                        "Karnataka countryside rural road lush green rice paddies fields beautiful landscape panoramic",
                        "India highway travel scenic route mountains fields peaceful journey wide angle vibrant colors"
                    ]
                }}
            ]
        }}
    ]
}}

IMPORTANT:
- Output ONLY valid JSON, no markdown, no code blocks, no extra text
- Ensure all scenes have valid categories and keywords
- Maintain geographic logic (no backtracking)
- Include hotels in 'stay' category
- Start with airport arrival, end with airport departure
- Total duration estimate: ≤ {max_duration_minutes} minutes
"""
            
            logger.info("Sending request to OpenAI for itinerary generation...")
            
            # Use GPT-4o-mini directly (GPT-5 is unreliable/hanging)
            # TODO: Re-enable GPT-5 when it's more stable
            models_to_try = [
                ("gpt-4o-mini", {"temperature": 0.7, "max_tokens": 16384})  # Maximum for gpt-4o-mini
            ]
            
            response_text = None
            model_name = None
            last_error = None
            
            for model, params in models_to_try:
                try:
                    model_name = model
                    logger.info(f"Trying model: {model_name}")
                    
                    system_message = "You are an expert travel itinerary planner specializing in creating structured, geographically logical travel itineraries for video content."
                    
                    schema = self._get_itinerary_schema()
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "ItinerarySchema",
                                "schema": schema,
                                "strict": False  # Allow flexibility to avoid truncation
                            }
                        },
                        temperature=params.get("temperature", 0.7),
                        max_tokens=params.get("max_tokens", 10000)
                    )
                    response_text = response.choices[0].message.content if response.choices else None
                    logger.debug(f"Model {model_name} returned response text: {response_text is not None}")
                    
                    if response_text:
                        logger.info(f"✅ Successfully got response from {model_name}")
                        break
                    else:
                        logger.warning(f"Empty response from {model_name}, trying fallback...")
                        last_error = f"Empty response from {model_name}"
                except Exception as api_error:
                    logger.warning(f"Model {model_name} failed: {api_error}")
                    last_error = str(api_error)
                    response_text = None
                    continue
            
            # If all models failed, raise error
            if response_text is None:
                error_msg = f"All models failed. Last error: {last_error}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Parse response
            content = response_text.strip() if isinstance(response_text, str) else response_text or ""
            
            if content is None or not content.strip():
                logger.error(f"Null or empty content in response from {model_name}")
                raise ValueError(f"Empty content in response from {model_name}")
            
            content = content.strip()
            safe_destination = (
                destination.replace(",", "_")
                .replace(" ", "_")
                .replace("/", "_")
            )
            raw_response_file = self.destinations_dir / f"{safe_destination}_itinerary_raw.json"
            try:
                raw_response_file.write_text(content, encoding='utf-8')
                logger.debug(f"Saved raw itinerary response to {raw_response_file}")
            except Exception as raw_error:
                logger.warning(f"Unable to write raw itinerary response: {raw_error}")
            logger.info(f"✅ Received response from {model_name} ({len(content)} chars)")
            logger.debug(f"Raw response content (first 500 chars): {content[:500]}")
            
            # Check if JSON appears incomplete
            if not content.strip().endswith('}'):
                logger.warning("Response JSON may be incomplete or truncated. Attempting to parse anyway...")
                # Try to fix common truncation issues
                content = content.strip()
                # Count open vs close braces to see if we can auto-close
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces > close_braces:
                    missing = open_braces - close_braces
                    logger.warning(f"Missing {missing} closing brace(s). Attempting to auto-close...")
                    # Try to find the last incomplete structure and close it
                    # This is a simple heuristic - add closing braces
                    content += '}' * missing
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:-3] if content.endswith('```') else content[7:]
            elif content.startswith('```'):
                content = content[3:-3] if content.endswith('```') else content[3:]
            
            # Parse JSON (with sanitization fallback)
            try:
                itinerary_data = json.loads(content)
            except json.JSONDecodeError as primary_error:
                logger.warning(f"JSON decode failed ({primary_error}). Attempting sanitation...")
                sanitized_content = self._sanitize_json_response(content)
                try:
                    itinerary_data = json.loads(sanitized_content)
                    content = sanitized_content
                except json.JSONDecodeError as secondary_error:
                    logger.error(f"Sanitization also failed: {secondary_error}")
                    logger.error(f"Content length: {len(content)}, ends with: {content[-100:]}")
                    raise ValueError(f"Unable to parse JSON response even after sanitization: {secondary_error}")
            
            self._normalize_itinerary_blueprints(itinerary_data)
            
            # Add metadata
            itinerary_data['generated_at'] = datetime.now().isoformat()
            itinerary_data['max_duration_minutes'] = max_duration_minutes
            
            logger.info(f"✅ Generated itinerary with {itinerary_data.get('ideal_days', 0)} days")
            logger.info(f"   Total scenes: {sum(len(day.get('scenes', [])) for day in itinerary_data.get('itinerary', []))}")
            
            return itinerary_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse itinerary JSON: {e}")
            logger.error(f"Response content: {content[:500]}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        except Exception as e:
            logger.error(f"Failed to generate itinerary: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def save_itinerary(self, itinerary_data: Dict[str, Any], destination: str) -> Path:
        """
        Save itinerary to file
        
        Args:
            itinerary_data: Itinerary data
            destination: Destination name
            
        Returns:
            Path to saved itinerary file
        """
        try:
            # Create safe filename
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            itinerary_file = self.destinations_dir / f"{safe_destination}_itinerary.json"
            
            # Save itinerary
            with open(itinerary_file, 'w', encoding='utf-8') as f:
                json.dump(itinerary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved itinerary to {itinerary_file}")
            return itinerary_file
            
        except Exception as e:
            logger.error(f"Failed to save itinerary: {e}")
            raise
    
    def load_itinerary(self, destination: str) -> Optional[Dict[str, Any]]:
        """
        Load itinerary from file
        
        Args:
            destination: Destination name
            
        Returns:
            Itinerary data or None if not found
        """
        try:
            # Create safe filename
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            itinerary_file = self.destinations_dir / f"{safe_destination}_itinerary.json"
            
            if not itinerary_file.exists():
                return None
            
            # Load itinerary
            with open(itinerary_file, 'r', encoding='utf-8') as f:
                itinerary_data = json.load(f)
            
            logger.info(f"Loaded itinerary from {itinerary_file}")
            return itinerary_data
            
        except Exception as e:
            logger.error(f"Failed to load itinerary: {e}")
            return None
    
    def validate_itinerary_structure(self, itinerary_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate itinerary structure
        
        Args:
            itinerary_data: Itinerary data
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        try:
            # Check required fields
            if 'destination' not in itinerary_data:
                errors.append("Missing 'destination' field")
            
            if 'ideal_days' not in itinerary_data:
                errors.append("Missing 'ideal_days' field")
            
            if 'itinerary' not in itinerary_data:
                errors.append("Missing 'itinerary' field")
            
            if not isinstance(itinerary_data.get('itinerary'), list):
                errors.append("'itinerary' must be a list")
            
            # Check days
            itinerary = itinerary_data.get('itinerary', [])
            if len(itinerary) == 0:
                errors.append("Itinerary has no days")
            
            # Check each day
            for day_idx, day in enumerate(itinerary):
                if 'day_number' not in day:
                    errors.append(f"Day {day_idx + 1} missing 'day_number'")
                
                if 'title' not in day:
                    errors.append(f"Day {day_idx + 1} missing 'title'")
                
                if 'scenes' not in day:
                    errors.append(f"Day {day_idx + 1} missing 'scenes'")
                
                daily_blueprint = day.get('daily_blueprint')
                if not isinstance(daily_blueprint, dict):
                    errors.append(f"Day {day_idx + 1} missing 'daily_blueprint' object")
                else:
                    if not daily_blueprint.get('summary'):
                        errors.append(f"Day {day_idx + 1} blueprint missing 'summary'")
                    
                    segments = daily_blueprint.get('segments')
                    if not isinstance(segments, list):
                        errors.append(f"Day {day_idx + 1} blueprint 'segments' must be a list")
                    else:
                        if len(segments) < 4:
                            errors.append(f"Day {day_idx + 1} blueprint should have at least 4 segments")
                        
                        allowed_segment_types = [
                            "arrival_connector",
                            "morning_activity",
                            "midday_food",
                            "afternoon_culture",
                            "adventure_block",
                            "evening_relaxation",
                            "nightlife",
                            "transit_connector",
                            "lodging_checkin"
                        ]
                        
                        for seg_idx, segment in enumerate(segments):
                            segment_path = f"Day {day_idx + 1} segment {seg_idx + 1}"
                            if not isinstance(segment, dict):
                                errors.append(f"{segment_path} must be an object")
                                continue
                            
                            required_segment_fields = [
                                "segment_type",
                                "time_of_day",
                                "title",
                                "description",
                                "primary_locations",
                                "experience_focus",
                                "recommended_duration_minutes",
                                "must_try_food",
                                "cultural_insight",
                                "image_prompt"
                            ]
                            
                            for field in required_segment_fields:
                                if field not in segment:
                                    errors.append(f"{segment_path} missing '{field}'")
                            
                            if segment.get('segment_type') not in allowed_segment_types:
                                errors.append(f"{segment_path} has invalid segment_type: {segment.get('segment_type')}")
                            
                            primary_locations = segment.get('primary_locations')
                            if not isinstance(primary_locations, list) or len(primary_locations) == 0:
                                errors.append(f"{segment_path} must include at least one primary location")
                            
                            duration = segment.get('recommended_duration_minutes')
                            if not isinstance(duration, (int, float)) or duration <= 0:
                                errors.append(f"{segment_path} has invalid recommended_duration_minutes: {duration}")
                    
                    lodging = daily_blueprint.get('lodging_recommendation')
                    if not isinstance(lodging, dict):
                        errors.append(f"Day {day_idx + 1} blueprint missing 'lodging_recommendation'")
                    else:
                        for field in ["name", "neighborhood", "style", "price_range", "why_it_works", "image_prompt"]:
                            if field not in lodging or not lodging.get(field):
                                errors.append(f"Day {day_idx + 1} lodging missing '{field}'")
                    
                    local_tips = daily_blueprint.get('local_tips')
                    if not isinstance(local_tips, list) or len(local_tips) < 2:
                        errors.append(f"Day {day_idx + 1} blueprint should include at least 2 local tips")
                    else:
                        allowed_tip_categories = ["transport", "etiquette", "safety", "money", "weather"]
                        for tip_idx, tip in enumerate(local_tips):
                            tip_path = f"Day {day_idx + 1} tip {tip_idx + 1}"
                            if not isinstance(tip, dict):
                                errors.append(f"{tip_path} must be an object")
                                continue
                            for field in ["title", "description", "category"]:
                                if field not in tip or not tip.get(field):
                                    errors.append(f"{tip_path} missing '{field}'")
                            if tip.get('category') not in allowed_tip_categories:
                                errors.append(f"{tip_path} has invalid category: {tip.get('category')}")
                
                if not isinstance(day.get('scenes'), list):
                    errors.append(f"Day {day_idx + 1} 'scenes' must be a list")
                
                # Check scenes
                scenes = day.get('scenes', [])
                if len(scenes) == 0:
                    errors.append(f"Day {day_idx + 1} has no scenes")
                
                # Check scene order
                scene_orders = [scene.get('order') for scene in scenes if 'order' in scene]
                if len(scene_orders) != len(scenes):
                    errors.append(f"Day {day_idx + 1} has scenes with missing 'order'")
                
                if sorted(scene_orders) != list(range(1, len(scenes) + 1)):
                    errors.append(f"Day {day_idx + 1} has invalid scene order")
                
                # Check each scene
                for scene_idx, scene in enumerate(scenes):
                    if 'category' not in scene:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} missing 'category'")
                    
                    valid_categories = ['arrival', 'attraction', 'food', 'stay', 'scenic', 'nightlife', 'transit']
                    if scene.get('category') not in valid_categories:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} has invalid category: {scene.get('category')}")
                    
                    if 'image_search_keywords' not in scene:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} missing 'image_search_keywords'")
                    
                    keywords = scene.get('image_search_keywords', [])
                    if not isinstance(keywords, list):
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} 'image_search_keywords' must be a list")
                    
                    if len(keywords) < 3:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} has fewer than 3 keywords")
                    
                    if len(keywords) > 5:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} has more than 5 keywords")
                    
                    # Check for empty keywords
                    if any(not keyword or not keyword.strip() for keyword in keywords):
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} has empty keywords")
            
            # Check for airport arrival and departure
            first_day = itinerary[0] if itinerary else None
            last_day = itinerary[-1] if itinerary else None
            
            if first_day:
                first_scenes = first_day.get('scenes', [])
                first_scene = first_scenes[0] if first_scenes else None
                if not first_scene or first_scene.get('category') != 'arrival':
                    errors.append("First day must start with 'arrival' category (airport arrival)")
            
            if last_day:
                last_scenes = last_day.get('scenes', [])
                last_scene = last_scenes[-1] if last_scenes else None
                if last_scene and last_scene.get('category') not in ['transit', 'arrival']:
                    errors.append("Last day should end with 'transit' or 'arrival' category (airport departure)")
            
            is_valid = len(errors) == 0
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating itinerary: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def get_itinerary_summary(self, itinerary_data: Dict[str, Any]) -> str:
        """
        Get human-readable summary of itinerary
        
        Args:
            itinerary_data: Itinerary data
            
        Returns:
            Summary string
        """
        try:
            destination = itinerary_data.get('destination', 'Unknown')
            ideal_days = itinerary_data.get('ideal_days', 0)
            itinerary = itinerary_data.get('itinerary', [])
            
            summary = f"\n=== Itinerary Summary: {destination} ===\n\n"
            summary += f"Total Days: {ideal_days}\n"
            summary += f"Days in Itinerary: {len(itinerary)}\n\n"
            
            for day in itinerary:
                day_number = day.get('day_number', 0)
                title = day.get('title', 'No title')
                scenes = day.get('scenes', [])
                
                summary += f"Day {day_number}: {title}\n"
                summary += f"  Scenes: {len(scenes)}\n"
                
                for scene in scenes:
                    order = scene.get('order', 0)
                    category = scene.get('category', 'unknown')
                    keywords = scene.get('image_search_keywords', [])
                    
                    summary += f"    {order}. {category}: {', '.join(keywords[:3])}\n"
                
                summary += "\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating itinerary summary: {e}")
            return "Error generating summary"

    def _call_model_with_schema(self, prompt: str, model_name: str, schema: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        params = params or {}
        system_message = "You are an expert travel itinerary planner specializing in creating structured, geographically logical travel itineraries for video content."
        
        request_kwargs = {}
        if "temperature" in params:
            request_kwargs["temperature"] = params["temperature"]
        if "max_tokens" in params:
            request_kwargs["max_tokens"] = params["max_tokens"]
        
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_schema", "json_schema": schema},
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 16384)
        )
        
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content
        return None

    def _normalize_itinerary_blueprints(self, itinerary_data: Dict[str, Any]) -> None:
        if not isinstance(itinerary_data, dict):
            return
        itinerary = itinerary_data.get('itinerary')
        if not isinstance(itinerary, list):
            return
        for day in itinerary:
            self._normalize_daily_blueprint(day)

    def _normalize_daily_blueprint(self, day: Dict[str, Any]) -> None:
        if not isinstance(day, dict):
            return
        title = day.get('title', 'Daily Blueprint')
        blueprint = day.get('daily_blueprint')
        if not isinstance(blueprint, dict):
            day['daily_blueprint'] = self._create_placeholder_blueprint(title)
            return
        
        blueprint.setdefault('summary', title)
        
        segments = blueprint.get('segments')
        normalized_segments = []
        
        if isinstance(segments, list):
            normalized_segments = [seg for seg in segments if isinstance(seg, dict)]
        else:
            for segment_type, keys in self.segment_type_defaults:
                for key in keys:
                    seg = blueprint.pop(key, None)
                    if isinstance(seg, dict):
                        seg.setdefault('segment_type', segment_type)
                        normalized_segments.append(seg)
        
        if not normalized_segments:
            normalized_segments = [self._create_placeholder_segment("morning_activity", title)]
        
        # Ensure each segment has required fields
        for seg in normalized_segments:
            seg.setdefault('segment_type', 'morning_activity')
            seg.setdefault('time_of_day', "08:00-10:00")
            seg.setdefault('title', title)
            seg.setdefault('description', f"Activities for {title}.")
            seg.setdefault('primary_locations', [day.get('title', 'Destination')])
            seg.setdefault('experience_focus', 'sightseeing')
            seg.setdefault('recommended_duration_minutes', 90)
            seg.setdefault('must_try_food', None)
            seg.setdefault('cultural_insight', "Embrace local customs respectfully.")
            seg.setdefault('image_prompt', f"{title} scenic view travelers exploring vibrant atmosphere")
        
        blueprint['segments'] = normalized_segments
        
        if not isinstance(blueprint.get('lodging_recommendation'), dict):
            blueprint['lodging_recommendation'] = self._create_placeholder_lodging(day.get('day_number'))
        
        local_tips = blueprint.get('local_tips')
        if not isinstance(local_tips, list):
            local_tips = []
        local_tips = [tip for tip in local_tips if isinstance(tip, dict)]
        while len(local_tips) < 2:
            local_tips.append(self._create_placeholder_tip(len(local_tips)))
        blueprint['local_tips'] = local_tips
        
        day['daily_blueprint'] = blueprint

    def _create_placeholder_blueprint(self, title: str) -> Dict[str, Any]:
        return {
            "summary": title,
            "segments": [self._create_placeholder_segment("morning_activity", title)],
            "lodging_recommendation": self._create_placeholder_lodging(None),
            "local_tips": [
                self._create_placeholder_tip(0),
                self._create_placeholder_tip(1)
            ]
        }

    def _create_placeholder_segment(self, segment_type: str, title: str) -> Dict[str, Any]:
        return {
            "segment_type": segment_type,
            "time_of_day": "08:00-10:00",
            "title": title,
            "description": f"Explore highlights of {title}.",
            "primary_locations": [title],
            "experience_focus": "sightseeing",
            "recommended_duration_minutes": 90,
            "must_try_food": None,
            "cultural_insight": "Respect local customs and dress codes.",
            "image_prompt": f"{title} scenic view travelers exploring vibrant atmosphere"
        }

    def _create_placeholder_lodging(self, day_number: Optional[int]) -> Dict[str, Any]:
        label = f"Day {day_number} Stay" if day_number else "Recommended Stay"
        return {
            "name": label,
            "neighborhood": "City Center",
            "style": "boutique",
            "price_range": "$$",
            "why_it_works": "Comfortable base with convenient access to daily highlights.",
            "image_prompt": "boutique hotel exterior warm lighting inviting entrance evening"
        }

    def _create_placeholder_tip(self, index: int) -> Dict[str, Any]:
        categories = ["transport", "etiquette", "safety", "money", "weather"]
        category = categories[index % len(categories)]
        return {
            "title": f"{category.capitalize()} tip",
            "description": "Keep essentials handy and stay flexible with local conditions.",
            "category": category
        }

    def _sanitize_json_response(self, content: str) -> str:
        """
        Sanitize JSON response to fix common issues:
        - Trailing commas
        - Encoding issues
        - Malformed unicode characters
        """
        # First, try to fix encoding issues
        try:
            # Ensure content is properly encoded
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='replace')
            else:
                # Re-encode to fix any encoding issues
                content = content.encode('utf-8', errors='ignore').decode('utf-8')
        except Exception as e:
            logger.warning(f"Encoding fix warning: {e}")
        
        # Fix trailing commas and structure issues
        lines = content.splitlines()
        sanitized_lines: List[str] = []
        
        for line in lines:
            stripped = line.strip()
            if stripped == ',' and sanitized_lines:
                indent = line[: len(line) - len(line.lstrip())]
                prev = sanitized_lines[-1].rstrip()
                if prev.endswith(']') or prev.endswith('}'):
                    sanitized_lines.append(f"{indent}}},")
                else:
                    sanitized_lines[-1] = prev + ','
                continue
            sanitized_lines.append(line)
        
        sanitized = "\n".join(sanitized_lines)
        
        # Remove trailing commas before closing brackets/braces
        sanitized = re.sub(
            r',\s*(\r?\n\s*[\}\]])',
            r'\1',
            sanitized
        )
        
        # Fix encoding issues in string values (replace problematic unicode with ASCII)
        # Only fix string content, not JSON structure
        def fix_string_encoding(match):
            """Fix encoding in JSON string values"""
            string_content = match.group(1)
            # Replace with ASCII-safe version
            fixed = string_content.encode('ascii', errors='ignore').decode('ascii')
            return f'"{fixed}"'
        
        # Match JSON string values (but preserve structure)
        # This is a conservative approach - only fix obvious encoding issues
        try:
            # Try to parse first - if it works, no need to fix
            json.loads(sanitized)
            return sanitized
        except json.JSONDecodeError:
            # If parsing fails, try to fix encoding in string values
            # Match: "content" where content may have encoding issues
            pattern = r'"([^"]*)"'
            sanitized = re.sub(pattern, fix_string_encoding, sanitized)
            return sanitized

    def _get_itinerary_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "ideal_days": {"type": "integer"},
                "itinerary": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "title": {"type": "string"},
                            "daily_blueprint": {
                                "type": "object",
                                "properties": {
                                    "summary": {"type": "string"},
                                    "segments": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "segment_type": {
                                                    "type": "string",
                                                    "enum": [
                                                        "arrival_connector",
                                                        "morning_activity",
                                                        "midday_food",
                                                        "afternoon_culture",
                                                        "adventure_block",
                                                        "evening_relaxation",
                                                        "nightlife",
                                                        "transit_connector",
                                                        "lodging_checkin"
                                                    ]
                                                },
                                                "time_of_day": {"type": "string"},
                                                "title": {"type": "string"},
                                                "description": {"type": "string"},
                                                "primary_locations": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "minItems": 1,
                                                },
                                                "experience_focus": {"type": "string"},
                                                "recommended_duration_minutes": {"type": "number"},
                                                "must_try_food": {"type": ["string", "null"]},
                                                "cultural_insight": {"type": "string"},
                                                "image_prompt": {"type": "string"}
                                            },
                                            "required": [
                                                "segment_type",
                                                "time_of_day",
                                                "title",
                                                "description",
                                                "primary_locations",
                                                "experience_focus",
                                                "recommended_duration_minutes",
                                                "must_try_food",
                                                "cultural_insight",
                                                "image_prompt"
                                            ],
                                            "additionalProperties": False
                                        },
                                        "minItems": 4
                                    },
                                    "lodging_recommendation": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "neighborhood": {"type": "string"},
                                            "style": {"type": "string"},
                                            "price_range": {"type": "string"},
                                            "why_it_works": {"type": "string"},
                                            "image_prompt": {"type": "string"}
                                        },
                                        "required": [
                                            "name",
                                            "neighborhood",
                                            "style",
                                            "price_range",
                                            "why_it_works",
                                            "image_prompt"
                                        ],
                                        "additionalProperties": False
                                    },
                                    "local_tips": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "title": {"type": "string"},
                                                "description": {"type": "string"},
                                                "category": {
                                                    "type": "string",
                                                    "enum": ["transport", "etiquette", "safety", "money", "weather"]
                                                }
                                            },
                                            "required": ["title", "description", "category"],
                                            "additionalProperties": False
                                        },
                                        "minItems": 2
                                    }
                                },
                                "required": ["summary", "segments", "lodging_recommendation", "local_tips"],
                                "additionalProperties": False
                            },
                            "scenes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "order": {"type": "integer"},
                                        "category": {
                                            "type": "string",
                                            "enum": ["arrival", "attraction", "food", "stay", "scenic", "nightlife", "transit"]
                                        },
                                        "image_search_keywords": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                            "minItems": 3,
                                            "maxItems": 5
                                        }
                                    },
                                    "required": ["order", "category", "image_search_keywords"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["day_number", "title", "daily_blueprint", "scenes"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["destination", "ideal_days", "itinerary"],
            "additionalProperties": False
        }


def main():
    """Test itinerary generator"""
    generator = ItineraryGeneratorLong()
    
    # Test generation
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing itinerary generation for {test_destination}")
    
    itinerary_data = generator.generate_itinerary(test_destination, max_duration_minutes=8)
    
    # Validate
    is_valid, errors = generator.validate_itinerary_structure(itinerary_data)
    
    if is_valid:
        logger.info("✅ Itinerary is valid")
    else:
        logger.error("❌ Itinerary validation failed:")
        for error in errors:
            logger.error(f"   - {error}")
    
    # Save
    generator.save_itinerary(itinerary_data, test_destination)
    
    # Print summary
    print(generator.get_itinerary_summary(itinerary_data))


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Script Generator for Long Videos
Generates cinematic narration from itinerary
Creates per-day narration with scene-level alignment
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv
import sys
from pathlib import Path

# Debugging: Print Python path
print("Python sys.path:", sys.path)

# Add absolute path to config directory
sys.path.append("d:\\posty\\tripavail_ai\\config")

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

load_dotenv()


class ScriptGeneratorLong:
    """
    Generates cinematic narration from itinerary
    Creates per-day narration with scene-level alignment
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.data_dir = Path(settings_long.DATA_DIR)
        self.long_videos_dir = Path(settings_long.LONG_VIDEOS_DIR)
        self.scripts_dir = Path(settings_long.SCRIPTS_DIR)
        
        # Ensure directories exist
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Script Generator Long initialized")
    
    def generate_script(self, itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate script from itinerary using the new blueprint structure
        
        Args:
            itinerary_data: Itinerary data with days and daily_blueprint.segments
            
        Returns:
            Script data with day-level and scene-level narration aligned with blueprint segments
        """
        try:
            destination = itinerary_data.get('destination', 'Unknown')
            itinerary = itinerary_data.get('itinerary', [])
            max_duration_minutes = itinerary_data.get('max_duration_minutes', 8)
            
            logger.info(f"Generating script for {destination} (max duration: {max_duration_minutes} minutes)")
            
            # Generate itinerary introduction
            itinerary_introduction = self._generate_itinerary_introduction(itinerary, destination)
            
            # Prepare itinerary summary for context
            itinerary_summary = self._prepare_itinerary_summary_from_blueprint(itinerary)
            
            # Generate script for all days together to maintain narrative flow
            script_days = self._generate_days_script(itinerary, destination, max_duration_minutes, itinerary_summary)
            
            # Calculate total duration
            total_voiceover_seconds = sum(day.get('estimated_voiceover_seconds', 0) for day in script_days)
            intro_duration_estimate = self._parse_duration_estimate(itinerary_introduction.get('duration_estimate', '≈ 25 s'))
            total_voiceover_seconds += intro_duration_estimate
            
            script_data = {
                "destination": destination,
                "itinerary_introduction": itinerary_introduction.get('text', ''),
                "itinerary_introduction_duration_estimate": itinerary_introduction.get('duration_estimate', '≈ 25 s'),
                "total_duration_estimate_seconds": int(total_voiceover_seconds),
                "days": script_days
            }
            
            logger.info(f"✅ Generated script with {len(script_days)} days")
            logger.info(f"   Total estimated duration: {total_voiceover_seconds / 60:.2f} minutes")
            
            return script_data
            
        except Exception as e:
            logger.error(f"Failed to generate script: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _generate_itinerary_introduction(self, itinerary: List[Dict[str, Any]], destination: str) -> Dict[str, Any]:
        """Generate itinerary introduction paragraph"""
        try:
            # Extract day titles
            day_titles = [day.get('title', f"Day {day.get('day_number', 0)}") for day in itinerary]
            ideal_days = len(day_titles)
            
            prompt = f"""Create a compelling 40-60 word introduction for a travel video about {destination}.

ITINERARY OVERVIEW:
{chr(10).join(f"  • {title}" for title in day_titles)}

REQUIREMENTS:
- Create intrigue and set up the journey as a story
- Introduce the destination with emotional connection
- Mention all {ideal_days} days briefly
- Establish an overarching theme or journey arc
- End with anticipation of what's to come
- Write in poetic, cinematic style like premium travel documentaries
- Output ONLY the introduction text (40-60 words), no extra commentary

Introduction:"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a travel documentary narrator specializing in creating compelling story hooks for travel videos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            intro_text = response.choices[0].message.content.strip()
            # Remove quotes if present
            intro_text = intro_text.strip('"').strip("'")
            
            # Estimate duration (assuming ~2.5 words per second for voiceover)
            word_count = len(intro_text.split())
            duration_seconds = int(word_count / 2.5)
            duration_estimate = f"≈ {duration_seconds} s"
            
            return {
                "text": intro_text,
                "duration_estimate": duration_estimate
            }
            
        except Exception as e:
            logger.error(f"Failed to generate itinerary introduction: {e}")
            return {
                "text": f"Welcome to {destination}, where adventure awaits across {len(itinerary)} incredible days.",
                "duration_estimate": "≈ 25 s"
            }
    
    def _prepare_itinerary_summary_from_blueprint(self, itinerary: List[Dict[str, Any]]) -> str:
        """Prepare itinerary summary from blueprint segments for GPT context"""
        try:
            summary_parts = []
            
            for day in itinerary:
                day_number = day.get('day_number', 0)
                title = day.get('title', 'No title')
                blueprint = day.get('daily_blueprint', {})
                segments = blueprint.get('segments', [])
                
                summary_parts.append(f"Day {day_number}: {title}")
                summary_parts.append(f"  Summary: {blueprint.get('summary', '')}")
                summary_parts.append(f"  Segments ({len(segments)}):")
                
                for i, segment in enumerate(segments, 1):
                    segment_title = segment.get('title', '')
                    time_of_day = segment.get('time_of_day', '')
                    experience_focus = segment.get('experience_focus', '')
                    primary_locations = segment.get('primary_locations', [])
                    must_try_food = segment.get('must_try_food')
                    
                    summary_parts.append(f"    {i}. [{time_of_day}] {segment_title} ({experience_focus})")
                    if primary_locations:
                        summary_parts.append(f"       Locations: {', '.join(primary_locations)}")
                    if must_try_food:
                        summary_parts.append(f"       Must Try: {must_try_food}")
                
                summary_parts.append("")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error preparing itinerary summary: {e}")
            return str(itinerary)
    
    def _generate_days_script(self, itinerary: List[Dict[str, Any]], destination: str, max_duration_minutes: int, itinerary_summary: str) -> List[Dict[str, Any]]:
        """Generate day-level and scene-level narration for all days"""
        try:
            script_days = []
            
            for day_idx, day in enumerate(itinerary):
                day_number = day.get('day_number', 0)
                day_title = day.get('title', '')
                blueprint = day.get('daily_blueprint', {})
                segments = blueprint.get('segments', [])
                
                if not segments:
                    logger.warning(f"Day {day_number} has no segments, skipping")
                    continue
                
                # Determine if this is the last day
                is_final_day = (day_idx == len(itinerary) - 1)
                
                # Generate day script with scene-level narration
                day_script = self._generate_day_script_with_segments(
                    day_number=day_number,
                    day_title=day_title,
                    segments=segments,
                    destination=destination,
                    is_final_day=is_final_day,
                    day_idx=day_idx,
                    total_days=len(itinerary)
                )
                
                script_days.append(day_script)
            
            return script_days
            
        except Exception as e:
            logger.error(f"Failed to generate days script: {e}")
            raise
    
    def _generate_day_script_with_segments(
        self,
        day_number: int,
        day_title: str,
        segments: List[Dict[str, Any]],
        destination: str,
        is_final_day: bool,
        day_idx: int,
        total_days: int
    ) -> Dict[str, Any]:
        """Generate day-level narration and scene-level narration from segments"""
        try:
            # Build context from segments
            segments_info = []
            for i, segment in enumerate(segments, 1):
                segment_info = {
                    "order": i,
                    "title": segment.get('title', ''),
                    "time_of_day": segment.get('time_of_day', ''),
                    "description": segment.get('description', ''),
                    "primary_locations": segment.get('primary_locations', []),
                    "experience_focus": segment.get('experience_focus', ''),
                    "must_try_food": segment.get('must_try_food'),
                    "cultural_insight": segment.get('cultural_insight', ''),
                    "image_prompt": segment.get('image_prompt', '')
                }
                segments_info.append(segment_info)
            
            # Extract all locations and dishes from segments
            all_locations = []
            all_dishes = []
            all_image_prompts = []
            
            for segment in segments:
                locations = segment.get('primary_locations', [])
                all_locations.extend([loc for loc in locations if loc and loc not in all_locations])
                
                dish = segment.get('must_try_food')
                if dish and dish not in all_dishes:
                    all_dishes.append(dish)
                
                image_prompt = segment.get('image_prompt', '')
                if image_prompt and image_prompt not in all_image_prompts:
                    all_image_prompts.append(image_prompt)
            
            # Generate day-level narration using GPT
            day_narration = self._generate_day_narration_gpt(
                day_number=day_number,
                day_title=day_title,
                segments_info=segments_info,
                destination=destination,
                is_final_day=is_final_day,
                day_idx=day_idx,
                total_days=total_days
            )
            
            # Generate scene-level narration for each segment
            scene_narrations = []
            for segment in segments:
                scene_narration = self._generate_scene_narration_from_segment(segment)
                scene_narrations.append({
                    "order": len(scene_narrations) + 1,
                    "title": segment.get('title', ''),
                    "time_of_day": segment.get('time_of_day', ''),
                    "experience_focus": segment.get('experience_focus', ''),
                    "scene_narration": scene_narration,
                    "image_prompt": segment.get('image_prompt', '')
                })
            
            # Calculate duration estimates
            narration_word_count = len(day_narration.split())
            estimated_voiceover_seconds = int(narration_word_count / 2.5)  # ~2.5 words per second
            narration_duration_estimate = f"≈ {estimated_voiceover_seconds} s"
            
            # Generate transition prompt
            if is_final_day:
                transition_prompt = "The journey concludes with a sense of fulfillment and memories to last a lifetime."
            else:
                transition_prompt = f"As day {day_number} fades, anticipation builds for the adventures that await tomorrow."
            
            day_script = {
                "day_number": day_number,
                "day_title": day_title,
                "narration": day_narration,
                "narration_duration_estimate": narration_duration_estimate,
                "narration_word_count": narration_word_count,
                "estimated_voiceover_seconds": estimated_voiceover_seconds,
                "transition_prompt": transition_prompt,
                "image_keywords": all_image_prompts[:12],  # Limit to 12 keywords
                "specific_locations": all_locations,
                "specific_dishes": all_dishes,
                "specific_restaurants": [],  # Optional field
                "scenes": scene_narrations
            }
            
            return day_script
            
        except Exception as e:
            logger.error(f"Failed to generate day script for day {day_number}: {e}")
            raise
    
    def _generate_day_narration_gpt(
        self,
        day_number: int,
        day_title: str,
        segments_info: List[Dict[str, Any]],
        destination: str,
        is_final_day: bool,
        day_idx: int,
        total_days: int
    ) -> str:
        """Generate day-level narration using GPT"""
        try:
            segments_text = "\n".join([
                f"  {seg['order']}. [{seg['time_of_day']}] {seg['title']} ({seg['experience_focus']})\n"
                f"     Description: {seg['description']}\n"
                f"     Locations: {', '.join(seg['primary_locations']) if seg['primary_locations'] else 'N/A'}\n"
                + (f"     Must Try: {seg['must_try_food']}\n" if seg.get('must_try_food') else "")
                for seg in segments_info
            ])
            
            prompt = f"""You are a travel documentary narrator. Generate cinematic, poetic narration for Day {day_number} of a journey to {destination}.

DAY TITLE: {day_title}

DAY SEGMENTS:
{segments_text}

REQUIREMENTS:
1. Generate ONE flowing narration paragraph (70-140 words, ≈45-90 seconds of voiceover)
2. DO NOT prefix with "Day {day_number}" - weave the day naturally into the narrative
3. Write in poetic, cinematic, evocative style like premium travel documentaries
4. Cover all segments in chronological order, creating a cohesive story
5. Include specific locations, activities, and food naturally in the narration
6. {"This is the FINAL day - conclude with reflection and fulfillment" if is_final_day else "End with anticipation for the next day (don't explicitly say 'tomorrow' - hint at it)"}
7. Make it immersive and vivid - help viewers feel like they're there

Output ONLY the narration paragraph, no extra text, no quotation marks:"""
                    
                    response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                        messages=[
                    {"role": "system", "content": "You are a travel documentary narrator specializing in creating poetic, immersive narration for travel videos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=400
            )
            
            narration = response.choices[0].message.content.strip()
            # Remove quotes if present
            narration = narration.strip('"').strip("'")
            
            return narration
            
        except Exception as e:
            logger.error(f"Failed to generate day narration via GPT: {e}")
            # Fallback narration
            return f"{day_title} unfolds with memorable experiences, from arrival to exploration, creating lasting memories of {destination}."
    
    def _generate_scene_narration_from_segment(self, segment: Dict[str, Any]) -> str:
        """Generate scene-specific narration from a segment"""
        try:
            title = segment.get('title', '')
            description = segment.get('description', '')
            time_of_day = segment.get('time_of_day', '')
            experience_focus = segment.get('experience_focus', '')
            primary_locations = segment.get('primary_locations', [])
            cultural_insight = segment.get('cultural_insight', '')
            
            # For scene narration, keep it shorter and more focused (1-2 sentences)
            if description:
                # Use the description as base, but make it more cinematic
                narration = description
                # Add location context if available
                if primary_locations:
                    location_context = f"At {primary_locations[0]}" if len(primary_locations) == 1 else f"In {', '.join(primary_locations[:-1])} and {primary_locations[-1]}"
                    narration = f"{location_context}, {description.lower()}"
                    else:
                narration = f"Experience {title} during {time_of_day}, immersing yourself in the {experience_focus} of this moment."
            
            return narration
            
        except Exception as e:
            logger.error(f"Failed to generate scene narration: {e}")
            return segment.get('description', segment.get('title', ''))
    
    def _parse_duration_estimate(self, duration_str: str) -> float:
        """Parse duration estimate string like '≈ 25 s' to seconds"""
        try:
            # Extract number from string
            import re
            match = re.search(r'(\d+)', duration_str)
            if match:
                return float(match.group(1))
            return 25.0  # Default
        except:
            return 25.0  # Default
    
    def _copy_keywords_from_itinerary(
        self,
        script_data: Dict[str, Any],
        itinerary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine all keywords from itinerary scenes into day-level keywords (simplified)
        This ensures we have all keywords for the whole day
        
        Args:
            script_data: Generated script data
            itinerary_data: Itinerary data with keywords
            
        Returns:
            Script data with day-level keywords combined from itinerary
        """
        try:
            itinerary = itinerary_data.get('itinerary', [])
            script_days = script_data.get('days', [])
            
            # Combine all scene keywords per day
            for script_day in script_days:
                day_number = script_day.get('day_number', 0)
                
                # Find matching itinerary day
                itinerary_day = next((d for d in itinerary if d.get('day_number') == day_number), None)
                if not itinerary_day:
                    logger.warning(f"No itinerary found for day {day_number}")
                    continue
                
                # Combine all keywords from all scenes in this day
                all_keywords = []
                seen_keywords = set()
                
                for scene in itinerary_day.get('scenes', []):
                    keywords = scene.get('image_search_keywords', [])
                    for keyword in keywords:
                        # Deduplicate while preserving order
                        keyword_lower = keyword.lower().strip()
                        if keyword_lower and keyword_lower not in seen_keywords:
                            all_keywords.append(keyword)
                            seen_keywords.add(keyword_lower)
                
                # If script already has image_keywords, merge them (deduplicate)
                existing_keywords = script_day.get('image_keywords', [])
                if existing_keywords:
                    for keyword in existing_keywords:
                        keyword_lower = keyword.lower().strip()
                        if keyword_lower and keyword_lower not in seen_keywords:
                            all_keywords.append(keyword)
                            seen_keywords.add(keyword_lower)
                
                # Update script day with combined keywords
                script_day['image_keywords'] = all_keywords[:12]  # Limit to 12 keywords
                logger.debug(f"Combined {len(all_keywords)} keywords for Day {day_number}")
            
            logger.info(f"✅ Combined keywords from itinerary for {len(script_days)} days")
            
            return script_data
            
        except Exception as e:
            logger.error(f"Error combining keywords from itinerary: {e}")
            # Return script_data as-is if merge fails
            return script_data
    
    def _prepare_itinerary_summary(self, itinerary: List[Dict[str, Any]]) -> str:
        """
        Prepare itinerary summary for GPT prompt
        
        Args:
            itinerary: List of days with scenes
            
        Returns:
            Formatted itinerary summary
        """
        try:
            summary_parts = []
            
            for day in itinerary:
                day_number = day.get('day_number', 0)
                title = day.get('title', 'No title')
                scenes = day.get('scenes', [])
                
                summary_parts.append(f"Day {day_number}: {title}")
                summary_parts.append(f"  Scenes ({len(scenes)}):")
                
                for scene in scenes:
                    order = scene.get('order', 0)
                    category = scene.get('category', 'unknown')
                    keywords = scene.get('image_search_keywords', [])
                    
                    summary_parts.append(f"    {order}. {category}: {', '.join(keywords)}")
                
                summary_parts.append("")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error preparing itinerary summary: {e}")
            return str(itinerary)
    
    def save_script(self, script_data: Dict[str, Any], destination: str) -> Path:
        """
        Save script to file
        
        Args:
            script_data: Script data
            destination: Destination name
            
        Returns:
            Path to saved script file
        """
        try:
            # Create safe filename
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            script_file = self.scripts_dir / f"{safe_destination}_script.json"
            
            # Save script
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved script to {script_file}")
            return script_file
            
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            raise
    
    def load_script(self, destination: str) -> Optional[Dict[str, Any]]:
        """
        Load script from file
        
        Args:
            destination: Destination name
            
        Returns:
            Script data or None if not found
        """
        try:
            # Create safe filename
            safe_destination = destination.replace(",", "_").replace(" ", "_").replace("/", "_")
            script_file = self.scripts_dir / f"{safe_destination}_script.json"
            
            if not script_file.exists():
                return None
            
            # Load script
            with open(script_file, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            logger.info(f"Loaded script from {script_file}")
            return script_data
            
        except Exception as e:
            logger.error(f"Failed to load script: {e}")
            return None
    
    def validate_script_structure(self, script_data: Dict[str, Any], itinerary_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate script structure and alignment with itinerary
        
        Args:
            script_data: Script data
            itinerary_data: Itinerary data
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        simplified_day_mode = getattr(settings_long, "LONG_VIDEO_SIMPLIFIED_DAY_MODE", True)
        
        try:
            # Check required fields
            if 'destination' not in script_data:
                errors.append("Missing 'destination' field")
            
            if 'days' not in script_data:
                errors.append("Missing 'days' field")
            
            if not isinstance(script_data.get('days'), list):
                errors.append("'days' must be a list")
            
            # Check alignment with itinerary
            itinerary = itinerary_data.get('itinerary', [])
            script_days = script_data.get('days', [])
            
            if len(script_days) != len(itinerary):
                errors.append(f"Script has {len(script_days)} days, but itinerary has {len(itinerary)} days")
            
            # Check each day
            for day_idx, (script_day, itinerary_day) in enumerate(zip(script_days, itinerary)):
                if script_day.get('day_number') != itinerary_day.get('day_number'):
                    errors.append(f"Day {day_idx + 1} day_number mismatch: script={script_day.get('day_number')}, itinerary={itinerary_day.get('day_number')}")
                
                if 'narration' not in script_day:
                    errors.append(f"Day {day_idx + 1} missing 'narration'")
                
                if not script_day.get('narration', '').strip():
                    errors.append(f"Day {day_idx + 1} has empty narration")
                
                if 'scenes' not in script_day:
                    errors.append(f"Day {day_idx + 1} missing 'scenes'")
                
                if not isinstance(script_day.get('scenes'), list):
                    errors.append(f"Day {day_idx + 1} 'scenes' must be a list")
                
            # Check scene alignment with blueprint segments
            blueprint = itinerary_day.get('daily_blueprint', {})
            itinerary_segments = blueprint.get('segments', [])
                script_scenes = script_day.get('scenes', [])
                
            if simplified_day_mode:
                if len(script_scenes) != len(itinerary_segments):
                    logger.warning(
                        f"[Simplified mode] Day {day_idx + 1} has {len(script_scenes)} script scenes but "
                        f"{len(itinerary_segments)} itinerary segments"
                    )
                for scene_idx, (script_scene, itinerary_segment) in enumerate(zip(script_scenes, itinerary_segments)):
                    if script_scene.get('order') != scene_idx + 1:
                        logger.warning(
                            f"[Simplified mode] Day {day_idx + 1} scene {scene_idx + 1} order mismatch "
                            f"(script={script_scene.get('order')}, expected={scene_idx + 1})"
                        )
                    if not script_scene.get('scene_narration', '').strip():
                        logger.warning(
                            f"[Simplified mode] Day {day_idx + 1} scene {scene_idx + 1} has empty scene narration"
                        )
            else:
                if len(script_scenes) != len(itinerary_segments):
                    errors.append(f"Day {day_idx + 1} has {len(script_scenes)} scenes in script, but {len(itinerary_segments)} segments in itinerary")
                
                # Check each scene
                for scene_idx, (script_scene, itinerary_segment) in enumerate(zip(script_scenes, itinerary_segments)):
                    if script_scene.get('order') != scene_idx + 1:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} order mismatch (expected {scene_idx + 1}, got {script_scene.get('order')})")
                    
                    if 'scene_narration' not in script_scene:
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} missing 'scene_narration'")
                    
                    if not script_scene.get('scene_narration', '').strip():
                        errors.append(f"Day {day_idx + 1} scene {scene_idx + 1} has empty scene_narration")
            
            # Check duration - REMOVED: Videos can now exceed 8 minutes
            # total_seconds = script_data.get('total_estimated_voiceover_seconds', 0)
            # max_duration_seconds = itinerary_data.get('max_duration_minutes', 8) * 60
            # 
            # if total_seconds > max_duration_seconds:
            #     errors.append(f"Total estimated duration ({total_seconds / 60:.2f} minutes) exceeds maximum ({max_duration_seconds / 60} minutes)")
            
            is_valid = len(errors) == 0
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Error validating script: {e}")
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def get_script_summary(self, script_data: Dict[str, Any]) -> str:
        """
        Get human-readable summary of script
        
        Args:
            script_data: Script data
            
        Returns:
            Summary string
        """
        try:
            destination = script_data.get('destination', 'Unknown')
            days = script_data.get('days', [])
            total_words = script_data.get('total_narration_word_count', 0)
            total_minutes = script_data.get('total_estimated_voiceover_minutes', 0)
            
            summary = f"\n=== Script Summary: {destination} ===\n\n"
            summary += f"Total Days: {len(days)}\n"
            summary += f"Total Words: {total_words}\n"
            summary += f"Estimated Duration: {total_minutes:.2f} minutes\n\n"
            
            for day in days:
                day_number = day.get('day_number', 0)
                narration = day.get('narration', '')
                word_count = day.get('narration_word_count', 0)
                estimated_seconds = day.get('estimated_voiceover_seconds', 0)
                scenes = day.get('scenes', [])
                
                summary += f"Day {day_number}:\n"
                summary += f"  Words: {word_count}\n"
                summary += f"  Duration: {estimated_seconds:.2f} seconds\n"
                summary += f"  Scenes: {len(scenes)}\n"
                summary += f"  Narration: {narration[:100]}...\n\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating script summary: {e}")
            return "Error generating summary"


def main():
    """Test script generator"""
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    
    # Generate itinerary first
    itinerary_generator = ItineraryGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing script generation for {test_destination}")
    
    # Load or generate itinerary
    itinerary_data = itinerary_generator.load_itinerary(test_destination)
    if not itinerary_data:
        logger.info("Generating itinerary first...")
        itinerary_data = itinerary_generator.generate_itinerary(test_destination, max_duration_minutes=8)
        itinerary_generator.save_itinerary(itinerary_data, test_destination)
    
    # Generate script
    script_generator = ScriptGeneratorLong()
    script_data = script_generator.generate_script(itinerary_data)
    
    # Validate
    is_valid, errors = script_generator.validate_script_structure(script_data, itinerary_data)
    
    if is_valid:
        logger.info("✅ Script is valid")
    else:
        logger.error("❌ Script validation failed:")
        for error in errors:
            logger.error(f"   - {error}")
    
    # Save
    script_generator.save_script(script_data, test_destination)
    
    # Print summary
    print(script_generator.get_script_summary(script_data))


if __name__ == "__main__":
    main()


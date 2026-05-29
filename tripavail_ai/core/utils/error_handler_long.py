#!/usr/bin/env python3
"""
Error Handler for Long Videos
Validates itinerary and script, auto-fixes errors via GPT, retries up to 3 times
Sends email notifications for critical failures
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

# Import long video settings
try:
    from config import settings_long
except ImportError:
    logger.error("settings_long not found. Please ensure config/settings_long.py exists")
    raise

load_dotenv()


class ErrorHandlerLong:
    """
    Handles errors in itinerary and script generation
    Validates structure, auto-fixes errors via GPT, retries up to 3 times
    Sends email notifications for critical failures
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.max_retries = 3
        
        # Email settings (for notifications)
        self.email_enabled = os.getenv('EMAIL_ENABLED', '0') == '1'
        self.notify_email = os.getenv('NOTIFY_EMAIL', '')
        
        logger.info("Error Handler Long initialized")
    
    def validate_and_fix_itinerary(
        self,
        itinerary_data: Dict[str, Any],
        destination: str,
        max_retries: int = None
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate itinerary and auto-fix errors via GPT
        
        Args:
            itinerary_data: Itinerary data to validate
            destination: Destination name
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Tuple of (is_valid, fixed_itinerary, errors)
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        # Import itinerary generator for validation
        from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
        itinerary_generator = ItineraryGeneratorLong()
        
        # Validate itinerary
        is_valid, errors = itinerary_generator.validate_itinerary_structure(itinerary_data)
        
        if is_valid:
            logger.info("✅ Itinerary is valid")
            return True, itinerary_data, []
        
        logger.warning(f"❌ Itinerary validation failed with {len(errors)} errors")
        
        # Try to fix errors
        for attempt in range(1, max_retries + 1):
            logger.info(f"Attempting to fix itinerary (attempt {attempt}/{max_retries})...")
            
            try:
                # Generate fix prompt
                fix_prompt = self._generate_fix_prompt(itinerary_data, errors, destination, "itinerary")
                
                # Request fix from GPT - Use GPT-4o-mini directly (GPT-5 is unreliable/hanging)
                # TODO: Re-enable GPT-5 when it's more stable
                models_to_try = [
                    ("gpt-4o-mini", {"temperature": 0.7, "max_tokens": 4000})
                ]
                
                response = None
                model_name = None
                last_error = None
                
                for model, params in models_to_try:
                    try:
                        model_name = model
                        logger.info(f"Requesting fix from {model_name} (attempt {attempt}/{max_retries})...")
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert at fixing structured travel itinerary data. You excel at identifying and correcting errors in itinerary structure, scene order, categories, and keywords. Always return valid JSON with proper UTF-8 encoding. Replace any problematic unicode characters with ASCII-safe equivalents."
                                },
                                {
                                    "role": "user",
                                    "content": fix_prompt
                                }
                            ],
                            response_format={"type": "json_object"},
                            **params
                        )
                        
                        if response.choices and response.choices[0].message.content:
                            logger.info(f"✅ Received response from {model_name}")
                            break
                        else:
                            last_error = f"Empty response from {model_name}"
                            response = None
                            
                    except Exception as api_error:
                        last_error = str(api_error)
                        response = None
                        logger.warning(f"API error from {model_name}: {api_error}")
                        continue
                
                if response is None or not response.choices:
                    raise ValueError(f"All models failed for itinerary fix. Last error: {last_error}")
                
                # Parse response
                content = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith('```json'):
                    content = content[7:-3]
                elif content.startswith('```'):
                    content = content[3:-3]
                
                # Parse JSON with encoding error handling
                try:
                    fixed_itinerary = json.loads(content)
                except json.JSONDecodeError as json_error:
                    # Try to fix encoding issues
                    logger.warning(f"JSON decode failed: {json_error}. Attempting encoding fix...")
                    sanitized_content = self._fix_json_encoding(content)
                    try:
                        fixed_itinerary = json.loads(sanitized_content)
                        logger.info("✅ Successfully fixed JSON encoding issues")
                    except json.JSONDecodeError as second_error:
                        logger.error(f"Encoding fix also failed: {second_error}")
                        raise
                
                # Add metadata
                fixed_itinerary['generated_at'] = datetime.now().isoformat()
                fixed_itinerary['fixed_at'] = datetime.now().isoformat()
                fixed_itinerary['fix_attempt'] = attempt
                
                # Validate fixed itinerary
                is_valid, new_errors = itinerary_generator.validate_itinerary_structure(fixed_itinerary)
                
                if is_valid:
                    logger.info(f"✅ Itinerary fixed successfully on attempt {attempt}")
                    return True, fixed_itinerary, []
                else:
                    logger.warning(f"⚠️ Fix attempt {attempt} still has {len(new_errors)} errors")
                    errors = new_errors
                    itinerary_data = fixed_itinerary
                    
            except Exception as e:
                logger.error(f"Error during fix attempt {attempt}: {e}")
                continue
        
        # All retries failed
        logger.error(f"❌ Failed to fix itinerary after {max_retries} attempts")
        
        # Send email notification
        if self.email_enabled:
            self._send_error_notification(destination, "itinerary", errors)
        
        # Return original itinerary with errors (graceful degradation)
        return False, itinerary_data, errors
    
    def _fix_json_encoding(self, content: str) -> str:
        """
        Fix common encoding issues in JSON content
        
        Args:
            content: JSON string that may have encoding issues
            
        Returns:
            Sanitized JSON string
        """
        import re
        
        # Try to decode/re-encode to fix encoding issues
        try:
            # If content has encoding issues, try to fix them
            # Replace common problematic characters
            content = content.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Fix common encoding issues in strings
            # Replace malformed unicode sequences with ASCII approximations
            replacements = {
                # Common Czech characters
                'š': 's', 'č': 'c', 'ř': 'r', 'ž': 'z', 'ý': 'y', 'á': 'a', 'í': 'i', 'é': 'e', 'ó': 'o', 'ú': 'u', 'ů': 'u',
                'Š': 'S', 'Č': 'C', 'Ř': 'R', 'Ž': 'Z', 'Ý': 'Y', 'Á': 'A', 'Í': 'I', 'É': 'E', 'Ó': 'O', 'Ú': 'U', 'Ů': 'U',
                # Common Polish characters
                'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z',
            }
            
            # Only replace in string values (not in keys or structure)
            # Use regex to find string values and fix encoding
            def fix_string_encoding(match):
                string_content = match.group(1)
                for old, new in replacements.items():
                    string_content = string_content.replace(old, new)
                return f'"{string_content}"'
            
            # Match JSON string values (content between quotes)
            # This regex matches: "content" but avoids escaped quotes
            pattern = r'"((?:[^"\\]|\\.)*)"'
            content = re.sub(pattern, lambda m: f'"{m.group(1).encode("ascii", errors="ignore").decode("ascii")}"', content)
            
            # Also fix any remaining encoding issues by removing non-printable characters
            # but keep JSON structure intact
            lines = content.split('\n')
            fixed_lines = []
            for line in lines:
                # Only fix string values, not JSON structure
                if ':' in line and '"' in line:
                    # Try to preserve the line structure
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0]
                        value = parts[1]
                        # Fix encoding in value only
                        try:
                            # Try to parse as JSON value first
                            json.loads(value.strip())
                            fixed_lines.append(line)
                        except:
                            # If not valid JSON, try to fix encoding
                            fixed_value = value.encode('ascii', errors='ignore').decode('ascii')
                            fixed_lines.append(f"{key}:{fixed_value}")
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
        except Exception as e:
            logger.warning(f"Encoding fix encountered issue: {e}, using original content")
        
        return content
    
    def validate_and_fix_script(
        self,
        script_data: Dict[str, Any],
        itinerary_data: Dict[str, Any],
        destination: str,
        max_retries: int = None
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate script and auto-fix errors via GPT
        
        Args:
            script_data: Script data to validate
            itinerary_data: Itinerary data (for alignment check)
            destination: Destination name
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Tuple of (is_valid, fixed_script, errors)
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        # Import script generator for validation
        from core.content.generation.script_generator_long import ScriptGeneratorLong
        script_generator = ScriptGeneratorLong()
        
        # Validate script
        is_valid, errors = script_generator.validate_script_structure(script_data, itinerary_data)
        
        if is_valid:
            logger.info("✅ Script is valid")
            return True, script_data, []
        
        logger.warning(f"❌ Script validation failed with {len(errors)} errors")
        
        # Try to fix errors
        for attempt in range(1, max_retries + 1):
            logger.info(f"Attempting to fix script (attempt {attempt}/{max_retries})...")
            
            try:
                # Generate fix prompt
                fix_prompt = self._generate_fix_prompt(script_data, errors, destination, "script", itinerary_data)
                
                # Request fix from GPT - Use GPT-4o-mini directly (GPT-5 is unreliable/hanging)
                # TODO: Re-enable GPT-5 when it's more stable
                models_to_try = [
                    ("gpt-4o-mini", {"temperature": 0.7, "max_tokens": 4000})
                ]
                
                response = None
                model_name = None
                last_error = None
                
                for model, params in models_to_try:
                    try:
                        model_name = model
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are an expert at fixing structured travel script data. You excel at identifying and correcting errors in script structure, narration alignment, scene order, and timing estimates."
                                },
                                {
                                    "role": "user",
                                    "content": fix_prompt
                                }
                            ],
                            response_format={"type": "json_object"},
                            **params
                        )
                        
                        if response.choices and response.choices[0].message.content:
                            break
                        else:
                            last_error = f"Empty response from {model_name}"
                            response = None
                            
                    except Exception as api_error:
                        last_error = str(api_error)
                        response = None
                        continue
                
                if response is None or not response.choices:
                    raise ValueError(f"All models failed for script fix. Last error: {last_error}")
                
                # Parse response
                content = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith('```json'):
                    content = content[7:-3]
                elif content.startswith('```'):
                    content = content[3:-3]
                
                # Parse JSON
                fixed_script = json.loads(content)
                
                # Add metadata
                fixed_script['generated_at'] = script_data.get('generated_at', datetime.now().isoformat())
                fixed_script['fixed_at'] = datetime.now().isoformat()
                fixed_script['fix_attempt'] = attempt
                
                # Validate fixed script
                is_valid, new_errors = script_generator.validate_script_structure(fixed_script, itinerary_data)
                
                if is_valid:
                    logger.info(f"✅ Script fixed successfully on attempt {attempt}")
                    return True, fixed_script, []
                else:
                    logger.warning(f"⚠️ Fix attempt {attempt} still has {len(new_errors)} errors")
                    errors = new_errors
                    script_data = fixed_script
                    
            except Exception as e:
                logger.error(f"Error during fix attempt {attempt}: {e}")
                continue
        
        # All retries failed
        logger.error(f"❌ Failed to fix script after {max_retries} attempts")
        
        # Send email notification
        if self.email_enabled:
            self._send_error_notification(destination, "script", errors)
        
        # Return original script with errors (graceful degradation)
        return False, script_data, errors
    
    def _generate_fix_prompt(
        self,
        data: Dict[str, Any],
        errors: List[str],
        destination: str,
        data_type: str,
        reference_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate fix prompt for GPT
        
        Args:
            data: Data to fix
            errors: List of errors
            destination: Destination name
            data_type: Type of data ("itinerary" or "script")
            reference_data: Reference data (itinerary for script fixes)
            
        Returns:
            Fix prompt string
        """
        try:
            if data_type == "itinerary":
                prompt = f"""You generated this travel itinerary for {destination}, but validation found these issues:

ERRORS:
{chr(10).join(f"- {error}" for error in errors)}

CURRENT ITINERARY:
{json.dumps(data, indent=2)}

REQUIREMENTS:
1. Fix all validation errors listed above.
2. Ensure all required fields are present.
3. Ensure all scenes have valid categories and keywords.
4. Ensure scene order is correct (1, 2, 3, ...).
5. Ensure geographic logic is maintained (no backtracking).
6. Include hotels in 'stay' category.
7. Start with airport arrival, end with airport departure.
8. Ensure all keywords are non-empty and descriptive.

Please regenerate the itinerary with the same structure, fixing all errors.
Output ONLY valid JSON, no markdown, no code blocks, no extra text.
"""
            elif data_type == "script":
                prompt = f"""You generated this travel script for {destination}, but validation found these issues:

ERRORS:
{chr(10).join(f"- {error}" for error in errors)}

CURRENT SCRIPT:
{json.dumps(data, indent=2)}

REFERENCE ITINERARY:
{json.dumps(reference_data, indent=2) if reference_data else "N/A"}

REQUIREMENTS:
1. Fix all validation errors listed above.
2. Ensure script matches itinerary exactly (same days, same scenes, same order).
3. Ensure all days have narration.
4. Ensure all scenes have scene_narration.
5. Ensure total duration does not exceed maximum.
6. Ensure narration matches image keywords.
7. Include hotel mentions naturally.

Please regenerate the script with the same structure, fixing all errors.
Output ONLY valid JSON, no markdown, no code blocks, no extra text.
"""
            else:
                raise ValueError(f"Unknown data_type: {data_type}")
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating fix prompt: {e}")
            return f"Fix the following errors in the {data_type}:\n{chr(10).join(errors)}"
    
    def _send_error_notification(self, destination: str, data_type: str, errors: List[str]):
        """
        Send email notification for critical errors
        
        Args:
            destination: Destination name
            data_type: Type of data ("itinerary" or "script")
            errors: List of errors
        """
        try:
            if not self.email_enabled or not self.notify_email:
                logger.warning("Email notifications disabled or no email address configured")
                return
            
            # Import email sender
            try:
                from core.utils.email_sender import EmailSender
                email_sender = EmailSender()
                
                subject = f"⚠️ Long Video Generation Failed - {destination}"
                body = f"""
Long Video Generation Error

Destination: {destination}
Data Type: {data_type}
Error Count: {len(errors)}
Timestamp: {datetime.now().isoformat()}

Errors:
{chr(10).join(f"- {error}" for error in errors)}

Action Required: Manual review or retry generation
"""
                
                email_sender.send_email(self.notify_email, subject, body)
                logger.info(f"✅ Error notification sent to {self.notify_email}")
                
            except ImportError:
                logger.warning("EmailSender not available, skipping email notification")
            except Exception as e:
                logger.error(f"Failed to send error notification: {e}")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def should_proceed_with_errors(self, errors: List[str], data_type: str) -> bool:
        """
        Determine if we should proceed with errors (graceful degradation)
        
        Args:
            errors: List of errors
            data_type: Type of data ("itinerary" or "script")
            
        Returns:
            True if we should proceed, False otherwise
        """
        # Critical errors that prevent proceeding
        critical_errors = [
            "Missing 'destination' field",
            "Missing 'itinerary' field",
            "Missing 'days' field",
            "Itinerary has no days",
            # Duration check removed - videos can exceed 8 minutes
            # "Total estimated duration exceeds maximum",
        ]
        
        # Check for critical errors
        for error in errors:
            if any(critical in error for critical in critical_errors):
                logger.error(f"Critical error found: {error}. Cannot proceed.")
                return False
        
        # Non-critical errors allow proceeding (graceful degradation)
        logger.warning(f"Non-critical errors found. Proceeding with graceful degradation.")
        return True


def main():
    """Test error handler"""
    from core.content.generation.itinerary_generator_long import ItineraryGeneratorLong
    
    # Generate itinerary
    itinerary_generator = ItineraryGeneratorLong()
    test_destination = "Bali, Indonesia"
    
    logger.info(f"Testing error handler for {test_destination}")
    
    # Generate itinerary
    itinerary_data = itinerary_generator.generate_itinerary(test_destination, max_duration_minutes=8)
    
    # Test error handler
    error_handler = ErrorHandlerLong()
    
    # Validate and fix
    is_valid, fixed_itinerary, errors = error_handler.validate_and_fix_itinerary(
        itinerary_data, test_destination, max_retries=3
    )
    
    if is_valid:
        logger.info("✅ Itinerary is valid after error handling")
    else:
        logger.error("❌ Itinerary still has errors after error handling:")
        for error in errors:
            logger.error(f"   - {error}")
        
        # Check if we should proceed
        if error_handler.should_proceed_with_errors(errors, "itinerary"):
            logger.info("✅ Proceeding with graceful degradation")
        else:
            logger.error("❌ Cannot proceed due to critical errors")


if __name__ == "__main__":
    main()


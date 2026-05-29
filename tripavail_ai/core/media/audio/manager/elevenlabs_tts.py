"""
Premium ElevenLabs TTS client with Turbo v2.5 and Sound Effects
Docs: https://elevenlabs.io/docs/api-reference/text-to-speech
Creator Plan Features: Turbo v2.5, Sound Effects, Premium Voices
"""

import os
from pathlib import Path
from typing import Optional
import requests
from loguru import logger


ELEVEN_API_URL = "https://api.elevenlabs.io/v1"


def synthesize(
    text: str,
    output_path: Path,
    api_key: Optional[str] = None,
    voice_id: Optional[str] = None,
    model: str = "eleven_turbo_v2_5",  # PREMIUM: Turbo v2.5 (3x quality)
    voice_stability: float = 0.5,
    voice_similarity_boost: float = 0.75,
    style: float = 0.4,
    use_speaker_boost: bool = True,
) -> bool:
    """
    Synthesize speech via ElevenLabs REST API using PREMIUM Turbo v2.5 model
    
    Args:
        text: Text to synthesize
        output_path: Where to save MP3
        api_key: ElevenLabs API key
        voice_id: Premium voice ID (Turbo v2.5 compatible)
        model: TTS model (eleven_turbo_v2_5 for premium quality)
        voice_stability: 0.0-1.0 (higher = consistent, lower = expressive)
        voice_similarity_boost: 0.0-1.0 (higher = authentic to voice)
        style: 0.0-1.0 (Turbo v2.5 only - emotional depth)
        use_speaker_boost: Enhance clarity and presence
    
    Returns:
        True on success, False on failure
    """
    try:
        key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return False

        # Use premium voice (not free Rachel)
        vid = voice_id or os.getenv("ELEVENLABS_VOICE_ID") or "21m00Tcm4TlvDq8ikWAM"

        headers = {
            "xi-api-key": key,
            "accept": "audio/mpeg",
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": voice_stability,
                "similarity_boost": voice_similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost,
            },
        }

        url = f"{ELEVEN_API_URL}/text-to-speech/{vid}"
        text_length = len(text)
        logger.info(f"Generating premium voiceover with Turbo v2.5 (voice: {vid[:8]}...) - Text length: {text_length} chars")
        
        # Increase timeout for longer texts (120 seconds for long voiceovers)
        timeout = 120 if text_length > 1000 else 60
        
        # Retry logic with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
                resp.raise_for_status()

                # Save MP3
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)

                logger.info(f"Premium voiceover generated: {output_path}")
                return True
                
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                    logger.warning(f"ElevenLabs API timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"ElevenLabs API timeout after {max_retries} attempts (timeout: {timeout}s, text length: {text_length} chars)")
                    return False
                    
            except requests.exceptions.HTTPError as e:
                # Don't retry on HTTP errors (rate limits, auth errors, etc.)
                error_msg = e.response.text[:200] if hasattr(e.response, 'text') else str(e)
                logger.error(f"ElevenLabs API error: {e.response.status_code} - {error_msg}")
                return False
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5
                    logger.warning(f"ElevenLabs API error (attempt {attempt + 1}/{max_retries}): {e}, retrying in {wait_time}s...")
                    import time
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Failed to generate voiceover after {max_retries} attempts: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to generate voiceover: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def generate_sound_effect(
    prompt: str,
    output_path: Path,
    api_key: Optional[str] = None,
    duration_seconds: float = 3.0,
    prompt_influence: float = 0.3,
) -> bool:
    """
    Generate sound effects using ElevenLabs Sound Effects API
    PREMIUM FEATURE: Creator Plan and above
    
    Args:
        prompt: Description of sound effect (e.g., "ocean waves crashing")
        output_path: Where to save MP3
        api_key: ElevenLabs API key
        duration_seconds: Length of sound effect (0.5 - 22 seconds)
        prompt_influence: How closely to follow prompt (0.0 - 1.0)
    
    Returns:
        True on success, False on failure
    """
    try:
        key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return False

        headers = {
            "xi-api-key": key,
            "accept": "audio/mpeg",
            "Content-Type": "application/json",
        }

        payload = {
            "text": prompt,
            "duration_seconds": duration_seconds,
            "prompt_influence": prompt_influence,
        }

        url = f"{ELEVEN_API_URL}/sound-generation"
        logger.info(f"Generating sound effect: '{prompt}' ({duration_seconds}s)")
        
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()

        # Save MP3
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(resp.content)

        logger.info(f"Sound effect generated: {output_path}")
        return True
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"ElevenLabs Sound API error: {e.response.status_code} - {e.response.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"Failed to generate sound effect: {e}")
        return False


def list_available_voices(api_key: Optional[str] = None) -> list:
    """
    List all available voices from your ElevenLabs account
    Helps identify premium Turbo v2.5 voices
    
    Returns:
        List of voice dictionaries with id, name, and labels
    """
    try:
        key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return []

        headers = {"xi-api-key": key}
        url = f"{ELEVEN_API_URL}/voices"
        
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        
        data = resp.json()
        voices = data.get('voices', [])
        
        logger.info(f"Found {len(voices)} available voices")
        return voices
        
    except Exception as e:
        logger.error(f"Failed to list voices: {e}")
        return []



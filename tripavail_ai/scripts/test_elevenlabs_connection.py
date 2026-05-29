#!/usr/bin/env python3
"""
Test ElevenLabs API Connection
Tests API key and voice ID configuration
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging FIRST
from core.utils import logging_setup  # noqa

import os
import requests
from pathlib import Path
from loguru import logger
from config import settings_long
from typing import Dict


class ElevenLabsConnectionTester:
    """
    Test ElevenLabs API connection and voice configuration
    """
    
    def __init__(self):
        self.api_key = settings_long.ELEVENLABS_API_KEY_LONG
        self.voice_id = settings_long.ELEVENLABS_VOICE_ID_LONG
        self.api_url = "https://api.elevenlabs.io/v1"
        
        logger.info("ElevenLabs Connection Tester initialized")
        logger.info(f"API Key: {self.api_key[:10]}...{self.api_key[-10:]}" if self.api_key else "API Key: NOT SET")
        logger.info(f"Voice ID: {self.voice_id}")
    
    def test_api_connection(self) -> bool:
        """
        Test ElevenLabs API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("TESTING ELEVENLABS API CONNECTION")
            logger.info("=" * 60)
            
            if not self.api_key:
                logger.error("❌ ElevenLabs API key not found")
                return False
            
            # Test 1: List voices
            logger.info("Test 1: Listing available voices...")
            url = f"{self.api_url}/voices"
            headers = {
                "xi-api-key": self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                voices = data.get('voices', [])
                logger.info(f"✅ API connection successful! Found {len(voices)} voices")
                
                # List available voices
                logger.info("\nAvailable voices:")
                for i, voice in enumerate(voices[:10], 1):  # Show first 10
                    voice_id = voice.get('voice_id', '')
                    voice_name = voice.get('name', 'Unknown')
                    voice_category = voice.get('category', 'Unknown')
                    logger.info(f"  {i}. {voice_name} (ID: {voice_id[:20]}...) [{voice_category}]")
                
                if len(voices) > 10:
                    logger.info(f"  ... and {len(voices) - 10} more voices")
                
                return True
            else:
                logger.error(f"❌ API connection failed: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing API connection: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_voice_id(self) -> bool:
        """
        Test if the configured voice ID is valid
        
        Returns:
            True if voice ID is valid, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("TESTING VOICE ID")
            logger.info("=" * 60)
            
            if not self.voice_id:
                logger.error("❌ Voice ID not configured")
                return False
            
            if not self.api_key:
                logger.error("❌ ElevenLabs API key not found")
                return False
            
            # Test 2: Get voice details
            logger.info(f"Test 2: Getting voice details for '{self.voice_id}'...")
            url = f"{self.api_url}/voices/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                voice_name = data.get('name', 'Unknown')
                voice_category = data.get('category', 'Unknown')
                voice_description = data.get('description', 'No description')
                
                logger.info(f"✅ Voice ID is valid!")
                logger.info(f"Voice Name: {voice_name}")
                logger.info(f"Voice Category: {voice_category}")
                logger.info(f"Voice Description: {voice_description}")
                
                return True
            elif response.status_code == 404:
                logger.error(f"❌ Voice ID not found: {self.voice_id}")
                logger.error("Please check the voice ID and try again")
                return False
            else:
                logger.error(f"❌ Error getting voice details: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing voice ID: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def test_voiceover_generation(self) -> bool:
        """
        Test voiceover generation with a short text
        
        Returns:
            True if voiceover generation successful, False otherwise
        """
        try:
            logger.info("=" * 60)
            logger.info("TESTING VOICEOVER GENERATION")
            logger.info("=" * 60)
            
            if not self.api_key:
                logger.error("❌ ElevenLabs API key not found")
                return False
            
            if not self.voice_id:
                logger.error("❌ Voice ID not configured")
                return False
            
            # Test 3: Generate voiceover
            logger.info(f"Test 3: Generating voiceover with voice '{self.voice_id}'...")
            
            test_text = "This is a test voiceover for the long video system. The voice should sound clear and natural."
            
            url = f"{self.api_url}/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "accept": "audio/mpeg",
                "Content-Type": "application/json",
            }
            
            data = {
                "text": test_text,
                "model_id": settings_long.ELEVENLABS_MODEL_LONG,
                "voice_settings": settings_long.ELEVENLABS_TTS_LONG
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # Save test voiceover
                test_output_dir = Path("data/long_videos/voiceovers")
                test_output_dir.mkdir(parents=True, exist_ok=True)
                test_output_path = test_output_dir / "test_voiceover.mp3"
                
                with open(test_output_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = test_output_path.stat().st_size / 1024  # KB
                logger.info(f"✅ Voiceover generation successful!")
                logger.info(f"Test voiceover saved: {test_output_path}")
                logger.info(f"File size: {file_size:.2f} KB")
                
                return True
            else:
                logger.error(f"❌ Voiceover generation failed: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing voiceover generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Run all tests
        
        Returns:
            Dictionary with test results
        """
        results = {
            "api_connection": False,
            "voice_id": False,
            "voiceover_generation": False
        }
        
        logger.info("=" * 60)
        logger.info("ELEVENLABS CONNECTION TEST SUITE")
        logger.info("=" * 60)
        logger.info(f"API Key: {self.api_key[:10]}...{self.api_key[-10:]}" if self.api_key else "API Key: NOT SET")
        logger.info(f"Voice ID: {self.voice_id}")
        logger.info(f"Model: {settings_long.ELEVENLABS_MODEL_LONG}")
        logger.info("=" * 60)
        
        # Test 1: API Connection
        results["api_connection"] = self.test_api_connection()
        
        # Test 2: Voice ID (only if API connection successful)
        if results["api_connection"]:
            results["voice_id"] = self.test_voice_id()
        else:
            logger.warning("Skipping voice ID test (API connection failed)")
        
        # Test 3: Voiceover Generation (only if voice ID is valid)
        if results["voice_id"]:
            results["voiceover_generation"] = self.test_voiceover_generation()
        else:
            logger.warning("Skipping voiceover generation test (voice ID invalid)")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"API Connection: {'✅ PASSED' if results['api_connection'] else '❌ FAILED'}")
        logger.info(f"Voice ID: {'✅ PASSED' if results['voice_id'] else '❌ FAILED'}")
        logger.info(f"Voiceover Generation: {'✅ PASSED' if results['voiceover_generation'] else '❌ FAILED'}")
        logger.info("=" * 60)
        
        return results


def main():
    """Main function"""
    try:
        logger.info("=" * 60)
        logger.info("ELEVENLABS CONNECTION TEST")
        logger.info("=" * 60)
        
        # Initialize tester
        tester = ElevenLabsConnectionTester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Exit with appropriate code
        if all(results.values()):
            logger.info("✅ All tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()


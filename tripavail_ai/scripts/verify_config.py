#!/usr/bin/env python3
"""Verify environment variables and configuration"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Environment Variables Check")
print("=" * 60)

# Check critical variables
checks = {
    "SHUTTERSTOCK_ACCESS_TOKEN": os.getenv("SHUTTERSTOCK_ACCESS_TOKEN"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY"),
}

for key, value in checks.items():
    status = "✅ Set" if value else "❌ Missing"
    preview = value[:30] + "..." if value and len(value) > 30 else (value or "")
    print(f"{key}: {status}")
    if value:
        print(f"  Preview: {preview}")

print("\n" + "=" * 60)
print("Testing HybridImageGenerator")
print("=" * 60)

try:
    from core.media.images.generator.hybrid_generator import HybridImageGenerator
    gen = HybridImageGenerator()
    
    print(f"Shutterstock token: {'✅ Set' if gen.shutterstock_access_token else '❌ Missing'}")
    print(f"OpenAI client: {'✅ Available' if gen.openai_client else '❌ Missing'}")
    print(f"Has OpenAI optimization: {'✅ Yes' if hasattr(gen, '_optimize_query_with_openai') else '❌ No'}")
    
    print("\n" + "=" * 60)
    print("Testing EnhancedVoiceoverGenerator (ElevenLabs)")
    print("=" * 60)
    
    from core.media.video.generator.enhanced_voiceover import EnhancedVoiceoverGenerator
    voice_gen = EnhancedVoiceoverGenerator()
    
    print(f"ElevenLabs API Key: {'✅ Set' if voice_gen.eleven_api_key else '❌ Missing'}")
    if voice_gen.eleven_api_key:
        print(f"  Preview: {voice_gen.eleven_api_key[:30]}...")
    print(f"Voice Map: {'✅ Loaded' if voice_gen.eleven_voice_map else '❌ Missing'}")
    if voice_gen.eleven_voice_map:
        print(f"  Voices: {len(voice_gen.eleven_voice_map)} premium voices")
    
    print("\n🎉 Configuration verified!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


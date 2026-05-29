#!/usr/bin/env python3
"""
Test ElevenLabs Premium Features
- Turbo v2.5 Voiceover
- AI-Generated Ambient Sounds
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("ELEVENLABS PREMIUM FEATURES TEST")
print("="*60 + "\n")

# Test 1: Check Configuration
print("[1/4] Checking Configuration...")
try:
    from config import settings
    
    api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
    model = getattr(settings, 'ELEVENLABS_MODEL', None)
    voice_id = getattr(settings, 'ELEVENLABS_VOICE_ID', None)
    sfx_enabled = getattr(settings, 'ELEVENLABS_SOUND_EFFECTS', {}).get('enabled', False)
    
    print(f"  API Key: {'✓ Configured' if api_key else '✗ Missing'}")
    print(f"  Model: {model or 'NOT SET'}")
    print(f"  Default Voice: {voice_id[:8]}..." if voice_id else "  Default Voice: NOT SET")
    print(f"  Sound Effects: {'✓ Enabled' if sfx_enabled else '✗ Disabled'}")
    
    if not api_key:
        print("\n❌ ElevenLabs API Key not configured!")
        print("Set ELEVENLABS_API_KEY in config/settings.py")
        sys.exit(1)
    
    if model != "eleven_turbo_v2_5":
        print(f"\n⚠️  Model is '{model}', expected 'eleven_turbo_v2_5'")
        print("Update ELEVENLABS_MODEL in config/settings.py")
    
    print("  ✓ Configuration OK\n")
    
except Exception as e:
    print(f"  ✗ Error: {e}\n")
    sys.exit(1)

# Test 2: Test Premium Voiceover
print("[2/4] Testing Premium Turbo v2.5 Voiceover...")
try:
    from core.media.audio.manager.elevenlabs_tts import synthesize
    
    test_text = "Welcome to TripAvail. Experience luxury travel like never before."
    test_output = Path("test_premium_voice.mp3")
    
    print(f"  Generating: '{test_text[:40]}...'")
    
    success = synthesize(
        text=test_text,
        output_path=test_output,
        api_key=api_key,
        voice_id=voice_id,
        model=model or "eleven_turbo_v2_5"
    )
    
    if success and test_output.exists():
        size_kb = test_output.stat().st_size / 1024
        print(f"  ✓ Generated: {test_output} ({size_kb:.1f} KB)")
        print(f"  🎧 Listen to verify quality!")
    else:
        print(f"  ✗ Failed to generate voiceover")
    print()
    
except Exception as e:
    print(f"  ✗ Error: {e}\n")

# Test 3: Test Ambient Sound Generation
print("[3/4] Testing AI Ambient Sound Generation...")
try:
    from core.media.audio.manager.ambient_sound import AmbientSoundManager
    
    manager = AmbientSoundManager()
    
    if not manager.enabled or not manager.api_key:
        print("  ⚠️  Ambient sounds disabled or API key missing")
        print("  Set ELEVENLABS_SOUND_EFFECTS['enabled'] = True in config\n")
    else:
        print(f"  Testing content type: 'beach'")
        
        beach_sound = manager.get_ambient_for_content_type("beach", duration=5.0)
        
        if beach_sound and beach_sound.exists():
            size_kb = beach_sound.stat().st_size / 1024
            print(f"  ✓ Generated: {beach_sound.name} ({size_kb:.1f} KB)")
            print(f"  🌊 Beach ambient sound created!")
        else:
            print(f"  ✗ Failed to generate ambient sound")
        print()
        
except Exception as e:
    print(f"  ✗ Error: {e}\n")

# Test 4: List Available Voices
print("[4/4] Listing Available Premium Voices...")
try:
    from core.media.audio.manager.elevenlabs_tts import list_available_voices
    
    voices = list_available_voices(api_key)
    
    if voices:
        print(f"  Found {len(voices)} voices in your account:\n")
        
        # Show first 5 voices
        for voice in voices[:5]:
            name = voice.get('name', 'Unknown')
            voice_id = voice.get('voice_id', '')
            labels = voice.get('labels', {})
            
            print(f"  • {name}")
            print(f"    ID: {voice_id}")
            print(f"    Gender: {labels.get('gender', 'N/A')}, "
                  f"Accent: {labels.get('accent', 'N/A')}, "
                  f"Age: {labels.get('age', 'N/A')}")
            print()
        
        if len(voices) > 5:
            print(f"  ... and {len(voices) - 5} more voices")
            print(f"\n  View all at: https://elevenlabs.io/voice-lab")
    else:
        print("  ✗ No voices found or API error")
    print()
    
except Exception as e:
    print(f"  ✗ Error: {e}\n")

# Summary
print("="*60)
print("TEST COMPLETE")
print("="*60)
print("\n✅ Next Steps:")
print("1. Listen to test_premium_voice.mp3 to verify quality")
print("2. Check assets/audio/ambient_elevenlabs/ for generated sounds")
print("3. Run: python bot.py --test")
print("4. Watch for 'Turbo v2.5 PREMIUM' in logs\n")

print("📖 Full documentation: ELEVENLABS_PREMIUM_IMPLEMENTED.md\n")


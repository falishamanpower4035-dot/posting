#!/usr/bin/env python3
"""
Test Script for TripAvail AI Enhancements
Tests all new features independently
"""

import sys
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_music_library():
    """Test music library functionality"""
    print_header("Testing Music Library")
    
    try:
        from modules.audio_manager.music_library import MusicLibrary
        
        library = MusicLibrary()
        print("✅ Music Library initialized")
        
        # Test music selection
        test_regions = ["Maldives", "Swiss Alps", "Tokyo"]
        for region in test_regions:
            music = library.get_music_for_region(region)
            if music:
                print(f"✓ Region '{region}' → Music: {music['name']} ({music['category']})")
        
        # Show available tracks
        tracks = library.list_all_tracks()
        print(f"\n📀 Total music tracks available: {len(tracks)}")
        
        return True
    except Exception as e:
        print(f"❌ Music Library test failed: {e}")
        return False

def test_voiceover_generator():
    """Test enhanced voiceover generator"""
    print_header("Testing Enhanced Voiceover Generator")
    
    try:
        from modules.video_generator.enhanced_voiceover import EnhancedVoiceoverGenerator
        
        generator = EnhancedVoiceoverGenerator()
        print("✅ Voiceover Generator initialized")
        
        # Test voice selection
        test_cases = [
            {"caption": "Adventure awaits in the Alps", "region": "Switzerland"},
            {"caption": "Luxury resort experience", "region": "Maldives"},
            {"caption": "Cultural heritage tour", "region": "Japan"}
        ]
        
        for test in test_cases:
            voice = generator.select_voice_for_content(
                test["caption"], 
                test["region"]
            )
            voice_info = generator.get_voice_info(voice)
            print(f"✓ '{test['caption'][:30]}...' → Voice: {voice} ({voice_info['description']})")
        
        # Show available voices
        voices = generator.list_available_voices()
        print(f"\n🎤 Total voices available: {len(voices)}")
        
        return True
    except Exception as e:
        print(f"❌ Voiceover Generator test failed: {e}")
        return False

def test_text_overlay_manager():
    """Test text overlay manager"""
    print_header("Testing Text Overlay Manager")
    
    try:
        from modules.video_generator.text_overlay_manager import TextOverlayManager
        
        manager = TextOverlayManager()
        print("✅ Text Overlay Manager initialized")
        
        # Test subtitle generation
        test_text = "Discover paradise beaches. Crystal clear waters await. Book your dream vacation today!"
        subtitles = manager.generate_subtitles_from_text(test_text, duration=15.0)
        print(f"✓ Generated {len(subtitles)} subtitles from text")
        
        for i, sub in enumerate(subtitles[:3], 1):
            print(f"  {i}. [{sub['start']:.1f}s-{sub['end']:.1f}s]: {sub['text'][:40]}...")
        
        # Test keyword extraction
        keywords = manager.extract_keywords(test_text)
        print(f"✓ Extracted keywords: {', '.join(keywords)}")
        
        # Show CTA templates
        print(f"\n📢 CTA templates available: {len(manager.cta_templates)}")
        
        return True
    except Exception as e:
        print(f"❌ Text Overlay Manager test failed: {e}")
        return False

def test_trending_detector():
    """Test trending topic detector"""
    print_header("Testing Trending Topic Detector")
    
    try:
        from modules.content_intelligence.trending_detector import TrendingTopicDetector
        
        detector = TrendingTopicDetector()
        print("✅ Trending Topic Detector initialized")
        
        # Test content scoring
        sample_post = {
            "caption": "Discover sustainable travel in Bali #EcoTourism #SustainableTravel",
            "region": "Bali",
            "hashtags": ["#EcoTourism", "#SustainableTravel", "#Bali"],
            "score": 8
        }
        
        trend_score = detector.score_content_trendiness(sample_post)
        print(f"✓ Content trend score: {trend_score}/100")
        
        # Get suggestions
        suggestions = detector.suggest_content_improvements(sample_post)
        print(f"✓ Suggested hashtags: {', '.join(suggestions.get('suggested_hashtags', [])[:3])}")
        
        return True
    except Exception as e:
        print(f"❌ Trending Detector test failed: {e}")
        return False

def test_engagement_predictor():
    """Test engagement predictor"""
    print_header("Testing Engagement Predictor")
    
    try:
        from modules.content_intelligence.engagement_predictor import EngagementPredictor
        
        predictor = EngagementPredictor()
        print("✅ Engagement Predictor initialized")
        
        # Test prediction
        sample_post = {
            "caption": "Stunning Maldives beaches 🏝️ #TravelGoals #Paradise",
            "region": "Maldives",
            "hashtags": ["#Maldives", "#TravelGoals", "#Paradise", "#Beach"],
            "score": 8
        }
        
        prediction = predictor.predict_engagement(sample_post, "instagram")
        print(f"✓ Predicted engagement: {prediction.get('predicted_engagement_rate', 0):.2f}%")
        print(f"✓ Engagement level: {prediction.get('engagement_level', 'N/A')}")
        print(f"✓ Viral potential: {prediction.get('viral_potential', 0):.1f}/100")
        
        # Test optimal timing
        times = predictor.optimize_posting_time("instagram", "global")
        print(f"✓ Optimal posting times: {', '.join(times['optimal_times'])}")
        
        return True
    except Exception as e:
        print(f"❌ Engagement Predictor test failed: {e}")
        return False

def test_seasonal_optimizer():
    """Test seasonal optimizer"""
    print_header("Testing Seasonal Content Optimizer")
    
    try:
        from modules.content_intelligence.seasonal_optimizer import SeasonalContentOptimizer
        
        optimizer = SeasonalContentOptimizer()
        print("✅ Seasonal Optimizer initialized")
        
        # Get current season
        season = optimizer.get_current_season()
        print(f"✓ Current season: {season.upper()}")
        
        # Test seasonal analysis
        sample_post = {
            "caption": "Beach vacation in Thailand",
            "region": "Thailand",
            "hashtags": ["#Thailand", "#Beach"]
        }
        
        analysis = optimizer.analyze_seasonal_relevance(sample_post)
        print(f"✓ Seasonal score: {analysis.get('seasonal_score', 0)}/100")
        print(f"✓ Is timely: {analysis.get('is_timely', False)}")
        
        # Get upcoming holidays
        holidays = optimizer.get_upcoming_holidays()
        if holidays:
            print(f"✓ Upcoming holidays: {', '.join([h['name'] for h in holidays[:3]])}")
        
        return True
    except Exception as e:
        print(f"❌ Seasonal Optimizer test failed: {e}")
        return False

def test_audio_ducking():
    """Test audio ducking (without actual files)"""
    print_header("Testing Audio Ducking")
    
    try:
        from modules.audio_manager.audio_ducking import AudioDucker
        
        ducker = AudioDucker(music_volume=0.15, ducked_volume=0.05)
        print("✅ Audio Ducker initialized")
        print(f"✓ Music volume: {ducker.music_volume}")
        print(f"✓ Ducked volume: {ducker.ducked_volume}")
        print("✓ Ready to mix audio with voiceover")
        
        return True
    except Exception as e:
        print(f"❌ Audio Ducking test failed: {e}")
        return False

def test_sound_effects():
    """Test sound effects manager"""
    print_header("Testing Sound Effects Manager")
    
    try:
        from modules.audio_manager.sound_effects import SoundEffectsManager
        
        sfx = SoundEffectsManager()
        print("✅ Sound Effects Manager initialized")
        
        # Get transition effect
        effect = sfx.get_transition_effect("whoosh")
        if effect:
            print(f"✓ Transition effect: {effect['name']}")
        
        # Test region-based effects
        test_regions = ["Maldives Beach", "New York City"]
        for region in test_regions:
            ambient = sfx.get_ambient_effect(region)
            if ambient:
                print(f"✓ Region '{region}' → Ambient: {ambient['name']}")
        
        effects = sfx.list_all_effects()
        print(f"\n🔊 Total sound effects available: {len(effects)}")
        
        return True
    except Exception as e:
        print(f"❌ Sound Effects test failed: {e}")
        return False

def run_all_tests():
    """Run all enhancement tests"""
    print("\n" + "=" * 70)
    print("  TRIPAVAIL AI - ENHANCEMENTS TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Music Library", test_music_library),
        ("Voiceover Generator", test_voiceover_generator),
        ("Text Overlay Manager", test_text_overlay_manager),
        ("Trending Detector", test_trending_detector),
        ("Engagement Predictor", test_engagement_predictor),
        ("Seasonal Optimizer", test_seasonal_optimizer),
        ("Audio Ducking", test_audio_ducking),
        ("Sound Effects", test_sound_effects)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results[name] = False
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'=' * 70}")
    print(f"Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
    print("=" * 70 + "\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready to use.")
    else:
        print("⚠️ Some tests failed. Check errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


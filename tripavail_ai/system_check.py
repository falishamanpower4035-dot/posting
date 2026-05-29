#!/usr/bin/env python3
"""
TripAvail AI - Complete System Check
Verifies all components before deployment
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*70)
print("TRIPAVAIL AI - SYSTEM CHECK")
print("="*70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70 + "\n")

# Track results
checks = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def check(name, test_func):
    """Run a check and track result"""
    try:
        result = test_func()
        if result is True:
            checks['passed'].append(name)
            print(f"✅ {name}")
            return True
        elif result is False:
            checks['failed'].append(name)
            print(f"❌ {name}")
            return False
        else:  # Warning
            checks['warnings'].append(name)
            print(f"⚠️  {name}")
            return None
    except Exception as e:
        checks['failed'].append(f"{name}: {str(e)}")
        print(f"❌ {name}: {str(e)}")
        return False

# 1. Environment Check
print("1. ENVIRONMENT CHECKS")
print("-" * 70)

def check_python_version():
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   Python {version.major}.{version.minor}.{version.micro}")
        return True
    return False

check("Python 3.8+", check_python_version)

def check_venv():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

check("Virtual Environment Active", check_venv)

def check_env_file():
    return Path(".env").exists()

check(".env File Exists", check_env_file)

# 2. Directory Structure
print("\n2. DIRECTORY STRUCTURE")
print("-" * 70)

required_dirs = [
    'data',
    'data/posts',
    'config',
    'core',
    'core/content',
    'core/social',
    'core/social/platforms',
    'logs'
]

for dir_path in required_dirs:
    check(f"Directory: {dir_path}", lambda d=dir_path: Path(d).exists())

# 3. Core Files
print("\n3. CORE FILES")
print("-" * 70)

core_files = [
    'smart_scheduler.py',
    'config/settings.py',
    'core/content/post_manager.py',
    'core/social/platforms/instagram_poster.py',
    'core/social/platforms/facebook_poster.py',
    'core/social/platforms/youtube_uploader.py',
    'core/social/platforms/google_drive_uploader.py'
]

for file_path in core_files:
    check(f"File: {file_path}", lambda f=file_path: Path(f).exists())

# 4. Python Dependencies
print("\n4. PYTHON DEPENDENCIES")
print("-" * 70)

dependencies = [
    ('loguru', 'loguru'),
    ('schedule', 'schedule'),
    ('requests', 'requests'),
    ('pillow', 'PIL'),  # Pillow imports as PIL
    ('moviepy', 'moviepy'),
    ('google', 'google'),
    ('openai', 'openai'),
    ('dotenv', 'dotenv')
]

for name, import_name in dependencies:
    def check_import(module):
        try:
            __import__(module.replace('-', '_'))
            return True
        except ImportError:
            return False
    
    check(f"Package: {name}", lambda m=import_name: check_import(m))

# 5. Configuration
print("\n5. CONFIGURATION")
print("-" * 70)

try:
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check critical API keys
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'NEWSDATA_API_KEY': os.getenv('NEWSDATA_API_KEY'),
        'STABILITY_API_KEY': os.getenv('STABILITY_API_KEY'),
        'FACEBOOK_GRAPH_TOKEN': None,
        'INSTAGRAM_USER_ID': None,
        'GDRIVE_FOLDER_ID': os.getenv('GDRIVE_FOLDER_ID')
    }
    
    # Load from settings
    try:
        from config import settings
        api_keys['FACEBOOK_GRAPH_TOKEN'] = settings.FACEBOOK_GRAPH_TOKEN
        api_keys['INSTAGRAM_USER_ID'] = settings.INSTAGRAM_USER_ID
    except:
        pass
    
    for key, value in api_keys.items():
        if value and len(str(value)) > 10:
            check(f"API Key: {key}", lambda: True)
        else:
            check(f"API Key: {key}", lambda: "Warning")
    
except Exception as e:
    print(f"❌ Configuration Error: {e}")

# 6. Module Imports
print("\n6. MODULE IMPORTS")
print("-" * 70)

modules = [
    ('SmartScheduler', 'from smart_scheduler import SmartScheduler'),
    ('PostManager', 'from core.content.post_manager import PostManager'),
    ('InstagramPoster', 'from core.social.platforms.instagram_poster import InstagramPoster'),
    ('FacebookPoster', 'from core.social.platforms.facebook_poster import FacebookPoster'),
    ('YouTubeUploader', 'from core.social.platforms.youtube_uploader import YouTubeUploader'),
    ('GoogleDriveUploader', 'from core.social.platforms.google_drive_uploader import GoogleDriveUploader')
]

for name, import_statement in modules:
    def test_import(statement):
        try:
            exec(statement)
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False
    
    check(f"Import: {name}", lambda s=import_statement: test_import(s))

# 7. Scheduler Check
print("\n7. SCHEDULER FUNCTIONALITY")
print("-" * 70)

try:
    from smart_scheduler import SmartScheduler
    scheduler = SmartScheduler()
    
    check("Scheduler Initialization", lambda: True)
    
    # Check if posts exist
    top_posts = scheduler.get_top_posts(count=10)
    if len(top_posts) > 0:
        check(f"Posts Available ({len(top_posts)} found)", lambda: True)
    else:
        check("Posts Available", lambda: "Warning - No posts found")
    
    # Check tracking files
    check("Performance Tracking", lambda: scheduler.performance_file.parent.exists())
    check("Daily Stats", lambda: scheduler.daily_stats_file.parent.exists())
    
except Exception as e:
    check("Scheduler System", lambda: False)
    print(f"      Error: {e}")

# 8. Google Drive
print("\n8. GOOGLE DRIVE")
print("-" * 70)

try:
    from core.social.platforms.google_drive_uploader import GoogleDriveUploader
    drive = GoogleDriveUploader()
    check("Google Drive Uploader", lambda: True)
    check("OAuth Token", lambda: Path("drive_token.json").exists())
except Exception as e:
    check("Google Drive Uploader", lambda: False)
    print(f"      Error: {e}")

# 9. Data Files
print("\n9. DATA FILES")
print("-" * 70)

check("Posts Directory", lambda: len(list(Path("data/posts").glob("post_*"))) > 0 if Path("data/posts").exists() else "Warning")

# 10. Documentation
print("\n10. DOCUMENTATION")
print("-" * 70)

docs = [
    'README.md',
    'SMART_SCHEDULER_COMPLETE.md',
    'ENHANCED_FEATURES_COMPLETE.md',
    'SPACING_CORRECT_BEHAVIOR.md'
]

for doc in docs:
    check(f"Doc: {doc}", lambda d=doc: Path(d).exists())

# Summary
print("\n" + "="*70)
print("SYSTEM CHECK SUMMARY")
print("="*70)
print(f"✅ Passed: {len(checks['passed'])}")
print(f"❌ Failed: {len(checks['failed'])}")
print(f"⚠️  Warnings: {len(checks['warnings'])}")
print("="*70)

if len(checks['failed']) == 0:
    print("\n🎉 SYSTEM IS READY FOR DEPLOYMENT!")
    print("\nNext Steps:")
    print("  1. Review warnings (if any)")
    print("  2. Test posting: python smart_scheduler.py --post-now")
    print("  3. Start scheduler: python smart_scheduler.py --run")
    sys.exit(0)
else:
    print("\n⚠️  SYSTEM HAS ISSUES - RESOLVE BEFORE DEPLOYMENT")
    print("\nFailed Checks:")
    for item in checks['failed']:
        print(f"  ❌ {item}")
    print("\nPlease fix these issues and run check again.")
    sys.exit(1)


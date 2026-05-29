#!/usr/bin/env python3
"""
Phase 2 Sandbox Test Runner
============================
Quick test suite for Phase 2 experimental features.
Run this to validate sandbox setup and test new features.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import from main project
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure sandbox logging
log_file = Path(__file__).parent / "logs" / f"phase2_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logger.add(log_file, rotation="10 MB", retention="7 days", level="DEBUG")

print("=" * 70)
print("  PHASE 2 SANDBOX - TEST SUITE")
print("=" * 70)
print()

# Check if we're in sandbox mode
def check_sandbox_mode():
    """Verify we're running in sandbox mode"""
    print("[1/5] Checking sandbox mode...")
    
    # Check for .env_sandbox file
    env_sandbox = Path(__file__).parent / ".env_sandbox"
    if not env_sandbox.exists():
        print("❌ .env_sandbox not found!")
        print("    Please copy .env_sandbox_template to .env_sandbox")
        return False
    
    # Load sandbox env
    from dotenv import load_dotenv
    load_dotenv(env_sandbox)
    
    sandbox_mode = os.getenv("SANDBOX_MODE", "false").lower() == "true"
    
    if sandbox_mode:
        print("✅ Sandbox mode: ACTIVE")
        print(f"   Version: {os.getenv('SANDBOX_VERSION', 'unknown')}")
        return True
    else:
        print("⚠️  WARNING: SANDBOX_MODE not set to 'true'!")
        print("   This may affect production systems!")
        return False

def test_directory_structure():
    """Verify sandbox directory structure"""
    print("\n[2/5] Checking directory structure...")
    
    base_dir = Path(__file__).parent
    required_dirs = ["config", "core", "data", "logs", "scripts"]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - MISSING")
            all_exist = False
    
    return all_exist

def test_isolated_data():
    """Test that we're using isolated data directory"""
    print("\n[3/5] Checking data isolation...")
    
    data_dir = Path(__file__).parent / "data"
    
    # Create test file to verify isolation
    test_file = data_dir / "sandbox_test.txt"
    test_file.write_text(f"Sandbox test at {datetime.now()}")
    
    if test_file.exists():
        print("   ✅ Sandbox data directory is writable")
        print(f"   📁 Location: {data_dir.absolute()}")
        test_file.unlink()  # Clean up
        return True
    else:
        print("   ❌ Cannot write to sandbox data directory")
        return False

def test_environment_variables():
    """Test environment variable loading"""
    print("\n[4/5] Checking environment variables...")
    
    env_sandbox = Path(__file__).parent / ".env_sandbox"
    if not env_sandbox.exists():
        print("   ⚠️  .env_sandbox not found - using template")
        return False
    
    from dotenv import load_dotenv
    load_dotenv(env_sandbox)
    
    # Check for critical variables
    critical_vars = ["SANDBOX_MODE", "DEBUG_MODE", "DRY_RUN"]
    all_set = True
    
    for var in critical_vars:
        value = os.getenv(var, "NOT_SET")
        if value != "NOT_SET":
            print(f"   ✅ {var}={value}")
        else:
            print(f"   ❌ {var}=NOT_SET")
            all_set = False
    
    return all_set

def test_imports():
    """Test that we can import core modules"""
    print("\n[5/5] Testing module imports...")
    
    try:
        # Try importing key modules
        print("   Importing config.settings...", end=" ")
        from config import settings
        print("✅")
        
        print("   Checking Shutterstock integration...", end=" ")
        if hasattr(settings, 'SHUTTERSTOCK_ACCESS_TOKEN'):
            print("✅")
        else:
            print("⚠️  Not configured")
        
        print("   Checking API keys...", end=" ")
        api_keys_found = sum([
            bool(os.getenv('OPENAI_API_KEY')),
            bool(os.getenv('GOOGLE_API_KEY')),
            bool(os.getenv('ELEVENLABS_API_KEY'))
        ])
        print(f"✅ {api_keys_found}/3 keys set")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def run_phase2_experiments():
    """Placeholder for Phase 2 experimental tests"""
    print("\n" + "=" * 70)
    print("  PHASE 2 EXPERIMENTAL FEATURES")
    print("=" * 70)
    print()
    print("🔬 Experiment Framework Ready!")
    print()
    print("Add your Phase 2 tests here:")
    print("  - Test new AI models")
    print("  - Experiment with new integrations")
    print("  - Validate performance improvements")
    print("  - Try advanced features")
    print()

# Main test runner
def main():
    results = []
    
    # Run all tests
    results.append(("Sandbox Mode Check", check_sandbox_mode()))
    results.append(("Directory Structure", test_directory_structure()))
    results.append(("Data Isolation", test_isolated_data()))
    results.append(("Environment Variables", test_environment_variables()))
    results.append(("Module Imports", test_imports()))
    
    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 All tests passed! Sandbox is ready for Phase 2 development.")
        run_phase2_experiments()
        return 0
    else:
        print()
        print("⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error in test suite")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

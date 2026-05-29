#!/usr/bin/env python3
"""
TripAvail AI - Test Script
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")
    
    try:
        import openai
        print("[OK] OpenAI imported successfully")
    except ImportError as e:
        print(f"[ERROR] OpenAI import failed: {e}")
        return False
    
    try:
        import langchain
        print("[OK] LangChain imported successfully")
    except ImportError as e:
        print(f"[ERROR] LangChain import failed: {e}")
        return False
    
    try:
        import requests
        print("[OK] Requests imported successfully")
    except ImportError as e:
        print(f"[ERROR] Requests import failed: {e}")
        return False
    
    try:
        import pandas
        print("[OK] Pandas imported successfully")
    except ImportError as e:
        print(f"[ERROR] Pandas import failed: {e}")
        return False
    
    try:
        import loguru
        print("[OK] Loguru imported successfully")
    except ImportError as e:
        print(f"[ERROR] Loguru import failed: {e}")
        return False
    
    try:
        import schedule
        print("[OK] Schedule imported successfully")
    except ImportError as e:
        print(f"[ERROR] Schedule import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment setup."""
    print("\nTesting environment setup...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("[OK] .env file exists")
    else:
        print("[ERROR] .env file not found")
        return False
    
    # Check if logs directory exists
    logs_dir = Path("logs")
    if logs_dir.exists():
        print("[OK] logs directory exists")
    else:
        print("[ERROR] logs directory not found")
        return False
    
    # Check if config directory exists
    config_dir = Path("config")
    if config_dir.exists():
        print("[OK] config directory exists")
    else:
        print("[ERROR] config directory not found")
        return False
    
    return True

def test_main_app():
    """Test main application."""
    print("\nTesting main application...")
    
    try:
        from main import main
        print("[OK] Main application can be imported")
        
        # Test that main function exists and is callable
        if callable(main):
            print("[OK] Main function is callable")
        else:
            print("[ERROR] Main function is not callable")
            return False
            
    except ImportError as e:
        print(f"[ERROR] Main application import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("TripAvail AI - Environment Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_environment,
        test_main_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! Environment is ready.")
        return True
    else:
        print("Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

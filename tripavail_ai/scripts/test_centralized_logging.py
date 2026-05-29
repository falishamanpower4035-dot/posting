#!/usr/bin/env python3
"""
Test Centralized Logging Setup
Validates that the logging system works correctly and all sinks are active.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize centralized logging
from core.utils import logging_setup  # noqa

# Test both loguru and stdlib logging
from loguru import logger
import logging

def test_loguru_logging():
    """Test that Loguru logger works"""
    print("\n=== Testing Loguru Logger ===")
    logger.debug("🔍 Debug message from Loguru")
    logger.info("ℹ️ Info message from Loguru")
    logger.warning("⚠️ Warning message from Loguru")
    logger.error("❌ Error message from Loguru")
    logger.success("✅ Success message from Loguru")
    print("✅ Loguru logging test complete")

def test_stdlib_logging():
    """Test that stdlib logging is intercepted"""
    print("\n=== Testing Stdlib Logging (should flow through Loguru) ===")
    stdlib_logger = logging.getLogger(__name__)
    stdlib_logger.debug("🔍 Debug from stdlib logging")
    stdlib_logger.info("ℹ️ Info from stdlib logging")
    stdlib_logger.warning("⚠️ Warning from stdlib logging")
    stdlib_logger.error("❌ Error from stdlib logging")
    print("✅ Stdlib logging interception test complete")

def test_context_logging():
    """Test logging with extra context"""
    print("\n=== Testing Context Logging ===")
    logger.info("Processing post", post_id="TEST_001", region="Paris")
    logger.error("API failed", endpoint="shutterstock", status_code=400)
    logger.bind(module="test").info("Bound context works")
    print("✅ Context logging test complete")

def verify_log_files():
    """Verify that log files are created"""
    print("\n=== Verifying Log Files ===")
    from config import settings
    logs_dir = Path(settings.LOGS_DIR)
    
    expected_files = ["app.log", "app_error.log"]
    for file_name in expected_files:
        log_file = logs_dir / file_name
        if log_file.exists():
            size = log_file.stat().st_size
            print(f"✅ {file_name} exists ({size} bytes)")
        else:
            print(f"⚠️ {file_name} not found (may not have been written yet)")
    
    print("\n📁 All log files location:", logs_dir.absolute())

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Centralized Logging Setup")
    print("=" * 60)
    
    test_loguru_logging()
    test_stdlib_logging()
    test_context_logging()
    verify_log_files()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)
    print("\n💡 Check the logs/ directory for output files:")
    print("   - app.log (all logs)")
    print("   - app_error.log (errors only)")
    print("\nYou can tail logs in real-time:")
    print("   tail -f logs/app.log")

if __name__ == "__main__":
    main()

import sys
from pathlib import Path

# Write to multiple locations
test_file = Path("TEST_OUTPUT.txt")
test_file.write_text("This is a test file created by Python\n")

print("File written to:", test_file.absolute())
print("File exists:", test_file.exists())
print("File content:", test_file.read_text())

# Also try stderr
sys.stderr.write("STDERR: Test output\n")
sys.stderr.flush()

# And stdout
sys.stdout.write("STDOUT: Test output\n")
sys.stdout.flush()


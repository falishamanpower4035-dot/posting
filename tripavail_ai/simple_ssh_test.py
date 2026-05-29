import subprocess
import sys

result = subprocess.run(
    ["ssh", "-i", r"C:\Users\hp\.ssh\id_ed25519_do", "root@138.68.141.3", "echo 'Hello from droplet'"],
    capture_output=True,
    text=True,
    timeout=10
)

print(f"Return code: {result.returncode}", file=sys.stderr)
print(f"STDOUT: {result.stdout}", file=sys.stderr)
print(f"STDERR: {result.stderr}", file=sys.stderr)

# Write to file
with open("ssh_output.txt", "w") as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write(f"STDOUT: {result.stdout}\n")
    f.write(f"STDERR: {result.stderr}\n")

print("Output written to ssh_output.txt", file=sys.stderr)


#!/usr/bin/env python3
"""
Music Archive Diagnostic Script
Checks all archived music files for issues
"""

import subprocess
from pathlib import Path
from collections import defaultdict

def check_music_archive():
    archive_dir = Path("data/music_archive")
    
    if not archive_dir.exists():
        print("❌ Archive directory not found!")
        return
    
    issues = defaultdict(list)
    valid_files = []
    
    print("=" * 60)
    print("MUSIC ARCHIVE DIAGNOSTIC REPORT")
    print("=" * 60)
    print()
    
    # Get all MP3 files
    mp3_files = sorted(archive_dir.glob("*.mp3"))
    total_files = len(mp3_files)
    
    print(f"📁 Total files found: {total_files}")
    print()
    
    for mp3_file in mp3_files:
        filename = mp3_file.name
        size = mp3_file.stat().st_size
        
        # Check 1: File size
        if size == 0:
            issues["Empty files"].append(filename)
            continue
        
        if size < 1000:
            issues["Very small files (<1KB)"].append(f"{filename} ({size} bytes)")
            continue
        
        # Check 2: FFprobe validation
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(mp3_file)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()[:100]
            issues["FFprobe errors"].append(f"{filename}: {error_msg}")
            continue
        
        # Check 3: Duration
        try:
            duration = float(result.stdout.strip())
            
            if duration < 15:
                issues["Too short (<15s)"].append(f"{filename} ({duration:.2f}s)")
            elif duration > 30:
                issues["Too long (>30s)"].append(f"{filename} ({duration:.2f}s)")
            else:
                valid_files.append((filename, duration, size))
        except:
            issues["Duration parse errors"].append(filename)
    
    # Print summary
    print(f"✅ Valid files: {len(valid_files)}")
    print(f"❌ Files with issues: {sum(len(v) for v in issues.values())}")
    print()
    
    # Print issues by category
    if issues:
        print("=" * 60)
        print("ISSUES FOUND:")
        print("=" * 60)
        
        for category, file_list in sorted(issues.items()):
            print(f"\n📋 {category}: {len(file_list)}")
            for item in file_list:
                print(f"   - {item}")
    else:
        print("✅ No issues found!")
    
    # Print valid files summary
    if valid_files:
        print()
        print("=" * 60)
        print("VALID FILES SUMMARY:")
        print("=" * 60)
        durations = [d for _, d, _ in valid_files]
        sizes = [s for _, _, s in valid_files]
        
        print(f"Total valid: {len(valid_files)}")
        print(f"Duration range: {min(durations):.2f}s - {max(durations):.2f}s")
        print(f"Average duration: {sum(durations)/len(durations):.2f}s")
        print(f"Size range: {min(sizes)/1024:.1f}KB - {max(sizes)/1024:.1f}KB")
        print(f"Average size: {sum(sizes)/len(sizes)/1024:.1f}KB")
    
    # Recommendations
    print()
    print("=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if "Empty files" in issues:
        print("1. Delete empty files (they cannot be used)")
    
    if "Too short" in issues or "Too long" in issues:
        print("2. Consider regenerating files with incorrect duration")
    
    if len(valid_files) >= 40:
        print("3. ✅ You have enough valid files for production use")
    elif len(valid_files) < 20:
        print("3. ⚠️ Consider generating more music files")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    check_music_archive()


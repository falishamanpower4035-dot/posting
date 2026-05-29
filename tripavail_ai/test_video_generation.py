#!/usr/bin/env python3
"""
Test video generation for a specific post
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.media.video.generator.pro_video import ProVideoGenerator
from core.content.post_manager import PostManager

def main():
    post_id = sys.argv[1] if len(sys.argv) > 1 else "001"
    
    print(f"\n{'='*60}")
    print(f"  Testing Video Generation for Post {post_id}")
    print(f"{'='*60}\n")
    
    pm = PostManager()
    
    # Check if post exists
    if post_id not in pm.get_all_posts():
        print(f"❌ Error: Post {post_id} does not exist")
        return False
    
    # Check if images exist
    images = pm.get_image_paths(post_id)
    if not images:
        print(f"❌ Error: No images found for post {post_id}")
        return False
    
    print(f"✅ Found {len(images)} images")
    
    # Check if voiceover exists
    voiceover = pm.get_voiceover_path(post_id)
    if not voiceover.exists():
        print(f"⚠️  Warning: No voiceover found, video will be silent")
    else:
        print(f"✅ Found voiceover: {voiceover}")
    
    # Get post metadata
    metadata = pm.get_metadata(post_id)
    if not metadata:
        metadata = {"post_id": post_id, "topic_id": post_id}
    
    # Generate video
    print(f"\n📹 Generating video...")
    gen = ProVideoGenerator()
    
    try:
        result = gen.generate_for_post(metadata)
        
        if result:
            final_video = pm.get_final_video_path(post_id)
            if final_video.exists():
                size_mb = final_video.stat().st_size / (1024*1024)
                print(f"\n✅ SUCCESS: Video generated!")
                print(f"   Path: {final_video}")
                print(f"   Size: {size_mb:.1f} MB")
                return True
            else:
                print(f"\n❌ ERROR: Video generation reported success but file not found")
                return False
        else:
            print(f"\n❌ ERROR: Video generation failed")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


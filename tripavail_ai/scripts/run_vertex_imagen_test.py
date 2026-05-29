#!/usr/bin/env python3
import os
from core.media.images.generator.thumbnail_generator import ThumbnailGenerator


def main():
    print("Starting Vertex Imagen test...")
    meta = {
        'original_title': 'Maldives at Sunset',
        'caption': 'Cinematic travel thumbnail, vertical 9:16',
        'region': 'Maldives',
        'hashtags': ['#travel']
    }
    t = ThumbnailGenerator()
    result = t.generate_thumbnail_for_post('vertex_test', meta)
    print("Result:", result)


if __name__ == "__main__":
    main()




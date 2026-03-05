#!/usr/bin/env python3
"""
Download sample images and audio files for the CLIP & CLAP demo.
Uses publicly available samples from various sources.
"""

import os
import urllib.request
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent / "samples"

# Sample images from Unsplash (small, royalty-free)
SAMPLE_IMAGES = {
    "cat.jpg": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=640&q=80",
    "street.jpg": "https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?w=640&q=80",
    "food.jpg": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=640&q=80",
    "mountain.jpg": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=640&q=80",
}

# Sample audio - we'll generate simple ones or use public domain
# For the demo, you can also record your own or use freesound.org samples
SAMPLE_AUDIO_INSTRUCTIONS = """
Sample audio files need to be manually added to backend/samples/audio/

Recommended sources (all free, attribution may be required):
- https://freesound.org/ - Search for: dog bark, traffic, music, speech
- https://www.zapsplat.com/ - Free sound effects
- https://pixabay.com/sound-effects/ - Royalty free sounds

Required files:
- dog_bark.wav - A dog barking sound (2-5 seconds)
- traffic.wav - City traffic sounds (2-5 seconds)
- music.wav - Short music clip (5-10 seconds)
- speech.wav - Someone speaking (2-5 seconds)

Convert to WAV format if needed (48kHz, mono or stereo).
"""


def download_images():
    """Download sample images from Unsplash."""
    images_dir = SAMPLES_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    for filename, url in SAMPLE_IMAGES.items():
        filepath = images_dir / filename
        if filepath.exists():
            print(f"  [skip] {filename} already exists")
            continue

        print(f"  [download] {filename}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"  [done] {filename}")
        except Exception as e:
            print(f"  [error] {filename}: {e}")


def setup_audio_directory():
    """Create audio directory and instructions file."""
    audio_dir = SAMPLES_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    readme_path = audio_dir / "README.txt"
    with open(readme_path, "w") as f:
        f.write(SAMPLE_AUDIO_INSTRUCTIONS)

    print(f"  [info] Audio sample instructions written to {readme_path}")
    print("  [info] Please add audio samples manually (see README.txt)")


def create_placeholder_audio():
    """Create simple placeholder audio files using scipy if available."""
    try:
        import numpy as np
        from scipy.io import wavfile

        audio_dir = SAMPLES_DIR / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        sample_rate = 48000
        duration = 3  # seconds

        # Create simple placeholder tones/noise
        placeholders = {
            "dog_bark.wav": lambda t: np.sin(2 * np.pi * 300 * t) * np.exp(-t * 2) * (np.random.random(len(t)) > 0.7).astype(float),
            "traffic.wav": lambda t: np.random.randn(len(t)) * 0.3,
            "music.wav": lambda t: np.sin(2 * np.pi * 440 * t) * 0.3 + np.sin(2 * np.pi * 554 * t) * 0.2,
            "speech.wav": lambda t: np.sin(2 * np.pi * 150 * t) * (1 + 0.5 * np.sin(2 * np.pi * 5 * t)) * 0.3,
        }

        t = np.linspace(0, duration, int(sample_rate * duration))

        for filename, generator in placeholders.items():
            filepath = audio_dir / filename
            if filepath.exists():
                print(f"  [skip] {filename} already exists")
                continue

            signal = generator(t)
            signal = (signal * 32767).astype(np.int16)
            wavfile.write(filepath, sample_rate, signal)
            print(f"  [created] {filename} (placeholder)")

        print("\n  Note: These are placeholder audio files.")
        print("  For best demo results, replace with real audio samples.")

    except ImportError:
        print("  [info] scipy not available, skipping placeholder audio generation")
        setup_audio_directory()


def main():
    print("CLIP & CLAP Demo - Sample Data Setup\n")

    print("Downloading sample images...")
    download_images()

    print("\nSetting up audio samples...")
    create_placeholder_audio()

    print("\nDone! Sample data is ready.")
    print(f"Location: {SAMPLES_DIR}")


if __name__ == "__main__":
    main()

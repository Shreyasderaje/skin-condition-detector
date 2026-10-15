"""Generate small synthetic placeholder images for smoke-testing the upload flow.

These are NOT medical images and carry no clinical meaning — they only
exercise the HTTP -> validation -> inference -> storage pipeline when no
HAM10000 sample is at hand. Output: ../sample_images/*.jpg (224x224).
"""
import os
import random

from PIL import Image, ImageDraw

BASE_TONES = [
    (214, 164, 132),  # light brown
    (198, 138, 104),  # medium brown
    (176, 118, 92),   # deeper brown
]
OUTPUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "sample_images")
)

random.seed(42)


def make_image(index: int) -> Image.Image:
    base = BASE_TONES[index % len(BASE_TONES)]
    img = Image.new("RGB", (224, 224), base)
    draw = ImageDraw.Draw(img)

    # A few irregular blotches in lighter/darker shades
    for _ in range(6):
        shade = tuple(max(0, min(255, c + random.randint(-45, 45))) for c in base)
        x, y = random.randint(20, 180), random.randint(20, 180)
        r = random.randint(15, 45)
        draw.ellipse([x, y, x + r, y + r], fill=shade)

    # Grain
    pixels = img.load()
    for _ in range(4000):
        x, y = random.randint(0, 223), random.randint(0, 223)
        delta = random.randint(-18, 18)
        r, g, b = pixels[x, y]
        pixels[x, y] = (max(0, min(255, r + delta)),
                        max(0, min(255, g + delta)),
                        max(0, min(255, b + delta)))
    return img


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i in range(1, 4):
        path = os.path.join(OUTPUT_DIR, f"sample_{i}.jpg")
        make_image(i).save(path, "JPEG", quality=85)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()

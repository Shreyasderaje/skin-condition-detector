"""Storage for uploaded screening images.

Files are named by content hash + timestamp so no PII ever appears in
filenames (compliance requirement).
"""
import hashlib
import os
import time

from PIL import Image


def save_image(img: Image.Image, upload_folder: str) -> str:
    """Persist a PIL image as JPEG; returns the generated filename."""
    os.makedirs(upload_folder, exist_ok=True)
    digest = hashlib.sha256(img.tobytes()).hexdigest()[:16]
    filename = f"{digest}_{int(time.time() * 1000)}.jpg"
    img.save(os.path.join(upload_folder, filename), "JPEG", quality=90)
    return filename


def image_file_path(filename, upload_folder):
    return os.path.join(upload_folder, os.path.basename(filename))

"""Shared class definitions and image preprocessing (inference + training)."""
import numpy as np
from PIL import Image

IMG_SIZE = 224
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# HAM10000's seven diagnostic categories, in canonical order.
# DX_CODES order must match the zero-padded folder names written by
# ml/prepare_data.py (00_mel, 01_bcc, ...) so ImageFolder picks them up
# in exactly this order.
CLASSES = [
    "Melanoma",             # mel
    "Basal Cell Carcinoma",  # bcc
    "Actinic Keratosis",    # akiec
    "Benign Keratosis",     # bkl
    "Vascular Lesion",      # vasc
    "Dermatofibroma",       # df
    "Melanocytic Nevus",    # nv
]
DX_CODES = ["mel", "bcc", "akiec", "bkl", "vasc", "df", "nv"]

# Fixed clinical triage mapping: 7 lesion classes -> 3 risk buckets.
CLASS_TO_RISK = {
    "Melanoma": "HIGH",
    "Basal Cell Carcinoma": "HIGH",
    "Actinic Keratosis": "MEDIUM",
    "Vascular Lesion": "MEDIUM",
    "Benign Keratosis": "LOW",
    "Dermatofibroma": "LOW",
    "Melanocytic Nevus": "LOW",
}


def preprocess(img: Image.Image) -> np.ndarray:
    """PIL image -> normalized float32 array of shape (3, 224, 224)."""
    img = img.convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    return np.transpose(arr, (2, 0, 1))

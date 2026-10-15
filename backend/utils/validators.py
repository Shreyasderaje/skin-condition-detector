"""Input validation for images, patients and auth payloads."""
import re

from PIL import Image

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_MIMES = {"image/jpeg", "image/jpg", "image/png"}
PHONE_RE = re.compile(r"^\+?[1-9]\d{7,14}$")  # E.164-ish
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GENDERS = {"Male", "Female", "Other"}
MIN_DIM, MAX_DIM = 64, 8000  # pixels


def is_allowed_image(filename, mimetype):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if mimetype and mimetype not in ALLOWED_MIMES:
        return False
    return True


def open_and_validate_image(stream):
    """Load an uploaded stream into a PIL RGB image, checking pixel dims.

    Raises ValueError with a user-facing message if invalid.
    """
    try:
        img = Image.open(stream)
        img = img.convert("RGB")
    except Exception:
        raise ValueError("Invalid or corrupted image file")
    width, height = img.size
    if width < MIN_DIM or height < MIN_DIM:
        raise ValueError(f"Image too small (minimum {MIN_DIM}x{MIN_DIM} pixels)")
    if width > MAX_DIM or height > MAX_DIM:
        raise ValueError(f"Image too large (maximum {MAX_DIM}x{MAX_DIM} pixels)")
    return img


def validate_password(password):
    return isinstance(password, str) and len(password) >= 8


def validate_email(email):
    return isinstance(email, str) and bool(EMAIL_RE.match(email))


def validate_age(age):
    return isinstance(age, int) and 1 <= age <= 120


def validate_gender(gender):
    return gender in GENDERS


def validate_phone(number):
    # Optional field: empty/None passes, otherwise must look like E.164.
    return not number or (isinstance(number, str) and bool(PHONE_RE.match(number)))
